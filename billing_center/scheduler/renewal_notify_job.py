# ============================================================
# ⏱ Renewal Notification Job
# Mham Cloud | Billing Center
# ============================================================

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from billing_center.models import CompanySubscription
from billing_center.services.billing_notifications import notify_before_renewal


# ============================================================
# 🧩 Helpers
# ============================================================
def _target_dates(today):
    return [
        today + timedelta(days=7),
        today + timedelta(days=1),
    ]


# ============================================================
# 🔔 Notify Upcoming Renewals
# ============================================================
def notify_upcoming_renewals():
    """
    إرسال تنبيهات الاشتراكات القريبة من التجديد.
    حاليًا:
    - قبل 7 أيام
    - قبل يوم واحد
    """
    today = timezone.now().date()
    notified = 0

    targets = CompanySubscription.objects.filter(
        auto_renew=True,
        status="ACTIVE",
        end_date__in=_target_dates(today),
    )

    for subscription in targets:
        days_left = (subscription.end_date - today).days

        notify_before_renewal(
            company=subscription.company,
            days_left=days_left,
            end_date=subscription.end_date,
        )
        notified += 1

    return {
        "success": True,
        "notified_count": notified,
        "target_dates": _target_dates(today),
    }