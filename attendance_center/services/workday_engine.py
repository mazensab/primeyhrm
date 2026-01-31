# ================================================================
# 🧠 Workday Engine V5.1 — Enterprise Ultra Pro (MINUTE ACCURATE)
# Primey HR Cloud — Attendance Center
# Phase F.5.5 — Schedule Type Behavior
# ================================================================

from datetime import datetime, time, timedelta
from functools import lru_cache

from django.db import transaction

from attendance_center.models import (
    AttendancePolicy,
    EmployeeAttendancePolicy,
)

from attendance_center.services.services import WorkScheduleResolver
from attendance_center.services.holiday_resolver import HolidayResolver  # ✅ NEW


# ===================================================================
# 🧩 WorkdaySummary — كائن ملخّص يوم العمل
# ===================================================================
class WorkdaySummary:
    """كائن جاهز للرواتب والتحليلات."""

    def __init__(
        self,
        status,
        reason_code,
        late,
        early,
        overtime,
        actual_minutes,
        official_minutes,
        schedule_source=None,
    ):
        self.status = status
        self.reason = reason_code
        self.late_minutes = late
        self.early_minutes = early
        self.overtime_minutes = overtime
        self.actual_minutes = actual_minutes
        self.official_minutes = official_minutes
        self.schedule_source = schedule_source

    @staticmethod
    def minutes_to_hours(total_minutes: int) -> float:
        total_minutes = max(int(total_minutes or 0), 0)
        return round(total_minutes / 60.0, 2)

    def as_dict(self):
        return {
            "status": self.status,
            "reason": self.reason,
            "late_minutes": self.late_minutes,
            "early_minutes": self.early_minutes,
            "overtime_minutes": self.overtime_minutes,
            "actual_hours": self.minutes_to_hours(self.actual_minutes),
            "official_hours": self.minutes_to_hours(self.official_minutes),
            "schedule_source": self.schedule_source,
        }


