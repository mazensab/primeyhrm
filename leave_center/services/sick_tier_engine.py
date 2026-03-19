# ================================================================
# 🏥 Sick Tier Engine — Saudi Labour Law 2025
# Phase P5
# ================================================================

from datetime import timedelta
from django.utils import timezone
from leave_center.models import LeaveRequest


class SickTierEngine:
    """
    يحسب:
    - عدد أيام الإجازات المرضية خلال آخر 365 يوم
    - الشريحة الحالية
    - نسبة الأجر المستحقة
    """

    FULL_PAY_DAYS = 30
    PARTIAL_PAY_DAYS = 60
    NO_PAY_DAYS = 30

    def __init__(self, employee):
        self.employee = employee
        self.today = timezone.now().date()

    # ------------------------------------------------------------
    # 🔎 حساب الأيام المرضية خلال 365 يوم
    # ------------------------------------------------------------
    def get_used_days_last_year(self):
        one_year_ago = self.today - timedelta(days=365)

        sick_leaves = LeaveRequest.objects.filter(
            employee=self.employee,
            leave_type__category="sick",
            status="approved",
            start_date__gte=one_year_ago,
        )

        total_days = sum(l.total_days for l in sick_leaves)
        return total_days

    # ------------------------------------------------------------
    # ⚖ تحديد الشريحة الحالية
    # ------------------------------------------------------------
    def get_current_tier(self):
        used = self.get_used_days_last_year()

        if used < self.FULL_PAY_DAYS:
            return "full", 100

        elif used < self.FULL_PAY_DAYS + self.PARTIAL_PAY_DAYS:
            return "partial", 75

        elif used < self.FULL_PAY_DAYS + self.PARTIAL_PAY_DAYS + self.NO_PAY_DAYS:
            return "unpaid", 0

        else:
            return "exceeded", 0

    # ------------------------------------------------------------
    # 🛡 تحقق هل يمكن قبول طلب جديد
    # ------------------------------------------------------------
    def can_apply(self, requested_days):
        used = self.get_used_days_last_year()
        total_allowed = (
            self.FULL_PAY_DAYS
            + self.PARTIAL_PAY_DAYS
            + self.NO_PAY_DAYS
        )

        if used + requested_days > total_allowed:
            return False, "تجاوز الحد الأعلى للإجازات المرضية خلال سنة."

        return True, None