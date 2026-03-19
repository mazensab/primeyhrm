# ============================================================
# 🧾 Company Invoices API
# Primey HR Cloud
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

from billing_center.models import Invoice
from billing_center.models import PaymentTransaction


# ============================================================
# 🔁 Response Helper
# ============================================================

def success(data):
    return JsonResponse(
        {"status": "success", "data": data},
        json_dumps_params={"ensure_ascii": False},
    )


# ============================================================
# 🧾 SYSTEM — Company Invoices
# ============================================================

@require_GET
@login_required
def system_company_invoices(request, company_id):

    invoices = (
        Invoice.objects
        .filter(company_id=company_id)
        .select_related("company")
        .order_by("-issue_date", "-id")
    )

    results = []

    for inv in invoices:

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
            "number": inv.invoice_number,
            "company_id": inv.company_id,
            "company_name": inv.company.name if inv.company else None,
            "total_amount": str(inv.total_amount),

            # العملة ثابتة
            "currency": "SAR",

            "status": inv.status,
            "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,

            # بدون كسر النظام
            "payment_method": getattr(payment, "payment_method", None) if payment else None,
        })

    return success({
        "results": results,
        "count": len(results),
    })