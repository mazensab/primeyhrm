# ===============================================================
# 🧾 Invoice Factory
# Primey HR Cloud | Billing Center
# ===============================================================

from decimal import Decimal
from django.utils import timezone

from billing_center.models import Invoice, CompanySubscription


def create_subscription_invoice(
    subscription: CompanySubscription,
    amount: Decimal,
    event_type: str,
) -> Invoice:
    """
    Create invoice for subscription events
    event_type: RENEWAL | UPGRADE
    """

    invoice = Invoice.objects.create(
        company=subscription.company,
        subscription=subscription,
        invoice_number=f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}",
        issue_date=timezone.now().date(),
        total_amount=amount,
        status="PENDING",
    )

    return invoice
