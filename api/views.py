from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import localdate
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import ensure_csrf_cookie

# ====================== MODELS ======================
from company_manager.models import Company, CompanyUser
from employee_center.models import Employee
from payroll_center.models import PayrollRecord
from leave_center.models import LeaveRequest
from attendance_center.models import AttendanceRecord


# ============================================================
# 🔵 Health Check (Public)
# ============================================================
def health_check(request):
    """
    API فحص سريع لحالة النظام
    """
    return JsonResponse(
        {
            "status": "ok",
            "service": "Primey API Gateway V3",
        },
        status=200,
    )


# ============================================================
# 🟣 Dashboard Overview API — Company Owner
# ============================================================
def dashboard_overview(request):
    """
    📊 ملخص سريع لحالة الشركة / النظام
    """

    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)

    today = localdate()

    try:
        total_companies = Company.objects.count()
    except Exception:
        total_companies = 0

    try:
        total_employees = Employee.objects.count()
    except Exception:
        total_employees = 0

    try:
        attendance_today = AttendanceRecord.objects.filter(date=today).count()
    except Exception:
        attendance_today = 0

    try:
        payroll_records = PayrollRecord.objects.count()
    except Exception:
        payroll_records = 0

    try:
        pending_leaves = LeaveRequest.objects.filter(status="pending").count()
    except Exception:
        pending_leaves = 0

    return JsonResponse(
        {
            "status": "success",
            "metrics": {
                "companies": total_companies,
                "employees": total_employees,
                "attendance_today": attendance_today,
                "payroll_records": payroll_records,
                "pending_leaves": pending_leaves,
            },
        },
        status=200,
    )


# ============================================================
# 🟢 Company List API
# ============================================================
def company_list(request):
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)

    companies = Company.objects.all().values(
        "id",
        "name",
        "domain",
        "is_active",
        "created_at",
    )

    return JsonResponse(
        {
            "status": "success",
            "companies": list(companies),
        },
        status=200,
    )


# ============================================================
# 🟡 Company Detail API
# ============================================================
def company_detail(request, company_id):
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)

    try:
        company = Company.objects.get(id=company_id)
    except ObjectDoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Company not found"},
            status=404,
        )

    return JsonResponse(
        {
            "status": "success",
            "company": {
                "id": str(company.id),
                "name": company.name,
                "domain": company.domain,
                "is_active": company.is_active,
                "created_at": company.created_at,
            },
        },
        status=200,
    )


# ============================================================
# 🟦 Team Members API
# ============================================================
def company_team(request):
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)

    team = CompanyUser.objects.select_related("user", "role")

    data = [
        {
            "id": cu.id,
            "name": cu.user.get_full_name() or cu.user.username,
            "email": cu.user.email,
            "role": cu.role.name if cu.role else "Member",
        }
        for cu in team
    ]

    return JsonResponse(
        {
            "status": "success",
            "team": data,
        },
        status=200,
    )


# ============================================================
# 🟩 Recent Payments API
# ============================================================
def recent_payments(request):
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)

    records = (
        PayrollRecord.objects
        .select_related("employee")
        .order_by("-created_at")[:20]
    )

    data = [
        {
            "id": str(record.id),
            "employee": (
                record.employee.full_name
                if record.employee else "Unknown"
            ),
            "email": (
                record.employee.email
                if record.employee else ""
            ),
            "amount": float(record.net_salary or 0),
            "status": "success",
            "date": record.created_at,
        }
        for record in records
    ]

    return JsonResponse(
        {
            "status": "success",
            "payments": data,
        },
        status=200,
    )


# ============================================================
# 🔐 WhoAmI — API SAFE
# ============================================================
@require_GET
def whoami(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"authenticated": False},
            status=200,
        )

    return JsonResponse(
        {
            "authenticated": True,
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "is_superuser": request.user.is_superuser,
        },
        status=200,
    )


# ============================================================
# 🔐 CSRF — API SAFE (FINAL / PRODUCTION READY)
# ============================================================
@require_GET
@ensure_csrf_cookie
def csrf(request):
    """
    CSRF bootstrap endpoint for Next.js
    - GET only
    - No auth
    - No redirect
    - Sets csrftoken cookie
    """
    return JsonResponse(
        {"status": "ok"},
        status=200,
    )
