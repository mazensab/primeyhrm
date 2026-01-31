# ===============================================================
# 📂 api/company/users.py
# 👥 Company Users API — V1 FINAL
# Primey HR Cloud
# ===============================================================
# ✔ Company scoped
# ✔ Active users only
# ✔ Optional: unlinked users only
# ✔ Safe & defensive
# ===============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from company_manager.models import CompanyUser
from employee_center.models import Employee


@login_required
@require_http_methods(["GET"])
def company_users_list(request):
    """
    GET /api/company/users/
    GET /api/company/users/?unlinked=true
    """

    # -----------------------------------------------------------
    # 🔐 Resolve Company Context (STRICT)
    # -----------------------------------------------------------
    company_user = (
        CompanyUser.objects
        .select_related("company", "user")
        .filter(
            user=request.user,
            is_active=True,
            company__isnull=False,
        )
        .order_by("-id")
        .first()
    )

    if not company_user:
        return JsonResponse(
            {"error": "Company context not found"},
            status=403
        )

    company = company_user.company

    # -----------------------------------------------------------
    # 📥 Query Params
    # -----------------------------------------------------------
    unlinked_only = request.GET.get("unlinked") == "true"

    # -----------------------------------------------------------
    # 👥 Base Query (Active Company Users)
    # -----------------------------------------------------------
    qs = (
        CompanyUser.objects
        .select_related("user")
        .filter(
            company=company,
            is_active=True,
            user__isnull=False,
        )
    )

    # -----------------------------------------------------------
    # 🔗 Exclude users already linked to employees
    # -----------------------------------------------------------
    if unlinked_only:
        linked_user_ids = (
            Employee.objects
            .filter(
                company=company,
                user__isnull=False,
            )
            .values_list("user_id", flat=True)
        )

        qs = qs.exclude(user_id__in=linked_user_ids)

    # -----------------------------------------------------------
    # 📤 Serialize
    # -----------------------------------------------------------
    users = [
        {
            "id": cu.user.id,
            "username": cu.user.username,
            "email": cu.user.email,
            "is_active": cu.user.is_active,
        }
        for cu in qs
    ]

    return JsonResponse({
        "users": users
    })
