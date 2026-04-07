# ============================================================
# 🏢 Company Leave APIs — FINAL STABLE
# Mham Cloud
# Version: V2.1 Notification Center Cleanup ✅
# ============================================================

import json
import logging

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from company_manager.models import CompanyUser
from employee_center.models import Employee
from leave_center.engines import (
    LeaveApprovalEngine,
    LeaveRulesEngine,
    LeaveWorkflowEngine,
)
from leave_center.models import (
    CompanyAnnualLeavePolicy,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
)
from notification_center.services_hr import (
    notify_leave_requested,
    notify_leave_approved,
    notify_leave_rejected,
)

logger = logging.getLogger(__name__)


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
# 🏛️ Enterprise Strict — HR/Admin can create for others
# ============================================================
@login_required
@require_http_methods(["POST"])
@transaction.atomic
def create_leave_request(request):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "Company not resolved"}, status=403)

    # ======================================================
    # 🔐 Resolve CompanyUser + Role (RBAC Core)
    # ======================================================
    company_user = (
        CompanyUser.objects
        .select_related("company", "role")
        .filter(user=request.user, company=company, is_active=True)
        .first()
    )

    if not company_user:
        return JsonResponse(
            {"error": "Company user not resolved"},
            status=403
        )

    role = getattr(company_user, "role", None)
    role_permissions = getattr(role, "permissions", []) or []

    # Normalize permissions
    if isinstance(role_permissions, dict):
        role_permissions = list(role_permissions.keys())

    # ======================================================
    # 📥 Request Data
    # ======================================================
    employee_id = request.POST.get("employee_id")
    leave_type_id = request.POST.get("leave_type_id")
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")
    reason = request.POST.get("reason", "")

    if not leave_type_id or not start_date or not end_date:
        return JsonResponse(
            {"error": "Missing required fields"},
            status=400
        )

    # ======================================================
    # 👤 Employee Resolution (Enterprise Logic)
    # ======================================================
    # 🎭 CASE 1: Admin / HR → can select any employee
    can_create_for_others = (
        role and (
            role.is_system_role or
            "leaves.create_for_others" in role_permissions or
            "hr.manage_leaves" in role_permissions
        )
    )

    if employee_id and can_create_for_others:
        employee = get_object_or_404(
            Employee,
            id=employee_id,
            company=company,
        )
    else:
        # 👤 CASE 2: Normal Employee → only for himself
        employee = (
            Employee.objects
            .filter(user=request.user, company=company)
            .first()
        )

        if not employee:
            return JsonResponse(
                {"error": "Employee profile not found for user"},
                status=400
            )

    # ======================================================
    # 🏷 Leave Type (Company Scoped — Multi-Tenant Safe)
    # ======================================================
    leave_type = get_object_or_404(
        LeaveType,
        id=leave_type_id,
        company=company,
        is_active=True,
    )

    # ======================================================
    # 🔐 Rules Validation (Engine Safe)
    # ======================================================
    LeaveRulesEngine.validate(
        employee=employee,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
    )

    # ======================================================
    # 🔁 Workflow Engine (Source of Truth)
    # ======================================================
    leave_request = LeaveWorkflowEngine.create_request(
        employee=employee,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
    )

    # ======================================================
    # 🔔 Notification Center Hook — Leave Submitted
    # المسار الرسمي الموحد بدل الإرسال المباشر من الـ API
    # ======================================================
    try:
        notify_leave_requested(
            leave_request,
            send_email=False,
            send_whatsapp=True,
        )
    except Exception:
        logger.exception("⚠ Leave submit notification hook failed (non-blocking)")

    return JsonResponse({
        "status": "created",
        "request_id": leave_request.id,
        "employee_id": employee.id,
    })


