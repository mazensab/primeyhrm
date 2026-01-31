# ============================================================
# 🟦 Holiday Resolver Engine — Phase H.3
# Single Source of Truth for Company Holidays
# ============================================================

from datetime import date
from typing import Optional

from attendance_center.models import CompanyHoliday
from company_manager.models import Company


class HolidayResolver:
    """
    🧠 Holiday Resolver Engine

    مسؤول عن:
    - تحديد هل اليوم إجازة رسمية للشركة
    - إرجاع كائن الإجازة أو None

    ❌ لا يتعامل مع:
    - Leave
    - Weekend
    - Attendance Status
    """

    @staticmethod
    def resolve(
        target_date: date,
        company: Company
    ) -> Optional[CompanyHoliday]:
        """
        🔍 هل هذا التاريخ إجازة رسمية؟

        Returns:
            CompanyHoliday | None
        """

        if not target_date or not company:
            return None

        try:
            return (
                CompanyHoliday.objects
                .filter(
                    company=company,
                    is_active=True,
                    start_date__lte=target_date,
                    end_date__gte=target_date,
                )
                .order_by("start_date")
                .first()
            )
        except Exception:
            # 🛡️ Silent fail (no side effects)
            return None

    # ========================================================
    # 🧠 Helper Shortcuts
    # ========================================================
    @staticmethod
    def is_holiday(
        target_date: date,
        company: Company
    ) -> bool:
        """
        هل اليوم إجازة؟
        """
        return HolidayResolver.resolve(
            target_date,
            company
        ) is not None

    @staticmethod
    def get_holiday_name(
        target_date: date,
        company: Company
    ) -> Optional[str]:
        """
        اسم الإجازة إن وجدت
        """
        holiday = HolidayResolver.resolve(
            target_date,
            company
        )
        return holiday.name if holiday else None

    @staticmethod
    def is_paid_holiday(
        target_date: date,
        company: Company
    ) -> bool:
        """
        هل الإجازة مدفوعة؟
        """
        holiday = HolidayResolver.resolve(
            target_date,
            company
        )
        if not holiday:
            return False

        # أولوية: Holiday نفسها → HolidayType
        if holiday.is_paid is not None:
            return holiday.is_paid

        if holiday.holiday_type:
            return holiday.holiday_type.is_paid

        return False
