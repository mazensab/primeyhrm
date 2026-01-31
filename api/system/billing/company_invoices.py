from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from billing_center.models import Invoice
from company_manager.models import Company

# ✅ التصحيح هنا فقط
from api.system.users_actions import system_permission_required


# ================================================================
# 🔒 Response Helpers
# ================================================================
def success(data):
    return JsonResponse(
        {"status": "success", "items": data},
        status=200,
        json_dumps_params={"ensure_ascii": False},
    )


def error(msg, status=400):
    return JsonResponse(
        {"status": "error", "message": msg},
        status=status,
        json_dumps_params={"ensure_ascii": False},
    )


# ================================================================
# 🧾 Company Invoices (ALL SUBSCRIPTIONS)
# ================================================================
@login_required
@system_permission_required("companies.view")
def company_invoices(request, company_id: int):
    """
    ============================================================
    🧾 Company Invoices API
    ------------------------------------------------------------
    ✔ Returns ALL invoices for the company
    ✔ Across ALL subscriptions (old + new)
    ✔ Sorted by issue_date DESC
    ✔ System Admin only
    ✔ Impersonation safe
    ============================================================
    """

    company = get_object_or_404(Company, id=company_id)

    invoices = (
        Invoice.objects
        .filter(company=company)
        .select_related("subscription")
        .order_by("-issue_date", "-id")
    )

    items = []
    for invoice in invoices:
        items.append({
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "total_after_discount": float(invoice.total_after_discount or 0),
            "paid_amount": float(invoice.paid_amount or 0),
            "issue_date": invoice.issue_date,
            "subscription_id": invoice.subscription_id,
            "primary_payment": invoice.primary_payment_id is not None,
        })

    return success(items)
