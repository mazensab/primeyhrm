# ============================================================
# 📂 api/company/payroll/runs.py
# 🏦 Payroll Run APIs — Phase 5.6 (Enhanced Payment Dialog Ready)
# 🔐 Company Scoped | Enterprise Safe
# 🌐 Localized API Messages (AR / EN)
# ✅ Pro-Rata Compatible Summary Payload
# ✅ Notification Center First
# ✅ Full Run Payment Method / Reference / Notes Support
# ============================================================

import logging
from datetime import datetime
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Count

from payroll_center.models import PayrollRun, PayrollRecord, PayrollRecordHistory
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
from notification_center.services_hr import (
    notify_payroll_record_paid,
    notify_payroll_run_paid,
)

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


def _safe_record_remaining_amount(record) -> Decimal:
    net_salary = _to_decimal(getattr(record, "net_salary", None), "0.00")
    paid_amount = _to_decimal(getattr(record, "paid_amount", None), "0.00")
    remaining = net_salary - paid_amount
    if remaining < Decimal("0.00"):
        return Decimal("0.00")
    return remaining.quantize(Decimal("0.01"))


def _build_run_response_payload(run, summary: dict) -> dict:
    amounts = summary.get("amounts", {}) or {}
    records_block = summary.get("records", {}) or {}

    total_records = records_block.get("total", 0)
    paid_records = records_block.get("paid", 0)
    pending_records = records_block.get("pending", 0)

    partial_records = (
        PayrollRecord.objects
        .filter(run=run, status="PARTIAL")
        .count()
    )

    unpaid_records = max(int(pending_records) - int(partial_records), 0)

    total_net = amounts.get("total_net", Decimal("0.00"))
    total_paid = (
        amounts.get("total_paid")
        or amounts.get("paid_net")
        or Decimal("0.00")
    )
    total_remaining = (
        amounts.get("total_remaining")
        or amounts.get("pending_net")
        or Decimal("0.00")
    )

    return {
        "id": run.id,
        "run_id": run.id,
        "month": run.month.strftime("%Y-%m"),
        "status": run.status,
        "progress_percent": summary.get("progress_percent", 0),
        "accounting_consistency": summary.get("accounting_consistency", True),
        "amounts": {
            "total_net": total_net,
            "total_paid": total_paid,
            "total_remaining": total_remaining,
        },
        "counts": {
            "total_records": total_records,
            "paid_records": paid_records,
            "unpaid_records": unpaid_records,
            "partial_records": partial_records,
        },
        "records": records_block,
        "journals": summary.get("journals", {}) or {},
        "paid_percent": summary.get("paid_percent", 0),
    }


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
# 🌐 I18N Helpers
# ============================================================

def _is_arabic_request(request) -> bool:
    lang = ""

    try:
        lang = (getattr(request, "LANGUAGE_CODE", "") or "").lower().strip()
    except Exception:
        lang = ""

    if lang.startswith("ar"):
        return True

    accept_language = (
        request.headers.get("Accept-Language", "")
        or request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        or ""
    ).lower().strip()

    return accept_language.startswith("ar")


def _t(request, ar_text: str, en_text: str) -> str:
    return ar_text if _is_arabic_request(request) else en_text


