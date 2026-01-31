# ============================================================
# 🔄 Renewal Service — Subscription Auto Renewal
# Primey HR Cloud | Billing Center
# ============================================================

from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from billing_center.models import (
    CompanySubscription,
    Invoice,
)

from notification_center.services.billing_notifications import (
    notify_invoice_created,
)


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
    if not subscription.auto_renew:
        return None

    if subscription.status != "ACTIVE":
        return None

    # ------------------------------------------------------------
    # 2️⃣ 🛑 منع التجديد إذا توجد فاتورة غير مدفوعة
    # ------------------------------------------------------------
    has_unpaid = Invoice.objects.filter(
        subscription=subscription,
        status="PENDING",
    ).exists()

    if has_unpaid:
        return None

    today = timezone.now().date()

    # ------------------------------------------------------------
    # 3️⃣ منع تكرار الفاتورة لنفس اليوم
    # ------------------------------------------------------------
    existing = Invoice.objects.filter(
        subscription=subscription,
        issue_date=today,
    ).first()

    if existing:
        return existing

    plan = subscription.plan
    if not plan:
        return None

    # ------------------------------------------------------------
    # 4️⃣ تحديد دورة الفوترة
    # ------------------------------------------------------------
    billing_cycle = _get_billing_cycle(subscription)

    if billing_cycle == "yearly":
        amount = Decimal(plan.price_yearly)
        new_end_date = subscription.end_date + timedelta(days=365)
        label = "Y"
    else:
        amount = Decimal(plan.price_monthly)
        new_end_date = subscription.end_date + timedelta(days=30)
        label = "M"

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
    # 6️⃣ تحديث تاريخ نهاية الاشتراك (يُعتمد بعد الدفع)
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
