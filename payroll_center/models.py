# ============================================================
# 📂 الملف: payroll_center/models.py
# 🧠 وحدة الرواتب — الإصدار V11.0 Ultra Pro
# ➕ Added PayrollRun (Non-breaking)
# ============================================================

from django.db import models
from django.utils import timezone
from django.conf import settings

# 🔗 من وحدة الموظفين
from employee_center.models import Employee, Contract
from company_manager.models import Company


# ============================================================
# 🧾 Payroll Run — دورة رواتب شهرية (Enterprise Locked V2)
# 🔐 Financially Immutable After Processing
# ============================================================

class PayrollRun(models.Model):
    """
    PayrollRun يمثل دورة رواتب لشهر معيّن داخل شركة.
    لا يحل محل PayrollRecord — بل يجمعه.
    """

    # ========================================================
    # 🧠 Enterprise Status Enum (Engine Compatible)
    # ========================================================
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "مسودة"
        CALCULATED = "CALCULATED", "محسوبة"
        APPROVED = "APPROVED", "معتمدة"
        PAID = "PAID", "مدفوعة"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="payroll_runs",
        verbose_name="الشركة"
    )

    month = models.DateField(
        verbose_name="شهر دورة الرواتب",
        help_text="يمثل أول يوم في الشهر"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="حالة الدورة"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="تم الإنشاء بواسطة"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )

    class Meta:
        verbose_name = "دورة رواتب"
        verbose_name_plural = "دورات الرواتب"
        ordering = ["-month", "-created_at"]
        unique_together = ("company", "month")

    # ========================================================
    # 🔐 Hard Save Protection
    # ========================================================
    def save(self, *args, **kwargs):

        if self.pk:
            old = PayrollRun.objects.get(pk=self.pk)

            # ------------------------------------------------
            # 🔒 منع تعديل الشركة أو الشهر بعد المعالجة
            # ------------------------------------------------
            if old.status in [
                self.Status.CALCULATED,
                self.Status.APPROVED,
                self.Status.PAID,
            ]:
                if self.company_id != old.company_id:
                    raise ValueError("Cannot change company after processing")

                if self.month != old.month:
                    raise ValueError("Cannot change month after processing")

            # ------------------------------------------------
            # 🔒 منع الرجوع للخلف في الحالة
            # ------------------------------------------------
            status_order = [
                self.Status.DRAFT,
                self.Status.CALCULATED,
                self.Status.APPROVED,
                self.Status.PAID,
            ]

            if status_order.index(self.status) < status_order.index(old.status):
                raise ValueError("Cannot revert PayrollRun status backwards")

            # ------------------------------------------------
            # 🔒 منع أي تعديل بعد PAID
            # ------------------------------------------------
            if old.status == self.Status.PAID and self.status == self.Status.PAID:
                raise ValueError("Cannot modify a PAID PayrollRun")

        super().save(*args, **kwargs)

    # ========================================================
    # 🔐 Hard Delete Protection
    # ========================================================
    def delete(self, *args, **kwargs):

        if self.status in [
            self.Status.CALCULATED,
            self.Status.APPROVED,
            self.Status.PAID,
        ]:
            raise ValueError("Cannot delete a processed PayrollRun")

        super().delete(*args, **kwargs)

    # ========================================================
    # 🧾 String
    # ========================================================
    def __str__(self):
        return f"Payroll Run — {self.company} — {self.month.strftime('%B %Y')}"

# ============================================================
# 🧾 سجل الرواتب — PayrollRecord (Enterprise Lock V6)
# ============================================================

from django.db import models, transaction
from decimal import Decimal


# ============================================================
# 🔐 Safe QuerySet — Prevent Bulk Operations
# ============================================================

class PayrollRecordQuerySet(models.QuerySet):

    def delete(self):
        for obj in self:
            obj.delete()

    def update(self, **kwargs):
        raise ValueError("Bulk update is not allowed on PayrollRecord")


class PayrollRecordManager(models.Manager):
    def get_queryset(self):
        return PayrollRecordQuerySet(self.model, using=self._db)


