# ============================================================
# ⏱ Renewal Notification Job
# ============================================================

from django.utils import timezone
from datetime import timedelta

from billing_center.models import CompanySubscription
from notification_center.services.billing_notifications import (
    notify_before_renewal,
)


def notify_upcoming_renewals():
    today = timezone.now().date()

    targets = CompanySubscription.objects.filter(
        auto_renew=True,
        status="ACTIVE",
        end_date__in=[
            today + timedelta(days=7),
            today + timedelta(days=1),
        ],
    )

    for sub in targets:
        days_left = (sub.end_date - today).days
        notify_before_renewal(
            company=sub.company,
            days_left=days_left,
            end_date=sub.end_date,
        )
