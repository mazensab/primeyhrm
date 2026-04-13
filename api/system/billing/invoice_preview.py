# ============================================================
# 🧾 SYSTEM — Invoice Preview API
# Mham Cloud | PRODUCT-AWARE SAFE
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from billing_center.models import Discount, SubscriptionPlan

VAT_RATE = 0.15


@require_GET
def invoice_preview(request):
    """
    GET /api/system/billing/preview/

    Query params:
    - plan_id
    - billing_cycle = monthly | yearly
    - discount_code (optional)
    """

    plan_id = request.GET.get("plan_id")
    billing_cycle = (request.GET.get("billing_cycle") or "monthly").strip().lower()
    discount_code = (request.GET.get("discount_code") or "").strip()

    if not plan_id:
        return JsonResponse({"error": "plan_id required"}, status=400)

    if billing_cycle not in {"monthly", "yearly"}:
        return JsonResponse(
            {"error": "billing_cycle must be monthly or yearly"},
            status=400,
        )

    try:
        plan = SubscriptionPlan.objects.select_related("product").get(
            id=plan_id,
            is_active=True,
        )
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({"error": "Invalid plan"}, status=404)

    # =====================================
    # Plan Price
    # =====================================
    if billing_cycle == "yearly":
        price = float(plan.price_yearly or 0)
    else:
        price = float(plan.price_monthly or 0)

    discount_amount = 0.0
    discount_payload = None

    # =====================================
    # Discount
    # =====================================
    if discount_code:
        discount = (
            Discount.objects
            .filter(code__iexact=discount_code, is_active=True)
            .first()
        )

        if discount:
            if discount.applies_to_all_plans or discount.allowed_plans.filter(id=plan.id).exists():
                if discount.discount_type == "fixed":
                    discount_amount = float(discount.value or 0)

                elif discount.discount_type == "percentage":
                    discount_amount = price * float(discount.value or 0) / 100

                discount_payload = {
                    "code": discount.code,
                    "type": discount.discount_type,
                    "value": float(discount.value or 0),
                }

    subtotal = max(price - discount_amount, 0.0)
    vat = subtotal * VAT_RATE
    total = subtotal + vat

    product = getattr(plan, "product", None)

    return JsonResponse(
        {
            "plan": {
                "id": plan.id,
                "name": plan.name,
                "product": {
                    "id": product.id,
                    "code": product.code,
                    "name": product.name,
                } if product else None,
            },
            "billing_cycle": billing_cycle,
            "discount": discount_payload,
            "pricing": {
                "price": price,
                "discount_amount": discount_amount,
                "subtotal": subtotal,
                "vat": vat,
                "total": total,
            },
        }
    )