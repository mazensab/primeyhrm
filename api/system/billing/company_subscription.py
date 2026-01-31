# ============================================================
# 🏢 SYSTEM — Company Subscription Detail
# Primey HR Cloud | V1.0 ULTRA STABLE
# ============================================================
# ✔ Single Company
# ✔ Includes Subscription
# ✔ Includes Latest Invoice
# ✔ READ ONLY
# ============================================================

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from company_manager.models import Company
from billing_center.models import CompanySubscription, Invoice


@login_required
def company_subscription_detail(request, company_id):
    """
    GET /api/system/companies/<id>/subscription
    """

    company = get_object_or_404(Company, id=company_id)

    subscription = (
        CompanySubscription.objects
        .filter(company=company)
        .order_by("-end_date", "-created_at")
        .first()
    )

    if not subscription:
        return JsonResponse(
            {
                "company_id": company.id,
                "subscription": None,
            },
            status=200,
        )

    latest_invoice = (
        Invoice.objects
        .filter(subscription=subscription)
        .order_by("-issue_date", "-id")
        .first()
    )

    return JsonResponse(
        {
            "company_id": company.id,
            "company_name": company.name,

            "subscription": {
                "id": subscription.id,
                "status": subscription.status,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
                "plan": {
                    "id": subscription.plan.id,
                    "name": subscription.plan.name,
                } if subscription.plan else None,
            },

            "latest_invoice": {
                "id": latest_invoice.id,
                "invoice_number": latest_invoice.invoice_number,
                "status": latest_invoice.status,
                "total_amount": float(latest_invoice.total_amount),
            } if latest_invoice else None,
        },
        status=200,
    )
