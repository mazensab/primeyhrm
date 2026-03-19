# ============================================================
# 📘 Attendance Policy Engine V4 — Ultra Pro (2025 Edition)
# ============================================================

from django.utils import timezone
from django.db import models
from datetime import time

from attendance_center.models import (
    AttendancePolicy,
    EmployeeAttendancePolicy,
    AttendanceSetting,
)

from employee_center.models import Employee

import logging
logger = logging.getLogger(__name__)


# ============================================================
# 🎯 EffectivePolicy Object
# ============================================================

class EffectivePolicy:
    def __init__(
        self,
        work_start,
        work_end,
        grace_minutes,
        overtime_enabled,
        overtime_rate,
        auto_absent_if_no_checkin,
        weekend_days,
        weekly_hours_limit,
        source
    ):
        self.work_start = work_start
        self.work_end = work_end
        self.grace_minutes = grace_minutes
        self.overtime_enabled = overtime_enabled
        self.overtime_rate = overtime_rate
        self.auto_absent_if_no_checkin = auto_absent_if_no_checkin
        self.weekend_days = weekend_days
        self.weekly_hours_limit = weekly_hours_limit
        self.source = source


# ============================================================
# 🧠 PolicyService
# ============================================================

class PolicyService:

    @staticmethod
    def get_effective_policy(employee: Employee) -> EffectivePolicy:

        company = employee.company

        # ------------------------------------------------------
        # 1) Employee Override Policy
        # ------------------------------------------------------
        override = (
            EmployeeAttendancePolicy.objects
            .filter(employee=employee)
            .select_related("company_policy")
            .first()
        )

        if override and override.company_policy:
            policy = override.company_policy

            return EffectivePolicy(
                work_start=override.custom_work_start or policy.work_start,
                work_end=override.custom_work_end or policy.work_end,
                grace_minutes=override.custom_grace_minutes or policy.grace_minutes,
                overtime_enabled=(
                    override.custom_overtime_enabled
                    if override.custom_overtime_enabled is not None
                    else policy.overtime_enabled
                ),
                overtime_rate=(
                    override.custom_overtime_rate
                    if override.custom_overtime_rate is not None
                    else policy.overtime_rate
                ),
                auto_absent_if_no_checkin=policy.auto_absent_if_no_checkin,
                weekend_days=policy.weekend_days,
                weekly_hours_limit=policy.weekly_hours_limit,
                source="override",
            )

        # ------------------------------------------------------
        # 2) Company Policy
        # ------------------------------------------------------
        policy = AttendancePolicy.objects.filter(company=company).first()
        if policy:
            return EffectivePolicy(
                work_start=policy.work_start,
                work_end=policy.work_end,
                grace_minutes=policy.grace_minutes,
                overtime_enabled=policy.overtime_enabled,
                overtime_rate=policy.overtime_rate,
                auto_absent_if_no_checkin=policy.auto_absent_if_no_checkin,
                weekend_days=policy.weekend_days,
                weekly_hours_limit=policy.weekly_hours_limit,
                source="company_policy",
            )

        # ------------------------------------------------------
        # 3) Attendance Settings Fallback
        # ------------------------------------------------------
        settings = AttendanceSetting.objects.filter(company=company).first()
        if settings:
            return EffectivePolicy(
                work_start=settings.work_start,
                work_end=settings.work_end,
                grace_minutes=settings.grace_minutes,
                overtime_enabled=True,
                overtime_rate=1.50,
                auto_absent_if_no_checkin=True,
                weekend_days="fri,sat",
                weekly_hours_limit=48,
                source="settings",
            )

        # ------------------------------------------------------
        # 4) Hard Default
        # ------------------------------------------------------
        return EffectivePolicy(
            work_start=time(9, 0),
            work_end=time(17, 0),
            grace_minutes=15,
            overtime_enabled=True,
            overtime_rate=1.50,
            auto_absent_if_no_checkin=True,
            weekend_days="fri,sat",
            weekly_hours_limit=48,
            source="default",
        )


# ============================================================
# 🕒 WorkScheduleResolver — STRICT Employee-Only Mode
# ============================================================

