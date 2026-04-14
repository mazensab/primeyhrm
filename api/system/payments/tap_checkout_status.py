# ============================================================
# 📂 api/system/payments/tap_checkout_status.py
# 🔎 Resolve Tap checkout result to invoice redirect
# Mham Cloud
# ============================================================

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from billing_center.models import CompanyOnboardingTransaction, Invoice, PaymentTransaction
from company_manager.models import Company


def _clean_str(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _extract_draft_id_from_description(description: str) -> int | None:
    description = _clean_str(description)
    if not description:
        return None

    import re

    match = re.search(r"draft\s*#?\s*(\d+)", description, re.IGNORECASE)
    if not match:
        return None

    try:
        return int(match.group(1))
    except Exception:
        return None


def _find_company_from_draft(draft: CompanyOnboardingTransaction | None) -> Company | None:
    if not draft:
        return None

    commercial_number = _clean_str(getattr(draft, "commercial_number", None))
    company_name = _clean_str(getattr(draft, "company_name", None))

    if commercial_number:
        company = (
            Company.objects
            .filter(commercial_number=commercial_number)
            .order_by("-id")
            .first()
        )
        if company:
            return company

    if company_name:
        company = (
            Company.objects
            .filter(name=company_name)
            .order_by("-id")
            .first()
        )
        if company:
            return company

    return None


@require_GET
@login_required
def tap_checkout_status(request):
    tap_id = _clean_str(request.GET.get("tap_id"))

    if not tap_id:
        return JsonResponse(
            {
                "status": "error",
                "message": "tap_id is required.",
            },
            status=400,
        )

    payment_txn = (
        PaymentTransaction.objects
        .select_related("invoice", "company")
        .filter(transaction_id=tap_id)
        .order_by("-id")
        .first()
    )

    if not payment_txn:
        return JsonResponse(
            {
                "status": "pending",
                "message": "Payment transaction not found yet.",
                "tap_id": tap_id,
            },
            status=404,
        )

    invoice = getattr(payment_txn, "invoice", None)

    if invoice:
        invoice_number = getattr(invoice, "invoice_number", "") or ""

        return JsonResponse(
            {
                "status": "ok",
                "message": "Invoice resolved successfully.",
                "tap_id": tap_id,
                "payment_id": payment_txn.id,
                "payment_status": payment_txn.status,
                "invoice_id": invoice.id,
                "invoice_number": invoice_number,
                "redirect_url": f"/system/invoices/{invoice_number}",
            },
            status=200,
        )

    draft_id = _extract_draft_id_from_description(getattr(payment_txn, "description", "") or "")
    if draft_id:
        draft = (
            CompanyOnboardingTransaction.objects
            .filter(id=draft_id)
            .order_by("-id")
            .first()
        )

        if draft:
            if draft.status != "PAID":
                return JsonResponse(
                    {
                        "status": "pending",
                        "message": "Payment found, but onboarding is still being finalized.",
                        "tap_id": tap_id,
                        "payment_id": payment_txn.id,
                        "payment_status": payment_txn.status,
                        "draft_id": draft.id,
                        "draft_status": draft.status,
                    },
                    status=202,
                )

            company = _find_company_from_draft(draft)
            if company:
                latest_invoice = (
                    Invoice.objects
                    .filter(company=company)
                    .order_by("-id")
                    .first()
                )

                if latest_invoice:
                    return JsonResponse(
                        {
                            "status": "ok",
                            "message": "Invoice resolved successfully from paid onboarding draft.",
                            "tap_id": tap_id,
                            "payment_id": payment_txn.id,
                            "payment_status": payment_txn.status,
                            "draft_id": draft.id,
                            "draft_status": draft.status,
                            "company_id": company.id,
                            "company_name": company.name,
                            "invoice_id": latest_invoice.id,
                            "invoice_number": latest_invoice.invoice_number,
                            "redirect_url": f"/system/invoices/{latest_invoice.invoice_number}",
                        },
                        status=200,
                    )

                return JsonResponse(
                    {
                        "status": "ok",
                        "message": "Company was activated successfully, but invoice is not linked yet.",
                        "tap_id": tap_id,
                        "payment_id": payment_txn.id,
                        "payment_status": payment_txn.status,
                        "draft_id": draft.id,
                        "draft_status": draft.status,
                        "company_id": company.id,
                        "company_name": company.name,
                        "invoice_id": None,
                        "invoice_number": None,
                        "redirect_url": None,
                    },
                    status=200,
                )

    return JsonResponse(
        {
            "status": "pending",
            "message": "Payment found but invoice is not linked yet.",
            "tap_id": tap_id,
            "payment_id": payment_txn.id,
            "payment_status": payment_txn.status,
        },
        status=202,
    )