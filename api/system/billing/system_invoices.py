# ============================================================
# 🧾 SYSTEM — All Invoices (Super Admin)
# Mham Cloud | PRODUCT-AWARE SAFE
# ============================================================

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import OuterRef, Subquery

from billing_center.models import Invoice, Payment, PaymentTransaction
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

            role = getattr(company_user, "role", None)
            role_code = getattr(role, "code", None)

            if role_code not in ("SYSTEM_ADMIN", "SYSTEM_OWNER"):
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
# 📄 SYSTEM — Invoices List
# ============================================================

@login_required
@system_permission_required("billing.read")
def system_invoices(request):
    """
    ============================================================
    📄 List ALL invoices across ALL companies
    ✔ Includes subscription snapshot
    ✔ Includes payment_method
    ✔ PRODUCT-AWARE
    ============================================================
    """

    # --------------------------------------------------------
    # Latest successful PaymentTransaction per invoice
    # --------------------------------------------------------
    latest_transaction_payment_method = Subquery(
        PaymentTransaction.objects.filter(
            invoice_id=OuterRef("pk"),
            status="success",
        )
        .order_by("-processed_at", "-created_at", "-id")
        .values("payment_method")[:1]
    )

    # --------------------------------------------------------
    # Latest Payment per invoice
    # --------------------------------------------------------
    latest_payment_method = Subquery(
        Payment.objects.filter(
            invoice_id=OuterRef("pk"),
        )
        .order_by("-paid_at", "-id")
        .values("method")[:1]
    )

    invoices = (
        Invoice.objects
        .select_related(
            "company",
            "subscription",
            "subscription__plan",
            "subscription__product",
        )
        .annotate(
            transaction_payment_method=latest_transaction_payment_method,
            direct_payment_method=latest_payment_method,
        )
        .order_by("-issue_date", "-id")
    )

    results = []

    for inv in invoices:
        sub = inv.subscription
        resolved_product = getattr(sub, "resolved_product", None) if sub else None

        payment_method = inv.direct_payment_method or inv.transaction_payment_method

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
            "issued_at": inv.issue_date.isoformat() if inv.issue_date else None,
            "billing_reason": getattr(inv, "billing_reason", None),

            # 💳 Payment
            "payment_method": payment_method,

            # 📦 Subscription
            "subscription_id": sub.id if sub else None,
            "product": {
                "id": resolved_product.id,
                "code": resolved_product.code,
                "name": resolved_product.name,
            } if resolved_product else None,
            "plan_name": sub.plan.name if sub and sub.plan else None,
            "period_start": sub.start_date.isoformat() if sub and sub.start_date else None,
            "period_end": sub.end_date.isoformat() if sub and sub.end_date else None,
        })

    return success({
        "results": results,
        "count": len(results),
    })