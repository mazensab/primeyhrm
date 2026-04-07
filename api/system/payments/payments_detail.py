# ============================================================
# 💳 SYSTEM — Payment Detail (READ ONLY)
# Mham Cloud
# ============================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404

from billing_center.models import Payment


@require_GET
@login_required
def payment_detail(request, payment_id):
    """
    ============================================================
    🔒 SYSTEM PAYMENT DETAIL
    - Read only
    - Safe
    ============================================================
    """

    payment = get_object_or_404(
        Payment.objects.select_related(
            "invoice",
            "invoice__company"
        ),
        id=payment_id
    )

    data = {
        "id": payment.id,
        "amount": float(payment.amount),
        "currency": "SAR",
        "status": "PAID" if payment.paid_at else "PENDING",
        "method": payment.method,
        "paid_at": payment.paid_at,
        "reference": payment.reference_number,

        # Invoice
        "invoice": {
            "id": payment.invoice.id,
            "number": payment.invoice.invoice_number,
            "status": payment.invoice.status,
        } if payment.invoice else None,

        # Company
        "company": {
            "id": payment.invoice.company.id,
            "name": payment.invoice.company.name,
        } if payment.invoice and payment.invoice.company else None,
    }
    return JsonResponse(
        data,
        json_dumps_params={"ensure_ascii": False},
    )