# ============================================================
# 🧾 PayrollRecord — Enterprise Lock V7 (Partial Payment Ready)
# ============================================================

from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError


class PayrollRecord(models.Model):

    objects = PayrollRecordManager()

    # ========================================================
    # 👤 بيانات الموظف و العقد
    # ========================================================

    employee = models.ForeignKey(
        "employee_center.Employee",
        on_delete=models.CASCADE,
        related_name="payroll_records",
    )

    contract = models.ForeignKey(
        "employee_center.Contract",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payroll_records",
    )

    # ========================================================
    # 🔗 ربط بدورة الرواتب
    # ========================================================

    run = models.ForeignKey(
        "payroll_center.PayrollRun",
        on_delete=models.CASCADE,
        related_name="records",
    )

    # ========================================================
    # 💵 تفاصيل الراتب
    # ========================================================

    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    breakdown = models.JSONField(null=True, blank=True)

    month = models.DateField()

    # ========================================================
    # 💰 Payment Tracking (NEW — Partial Payment Engine)
    # ========================================================

    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    # ========================================================
    # 🔖 الحالة
    # ========================================================

    STATUS_CHOICES = (
        ("PENDING", "قيد الانتظار"),
        ("PARTIAL", "مدفوع جزئياً"),
        ("PAID", "مدفوع بالكامل"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    PAYMENT_METHOD_CHOICES = (
        ("CASH", "نقدًا"),
        ("BANK", "تحويل بنكي"),
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        null=True,
        blank=True,
    )

    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-month", "-created_at"]
        unique_together = ("employee", "run")

    # ========================================================
    # 🧮 Calculations
    # ========================================================

    def calculate_net_salary(self):
        return (
            self.base_salary
            + self.allowance
            + self.bonus
            + self.overtime
            - self.deductions
        )

    @property
    def remaining_amount(self):
        return self.net_salary - self.paid_amount

    @property
    def is_fully_paid(self):
        return self.paid_amount >= self.net_salary

    # ========================================================
    # 🔐 Hard Financial Lock
    # ========================================================

    def save(self, *args, **kwargs):

        is_create = self.pk is None

        if not is_create:
            old = PayrollRecord.objects.get(pk=self.pk)

            # 🔒 لا تعديل بعد الدفع الكامل
            if old.status == "PAID":
                raise ValueError("Cannot modify a fully PAID payroll record")

            # 🔒 لا تعديل بعد اعتماد الدورة
            if old.run.status in ["APPROVED", "PAID"]:
                if self.paid_amount != old.paid_amount:
                    pass  # مسموح تعديل paid_amount عبر Payment Engine فقط
                else:
                    raise ValueError("Cannot modify record from processed PayrollRun")

        # ====================================================
        # 🧠 لا نعيد حساب الراتب إذا كان من Engine بعد المعالجة
        # ====================================================
        if is_create or (self.run and self.run.status == "DRAFT"):
            self.net_salary = self.calculate_net_salary()


        # 🔒 Validation
        if self.paid_amount < 0:
            raise ValidationError("Paid amount cannot be negative")

        from decimal import Decimal
        # 🔒 Validation (Accounting Tolerance — Enterprise Safe)
        tolerance = Decimal("0.01")

        if self.paid_amount < 0:
            raise ValidationError("Paid amount cannot be negative")
        # السماح بفارق كسري محاسبي بسبب rounding / overtime / quantize
        if self.paid_amount > (self.net_salary + tolerance):
            raise ValidationError("Paid amount cannot exceed net salary")
            

        super().save(*args, **kwargs)

        # ====================================================
        # 📝 Audit Log
        # ====================================================

        from payroll_center.models import PayrollRecordHistory

        action = "CREATE" if is_create else "UPDATE"

        PayrollRecordHistory.objects.create(
            payroll=self,
            action=action,
            notes="Payroll record saved",
        )

    # ========================================================
    # 🔐 Hard Delete Protection
    # ========================================================

    def delete(self, *args, **kwargs):

        if self.run.status in ["CALCULATED", "APPROVED", "PAID"]:
            raise ValueError("Cannot delete record from processed PayrollRun")

        super().delete(*args, **kwargs)

    # ========================================================
    # 🏗 Auto Generator
    # ========================================================

    @classmethod
    @transaction.atomic
    def create_for_run_from_active_employees(cls, run):

        if run.status != "DRAFT":
            raise ValueError("PayrollRun must be DRAFT to generate records")

        if cls.objects.filter(run=run).exists():
            return

        from employee_center.models import Employee

        employees = Employee.objects.filter(
            company_id=run.company_id,
            status="active",
        )

        for employee in employees:

            contract = (
                employee.contracts
                .filter(is_active=True)
                .order_by("-created_at")
                .first()
            )

            cls.objects.create(
                employee=employee,
                contract=contract,
                run=run,
                month=run.month,
            )

    def __str__(self):
        return f"{self.employee} — {self.month.strftime('%B %Y')}"

# ============================================================
# 🧾 سجل عمليات الراتب — PayrollRecordHistory (كما هو)
# ============================================================
class PayrollRecordHistory(models.Model):

    ACTION_CHOICES = (
        ("CREATE", "إنشاء السجل"),
        ("UPDATE", "تحديث البيانات"),
        ("MARK_PAID", "صرف الراتب"),
    )

    payroll = models.ForeignKey(
        PayrollRecord,
        on_delete=models.CASCADE,
        related_name="history_logs",
        verbose_name="سجل الراتب"
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="نوع العملية")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="تم بواسطة"
    )

    notes = models.TextField(null=True, blank=True, verbose_name="تفاصيل إضافية")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت العملية")

    class Meta:
        verbose_name = "سجل عملية راتب"
        verbose_name_plural = "سجلات عمليات الرواتب"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} — {self.payroll} — {self.created_at.strftime('%Y-%m-%d %H:%M')}"

