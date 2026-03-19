# ============================================================
# 📦 SYSTEM — Subscriptions List API
# Primey HR Cloud
# ============================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from billing_center.models import CompanySubscription


@login_required
def subscriptions_list(request):

    subscriptions = CompanySubscription.objects.select_related(
        "company",
        "plan"
    ).order_by("-id")

    data = []

    for sub in subscriptions:

        # السعر من الخطة
        price = sub.plan.price_monthly

        data.append({
            "id": sub.id,
            "company_name": sub.company.name,
            "plan_name": sub.plan.name,
            "status": sub.status,
            "start_date": sub.start_date,
            "end_date": sub.end_date,
            "price": float(price),
        })

    return JsonResponse({
        "subscriptions": data
    })