# ============================================================
# 📂 api/company/payroll/runs.py
# 🏦 Payroll Run APIs — Phase 5.3 (Enhanced)
# 🔐 Company Scoped | Enterprise Safe
# ============================================================

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Count

from payroll_center.models import PayrollRun, PayrollRecord
from payroll_center.services.payroll_engine import (
    calculate_payroll_run,
    approve_payroll_run,
    reset_payroll_run,
    mark_payroll_record_paid,
)
from payroll_center.services.reporting import (
    get_payroll_run_financial_summary,
)

from company_manager.models import CompanyUser


# ============================================================
# 🔐 Resolve Company Context
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
# 📋 Run List API
# GET /api/company/payroll/runs/
# ============================================================

class PayrollRunListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        company = _resolve_company(request.user)
        if not company:
            return Response(
                {"detail": "Company context not found"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # -----------------------------------------------
        # 🔥 Annotate employees count (NO N+1)
        # -----------------------------------------------
        runs = (
            PayrollRun.objects
            .filter(company=company)
            .annotate(total_employees=Count("records"))
            .order_by("-month")
        )

        results = []

        for run in runs:
            summary = get_payroll_run_financial_summary(run)

            results.append({
                "id": run.id,
                "month": run.month.strftime("%Y-%m"),
                "status": run.status,
                "total_net": summary["amounts"]["total_net"],
                "progress_percent": summary["progress_percent"],
                "accounting_consistency": summary["accounting_consistency"],

                # ✅ NEW FIELD
                "total_employees": run.total_employees,
            })

        return Response(results, status=status.HTTP_200_OK)


# ============================================================
# ➕ Create Payroll Run API
# POST /api/company/payroll/runs/create/
# ============================================================

from datetime import datetime


class PayrollRunCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        company = _resolve_company(request.user)
        if not company:
            return Response(
                {"detail": "Company context not found"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not isinstance(request.data, dict):
            return Response(
                {"detail": "Invalid payload format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        month_str = request.data.get("month")
        if not month_str:
            return Response(
                {"detail": "Month is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            month_date = datetime.strptime(month_str, "%Y-%m").date()
            month_date = month_date.replace(day=1)
        except ValueError:
            return Response(
                {"detail": "Invalid month format. Use YYYY-MM."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exists = PayrollRun.objects.filter(
            company=company,
            month=month_date,
        ).exists()

        if exists:
            return Response(
                {"detail": "Payroll run for this month already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        run = PayrollRun.objects.create(
            company=company,
            month=month_date,
            status=PayrollRun.Status.DRAFT,
        )

        return Response(
            {
                "run_id": run.id,
                "month": run.month.strftime("%Y-%m"),
                "status": run.status,
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# 📊 Run Detail API
# GET /api/company/payroll/runs/<id>/
# ============================================================

class PayrollRunDetailAPIView(APIView):
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

        summary = get_payroll_run_financial_summary(run)

        return Response(summary, status=status.HTTP_200_OK)


# ============================================================
# 🧮 Calculate Run API
# ============================================================

class PayrollRunCalculateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, run_id):

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

        try:
            calculate_payroll_run(run)
            return Response({"status": "CALCULATED"})
        except ValueError as ve:
            return Response(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ============================================================
# ✅ Approve Run API
# ============================================================

class PayrollRunApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, run_id):

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

        try:
            approve_payroll_run(run)
            return Response({"status": "APPROVED"})
        except ValueError as ve:
            return Response(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ============================================================
# 🔁 Reset Run API
# ============================================================

class PayrollRunResetAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, run_id):

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

        try:
            reset_payroll_run(run)
            return Response({"status": "RESET_TO_DRAFT"})
        except ValueError as ve:
            return Response(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ============================================================
# 💵 Pay Full Payroll Run (ENTERPRISE ATOMIC)
# ============================================================

class PayrollRunPayAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, run_id):

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

        if run.status != PayrollRun.Status.APPROVED:
            return Response(
                {"detail": "Only approved runs can be paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = PayrollRecord.objects.filter(run=run)

        for record in records:
            remaining = record.remaining_amount
            if remaining > 0:
                mark_payroll_record_paid(
                    record=record,
                    payment_method="BANK",
                    amount=remaining,
                )

        run.refresh_from_db()

        return Response(
            {"detail": "Payroll run paid successfully."},
            status=status.HTTP_200_OK,
        )