# =====================================================================
# 📂 الملف: analytics_engine/models.py (نسخة معدّلة)
# =====================================================================

from django.db import models
from django.contrib.auth import get_user_model
from company_manager.models import Company   # ← ← ✔ تم تصحيح الاستيراد

User = get_user_model()

# =====================================================================
# 📊 1️⃣ نموذج التقارير الذكية (Smart Report)
# =====================================================================
class Report(models.Model):
    """
    📊 يمثل التقارير الداخلية داخل النظام:
    - التقارير المالية / الاشتراكات / الموظفين / الأنشطة
    - يدعم التكامل مع المساعد الذكي (Smart Assistant)
    """

    REPORT_TYPES = [
        ("subscription", "تقارير الاشتراكات"),
        ("finance", "التقارير المالية"),
        ("employees", "تقارير الموظفين"),
        ("activity", "سجلات النشاط"),
        ("ai_analysis", "تحليل ذكي تلقائي"),
    ]

    STATUS_CHOICES = [
        ("READY", "جاهز"),
        ("PENDING", "قيد المعالجة"),
        ("FAILED", "فشل"),
    ]

    title = models.CharField(max_length=255, verbose_name="عنوان التقرير")
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES, verbose_name="نوع التقرير")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="READY", verbose_name="حالة التقرير"
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports",
        verbose_name="الشركة",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="منشئ التقرير",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    file_path = models.FileField(
        upload_to="reports/",
        null=True,
        blank=True,
        verbose_name="ملف التقرير (PDF أو Excel)",
    )

    auto_generated = models.BooleanField(default=False, verbose_name="تم توليده تلقائيًا")

    ai_summary = models.TextField(blank=True, null=True, verbose_name="التحليل الذكي التلقائي")
    ai_score = models.FloatField(default=0.0, verbose_name="مؤشر الأداء العام (%)")

    class Meta:
        verbose_name = "تقرير ذكي"
        verbose_name_plural = "📊 التقارير الذكية"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"

    def short_summary(self):
        if self.ai_summary:
            return self.ai_summary[:120] + "..." if len(self.ai_summary) > 120 else self.ai_summary
        return "لا يوجد تحليل ذكي بعد."

    def is_ai_ready(self):
        return bool(self.ai_summary and self.ai_score > 0)


# =====================================================================
# 🧾 2️⃣ سجل العمليات على التقارير (Report Logs)
# =====================================================================
class ReportLog(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "إنشاء تقرير"),
        ("UPDATE", "تحديث تقرير"),
        ("GENERATE_AI", "تحليل ذكي"),
        ("DELETE", "حذف تقرير"),
    ]

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="التقرير",
    )

    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name="نوع العملية")

    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="المستخدم المنفذ",
    )

    executed_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التنفيذ")

    details = models.TextField(blank=True, null=True, verbose_name="تفاصيل إضافية أو رسالة النظام")

    class Meta:
        verbose_name = "سجل تقرير ذكي"
        verbose_name_plural = "🧾 سجلات التقارير الذكية"
        ordering = ["-executed_at"]

    def __str__(self):
        return f"{self.report.title} - {self.get_action_display()}"

    def formatted_date(self):
        return self.executed_at.strftime("%Y-%m-%d %H:%M")
