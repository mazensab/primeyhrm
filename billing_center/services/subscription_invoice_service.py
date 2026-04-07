# ===============================================================
# 🔁 Subscription → Invoice Automation Service
# Mham Cloud | Billing Center
# ===============================================================

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from billing_center.models import CompanySubscription
from billing_center.services.discount_service import apply_discount_to_invoice
from billing_center.services.invoice_factory import create_subscription_invoice
from billing_center.services.billing_notifications import notify_invoice_created


# ===============================================================
# 🧩 Helpers
# ===============================================================
def _resolve_invoice_amount(subscription: CompanySubscription, event_type: str) -> Decimal:
    """
    تحديد مبلغ الفاتورة بناءً على نوع الحدث.
    """
    if event_type == "RENEWAL":
        amount = (
            subscription.plan.price_yearly
            if subscription.auto_renew
            else subscription.plan.price_monthly
        )
        return Decimal(amount)

    if event_type == "UPGRADE":
        # حاليًا: فرق السعر الكامل (Proration لاحقًا)
        return Decimal(subscription.plan.price_monthly)

    raise ValidationError("نوع الحدث غير مدعوم")


def _notify_subscription_invoice_created(subscription: CompanySubscription, invoice) -> None:
    """
    إشعار آمن عند إنشاء فاتورة اشتراك.
    """
    try:
        notify_invoice_created(
            company=subscription.company,
            invoice_number=getattr(invoice, "invoice_number", ""),
        )
    except Exception:
        # لا نكسر تدفق إنشاء الفاتورة بسبب الإشعار
        pass


# ===============================================================
# 🧾 Generate Invoice For Subscription Event
# ===============================================================
@transaction.atomic
def generate_invoice_for_subscription_event(
    subscription: CompanySubscription,
    event_type: str,
    discount_code: str | None = None,
):
    """
    Handles:
    - Subscription Renewal
    - Plan Upgrade / Change
    """

    if not subscription:
        raise ValidationError("الاشتراك غير موجود")

    if not subscription.plan:
        raise ValidationError("لا توجد باقة مرتبطة بالاشتراك")

    # ----------------------------------------------------------
    # 1) تحديد المبلغ
    # ----------------------------------------------------------
    amount = _resolve_invoice_amount(subscription, event_type)

    # ----------------------------------------------------------
    # 2) إنشاء الفاتورة
    # ----------------------------------------------------------
    invoice = create_subscription_invoice(
        subscription=subscription,
        amount=amount,
        event_type=event_type,
    )

    # ----------------------------------------------------------
    # 3) تطبيق الخصم (اختياري)
    # ----------------------------------------------------------
    if discount_code:
        apply_discount_to_invoice(invoice, discount_code)

    # ----------------------------------------------------------
    # 4) إشعار إنشاء الفاتورة
    # ----------------------------------------------------------
    _notify_subscription_invoice_created(subscription, invoice)

    return invoice