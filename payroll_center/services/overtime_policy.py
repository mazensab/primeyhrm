# ================================================================
# 💰 Overtime Policy Engine — Clean Version
# ================================================================

from decimal import Decimal
from payroll_center.models import CompanyOvertimeSetting


class OvertimePolicy:

    def __init__(self, company):
        self.company = company
        self.settings = self._load_settings()

    def _load_settings(self):
        try:
            return CompanyOvertimeSetting.objects.get(company=self.company)
        except CompanyOvertimeSetting.DoesNotExist:
            return None

    def get_multiplier(self, overtime_type: str) -> float:

        if not self.settings:
            return 1.0

        if overtime_type == "weekend_overtime":
            return float(self.settings.weekend_multiplier)

        if overtime_type == "holiday_overtime":
            return float(self.settings.holiday_multiplier)

        return float(self.settings.normal_multiplier)

    def calculate_overtime_amount(
        self,
        overtime_minutes: int,
        hourly_rate: float,
        overtime_type: str,
    ) -> Decimal:

        if not overtime_minutes or overtime_minutes <= 0:
            return Decimal("0.00")

        multiplier = Decimal(str(self.get_multiplier(overtime_type)))
        hours = Decimal(overtime_minutes) / Decimal("60")
        rate = Decimal(str(hourly_rate))

        return (hours * rate * multiplier).quantize(Decimal("0.01"))
