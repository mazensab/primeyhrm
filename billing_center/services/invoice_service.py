# ============================================================
# 🧾 Invoice Service — Auto Approval
# ============================================================

from django.utils import timezone
from billing_center.models import Invoice


def approve_invoice(invoice: Invoice):
    """
    ============================================================
    Auto Approve Invoice
    - Called after successful payment
    - Idempotent (safe to call multiple times)
    ============================================================
    """
    if invoice.status == "PAID" and not invoice.is_approved:
        invoice.is_approved = True
        invoice.approved_at = timezone.now()
        invoice.save(update_fields=["is_approved", "approved_at"])
