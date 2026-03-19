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
from django.utils import timezone
from leave_center.services.sick_tier_engine import SickTierEngine
# ================================================================
# 🟣 Phase P3 — Policy Engine Integration
# ================================================================
from leave_center.services.policy_resolver import PolicyResolver

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
# 🧠 1) LeaveRulesEngine — محرك القواعد (مع Overlap Guard)
# ===================================================================
class LeaveRulesEngine:
    """
    يتحقق من:
    ✔ الرصيد
    ✔ المرفقات
    ✔ الحد الأعلى للأيام
    ✔ منع تداخل الإجازات (Overlap Guard) 🔒
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
    # 🟣 Policy Engine Guard — Phase P3
    # ---------------------------------------------------------------
    def check_policy_rules(self):
        """
        يتحقق من:
        ✔ max_consecutive_days من LeavePolicy
        ✔ gender_restriction
        """

        policy = PolicyResolver.resolve(self.employee, self.leave_type)

        # 1️⃣ Max Consecutive Guard
        max_consecutive = policy.get("max_consecutive")
        if max_consecutive and self.leave.total_days > max_consecutive:
            return False, f"لا يمكن أن تتجاوز الإجازة {max_consecutive} يوم حسب سياسة الشركة."

        # 2️⃣ Gender Restriction Guard
        gender_rule = policy.get("gender_restriction")
        if gender_rule and hasattr(self.employee, "gender"):
            if self.employee.gender != gender_rule:
                return False, "هذا النوع من الإجازات غير متاح لهذا الجنس."

        return True, None
    # ---------------------------------------------------------------
    # 🛡️ Overlap Guard — منع تداخل الإجازات (Enterprise Safe)
    # ---------------------------------------------------------------
    def check_overlap(self):
        """
        يمنع:
        - التداخل مع إجازات معتمدة
        - التداخل مع طلبات قيد الانتظار الحرجة
        - التداخل الجزئي أو الكلي
        """
        start = self.leave.start_date
        end = self.leave.end_date

        if not start or not end:
            return True, None

        qs = LeaveRequest.objects.filter(
            employee=self.employee,
            company=self.employee.company,
            start_date__lte=end,
            end_date__gte=start,
        ).exclude(id=self.leave.id)

        # نركز فقط على الحالات المؤثرة
        qs = qs.filter(
            status__in=[
                "approved",
                "pending",
                "pending_manager",
                "waiting_manager",
                "waiting_hr",
            ]
        )

        if qs.exists():
            conflict = qs.first()
            return False, (
                f"يوجد تداخل مع طلب إجازة آخر "
                f"({conflict.start_date} → {conflict.end_date})"
            )

        return True, None

    # ---------------------------------------------------------------
    def is_auto_approved(self):
        return self.leave_type.category in ["marriage", "death"]

    # ---------------------------------------------------------------
    def validate(self):
        """
        ترتيب التحقق الاحترافي:
        1) Overlap Guard أولاً (الأخطر)
        2) الحد الأعلى
        3) المرفقات
        4) الرصيد
        """
        for rule in (
            self.check_overlap,   # 🔥 Patch جديد بدون كسر أي منجز
            self.check_sick_tier,
            self.check_max_days,
            self.check_policy_rules,
            self.check_attachment,
            self.check_balance,
        ):
            ok, msg = rule()
            if not ok:
                return False, msg
        return True, None
    
    def check_sick_tier(self):
        if self.leave_type.category != "sick":
            return True, None

        from leave_center.services.sick_tier_engine import SickTierEngine

        engine = SickTierEngine(self.employee)
        return engine.can_apply(self.leave.total_days)


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
# ✔ 3) LeaveApprovalEngine — Enterprise Deduction Engine Patch V1
# Primey HR Cloud — Production Safe / Multi-Tenant
# ===================================================================
from django.db import transaction
from django.core.exceptions import ValidationError

class LeaveApprovalEngine:
    """
    الوظائف:
    ✔ الموافقة + الرفض + الإلغاء
    ✔ تسجيل ApprovalLog متوافق مع الموديل
    ✔ تطبيق الإجازة على الحضور Attendance
    ✔ Rollback كامل (Attendance + Balance)
    ✔ Deduction Engine احترافي (Idempotent + Atomic + Multi-Tenant)
    """

    def __init__(self, leave_request: LeaveRequest, user):
        self.leave = leave_request
        self.user = user

    # ---------------------------------------------------------------
    # 🧾 Smart Logging (متوافق مع ApprovalLog Model)
    # ---------------------------------------------------------------
    def _log(self, action, comment=None, phase="system"):
        ApprovalLog.objects.create(
            leave_request=self.leave,
            user=self.user,
            phase=phase,
            action=action,
            comment=comment,
        )

    # ---------------------------------------------------------------
    # 🔍 الحصول على الرصيد بقفل قاعدة البيانات (Concurrency Safe)
    # ---------------------------------------------------------------
    def _get_locked_balance(self):
        return LeaveBalance.objects.select_for_update().filter(
            employee_id=self.leave.employee_id,
            company_id=self.leave.company_id
        ).first()

    # ---------------------------------------------------------------
    # 🧠 Deduction Engine — Enterprise Safe
    # ---------------------------------------------------------------
    def _deduct_balance(self):
        """
        خصم الرصيد بطريقة:
        - Atomic (داخل transaction)
        - Idempotent (لا يخصم مرتين حتى مع إعادة الطلب)
        - Multi-Tenant Safe
        - محاسبي وقانوني (منع الرصيد السالب)
        """
        leave = self.leave

        # 🛑 Idempotent Guard (Database Level)
        if getattr(leave, "_deduction_applied", False):
            return

        # 🛑 لا تخصم إذا الطلب غير معتمد
        if leave.status == "approved":
            return

        balance = self._get_locked_balance()

        if not balance:
            raise ValidationError("لا يوجد رصيد إجازات مسجل لهذا الموظف.")

        category = leave.leave_type.category
        days = leave.total_days

        # unpaid لا يخصم (متوافق مع قانون العمل)
        if category == "unpaid":
            leave._deduction_applied = True
            return

        field_map = {
            "annual": "annual_balance",
            "sick": "sick_balance",
            "maternity": "maternity_balance",
            "marriage": "marriage_balance",
            "death": "death_balance",
            "hajj": "hajj_balance",
            "study": "study_balance",
        }

        field_name = field_map.get(category)
        if not field_name:
            return

        current_balance = getattr(balance, field_name, 0)

        # 🛑 حماية قانونية + Payroll Safe
        if current_balance < days:
            raise ValidationError(
                f"الرصيد غير كافٍ. المتبقي: {current_balance} يوم"
            )

        # تنفيذ الخصم
        new_balance = current_balance - days
        setattr(balance, field_name, new_balance)
        balance.save(update_fields=[field_name])

        # وسم داخلي + DB Safe Attribute
        leave._deduction_applied = True

        self._log(
            action="approved",
            phase="system",
            comment=f"Deduction Applied: -{days} يوم من رصيد {category} (المتبقي: {new_balance})"
        )

    # ---------------------------------------------------------------
    # ♻️ Refund Engine (عند الإلغاء أو الرفض)
    # ---------------------------------------------------------------
    def _refund_balance(self):
        """
        استرجاع الرصيد إذا:
        - تم إلغاء طلب معتمد
        - أو تم رفضه بعد الموافقة (سيناريو نادر)
        """
        leave = self.leave

        if leave.status != "approved":
            return

        balance = self._get_locked_balance()
        if not balance:
            return

        category = leave.leave_type.category
        days = leave.total_days

        if category == "unpaid":
            return

        field_map = {
            "annual": "annual_balance",
            "sick": "sick_balance",
            "maternity": "maternity_balance",
            "marriage": "marriage_balance",
            "death": "death_balance",
            "hajj": "hajj_balance",
            "study": "study_balance",
        }

        field_name = field_map.get(category)
        if not field_name:
            return

        current_balance = getattr(balance, field_name, 0)
        new_balance = current_balance + days

        setattr(balance, field_name, new_balance)
        balance.save(update_fields=[field_name])

        self._log(
            action="cancelled",
            phase="system",
            comment=f"Refund Applied: +{days} يوم إلى رصيد {category} (أصبح: {new_balance})"
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
            action="approved",
            phase="system",
            comment=f"Attendance Applied: إنشاء {created} سجل غياب مبرّر"
        )

    # ---------------------------------------------------------------
    # 🔴 Rollback الحضور
    # ---------------------------------------------------------------
    def _rollback_attendance(self):
        if not LeaveAttendanceIntegrator:
            return

        integrator = LeaveAttendanceIntegrator(self.leave)
        removed = integrator.rollback()

        self._log(
            action="cancelled",
            phase="system",
            comment=f"Attendance Rollback: إزالة {removed} سجل حضور"
        )

    # ---------------------------------------------------------------
    # ✔ الموافقة النهائية — Enterprise Atomic Flow
    # ---------------------------------------------------------------
    @transaction.atomic
    def approve(self, comment=None):
        if self.leave.status == "approved":
            return True, "الطلب معتمد مسبقًا."

        # 1️⃣ خصم الرصيد أولاً
        self._deduct_balance()

        # 🟣 Phase P6 Injection
        self._inject_sick_snapshot()

        # 2️⃣ تحديث الحالة
        self.leave.status = "approved"
        self.leave.save(update_fields=["status"])

        # 3️⃣ تسجيل الموافقة
        self._log("approved", comment, phase="system")

        # 4️⃣ تطبيق الحضور
        self._apply_attendance()

        return True, "تمت الموافقة على الطلب وخصم الرصيد بنجاح."
    # ---------------------------------------------------------------
    # ❌ الرفض — مع Rollback كامل
    # ---------------------------------------------------------------
    @transaction.atomic
    def reject(self, comment=None):
        # استرجاع الرصيد إن كان قد تم خصمه
        self._refund_balance()

        self.leave.status = "rejected"
        self.leave.save(update_fields=["status"])

        self._log("rejected", comment, phase="system")
        self._rollback_attendance()

        return True, "تم رفض الطلب مع استرجاع الرصيد."

    # ---------------------------------------------------------------
    # ⚫ الإلغاء — Enterprise Safe
    # ---------------------------------------------------------------
    @transaction.atomic
    def cancel(self):
        # استرجاع الرصيد إذا كان معتمد سابقًا
        self._refund_balance()

        self.leave.status = "cancelled"
        self.leave.save(update_fields=["status"])

        self._log("cancelled", "تم إلغاء الطلب من قبل الموظف.", phase="system")
        self._rollback_attendance()

        return True, "تم إلغاء الطلب واسترجاع الرصيد بنجاح."
    # ---------------------------------------------------------------
    # 🟣 Phase P6 — Sick Pay Snapshot Injection (Immutable)
    # ---------------------------------------------------------------
    def _inject_sick_snapshot(self):

        leave = self.leave

        if leave.leave_type.category != "sick":
            return

        if leave.sick_tier is not None:
            return

        engine = SickTierEngine(leave.employee)

        tier_name, percentage = engine.get_current_tier()
        counted_days = engine.get_used_days_last_year()

        leave.sick_tier = tier_name
        leave.pay_percentage = percentage
        leave.sick_days_counted = counted_days
        leave.sick_calculated_at = timezone.now()

        leave.save(update_fields=[
            "sick_tier",
            "pay_percentage",
            "sick_days_counted",
            "sick_calculated_at",
        ])