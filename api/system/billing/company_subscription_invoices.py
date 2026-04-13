# ============================================================
# 🧾 SYSTEM — Company Subscription Invoices API
# Mham Cloud | V2.0 PRODUCT-AWARE
# ============================================================
# ✔ Product-aware
# ✔ Supports ALL company subscriptions
# ✔ Optional subscription_id filter
# ✔ Frontend Contract Compatible
# ✔ READ ONLY
# ============================================================

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from billing_center.models import CompanySubscription, Invoice, Payment
from company_manager.models import Company


@login_required
def company_subscription_invoices(request, company_id):
    """
    GET /api/system/companies/<company_id>/subscription/invoices/

    Optional query params:
    - subscription_id: return invoices for one specific subscription only

    Default behavior:
    - return invoices across ALL subscriptions of the company
    """

    # ========================================================
    # 🏢 Company
    # ========================================================
    company = get_object_or_404(Company, id=company_id)

    # ========================================================
    # 📦 Company Subscriptions
    # ========================================================
    subscriptions_qs = (
        CompanySubscription.objects
        .filter(company=company)
        .select_related("product", "plan")
        .order_by("-created_at", "-id")
    )

    subscription_id = request.GET.get("subscription_id")

    if subscription_id:
        subscriptions_qs = subscriptions_qs.filter(id=subscription_id)

    subscriptions = list(subscriptions_qs)

    # --------------------------------------------------------
    # No subscriptions → empty but valid response
    # --------------------------------------------------------
    if not subscriptions:
        return JsonResponse(
            {
                "company_id": company.id,
                "company_name": company.name,
                "subscriptions": [],
                "items": [],
            },
            status=200,
        )

    subscription_map = {}
    subscription_ids = []

    for sub in subscriptions:
        resolved_product = getattr(sub, "resolved_product", None)

        subscription_map[sub.id] = {
            "id": sub.id,
            "status": sub.status,
            "start_date": sub.start_date.isoformat() if sub.start_date else None,
            "end_date": sub.end_date.isoformat() if sub.end_date else None,
            "product": {
                "id": resolved_product.id,
                "code": resolved_product.code,
                "name": resolved_product.name,
            } if resolved_product else None,
            "plan": {
                "id": sub.plan.id,
                "name": sub.plan.name,
            } if sub.plan else None,
        }
        subscription_ids.append(sub.id)

    # ========================================================
    # 🧾 Invoices linked to company subscriptions
    # ========================================================
    invoices_qs = (
        Invoice.objects
        .filter(company=company, subscription_id__in=subscription_ids)
        .select_related("subscription", "subscription__product", "subscription__plan")
        .order_by("-created_at", "-id")
    )

    items = []

    for inv in invoices_qs:
        payments_qs = Payment.objects.filter(invoice=inv)
        paid_amount = sum(float(p.amount) for p in payments_qs)

        sub = inv.subscription
        resolved_product = getattr(sub, "resolved_product", None) if sub else None

        items.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "status": inv.status,
            "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
            "total_amount": float(inv.total_amount),
            "total_after_discount": float(
                inv.total_after_discount
                if inv.total_after_discount is not None
                else inv.total_amount
            ),

            # UI يعتمد عليها
            "primary_payment": True if inv.status == "PAID" else False,

            "payments_count": payments_qs.count(),
            "paid_amount": paid_amount,

            "created_at": inv.created_at.isoformat()
            if hasattr(inv, "created_at") and inv.created_at else None,

            # Product-aware fields
            "subscription_id": inv.subscription_id,
            "product": {
                "id": resolved_product.id,
                "code": resolved_product.code,
                "name": resolved_product.name,
            } if resolved_product else None,
            "plan_name": sub.plan.name if sub and sub.plan else None,
        })

    # ========================================================
    # ✅ FINAL RESPONSE (UI SAFE)
    # ========================================================
    return JsonResponse(
        {
            "company_id": company.id,
            "company_name": company.name,
            "subscriptions": list(subscription_map.values()),
            "items": items,
        },
        status=200,
    )