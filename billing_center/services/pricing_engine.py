# ============================================================
# 💳 Pricing Engine — V1.0 Ultra Stable
# Primey HR Cloud
# ============================================================
# ✔ Pure Business Logic (NO DB writes)
# ✔ Applies Coupon Discount (Discount model)
# ✔ Safe validations: active + date + plan applicability
# ✔ Supports: discount_type / type
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any

from django.utils.timezone import now

from billing_center.models import Discount


# =========================
# Utils
# =========================

def _to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _money(value: Decimal) -> Decimal:
    # 2 decimals, standard rounding
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _is_discount_valid_today(discount: Discount, today: date) -> bool:
    if getattr(discount, "is_active", False) is False:
        return False

    start = getattr(discount, "start_date", None)
    end = getattr(discount, "end_date", None)

    if start and today < start:
        return False
    if end and today > end:
        return False

    return True


def _discount_applies_to_plan(discount: Discount, plan) -> bool:
    if getattr(discount, "applies_to_all_plans", False):
        return True

    # If the model has M2M plans relation, enforce it
    plans_rel = getattr(discount, "plans", None)
    if plans_rel is not None and hasattr(plans_rel, "filter"):
        try:
            return plans_rel.filter(id=getattr(plan, "id", None)).exists()
        except Exception:
            return False

    # If no relation exists, treat as not applicable (safer)
    return False


def _apply_coupon_discount(base_price: Decimal, discount: Discount) -> Dict[str, Any]:
    discount_type = getattr(discount, "discount_type", None) or getattr(discount, "type", None)
    discount_value = _to_decimal(getattr(discount, "value", "0"))

    discount_amount = Decimal("0")

    if discount_type == "percentage":
        # percentage value: 10 means 10%
        discount_amount = (base_price * discount_value / Decimal("100"))
    elif discount_type == "fixed":
        discount_amount = discount_value
    else:
        # Unknown type — ignore safely
        discount_type = None
        discount_value = Decimal("0")
        discount_amount = Decimal("0")

    # Cap discount: cannot exceed base
    if discount_amount > base_price:
        discount_amount = base_price

    discount_amount = _money(discount_amount)

    return {
        "code": getattr(discount, "code", None),
        "type": discount_type,
        "value": float(_money(discount_value)),
        "amount": float(discount_amount),
    }


# =========================
# Public API
# =========================

def calculate_subscription_pricing(
    *,
    plan,
    duration: str,
    discount_code: Optional[str] = None,
    today: Optional[date] = None,
) -> Dict[str, Any]:
    """
    يحسب سعر الاشتراك النهائي (Snapshot) بطريقة موحدة:
    - base_price من plan حسب duration
    - يطبق كود خصم (Coupon) إن وجد
    - لا يقوم بأي حفظ في DB

    Returns:
        {
          "duration": "monthly|yearly",
          "base_price": float,
          "final_price": float,
          "discount": {code,type,value,amount} | None,
          "errors": []  # empty means OK
        }
    """
    errors = []

    duration = (duration or "").strip().lower()
    if duration not in ("monthly", "yearly"):
        errors.append("INVALID_DURATION")

    # base price from plan
    base_price = Decimal("0")
    if not errors:
        if duration == "monthly":
            base_price = _to_decimal(getattr(plan, "price_monthly", 0))
        else:
            base_price = _to_decimal(getattr(plan, "price_yearly", 0))

    base_price = _money(base_price)

    discount_snapshot = None
    final_price = base_price

    if today is None:
        today = now().date()

    # Apply coupon discount if provided
    if discount_code:
        code = str(discount_code).strip()
        if code:
            try:
                discount = Discount.objects.get(code=code)
            except Discount.DoesNotExist:
                errors.append("DISCOUNT_NOT_FOUND")
                discount = None

            if discount is not None:
                if not _is_discount_valid_today(discount, today):
                    errors.append("DISCOUNT_NOT_ACTIVE_OR_EXPIRED")
                elif not _discount_applies_to_plan(discount, plan):
                    errors.append("DISCOUNT_NOT_APPLICABLE_TO_PLAN")
                else:
                    discount_snapshot = _apply_coupon_discount(base_price, discount)
                    final_price = _money(base_price - _to_decimal(discount_snapshot["amount"]))

    return {
        "duration": duration,
        "base_price": float(base_price),
        "final_price": float(final_price),
        "discount": discount_snapshot,
        "errors": errors,
    }
