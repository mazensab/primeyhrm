# ============================================================
# 🧾 SYSTEM — All Invoices (Super Admin)
# Primey HR Cloud
# ============================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery

from billing_center.models import Invoice, PaymentTransaction
from company_manager.models import CompanyUser


# ============================================================
# 🔐 SYSTEM Permission
# ============================================================

def system_permission_required(permission: str):
    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return JsonResponse(
                    {"status": "error", "message": "Unauthorized"},
                    status=401,
                    json_dumps_params={"ensure_ascii": False},
                )

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            try:
                company_user = CompanyUser.objects.get(user=request.user)
            except CompanyUser.DoesNotExist:
                return JsonResponse(
                    {"status": "error", "message": "Invalid system user"},
                    status=403,
                    json_dumps_params={"ensure_ascii": False},
                )

            if company_user.role.code not in ("SYSTEM_ADMIN", "SYSTEM_OWNER"):
                return JsonResponse(
                    {"status": "error", "message": "Permission denied"},
                    status=403,
                    json_dumps_params={"ensure_ascii": False},
                )

            return view_func(request, *args, **kwargs)

        return _wrapped
    return decorator


# ============================================================
# 🔁 Response Helper
# ============================================================

def success(data=None):
    return JsonResponse(
        {"status": "success", "data": data or {}},
        status=200,
        json_dumps_params={"ensure_ascii": False},
    )


# ============================================================
# 📄 SYSTEM — Invoices List (WITH PAYMENT METHOD)
# ============================================================

@login_required
@system_permission_required("billing.read")
def system_invoices(request):
    """
    ============================================================
    📄 List ALL invoices across ALL companies
    ✔ Includes subscription snapshot
    ✔ Includes payment_method from latest PAID transaction
    ============================================================
    """

    # --------------------------------------------------------
    # 🔗 Subquery: latest successful payment per invoice
    # --------------------------------------------------------
    latest_payment_method = Subquery(
        PaymentTransaction.objects.filter(
            invoice_id=OuterRef("pk"),
            status="PAID",
        )
        .order_by("-processed_at")
        .values("payment_method")[:1]
    )

    invoices = (
        Invoice.objects
        .select_related(
            "company",
            "subscription",
            "subscription__plan",
        )
        .annotate(payment_method=latest_payment_method)
        .order_by("-issue_date")
    )

    results = []

    for inv in invoices:
        sub = inv.subscription

        results.append({
            "id": inv.id,
            "number": inv.invoice_number,

            # 🏢 Company
            "company_id": inv.company_id,
            "company_name": inv.company.name if inv.company else None,

            # 💰 Invoice
            "total_amount": str(inv.total_amount),
            "currency": "SAR",
            "status": inv.status,
            "issued_at": inv.issue_date,

            # 💳 Payment
            "payment_method": inv.payment_method,  # ✅ HERE

            # 📦 Subscription snapshot
            "subscription_id": sub.id if sub else None,
            "plan_name": sub.plan.name if sub and sub.plan else None,
            "period_start": sub.start_date if sub else None,
            "period_end": sub.end_date if sub else None,
        })

    return success({
        "results": results,
        "count": len(results),
    })
