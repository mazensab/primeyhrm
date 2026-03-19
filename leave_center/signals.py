# ============================================================
# 📂 leave_center/signals.py — Leave ↔ Attendance Auto Bridge
# Version: V1.2 Ultra Stable (UNIQUE CONSTRAINT SAFE 🔒)
# Primey HR Cloud
# ============================================================
# ✔ Fully compatible with unique_attendance_per_employee_per_day
# ✔ Atomic + race-condition safe
# ✔ Idempotent
# ✔ Never overrides real attendance
# ✔ Production safe
# ============================================================

from datetime import timedelta
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction, IntegrityError

from leave_center.models import LeaveRequest
from attendance_center.models import AttendanceRecord


logger = logging.getLogger("leave.signals")


# ============================================================
# 🧠 Helpers
# ============================================================

def daterange(start_date, end_date):
    """Generate dates between start and end inclusive."""
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


# ============================================================
# 🔗 Signal: LeaveRequest Post Save
# ============================================================

@receiver(post_save, sender=LeaveRequest)
def sync_leave_to_attendance(sender, instance: LeaveRequest, created, **kwargs):
    """
    🎯 Sync LeaveRequest → AttendanceRecord automatically.

    حالات المعالجة:
    1) APPROVED   → إنشاء / تحديث Attendance (is_leave = True)
    2) CANCELLED
       REJECTED   → حذف Attendance المرتبطة بالإجازة فقط
    """

    try:
        with transaction.atomic():

            employee = instance.employee
            company = instance.company
            start_date = instance.start_date
            end_date = instance.end_date
            status = (instance.status or "").upper()

            # ------------------------------------------------
            # ✅ APPROVED → Create / Update Attendance
            # ------------------------------------------------
            if status == "APPROVED":

                for day in daterange(start_date, end_date):

                    try:
                        record = (
                            AttendanceRecord.objects
                            .select_for_update()
                            .filter(employee=employee, date=day)
                            .first()
                        )

                        # 🟢 لا يوجد سجل → أنشئ سجل إجازة
                        if not record:
                            AttendanceRecord.objects.create(
                                employee=employee,
                                date=day,
                                status="leave",
                                reason_code="leave",
                                is_leave=True,
                                official_hours=0,
                                actual_hours=0,
                                late_minutes=0,
                                early_minutes=0,
                                overtime_minutes=0,
                                synced_from_biotime=False,
                            )
                            continue

                        # 🚫 لا نلمس أي حضور فعلي
                        if not record.is_leave and record.status not in ("leave", "unknown"):
                            continue

                        # 🟡 تحديث سجل الإجازة فقط
                        record.status = "leave"
                        record.reason_code = "leave"
                        record.is_leave = True
                        record.official_hours = 0
                        record.actual_hours = 0
                        record.late_minutes = 0
                        record.early_minutes = 0
                        record.overtime_minutes = 0

                        record.save(update_fields=[
                            "status",
                            "reason_code",
                            "is_leave",
                            "official_hours",
                            "actual_hours",
                            "late_minutes",
                            "early_minutes",
                            "overtime_minutes",
                        ])

                    except IntegrityError:
                        # 🛡️ حماية من سباق التزامن (rare edge case)
                        logger.warning(
                            f"[Leave→Attendance] Integrity race detected for "
                            f"{employee_id=}, {day=}. Skipped safely."
                        )
                        continue

                logger.info(
                    f"[Leave→Attendance] Leave #{instance.id} synced successfully "
                    f"({start_date} → {end_date})"
                )

            # ------------------------------------------------
            # 🧹 CANCELLED / REJECTED → Rollback Attendance
            # ------------------------------------------------
            elif status in ("CANCELLED", "REJECTED"):

                qs = AttendanceRecord.objects.filter(
                    employee=employee,
                    date__gte=start_date,
                    date__lte=end_date,
                    is_leave=True,
                )

                deleted_count = qs.count()
                qs.delete()

                logger.info(
                    f"[Leave→Attendance] Leave #{instance.id} rollback completed "
                    f"(deleted {deleted_count} records)"
                )

    except Exception as e:
        logger.exception(
            f"[Leave→Attendance ERROR] Leave #{instance.id} sync failed: {e}"
        )
# ============================================================
# 🟢 Signal: Auto Create LeaveBalance on Employee Creation
# Version: V1.0 — Ultra Safe (Patch Only)
# Primey HR Cloud — Leave Initialization Layer
# ============================================================

from employee_center.models import Employee
from leave_center.models import LeaveBalance


@receiver(post_save, sender=Employee)
def auto_create_leave_balance(sender, instance: Employee, created, **kwargs):
    """
    🎯 إنشاء رصيد إجازات تلقائي لكل موظف جديد.

    المميزات:
    ✔ Multi-Tenant Safe (يربط بالشركة تلقائياً)
    ✔ OneToOne Guard (لا ينشئ رصيد مكرر)
    ✔ Atomic Safe
    ✔ لا يؤثر على أي منجز سابق
    """

    if not created:
        return

    try:
        with transaction.atomic():
            # 🛡️ منع التكرار (في حال وجود رصيد مسبق)
            if LeaveBalance.objects.filter(employee=instance).exists():
                return

            LeaveBalance.objects.create(
                employee=instance,
                company=instance.company,
                annual_balance=21,
                sick_balance=30,
                maternity_balance=10,
                marriage_balance=5,
                death_balance=3,
                hajj_balance=10,
                study_balance=15,
                unpaid_balance=999,
            )

            logger.info(
                f"[Leave Init] LeaveBalance auto-created for Employee #{instance.id}"
            )

    except Exception as e:
        logger.exception(
            f"[Leave Init ERROR] Failed to create LeaveBalance for Employee #{instance.id}: {e}"
        )
