# ================================================================
# 🟢 Absence Deduction Engine — V1.0 (Clean Layer)
# ================================================================
# ✔ FIXED_30 Policy Supported
# ✔ Pure Payroll Layer
# ✔ No dependency on Attendance Engine
# ✔ Company extensible
# ================================================================

from decimal import Decimal, ROUND_HALF_UP


class AbsenceDeductionEngine:
    """
    Responsible only for calculating absence deductions.
    """

    POLICY_FIXED_30 = "FIXED_30"

    def __init__(self, policy: str = POLICY_FIXED_30):
        self.policy = policy

    # ------------------------------------------------------------
    # Daily Rate Calculator
    # ------------------------------------------------------------
    def _calculate_daily_rate(self, monthly_salary: Decimal) -> Decimal:

        if self.policy == self.POLICY_FIXED_30:
            divisor = Decimal("30")
        else:
            divisor = Decimal("30")  # Default fallback

        return (monthly_salary / divisor).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    # ------------------------------------------------------------
    # Deduction Calculator
    # ------------------------------------------------------------
    def calculate_deduction(
        self,
        monthly_salary: Decimal,
        absent_days: int,
    ) -> Decimal:

        if absent_days <= 0:
            return Decimal("0.00")

        daily_rate = self._calculate_daily_rate(monthly_salary)

        deduction = daily_rate * Decimal(absent_days)

        return deduction.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
