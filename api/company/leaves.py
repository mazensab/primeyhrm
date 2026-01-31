# ============================================================
# 🏢 Company Leave APIs — FINAL STABLE
# Primey HR Cloud
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import transaction

from employee_center.models import Employee
from company_manager.models import CompanyUser
from leave_center.models import LeaveRequest, LeaveType, LeaveBalance
from leave_center.engines import (
    LeaveRulesEngine,
    LeaveWorkflowEngine,
    LeaveApprovalEngine,
)

# ============================================================
# 🔐 Company Resolver (SINGLE SOURCE OF TRUTH)
# ============================================================
def _resolve_company(request):
    """
    Resolve company safely using CompanyUser
    Compatible with Primey multi-company design
    """
    cu = (
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
    return cu.company if cu else None


# ============================================================
# 👤 Employee Resolver (SAFE — NO user FK)
# ============================================================
def _resolve_employee(company):
    """
    Resolve employee safely without relying on User FK
    """
    return (
        Employee.objects
        .filter(company=company)
        .order_by("-id")
        .first()
    )


# ============================================================
# 📄 GET /api/company/leaves/requests/
# ============================================================
@login_required
@require_http_methods(["GET"])
def company_leave_requests(request):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "Company not resolved"}, status=403)

    qs = (
        LeaveRequest.objects
        .select_related("employee", "leave_type")
        .filter(employee__company=company)
        .order_by("-created_at")
    )

    return JsonResponse({
        "requests": [
            {
                "id": r.id,
                "employee_name": r.employee.full_name,
                "employee_id": r.employee.id,
                "type": r.leave_type.name,
                "from_date": r.start_date,
                "to_date": r.end_date,
                "status": r.status,
            }
            for r in qs
        ]
    })


# ============================================================
# ➕ POST /api/company/leaves/request/
# ============================================================
@login_required
@require_http_methods(["POST"])
@transaction.atomic
def create_leave_request(request):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "Company not resolved"}, status=403)

    employee = _resolve_employee(company)
    if not employee:
        return JsonResponse(
            {"error": "Employee not resolved"},
            status=400
        )

    leave_type_id = request.POST.get("leave_type_id")
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")
    reason = request.POST.get("reason", "")

    leave_type = get_object_or_404(
        LeaveType,
        id=leave_type_id,
        company=company,
        is_active=True,
    )

    # 🔐 Rules Validation
    LeaveRulesEngine.validate(
        employee=employee,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
    )

    # 🔁 Workflow
    leave_request = LeaveWorkflowEngine.create_request(
        employee=employee,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
    )

    return JsonResponse({
        "status": "created",
        "request_id": leave_request.id,
    })


# ============================================================
# ✅ POST /api/company/leaves/<id>/approve/
# ============================================================
@login_required
@require_http_methods(["POST"])
@transaction.atomic
def approve_leave(request, leave_id):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "Company not resolved"}, status=403)

    leave = get_object_or_404(
        LeaveRequest,
        id=leave_id,
        employee__company=company,
    )

    LeaveApprovalEngine.approve(
        leave_request=leave,
        approved_by=request.user,
    )

    return JsonResponse({"status": "approved"})


# ============================================================
# ❌ POST /api/company/leaves/<id>/reject/
# ============================================================
@login_required
@require_http_methods(["POST"])
@transaction.atomic
def reject_leave(request, leave_id):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "Company not resolved"}, status=403)

    leave = get_object_or_404(
        LeaveRequest,
        id=leave_id,
        employee__company=company,
    )

    LeaveApprovalEngine.reject(
        leave_request=leave,
        rejected_by=request.user,
    )

    return JsonResponse({"status": "rejected"})


# ============================================================
# 🧮 GET /api/company/leaves/balance/
# ============================================================
@login_required
@require_http_methods(["GET"])
def leave_balance(request):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "Company not resolved"}, status=403)

    employee = _resolve_employee(company)
    if not employee:
        return JsonResponse({"balances": []})

    balances = LeaveBalance.objects.filter(employee=employee)

    return JsonResponse({
        "balances": [
            {
                "leave_type": b.leave_type.name,
                "year": b.year,
                "balance": float(b.balance),
            }
            for b in balances
        ]
    })
