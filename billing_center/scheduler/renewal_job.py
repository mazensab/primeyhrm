# ============================================================
# ⏱ Renewal Job — APScheduler
# Mham Cloud | Billing Center
# ============================================================

from __future__ import annotations

from django.utils import timezone

from billing_center.models import CompanySubscription
from billing_center.services.renewal_service import generate_renewal_invoice


# ============================================================
# 🔄 Run Subscription Renewals
# ============================================================
def run_subscription_renewals():
    """
    ============================================================
    Daily Job:
    - Find subscriptions expiring today or earlier
    - Generate renewal invoice
    - Return execution summary
    ============================================================
    """
    today = timezone.now().date()

    subscriptions = CompanySubscription.objects.filter(
        auto_renew=True,
        status="ACTIVE",
        end_date__lte=today,
    )

    processed_count = 0
    created_count = 0
    skipped_count = 0

    for subscription in subscriptions:
        processed_count += 1

        invoice = generate_renewal_invoice(subscription)

        if invoice:
            created_count += 1
        else:
            skipped_count += 1

    return {
        "success": True,
        "processed_count": processed_count,
        "created_count": created_count,
        "skipped_count": skipped_count,
        "run_date": today,
    }