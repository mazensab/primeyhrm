# ============================================================================
# 💳 System Payments API — V3 Ultra Stable (MODEL ALIGNED)
# Primey HR Cloud — Super Admin Level
# ============================================================================
# ✔ Dashboard: Latest Payments
# ✔ Company Payments Detail (?company_id)
# ✔ Uses PaymentTransaction (SOURCE OF TRUTH)
# ✔ Uses processed_at (NOT created_at bug)
# ✔ Safe / Clean / Deterministic
# ============================================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from billing_center.models import (
    PaymentTransaction,
    Invoice,
)
from company_manager.models import Company


# ============================================================================
# 🔵 Helper — Serialize PaymentTransaction
# ============================================================================

def serialize_payment(tx: PaymentTransaction) -> dict:
    invoice = tx.invoice
    company = tx.company or (invoice.company if invoice else None)

    return {
        "id": tx.id,
        "amount": float(tx.amount) if tx.amount else 0.0,
        "status": tx.status,  # COMPLETED / FAILED
        "payment_method": tx.payment_method,  # CASH / BANK / ...
        "invoice_id": invoice.id if invoice else None,
        "invoice_status": invoice.status if invoice else None,
        "company_id": company.id if company else None,
        "company_name": company.name if company else None,
        "processed_at": (
            tx.processed_at.isoformat()
            if tx.processed_at
            else None
        ),
        "created_by": tx.created_by.username if tx.created_by else None,
    }


# ============================================================================
# 💳 Latest Payments / Company Payments
# GET /api/system/payments/latest/
# GET /api/system/payments/latest/?company_id=<int>
# ============================================================================

@require_GET
def latest_payments(request):
    """
    System Payments Endpoint
    - Super Admin only (guarded by middleware)
    - Uses PaymentTransaction as Single Source of Truth
    """

    company_id = request.GET.get("company_id")

    transactions = (
        PaymentTransaction.objects
        .select_related(
            "invoice",
            "invoice__company",
            "company",
            "created_by",
        )
        .order_by("-processed_at")
    )

    # ------------------------------------------------------------
    # 🔹 Filter by Company (optional)
    # ------------------------------------------------------------
    company = None
    if company_id:
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return JsonResponse(
                {"error": "Company not found"},
                status=404,
            )

        transactions = transactions.filter(company=company)

    # ------------------------------------------------------------
    # 🔹 Limit (Dashboard = last 10 only)
    # ------------------------------------------------------------
    if not company_id:
        transactions = transactions[:10]

    results = [serialize_payment(tx) for tx in transactions]

    # ------------------------------------------------------------
    # 🔹 Response
    # ------------------------------------------------------------
    if company_id:
        return JsonResponse(
            {
                "success": True,
                "company": {
                    "id": company.id,
                    "name": company.name,
                },
                "results": results,
            },
            status=200,
        )

    return JsonResponse(
        {
            "success": True,
            "results": results,
        },
        status=200,
    )
