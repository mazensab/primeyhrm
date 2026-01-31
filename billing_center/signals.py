# ======================================================
# 🔔 Subscription Apps Snapshot Signals — Phase B
# Primey HR Cloud
# ======================================================

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from billing_center.models import (
    CompanySubscription,
    Payment,
    PaymentTransaction,
)

# ======================================================
# 📦 Subscription → Apps Snapshot
# ======================================================

@receiver(post_save, sender=CompanySubscription)
def set_apps_snapshot_on_create(
    sender,
    instance: CompanySubscription,
    created,
    **kwargs
):
    """
    Create apps_snapshot ONCE when subscription is created as ACTIVE
    """
    if not created:
        return

    if instance.status != "ACTIVE":
        return

    if instance.apps_snapshot:
        return

    if not instance.plan or not instance.plan.apps:
        instance.apps_snapshot = []
        instance.save(update_fields=["apps_snapshot"])
        return

    instance.apps_snapshot = instance.plan.apps
    instance.save(update_fields=["apps_snapshot"])


@receiver(pre_save, sender=CompanySubscription)
def update_apps_snapshot_on_plan_change(
    sender,
    instance: CompanySubscription,
    **kwargs
):
    """
    Update apps_snapshot ONLY when plan changes
    """
    if not instance.pk:
        return

    try:
        previous = CompanySubscription.objects.get(pk=instance.pk)
    except CompanySubscription.DoesNotExist:
        return

    if previous.plan_id == instance.plan_id:
        return

    if not instance.plan or not instance.plan.apps:
        instance.apps_snapshot = []
        return

    instance.apps_snapshot = instance.plan.apps


# ============================================================
# 💳 Billing Signals — Auto PaymentTransaction Creator
# Primey HR Cloud
# ============================================================

@receiver(post_save, sender=Payment)
def create_payment_transaction_on_paid(
    sender,
    instance: Payment,
    created,
    **kwargs
):
    """
    🔒 Create PaymentTransaction automatically when Payment is marked as PAID

    ✔ Model-aligned (NO payment FK)
    ✔ Prevents duplicates safely
    ✔ Single Source of Truth for dashboards
    """

    # ------------------------------------------------------------
    # Only when payment is actually paid
    # ------------------------------------------------------------
    if not instance.paid_at:
        return

    invoice = instance.invoice
    if not invoice:
        return

    company = invoice.company

    # ------------------------------------------------------------
    # Prevent duplicates (STRICT & SAFE)
    # ------------------------------------------------------------
    if PaymentTransaction.objects.filter(
        invoice=invoice,
        amount=instance.amount,
        processed_at=instance.paid_at,
        status="PAID",
    ).exists():
        return

    # ------------------------------------------------------------
    # Create Transaction
    # ------------------------------------------------------------
    PaymentTransaction.objects.create(
        invoice=invoice,
        company=company,
        amount=instance.amount,
        status="PAID",
        payment_method=instance.method,
        processed_at=instance.paid_at,
        created_by=None,
        description="Auto-created from Payment",
    )
