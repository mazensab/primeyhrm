# ============================================================
# 📂 api/system/payments/tap_checkout_status.py
# 🔎 Resolve Tap checkout result to invoice redirect
# Mham Cloud
# ============================================================

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from billing_center.models import PaymentTransaction


@require_GET
@login_required
def tap_checkout_status(request):
    tap_id = (request.GET.get("tap_id") or "").strip()

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

    if not invoice:
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