# ===================================================================
# 🧠 WorkdayEngine
# ===================================================================
class WorkdayEngine:

    def __init__(self, employee, company):
        self.employee = employee
        self.company = company

    # ================================================================
    # 🟦 1) Policy Resolution
    # ================================================================
    @lru_cache(maxsize=128)
    def get_active_policy(self):
        override = EmployeeAttendancePolicy.objects.filter(
            employee=self.employee,
            company_policy__company=self.company
        ).select_related("company_policy").first()

        if override:
            return override.company_policy

        return AttendancePolicy.objects.filter(company=self.company).first()

    # ================================================================
    # 🟦 2) Day Type (Weekend / Workday)
    # ================================================================
    def get_day_type(self, day, weekend_days: str):
        weekday = day.weekday()
        weekend_codes = (weekend_days or "").split(",")

        mapping = {
            "mon": 0,
            "tue": 1,
            "wed": 2,
            "thu": 3,
            "fri": 4,
            "sat": 5,
            "sun": 6,
        }

        weekend_indexes = [mapping[x] for x in weekend_codes if x in mapping]
        return "WEEKEND" if weekday in weekend_indexes else "WORKDAY"

    # ================================================================
    # 🧩 3) Resolve Periods
    # ================================================================
    def _resolve_periods(self, schedule, base_date):
        if not schedule or not base_date:
            return []

        periods = []
        day_start = datetime.combine(base_date, time.min)
        day_end = day_start + timedelta(days=1)

        def build_period(start: time, end: time):
            if not start or not end:
                return None

            start_dt = datetime.combine(base_date, start)
            end_dt = datetime.combine(base_date, end)

            if end_dt <= start_dt:
                end_dt += timedelta(days=1)

            start_dt = max(start_dt, day_start)
            end_dt = min(end_dt, day_end)

            if start_dt >= end_dt:
                return None

            return start_dt, end_dt

        for p in (
            build_period(schedule.period1_start, schedule.period1_end),
            build_period(schedule.period2_start, schedule.period2_end),
        ):
            if p:
                periods.append(p)

        periods.sort(key=lambda p: p[0])
        return periods

    # ================================================================
    # 🧮 Helpers
    # ================================================================
    def _safe_diff_minutes(self, later: datetime, earlier: datetime):
        if not later or not earlier:
            return 0
        return max(int((later - earlier).total_seconds() // 60), 0)

    def _resolve_grace_minutes(self, policy):
        try:
            return max(int(policy.grace_minutes or 0), 0) if policy else 0
        except Exception:
            return 0

    # ================================================================
    # 🟩 4) Core Classification — FINAL DECISION TREE
    # ================================================================
    def classify(self, record):

        schedule = WorkScheduleResolver.resolve(self.employee)
        schedule_source = getattr(schedule, "name", None)
        schedule_type = getattr(schedule, "schedule_type", "FULL_TIME")

        policy = self.get_active_policy()
        grace_minutes = self._resolve_grace_minutes(policy)

        weekend_days = (
            schedule.weekend_days
            if schedule and schedule.weekend_days
            else (policy.weekend_days if policy else "fri,sat")
        )

        # ------------------------------------------------------------
        # 🟥 1) APPROVED LEAVE (Highest Priority)
        # ------------------------------------------------------------
        if getattr(record, "is_leave", False):
            return WorkdaySummary(
                "HOLIDAY", "approved_leave",
                0, 0, 0, 0, 0, schedule_source
            )

        # ------------------------------------------------------------
        # 🟥 2) OFFICIAL HOLIDAY
        # ------------------------------------------------------------
        if HolidayResolver.is_holiday(record.date, self.company):
            return WorkdaySummary(
                "HOLIDAY", "official_holiday",
                0, 0, 0, 0, 0, schedule_source
            )

        # ------------------------------------------------------------
        # 🟥 3) WEEKEND
        # ------------------------------------------------------------
        if self.get_day_type(record.date, weekend_days) == "WEEKEND":
            return WorkdaySummary(
                "WEEKEND", "weekly_off",
                0, 0, 0, 0, 0, schedule_source
            )

        periods = self._resolve_periods(schedule, record.date)

        # ------------------------------------------------------------
        # 🟥 4) NO SCHEDULE
        # ------------------------------------------------------------
        if not periods:
            if record.check_in and record.check_out:
                in_dt = datetime.combine(record.date, record.check_in)
                out_dt = datetime.combine(record.date, record.check_out)
                if out_dt <= in_dt:
                    out_dt += timedelta(days=1)

                actual = self._safe_diff_minutes(out_dt, in_dt)
                return WorkdaySummary(
                    "PRESENT", "no_schedule_fallback",
                    0, 0, 0,
                    actual, actual,
                    schedule_source or "NO_SCHEDULE"
                )

            return WorkdaySummary(
                "ABSENT", "no_schedule_no_attendance",
                0, 0, 0, 0, 0,
                schedule_source or "NO_SCHEDULE"
            )

        # ------------------------------------------------------------
        # 🟥 5) NO CHECK-IN / OUT
        # ------------------------------------------------------------
        if not record.check_in and not record.check_out:
            return WorkdaySummary(
                "ABSENT", "no_checkin",
                0, 0, 0, 0, 0,
                schedule_source
            )

        # ------------------------------------------------------------
        # 🧮 Official Minutes
        # ------------------------------------------------------------
        official_minutes = sum(
            int((end - start).total_seconds() // 60)
            for start, end in periods
        )

        in_dt = datetime.combine(record.date, record.check_in) if record.check_in else None
        out_dt = datetime.combine(record.date, record.check_out) if record.check_out else None

        if in_dt and out_dt and out_dt <= in_dt:
            out_dt += timedelta(days=1)

        overlap_minutes = 0
        if in_dt and out_dt:
            for p_start, p_end in periods:
                latest_start = max(in_dt, p_start)
                earliest_end = min(out_dt, p_end)
                if latest_start < earliest_end:
                    overlap_minutes += int(
                        (earliest_end - latest_start).total_seconds() // 60
                    )

        first_start = periods[0][0]
        last_end = periods[-1][1]

        late = early = overtime = 0

        if in_dt:
            grace_in = first_start + timedelta(minutes=grace_minutes)
            if in_dt > grace_in:
                late = self._safe_diff_minutes(in_dt, grace_in)

        if out_dt:
            grace_out = last_end - timedelta(minutes=grace_minutes)
            if out_dt < grace_out:
                early = self._safe_diff_minutes(grace_out, out_dt)
            if out_dt > last_end:
                overtime = self._safe_diff_minutes(out_dt, last_end)

        actual_minutes = overlap_minutes + overtime

        # ============================================================
        # 🟦 Phase F.5.5 — Schedule Type Behavior
        # ============================================================

        if schedule_type == "FLEXIBLE":
            if actual_minutes > 0:
                return WorkdaySummary(
                    "PRESENT", "flexible_attendance",
                    0, 0, 0,
                    actual_minutes,
                    official_minutes,
                    schedule_source
                )
            return WorkdaySummary(
                "ABSENT", "flexible_no_attendance",
                0, 0, 0, 0,
                official_minutes,
                schedule_source
            )

        if schedule_type == "HOURLY":
            target = getattr(schedule, "target_daily_hours", None)
            target_minutes = int(target * 60) if target else official_minutes

            if actual_minutes > 0:
                return WorkdaySummary(
                    "PRESENT", "hourly_attendance",
                    0, 0, 0,
                    actual_minutes,
                    target_minutes,
                    schedule_source
                )

            return WorkdaySummary(
                "ABSENT", "hourly_no_attendance",
                0, 0, 0, 0,
                target_minutes,
                schedule_source
            )

        # ============================================================
        # FULL_TIME — Original Behavior (UNCHANGED)
        # ============================================================
        if actual_minutes <= 0:
            return WorkdaySummary(
                "ABSENT", "no_effective_work",
                0, 0, 0, 0,
                official_minutes,
                schedule_source
            )

        if late > 0:
            return WorkdaySummary(
                "LATE", "late_in",
                late, 0, overtime,
                actual_minutes,
                official_minutes,
                schedule_source
            )

        if early > 0:
            return WorkdaySummary(
                "EARLY_LEAVE", "early_leave",
                0, early, overtime,
                actual_minutes,
                official_minutes,
                schedule_source
            )

        return WorkdaySummary(
            "PRESENT", "normal",
            0, 0, overtime,
            actual_minutes,
            official_minutes,
            schedule_source
        )

    # ================================================================
    # 🟦 5) apply() — SAFE + IDEMPOTENT + TRANSACTIONAL
    # ================================================================
    def apply(self, record):

        summary = self.classify(record)

        update_fields = []
        changed = False

        for field, value in {
            "status": summary.status,
            "actual_minutes": summary.actual_minutes,
            "official_minutes": summary.official_minutes,
            "late_minutes": summary.late_minutes,
            "early_minutes": summary.early_minutes,
            "overtime_minutes": summary.overtime_minutes,
        }.items():
            if hasattr(record, field) and getattr(record, field) != value:
                setattr(record, field, value)
                update_fields.append(field)
                changed = True

        if hasattr(record, "actual_hours"):
            hours = summary.minutes_to_hours(summary.actual_minutes)
            if record.actual_hours != hours:
                record.actual_hours = hours
                update_fields.append("actual_hours")
                changed = True

        if hasattr(record, "official_hours"):
            hours = summary.minutes_to_hours(summary.official_minutes)
            if record.official_hours != hours:
                record.official_hours = hours
                update_fields.append("official_hours")
                changed = True

        if not changed:
            return summary

        with transaction.atomic():
            record.save(update_fields=update_fields)

        return summary
