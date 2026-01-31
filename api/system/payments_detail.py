# ============================================================
# 💳 SYSTEM — Payment Detail (READ ONLY)
# Primey HR Cloud
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
        "status": "PAID" if payment.paid_at else "PENDING",
        "method": payment.method,
        "paid_at": payment.paid_at,
        "reference": payment.reference_number,
        "invoice_id": payment.invoice_id,
        "invoice_number": (
            payment.invoice.invoice_number
            if payment.invoice else None
        ),
        "company_name": (
            payment.invoice.company.name
            if payment.invoice and payment.invoice.company else None
        ),
    }

    return JsonResponse(
        data,
        json_dumps_params={"ensure_ascii": False},
    )
