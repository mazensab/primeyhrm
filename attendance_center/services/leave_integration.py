# ================================================================
# 📘 LeaveToAttendanceBridge — Primey HR Cloud V3 Ultra Pro
# ================================================================
# مسؤول عن:
# 1) تطبيق الإجازة على الحضور عند الموافقة
# 2) إزالة أثر الإجازة عند الرفض/الإلغاء (Rollback)
# 3) حماية السجلات القادمة من Biotime
# 4) منع التضارب بين Leave ↔ Attendance
# 5) ربط attendance_record بالـ leave_request نفسه
#
# ⚠ يعتمد على:
# - AttendanceRecord
# - leave_request.start_date / end_date
# - leave_request.leave_type
# ================================================================

from datetime import timedelta
from attendance_center.models import AttendanceRecord


class LeaveToAttendanceBridge:

    def __init__(self, leave_request):
        self.leave = leave_request
        self.employee = leave_request.employee
        self.company = leave_request.company

    # ============================================================
    # 🟩 Helper — جميع الأيام داخل الإجازة
    # ============================================================
    def _days_range(self):
        cur = self.leave.start_date
        while cur <= self.leave.end_date:
            yield cur
            cur += timedelta(days=1)

    # ============================================================
    # 🟦 1) Apply Leave → عند الموافقة النهائية
    # ============================================================
    def apply(self):
        """
        - إذا كان هناك سجل Biotime → نحوله إلى leave
        - إذا كان سجل يدوي → نحوله إلى leave
        - إذا لا يوجد سجل → ننشئ سجل جديد
        """

        created = 0

        for day in self._days_range():

            record = AttendanceRecord.objects.filter(
                employee=self.employee,
                date=day
            ).first()

            # -------------------------------------------------------
            # 🟦 A) سجل Biotime موجود → نعدل الحالة فقط
            # -------------------------------------------------------
            if record:

                if record.synced_from_biotime:
                    record.status = "leave"
                    record.is_leave = True
                    record.source = "biotime"   # نترك المصدر الأصلي
                    record.leave_request = self.leave
                    record.save()
                    continue

                # سجل يدوي → اجعله إجازة
                record.status = "leave"
                record.is_leave = True
                record.source = "leave"
                record.leave_request = self.leave
                record.save()
                continue

            # -------------------------------------------------------
            # 🟦 B) لا يوجد سجل — ننشئ واحد جديد
            # -------------------------------------------------------
            AttendanceRecord.objects.create(
                company=self.company,
                employee=self.employee,
                date=day,
                status="leave",
                is_leave=True,
                source="leave",
                leave_request=self.leave,
                synced_from_biotime=False,
                check_in=None,
                check_out=None,
                remarks=f"إجازة: {self.leave.leave_type.name}",
            )

            created += 1

        return created

    # ============================================================
    # 🟥 2) Rollback Leave → عند الرفض/الإلغاء
    # ============================================================
    def rollback(self):
        """
        - إذا سجل Biotime: نعيد تصنيفه تلقائيًا فقط
        - إذا سجل مُنشأ من leave: نحذفه
        """

        removed = 0

        for day in self._days_range():

            record = AttendanceRecord.objects.filter(
                employee=self.employee,
                date=day
            ).first()

            if not record:
                continue

            # -------------------------------------------------------
            # 🟥 A) سجل Biotime — لا نحذفه أبداً
            # -------------------------------------------------------
            if record.synced_from_biotime:
                record.is_leave = False
                record.leave_request = None
                record.source = "biotime"

                # إعادة التصنيف حسب النظام
                try:
                    record.status = record.classify_status()
                except:
                    record.status = "present"

                record.save()
                continue

            # -------------------------------------------------------
            # 🟥 B) سجل منشأ بواسطة leave → نحذفه
            # -------------------------------------------------------
            if record.source == "leave" and record.leave_request_id == self.leave.id:
                record.delete()
                removed += 1
                continue

            # -------------------------------------------------------
            # 🟥 C) سجل يدوي (معدّل) → نرجعه طبيعي
            # -------------------------------------------------------
            if record.is_leave and record.leave_request_id == self.leave.id:
                record.is_leave = False
                record.leave_request = None
                record.source = "manual"
                record.status = "absent"
                record.save()

        return removed
