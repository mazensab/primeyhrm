# ===============================================================
# 🧾 Invoice Factory
# Mham Cloud | Billing Center
# ===============================================================

from __future__ import annotations

from decimal import Decimal

from django.utils import timezone

from billing_center.models import CompanySubscription, Invoice


# ===============================================================
# 🧩 Helpers
# ===============================================================
def _clean_event_type(event_type: str) -> str:
    return str(event_type or "").strip().upper()


def _build_invoice_number(event_type: str) -> str:
    """
    توليد رقم فاتورة واضح حسب نوع الحدث.
    """
    normalized_event_type = _clean_event_type(event_type)

    if normalized_event_type == "RENEWAL":
        prefix = "INV-R"
    elif normalized_event_type == "UPGRADE":
        prefix = "INV-U"
    else:
        prefix = "INV"

    return f"{prefix}-{timezone.now().strftime('%Y%m%d%H%M%S')}"


def _build_invoice_payload(
    *,
    subscription: CompanySubscription,
    amount: Decimal,
    event_type: str,
) -> dict:
    """
    تجهيز payload إنشاء الفاتورة بشكل مرن وآمن.
    """
    today = timezone.now().date()

    payload = {
        "company": subscription.company,
        "subscription": subscription,
        "invoice_number": _build_invoice_number(event_type),
        "issue_date": today,
        "total_amount": amount,
        "status": "PENDING",
    }

    # ----------------------------------------------------------
    # حقول إضافية إن كانت موجودة في موديل Invoice
    # ----------------------------------------------------------
    invoice_field_names = {field.name for field in Invoice._meta.fields}

    if "due_date" in invoice_field_names:
        payload["due_date"] = today

    if "subtotal_amount" in invoice_field_names:
        payload["subtotal_amount"] = amount

    if "total_after_discount" in invoice_field_names:
        payload["total_after_discount"] = amount

    return payload


# ===============================================================
# 🧾 Create Subscription Invoice
# ===============================================================
def create_subscription_invoice(
    subscription: CompanySubscription,
    amount: Decimal,
    event_type: str,
) -> Invoice:
    """
    Create invoice for subscription events
    event_type: RENEWAL | UPGRADE
    """
    payload = _build_invoice_payload(
        subscription=subscription,
        amount=Decimal(amount),
        event_type=event_type,
    )

    invoice = Invoice.objects.create(**payload)
    return invoice