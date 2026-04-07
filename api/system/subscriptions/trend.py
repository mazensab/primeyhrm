# ============================================================
# 📊 SYSTEM — Subscriptions Trend API
# Mham Cloud
# ============================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

from datetime import timedelta
from collections import defaultdict

from billing_center.models import CompanySubscription


@login_required
def subscriptions_trend(request):

    today = now()
    six_months_ago = today - timedelta(days=180)

    subs = CompanySubscription.objects.filter(
        created_at__gte=six_months_ago
    )

    trend = defaultdict(int)

    for s in subs:

        month_key = s.created_at.strftime("%Y-%m")
        trend[month_key] += 1

    result = [
        {"month": month, "count": count}
        for month, count in sorted(trend.items())
    ]

    return JsonResponse(result, safe=False)