# ================================================================
# 📘 Attendance Integration API — V1 Ultra Pro
# ================================================================
# يقوم بربط إجازات Leave Center مع حضور Attendance Center
# ---------------------------------------------------------------
# ✔ عند الموافقة على الإجازة → إنشاء سجلات غياب Authorized
# ✔ عند إلغاء / رفض الإجازة → حذف السجلات المرتبطة
# ✔ متوافق مع Biotime Sync
# ✔ يدعم المدى بين start_date → end_date
# ================================================================

from datetime import timedelta, date

from attendance_center.models import AttendanceRecord
from attendance_center.biotime_sync import BiotimeSync
from employee_center.models import Employee
from django.utils.timezone import make_aware


class AttendanceSyncService:
    """
    🧠 خدمة التكامل الأساسية بين الإجازات والحضور.
    """

    def __init__(self, employee: Employee, leave):
        self.employee = employee
        self.leave = leave

    # ------------------------------------------------------------
    # 🟣 توليد جميع التواريخ بين البداية والنهاية
    # ------------------------------------------------------------
    def _daterange(self):
        current = self.leave.start_date
        end = self.leave.end_date

        while current <= end:
            yield current
            current += timedelta(days=1)

    # ------------------------------------------------------------
    # 🔎 التحقق من وجود أيام حضور متعارضة
    # ------------------------------------------------------------
    def check_overlap(self):
        return AttendanceRecord.objects.filter(
            employee=self.employee,
            date__range=(self.leave.start_date, self.leave.end_date)
        ).exists()

    # ------------------------------------------------------------
    # 🟩 تطبيق الإجازة على جدول الحضور
    # ------------------------------------------------------------
    def apply_leave(self):
        """
        ينشئ سجلات حضور من نوع Authorized Absence
        """

        for day in self._daterange():

            # حذف أي سجل قديم لنفس اليوم
            AttendanceRecord.objects.filter(
                employee=self.employee,
                date=day
            ).delete()

            # إنشاء السجل الجديد
            AttendanceRecord.objects.create(
                employee=self.employee,
                date=day,
                status="leave",
                is_late=False,
                overtime_hours=0,
                duration=None,
                source="leave_center",
                reference_id=self.leave.id
            )

        return True

    # ------------------------------------------------------------
    # 🗑 حذف أثر الإجازة عند الإلغاء أو الرفض
    # ------------------------------------------------------------
    def remove_leave(self):

        AttendanceRecord.objects.filter(
            employee=self.employee,
            date__range=(self.leave.start_date, self.leave.end_date),
            source="leave_center",
            reference_id=self.leave.id
        ).delete()

        return True

    # ------------------------------------------------------------
    # 🔗 إرسال التحديث إلى Biotime (اختياري)
    # ------------------------------------------------------------
    def sync_biotime(self):
        """
        يستدعي محرك Biotime لإرسال حالة الغياب
        في حال كانت الشركة مفعّلة التكامل.
        """

        try:
            sync = BiotimeSync(self.employee.company)
            sync.push_leave(self.employee, self.leave)
            return True
        except Exception:
            return False
