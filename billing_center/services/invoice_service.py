# ============================================================
# 🧾 Invoice Service — Auto Approval
# Mham Cloud | Billing Center
# ============================================================

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from billing_center.models import Invoice
from billing_center.services.billing_notifications import notify_invoice_approved


# ============================================================
# 🧩 Helpers
# ============================================================
def _clean(value) -> str:
    return str(value).strip() if value is not None else ""


def _safe_amount(invoice: Invoice) -> str:
    return (
        _clean(getattr(invoice, "total_amount", ""))
        or _clean(getattr(invoice, "total_after_discount", ""))
        or _clean(getattr(invoice, "subtotal_amount", ""))
        or "0"
    )


def _notify_invoice_approved_safe(invoice: Invoice) -> None:
    """
    إشعار آمن عند اعتماد الفاتورة.
    لا يسمح بكسر مسار الاعتماد إذا فشل الإشعار.
    """
    company = getattr(invoice, "company", None)
    if not company:
        return

    invoice_number = _clean(getattr(invoice, "invoice_number", ""))
    amount = _safe_amount(invoice)

    try:
        notify_invoice_approved(
            company=company,
            invoice_number=invoice_number,
            amount=amount,
        )
    except Exception:
        pass


# ============================================================
# ✅ Auto Approve Invoice
# ============================================================
@transaction.atomic
def approve_invoice(invoice: Invoice) -> Invoice:
    """
    ============================================================
    Auto Approve Invoice
    - Called after successful payment
    - Idempotent (safe to call multiple times)
    - Notification-safe
    ============================================================
    """
    if not invoice:
        return invoice

    if invoice.status == "PAID" and not invoice.is_approved:
        invoice.is_approved = True
        invoice.approved_at = timezone.now()
        invoice.save(update_fields=["is_approved", "approved_at"])

        _notify_invoice_approved_safe(invoice)

    return invoice