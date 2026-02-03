from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import localdate

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
    📊 ملخص سريع لحالة الشركة / النظام:
        - عدد الشركات
        - عدد الموظفين
        - حضور اليوم
        - سجلات الرواتب
        - الإجازات المعلقة
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
# 🟦 Team Members API — TeamMembersCard
# ============================================================
def company_team(request):
    """
    قائمة مختصرة بأعضاء الفريق (Company Users)
    """

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
# 🟩 Recent Payments API — LatestPayments Card
# ============================================================
def recent_payments(request):
    """
    آخر 20 سجل رواتب (كمصدر مؤقت للمدفوعات)
    """

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
            "status": "success",  # جاهز للربط الفعلي لاحقًا
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

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import ensure_csrf_cookie


# ============================================================================
# 🔐 WhoAmI — API SAFE (NO REDIRECT / NO ADMIN)
# ============================================================================
@require_GET
def whoami(request):
    """
    API ONLY:
    - لا redirect
    - لا HTML
    - JSON فقط
    - آمن لـ Next.js
    """

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "authenticated": False,
            },
            status=200,
        )

    return JsonResponse(
        {
            "authenticated": True,
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "is_superuser": request.user.is_superuser,
            # لو عندك Role مرتبط بالمستخدم
            "role": getattr(request.user, "role", None),
        },
        status=200,
    )


# ============================================================================
# 🔐 CSRF — API SAFE (COOKIE INIT)
# ============================================================================
@require_GET
@ensure_csrf_cookie
def csrf(request):
    """
    Endpoint مخصص لـ Next.js
    - ينشئ csrftoken cookie
    - لا يعتمد على admin
    """
    return JsonResponse(
        {
            "detail": "CSRF cookie set",
        },
        status=200,
    )

# ============================================================
# 🔐 CSRF API — SAFE / FINAL
# Primey HR Cloud
# ============================================================

from django.http import JsonResponse
from django.middleware.csrf import get_token


def csrf(request):
    """
    API endpoint to initialize CSRF cookie safely.
    - No auth required
    - No redirect
    - Sets csrftoken cookie
    """
    token = get_token(request)

    return JsonResponse(
        {
            "csrfToken": token,
        },
        status=200,
    )

from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"status": "ok"})
