# ================================================================
# Mham Cloud
# System Subscriptions — Subscription Detail API
# ================================================================

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from billing_center.models import (
    CompanySubscription,
    Invoice,
    Payment,
)
from billing_center.services.subscription_limits import (
    build_subscription_usage_snapshot,
)


# ================================================================
# Subscription Detail
# ================================================================

@login_required
def system_subscription_detail(request, subscription_id):

    try:
        subscription = (
            CompanySubscription.objects
            .select_related("company", "plan", "product")
            .get(id=subscription_id)
        )

    except CompanySubscription.DoesNotExist:
        return JsonResponse(
            {"error": "Subscription not found"},
            status=404
        )

    # ============================================================
    # Determine Billing Cycle
    # ============================================================

    billing_cycle = "YEARLY"

    if subscription.plan and subscription.plan.price_monthly and subscription.plan.price_yearly:
        if subscription.plan.price_yearly > subscription.plan.price_monthly:
            billing_cycle = "YEARLY"
        else:
            billing_cycle = "MONTHLY"

    # ============================================================
    # Subscription Data
    # ============================================================

    subscription_data = {
        "id": subscription.id,

        "company_id": subscription.company.id,
        "company_name": subscription.company.name,

        "product": (
            {
                "id": subscription.product.id,
                "code": subscription.product.code,
                "name": subscription.product.name,
            }
            if getattr(subscription, "product", None) else None
        ),

        "plan_name": subscription.plan.name if subscription.plan else None,

        "status": subscription.status,

        "start_date": subscription.start_date,
        "end_date": subscription.end_date,

        "billing_cycle": billing_cycle,

        "auto_renew": subscription.auto_renew,

        # السعر الذي سيظهر في الواجهة
        "price": (
            subscription.plan.price_yearly or subscription.plan.price_monthly
        ) if subscription.plan else None,

        "price_monthly": subscription.plan.price_monthly if subscription.plan else None,
        "price_yearly": subscription.plan.price_yearly if subscription.plan else None,

        "created_at": subscription.created_at,
    }

    # ============================================================
    # Invoices
    # ============================================================

    invoices_qs = (
        Invoice.objects
        .filter(subscription=subscription)
        .order_by("-created_at")
    )

    invoices = []

    for inv in invoices_qs:
        invoices.append({
            "id": inv.id,
            "invoice": inv.invoice_number or str(inv),
            "amount": inv.total_amount,
            "status": inv.status,
            "date": inv.created_at.strftime("%Y-%m-%d") if getattr(inv, "created_at", None) else None,
        })

    # ============================================================
    # Payments
    # ============================================================

    payments_qs = (
        Payment.objects
        .filter(invoice__subscription=subscription)
        .select_related("invoice")
        .order_by("-paid_at")
    )

    payments = []

    for p in payments_qs:
        payments.append({
            "id": p.id,
            "amount": p.amount,
            "method": p.method,
            "date": p.paid_at.strftime("%Y-%m-%d") if getattr(p, "paid_at", None) else None,
            "invoice_id": p.invoice.id if p.invoice else None,
        })

    # ============================================================
    # Renewals
    # ============================================================

    renewals = []

    for inv in invoices_qs:
        renewals.append({
            "date": inv.created_at.strftime("%Y-%m-%d") if getattr(inv, "created_at", None) else None,
            "plan": subscription.plan.name if subscription.plan else None,
            "amount": inv.total_amount,
        })

    # ============================================================
    # Usage — Unified Product-Aware Snapshot
    # ============================================================

    usage = build_subscription_usage_snapshot(subscription)

    # ============================================================
    # Response
    # ============================================================

    return JsonResponse({
        "subscription": subscription_data,
        "invoices": invoices,
        "payments": payments,
        "renewals": renewals,
        "usage": usage,
    })