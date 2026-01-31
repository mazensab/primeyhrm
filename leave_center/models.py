# ================================================================
# 📂 Leave Center — Models V4 Ultra Pro
# Primey HR Cloud — Saudi Labour Law 2025 Compliant
# ------------------------------------------------
# ✔ تكامل كامل مع Employee Center + Attendance + Payroll
# ✔ جاهز لمحرك الإجازات LeaveEngines V3 Ultra Pro
# ✔ يدعم Auto Reset + Scheduler V5
# ✔ تصميم نظيف وقابل للتوسع بسهولة
# ================================================================

from django.db import models
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
# 🟦 3) Leave Balance — V4 Ultra Pro
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
    auto_reset_month = models.IntegerField(default=1)  # يناير

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Leave Balance — {self.employee.full_name}"

    # ------------------------------------------------------------
    # 🔥 هل يجب إعادة الضبط؟
    # ------------------------------------------------------------
    def should_reset(self):
        today = timezone.now().date()

        if not self.auto_reset_enabled:
            return False

        if today.month != self.auto_reset_month:
            return False

        if not self.last_reset or self.last_reset.year < today.year:
            return True

        return False

    # ------------------------------------------------------------
    # 🔥 تنفيذ إعادة التعيين + سجل
    # ------------------------------------------------------------
    def perform_reset(self, performed_by=None):
        from django.db.utils import ProgrammingError

        today = timezone.now().date()

        # --------------------------------------------------------
        # 🧠 Phase F.5.3 — CompanyAnnualLeavePolicy Source of Truth
        # (Safe Query — بدون كسر إذا الجدول غير موجود)
        # --------------------------------------------------------
        policy = None
        try:
            policy = CompanyAnnualLeavePolicy.objects.filter(
                company=self.company,
                is_active=True
            ).first()
        except ProgrammingError:
            # الجدول غير موجود (قبل migration) → fallback آمن
            policy = None

        # --------------------------------------------------------
        # 🛡️ Fallback افتراضي (يحاكي السلوك السابق 100%)
        # --------------------------------------------------------
        annual_days = 21
        carry_enabled = True
        carry_limit = 15
        reset_month = self.auto_reset_month

        if policy:
            annual_days = policy.annual_days
            carry_enabled = policy.carry_forward_enabled
            carry_limit = policy.carry_forward_limit
            reset_month = policy.reset_month

        # --------------------------------------------------------
        # ⏱️ تأكيد شهر إعادة التعيين
        # --------------------------------------------------------
        if today.month != reset_month:
            return

        # --------------------------------------------------------
        # 🔁 حساب الرصيد الجديد
        # --------------------------------------------------------
        old = self.annual_balance

        if carry_enabled:
            carry = min(self.annual_balance, carry_limit)
        else:
            carry = 0

        new = annual_days + carry

        # --------------------------------------------------------
        # 🟧 Reset History (Audit)
        # --------------------------------------------------------
        ResetHistory.objects.create(
            company=self.company,
            employee=self.employee,
            old_balance=old,
            new_balance=new,
            year=today.year,
            performed_by=performed_by
        )

        # --------------------------------------------------------
        # 🔄 Reset Balances (كما هو — بدون تغيير)
        # --------------------------------------------------------
        self.annual_balance = new
        self.sick_balance = 30
        self.maternity_balance = 10
        self.marriage_balance = 5
        self.death_balance = 3
        self.hajj_balance = 10
        self.study_balance = 15

        self.last_reset = today
        self.save()

# ================================================================
# 🟩 4) Leave Request — طلب الإجازة
# ================================================================
class LeaveRequest(models.Model):

    STATUS = [
        ("pending_manager", "بانتظار المدير"),
        ("pending_hr", "بانتظار HR"),
        ("approved", "مقبول نهائي"),
        ("rejected", "مرفوض"),
        ("cancelled", "ملغي"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)

    start_date = models.DateField()
    end_date = models.DateField()

    reason = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to="leave_attachments/", blank=True, null=True)

    status = models.CharField(max_length=30, choices=STATUS, default="pending_manager")

    created_at = models.DateTimeField(auto_now_add=True)

    manager_approved_at = models.DateTimeField(null=True, blank=True)
    hr_approved_at = models.DateTimeField(null=True, blank=True)

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