# ============================================================
# ➕ Payroll Adjustment — Enterprise Layer (V1.0)
# ============================================================

class PayrollAdjustment(models.Model):
    """
    طبقة الإضافات والخصومات اليدوية.
    لا يُسمح بإنشاء سجل إلا إذا كان الموظف ضمن نفس الدورة.
    """

    TYPE_CHOICES = (
        ("ADDITION", "إضافة"),
        ("DEDUCTION", "خصم"),
    )

    CATEGORY_CHOICES = (
        ("BONUS", "مكافأة"),
        ("ADVANCE", "سلفة"),
        ("PENALTY", "جزاء"),
        ("CORRECTION", "تصحيح"),
        ("OTHER", "أخرى"),
    )

    run = models.ForeignKey(
        PayrollRun,
        on_delete=models.CASCADE,
        related_name="adjustments",
        verbose_name="دورة الرواتب"
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="payroll_adjustments",
        verbose_name="الموظف"
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="نوع العملية"
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="OTHER",
        verbose_name="التصنيف"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="المبلغ"
    )

    reason = models.TextField(
        null=True,
        blank=True,
        verbose_name="السبب / الملاحظات"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="تم بواسطة"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )

    class Meta:
        verbose_name = "إضافة / خصم راتب"
        verbose_name_plural = "إضافات وخصومات الرواتب"
        ordering = ["-created_at"]

    # ========================================================
    # 🔐 Guard Rules — Enterprise Protection
    # ========================================================
from django.core.exceptions import ValidationError

def clean(self):

    # 🔐 1️⃣ منع التعديل خارج DRAFT
    if self.run.status != "DRAFT":
        raise ValidationError(
            "Adjustments allowed only in DRAFT state"
        )

    # 🔐 2️⃣ التأكد أن الموظف مدرج داخل نفس الدورة
    from payroll_center.models import PayrollRecord

    exists = PayrollRecord.objects.filter(
        run=self.run,
        employee=self.employee,
    ).exists()

    if not exists:
        raise ValidationError(
            "Employee is not included in this PayrollRun"
        )

