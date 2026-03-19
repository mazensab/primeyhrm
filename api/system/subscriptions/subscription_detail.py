# ================================================================
# PRIMEY HR CLOUD
# System Subscriptions — Subscription Detail API
# ================================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from employee_center.models import Employee

from billing_center.models import (
    CompanySubscription,
    Invoice,
    Payment
)


# ================================================================
# Subscription Detail
# ================================================================

@login_required
def system_subscription_detail(request, subscription_id):

    try:

        subscription = (
            CompanySubscription.objects
            .select_related("company", "plan")
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

    if subscription.plan.price_monthly and subscription.plan.price_yearly:

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

        "plan_name": subscription.plan.name,

        "status": subscription.status,

        "start_date": subscription.start_date,
        "end_date": subscription.end_date,

        "billing_cycle": billing_cycle,

        "auto_renew": subscription.auto_renew,

        # السعر الذي سيظهر في الواجهة
        "price": subscription.plan.price_yearly or subscription.plan.price_monthly,

        "price_monthly": subscription.plan.price_monthly,
        "price_yearly": subscription.plan.price_yearly,

        "created_at": subscription.created_at,
    }

    # ============================================================
    # Invoices
    # ============================================================

    invoices_qs = (
        Invoice.objects
        .filter(company=subscription.company)
        .order_by("-created_at")
    )

    invoices = []

    for inv in invoices_qs:

        invoices.append({

            "id": inv.id,

            "invoice": inv.invoice_number or str(inv),

            "amount": inv.total_amount,

            "status": inv.status,

            "date": inv.created_at.strftime("%Y-%m-%d"),
        })
    # ============================================================
    # Payments
    # ============================================================

    payments_qs = (
        Payment.objects
        .filter(invoice__company=subscription.company)
        .select_related("invoice")
        .order_by("-paid_at")
    )

    payments = []

    for p in payments_qs:

        payments.append({

            "id": p.id,

            "amount": p.amount,

            "method": p.method,

            "date": p.paid_at.strftime("%Y-%m-%d"),

            "invoice_id": p.invoice.id if p.invoice else None,
        })

    # ============================================================
    # Renewals
    # ============================================================

    renewals = []

    for inv in invoices_qs:

        renewals.append({

            "date": inv.created_at.strftime("%Y-%m-%d"),

            "plan": subscription.plan.name,

            "amount": inv.total_amount,
        })

    # ============================================================
    # Usage
    # ============================================================

    employees_count = (
        Employee.objects
        .filter(company=subscription.company)
        .count()
    )

    usage = {

        "employees": employees_count,

        "max_employees": getattr(subscription.plan, "max_employees", None),

        "devices": 0
    }
    
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