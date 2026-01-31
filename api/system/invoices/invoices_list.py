# ============================================================
# 🧾 System Invoices List API — WITH PAYMENT METHOD
# Primey HR Cloud | FINAL FIX
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.utils.timezone import make_aware
from datetime import datetime

from billing_center.models import Invoice
from billing_center.models import PaymentTransaction
from company_manager.permissions import system_permission_required


# ============================================================
# 🔁 Response Helpers
# ============================================================

def success(data):
    return JsonResponse(
        {"status": "success", "data": data},
        status=200,
        json_dumps_params={"ensure_ascii": False},
    )


# ============================================================
# 🧾 SYSTEM — Invoices List
# ============================================================

@require_GET
@login_required
@system_permission_required("SYSTEM_ADMIN")
def system_invoices_list(request):

    qs = (
        Invoice.objects
        .select_related("company")
        .order_by("-issued_at", "-id")
    )

    # --------------------------------------------------------
    # Filters
    # --------------------------------------------------------
    number = request.GET.get("number")
    company = request.GET.get("company")
    status = request.GET.get("status")

    if number:
        qs = qs.filter(number__icontains=number)

    if company:
        qs = qs.filter(company__name__icontains=company)

    if status:
        qs = qs.filter(status=status)

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 25))

    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size

    qs = qs[start:end]

    # --------------------------------------------------------
    # Serialize
    # --------------------------------------------------------
    results = []

    for inv in qs:

        payment = (
            PaymentTransaction.objects
            .filter(
                invoice=inv,
                status__in=["PAID", "SUCCESS"]
            )
            .order_by("-created_at")
            .first()
        )

        results.append({
            "id": inv.id,
            "number": inv.number,
            "company_id": inv.company_id,
            "company_name": inv.company.name if inv.company else None,
            "total_amount": str(inv.total_amount),
            "currency": inv.currency,
            "status": inv.status,
            "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,

            # ⭐ FIX HERE
            "payment_method": payment.method if payment else None,
        })

    return success({
        "results": results,
        "count": total,
        "page": page,
        "page_size": page_size,
    })
