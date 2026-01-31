# ============================================================
# 📂 الملف: scheduler/models.py
# 🧠 وحدة الجدولة الذكية (Scheduler Center) — الإصدار V8.4
# 🕓 تشمل: مهام التوليد التلقائي، إدارة جداول الرواتب، التقارير اليومية
# 💾 متوافقة بالكامل مع AUTH_USER_MODEL ومع Payroll Center
# ============================================================

from django.db import models
from django.utils import timezone
from django.conf import settings


# ============================================================
# 🧩 نموذج سجل الرواتب المجدول (Payroll)
# ============================================================
class Payroll(models.Model):
    # 🧍‍♂️ بيانات الموظف
    employee_id = models.PositiveIntegerField(verbose_name="معرّف الموظف")
    employee_name = models.CharField(max_length=255, verbose_name="اسم الموظف")
    department = models.CharField(max_length=150, null=True, blank=True, verbose_name="القسم")

    # 💼 تفاصيل الراتب
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الراتب الأساسي")
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="البدلات")
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الخصومات")
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="ساعات إضافية")
    overtime_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="معدل الساعة الإضافية")

    # 💰 الناتج النهائي
    total_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="صافي الراتب")

    # 📅 بيانات الجدولة الزمنية
    month = models.PositiveIntegerField(verbose_name="الشهر")
    year = models.PositiveIntegerField(verbose_name="السنة")

    # ⚙️ حالة المعالجة
    is_generated = models.BooleanField(default=False, verbose_name="تم التوليد التلقائي")
    is_sent = models.BooleanField(default=False, verbose_name="تم الإرسال إلى Payroll Center")

    # 🕓 التحكم الزمني
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    # 👤 المستخدم المنشئ — متوافق مع CustomUser
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduler_payrolls_created",
        verbose_name="أنشئ بواسطة"
    )

    class Meta:
        verbose_name = "راتب مجدول"
        verbose_name_plural = "الرواتب المجدولة"
        ordering = ["-year", "-month", "employee_name"]
        unique_together = ("employee_id", "month", "year")

    def __str__(self):
        return f"💰 {self.employee_name} - {self.month}/{self.year}"

    # ============================================================
    # 🧮 حساب الراتب النهائي
    # ============================================================
    def calculate_total_salary(self):
        """
        🧮 تحسب الراتب النهائي حسب:
        - الراتب الأساسي
        - البدلات
        - الخصومات
        - الإضافي (ساعات × معدل)
        """
        try:
            overtime_total = self.overtime_hours * self.overtime_rate
            self.total_salary = (self.base_salary + self.allowances + overtime_total) - self.deductions
            return self.total_salary
        except Exception as e:
            print(f"❌ خطأ أثناء حساب راتب {self.employee_name}: {e}")
            return 0

    # ============================================================
    # 💾 الحفظ التلقائي مع الحساب
    # ============================================================
    def save(self, *args, **kwargs):
        self.calculate_total_salary()
        super().save(*args, **kwargs)


# ============================================================
# 🧩 نموذج مهمة مجدولة (Job Task)
# ============================================================
class ScheduledJob(models.Model):
    JOB_TYPES = [
        ("PAYROLL_GENERATION", "توليد الرواتب تلقائيًا"),
        ("SYNC_BIOTIME", "مزامنة Biotime"),
        ("HEALTH_CHECK", "فحص النظام"),
        ("CLEANUP", "تنظيف البيانات القديمة"),
        ("REPORT_GENERATION", "توليد التقارير الذكية"),
    ]

    job_name = models.CharField(max_length=255, verbose_name="اسم المهمة")
    job_type = models.CharField(max_length=50, choices=JOB_TYPES, verbose_name="نوع المهمة")
    is_active = models.BooleanField(default=True, verbose_name="نشطة؟")
    last_run = models.DateTimeField(null=True, blank=True, verbose_name="آخر تشغيل")
    next_run = models.DateTimeField(null=True, blank=True, verbose_name="التشغيل القادم")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الإنشاء")

    # المستخدم الذي أنشأ المهمة
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduler_jobs_created",
        verbose_name="أنشئ بواسطة"
    )

    def __str__(self):
        return f"🧭 {self.job_name} ({self.get_job_type_display()})"

    class Meta:
        verbose_name = "مهمة مجدولة"
        verbose_name_plural = "المهام المجدولة"
        ordering = ["-created_at"]