# ============================================================
# 🧾 Journal Entry — Payroll Accounting (Hardened V3)
# 🔐 C3.6 — Partial Payment Enabled + Company Isolation
# ============================================================

class JournalEntry(models.Model):

    class Source(models.TextChoices):
        PAYROLL = "PAYROLL", "Payroll"
        PAYROLL_PAYMENT = "PAYROLL_PAYMENT", "Payroll Payment"

    # 🔒 Company Isolation (Multi-Tenant Safe)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="journal_entries",
        db_index=True,
        verbose_name="الشركة",
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.PAYROLL,
        db_index=True,
    )

    source_id = models.PositiveIntegerField(
        help_text="Reference ID (PayrollRun or PayrollRecord ID)",
        db_index=True,
    )

    description = models.CharField(
        max_length=255
    )

    date = models.DateField(default=timezone.now)

    total_debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

        # 🔐 Unique only for PAYROLL (Run-Level)
        constraints = [
            models.UniqueConstraint(
                fields=["company", "source", "source_id"],
                condition=models.Q(source="PAYROLL"),
                name="unique_payroll_run_journal_per_company"
            )
        ]

        indexes = [
            models.Index(fields=["company", "date"]),
            models.Index(fields=["company", "source"]),
            models.Index(fields=["company", "source", "source_id"]),
        ]

    def __str__(self):
        return (
            f"JournalEntry #{self.id} — "
            f"{self.company.name} — {self.description}"
        )

# ============================================================
# 🧾 Journal Line — Debit / Credit
# ============================================================

class JournalLine(models.Model):
    entry = models.ForeignKey(
        JournalEntry,
        related_name="lines",
        on_delete=models.CASCADE
    )

    account_code = models.CharField(
        max_length=20,
        help_text="e.g. 5100, 2100"
    )

    account_name = models.CharField(
        max_length=100
    )

    debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"{self.account_code} — D:{self.debit} C:{self.credit}"
# ============================================================
# 💰 Company Overtime Settings
# ============================================================

class CompanyOvertimeSetting(models.Model):
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name="overtime_setting"
    )

    normal_multiplier = models.DecimalField(
        default=1.25,
        max_digits=4,
        decimal_places=2
    )

    weekend_multiplier = models.DecimalField(
        default=2.0,
        max_digits=4,
        decimal_places=2
    )

    holiday_multiplier = models.DecimalField(
        default=2.0,
        max_digits=4,
        decimal_places=2
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Overtime Setting — {self.company.name}"
# ============================================================
# 🧾 Payroll Slip Snapshot — Enterprise Freeze Layer (V1)
# 🔐 Immutable Financial Archive
# ============================================================

class PayrollSlipSnapshot(models.Model):
    """
    Immutable snapshot of a PayrollRecord at APPROVED stage.
    This is the legally frozen salary slip.
    """

    payroll_record = models.OneToOneField(
        PayrollRecord,
        on_delete=models.CASCADE,
        related_name="snapshot",
        verbose_name="Payroll Record"
    )

    run = models.ForeignKey(
        PayrollRun,
        on_delete=models.CASCADE,
        related_name="snapshots"
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="payroll_snapshots"
    )

    # 🔒 Frozen Financial Data
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowance = models.DecimalField(max_digits=12, decimal_places=2)
    bonus = models.DecimalField(max_digits=12, decimal_places=2)
    overtime = models.DecimalField(max_digits=12, decimal_places=2)
    deductions = models.DecimalField(max_digits=12, decimal_places=2)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)

    breakdown = models.JSONField(null=True, blank=True)

    frozen_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payroll Slip Snapshot"
        verbose_name_plural = "Payroll Slip Snapshots"
        ordering = ["-frozen_at"]

    def save(self, *args, **kwargs):
        # 🔒 Hard Immutable Protection
        if self.pk:
            raise ValueError("PayrollSlipSnapshot is immutable")
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Snapshot — {self.payroll_record.employee.full_name} — "
            f"{self.run.month.strftime('%B %Y')}"
        )
