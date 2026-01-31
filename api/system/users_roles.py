from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from company_manager.models import CompanyRole


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
# 🔐 SYSTEM Permission Guard (FINAL)
# ================================================================
def system_permission_required(permission: str):
    """
    System-level permission guard
    يعتمد فقط على Django Superuser
    """
    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return error("غير مصرح", 401)

            # ✅ Super Admin only
            if not request.user.is_superuser:
                return error("ليس لديك صلاحيات النظام", 403)

            return view_func(request, *args, **kwargs)

        return _wrapped
    return decorator


# ================================================================
# 1️⃣ List System Roles
# ================================================================
@login_required
@system_permission_required("roles.view")
def list_roles(request):
    roles = (
        CompanyRole.objects
        .filter(is_system_role=True)
        .annotate(users_count=Count("company_users"))
        .values(
            "id",
            "name",
            "permissions",
            "is_system_role",
            "users_count",
        )
        .order_by("name")
    )

    return success({"items": list(roles)})


# ================================================================
# 2️⃣ Role Detail
# ================================================================
@login_required
@system_permission_required("roles.view")
def role_detail(request, role_id):
    try:
        role = (
            CompanyRole.objects
            .filter(is_system_role=True)
            .annotate(users_count=Count("company_users"))
            .get(id=role_id)
        )

        return success({
            "id": role.id,
            "name": role.name,
            "permissions": role.permissions or [],
            "is_system_role": role.is_system_role,
            "users_count": role.users_count,
        })

    except CompanyRole.DoesNotExist:
        return error("الدور غير موجود", 404)


# ================================================================
# 3️⃣ Create / Update System Role
# ================================================================
@login_required
@require_http_methods(["POST"])
@system_permission_required("roles.manage")
def save_role(request):
    role_id = request.POST.get("role_id")
    name = request.POST.get("name")
    permissions = request.POST.getlist("permissions[]")

    if not name:
        return error("اسم الدور مطلوب")

    if not permissions:
        return error("يجب تحديد صلاحية واحدة على الأقل")

    # -------------------------------
    # CREATE
    # -------------------------------
    if not role_id:
        role = CompanyRole.objects.create(
            name=name,
            permissions=permissions,
            is_system_role=True,
        )
        return success({"id": role.id})

    # -------------------------------
    # UPDATE
    # -------------------------------
    try:
        role = CompanyRole.objects.get(id=role_id, is_system_role=True)

        role.name = name
        role.permissions = permissions
        role.save(update_fields=["name", "permissions"])

        return success({"id": role.id})

    except CompanyRole.DoesNotExist:
        return error("الدور غير موجود", 404)
