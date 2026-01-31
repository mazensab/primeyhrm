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
# 🧾 Payroll Run — دورة رواتب شهرية
# ============================================================
class PayrollRun(models.Model):
    """
    PayrollRun يمثل دورة رواتب لشهر معيّن داخل شركة.
    لا يحل محل PayrollRecord — بل يجمعه.
    """

    STATUS_CHOICES = (
        ("DRAFT", "مسودة"),
        ("CALCULATED", "محسوبة"),
        ("APPROVED", "معتمدة"),
        ("PAID", "مدفوعة"),
    )

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
        choices=STATUS_CHOICES,
        default="DRAFT",
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

    def __str__(self):
        return f"Payroll Run — {self.company} — {self.month.strftime('%B %Y')}"


# ============================================================
# 🧾 سجل الرواتب — PayrollRecord (كما هو)
# ============================================================
class PayrollRecord(models.Model):

    # ========================================================
    # 👤 بيانات الموظف و العقد
    # ========================================================
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="payroll_records",
        verbose_name="الموظف"
    )

    contract = models.ForeignKey(
        Contract,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payroll_records",
        verbose_name="العقد"
    )

    # ========================================================
    # 🔗 ربط اختياري بدورة الرواتب
    # ========================================================
    run = models.ForeignKey(
        PayrollRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="records",
        verbose_name="دورة الرواتب"
    )

    # ========================================================
    # 💵 تفاصيل الرواتب
    # ========================================================
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الراتب الأساسي")
    allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="البدلات")
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الخصومات")
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="المكافآت")
    overtime = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الإضافي")

    # ========================================================
    # 💰 الراتب الصافي
    # ========================================================
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="صافي الراتب")

    # ========================================================
    # 🗓 الشهر
    # ========================================================
    month = models.DateField(verbose_name="شهر الراتب")

    # ========================================================
    # 🔖 الحالة
    # ========================================================
    STATUS_CHOICES = (
        ("PENDING", "قيد الانتظار"),
        ("PAID", "مدفوع"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        verbose_name="حالة الراتب"
    )

    # ========================================================
    # ⏱ timestamps
    # ========================================================
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    class Meta:
        verbose_name = "سجل راتب"
        verbose_name_plural = "سجلات الرواتب"
        ordering = ["-month", "-created_at"]
        unique_together = ("employee", "month")

    # ========================================================
    # 🧮 حساب صافي الراتب
    # ========================================================
    def calculate_net_salary(self):
        return (self.base_salary + self.allowance + self.bonus + self.overtime) - self.deductions

    def save(self, *args, **kwargs):
        self.net_salary = self.calculate_net_salary()
        super().save(*args, **kwargs)

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
# 🧾 Journal Entry — Payroll Accounting
# ============================================================

class JournalEntry(models.Model):
    class Source(models.TextChoices):
        PAYROLL = "PAYROLL", "Payroll"

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.PAYROLL,
    )

    source_id = models.PositiveIntegerField(
        help_text="PayrollRun ID"
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

    def __str__(self):
        return f"JournalEntry #{self.id} — {self.description}"
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
