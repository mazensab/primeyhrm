# ===============================================================
# 🔁 Subscription → Invoice Automation Service
# Primey HR Cloud | Billing Center
# ===============================================================

from decimal import Decimal
from django.core.exceptions import ValidationError

from billing_center.models import CompanySubscription
from billing_center.services.invoice_factory import create_subscription_invoice
from billing_center.services.discount_service import apply_discount_to_invoice


def generate_invoice_for_subscription_event(
    subscription: CompanySubscription,
    event_type: str,
    discount_code: str | None = None,
) -> None:
    """
    Handles:
    - Subscription Renewal
    - Plan Upgrade / Change
    """

    if not subscription.plan:
        raise ValidationError("لا توجد باقة مرتبطة بالاشتراك")

    # ----------------------------------------------------------
    # 1) تحديد المبلغ
    # ----------------------------------------------------------
    if event_type == "RENEWAL":
        amount = subscription.plan.price_yearly if subscription.auto_renew else subscription.plan.price_monthly

    elif event_type == "UPGRADE":
        # حاليًا: فرق السعر الكامل (Proration لاحقًا)
        amount = subscription.plan.price_monthly

    else:
        raise ValidationError("نوع الحدث غير مدعوم")

    # ----------------------------------------------------------
    # 2) إنشاء الفاتورة
    # ----------------------------------------------------------
    invoice = create_subscription_invoice(
        subscription=subscription,
        amount=Decimal(amount),
        event_type=event_type,
    )

    # ----------------------------------------------------------
    # 3) تطبيق الخصم (اختياري)
    # ----------------------------------------------------------
    if discount_code:
        apply_discount_to_invoice(invoice, discount_code)
