from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from company_manager.models import CompanyUser
from employee_center.models import Employee


@login_required
def company_users_unlinked(request):
    """
    ============================================================
    👥 Company Users — Unlinked Only (FINAL STABLE)
    Primey HR Cloud
    ============================================================
    ✔ Company scoped (SAFE)
    ✔ Supports trial & existing users
    ✔ Excludes users already linked to Employee
    ✔ Compatible with Impersonation
    ✔ Aligned with Company APIs contract
    ============================================================
    """

    # ------------------------------------------------------------
    # 🔐 Resolve Company Context (ABSOLUTELY SAFE)
    # ------------------------------------------------------------
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
        # ❌ لا يوجد سياق شركة → لا نكسر الواجهة
        return JsonResponse(
            {
                "users": [],
                "status": "ok",
            }
        )

    company = company_user.company

    # ------------------------------------------------------------
    # 🔗 Users already linked to employees (exclude)
    # ------------------------------------------------------------
    linked_user_ids = (
        Employee.objects
        .filter(
            company=company,
            user__isnull=False,
        )
        .values_list("user_id", flat=True)
    )

    # ------------------------------------------------------------
    # 👥 Company Users (UNLINKED ONLY)
    # ------------------------------------------------------------
    users = (
        CompanyUser.objects
        .select_related("user")
        .filter(
            company=company,
            is_active=True,
            user__isnull=False,
        )
        .exclude(user_id__in=linked_user_ids)
        .order_by("user__username")
    )

    # ------------------------------------------------------------
    # 📤 Response
    # ------------------------------------------------------------
    return JsonResponse(
        {
            "users": [
                {
                    "id": cu.user.id,
                    "username": cu.user.username,
                    "email": cu.user.email,
                    "is_active": cu.user.is_active,
                }
                for cu in users
            ],
            "status": "ok",
        }
    )
