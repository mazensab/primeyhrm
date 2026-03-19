# ============================================================
# Primey HR Cloud
# Public Invoice View
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from billing_center.models import Invoice, Payment


@require_GET
def public_invoice_detail(request, number):

    try:
        invoice = (
            Invoice.objects
            .select_related(
                "company",
                "subscription__plan"
            )
            .get(invoice_number=number)
        )

    except Invoice.DoesNotExist:
        return JsonResponse(
            {"error": "Invoice not found"},
            status=404
        )

    payment = (
        Payment.objects
        .filter(invoice=invoice)
        .order_by("-paid_at", "-id")
        .first()
    )

    subtotal = invoice.subtotal_amount or 0
    discount = invoice.discount_amount or 0
    total = invoice.total_amount or 0
    vat = total - subtotal + discount

    data = {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,

        "company": (
            invoice.company.name
            if invoice.company
            else "-"
        ),

        "plan": (
            invoice.subscription.plan.name
            if invoice.subscription and invoice.subscription.plan
            else None
        ),

        "subtotal": float(subtotal),
        "discount": float(discount),
        "vat": float(vat),
        "total": float(total),

        "status": invoice.status,

        "issue_date": (
            invoice.issue_date.isoformat()
            if invoice.issue_date
            else None
        ),

        "due_date": (
            invoice.due_date.isoformat()
            if invoice.due_date
            else None
        ),

        "payment_method": payment.method if payment else None,

        "paid_at": (
            payment.paid_at.isoformat()
            if payment and payment.paid_at
            else None
        ),

        "currency": "SAR",
    }

    return JsonResponse(
        data,
        json_dumps_params={"ensure_ascii": False}
    )