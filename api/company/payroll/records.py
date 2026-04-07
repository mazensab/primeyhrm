# ============================================================
# 📂 api/company/payroll/records.py
# 🧾 Payroll Record APIs — Phase 5.5
# 🔒 Snapshot Aware + Company Scoped + Audit Log
# ✅ Pro-Rata Aware + Safer Remaining Amount Logic
# ✅ Notification Center First
# ============================================================

from decimal import Decimal
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.db import transaction

from payroll_center.models import (
    PayrollRun,
    PayrollRecord,
    PayrollRecordHistory,
)

from payroll_center.services.reporting import get_employee_payroll_ledger
from payroll_center.services.payroll_engine import mark_payroll_record_paid

from company_manager.models import CompanyUser
from notification_center.services_hr import notify_payroll_record_paid

logger = logging.getLogger(__name__)


# ============================================================
# 🔧 Helpers
# ============================================================

def _to_decimal(value, default: str = "0.00") -> Decimal:
    try:
        if value is None or value == "":
            return Decimal(default)
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _safe_remaining_amount(record, source=None) -> Decimal:
    """
    نحسب المتبقي بشكل آمن حتى لو لم يكن الحقل property أو لم يكن متزامنًا.
    """
    source_obj = source or record

    net_salary = _to_decimal(getattr(source_obj, "net_salary", None), "0.00")
    paid_amount = _to_decimal(getattr(record, "paid_amount", None), "0.00")

    remaining = net_salary - paid_amount
    if remaining < Decimal("0.00"):
        return Decimal("0.00")
    return remaining.quantize(Decimal("0.01"))


def _can_pay_record(run, record, source=None) -> bool:
    if str(getattr(run, "status", "")).upper() != "APPROVED":
        return False

    if str(getattr(record, "status", "")).upper() == "PAID":
        return False

    return _safe_remaining_amount(record, source) > Decimal("0.00")


def _has_salary_content(source) -> bool:
    if not source:
        return False

    values = [
        getattr(source, "base_salary", 0),
        getattr(source, "allowance", 0),
        getattr(source, "bonus", 0),
        getattr(source, "overtime", 0),
        getattr(source, "deductions", 0),
        getattr(source, "net_salary", 0),
    ]
    return any(_to_decimal(v, "0.00") != Decimal("0.00") for v in values)


# ============================================================
# 🔐 Resolve Company
# ============================================================

def _resolve_company(user):
    cu = (
        CompanyUser.objects
        .select_related("company")
        .filter(user=user, is_active=True)
        .order_by("-id")
        .first()
    )
    return cu.company if cu else None


# ============================================================
# 🔐 RBAC Check — PAYROLL_CENTER.generate OR PAYROLL_CENTER.approve
# الهدف: الدفع مسموح لمن لديه generate أو approve
# ============================================================

def _has_payroll_generate_or_approve(user, company) -> bool:
    company_user = (
        CompanyUser.objects
        .prefetch_related("roles")
        .filter(company=company, user=user, is_active=True)
        .first()
    )

    if not company_user:
        return False

    if company_user.roles.count() == 0:
        return True

    for role in company_user.roles.all():
        perms = role.permissions or {}
        payroll_module = perms.get("PAYROLL_CENTER", {}) or {}

        if payroll_module.get("generate", False) or payroll_module.get("approve", False):
            return True

    return False


# ============================================================
# 📋 Records List API
# GET /api/company/payroll/runs/<id>/records/
# ============================================================

class PayrollRunRecordsListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, run_id):

        company = _resolve_company(request.user)
        if not company:
            return Response(
                {"detail": "Company context not found"},
                status=status.HTTP_403_FORBIDDEN,
            )

        run = get_object_or_404(
            PayrollRun,
            id=run_id,
            company=company,
        )

        queryset = (
            PayrollRecord.objects
            .select_related("employee", "run", "snapshot")
            .only(
                "id",
                "status",
                "paid_amount",
                "net_salary",
                "base_salary",
                "allowance",
                "bonus",
                "overtime",
                "deductions",
                "breakdown",
                "employee__id",
                "employee__full_name",
                "run__status",
                "snapshot__net_salary",
                "snapshot__base_salary",
                "snapshot__allowance",
                "snapshot__bonus",
                "snapshot__overtime",
                "snapshot__deductions",
                "snapshot__breakdown",
            )
            .filter(run=run)
            .order_by("employee__full_name")
        )

        status_filter = request.GET.get("status")
        search = request.GET.get("search")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if search:
            queryset = queryset.filter(
                Q(employee__full_name__icontains=search)
            )

        try:
            page = max(int(request.GET.get("page", 1)), 1)
        except ValueError:
            page = 1

        try:
            page_size = int(request.GET.get("page_size", 20))
        except ValueError:
            page_size = 20

        page_size = min(max(page_size, 1), 100)

        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()
        records = queryset[start:end]

        use_snapshot = run.status in ["APPROVED", "PAID"]

        results = []

        for record in records:
            source = record.snapshot if (use_snapshot and getattr(record, "snapshot", None)) else record
            remaining_amount = _safe_remaining_amount(record, source)
            can_pay = _can_pay_record(run, record, source)

            results.append({
                "record_id": record.id,
                "employee_id": record.employee.id,
                "employee_name": record.employee.full_name,
                "net_salary": source.net_salary,
                "paid_amount": record.paid_amount,
                "remaining_amount": remaining_amount,
                "status": record.status,
                "run_status": run.status,
                "is_snapshot": use_snapshot,
                "can_pay": can_pay,
                "can_print": _has_salary_content(source),
                "can_view_slip": _has_salary_content(source),
            })

        return Response({
            "run_id": run.id,
            "run_status": run.status,
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "results": results,
        })


# ============================================================
# 📄 Record Detail API (WITH AUDIT LOG)
# GET /api/company/payroll/records/<id>/
# ============================================================

class PayrollRecordDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):

        company = _resolve_company(request.user)
        if not company:
            return Response(
                {"detail": "Company context not found"},
                status=status.HTTP_403_FORBIDDEN,
            )

        record = get_object_or_404(
            PayrollRecord.objects
            .select_related("employee", "run", "snapshot")
            .prefetch_related(
                Prefetch(
                    "history_logs",
                    queryset=PayrollRecordHistory.objects
                    .select_related("user")
                    .only(
                        "id",
                        "action",
                        "notes",
                        "created_at",
                        "user__id",
                        "user__username",
                    )
                    .order_by("-created_at")
                )
            )
            .only(
                "id",
                "status",
                "paid_amount",
                "payment_method",
                "paid_at",
                "net_salary",
                "base_salary",
                "allowance",
                "bonus",
                "overtime",
                "deductions",
                "breakdown",
                "employee__id",
                "employee__full_name",
                "run__id",
                "run__month",
                "run__status",
                "snapshot__base_salary",
                "snapshot__allowance",
                "snapshot__bonus",
                "snapshot__overtime",
                "snapshot__deductions",
                "snapshot__net_salary",
                "snapshot__breakdown",
            ),
            id=record_id,
            run__company=company,
        )

        run = record.run
        use_snapshot = run.status in ["APPROVED", "PAID"]
        source = record.snapshot if (use_snapshot and getattr(record, "snapshot", None)) else record

        remaining_amount = _safe_remaining_amount(record, source)
        can_pay = _can_pay_record(run, record, source)
        can_print = _has_salary_content(source)

        response_data = {
            "record_id": record.id,
            "employee": {
                "id": record.employee.id,
                "full_name": record.employee.full_name,
            },
            "run": {
                "id": run.id,
                "month": run.month.strftime("%Y-%m"),
                "status": run.status,
            },
            "salary": {
                "base_salary": source.base_salary,
                "allowance": source.allowance,
                "bonus": source.bonus,
                "overtime": source.overtime,
                "deductions": source.deductions,
                "net_salary": source.net_salary,
            },
            "payment": {
                "status": record.status,
                "paid_amount": record.paid_amount,
                "remaining_amount": remaining_amount,
                "payment_method": record.payment_method,
                "paid_at": record.paid_at,
            },
            "breakdown": source.breakdown or {},
            "meta": {
                "is_snapshot": use_snapshot,
                "is_fully_paid": record.is_fully_paid,
                "can_pay": can_pay,
                "can_print": can_print,
                "can_view_slip": can_print,
                "has_remaining_amount": remaining_amount > Decimal("0.00"),
            },
            "history": [
                {
                    "id": log.id,
                    "action": log.action,
                    "notes": log.notes,
                    "created_at": log.created_at,
                    "user": (
                        {
                            "id": log.user.id,
                            "username": log.user.username,
                        }
                        if log.user else None
                    ),
                }
                for log in record.history_logs.all()
            ]
        }

        return Response(response_data, status=status.HTTP_200_OK)


