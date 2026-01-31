# ================================================================
# 🚀 Leave Engines — Primey HR Cloud V3 Ultra Pro
# ================================================================
# يشمل:
# 1) LeaveRulesEngine
# 2) LeaveWorkflowEngine
# 3) LeaveApprovalEngine  ← مدمج بالكامل مع Attendance + Rollback
#
# مميزات النسخة V3:
# ✔ دمج كامل مع LeaveToAttendanceBridge V3
# ✔ دعم Rollback كامل عند الرفض/الإلغاء
# ✔ حماية سجلات Biotime
# ✔ Smart Logging
# ✔ Workflow أكثر دقة
# ✔ تكامل مرن مع جميع الوحدات
# ================================================================

from datetime import date
from django.core.exceptions import ValidationError

# ================================================================
# 🔗 MODELS (✔ تصحيح الاستيراد — مهم جدًا)
# ================================================================
from ..models import (
    LeaveRequest,
    LeaveBalance,
    LeaveType,
    ApprovalLog
)

# ================================================================
# ⚡ Attendance Bridge + Reverse Integration
# ================================================================
try:
    from attendance_center.services.leave_integration import LeaveToAttendanceBridge
except Exception:
    LeaveToAttendanceBridge = None

try:
    from attendance_center.services.leave_reverse_integration import LeaveAttendanceIntegrator
except Exception:
    LeaveAttendanceIntegrator = None


# ===================================================================
# 🧠 1) LeaveRulesEngine — محرك القواعد
# ===================================================================
class LeaveRulesEngine:
    """
    يتحقق من:
    ✔ الرصيد
    ✔ المرفقات
    ✔ الحد الأعلى للأيام
    ✔ auto-approval للوفاة + الزواج
    """

    def __init__(self, leave_request: LeaveRequest):
        self.leave = leave_request
        self.employee = leave_request.employee
        self.leave_type = leave_request.leave_type

    # ---------------------------------------------------------------
    def check_balance(self):
        balance = LeaveBalance.objects.filter(employee=self.employee).first()
        if not balance:
            return False, "لا يوجد سجل رصيد لهذا الموظف."

        days = self.leave.total_days
        category = self.leave_type.category

        category_map = {
            "annual": balance.annual_balance,
            "sick": balance.sick_balance,
            "maternity": balance.maternity_balance,
            "marriage": balance.marriage_balance,
            "death": balance.death_balance,
            "hajj": balance.hajj_balance,
            "study": balance.study_balance,
        }

        if category not in category_map:
            return True, None

        if category_map[category] < days:
            return False, "الرصيد غير كافٍ."

        return True, None

    # ---------------------------------------------------------------
    def check_attachment(self):
        if self.leave_type.requires_attachment and not self.leave.attachment:
            return False, "هذا النوع من الإجازات يتطلب مرفق."
        return True, None

    # ---------------------------------------------------------------
    def check_max_days(self):
        if self.leave_type.max_days and self.leave.total_days > self.leave_type.max_days:
            return False, f"لا يمكن أن تتجاوز الإجازة {self.leave_type.max_days} يوم."
        return True, None

    # ---------------------------------------------------------------
    def is_auto_approved(self):
        return self.leave_type.category in ["marriage", "death"]

    # ---------------------------------------------------------------
    def validate(self):
        for rule in (
            self.check_max_days,
            self.check_attachment,
            self.check_balance,
        ):
            ok, msg = rule()
            if not ok:
                return False, msg
        return True, None


# ===================================================================
# 🔀 2) LeaveWorkflowEngine — محرك المسار
# ===================================================================
class LeaveWorkflowEngine:

    def __init__(self, leave_request: LeaveRequest):
        self.leave = leave_request
        self.leave_type = leave_request.leave_type

    def get_workflow(self):
        if self.leave_type.requires_hr_only:
            return ["hr"]

        if self.leave_type.requires_manager_only:
            return ["manager"]

        if self.leave_type.category in ["marriage", "death"]:
            return ["auto"]

        return ["manager", "hr"]

    def get_current_stage(self):
        return self.leave.status

    def next_stage(self):
        flow = self.get_workflow()

        if "auto" in flow:
            return "approved"

        if self.leave.status == "pending":
            return "waiting_manager" if "manager" in flow else "waiting_hr"

        if self.leave.status == "waiting_manager":
            return "waiting_hr" if "hr" in flow else "approved"

        if self.leave.status == "waiting_hr":
            return "approved"

        return "approved"


# ===================================================================
# ✔ 3) LeaveApprovalEngine — دمج الحضور + Rollback كامل
# ===================================================================
class LeaveApprovalEngine:
    """
    الوظائف:
    ✔ الموافقة + الرفض + الإلغاء
    ✔ تسجيل ApprovalLog
    ✔ تطبيق الإجازة على الحضور Attendance
    ✔ إزالة البيانات من الحضور عند الإلغاء/الرفض (Rollback)
    """

    def __init__(self, leave_request: LeaveRequest, user):
        self.leave = leave_request
        self.user = user

    # ---------------------------------------------------------------
    def _log(self, action, comment=None):
        ApprovalLog.objects.create(
            leave_request=self.leave,
            action=action,
            performed_by=self.user,
            comment=comment,
        )

    # ---------------------------------------------------------------
    # 🟢 دمج الحضور (Apply Leave)
    # ---------------------------------------------------------------
    def _apply_attendance(self):
        if not LeaveToAttendanceBridge:
            return

        bridge = LeaveToAttendanceBridge(self.leave)
        created = bridge.apply()

        self._log(
            "attendance_applied",
            f"إنشاء {created} سجل حضور (غياب مبرّر)"
        )

    # ---------------------------------------------------------------
    # 🔴 إزالة أثر الحضور (Rollback)
    # ---------------------------------------------------------------
    def _rollback_attendance(self):
        if not LeaveAttendanceIntegrator:
            return

        integrator = LeaveAttendanceIntegrator(self.leave)
        removed = integrator.rollback()

        self._log(
            "attendance_rollback",
            f"إزالة {removed} سجل حضور"
        )

    # ---------------------------------------------------------------
    # ✔ الموافقة النهائية
    # ---------------------------------------------------------------
    def approve(self, comment=None):
        self.leave.status = "approved"
        self.leave.save()

        self._log("approved", comment)

        self._apply_attendance()
        return True, "تمت الموافقة على الطلب."

    # ---------------------------------------------------------------
    # ❌ الرفض — مع Rollback
    # ---------------------------------------------------------------
    def reject(self, comment=None):
        self.leave.status = "rejected"
        self.leave.save()

        self._log("rejected", comment)

        self._rollback_attendance()
        return True, "تم رفض الطلب."

    # ---------------------------------------------------------------
    # ⚫ الإلغاء — مع Rollback
    # ---------------------------------------------------------------
    def cancel(self):
        self.leave.status = "cancelled"
        self.leave.save()

        self._log("cancelled", "تم إلغاء الطلب من قبل الموظف.")

        self._rollback_attendance()
        return True, "تم إلغاء الطلب."
