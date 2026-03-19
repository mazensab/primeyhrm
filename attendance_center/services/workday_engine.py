# ================================================================
#🧠 Workday Engine V6.4 — FULL_TIME Expansion (Stable)
#PART_TIME Stable
#FULL_TIME Overlap + Overtime + Late + Early
#No Double Counting
#Idempotent
# ================================================================

from datetime import datetime, timedelta
from django.db import transaction

from attendance_center.services.services import WorkScheduleResolver
from attendance_center.services.holiday_resolver import HolidayResolver

from django.db import transaction
from django.utils import timezone

from attendance_center.models import CompanyAttendanceSetting

from attendance_center.services.services import WorkScheduleResolver


# ===================================================================
# 🧩 WorkdaySummary
# ===================================================================
class WorkdaySummary:

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

    STATUS_MAP = {
        "PRESENT": "present",
        "LATE": "late",
        "ABSENT": "absent",
        "HOLIDAY": "holiday",
        "WEEKEND": "weekend",
        "OVERTIME": "present",
        "UNKNOWN": "unknown",
        "NOT_STARTED": "not_started",
        "TERMINATED": "terminated",

    }

    def __init__(self, employee, company):
        self.employee = employee
        self.company = company

    # ================================================================
    # 🟦 Helpers
    # ================================================================
    def _safe_diff_minutes(self, later, earlier):
        if not later or not earlier:
            return 0
        if later <= earlier:
            return 0
        return int((later - earlier).total_seconds() // 60)

    def _build_out_datetime(self, record, fallback_time):
        in_dt = datetime.combine(record.date, record.check_in)

        if record.check_out:
            out_dt = datetime.combine(record.date, record.check_out)
            if out_dt <= in_dt:
                out_dt += timedelta(days=1)
        else:
            out_dt = datetime.combine(record.date, fallback_time)

        return in_dt, out_dt

    # ================================================================
    # 🟩 Core Classification
    # ================================================================
    def classify(self, record):
        # ============================================================
        # 🟣 Work Start Date Guard — Ignore Before Commencement
        # ============================================================
        work_start = getattr(self.employee, "work_start_date", None)

        if work_start:
            if record.date < work_start:
                return WorkdaySummary(
                    "NOT_STARTED",
                    "before_work_start",
                    0, 0, 0, 0, 0,
                    None
                )
        # ============================================================
        # 🔴 End Date Guard — After Termination
        # ============================================================
        end_date = getattr(self.employee, "end_date", None)

        if end_date:
            if record.date > end_date:
                return WorkdaySummary(
                    "TERMINATED",
                    "after_end_date",
                    0, 0, 0, 0, 0,
                    None
                )
        


        schedule = WorkScheduleResolver.resolve(self.employee)
        if not schedule:
            return WorkdaySummary("ABSENT", "no_schedule", 0, 0, 0, 0, 0, None)

        schedule_source = schedule.name
        schedule_type = schedule.schedule_type

        # ------------------------------------------------------------
        # 1️⃣ Approved Leave
        # ------------------------------------------------------------
        if getattr(record, "is_leave", False):
            return WorkdaySummary(
                "HOLIDAY",
                "approved_leave",
                0, 0, 0, 0, 0,
                schedule_source
            )

        # ------------------------------------------------------------
        # 2️⃣ Official Holiday
        # ------------------------------------------------------------
        holiday = HolidayResolver.resolve(record.date, self.company)
        if holiday:

            if not record.check_in:
                return WorkdaySummary(
                    "HOLIDAY",
                    "official_holiday",
                    0, 0, 0, 0, 0,
                    schedule_source
                )

            in_dt = datetime.combine(record.date, record.check_in)

            if not record.check_out:
                return WorkdaySummary(
                    "HOLIDAY",
                    "holiday_open_shift",
                    0, 0, 0, 0, 0,
                    schedule_source
                )

            out_dt = datetime.combine(record.date, record.check_out)
            if out_dt <= in_dt:
                out_dt += timedelta(days=1)

            minutes = self._safe_diff_minutes(out_dt, in_dt)

            return WorkdaySummary(
                "PRESENT",
                "holiday_overtime",
                0, 0,
                minutes,
                minutes,
                0,
                schedule_source
            )

        # ------------------------------------------------------------
        # 3️⃣ Weekend
        # ------------------------------------------------------------
        if schedule.is_weekend(record.date):

            if not record.check_in:
                return WorkdaySummary(
                    "WEEKEND",
                    "weekly_off",
                    0, 0, 0, 0, 0,
                    schedule_source
                )

            in_dt = datetime.combine(record.date, record.check_in)

            if not record.check_out:
                return WorkdaySummary(
                    "WEEKEND",
                    "weekend_open_shift",
                    0, 0, 0, 0, 0,
                    schedule_source
                )

            out_dt = datetime.combine(record.date, record.check_out)
            if out_dt <= in_dt:
                out_dt += timedelta(days=1)

            minutes = self._safe_diff_minutes(out_dt, in_dt)

            return WorkdaySummary(
                "WEEKEND",
                "weekend_overtime",
                0, 0,
                minutes,
                minutes,
                0,
                schedule_source
            )

        # ------------------------------------------------------------
        # 🟢 FULL_TIME
        # ------------------------------------------------------------
        if schedule_type == "FULL_TIME":

            start_time = schedule.period1_start
            end_time = schedule.period1_end

            # --------------------------------------------------------
            # 🔒 No Check-In Lifecycle Handling
            # --------------------------------------------------------
            if not record.check_in:

                policy = (
                    CompanyAttendanceSetting.objects
                    .filter(company=self.company)
                    .first()
                )

                # 🟡 Phase 2 — Threshold Conversion
                if policy:
                    now = timezone.localtime()

                    start_dt = datetime.combine(record.date, start_time)
                    start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())

                    threshold_dt = start_dt + timedelta(
                        minutes=policy.absence_after_minutes
                    )

                    if now >= threshold_dt:
                        return WorkdaySummary(
                            "ABSENT",
                            "no_checkin_threshold",
                            0, 0, 0, 0, 0,
                            schedule_source
                        )

                # 🟢 Phase 1 — Lifecycle Pending
                if policy and not policy.auto_absent_if_no_checkin:
                    return WorkdaySummary(
                        "UNKNOWN",
                        "lifecycle_pending",
                        0, 0, 0, 0, 0,
                        schedule_source
                    )

                return WorkdaySummary(
                    "ABSENT",
                    "no_checkin",
                    0, 0, 0, 0, 0,
                    schedule_source
                )

            if not start_time or not end_time:
                return WorkdaySummary(
                    "ABSENT",
                    "invalid_schedule",
                    0, 0, 0, 0, 0,
                    schedule_source
                )

            in_dt, out_dt = self._build_out_datetime(record, end_time)

            start_dt = datetime.combine(record.date, start_time)
            end_dt = datetime.combine(record.date, end_time)

            total_actual = self._safe_diff_minutes(
                min(out_dt, end_dt),
                max(in_dt, start_dt)
            )

            late_minutes = 0
            if in_dt > start_dt:
                late_minutes = self._safe_diff_minutes(in_dt, start_dt)

            # 🔹 Apply Grace (From WorkSchedule — Phase F.5.4)
            grace = getattr(schedule, "grace_minutes", 0) or 0

            if late_minutes > 0 and late_minutes <= grace:
                late_minutes = 0

            early_minutes = 0
            if record.check_out and out_dt < end_dt:
                early_minutes = self._safe_diff_minutes(end_dt, out_dt)

            total_overtime = 0
            if record.check_out and out_dt > end_dt:
                total_overtime = self._safe_diff_minutes(out_dt, end_dt)

            if total_actual == 0 and total_overtime == 0:
                return WorkdaySummary(
                    "ABSENT",
                    "no_overlap",
                    0, 0, 0, 0, 0,
                    schedule_source
                )

            official_minutes = self._safe_diff_minutes(end_dt, start_dt)

            return WorkdaySummary(
                "PRESENT",
                "full_time_work",
                late_minutes,
                early_minutes,
                total_overtime,
                total_actual,
                official_minutes,
                schedule_source
            )
        
        # ------------------------------------------------------------
        # 🟡 PART_TIME (Correct Overlap Calculation)
        # ------------------------------------------------------------
        if schedule_type == "PART_TIME":

            if not record.check_in:
                return WorkdaySummary(
                    "ABSENT",
                    "no_checkin",
                    0, 0, 0, 0, 0,
                    schedule_source
                )

            p1_start = schedule.period1_start
            p1_end   = schedule.period1_end
            p2_start = schedule.period2_start
            p2_end   = schedule.period2_end

            in_dt = datetime.combine(record.date, record.check_in)
            out_dt = (
                datetime.combine(record.date, record.check_out)
                if record.check_out
                else None
            )

            total_actual = 0
            total_official = 0
            late_minutes = 0
            early_minutes = 0

            def calculate_period_overlap(start_time, end_time):
                nonlocal total_actual, total_official, late_minutes, early_minutes

                if not start_time or not end_time:
                    return

                s = datetime.combine(record.date, start_time)
                e = datetime.combine(record.date, end_time)

                total_official += self._safe_diff_minutes(e, s)

                if not out_dt:
                    return

                # Overlap logic (safe)
                overlap_start = max(in_dt, s)
                overlap_end = min(out_dt, e)

                if overlap_end > overlap_start:
                    total_actual += self._safe_diff_minutes(
                        overlap_end,
                        overlap_start
                    )

                if in_dt > s:
                    late_minutes += self._safe_diff_minutes(in_dt, s)

                if out_dt < e:
                    early_minutes += self._safe_diff_minutes(e, out_dt)

            # ✅ Apply for both periods (خارج الدالة)
            calculate_period_overlap(p1_start, p1_end)
            calculate_period_overlap(p2_start, p2_end)

            # 🔴 No overlap guard (PART_TIME ONLY) — خارج الدالة
            if total_actual == 0:
                return WorkdaySummary(
                    "ABSENT",
                    "no_overlap",
                    0, 0, 0, 0, total_official,
                    schedule_source
                )

            return WorkdaySummary(
                "PRESENT",
                "part_time_work",
                late_minutes,
                early_minutes,
                0,
                total_actual,
                total_official,
                schedule_source
            )

        # ------------------------------------------------------------
        # 🟢 HOURLY
        # ------------------------------------------------------------
        if schedule_type == "HOURLY":

            if not record.check_in or not record.check_out:
                return WorkdaySummary(
                    "ABSENT",
                    "no_checkin",
                    0, 0, 0, 0, 0,
                    schedule_source
                )

            in_dt = datetime.combine(record.date, record.check_in)
            out_dt = datetime.combine(record.date, record.check_out)

            if out_dt <= in_dt:
                out_dt += timedelta(days=1)

            actual_minutes = self._safe_diff_minutes(out_dt, in_dt)

            target_hours = float(schedule.target_daily_hours or 0)
            target_minutes = int(target_hours * 60)

            overtime_minutes = 0
            if actual_minutes > target_minutes:
                overtime_minutes = actual_minutes - target_minutes

            return WorkdaySummary(
                "PRESENT",
                "hourly_work",
                0,
                0,
                overtime_minutes,
                actual_minutes,
                target_minutes,
                schedule_source
            )


        # ------------------------------------------------------------
        # Default fallback
        # ------------------------------------------------------------
        return WorkdaySummary(
            "PRESENT",
            "normal",
            0, 0, 0, 0, 0,
            schedule_source
        )

    # ================================================================
    # 🟦 Apply (Idempotent + Lifecycle Safe)
    # ================================================================
    @classmethod
    def apply(cls, record, force=False):

        if not record or not record.employee:
            return None
        # ========================================================
        # 🔒 Finalization Guard (Phase F.6 — V1)
        # ========================================================
        if getattr(record, "is_finalized", False) and not force:
            return None


        engine = cls(record.employee, record.employee.company)
        summary = engine.classify(record)

        # ------------------------------------------------------------
        # 🔒 Lifecycle Safe Mode (Engine Level)
        # ------------------------------------------------------------
        try:
            policy = (
                CompanyAttendanceSetting.objects
                .filter(company=record.employee.company)
                .first()
            )

            if (
                policy
                and not policy.auto_absent_if_no_checkin
                and summary.status == "ABSENT"
                and summary.reason == "no_checkin"
                and not record.check_in
                and not record.check_out
            ):
                summary.status = "UNKNOWN"
                summary.reason = "lifecycle_pending"
                summary.late_minutes = 0
                summary.early_minutes = 0
                summary.overtime_minutes = 0
                summary.actual_minutes = 0
                summary.official_minutes = 0

        except Exception:
            pass

        mapped_status = cls.STATUS_MAP.get(summary.status, "present")

        # 🔴 Late Override — Engine is Source of Trut
        if mapped_status == "present" and summary.late_minutes > 0:
            summary.status = "LATE"
            mapped_status = "late"

        actual_hours = round(summary.actual_minutes / 60, 2)
        official_hours = round(summary.official_minutes / 60, 2)

        field_map = {
            "status": mapped_status,
            "reason_code": summary.reason,
            "late_minutes": summary.late_minutes,
            "early_minutes": summary.early_minutes,
            "overtime_minutes": summary.overtime_minutes,
            "actual_hours": actual_hours,
            "official_hours": official_hours,
        }

        update_fields = []
        changed = False

        for field, value in field_map.items():
            if hasattr(record, field) and getattr(record, field) != value:
                setattr(record, field, value)
                update_fields.append(field)
                changed = True

        if not changed:
            return summary

        with transaction.atomic():
            record.save(update_fields=update_fields, skip_engine=True)

        return summary