# ============================================================
# ✅ POST /api/company/leaves/<id>/approve/
# 🏛 Enterprise RBAC + Engine Ready (Attendance/Payroll Safe)
# ============================================================
@login_required
@require_http_methods(["POST"])
@transaction.atomic
def approve_leave(request, leave_id):
    """
    Enterprise Approval Logic:
    - Multi-Tenant Safe (Company Scoped)
    - RBAC Hierarchy Guard (Admin / Manager)
    - Idempotent Approval
    - Engine Driven (No Direct Logic)
    - Future Ready: Attendance + Payroll Hook (SAFE — Not Forced)
    """

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "Company not resolved"}, status=403)

    # =====================================================
    # 🔐 RBAC Guard — Enterprise Hierarchy
    # Admin / Manager only can approve leaves
    # =====================================================
    company_user = (
        CompanyUser.objects
        .select_related("company")
        .filter(
            user=request.user,
            company=company,
            is_active=True,
        )
        .first()
    )

    if not company_user:
        return JsonResponse(
            {"error": "Unauthorized company context"},
            status=403
        )

    # ملاحظة: متوافق مع Primey RBAC (role / is_owner / is_admin)
    role_name = getattr(company_user, "role", None)
    role_name = str(role_name).lower() if role_name else ""

    is_admin_like = (
        getattr(company_user, "is_owner", False)
        or getattr(company_user, "is_admin", False)
        or role_name in ["admin", "hr_manager", "manager"]
    )

    if not is_admin_like:
        return JsonResponse(
            {"error": "Permission denied (RBAC)"},
            status=403
        )

    # =====================================================
    # 📄 Load Leave (Company Scoped — Multi-Tenant Safe)
    # =====================================================
    leave = get_object_or_404(
        LeaveRequest,
        id=leave_id,
        employee__company=company,
    )

    # =====================================================
    # 🛡 Idempotency Guard (Enterprise Safety)
    # =====================================================
    if leave.status == "approved":
        return JsonResponse({
            "status": "approved",
            "idempotent": True,
            "message": "الطلب معتمد مسبقًا."
        })

    # =====================================================
    # 🧠 Approval Engine (Single Source of Truth)
    # =====================================================
    LeaveApprovalEngine.approve(
        leave_request=leave,
        approved_by=request.user,
    )

    # =====================================================
    # 🔄 Refresh Leave Snapshot
    # =====================================================
    leave.refresh_from_db()

    # =====================================================
    # 🔔 Notification Center Hook
    # المسار الرسمي الموحد بدل الإرسال المباشر من الـ API
    # =====================================================
    try:
        notify_leave_approved(
            leave,
            send_email=True,
            send_whatsapp=True,
        )
    except Exception:
        logger.exception("⚠ Leave approval notification hook failed (non-blocking)")

    # =====================================================
    # 🔗 FUTURE HOOK (SAFE — Enterprise Ready)
    # Attendance + Payroll Absence Engine
    # ⚠️ لا يغيّر السلوك الحالي — فقط تجهيز معماري
    # =====================================================
    try:
        # تجهيز للربط المستقبلي دون فرض التنفيذ الآن
        # Phase Ready:
        # - Attendance Engine (mark leave days)
        # - Payroll Absence Deduction Engine
        if hasattr(leave, "start_date") and hasattr(leave, "end_date"):
            # سيتم ربطه لاحقًا بـ:
            # WorkdayEngine / Absence Engine
            pass

    except Exception:
        # لا نكسر الموافقة في حال فشل أي Hook مستقبلي
        logger.exception("⚠ Leave Approval Hook Warning (non-blocking)")

    # =====================================================
    # 📦 Final Response (Frontend + Audit Ready)
    # =====================================================
    return JsonResponse({
        "status": "approved",
        "leave_id": leave.id,
        "employee_id": leave.employee_id,
        "approved_by": request.user.id,
    })


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

    rejection_reason = (
        request.POST.get("reason")
        or request.POST.get("rejection_reason")
        or ""
    ).strip()

    LeaveApprovalEngine.reject(
        leave_request=leave,
        rejected_by=request.user,
    )

    leave.refresh_from_db()

    # =====================================================
    # 🔔 Notification Center Hook
    # المسار الرسمي الموحد بدل الإرسال المباشر من الـ API
    # =====================================================
    try:
        notify_leave_rejected(
            leave,
            send_email=True,
            send_whatsapp=True,
        )
    except Exception:
        logger.exception("⚠ Leave rejection notification hook failed (non-blocking)")

    return JsonResponse({
        "status": "rejected",
        "leave_id": leave.id,
        "employee_id": leave.employee_id,
        "rejection_reason": rejection_reason,
    })


