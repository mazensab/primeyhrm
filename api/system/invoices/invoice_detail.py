# ================================================================
# Mham Cloud
# System Invoice Detail API
# ================================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from billing_center.models import Invoice, Payment


@require_GET
@login_required
def system_invoice_detail(request, invoice_number):

    try:
        invoice = (
            Invoice.objects
            .select_related("company", "subscription__plan")
            .get(invoice_number=invoice_number)
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
        "status": invoice.status,

        "company_name": (
            invoice.company.name
            if invoice.company
            else "-"
        ),

        "plan_name": (
            invoice.subscription.plan.name
            if invoice.subscription and invoice.subscription.plan
            else "-"
        ),

        "issue_date": invoice.issue_date.isoformat() if invoice.issue_date else None,
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,

        "subtotal": str(subtotal),
        "discount": str(discount),
        "vat": str(vat),
        "total": str(total),

        "payment_method": payment.method if payment else None,
        "paid_at": payment.paid_at.isoformat() if payment and payment.paid_at else None,

        "currency": "SAR",
    }

    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})