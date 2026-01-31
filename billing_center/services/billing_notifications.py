# ============================================================
# 🔔 Billing Notifications Service
# Primey HR Cloud | Notification Center
# ============================================================

from notification_center.services import notify_company


def notify_before_renewal(company, days_left: int, end_date):
    notify_company(
        company=company,
        title="تنبيه تجديد الاشتراك",
        message=(
            f"اشتراك شركتك سينتهي بعد {days_left} "
            f"يوم (تاريخ الانتهاء: {end_date}). "
            "سيتم التجديد تلقائيًا."
        ),
        level="warning",
        source="billing",
    )


def notify_invoice_created(company, invoice_number):
    notify_company(
        company=company,
        title="فاتورة تجديد الاشتراك",
        message=f"تم إنشاء فاتورة تجديد الاشتراك رقم {invoice_number}.",
        level="info",
        source="billing",
    )


def notify_subscription_renewed(company, end_date):
    notify_company(
        company=company,
        title="تم تجديد الاشتراك",
        message=f"تم تجديد اشتراك شركتك بنجاح حتى {end_date}.",
        level="success",
        source="billing",
    )

def notify_payment_failed(company, invoice_number, amount):
    notify_company(
        company=company,
        title="فشل عملية الدفع",
        message=(
            f"فشلت عملية دفع الفاتورة رقم {invoice_number} "
            f"بقيمة {amount}. يرجى تحديث وسيلة الدفع أو التواصل مع الدعم."
        ),
        level="error",
        source="billing",
    )
