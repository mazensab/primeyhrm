# ================================================================
# 👤 SYSTEM — Users Actions (V3.3 HARD LOCKED)
# Mham Cloud
# ================================================================

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db import transaction
import json

from company_manager.models import CompanyUser
from company_manager.models import CompanyRole as Role
from employee_center.models import Employee


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
# 📦 Payload Helper
# ================================================================
def get_payload(request):
    if request.content_type == "application/json":
        try:
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            return {}
    return request.POST


# ================================================================
# 🔐 SYSTEM Permission Guard
# ================================================================
def system_permission_required(permission: str):
    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return error("غير مصرح", 401)

            # System Admin session OR superuser
            if not request.user.is_superuser:
                if not request.session.get("system_admin_id"):
                    return error("ليس لديك صلاحيات النظام", 403)

            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# ================================================================
# 🧠 Internal Guards (MODEL-SAFE)
# ================================================================
def resolve_actor(request) -> CompanyUser | None:
    """
    المستخدم الذي ينفذ الإجراء
    """
    return CompanyUser.objects.filter(user=request.user).first()


def is_system_role(target: CompanyUser) -> bool:
    """
    يتحقق هل المستخدم System Admin
    يدعم:
    - ForeignKey Role
    - String-based Role
    """
    role = target.role

    # FK Role
    if hasattr(role, "is_system_role"):
        return bool(role.is_system_role)

    # String fallback
    if isinstance(role, str):
        return role.upper() in {"SYSTEM", "SYSTEM_ADMIN", "SUPER_ADMIN"}

    return False


def prevent_self_action(actor: CompanyUser | None, target: CompanyUser):
    """
    🔒 منع أي إجراء على نفسه:
    - تغيير الدور
    - الإيقاف
    - الحذف
    - إعادة تعيين كلمة المرور
    """
    if actor and actor.user_id == target.user_id:
        return error("لا يمكنك تنفيذ هذا الإجراء على حسابك", 403)
    return None


def is_last_system_admin(target: CompanyUser) -> bool:
    """
    يتحقق هل هذا المستخدم هو آخر System Admin نشط
    """
    if not is_system_role(target):
        return False

    qs = CompanyUser.objects.filter(is_active=True)

    qs_fk = qs.filter(role__is_system_role=True)
    qs_str = qs.filter(role__in=["SYSTEM", "SYSTEM_ADMIN", "SUPER_ADMIN"])

    return qs_fk.union(qs_str).exclude(id=target.id).count() == 0


def prevent_last_system_admin(target: CompanyUser):
    if is_last_system_admin(target):
        return error("لا يمكن تنفيذ هذا الإجراء على آخر مسؤول نظام", 403)
    return None


def apply_common_guards(actor: CompanyUser | None, target: CompanyUser):
    """
    حمايات مشتركة لكل العمليات الحساسة
    """
    block = prevent_self_action(actor, target)
    if block:
        return block

    block = prevent_last_system_admin(target)
    if block:
        return block

    return None


# ================================================================
# 1️⃣ Toggle User Status
# ================================================================
@login_required
@require_POST
@system_permission_required("users.manage")
def toggle_user_status(request):
    payload = get_payload(request)
    company_user_id = payload.get("company_user_id")

    if not company_user_id:
        return error("معرّف المستخدم مطلوب")

    actor = resolve_actor(request)
    target = get_object_or_404(
        CompanyUser.objects.select_related("user"),
        id=int(company_user_id),
    )

    block = apply_common_guards(actor, target)
    if block:
        return block

    target.is_active = not target.is_active
    target.save(update_fields=["is_active"])

    target.user.is_active = target.is_active
    target.user.save(update_fields=["is_active"])

    return success({
        "company_user_id": target.id,
        "is_active": target.is_active,
    })


# ================================================================
# 2️⃣ Change User Role
# ================================================================
@login_required
@require_POST
@system_permission_required("users.manage")
def change_user_role(request):
    payload = get_payload(request)

    company_user_id = payload.get("company_user_id")
    role_id = payload.get("role_id")

    if not company_user_id or not role_id:
        return error("company_user_id و role_id مطلوبان")

    actor = resolve_actor(request)
    target = get_object_or_404(
        CompanyUser.objects.select_related("user"),
        id=int(company_user_id),
    )

    # 🔒 الحماية الأساسية
    block = apply_common_guards(actor, target)
    if block:
        return block

    role = get_object_or_404(Role, id=int(role_id))

    # 🔒 منع إعادة تعيين نفس الدور
    if target.role_id == role.id:
        return error("الدور المحدد هو نفسه الدور الحالي")

    target.role = role
    target.save(update_fields=["role"])

    return success({
        "company_user_id": target.id,
        "role": role.name,
    })


# ================================================================
# 3️⃣ Reset User Password
# ================================================================
@login_required
@require_POST
@system_permission_required("users.manage")
def reset_user_password(request):
    payload = get_payload(request)

    company_user_id = payload.get("company_user_id")
    password = payload.get("password")

    if not company_user_id:
        return error("معرّف المستخدم مطلوب")

    if not password or len(password) < 8:
        return error("كلمة المرور يجب أن تكون 8 أحرف على الأقل")

    actor = resolve_actor(request)
    target = get_object_or_404(
        CompanyUser.objects.select_related("user"),
        id=int(company_user_id),
    )

    block = apply_common_guards(actor, target)
    if block:
        return block

    user: User = target.user
    user.set_password(password)
    user.save(update_fields=["password"])

    return success({
        "company_user_id": target.id,
        "user_id": user.id,
    })


# ================================================================
# 4️⃣ Delete User
# ================================================================
@login_required
@require_POST
@system_permission_required("users.manage")
def delete_user(request):
    payload = get_payload(request)
    company_user_id = payload.get("company_user_id")

    if not company_user_id:
        return error("معرّف المستخدم مطلوب")

    actor = resolve_actor(request)
    target = get_object_or_404(CompanyUser, id=int(company_user_id))

    block = apply_common_guards(actor, target)
    if block:
        return block

    target.delete()
    return success({"message": "تم حذف المستخدم"})


# ================================================================
# 5️⃣ Create Company User
# ================================================================
@login_required
@require_POST
@system_permission_required("users.manage")
@transaction.atomic
def create_company_user(request, company_id):
    payload = get_payload(request)

    username = payload.get("username", "").strip()
    full_name = payload.get("full_name", "").strip()
    email = payload.get("email", "").strip().lower()
    password = payload.get("password")
    role_id = payload.get("role_id")

    if not all([username, full_name, email, password, role_id]):
        return error("جميع الحقول مطلوبة")

    from company_manager.models import Company
    company = get_object_or_404(Company, id=company_id)

    if User.objects.filter(username=username).exists():
        return error("اسم المستخدم مستخدم مسبقًا")

    if User.objects.filter(email=email).exists():
        return error("البريد الإلكتروني مستخدم مسبقًا")

    role = get_object_or_404(Role, id=int(role_id))

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_active=True,
    )

    company_user = CompanyUser.objects.create(
        user=user,
        company=company,
        role=role,
        is_active=True,
    )

    employee = Employee.objects.create(
        company=company,
        full_name=full_name,
    )

    return success({
        "company_user_id": company_user.id,
        "employee_id": employee.id,
        "user_id": user.id,
        "username": username,
        "role": role.name,
    })
