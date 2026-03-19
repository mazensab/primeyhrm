# ============================================================
# 🧾 System Invoices List API
# Primey HR Cloud
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

from billing_center.models import Invoice, Payment


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
def system_invoices_list(request):
    qs = (
        Invoice.objects
        .select_related("company", "subscription__plan")
        .order_by("-issue_date", "-id")
    )

    # --------------------------------------------------------
    # Filters
    # --------------------------------------------------------
    number = request.GET.get("number")
    company = request.GET.get("company")
    status = request.GET.get("status")

    if number:
        qs = qs.filter(invoice_number__icontains=number)

    if company:
        qs = qs.filter(company__name__icontains=company)

    if status:
        qs = qs.filter(status=status)

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------
    try:
        page = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        page = 1

    try:
        page_size = int(request.GET.get("page_size", 25))
    except (TypeError, ValueError):
        page_size = 25

    if page < 1:
        page = 1

    if page_size < 1:
        page_size = 25

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
            Payment.objects
            .filter(invoice=inv)
            .order_by("-paid_at", "-id")
            .first()
        )

        results.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "company_id": inv.company_id,
            "company_name": inv.company.name if inv.company else None,
            "plan_name": (
                inv.subscription.plan.name
                if inv.subscription and inv.subscription.plan
                else None
            ),
            "total_amount": str(inv.total_amount),
            "status": inv.status,
            "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "payment_method": payment.method if payment else None,
            "currency": "SAR",
        })

    return success({
        "results": results,
        "count": total,
        "page": page,
        "page_size": page_size,
    })