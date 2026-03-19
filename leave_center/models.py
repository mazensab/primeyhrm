# ================================================================
# 📂 Leave Center — Models V4 Ultra Pro
# Primey HR Cloud — Saudi Labour Law 2025 Compliant
# ------------------------------------------------
# ✔ تكامل كامل مع Employee Center + Attendance + Payroll
# ✔ جاهز لمحرك الإجازات LeaveEngines V3 Ultra Pro
# ✔ يدعم Auto Reset + Scheduler V5
# ✔ تصميم نظيف وقابل للتوسع بسهولة
# ================================================================

from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from employee_center.models import Employee
from billing_center.models import Company

User = get_user_model()


# ================================================================
# 🟦 1) أنواع الإجازات — LeaveType
# ================================================================
class LeaveType(models.Model):

    CATEGORY_CHOICES = [
        ("annual", "إجازة سنوية"),
        ("sick", "إجازة مرضية"),
        ("maternity", "إجازة أمومة"),
        ("marriage", "إجازة زواج"),
        ("death", "إجازة وفاة"),
        ("hajj", "إجازة حج"),
        ("study", "إجازة دراسية"),
        ("unpaid", "إجازة بدون راتب"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="annual")

    # رصيد سنوي مخصص إذا رغبت الشركة
    annual_balance = models.PositiveIntegerField(default=0)

    # دعم أنواع تحتاج HR/Manager فقط
    requires_manager_only = models.BooleanField(default=False)
    requires_hr_only = models.BooleanField(default=False)

    # هل يتطلب مرفق؟
    requires_attachment = models.BooleanField(default=False)

    # الحد الأعلى
    max_days = models.PositiveIntegerField(null=True, blank=True)

    color = models.CharField(max_length=20, default="#0ea5e9")  # دعم التقويم

    def __str__(self):
        return self.name

# ================================================================
# 🟪 Leave Policy — B+ Engine Core (Multi-Tenant Safe)
# Phase P1
# ================================================================
class LeavePolicy(models.Model):
    """
    Company Scoped Leave Policy
    Source of Truth for Leave Rules
    B+ Expandable Architecture
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="leave_policies"
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="policies"
    )

    # ============================================================
    # 🟢 Core Policy Settings
    # ============================================================
    default_days = models.PositiveIntegerField(
        default=0,
        help_text="عدد الأيام الأساسية سنويًا"
    )

    # خدمة ≥ X سنوات → يحصل على أيام مختلفة
    min_service_years = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="الحد الأدنى لسنوات الخدمة لتطبيق days_after_service"
    )

    days_after_service = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="عدد الأيام بعد تجاوز سنوات الخدمة"
    )

    # ============================================================
    # 🔁 Carry Forward
    # ============================================================
    carry_forward_enabled = models.BooleanField(default=False)

    carry_forward_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="الحد الأعلى للترحيل"
    )

    # ============================================================
    # 🔄 Reset Settings
    # ============================================================
    reset_month = models.PositiveSmallIntegerField(
        default=1,
        help_text="شهر إعادة تعيين الرصيد"
    )

    # ============================================================
    # ⚖ Behaviour Flags
    # ============================================================
    paid_leave = models.BooleanField(default=True)

    requires_manager_approval = models.BooleanField(default=True)
    requires_hr_approval = models.BooleanField(default=False)

    max_consecutive_days = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    gender_restriction = models.CharField(
        max_length=10,
        choices=[
            ("male", "ذكر"),
            ("female", "أنثى"),
        ],
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ============================================================
    # 🛡 Multi-Tenant Isolation Guard
    # ============================================================
    class Meta:
        unique_together = ("company", "leave_type")
        verbose_name = "Leave Policy"
        verbose_name_plural = "Leave Policies"

    def __str__(self):
        return f"{self.company.name} — {self.leave_type.name}"
# ================================================================
# 🟦 Company Annual Leave Policy — Phase F.5.2
# Company Level Source of Truth
# ================================================================
class CompanyAnnualLeavePolicy(models.Model):

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name="annual_leave_policy"
    )

    # الرصيد السنوي الأساسي
    annual_days = models.PositiveIntegerField(
        default=21,
        help_text="عدد أيام الإجازة السنوية الممنوحة سنويًا"
    )

    # هل يسمح بالترحيل؟
    carry_forward_enabled = models.BooleanField(
        default=True,
        help_text="هل يسمح بترحيل الرصيد المتبقي للسنة القادمة"
    )

    # الحد الأعلى للترحيل
    carry_forward_limit = models.PositiveIntegerField(
        default=15,
        help_text="الحد الأعلى للأيام التي يمكن ترحيلها"
    )

    # شهر إعادة التعيين (1 = يناير)
    reset_month = models.PositiveSmallIntegerField(
        default=1,
        help_text="شهر إعادة تعيين رصيد الإجازة السنوية"
    )

    # هل التفعيل نشط؟
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company Annual Leave Policy"
        verbose_name_plural = "Company Annual Leave Policies"

    def __str__(self):
        return f"Annual Leave Policy — {self.company.name}"

# ================================================================
# 🟧 2) Reset History — سجل إعادة التعيين
# ================================================================
class ResetHistory(models.Model):

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)

    old_balance = models.FloatField(default=0)
    new_balance = models.FloatField(default=0)

    year = models.IntegerField()
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.full_name} — Reset {self.year}"



# ================================================================
# 🟦 3) Leave Balance — V4 Ultra Pro (Unified Reset Engine)
# ================================================================
class LeaveBalance(models.Model):

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="leave_balance")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="leave_balances")

    # أرصدة قانونية بحسب النظام السعودي
    annual_balance = models.PositiveIntegerField(default=21)
    sick_balance = models.PositiveIntegerField(default=30)
    maternity_balance = models.PositiveIntegerField(default=10)
    marriage_balance = models.PositiveIntegerField(default=5)
    death_balance = models.PositiveIntegerField(default=3)
    hajj_balance = models.PositiveIntegerField(default=10)
    study_balance = models.PositiveIntegerField(default=15)

    unpaid_balance = models.PositiveIntegerField(default=999)

    last_reset = models.DateField(null=True, blank=True)

    auto_reset_enabled = models.BooleanField(default=True)
    auto_reset_month = models.IntegerField(default=1)  # Fallback فقط

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Leave Balance — {self.employee.full_name}"

    # ------------------------------------------------------------
    # 🔥 هل يجب إعادة الضبط؟ (Policy Driven — Unified)
    # ------------------------------------------------------------
    def should_reset(self):
        today = timezone.now().date()

        if not self.auto_reset_enabled:
            return False

        from leave_center.models import LeaveType
        from leave_center.services.policy_resolver import PolicyResolver

        annual_leave_type = LeaveType.objects.filter(
            company=self.company,
            category="annual"
        ).first()

        if not annual_leave_type:
            return False

        resolved = PolicyResolver.resolve(self.employee, annual_leave_type)

        reset_month = resolved.get("reset_month") or self.auto_reset_month

        if today.month != reset_month:
            return False

        if not self.last_reset or self.last_reset.year < today.year:
            return True

        return False

    # ------------------------------------------------------------
    # 🔥 تنفيذ إعادة التعيين + سجل
    # 🔵 Phase F.5.3 — Reset Engine Binding (PolicyResolver)
    # ------------------------------------------------------------
    def perform_reset(self, performed_by=None):

        today = timezone.now().date()

        from leave_center.models import LeaveType
        from leave_center.services.policy_resolver import PolicyResolver

        # ------------------------------------------------------------
        # 1️⃣ جلب نوع الإجازة السنوية
        # ------------------------------------------------------------
        annual_leave_type = LeaveType.objects.filter(
            company=self.company,
            category="annual"
        ).first()

        if not annual_leave_type:
            return

        # ------------------------------------------------------------
        # 2️⃣ حل السياسة عبر PolicyResolver (Single Source of Truth)
        # ------------------------------------------------------------
        resolved = PolicyResolver.resolve(self.employee, annual_leave_type)

        # ------------------------------------------------------------
        # 3️⃣ تحديد شهر إعادة التعيين
        # ------------------------------------------------------------
        reset_month = resolved.get("reset_month") or self.auto_reset_month

        if today.month != reset_month:
            return

        # ------------------------------------------------------------
        # 4️⃣ تحديد الأيام الأساسية
        # ------------------------------------------------------------
        annual_days = resolved.get("allowed_days", 21)

        # ------------------------------------------------------------
        # 5️⃣ Carry Forward
        # ------------------------------------------------------------
        carry = 0

        if resolved.get("carry_forward_enabled"):
            limit = resolved.get("carry_forward_limit") or 0
            carry = min(self.annual_balance, limit)

        new_balance = annual_days + carry

        # ------------------------------------------------------------
        # 6️⃣ Idempotency Guard (منع إعادة التنفيذ)
        # ------------------------------------------------------------
        if self.last_reset and self.last_reset.year == today.year:
            return

        # ------------------------------------------------------------
        # 7️⃣ Audit Log
        # ------------------------------------------------------------
        old = self.annual_balance

        ResetHistory.objects.create(
            company=self.company,
            employee=self.employee,
            old_balance=old,
            new_balance=new_balance,
            year=today.year,
            performed_by=performed_by
        )

        # ------------------------------------------------------------
        # 8️⃣ تطبيق الرصيد الجديد
        # ------------------------------------------------------------
        self.annual_balance = new_balance
        self.sick_balance = 30
        self.maternity_balance = 10
        self.marriage_balance = 5
        self.death_balance = 3
        self.hajj_balance = 10
        self.study_balance = 15

        self.last_reset = today

        self.save(update_fields=[
            "annual_balance",
            "sick_balance",
            "maternity_balance",
            "marriage_balance",
            "death_balance",
            "hajj_balance",
            "study_balance",
            "last_reset",
        ])
# ================================================================
# 🟩 4) Leave Request — طلب الإجازة
# ================================================================

from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone


class LeaveRequest(models.Model):

    STATUS = [
        ("pending_manager", "بانتظار المدير"),
        ("pending_hr", "بانتظار HR"),
        ("approved", "مقبول نهائي"),
        ("rejected", "مرفوض"),
        ("cancelled", "ملغي"),
    ]

    company = models.ForeignKey("company_manager.Company", on_delete=models.CASCADE)
    employee = models.ForeignKey("employee_center.Employee", on_delete=models.CASCADE)
    leave_type = models.ForeignKey("LeaveType", on_delete=models.CASCADE)

    start_date = models.DateField()
    end_date = models.DateField()

    reason = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to="leave_attachments/", blank=True, null=True)

    status = models.CharField(max_length=30, choices=STATUS, default="pending_manager")

    created_at = models.DateTimeField(auto_now_add=True)

    manager_approved_at = models.DateTimeField(null=True, blank=True)
    hr_approved_at = models.DateTimeField(null=True, blank=True)

    # ============================================================
    # 🟣 Phase P6 — Sick Snapshot (Immutable After Approval)
    # ============================================================

    sick_tier = models.CharField(max_length=30, null=True, blank=True)
    pay_percentage = models.PositiveSmallIntegerField(null=True, blank=True)
    sick_days_counted = models.PositiveIntegerField(null=True, blank=True)
    sick_calculated_at = models.DateTimeField(null=True, blank=True)

    rejected_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leave_rejected_by"
    )

    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, null=True)

    # ============================================================
    # 🔒 Enterprise Validation Layer
    # ============================================================

    def clean(self):

        # 1️⃣ Date Integrity
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError("تاريخ نهاية الإجازة لا يمكن أن يكون قبل تاريخ البداية.")

        # 2️⃣ Hire Date Guard
        if self.employee and self.start_date:
            work_start = getattr(self.employee, "work_start_date", None)
            if work_start and self.start_date < work_start:
                raise ValidationError(
                    f"لا يمكن طلب إجازة قبل تاريخ المباشرة ({work_start})."
                )

        # 3️⃣ Overlap Guard (Soft Layer — قبل الحفظ)
        if self.employee_id and self.company_id and self.start_date and self.end_date:
            overlapping = LeaveRequest.objects.filter(
                employee_id=self.employee_id,
                company_id=self.company_id,
                start_date__lte=self.end_date,
                end_date__gte=self.start_date,
                status__in=["pending_manager", "pending_hr", "approved"],
            ).exclude(id=self.id)

            if overlapping.exists():
                conflict = overlapping.first()
                raise ValidationError(
                    f"يوجد تداخل مع طلب إجازة آخر "
                    f"({conflict.start_date} → {conflict.end_date})."
                )

    # ============================================================
    # 🔒 SAVE — Enterprise Hard Guard
    # ============================================================

    def save(self, *args, **kwargs):

        with transaction.atomic():

            # ----------------------------------------------------
            # 🔒 Snapshot Immutability Guard (DB Truth Based)
            # ----------------------------------------------------
            if self.pk:

                db_instance = LeaveRequest.objects.select_for_update().get(pk=self.pk)

                if db_instance.status == "approved":

                    protected_fields = [
                        "sick_tier",
                        "pay_percentage",
                        "sick_days_counted",
                        "sick_calculated_at",
                    ]

                    for field in protected_fields:
                        old_value = getattr(db_instance, field)
                        new_value = getattr(self, field)

                        if old_value != new_value:
                            raise ValidationError(
                                "لا يمكن تعديل بيانات الشريحة المرضية بعد الموافقة."
                            )

            # ----------------------------------------------------
            # 🛡 Hard Overlap Guard (DB Lock Level)
            # ----------------------------------------------------
            if self.employee_id and self.company_id and self.start_date and self.end_date:

                overlapping = LeaveRequest.objects.select_for_update().filter(
                    employee_id=self.employee_id,
                    company_id=self.company_id,
                    start_date__lte=self.end_date,
                    end_date__gte=self.start_date,
                    status__in=["pending_manager", "pending_hr", "approved"],
                ).exclude(id=self.id)

                if overlapping.exists():
                    conflict = overlapping.first()
                    raise ValidationError(
                        f"يوجد تداخل مع طلب إجازة آخر "
                        f"({conflict.start_date} → {conflict.end_date})."
                    )

            # ----------------------------------------------------
            # 🔍 Full Validation
            # ----------------------------------------------------
            self.full_clean()

            super().save(*args, **kwargs)

    # ============================================================
    # Helpers
    # ============================================================

    def __str__(self):
        return f"Leave Request #{self.id} — {self.employee.full_name}"

    @property
    def total_days(self):
        return (self.end_date - self.start_date).days + 1


# ================================================================
# 🟧 5) ApprovalLog — سجل خطوات الموافقة
# ================================================================
class ApprovalLog(models.Model):

    PHASE = [
        ("manager", "موافقة المدير"),
        ("hr", "موافقة HR"),
        ("system", "النظام"),
    ]

    ACTION = [
        ("approved", "موافقة"),
        ("rejected", "رفض"),
        ("cancelled", "إلغاء"),
    ]

    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name="approval_logs")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    phase = models.CharField(max_length=20, choices=PHASE)
    action = models.CharField(max_length=20, choices=ACTION)

    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]



# ================================================================
# 🟪 6) Workflow Status — الحالة المرحلية
# ================================================================
class LeaveWorkflowStatus(models.Model):

    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name="workflow_status")

    phase = models.CharField(max_length=20, choices=[
        ("manager", "مدير"),
        ("hr", "موارد بشرية"),
        ("rejected", "رفض"),
        ("cancelled", "إلغاء"),
    ])

    approved = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"Workflow — {self.leave_request.id} — {self.phase}"
