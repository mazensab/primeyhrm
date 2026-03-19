# ===============================================================
# 🧾 Company Subscription — SYSTEM API (SAFE)
# Primey HR Cloud
# ===============================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from billing_center.models import CompanySubscription


@login_required
@require_GET
def system_company_subscription(request, company_id):
    """
    GET /api/system/companies/<company_id>/subscription/
    """

    try:

        sub = (
            CompanySubscription.objects
            .select_related("plan")
            .filter(company_id=company_id)
            .order_by("-id")
            .first()
        )

        if not sub:
            return JsonResponse({
                "status": "success",
                "subscription": None
            })

        data = {
            "id": sub.id,
            "plan": getattr(sub.plan, "name", None),
            "status": getattr(sub, "status", None),
            "billing_cycle": getattr(sub, "billing_cycle", None),
            "started_at": getattr(sub, "start_date", None),
            "ends_at": getattr(sub, "end_date", None),
        }

        return JsonResponse({
            "status": "success",
            "subscription": data
        })

    except Exception as e:

        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)