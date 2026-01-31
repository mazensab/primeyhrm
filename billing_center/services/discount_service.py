# ===============================================================
# 💸 Discount Service — Invoice Level (Immutable)
# Primey HR Cloud | Billing Center
# ===============================================================

from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError

from billing_center.models import Invoice, Discount


def apply_discount_to_invoice(
    invoice: Invoice,
    discount_code: str | None = None
) -> Invoice:
    """
    ============================================================
    🧠 Apply Discount to Invoice (Single Responsibility)
    ------------------------------------------------------------
    - الخصم يُطبّق على الفاتورة فقط
    - Snapshot ثابت داخل Invoice (Immutable)
    - لا تأثير رجعي
    - يُنفّذ مرة واحدة عند الإنشاء
    ============================================================
    """

    # ------------------------------------------------------------
    # 1) لا يوجد خصم
    # ------------------------------------------------------------
    if not discount_code:
        invoice.subtotal_amount = invoice.total_amount
        invoice.discount_code = None
        invoice.discount_type = None
        invoice.discount_value = None
        invoice.discount_amount = Decimal("0.00")
        invoice.total_after_discount = invoice.total_amount

        invoice.save(update_fields=[
            "subtotal_amount",
            "discount_code",
            "discount_type",
            "discount_value",
            "discount_amount",
            "total_after_discount",
        ])
        return invoice

    # ------------------------------------------------------------
    # 2) جلب الخصم
    # ------------------------------------------------------------
    try:
        discount = Discount.objects.get(
            code=discount_code,
            is_active=True,
        )
    except Discount.DoesNotExist:
        raise ValidationError("كود الخصم غير موجود أو غير مفعل")

    today = timezone.now().date()

    # ------------------------------------------------------------
    # 3) التحقق من فترة الخصم
    # ------------------------------------------------------------
    if not (discount.start_date <= today <= discount.end_date):
        raise ValidationError("كود الخصم خارج فترة الصلاحية")

    # ------------------------------------------------------------
    # 4) التحقق من السماح للباقة
    # ------------------------------------------------------------
    if not discount.applies_to_all_plans:
        if not invoice.subscription or not invoice.subscription.plan:
            raise ValidationError("لا يمكن تطبيق الخصم بدون باقة")

        allowed_plan_ids = discount.allowed_plans.values_list("id", flat=True)

        if invoice.subscription.plan_id not in allowed_plan_ids:
            raise ValidationError("كود الخصم غير مسموح لهذه الباقة")

    # ------------------------------------------------------------
    # 5) الحساب
    # ------------------------------------------------------------
    subtotal = Decimal(invoice.total_amount)
    discount_amount = Decimal("0.00")

    if discount.discount_type == "percentage":
        discount_amount = (
            subtotal * Decimal(discount.value) / Decimal("100")
        )
    elif discount.discount_type == "fixed":
        discount_amount = Decimal(discount.value)

    # حماية من الخصم الزائد
    if discount_amount <= Decimal("0.00"):
        raise ValidationError("قيمة الخصم غير صحيحة")

    discount_amount = min(discount_amount, subtotal)
    total_after_discount = subtotal - discount_amount

    # ------------------------------------------------------------
    # 6) Snapshot ثابت داخل الفاتورة (Immutable)
    # ------------------------------------------------------------
    invoice.subtotal_amount = subtotal
    invoice.discount_code = discount.code
    invoice.discount_type = discount.discount_type
    invoice.discount_value = discount.value
    invoice.discount_amount = discount_amount
    invoice.total_after_discount = total_after_discount

    invoice.save(update_fields=[
        "subtotal_amount",
        "discount_code",
        "discount_type",
        "discount_value",
        "discount_amount",
        "total_after_discount",
    ])

    return invoice