# ============================================================
# 🧮 GET /api/company/leaves/balance/  (FIXED — FINAL STABLE)
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

    # 🧠 Multi-Tenant Safe Query
    balance = (
        LeaveBalance.objects
        .filter(employee=employee, company=company)
        .order_by("-id")
        .first()
    )

    if not balance:
        return JsonResponse({"balances": []})

    # 🏛️ Saudi Labour Law Compatible Structured Balances
    balances_payload = [
        {"leave_type": "Annual", "balance": float(balance.annual_balance)},
        {"leave_type": "Sick", "balance": float(balance.sick_balance)},
        {"leave_type": "Maternity", "balance": float(balance.maternity_balance)},
        {"leave_type": "Marriage", "balance": float(balance.marriage_balance)},
        {"leave_type": "Death", "balance": float(balance.death_balance)},
        {"leave_type": "Hajj", "balance": float(balance.hajj_balance)},
        {"leave_type": "Study", "balance": float(balance.study_balance)},
        {"leave_type": "Unpaid", "balance": float(balance.unpaid_balance)},
    ]

    return JsonResponse({
        "balances": balances_payload,
        "last_reset": balance.last_reset,
        "auto_reset_enabled": balance.auto_reset_enabled,
    })


# ============================================================
# 📄 GET /api/company/leaves/types/
# ============================================================
@login_required
@require_http_methods(["GET"])
def company_leave_types(request):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "Company not resolved"}, status=403)

    types = LeaveType.objects.filter(company=company)

    return JsonResponse({
        "types": [
            {"id": t.id, "name": t.name}
            for t in types
        ]
    })


# ============================================================
# 🏢 GET / PATCH /api/company/leaves/annual-policy/
# 🔵 Phase F.5.2 — Company Annual Leave Policy API
# Multi-Tenant Safe — Production Ready
# ============================================================
@login_required
@require_http_methods(["GET", "PATCH"])
@transaction.atomic
def company_annual_leave_policy(request):
    """
    Company Scoped Annual Leave Policy
    ✔ Auto-Provision
    ✔ RBAC Guard
    ✔ Multi-Tenant Safe
    ✔ Atomic Updates
    """

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "Company not resolved"}, status=403)

    # ======================================================
    # 🔐 RBAC Guard
    # ======================================================
    company_user = (
        CompanyUser.objects
        .select_related("company")
        .filter(
            user=request.user,
            company=company,
            is_active=True,
        )
        .first()
    )

    if not company_user:
        return JsonResponse({"error": "Unauthorized company context"}, status=403)

    role_name = getattr(company_user, "role", None)
    role_name = str(role_name).lower() if role_name else ""

    is_admin_like = (
        getattr(company_user, "is_owner", False)
        or getattr(company_user, "is_admin", False)
        or role_name in ["admin", "hr_manager", "manager"]
    )

    if not is_admin_like:
        return JsonResponse({"error": "Permission denied (RBAC)"}, status=403)

    # ======================================================
    # 🧠 Auto Provision (Safe)
    # ======================================================
    policy, created = CompanyAnnualLeavePolicy.objects.get_or_create(
        company=company,
        defaults={
            "annual_days": 21,
            "carry_forward_enabled": True,
            "carry_forward_limit": 15,
            "reset_month": 1,
            "is_active": True,
        }
    )

    # ======================================================
    # 📥 GET
    # ======================================================
    if request.method == "GET":
        return JsonResponse({
            "annual_days": policy.annual_days,
            "carry_forward_enabled": policy.carry_forward_enabled,
            "carry_forward_limit": policy.carry_forward_limit,
            "reset_month": policy.reset_month,
            "is_active": policy.is_active,
        })

    # ======================================================
    # ✏ PATCH (Atomic)
    # ======================================================
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    allowed_fields = [
        "annual_days",
        "carry_forward_enabled",
        "carry_forward_limit",
        "reset_month",
        "is_active",
    ]

    update_fields = []

    for field in allowed_fields:
        if field in data:
            setattr(policy, field, data[field])
            update_fields.append(field)

    if update_fields:
        policy.save(update_fields=update_fields + ["updated_at"])

    return JsonResponse({
        "status": "updated",
        "annual_days": policy.annual_days,
        "carry_forward_enabled": policy.carry_forward_enabled,
        "carry_forward_limit": policy.carry_forward_limit,
        "reset_month": policy.reset_month,
        "is_active": policy.is_active,
    })