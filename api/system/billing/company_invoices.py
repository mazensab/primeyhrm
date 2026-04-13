from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from billing_center.models import Invoice, Payment
from company_manager.models import Company

from api.system.users_actions import system_permission_required


# ================================================================
# 🔒 Response Helpers
# ================================================================
def success(data):
    return JsonResponse(
        {"status": "success", "items": data},
        status=200,
        json_dumps_params={"ensure_ascii": False},
    )


def error(msg, status=400):
    return JsonResponse(
        {"status": "error", "message": msg},
        status=status,
        json_dumps_params={"ensure_ascii": False},
    )


# ================================================================
# 🧾 Company Invoices (ALL SUBSCRIPTIONS)
# ================================================================
@login_required
@system_permission_required("companies.view")
def company_invoices(request, company_id: int):
    """
    ============================================================
    🧾 Company Invoices API
    ------------------------------------------------------------
    ✔ Returns ALL invoices for the company
    ✔ Across ALL subscriptions (old + new)
    ✔ Sorted by issue_date DESC
    ✔ Product-aware
    ✔ System Admin only
    ============================================================
    """

    company = get_object_or_404(Company, id=company_id)

    invoices = (
        Invoice.objects
        .filter(company=company)
        .select_related("subscription", "subscription__product", "subscription__plan")
        .order_by("-issue_date", "-id")
    )

    items = []

    for invoice in invoices:
        payments_qs = Payment.objects.filter(invoice=invoice)
        paid_amount = sum(float(p.amount) for p in payments_qs)

        subscription = invoice.subscription
        resolved_product = getattr(subscription, "resolved_product", None) if subscription else None

        items.append({
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "billing_reason": getattr(invoice, "billing_reason", None),

            "total_amount": float(invoice.total_amount or 0),
            "total_after_discount": float(
                invoice.total_after_discount
                if invoice.total_after_discount is not None
                else invoice.total_amount or 0
            ),
            "paid_amount": paid_amount,

            "issue_date": invoice.issue_date.isoformat() if invoice.issue_date else None,
            "subscription_id": invoice.subscription_id,

            "product": {
                "id": resolved_product.id,
                "code": resolved_product.code,
                "name": resolved_product.name,
            } if resolved_product else None,

            "plan_name": subscription.plan.name if subscription and subscription.plan else None,

            "primary_payment": True if invoice.status == "PAID" else False,
            "payments_count": payments_qs.count(),
        })

    return success(items)