# ============================================================
# 🧾 Ledger API
# GET /api/company/payroll/records/<id>/ledger/
# ============================================================

class PayrollRecordLedgerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):

        company = _resolve_company(request.user)
        if not company:
            return Response(
                {"detail": "Company context not found"},
                status=status.HTTP_403_FORBIDDEN,
            )

        record = get_object_or_404(
            PayrollRecord.objects.select_related("run", "employee"),
            id=record_id,
            run__company=company,
        )

        ledger_data = get_employee_payroll_ledger(record)

        return Response(ledger_data, status=status.HTTP_200_OK)


# ============================================================
# 💵 Pay Single Payroll Record (Partial Payment Enabled)
# POST /api/company/payroll/records/<id>/pay/
# ============================================================

class PayrollRecordPayAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, record_id):

        company = _resolve_company(request.user)
        if not company:
            return Response({"error": "NO_COMPANY"}, status=status.HTTP_403_FORBIDDEN)

        if not _has_payroll_generate_or_approve(request.user, company):
            return Response({"error": "PERMISSION_DENIED"}, status=status.HTTP_403_FORBIDDEN)

        record = get_object_or_404(
            PayrollRecord.objects.select_related("run", "employee", "snapshot").select_for_update(),
            id=record_id,
            run__company=company,
        )

        run = record.run
        use_snapshot = run.status in ["APPROVED", "PAID"]
        source = record.snapshot if (use_snapshot and getattr(record, "snapshot", None)) else record

        approved_value = getattr(PayrollRun.Status, "APPROVED", "APPROVED")
        if run.status != approved_value and run.status != "APPROVED":
            return Response(
                {"detail": "PayrollRun must be APPROVED before payment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount_raw = request.data.get("amount")
        method = request.data.get("method") or request.data.get("payment_method")
        reference = (request.data.get("reference") or "").strip()
        notes = (request.data.get("notes") or "").strip()

        if amount_raw is None:
            return Response(
                {"detail": "Payment amount is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = Decimal(str(amount_raw))
        except Exception:
            return Response(
                {"detail": "Invalid payment amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount <= 0:
            return Response(
                {"detail": "Payment amount must be greater than zero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        remaining = _safe_remaining_amount(record, source)
        if remaining <= 0:
            return Response(
                {"detail": "No remaining amount to pay."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount > remaining:
            return Response(
                {"detail": "Payment exceeds remaining amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if method not in ["CASH", "BANK"]:
            return Response(
                {"detail": "Invalid payment method."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if method == "BANK" and not reference:
            return Response(
                {"detail": "Transfer reference is required for bank payment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mark_payroll_record_paid(
            record=record,
            payment_method=method,
            amount=amount,
            user=request.user,
        )

        extra_notes = []
        if reference:
            extra_notes.append(f"reference={reference}")
        if notes:
            extra_notes.append(f"notes={notes}")

        if extra_notes:
            PayrollRecordHistory.objects.create(
                payroll_record=record,
                user=request.user,
                action="payment_note",
                notes=" | ".join(extra_notes),
            )

        record.refresh_from_db()
        refreshed_source = record.snapshot if (use_snapshot and getattr(record, "snapshot", None)) else record
        refreshed_remaining = _safe_remaining_amount(record, refreshed_source)

        try:
            notify_payroll_record_paid(
                record,
                send_email_to_employee=True,
                send_email_to_managers=False,
            )
        except Exception:
            logger.exception(
                "⚠ Payroll paid notification hook failed (non-blocking) | record=%s",
                record.id,
            )

        return Response(
            {
                "detail": "Payment applied successfully.",
                "record_status": record.status,
                "paid_amount": record.paid_amount,
                "remaining_amount": refreshed_remaining,
                "payment_method": method,
                "reference": reference or None,
                "notes": notes or None,
                "can_pay": _can_pay_record(run, record, refreshed_source),
            },
            status=status.HTTP_200_OK,
        )