# ============================================================
# 📦 SYSTEM — Billing Subscriptions API (LIST)
# Primey HR Cloud | V1.0 Ultra Stable
# ============================================================
# ✔ READ ONLY
# ✔ Super Admin only
# ✔ Source of truth: CompanySubscription
# ✔ Used by /system/billing/subscriptions
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

from billing_center.models import CompanySubscription


@require_GET
@login_required
def list_billing_subscriptions(request):
    """
    List all company subscriptions (System Billing)

    Response shape MUST match frontend expectations.
    """

    # ---------------------------------------------------------
    # 🔐 Super Admin only
    # ---------------------------------------------------------
    if not request.user.is_superuser:
        return JsonResponse(
            {"detail": "Forbidden"},
            status=403,
        )

    # ---------------------------------------------------------
    # 📦 Query
    # ---------------------------------------------------------
    subs = (
        CompanySubscription.objects
        .select_related("company", "plan")
        .order_by("-id")
    )

    items = []

    for sub in subs:
        items.append({
            "id": sub.id,
            "company_id": sub.company.id if sub.company else None,
            "company_name": sub.company.name if sub.company else "-",
            "plan_name": sub.plan.name if sub.plan else "-",
            "status": sub.status,
            "start_date": (
                sub.start_date.isoformat()
                if sub.start_date else None
            ),
            "end_date": (
                sub.end_date.isoformat()
                if sub.end_date else None
            ),
        })

    # ---------------------------------------------------------
    # ✅ Response
    # ---------------------------------------------------------
    return JsonResponse(
        {
            "count": len(items),
            "items": items,
        },
        status=200,
    )
