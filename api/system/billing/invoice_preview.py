# ============================================================
# 🧾 SYSTEM — Invoice Preview API
# Primey HR Cloud
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from billing_center.models import SubscriptionPlan
from billing_center.models import Discount

VAT_RATE = 0.15


@require_GET
def invoice_preview(request):
    """
    GET /api/system/billing/preview/
    """

    plan_id = request.GET.get("plan_id")
    billing_cycle = request.GET.get("billing_cycle", "monthly")
    discount_code = request.GET.get("discount_code")

    if not plan_id:
        return JsonResponse({"error": "plan_id required"}, status=400)

    try:
        plan = SubscriptionPlan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        return JsonResponse({"error": "Invalid plan"}, status=404)

    # =====================================
    # Plan Price
    # =====================================

    if billing_cycle == "yearly":
        price = float(plan.price_yearly or 0)
    else:
        price = float(plan.price_monthly or 0)

    discount_amount = 0

    # =====================================
    # Discount
    # =====================================

    if discount_code:

        discount = Discount.objects.filter(
            code__iexact=discount_code,
            is_active=True
        ).first()

        if discount:

            if discount.discount_type == "fixed":
                discount_amount = float(discount.value)

            elif discount.discount_type == "percentage":
                discount_amount = price * float(discount.value) / 100

    subtotal = max(price - discount_amount, 0)

    vat = subtotal * VAT_RATE

    total = subtotal + vat

    return JsonResponse({
        "price": price,
        "discount": discount_amount,
        "subtotal": subtotal,
        "vat": vat,
        "total": total,
    })