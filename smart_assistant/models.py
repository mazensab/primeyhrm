# 📂 الملف: smart_assistant/models.py
# 🤖 Smart Assistant V11.0 — Contextual AI Memory Model
# 🚀 متكامل مع Notification Center و Analytics Engine
# ============================================================
from django.db import models
from django.conf import settings
from django.utils import timezone


class AssistantInsight(models.Model):
    """
    🧠 تمثل التحليل أو التوصية التي أنشأها المساعد الذكي
    وتشكل ذاكرة معرفية يتم تحليلها لاحقًا لتوليد قرارات أفضل.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assistant_insights",
        verbose_name="المستخدم",
    )

    title = models.CharField(
        max_length=200,
        verbose_name="عنوان التحليل",
        help_text="العنوان المختصر للتحليل أو التوصية."
    )

    recommendation = models.TextField(
        verbose_name="نص التوصية / التحليل",
        help_text="النص الكامل للتحليل أو النتيجة التي تولدها الذكاء الاصطناعي."
    )

    confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.95,
        verbose_name="نسبة الثقة بالتحليل"
    )

    context_summary = models.TextField(
        null=True,
        blank=True,
        verbose_name="ملخص سياق التحليل",
        help_text="ملخص ذكي يصف السياق أو البيانات التي استند إليها التحليل."
    )

    source_module = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="الوحدة المصدر",
        help_text="المصدر الذي استُخرجت منه البيانات (مثل Payroll / Attendance / Analytics)."
    )

    ai_tags = models.JSONField(
        default=list,
        verbose_name="وسوم تحليلية",
        help_text="قائمة بالوسوم الذكية المرتبطة بالتحليل."
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاريخ الإنشاء"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخر تحديث"
    )

    is_archived = models.BooleanField(
        default=False,
        verbose_name="مؤرشف؟"
    )

    class Meta:
        verbose_name = "تحليل ذكي"
        verbose_name_plural = "التحليلات الذكية"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    # ============================================================
    # 🧩 وظائف ذكية مساعدة (لتحليل البيانات التاريخية)
    # ============================================================
    def short_recommendation(self, length=120):
        """📄 إرجاع نسخة مختصرة من التوصية"""
        return (self.recommendation[:length] + "...") if len(self.recommendation) > length else self.recommendation

    def tag_summary(self):
        """🔖 عرض وسوم التحليل كجملة واحدة"""
        return ", ".join(self.ai_tags) if self.ai_tags else "بدون وسوم"

    @staticmethod
    def get_recent_insights(limit=5):
        """📊 استرجاع أحدث التحليلات الذكية"""
        return AssistantInsight.objects.filter(is_archived=False).order_by("-created_at")[:limit]

    @staticmethod
    def archive_old_insights(days=30):
        """🗄️ أرشفة التحليلات الأقدم من مدة معينة"""
        threshold = timezone.now() - timezone.timedelta(days=days)
        return AssistantInsight.objects.filter(created_at__lt=threshold, is_archived=False).update(is_archived=True)
