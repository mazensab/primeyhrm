# ============================================================
# 📂 api/system/payments/tap_success_lookup.py
# ✅ Tap Success Lookup
# Mham Cloud
# ------------------------------------------------------------
# الهدف:
# - استقبال tap_id من صفحة نجاح الدفع في الفرونت
# - محاولة ربط tap_id بفاتورة داخل النظام
# - إرجاع invoice_number + redirect_url
# - مناسب للتسجيل الخارجي بدون login
# ============================================================

from __future__ import annotations

import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from billing_center.models import (
    CompanyOnboardingTransaction,
    Invoice,
    Payment,
    PaymentTransaction,
)
from company_manager.models import Company


# ============================================================
# 🔧 Helpers
# ============================================================

def _clean_str(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _extract_draft_id_from_description(description: str) -> int | None:
    """
    مثال متوقع:
    Onboarding draft #12 - Tap checkout
    """
    description = _clean_str(description)
    if not description:
        return None

    match = re.search(r"draft\s*#?\s*(\d+)", description, re.IGNORECASE)
    if not match:
        return None

    try:
        return int(match.group(1))
    except Exception:
        return None


def _build_invoice_payload(
    invoice: Invoice,
    *,
    source: str,
    payment_tx: PaymentTransaction | None = None,
):
    return {
        "success": True,
        "status": "resolved",
        "source": source,
        "tap_id": _clean_str(payment_tx.transaction_id if payment_tx else ""),
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "invoice_status": invoice.status,
        "company_id": invoice.company.id if invoice.company else None,
        "company_name": invoice.company.name if invoice.company else None,
        "redirect_url": f"/system/invoices/{invoice.invoice_number}",
    }


# ============================================================
# 🔎 Main Resolver
# ============================================================

def _resolve_invoice_from_tap_id(tap_id: str):
    """
    ترتيب المحاولة:
    1) PaymentTransaction.transaction_id == tap_id ومعه invoice مباشر
    2) Payment.reference_number == tap_id
    3) استخراج draft_id من وصف PaymentTransaction ثم محاولة إيجاد آخر فاتورة للشركة
    """

    # --------------------------------------------------------
    # 1) Official local transaction by tap charge id
    # --------------------------------------------------------
    payment_tx = (
        PaymentTransaction.objects
        .select_related("invoice", "invoice__company", "company", "created_by")
        .filter(transaction_id=tap_id)
        .order_by("-id")
        .first()
    )

    if payment_tx and payment_tx.invoice:
        return _build_invoice_payload(
            payment_tx.invoice,
            source="payment_transaction.invoice",
            payment_tx=payment_tx,
        )

    # --------------------------------------------------------
    # 2) Direct payment reference lookup
    # --------------------------------------------------------
    payment = (
        Payment.objects
        .select_related("invoice", "invoice__company")
        .filter(reference_number=tap_id)
        .order_by("-id")
        .first()
    )

    if payment and payment.invoice:
        return {
            "success": True,
            "status": "resolved",
            "source": "payment.reference_number",
            "tap_id": tap_id,
            "invoice_id": payment.invoice.id,
            "invoice_number": payment.invoice.invoice_number,
            "invoice_status": payment.invoice.status,
            "company_id": payment.invoice.company.id if payment.invoice.company else None,
            "company_name": payment.invoice.company.name if payment.invoice.company else None,
            "redirect_url": f"/system/invoices/{payment.invoice.invoice_number}",
        }

    # --------------------------------------------------------
    # 3) Fallback by onboarding draft reference from description
    # --------------------------------------------------------
    if payment_tx:
        draft_id = _extract_draft_id_from_description(payment_tx.description)

        if draft_id:
            draft = (
                CompanyOnboardingTransaction.objects
                .filter(id=draft_id)
                .order_by("-id")
                .first()
            )

            if draft:
                if draft.status != "PAID":
                    return {
                        "success": True,
                        "status": "pending",
                        "source": "draft_status_pending",
                        "tap_id": tap_id,
                        "draft_id": draft.id,
                        "draft_status": draft.status,
                        "message": "Payment is still being processed. Please wait a moment and retry.",
                        "retry_after_ms": 2500,
                    }

                company = (
                    Company.objects
                    .filter(name=draft.company_name)
                    .order_by("-id")
                    .first()
                )

                if company:
                    invoice = (
                        Invoice.objects
                        .select_related("company")
                        .filter(company=company)
                        .order_by("-id")
                        .first()
                    )

                    if invoice:
                        return {
                            "success": True,
                            "status": "resolved",
                            "source": "draft_company_latest_invoice",
                            "tap_id": tap_id,
                            "draft_id": draft.id,
                            "invoice_id": invoice.id,
                            "invoice_number": invoice.invoice_number,
                            "invoice_status": invoice.status,
                            "company_id": invoice.company.id if invoice.company else None,
                            "company_name": invoice.company.name if invoice.company else None,
                            "redirect_url": f"/system/invoices/{invoice.invoice_number}",
                        }

                return {
                    "success": True,
                    "status": "pending",
                    "source": "draft_paid_invoice_not_found_yet",
                    "tap_id": tap_id,
                    "draft_id": draft.id,
                    "draft_status": draft.status,
                    "message": "Payment confirmed, but invoice is not linked yet. Please retry shortly.",
                    "retry_after_ms": 2500,
                }

    # --------------------------------------------------------
    # 4) Not found
    # --------------------------------------------------------
    return {
        "success": False,
        "status": "not_found",
        "tap_id": tap_id,
        "message": "No invoice could be resolved for this Tap transaction.",
    }


# ============================================================
# 🌐 API
# GET /api/system/payments/tap/success-lookup/?tap_id=chg_...
# ============================================================

@csrf_exempt
@require_GET
def tap_success_lookup(request):
    tap_id = _clean_str(request.GET.get("tap_id"))

    if not tap_id:
        return JsonResponse(
            {
                "success": False,
                "status": "error",
                "message": "tap_id is required.",
            },
            status=400,
        )

    result = _resolve_invoice_from_tap_id(tap_id=tap_id)

    if result.get("status") == "resolved":
        return JsonResponse(result, status=200)

    if result.get("status") == "pending":
        return JsonResponse(result, status=202)

    if result.get("status") == "not_found":
        return JsonResponse(result, status=404)

    return JsonResponse(
        {
            "success": False,
            "status": "error",
            "message": "Unexpected lookup result.",
        },
        status=500,
    )