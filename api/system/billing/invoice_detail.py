# ============================================================
# 🧾 SYSTEM — Invoice Detail API
# Primey HR Cloud | V3.2 ULTRA STABLE
# ============================================================
# ✔ Invoice Single Source of Truth
# ✔ Includes Subscription Snapshot
# ✔ Includes Payments (FINAL FIX)
# ✔ No Side Effects
# ✔ Frontend Compatible (NO CHANGES REQUIRED)
# ============================================================

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from billing_center.models import Invoice, Payment


@login_required
def invoice_detail(request, invoice_id):
    """
    GET /api/system/invoices/<id>/

    Returns:
    - Invoice core data
    - Subscription snapshot (stored)
    - Payments related to this invoice
    """

    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "company",
            "subscription",
        ),
        id=invoice_id,
    )

    # ========================================================
    # 💳 Payments (Linked to Invoice)
    # ========================================================
    payments_qs = (
        Payment.objects
        .filter(invoice=invoice)
        .order_by("-paid_at", "-id")
    )

    payments = [
        {
            "id": p.id,
            "method": p.method,
            "amount": float(p.amount),
            "status": getattr(p, "status", "SUCCESS"),
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "reference": p.reference_number,
            "created_at": p.created_at.isoformat()
            if hasattr(p, "created_at") and p.created_at else None,
        }
        for p in payments_qs
    ]

    # ========================================================
    # 📦 Response (FINAL CONTRACT)
    # ========================================================
    return JsonResponse(
        {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "issue_date": invoice.issue_date.isoformat()
            if invoice.issue_date else None,

            "subtotal_amount": float(
                invoice.subtotal_amount
                if invoice.subtotal_amount is not None
                else invoice.total_amount
            ),

            "discount_amount": float(
                invoice.discount_amount or 0
            ),

            "total_amount": float(invoice.total_amount),

            "total_after_discount": float(
                invoice.total_after_discount
                if invoice.total_after_discount is not None
                else invoice.total_amount
            ),

            # -----------------------------
            # 🧩 Subscription Snapshot
            # -----------------------------
            "subscription_snapshot": invoice.subscription_snapshot,

            # -----------------------------
            # 💳 Payments (NEW)
            # -----------------------------
            "payments": payments,
        },
        status=200,
    )
