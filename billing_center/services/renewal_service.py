# ============================================================
# 🔄 Renewal Service — Subscription Auto Renewal
# Mham Cloud | Billing Center | PRODUCT-AWARE SAFE
# ============================================================
# ✔ Creates renewal invoice only
# ✔ Does NOT extend subscription dates directly
# ✔ Idempotent-safe
# ✔ Respects active product subscription model
# ✔ Safe notification hook
# ============================================================

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from billing_center.models import CompanySubscription, Invoice
from billing_center.services.billing_notifications import notify_invoice_created


# ============================================================
# 🧩 Helpers
# ============================================================
def _get_billing_cycle(subscription: CompanySubscription) -> str:
    """
    ============================================================
    Determine billing cycle from subscription duration
    ============================================================
    """
    if not subscription.start_date or not subscription.end_date:
        return "monthly"

    duration = (subscription.end_date - subscription.start_date).days
    return "yearly" if duration > 31 else "monthly"


def _get_plan_amount(subscription: CompanySubscription) -> tuple[Decimal, str]:
    """
    ============================================================
    Resolve billing amount + invoice label
    ============================================================
    """
    billing_cycle = _get_billing_cycle(subscription)
    plan = subscription.plan

    if billing_cycle == "yearly":
        amount = Decimal(plan.price_yearly)
        label = "Y"
    else:
        amount = Decimal(plan.price_monthly)
        label = "M"

    return amount, label


def _resolve_subscription_product(subscription: CompanySubscription):
    if not subscription:
        return None
    return getattr(subscription, "resolved_product", None)


# ============================================================
# 🧾 Generate Renewal Invoice
# ============================================================
@transaction.atomic
def generate_renewal_invoice(subscription: CompanySubscription) -> Invoice | None:
    """
    ============================================================
    Create Renewal Invoice
    - Safe
    - Idempotent
    - Monthly / Yearly
    - No duplicate pending invoice
    - No renewal if unpaid invoice exists
    - Does NOT extend subscription dates directly
    ============================================================
    """

    # ------------------------------------------------------------
    # 1️⃣ Basic Validation
    # ------------------------------------------------------------
    if not subscription:
        return None

    if not subscription.auto_renew:
        return None

    if subscription.status != "ACTIVE":
        return None

    plan = subscription.plan
    if not plan:
        return None

    resolved_product = _resolve_subscription_product(subscription)
    if not resolved_product:
        return None

    today = timezone.now().date()

    # ------------------------------------------------------------
    # 2️⃣ Prevent renewal if there is already a pending invoice
    # ------------------------------------------------------------
    existing_pending_invoice = (
        Invoice.objects
        .filter(
            subscription=subscription,
            status="PENDING",
        )
        .order_by("-id")
        .first()
    )

    if existing_pending_invoice:
        return existing_pending_invoice

    # ------------------------------------------------------------
    # 3️⃣ Prevent creating same-day duplicate renewal invoice
    # ------------------------------------------------------------
    existing_today_invoice = (
        Invoice.objects
        .filter(
            subscription=subscription,
            billing_reason="RENEWAL",
            issue_date=today,
        )
        .order_by("-id")
        .first()
    )

    if existing_today_invoice:
        return existing_today_invoice

    # ------------------------------------------------------------
    # 4️⃣ Resolve billing amount only
    # ------------------------------------------------------------
    amount, label = _get_plan_amount(subscription)

    # ------------------------------------------------------------
    # 5️⃣ Create invoice only
    # ------------------------------------------------------------
    invoice = Invoice.objects.create(
        company=subscription.company,
        subscription=subscription,
        invoice_number=f"INV-R-{label}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
        issue_date=today,
        due_date=today,
        total_amount=amount,
        subtotal_amount=amount,
        total_after_discount=amount,
        billing_reason="RENEWAL",
        status="PENDING",
        subscription_snapshot={
            "type": "RENEWAL",
            "subscription_id": subscription.id,
            "product": {
                "id": resolved_product.id,
                "code": resolved_product.code,
                "name": resolved_product.name,
            },
            "plan": {
                "id": plan.id,
                "name": plan.name,
            },
            "billing_cycle": _get_billing_cycle(subscription),
        },
    )

    # ------------------------------------------------------------
    # 6️⃣ Safe notification only
    # ------------------------------------------------------------
    try:
        notify_invoice_created(
            company=subscription.company,
            invoice_number=invoice.invoice_number,
        )
    except Exception:
        pass

    return invoice