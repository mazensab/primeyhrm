# ======================================================
# 🎭 Company Roles API — SAFE + MODEL-CORRECT (FINAL)
# Primey HR Cloud
# ======================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

from company_manager.models import CompanyRole, CompanyUser


# ------------------------------------------------------
# 🔐 Resolve Company (ABSOLUTELY SAFE)
# ------------------------------------------------------
def _resolve_company(request):
    company_user = (
        CompanyUser.objects
        .select_related("company")
        .filter(user=request.user, is_active=True)
        .order_by("-id")
        .first()
    )
    return company_user.company if company_user else None


# ------------------------------------------------------
# 📋 Roles List (FOR EMPLOYEE CREATE UI)
# ------------------------------------------------------
@require_GET
@login_required
def roles_list(request):
    company = _resolve_company(request)

    if not company:
        return JsonResponse(
            {
                "status": "error",
                "message": "User is not linked to any active company",
                "roles": [],
            },
            status=403,
        )

    roles = (
        CompanyRole.objects
        .filter(company=company)
        .order_by("is_system_role", "name")  # non-system roles first
    )

    return JsonResponse(
        {
            "status": "ok",
            "roles": [
                {
                    "id": r.id,
                    "name": r.name,
                    "is_system_role": r.is_system_role,
                }
                for r in roles
            ],
        }
    )


# ------------------------------------------------------
# 👁️ Role Preview (Before Save)
# ------------------------------------------------------
@require_GET
@login_required
def role_preview(request, role_id):
    company = _resolve_company(request)

    if not company:
        return JsonResponse(
            {
                "status": "error",
                "message": "User is not linked to any active company",
            },
            status=403,
        )

    role = CompanyRole.objects.filter(
        id=role_id,
        company=company,
    ).first()

    if not role:
        return JsonResponse(
            {"status": "error", "message": "Role not found"},
            status=404,
        )

    # --------------------------------------------------
    # 🧠 Normalize permissions → ALWAYS ARRAY
    # --------------------------------------------------
    permissions = role.permissions or []

    if isinstance(permissions, dict):
        permissions = list(permissions.keys())
    elif isinstance(permissions, str):
        permissions = []

    return JsonResponse(
        {
            "status": "ok",
            "role": {
                "id": role.id,
                "name": role.name,
                "is_system_role": role.is_system_role,
                "permissions": permissions,
            },
        }
    )
