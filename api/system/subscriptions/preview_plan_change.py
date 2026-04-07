# ============================================================
# 📂 api/system/subscriptions/preview_plan_change.py
# Mham Cloud
# Preview Plan Change API
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json

from billing_center.models import (
    CompanySubscription,
    SubscriptionPlan
)


# ============================================================
# Helper
# ============================================================

def _json_payload(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


# ============================================================
# API
# POST /api/system/subscriptions/<id>/preview-plan-change/
# ============================================================

@require_POST
@login_required
def preview_plan_change(request, subscription_id):

    payload = _json_payload(request)

    if not payload:
        return JsonResponse({"error": "Invalid payload"}, status=400)

    plan_id = payload.get("plan_id")

    if not plan_id:
        return JsonResponse({"error": "plan_id required"}, status=400)

    try:
        subscription = CompanySubscription.objects.get(id=subscription_id)
    except CompanySubscription.DoesNotExist:
        return JsonResponse({"error": "Subscription not found"}, status=404)

    try:
        new_plan = SubscriptionPlan.objects.get(id=plan_id)
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({"error": "Plan not found"}, status=404)

    current_plan = subscription.plan

    current_price = current_plan.price_yearly or 0
    new_price = new_plan.price_yearly or 0

    # --------------------------------------------------------
    # Same Plan
    # --------------------------------------------------------

    if current_plan.id == new_plan.id:

        return JsonResponse({
            "type": "same_plan",
            "message": "Already on this plan"
        })

    # --------------------------------------------------------
    # Upgrade
    # --------------------------------------------------------

    if new_price > current_price:

        difference = new_price - current_price

        return JsonResponse({

            "type": "upgrade",

            "current_plan": {
                "id": current_plan.id,
                "name": current_plan.name,
                "price": current_price
            },

            "new_plan": {
                "id": new_plan.id,
                "name": new_plan.name,
                "price": new_price
            },

            "amount_due": difference,

            "message": "You will be charged the price difference"
        })

    # --------------------------------------------------------
    # Downgrade
    # --------------------------------------------------------

    return JsonResponse({

        "type": "downgrade",

        "current_plan": {
            "id": current_plan.id,
            "name": current_plan.name,
            "price": current_price
        },

        "new_plan": {
            "id": new_plan.id,
            "name": new_plan.name,
            "price": new_price
        },

        "amount_due": 0,

        "message": "Plan will change at next renewal"
    })