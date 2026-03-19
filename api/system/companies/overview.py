from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.timezone import now

from billing_center.models import CompanySubscription
from company_manager.models import Company, CompanyUser


@login_required
def companies_overview(request):

    today = now().date()

    total = Company.objects.count()
    active = Company.objects.filter(is_active=True).count()
    suspended = Company.objects.filter(is_active=False).count()

    total_users = CompanyUser.objects.count()

    subscriptions_total = CompanySubscription.objects.count()

    subscriptions_active = CompanySubscription.objects.filter(
        status="ACTIVE"
    ).count()

    subscriptions_trial = CompanySubscription.objects.filter(
        status="TRIAL"
    ).count()

    subs = CompanySubscription.objects.exclude(end_date__isnull=True)

    expiring_7 = subs.filter(
        end_date__gte=today,
        end_date__lte=today + timedelta(days=7),
    ).count()

    expiring_30 = subs.filter(
        end_date__gte=today,
        end_date__lte=today + timedelta(days=30),
    ).count()

    expired = subs.filter(end_date__lt=today).count()

    return JsonResponse({
        "companies": {
            "total": total,
            "active": active,
            "suspended": suspended,
        },
        "users_total": total_users,
        "subscriptions": {
            "total": subscriptions_total,
            "active": subscriptions_active,
            "trial": subscriptions_trial,
            "expired": expired,
            "expiring_7": expiring_7,
            "expiring_30": expiring_30,
        }
    })