# ============================================================
# 💰 SYSTEM — Revenue Summary API
# Primey HR Cloud | Hybrid Dashboard Architecture
# ============================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.db.models import Sum
from datetime import timedelta
from decimal import Decimal

from billing_center.models import Payment


@login_required
def revenue_summary(request):

    today = now()
    current_month = today.replace(day=1)

    prev_month = (current_month - timedelta(days=1)).replace(day=1)

    # --------------------------------------------------------
    # Total Revenue
    # --------------------------------------------------------
    total_revenue = (
        Payment.objects.aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # Current Month
    # --------------------------------------------------------
    current_month_revenue = (
        Payment.objects.filter(paid_at__gte=current_month)
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # Previous Month
    # --------------------------------------------------------
    previous_month_revenue = (
        Payment.objects.filter(
            paid_at__gte=prev_month,
            paid_at__lt=current_month
        )
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # Growth %
    # --------------------------------------------------------
    growth_percent = Decimal("0.00")

    if previous_month_revenue > 0:
        growth_percent = (
            (current_month_revenue - previous_month_revenue)
            / previous_month_revenue
        ) * Decimal("100")

    # --------------------------------------------------------
    # Recent Payments
    # --------------------------------------------------------
    recent_qs = (
        Payment.objects
        .select_related("invoice__company")
        .order_by("-paid_at")[:10]
    )

    recent_payments = []

    for p in recent_qs:

        company_name = None

        if p.invoice and p.invoice.company:
            company_name = p.invoice.company.name

        recent_payments.append({
            "id": p.id,
            "company_name": company_name,
            "amount": float(p.amount or 0),
            "method": p.method,
            "paid_at": p.paid_at.strftime("%Y-%m-%d") if p.paid_at else None,
        })

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------
    return JsonResponse({
        "total_revenue": float(total_revenue),
        "current_month_revenue": float(current_month_revenue),
        "previous_month_revenue": float(previous_month_revenue),
        "growth_percent": float(round(growth_percent, 2)),

        # compatibility
        "payments": recent_payments,
        "recent": recent_payments,
    })