class WorkScheduleResolver:

    @staticmethod
    def resolve(employee: Employee):
        """
        🔒 Strict Mode:
        يعتمد فقط على جدول الموظف المباشر.
        لا يوجد fallback.
        لا يوجد Company Default.
        لا يوجد AttendanceSetting.
        """

        from attendance_center.models import WorkSchedule

        if not employee.default_work_schedule_id:
            raise ValueError(
                f"[WorkScheduleResolver] Employee {employee.id} "
                f"does not have a default_work_schedule assigned."
            )

        schedule = (
            WorkSchedule.objects
            .filter(
                id=employee.default_work_schedule_id,
                company=employee.company,
                is_active=True
            )
            .first()
        )

        if not schedule:
            raise ValueError(
                f"[WorkScheduleResolver] Invalid or inactive schedule "
                f"for employee {employee.id}."
            )

        return schedule

# ============================================================
# 📊 KPI SERVICE
# ============================================================

class KPIService:

    # ----------------------------------------------------------
    # 🎯 KPIs للشركة
    # ----------------------------------------------------------
    @staticmethod
    def get_company_kpis(company):
        from attendance_center.models import AttendanceRecord
        records = AttendanceRecord.objects.filter(employee__company=company)
        return KPIService._calculate_kpis(records)

    # ----------------------------------------------------------
    # 🎯 KPIs لموظف واحد
    # ----------------------------------------------------------
    @staticmethod
    def get_employee_kpis(employee: Employee):
        from attendance_center.models import AttendanceRecord
        records = AttendanceRecord.objects.filter(employee=employee)
        return KPIService._calculate_kpis(records)

    # ----------------------------------------------------------
    # 🎯 الحساب المركزي
    # ----------------------------------------------------------
    @staticmethod
    def _calculate_kpis(records):

        total_days = records.count()
        if total_days == 0:
            return {
                "attendance_rate": 0,
                "absence_rate": 0,
                "late_rate": 0,
                "avg_late_minutes": 0,
                "total_work_hours": 0,
                "total_overtime": 0,
                "top_employees": [],
                "poor_employees": [],
            }

        present_days = records.filter(status="present").count()
        absent_days = records.filter(status="absent").count()
        late_days = records.filter(status="late").count()

        # --------------------------------------------------
        # 📈 نسب الأداء
        # --------------------------------------------------
        attendance_rate = round((present_days / total_days) * 100, 2)
        absence_rate = round((absent_days / total_days) * 100, 2)
        late_rate = round((late_days / total_days) * 100, 2)

        # --------------------------------------------------
        # ⏳ متوسط التأخير
        # --------------------------------------------------
        late_records = records.filter(status="late", check_in__isnull=False)

        if late_records.exists():
            late_minutes = []
            from attendance_center.services.policy_engine import PolicyService  # ✅ FIXED

            for r in late_records:
                policy = PolicyService.get_effective_policy(r.employee)
                allowed = (
                    timezone.datetime.combine(r.date, policy.work_start)
                    + timezone.timedelta(minutes=policy.grace_minutes)
                )
                actual = timezone.datetime.combine(r.date, r.check_in)
                diff = actual - allowed
                late_minutes.append(max(diff.total_seconds() / 60, 0))

            avg_late_minutes = round(sum(late_minutes) / len(late_minutes), 2)
        else:
            avg_late_minutes = 0

        # --------------------------------------------------
        # 🔥 الساعات
        # --------------------------------------------------
        total_work_hours = sum([r.actual_hours or 0 for r in records])
        total_overtime = sum([(r.overtime_minutes or 0) / 60 for r in records])

        # --------------------------------------------------
        # 🏆 أفضل الموظفين
        # --------------------------------------------------
        top = (
            records.filter(status="present")
            .values("employee__full_name")
            .annotate(count=models.Count("id"))
            .order_by("-count")[:5]
        )

        # --------------------------------------------------
        # ❌ أسوأ الموظفين
        # --------------------------------------------------
        poor = (
            records.filter(status="absent")
            .values("employee__full_name")
            .annotate(count=models.Count("id"))
            .order_by("-count")[:5]
        )

        return {
            "attendance_rate": attendance_rate,
            "absence_rate": absence_rate,
            "late_rate": late_rate,
            "avg_late_minutes": avg_late_minutes,
            "total_work_hours": round(total_work_hours, 2),
            "total_overtime": round(total_overtime, 2),
            "top_employees": list(top),
            "poor_employees": list(poor),
        }
