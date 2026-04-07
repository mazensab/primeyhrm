# ============================================================
# 🔔 Billing Notifications Service
# Mham Cloud | Notification Center
# ============================================================

from __future__ import annotations

from notification_center.services import notify_company


# ============================================================
# 🧩 Helpers
# ============================================================
def _clean(value) -> str:
    return str(value).strip() if value is not None else ""


def _notify_billing_company(
    *,
    company,
    title: str,
    message: str,
    level: str,
    source: str,
):
    """
    Wrapper موحّد لإشعارات الفوترة على مستوى الشركة.
    نحافظ هنا على notify_company الحالية كما هي
    حتى لا نكسر أي منطق قديم أثناء الترحيل التدريجي.
    """
    return notify_company(
        company=company,
        title=_clean(title),
        message=_clean(message),
        level=_clean(level) or "info",
        source=_clean(source) or "billing",
    )


# ============================================================
# ⏰ قبل التجديد
# ============================================================
def notify_before_renewal(company, days_left: int, end_date):
    return _notify_billing_company(
        company=company,
        title="تنبيه تجديد الاشتراك",
        message=(
            f"اشتراك شركتك سينتهي بعد {days_left} "
            f"يوم (تاريخ الانتهاء: {end_date}). "
            "سيتم التجديد تلقائيًا."
        ),
        level="warning",
        source="billing.before_renewal",
    )


# ============================================================
# 🧾 إنشاء فاتورة
# ============================================================
def notify_invoice_created(company, invoice_number):
    invoice_number = _clean(invoice_number)

    return _notify_billing_company(
        company=company,
        title="فاتورة تجديد الاشتراك",
        message=f"تم إنشاء فاتورة تجديد الاشتراك رقم {invoice_number}.",
        level="info",
        source="billing.invoice_created",
    )


# ============================================================
# ✅ اعتماد فاتورة
# ============================================================
def notify_invoice_approved(company, invoice_number, amount=None):
    invoice_number = _clean(invoice_number)
    amount = _clean(amount)

    amount_text = f" بقيمة {amount}" if amount else ""

    return _notify_billing_company(
        company=company,
        title="تم اعتماد الفاتورة",
        message=f"تم اعتماد الفاتورة رقم {invoice_number} بنجاح{amount_text}.",
        level="success",
        source="billing.invoice_approved",
    )


# ============================================================
# ✅ تجديد الاشتراك
# ============================================================
def notify_subscription_renewed(company, end_date):
    return _notify_billing_company(
        company=company,
        title="تم تجديد الاشتراك",
        message=f"تم تجديد اشتراك شركتك بنجاح حتى {end_date}.",
        level="success",
        source="billing.subscription_renewed",
    )


# ============================================================
# ⛔ انتهاء الاشتراك
# ============================================================
def notify_subscription_expired(company, end_date):
    return _notify_billing_company(
        company=company,
        title="انتهاء الاشتراك",
        message=(
            f"انتهى اشتراك شركتك بتاريخ {end_date}. "
            "يرجى التجديد لإعادة تفعيل الخدمة."
        ),
        level="error",
        source="billing.subscription_expired",
    )


# ============================================================
# 🔄 تغيير حالة الاشتراك
# ============================================================
def notify_subscription_status_changed(company, old_status, new_status, end_date=None):
    old_status = _clean(old_status)
    new_status = _clean(new_status)
    end_date = _clean(end_date)

    suffix = f" تاريخ الانتهاء الحالي: {end_date}." if end_date else ""

    return _notify_billing_company(
        company=company,
        title="تحديث حالة الاشتراك",
        message=(
            f"تم تحديث حالة الاشتراك من {old_status} إلى {new_status}."
            f"{suffix}"
        ),
        level="info" if new_status != "EXPIRED" else "warning",
        source="billing.subscription_status_changed",
    )


# ============================================================
# ❌ فشل الدفع
# ============================================================
def notify_payment_failed(company, invoice_number, amount):
    invoice_number = _clean(invoice_number)
    amount = _clean(amount)

    return _notify_billing_company(
        company=company,
        title="فشل عملية الدفع",
        message=(
            f"فشلت عملية دفع الفاتورة رقم {invoice_number} "
            f"بقيمة {amount}. يرجى تحديث وسيلة الدفع أو التواصل مع الدعم."
        ),
        level="error",
        source="billing.payment_failed",
    )


# ============================================================
# ✅ تأكيد الدفع
# ============================================================
def notify_payment_confirmed(company, invoice_number, amount):
    invoice_number = _clean(invoice_number)
    amount = _clean(amount)

    return _notify_billing_company(
        company=company,
        title="تم تأكيد الدفع",
        message=(
            f"تم تأكيد دفع الفاتورة رقم {invoice_number} "
            f"بقيمة {amount} بنجاح."
        ),
        level="success",
        source="billing.payment_confirmed",
    )