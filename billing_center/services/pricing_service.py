# ============================================================
# 💰 Pricing Service — V1 Ultra Stable (FINAL)
# Primey HR Cloud
# ============================================================
# ✔ Single Source of Truth
# ✔ No DB Writes
# ✔ Supports Discounts
# ✔ Ready for Public Signup & System Flows
# ============================================================

from decimal import Decimal
from django.utils.timezone import now

from billing_center.models import Discount


# ============================================================
# 🚨 Exceptions
# ============================================================

class PricingError(Exception):
    """Base pricing exception"""


class InvalidPricingContext(PricingError):
    pass


# ============================================================
# 🧠 Core Pricing Calculator
# ============================================================

def calculate_pricing(context: dict) -> dict:
    """
    Calculate final pricing snapshot based on context.

    Expected context:
    {
        "plan": Plan instance,
        "billing_cycle": "monthly" | "yearly",
        "employees_count": int,
        "discount_code": str | None
    }
    """

    # --------------------------------------------------------
    # 🧪 Validate Context
    # --------------------------------------------------------
    required_keys = ["plan", "billing_cycle", "employees_count"]

    for key in required_keys:
        if key not in context:
            raise InvalidPricingContext(f"Missing required key: {key}")

    plan = context["plan"]
    billing_cycle = context["billing_cycle"]
    employees_count = context["employees_count"]
    discount_code = context.get("discount_code")

    if billing_cycle not in ("monthly", "yearly"):
        raise InvalidPricingContext("Invalid billing_cycle")

    if employees_count <= 0:
        raise InvalidPricingContext("employees_count must be > 0")

    # --------------------------------------------------------
    # 💵 Base Price
    # --------------------------------------------------------
    if billing_cycle == "monthly":
        base_price = Decimal(plan.monthly_price)
    else:
        base_price = Decimal(plan.yearly_price)

    final_price = base_price
    discount_snapshot = None

    # --------------------------------------------------------
    # 🏷️ Apply Discount (If Any)
    # --------------------------------------------------------
    if discount_code:
        discount = _get_valid_discount(
            code=discount_code,
            plan=plan,
        )

        if discount:
            discount_amount = _calculate_discount_amount(
                base_price=base_price,
                discount=discount,
            )

            final_price = max(
                Decimal("0.00"),
                base_price - discount_amount
            )

            discount_snapshot = {
                "id": discount.id,
                "code": discount.code,
                "type": discount.discount_type,
                "value": float(discount.value),
                "amount": float(discount_amount),
            }

    # --------------------------------------------------------
    # 📦 Final Snapshot
    # --------------------------------------------------------
    return {
        "base_price": float(base_price),
        "final_price": float(final_price),
        "currency": "SAR",
        "cycle": billing_cycle,
        "employees_count": employees_count,
        "discount": discount_snapshot,
    }


# ============================================================
# 🔎 Discount Helpers
# ============================================================

def _get_valid_discount(code, plan):
    """
    Validate discount:
    - Exists
    - Active
    - Within date
    - Applies to plan
    """

    today = now().date()

    try:
        discount = Discount.objects.get(
            code=code,
            is_active=True,
        )
    except Discount.DoesNotExist:
        return None

    if discount.start_date and discount.start_date > today:
        return None

    if discount.end_date and discount.end_date < today:
        return None

    if not discount.applies_to_all_plans:
        if not discount.plans.filter(id=plan.id).exists():
            return None

    return discount


def _calculate_discount_amount(base_price: Decimal, discount: Discount) -> Decimal:
    """
    Calculate discount amount safely.
    """

    if discount.discount_type == "percentage":
        return (base_price * Decimal(discount.value) / Decimal("100")).quantize(
            Decimal("0.01")
        )

    if discount.discount_type == "fixed":
        return min(
            Decimal(discount.value),
            base_price
        )

    return Decimal("0.00")
