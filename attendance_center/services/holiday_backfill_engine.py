# ================================================================
# 🧠 Holiday Backfill Engine — Phase H.6
# Primey HR Cloud | Attendance Center
# ================================================================

from django.db import transaction

from attendance_center.models import AttendanceRecord
from attendance_center.services.holiday_resolver import HolidayResolver


class HolidayBackfillEngine:
    """
    تحديث سجلات الحضور القديمة التي تقع ضمن إجازات رسمية
    """

    @classmethod
    def run(cls, company, start_date=None, end_date=None, dry_run=False):
        """
        :param company: Company instance
        :param start_date: date | None
        :param end_date: date | None
        :param dry_run: bool (للاختبار فقط)
        """

        qs = AttendanceRecord.objects.filter(
            employee__company=company,
            is_leave=False,               # لا نمس الإجازات المعتمدة
        )

        if start_date:
            qs = qs.filter(date__gte=start_date)

        if end_date:
            qs = qs.filter(date__lte=end_date)

        updated = 0
        skipped = 0

        for record in qs.select_related("employee"):
            if not HolidayResolver.is_holiday(record.date, company):
                skipped += 1
                continue

            # Idempotent guard
            if record.status == "HOLIDAY":
                skipped += 1
                continue

            if dry_run:
                updated += 1
                continue

            with transaction.atomic():
                record.status = "HOLIDAY"
                record.reason_code = "company_holiday"
                record.late_minutes = 0
                record.early_minutes = 0
                record.overtime_minutes = 0
                record.actual_hours = 0
                record.official_hours = 0
                record.save(update_fields=[
                    "status",
                    "reason_code",
                    "late_minutes",
                    "early_minutes",
                    "overtime_minutes",
                    "actual_hours",
                    "official_hours",
                ])
                updated += 1

        return {
            "updated": updated,
            "skipped": skipped,
            "total": updated + skipped,
            "dry_run": dry_run,
        }
