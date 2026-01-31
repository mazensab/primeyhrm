# ============================================================
# ⏱ Renewal Job — APScheduler
# ============================================================

from django.utils import timezone

from billing_center.models import CompanySubscription
from billing_center.services.renewal_service import generate_renewal_invoice


def run_subscription_renewals():
    """
    ============================================================
    Daily Job:
    - Find subscriptions expiring today
    - Generate renewal invoice
    ============================================================
    """

    today = timezone.now().date()

    subscriptions = CompanySubscription.objects.filter(
        auto_renew=True,
        status="ACTIVE",
        end_date__lte=today,
    )

    for subscription in subscriptions:
        generate_renewal_invoice(subscription)
