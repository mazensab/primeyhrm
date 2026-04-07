# ============================================================
# 📦 SYSTEM — Subscription Preview API
# Mham Cloud | V1.0 Ultra Stable
# ============================================================
# ✔ Single Source of Truth
# ✔ VAT 15%
# ✔ Discount support
# ✔ No side effects (READ ONLY)
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from billing_center.models import SubscriptionPlan, Discount


# ============================================================
# 🔐 Helpers
# ============================================================

def _get_payload(request):
    if request.body:
        try:
            import json
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            pass

    if request.POST:
        return request.POST.dict()

    return None


# ============================================================
# 🔍 Subscription Preview
# URL: /api/system/subscriptions/preview/
# ============================================================

@require_POST
@login_required
def subscription_preview(request):
    """
    حساب معاينة الاشتراك:
    - السعر الأساسي
    - الخصم
    - VAT
    - الإجمالي
    """

    payload = _get_payload(request)
    if not payload:
        return JsonResponse(
            {"detail": "Invalid or empty payload"},
            status=400,
        )

    plan_id = payload.get("plan_id")
    duration = payload.get("duration")
    discount_code = payload.get("discount_code")

    if not plan_id or duration not in ("monthly", "yearly"):
        return JsonResponse(
            {"detail": "Invalid plan_id or duration"},
            status=400,
        )

    # --------------------------------------------------------
    # 📦 Plan
    # --------------------------------------------------------
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse(
            {"detail": "Plan not found"},
            status=404,
        )

    if duration == "monthly":
        base_price = Decimal(plan.price_monthly)
    else:
        base_price = Decimal(plan.price_yearly)

    # --------------------------------------------------------
    # 🏷️ Discount
    # --------------------------------------------------------
    discount_amount = Decimal("0.00")

    if discount_code:
        try:
            discount = Discount.objects.get(
                code=discount_code,
                is_active=True,
            )

            if discount.discount_type == "percentage":
                discount_amount = (
                    base_price * Decimal(discount.value) / Decimal("100")
                )
            elif discount.discount_type == "fixed":
                discount_amount = Decimal(discount.value)

        except Discount.DoesNotExist:
            discount_amount = Decimal("0.00")

    price_after_discount = base_price - discount_amount
    if price_after_discount < 0:
        price_after_discount = Decimal("0.00")

    # --------------------------------------------------------
    # 🧾 VAT 15%
    # --------------------------------------------------------
    vat_amount = price_after_discount * Decimal("0.15")
    total = price_after_discount + vat_amount

    # --------------------------------------------------------
    # ✅ Response
    # --------------------------------------------------------
    return JsonResponse(
        {
            "plan_id": plan.id,
            "plan_name": plan.name,
            "duration": duration,
            "base_price": float(base_price),
            "discount_amount": float(discount_amount),
            "vat_amount": float(vat_amount),
            "total": float(total),
        },
        status=200,
    )
