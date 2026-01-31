"""
====================================================================
📊 Company Activity Snapshot API (READ ONLY)
Primey HR Cloud
Version: V1.1 Ultra Stable
====================================================================
✔ Single Source of Truth
✔ Company Scoped
✔ Session Auth
✔ Defensive Queries
✔ NEVER raises 500
====================================================================
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from company_manager.models import CompanyUser
from employee_center.models import Employee, Contract
from attendance_center.models import AttendanceRecord


@login_required
def activity_snapshot(request):
    """
    ----------------------------------------------------------------
    🧭 Dashboard Snapshot (KPI ONLY)
    ----------------------------------------------------------------
    """

    # ------------------------------------------------------------
    # 🔐 Resolve Company (ABSOLUTELY SAFE)
    # ------------------------------------------------------------
    company_user = (
        CompanyUser.objects
        .select_related("company")
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
            {
                "company": None,
                "stats": {
                    "employees_total": 0,
                    "active_contracts": 0,
                    "today_present": 0,
                },
            },
            status=200,
        )

    company = company_user.company
    today = timezone.localdate()

    # ------------------------------------------------------------
    # 📊 KPIs (DEFENSIVE – NO ASSUMPTIONS)
    # ------------------------------------------------------------
    try:
        employees_total = Employee.objects.filter(company=company).count()
    except Exception:
        employees_total = 0

    try:
        active_contracts = Contract.objects.filter(
            company=company,
            is_active=True,
        ).count()
    except Exception:
        active_contracts = 0

    try:
        today_present = (
            AttendanceRecord.objects
            .filter(company=company)
            .values("employee")
            .distinct()
            .count()
        )
    except Exception:
        today_present = 0

    # ------------------------------------------------------------
    # ✅ Stable Response
    # ------------------------------------------------------------
    return JsonResponse(
        {
            "company": {
                "id": company.id,
                "name": company.name,
            },
            "stats": {
                "employees_total": employees_total,
                "active_contracts": active_contracts,
                "today_present": today_present,
            },
        },
        status=200,
    )
