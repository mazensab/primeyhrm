# ================================================================
# 🔄 Reverse Integration Engine V1 — Primey HR Cloud Ultra Pro
# ================================================================
# هذا المحرك مسؤول عن:
# 1) إزالة تأثير الإجازة إذا قام Biotime بتسجيل Check-in فعلي
# 2) إعادة تصنيف السجل باستخدام WorkdayEngine
# 3) حماية سجلات الإجازات المرتبطة (LeaveRequest)
# 4) ضمان عدم وجود تضارب بين:
#       - LeaveAttendanceIntegrator
#       - Biotime Sync
#       - Manual Overrides
#
# 🧠 يعمل تلقائياً عند:
#       AttendanceRecord.create_from_biotime()
#       أو عند تعديل سجل حضور يدوي
# ================================================================

from attendance_center.models import AttendanceRecord
from leave_center.models import LeaveRequest
from datetime import timedelta


# ⚙️ Workday Engine (Inline import لمنع circular import)
try:
    from attendance_center.services.workday_engine import WorkdayEngine
except:
    WorkdayEngine = None


class ReverseIntegrationEngine:

    def __init__(self, record: AttendanceRecord):
        self.record = record
        self.employee = record.employee
        self.company = self.employee.company
        self.date = record.date

    # ------------------------------------------------------------
    # 🟦 1) إلغاء تأثير الإجازة إذا وجد Check-in حقيقي
    # ------------------------------------------------------------
    def _remove_leave_if_real_attendance(self):
        """
        إذا سجل الموظف حضور حقيقي عبر Biotime
        يجب إزالة الإجازة المرتبطة وإعادة تصنيف السجل.
        """

        # لا ندخل إلا إذا كانت الإجازة هي سبب الحالة
        if not self.record.is_leave:
            return

        # شرط أساسي: وجود Check-in فعلي (مزامنة من Biotime)
        if not self.record.synced_from_biotime:
            return

        if not self.record.check_in:
            return

        # --------------------------------------------------------
        # 🔥 البحث عن إجازة تخص هذا اليوم
        # --------------------------------------------------------
        leave_obj = LeaveRequest.objects.filter(
            employee=self.employee,
            start_date__lte=self.date,
            end_date__gte=self.date,
            status="approved",
        ).first()

        if not leave_obj:
            return  # لا يوجد إجازة مرتبطة

        # --------------------------------------------------------
        # 🔥 إزالة تأثير الإجازة
        # --------------------------------------------------------
        # لا نحذف الإجازة — فقط نوقف تأثيرها في هذا اليوم
        self.record.is_leave = False
        self.record.status = "present"  # سيتم إعادة تصنيفها لاحقاً
        self.record.save()

        # يمكن لاحقاً تسجيل Log لسبب إزالة الإجازة (اختياري)

    # ------------------------------------------------------------
    # 🟩 2) إعادة تصنيف السجل اعتماداً على WorkdayEngine
    # ------------------------------------------------------------
    def _reclassify(self):
        if not WorkdayEngine:
            return

        engine = WorkdayEngine(self.employee, self.company)
        new_status = engine.apply(self.record)
        return new_status

    # ------------------------------------------------------------
    # 🟥 3) تنفيذ Reverse Integration
    # ------------------------------------------------------------
    def run(self):
        """
        يتم استدعاؤه بعد كل
        AttendanceRecord.create_from_biotime()
        أو تعديل يدوي.
        """

        # 1) إزالة تأثير الإجازة عند وجود حضور حقيقي
        self._remove_leave_if_real_attendance()

        # 2) إعادة التصنيف الرسمي
        status = self._reclassify()

        return status
