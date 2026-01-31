from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from company_manager.models import CompanyUser, CompanyRole


# ================================================================
# 🔒 Response Helpers
# ================================================================
def error(msg, status=400):
    return JsonResponse(
        {"status": "error", "message": msg},
        status=status,
        json_dumps_params={"ensure_ascii": False},
    )


def success(data=None):
    return JsonResponse(
        {"status": "success", "data": data or {}},
        status=200,
        json_dumps_params={"ensure_ascii": False},
    )


# ================================================================
# 🔐 Company Permission Guard (IMPERSONATION AWARE)
# ================================================================
def company_permission_required(permission: str):
    """
    permissions:
        - users.manage
    """

    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):

            # ====================================================
            # 🧠 المصدر الوحيد الموثوق
            # (يُجهّز عبر CompanyImpersonationMiddleware)
            # ====================================================
            actor: CompanyUser | None = getattr(request, "company_user", None)

            if not actor or not actor.is_active:
                return error("لا تملك صلاحيات داخل أي شركة", 403)

            role = actor.role or ""

            # 👑 COMPANY OWNER — صلاحيات كاملة
            if role == "COMPANY_OWNER":
                return view_func(request, *args, **kwargs)

            # 👮 COMPANY ADMIN / ADMIN
            if permission == "users.manage" and role not in (
                "COMPANY_ADMIN",
                "ADMIN",
            ):
                return error("ليس لديك صلاحية إدارة المستخدمين", 403)

            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


# ================================================================
# 🧠 Internal Guards
# ================================================================
def ensure_same_company(actor: CompanyUser, target: CompanyUser):
    if actor.company_id != target.company_id:
        return error("لا يمكنك إدارة مستخدم من شركة أخرى", 403)
    return None


def prevent_self_action(actor: CompanyUser, target: CompanyUser):
    if actor.user_id == target.user_id:
        return error("لا يمكنك تنفيذ هذا الإجراء على حسابك", 403)
    return None


def is_last_company_owner(target: CompanyUser) -> bool:
    if target.role != "COMPANY_OWNER":
        return False

    return (
        CompanyUser.objects.filter(
            company=target.company,
            role="COMPANY_OWNER",
            is_active=True,
        )
        .exclude(id=target.id)
        .count()
        == 0
    )


def prevent_last_company_owner(target: CompanyUser):
    if is_last_company_owner(target):
        return error(
            "لا يمكن تنفيذ هذا الإجراء على آخر مالك للشركة",
            403,
        )
    return None


# ================================================================
# 1️⃣ Toggle User Status
# ================================================================
@csrf_exempt
@login_required
@require_POST
@company_permission_required("users.manage")
def toggle_user_status(request):
    company_user_id = request.POST.get("company_user_id")
    if not company_user_id:
        return error("معرّف المستخدم مطلوب")

    actor: CompanyUser = request.company_user
    target = get_object_or_404(CompanyUser, id=company_user_id)

    block = (
        ensure_same_company(actor, target)
        or prevent_self_action(actor, target)
        or prevent_last_company_owner(target)
    )
    if block:
        return block

    target.is_active = not target.is_active
    target.save(update_fields=["is_active"])

    # Sync Django User
    target.user.is_active = target.is_active
    target.user.save(update_fields=["is_active"])

    return success(
        {
            "user_id": target.id,
            "is_active": target.is_active,
        }
    )


# ================================================================
# 2️⃣ Change User Role
# ================================================================
@csrf_exempt
@login_required
@require_POST
@company_permission_required("users.manage")
def change_user_role(request):
    company_user_id = request.POST.get("company_user_id")
    new_role = request.POST.get("new_role")

    if not company_user_id:
        return error("معرّف المستخدم مطلوب")
    if not new_role:
        return error("اسم الدور مطلوب")

    actor: CompanyUser = request.company_user
    target = get_object_or_404(CompanyUser, id=company_user_id)

    block = (
        ensure_same_company(actor, target)
        or prevent_self_action(actor, target)
        or prevent_last_company_owner(target)
    )
    if block:
        return block

    # Validate role exists
    CompanyRole.objects.get(name=new_role)

    target.role = new_role
    target.save(update_fields=["role"])

    return success(
        {
            "user_id": target.id,
            "role": new_role,
        }
    )


# ================================================================
# 3️⃣ Reset User Password
# ================================================================
@csrf_exempt
@login_required
@require_POST
@company_permission_required("users.manage")
def reset_user_password(request):
    company_user_id = request.POST.get("company_user_id")
    new_password = request.POST.get("password")

    if not company_user_id:
        return error("معرّف المستخدم مطلوب")
    if not new_password:
        return error("كلمة المرور مطلوبة")

    actor: CompanyUser = request.company_user
    target = get_object_or_404(
        CompanyUser.objects.select_related("user"),
        id=company_user_id,
    )

    block = (
        ensure_same_company(actor, target)
        or prevent_self_action(actor, target)
        or prevent_last_company_owner(target)
    )
    if block:
        return block

    user: User = target.user
    user.set_password(new_password)
    user.save(update_fields=["password"])

    return success(
        {
            "user_id": target.id,
        }
    )


# ================================================================
# 4️⃣ Delete User
# ================================================================
@csrf_exempt
@login_required
@require_POST
@company_permission_required("users.manage")
def delete_user(request):
    company_user_id = request.POST.get("company_user_id")
    if not company_user_id:
        return error("معرّف المستخدم مطلوب")

    actor: CompanyUser = request.company_user
    target = get_object_or_404(CompanyUser, id=company_user_id)

    block = (
        ensure_same_company(actor, target)
        or prevent_self_action(actor, target)
        or prevent_last_company_owner(target)
    )
    if block:
        return block

    target.delete()

    return success(
        {
            "message": "تم حذف المستخدم من الشركة بنجاح",
        }
    )
