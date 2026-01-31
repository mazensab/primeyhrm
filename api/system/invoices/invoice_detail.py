# ============================================================
# 📄 api/system/invoices/invoice_detail.py
# ⚙️ Version: V1.0 Ultra Stable
# Primey HR Cloud | System Invoice Detail
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from billing_center.models import Invoice
from company_manager.permissions import system_permission_required


# ============================================================
# 🔁 Response Helpers
# ============================================================

def success(data):
    return JsonResponse(
        data,
        status=200,
        json_dumps_params={"ensure_ascii": False},
    )


# ============================================================
# 🧾 SYSTEM — Invoice Detail
# ============================================================

@require_GET
@login_required
@system_permission_required("SYSTEM_ADMIN")
def system_invoice_detail(request, invoice_id):
    """
    ============================================================
    🧾 System Invoice Detail API
    ------------------------------------------------------------
    ✔ Single invoice
    ✔ Subscription snapshot
    ✔ Plan info
    ✔ Company info
    ✔ Payments ready (future)
    ✔ Read-only
    ✔ Impersonation safe
    ============================================================
    """

    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "company",
            "subscription",
            "subscription__plan",
        ),
        id=invoice_id
    )

    subscription = invoice.subscription
    plan = subscription.plan if subscription else None

    data = {
        # ---------------- Invoice ----------------
        "id": invoice.id,
        "number": invoice.number,
        "status": invoice.status,
        "total_amount": float(invoice.total_amount),
        "currency": invoice.currency,
        "issued_at": (
            invoice.issued_at.isoformat()
            if invoice.issued_at
            else None
        ),

        # ---------------- Company ----------------
        "company": {
            "id": invoice.company_id,
            "name": invoice.company.name if invoice.company else None,
        },

        # ---------------- Subscription Snapshot ----------------
        "subscription": {
            "id": subscription.id if subscription else None,
            "starts_at": (
                subscription.starts_at.isoformat()
                if subscription and subscription.starts_at
                else None
            ),
            "ends_at": (
                subscription.ends_at.isoformat()
                if subscription and subscription.ends_at
                else None
            ),
            "plan": {
                "id": plan.id if plan else None,
                "name": plan.name if plan else None,
                "price": float(plan.price) if plan else None,
                "duration": plan.duration if plan else None,
            } if plan else None,
        },
    }

    return success(data)