def _localize_engine_error(request, message: str) -> str:
    if not message:
        return _t(request, "تعذر تنفيذ العملية.", "Failed to complete the operation.")

    if not _is_arabic_request(request):
        return message

    normalized = str(message).strip()

    if normalized.startswith("Payroll validation failed:"):
        details = normalized.replace("Payroll validation failed:", "", 1).strip()

        details = details.replace(" has no salary source", " لا يملك مصدر راتب")
        details = details.replace("Employee ", "الموظف ")
        details = details.replace("employees", "الموظفين")
        details = details.replace("employee", "الموظف")

        return f"فشل التحقق من الرواتب: {details}"

    known_map = {
        "Payroll run is already calculated.": "تم احتساب تشغيل الرواتب مسبقًا.",
        "Payroll run is already approved.": "تم اعتماد تشغيل الرواتب مسبقًا.",
        "Payroll run is already paid.": "تم دفع تشغيل الرواتب مسبقًا.",
        "Payroll run must be in DRAFT status.": "يجب أن تكون حالة تشغيل الرواتب مسودة أولًا.",
        "Payroll run must be in CALCULATED status.": "يجب أن تكون حالة تشغيل الرواتب محسوبة أولًا.",
        "Payroll run must be in APPROVED status.": "يجب أن تكون حالة تشغيل الرواتب معتمدة أولًا.",
        "No employees found for payroll calculation.": "لا يوجد موظفون متاحون لاحتساب الرواتب.",
        "No payroll records found.": "لا توجد سجلات رواتب.",
        "Payroll records already exist for this run.": "سجلات الرواتب موجودة مسبقًا لهذا التشغيل.",
        "Only approved runs can be paid.": "يمكن دفع التشغيلات المعتمدة فقط.",
        "Month is required": "الشهر مطلوب.",
        "Invalid payload format": "صيغة البيانات المرسلة غير صحيحة.",
        "Invalid month format. Use YYYY-MM.": "صيغة الشهر غير صحيحة. استخدم YYYY-MM.",
        "Payroll run for this month already exists.": "يوجد تشغيل رواتب لهذا الشهر مسبقًا.",
        "Company context not found": "تعذر العثور على سياق الشركة.",
        "Invalid payment method.": "طريقة الدفع غير صالحة.",
        "Transfer reference is required for bank payment.": "مرجع التحويل مطلوب عند اختيار التحويل البنكي.",
    }

    return known_map.get(normalized, normalized)


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
                {"detail": _t(request, "تعذر العثور على سياق الشركة.", "Company context not found")},
                status=status.HTTP_403_FORBIDDEN,
            )

        runs = (
            PayrollRun.objects
            .filter(company=company)
            .annotate(total_employees=Count("records"))
            .order_by("-month")
        )

        results = []

        for run in runs:
            summary = get_payroll_run_financial_summary(run)
            payload = _build_run_response_payload(run, summary)
            payload["total_employees"] = run.total_employees
            payload["total_net"] = payload["amounts"]["total_net"]
            results.append(payload)

        return Response(results, status=status.HTTP_200_OK)


# ============================================================
# ➕ Create Payroll Run API
# POST /api/company/payroll/runs/create/
# ============================================================

class PayrollRunCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        company = _resolve_company(request.user)
        if not company:
            return Response(
                {"detail": _t(request, "تعذر العثور على سياق الشركة.", "Company context not found")},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not isinstance(request.data, dict):
            return Response(
                {"detail": _t(request, "صيغة البيانات المرسلة غير صحيحة.", "Invalid payload format")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        month_str = request.data.get("month")
        if not month_str:
            return Response(
                {"detail": _t(request, "الشهر مطلوب.", "Month is required")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            month_date = datetime.strptime(month_str, "%Y-%m").date()
            month_date = month_date.replace(day=1)
        except ValueError:
            return Response(
                {"detail": _t(request, "صيغة الشهر غير صحيحة. استخدم YYYY-MM.", "Invalid month format. Use YYYY-MM.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exists = PayrollRun.objects.filter(
            company=company,
            month=month_date,
        ).exists()

        if exists:
            return Response(
                {"detail": _t(request, "يوجد تشغيل رواتب لهذا الشهر مسبقًا.", "Payroll run for this month already exists.")},
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
                {"detail": _t(request, "تعذر العثور على سياق الشركة.", "Company context not found")},
                status=status.HTTP_403_FORBIDDEN,
            )

        run = get_object_or_404(
            PayrollRun,
            id=run_id,
            company=company,
        )

        summary = get_payroll_run_financial_summary(run)
        payload = _build_run_response_payload(run, summary)

        return Response(payload, status=status.HTTP_200_OK)


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
                {"detail": _t(request, "تعذر العثور على سياق الشركة.", "Company context not found")},
                status=status.HTTP_403_FORBIDDEN,
            )

        run = get_object_or_404(
            PayrollRun,
            id=run_id,
            company=company,
        )

        try:
            calculate_payroll_run(run)
            return Response({
                "status": "CALCULATED",
                "detail": _t(request, "تم احتساب تشغيل الرواتب بنجاح.", "Payroll run calculated successfully."),
            })
        except ValueError as ve:
            return Response(
                {"error": _localize_engine_error(request, str(ve))},
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
                {"detail": _t(request, "تعذر العثور على سياق الشركة.", "Company context not found")},
                status=status.HTTP_403_FORBIDDEN,
            )

        run = get_object_or_404(
            PayrollRun,
            id=run_id,
            company=company,
        )

        try:
            approve_payroll_run(run)
            return Response({
                "status": "APPROVED",
                "detail": _t(request, "تم اعتماد تشغيل الرواتب بنجاح.", "Payroll run approved successfully."),
            })
        except ValueError as ve:
            return Response(
                {"error": _localize_engine_error(request, str(ve))},
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
                {"detail": _t(request, "تعذر العثور على سياق الشركة.", "Company context not found")},
                status=status.HTTP_403_FORBIDDEN,
            )

        run = get_object_or_404(
            PayrollRun,
            id=run_id,
            company=company,
        )

        try:
            reset_payroll_run(run)
            return Response({
                "status": "RESET_TO_DRAFT",
                "detail": _t(request, "تمت إعادة التشغيل إلى المسودة بنجاح.", "Payroll run reset to draft successfully."),
            })
        except ValueError as ve:
            return Response(
                {"error": _localize_engine_error(request, str(ve))},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ============================================================
# 💵 Pay Full Payroll Run (ENTERPRISE ATOMIC)
# يدعم الآن:
# - payment_method / method
# - reference
# - notes
# ============================================================

class PayrollRunPayAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, run_id):

        company = _resolve_company(request.user)
        if not company:
            return Response(
                {"detail": _t(request, "تعذر العثور على سياق الشركة.", "Company context not found")},
                status=status.HTTP_403_FORBIDDEN,
            )

        run = get_object_or_404(
            PayrollRun,
            id=run_id,
            company=company,
        )

        if run.status != PayrollRun.Status.APPROVED:
            return Response(
                {"detail": _t(request, "يمكن دفع التشغيلات المعتمدة فقط.", "Only approved runs can be paid.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment_method = (
            request.data.get("payment_method")
            or request.data.get("method")
            or "BANK"
        )
        payment_method = str(payment_method).strip().upper()

        reference = str(request.data.get("reference") or "").strip()
        notes = str(request.data.get("notes") or "").strip()

        if payment_method not in ["BANK", "CASH"]:
            return Response(
                {"detail": _t(request, "طريقة الدفع غير صالحة.", "Invalid payment method.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment_method == "BANK" and not reference:
            return Response(
                {"detail": _t(request, "مرجع التحويل مطلوب عند اختيار التحويل البنكي.", "Transfer reference is required for bank payment.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = (
            PayrollRecord.objects
            .select_related("employee", "run")
            .filter(run=run)
        )

        notification_sent_count = 0
        paid_records_count = 0

        for record in records:
            remaining = _safe_record_remaining_amount(record)
            if remaining > 0:
                mark_payroll_record_paid(
                    record=record,
                    payment_method=payment_method,
                    amount=remaining,
                    user=request.user,
                )

                paid_records_count += 1
                record.refresh_from_db()

                extra_notes = []
                if reference:
                    extra_notes.append(f"reference={reference}")
                if notes:
                    extra_notes.append(f"notes={notes}")

                if extra_notes:
                    PayrollRecordHistory.objects.create(
                        payroll_record=record,
                        user=request.user,
                        action="run_payment_note",
                        notes=" | ".join(extra_notes),
                    )

                try:
                    notify_payroll_record_paid(
                        record,
                        send_email_to_employee=True,
                        send_email_to_managers=False,
                    )
                    notification_sent_count += 1
                except Exception:
                    logger.exception(
                        "⚠ Payroll record notification hook failed (non-blocking) | run=%s | record=%s",
                        run.id,
                        record.id,
                    )

        run.refresh_from_db()
        final_summary = get_payroll_run_financial_summary(run)
        final_payload = _build_run_response_payload(run, final_summary)

        try:
            notify_payroll_run_paid(
                run,
                send_email_to_managers=True,
            )
        except Exception:
            logger.exception(
                "⚠ Payroll run notification hook failed (non-blocking) | run=%s",
                run.id,
            )

        return Response(
            {
                "detail": _t(request, "تم دفع تشغيل الرواتب بنجاح.", "Payroll run paid successfully."),
                "notifications_sent": notification_sent_count,
                "paid_records_count": paid_records_count,
                "payment_method": payment_method,
                "reference": reference or None,
                "notes": notes or None,
                "run": final_payload,
            },
            status=status.HTTP_200_OK,
        )