# ============================================================
# 🔄 Renewal Service — Subscription Auto Renewal
# Mham Cloud | Billing Center
# ============================================================

from __future__ import annotations

from datetime import timedelta
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


def _get_plan_amount_and_end_date(subscription: CompanySubscription) -> tuple[Decimal, object, str]:
    """
    ============================================================
    Resolve billing amount + next end date + invoice label
    ============================================================
    """
    billing_cycle = _get_billing_cycle(subscription)
    plan = subscription.plan

    if billing_cycle == "yearly":
        amount = Decimal(plan.price_yearly)
        new_end_date = subscription.end_date + timedelta(days=365)
        label = "Y"
    else:
        amount = Decimal(plan.price_monthly)
        new_end_date = subscription.end_date + timedelta(days=30)
        label = "M"

    return amount, new_end_date, label


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
    - No duplicate invoices
    - No renewal if unpaid invoice exists
    ============================================================
    """

    # ------------------------------------------------------------
    # 1️⃣ تحقق أساسي
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

    today = timezone.now().date()

    # ------------------------------------------------------------
    # 2️⃣ 🛑 منع التجديد إذا توجد فاتورة غير مدفوعة
    # ------------------------------------------------------------
    has_unpaid = Invoice.objects.filter(
        subscription=subscription,
        status="PENDING",
    ).exists()

    if has_unpaid:
        return None

    # ------------------------------------------------------------
    # 3️⃣ منع تكرار الفاتورة لنفس اليوم
    # ------------------------------------------------------------
    existing_invoice = Invoice.objects.filter(
        subscription=subscription,
        issue_date=today,
    ).first()

    if existing_invoice:
        return existing_invoice

    # ------------------------------------------------------------
    # 4️⃣ تحديد دورة الفوترة + المبلغ + تاريخ النهاية الجديد
    # ------------------------------------------------------------
    amount, new_end_date, label = _get_plan_amount_and_end_date(subscription)

    # ------------------------------------------------------------
    # 5️⃣ إنشاء الفاتورة
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
        status="PENDING",
    )

    # ------------------------------------------------------------
    # 6️⃣ تحديث تاريخ نهاية الاشتراك (كما هو معتمد حاليًا في النظام)
    # ------------------------------------------------------------
    subscription.end_date = new_end_date
    subscription.save(update_fields=["end_date"])

    # ------------------------------------------------------------
    # 7️⃣ 🔔 إشعار إنشاء فاتورة تجديد
    # ------------------------------------------------------------
    notify_invoice_created(
        company=subscription.company,
        invoice_number=invoice.invoice_number,
    )

    return invoice