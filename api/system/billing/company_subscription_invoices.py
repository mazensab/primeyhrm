# ============================================================
# 🧾 SYSTEM — Company Subscription Invoices API
# Primey HR Cloud | V1.1 ULTRA STABLE (FINAL FIX)
# ============================================================
# ✔ Single Source of Truth
# ✔ Subscription-scoped invoices
# ✔ Frontend Contract Compatible
# ✔ READ ONLY
# ============================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from company_manager.models import Company
from billing_center.models import CompanySubscription, Invoice, Payment


@login_required
def company_subscription_invoices(request, company_id):
    """
    GET /api/system/companies/<company_id>/subscription/invoices/
    """

    # ========================================================
    # 🏢 Company
    # ========================================================
    company = get_object_or_404(Company, id=company_id)

    # ========================================================
    # 📦 Latest Subscription (ANY STATUS)
    # ========================================================
    subscription = (
        CompanySubscription.objects
        .filter(company=company)
        .select_related("plan")
        .order_by("-created_at")
        .first()
    )

    # --------------------------------------------------------
    # No subscription → empty but valid response
    # --------------------------------------------------------
    if not subscription:
        return JsonResponse(
            {
                "company_id": company.id,
                "company_name": company.name,
                "subscription": None,
                "items": [],
            },
            status=200,
        )

    # ========================================================
    # 🧾 Invoices linked to subscription
    # ========================================================
    invoices_qs = (
        Invoice.objects
        .filter(subscription=subscription)
        .order_by("-created_at", "-id")
    )

    items = []

    for inv in invoices_qs:
        payments_qs = Payment.objects.filter(invoice=inv)

        paid_amount = sum(float(p.amount) for p in payments_qs)

        items.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "status": inv.status,

            "issue_date": inv.issue_date.isoformat()
            if inv.issue_date else None,

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
        })

    # ========================================================
    # ✅ FINAL RESPONSE (UI SAFE)
    # ========================================================
    return JsonResponse(
        {
            "company_id": company.id,
            "company_name": company.name,

            "subscription": {
                "id": subscription.id,
                "status": subscription.status,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
                "plan_name": subscription.plan.name
                if subscription.plan else None,
            },

            "items": items,
        },
        status=200,
    )
