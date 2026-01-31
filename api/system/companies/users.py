# ===============================================================
# 👥 Company Users — SYSTEM API (FINAL & ALIGNED ✅)
# Primey HR Cloud
# ===============================================================
# ✔ System scoped (Super Admin)
# ✔ Employee = User model respected
# ✔ Used by Company Detail → Users Tab
# ===============================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from company_manager.models import CompanyUser


@login_required
@require_GET
def system_company_users(request, company_id):
    """
    GET /api/system/companies/<company_id>/users/
    """

    try:
        users = (
            CompanyUser.objects
            .select_related("user")
            .filter(company_id=company_id)
            .order_by("user__username")
            .values(
                "id",                      # CompanyUser ID
                "user__username",
                "user__email",
                "role",
                "is_active",
            )
        )

        return JsonResponse(
            {
                "status": "success",
                "results": list(users),
                "count": users.count(),
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "message": str(e),
            },
            status=500,
        )
