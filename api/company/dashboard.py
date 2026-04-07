# ============================================================
# 🏢 Company Dashboard Snapshot API
# Mham Cloud — Enterprise Safe
# ============================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count

from employee_center.models import Employee, Contract
from attendance_center.models import AttendanceRecord
from payroll_center.models import PayrollRun


@login_required
def dashboard_overview(request):

    user = request.user
    company = getattr(user, "company", None)

    if not company:
        return JsonResponse({"error": "Company not found"}, status=400)

    today = timezone.now().date()

    # ========================================================
    # 👥 Employees
    # ========================================================
    employees_total = Employee.objects.filter(
        company=company
    ).count()

    # ========================================================
    # 📄 Active Contracts
    # ========================================================
    active_contracts = Contract.objects.filter(
        employee__company=company,
        is_active=True
    ).count()

    # ========================================================
    # 🟢 Today Attendance
    # ========================================================
    today_records = AttendanceRecord.objects.filter(
        employee__company=company,
        date=today
    )

    today_present = today_records.count()

    attendance_today = list(
        today_records.values(
            "employee__full_name",
            "check_in",
            "check_out",
            "status",
            "date",
        )[:10]
    )

    attendance_today = [
        {
            "employee": r["employee__full_name"],
            "check_in": r["check_in"],
            "check_out": r["check_out"],
            "status": r["status"],
            "date": r["date"],
        }
        for r in attendance_today
    ]

    # ========================================================
    # 💰 Payroll Status
    # ========================================================
    latest_run = PayrollRun.objects.filter(
        company=company
    ).order_by("-month").first()

    payroll_status = latest_run.status if latest_run else None

    return JsonResponse({
        "employees_total": employees_total,
        "active_contracts": active_contracts,
        "today_present": today_present,
        "payroll_status": payroll_status,
        "attendance_today": attendance_today,
    })