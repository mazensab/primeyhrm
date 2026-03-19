# ============================================================
# 📂 api/company/payroll/records.py
# 🧾 Payroll Record APIs — Phase 5.3
# 🔒 Snapshot Aware + Company Scoped + Audit Log
# ============================================================

from decimal import Decimal

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
# الهدف: الدفع مسموح لمن لديه generate أو approve (حسب قرارك)
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

    # ✅ إذا لا توجد أدوار نهائياً — اسمح مؤقتاً (وضع البناء)
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
                "employee__id",
                "employee__full_name",
                "run__status",
                "snapshot__net_salary",
            )
            .filter(run=run)
            .order_by("employee__full_name")
        )

        # 🔎 Filtering
        status_filter = request.GET.get("status")
        search = request.GET.get("search")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if search:
            queryset = queryset.filter(
                Q(employee__full_name__icontains=search)
            )

        # 📄 Pagination
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
            if use_snapshot and getattr(record, "snapshot", None):
                net_salary = record.snapshot.net_salary
            else:
                net_salary = record.net_salary

            results.append({
                "record_id": record.id,
                "employee_id": record.employee.id,
                "employee_name": record.employee.full_name,
                "net_salary": net_salary,
                "paid_amount": record.paid_amount,
                "remaining_amount": record.remaining_amount,
                "status": record.status,
                "run_status": run.status,
                "is_snapshot": use_snapshot,
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

        # 🧊 Snapshot Aware
        use_snapshot = run.status in ["APPROVED", "PAID"]
        source = record.snapshot if (use_snapshot and getattr(record, "snapshot", None)) else record

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
                "remaining_amount": record.remaining_amount,
                "payment_method": record.payment_method,
                "paid_at": record.paid_at,
            },

            "breakdown": source.breakdown or {},

            "meta": {
                "is_snapshot": use_snapshot,
                "is_fully_paid": record.is_fully_paid,
                "can_pay": run.status == "APPROVED" and record.status != "PAID",
            },

            # 🆕 Audit Log
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

        # ✅ RBAC: generate OR approve (حسب قرارك)
        if not _has_payroll_generate_or_approve(request.user, company):
            return Response({"error": "PERMISSION_DENIED"}, status=status.HTTP_403_FORBIDDEN)

        record = get_object_or_404(
            PayrollRecord.objects.select_related("run", "employee").select_for_update(),
            id=record_id,
            run__company=company,
        )

        run = record.run

        # 🔒 Run must be APPROVED
        approved_value = getattr(PayrollRun.Status, "APPROVED", "APPROVED")
        if run.status != approved_value and run.status != "APPROVED":
            return Response(
                {"detail": "PayrollRun must be APPROVED before payment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 📥 Read payload (Frontend يرسل method + amount)
        amount_raw = request.data.get("amount")
        method = request.data.get("method") or request.data.get("payment_method")

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

        remaining = record.remaining_amount
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

        # 💰 Apply payment (Partial supported)
        mark_payroll_record_paid(
            record=record,
            payment_method=method,
            amount=amount,
            user=request.user,
        )

        record.refresh_from_db()

        return Response(
            {
                "detail": "Payment applied successfully.",
                "record_status": record.status,
                "paid_amount": record.paid_amount,
                "remaining_amount": record.remaining_amount,
            },
            status=status.HTTP_200_OK,
        )