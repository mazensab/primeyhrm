# ============================================================
# 🏢 SYSTEM — Company Subscriptions Detail
# Mham Cloud | V2.0 PRODUCT-AWARE
# ============================================================
# ✔ Single Company
# ✔ Includes ALL subscriptions for the company
# ✔ Includes latest invoice per subscription
# ✔ PRODUCT-AWARE
# ✔ READ ONLY
# ============================================================

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from billing_center.models import CompanySubscription, Invoice
from company_manager.models import Company


@login_required
def company_subscription_detail(request, company_id):
    """
    GET /api/system/companies/<id>/subscription

    Product-aware response:
    - Returns ALL subscriptions for the company
    - Each subscription includes:
      - product
      - plan
      - latest invoice
    """

    company = get_object_or_404(Company, id=company_id)

    subscriptions = (
        CompanySubscription.objects
        .filter(company=company)
        .select_related("product", "plan")
        .order_by("-created_at", "-id")
    )

    if not subscriptions.exists():
        return JsonResponse(
            {
                "company_id": company.id,
                "company_name": company.name,
                "subscriptions": [],
            },
            status=200,
        )

    items = []

    for subscription in subscriptions:
        latest_invoice = (
            Invoice.objects
            .filter(subscription=subscription)
            .order_by("-issue_date", "-id")
            .first()
        )

        resolved_product = getattr(subscription, "resolved_product", None)

        items.append({
            "id": subscription.id,
            "status": subscription.status,
            "start_date": subscription.start_date,
            "end_date": subscription.end_date,

            "product": {
                "id": resolved_product.id,
                "code": resolved_product.code,
                "name": resolved_product.name,
            } if resolved_product else None,

            "plan": {
                "id": subscription.plan.id,
                "name": subscription.plan.name,
            } if subscription.plan else None,

            "latest_invoice": {
                "id": latest_invoice.id,
                "invoice_number": latest_invoice.invoice_number,
                "status": latest_invoice.status,
                "total_amount": float(latest_invoice.total_amount),
                "issue_date": latest_invoice.issue_date.isoformat()
                if latest_invoice.issue_date else None,
            } if latest_invoice else None,
        })

    return JsonResponse(
        {
            "company_id": company.id,
            "company_name": company.name,
            "subscriptions": items,
        },
        status=200,
    )