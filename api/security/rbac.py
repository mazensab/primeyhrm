# ===============================================================
# 🔐 RBAC ENGINE V1 — Backend Enforcement Only
# Mham Cloud
# ===============================================================
# ✔ Company Scoped
# ✔ ManyToMany Roles
# ✔ JSON permissions (list OR dict supported)
# ✔ Superuser override
# ✔ Safe Multi-Tenant
# ✔ No cache (V1 simple)
# ===============================================================

from functools import wraps
from typing import Set

from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser

from company_manager.models import CompanyUser


# ===============================================================
# 🔐 Resolve Active Company Context (STRICT)
# ===============================================================
def _resolve_company_user(request) -> CompanyUser | None:
    """
    STRICT Company Resolver
    - Requires active_company_id in session
    - Ensures membership is active
    """

    if not request.user or isinstance(request.user, AnonymousUser):
        return None

    active_company_id = request.session.get("active_company_id")

    if not active_company_id:
        return None

    return (
        CompanyUser.objects
        .select_related("company")
        .prefetch_related("roles")
        .filter(
            user=request.user,
            company_id=active_company_id,
            is_active=True,
        )
        .first()
    )


# ===============================================================
# 🧠 Resolve Permissions From Roles
# ===============================================================
def _resolve_permissions(company_user: CompanyUser) -> Set[str]:
    """
    Merge all role permissions into a flat set
    Supports:
        - JSON list
        - JSON dict (legacy support)
    """

    permissions: Set[str] = set()

    roles = company_user.roles.all()

    for role in roles:
        role_permissions = role.permissions or []

        # 🔹 If stored as list
        if isinstance(role_permissions, list):
            permissions.update(role_permissions)

        # 🔹 If stored as dict (legacy)
        elif isinstance(role_permissions, dict):
            permissions.update(
                key for key, value in role_permissions.items() if value
            )

    return permissions


# ===============================================================
# 🔎 Check Permission
# ===============================================================
def has_company_permission(request, permission_code: str) -> bool:
    """
    Core Permission Check
    """

    # -----------------------------------------------------------
    # 🟢 Superuser Override
    # -----------------------------------------------------------
    if request.user and request.user.is_superuser:
        return True

    company_user = _resolve_company_user(request)

    if not company_user:
        return False

    user_permissions = _resolve_permissions(company_user)

    return permission_code in user_permissions


# ===============================================================
# 🛡️ Decorator — Require Company Permission
# ===============================================================
def require_company_permission(permission_code: str):
    """
    Usage:
        @require_company_permission("employees.view")
        def view(request):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):

            # 🔒 Must be authenticated first
            if not request.user.is_authenticated:
                return JsonResponse(
                    {"error": "Authentication required"},
                    status=401,
                )

            if not has_company_permission(request, permission_code):
                return JsonResponse(
                    {
                        "error": "Permission denied",
                        "required_permission": permission_code,
                    },
                    status=403,
                )

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator