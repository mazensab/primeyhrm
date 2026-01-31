from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from company_manager.models import Company

User = get_user_model()

# ================================================================
# 🔔 Notification Model — Ultra Pro V2 (Recommended Stable)
# ================================================================
class Notification(models.Model):
    """
    نظام الإشعارات الرسمي في Primey HR Cloud
    يدعم:
    - إشعارات النظام System Events
    - الإشعارات الذكية Smart Alerts
    - التنبيهات المالية Billing Alerts
    - إشعارات الموارد البشرية HR Alerts
    - الربط الكامل مع WebSocket + Notification Signals
    """

    # 🏢 الشركة (اختياري)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
        verbose_name="الشركة"
    )

    # 👤 المستلم الأساسي
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="المستخدم المستلم"
    )

    # 📝 محتوى الإشعار
    title = models.CharField(max_length=200, verbose_name="العنوان")
    message = models.TextField(verbose_name="الرسالة")

    # 🔖 نوع الإشعار
    notification_type = models.CharField(
        max_length=50,
        default="system",
        verbose_name="نوع الإشعار"
    )

    # 🚦 مستوى الإشعار
    severity = models.CharField(
        max_length=20,
        default="info",
        verbose_name="مستوى الإشعار"
    )

    # 🔗 رابط داخلي (اختياري)
    link = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        verbose_name="الرابط الداخلي"
    )

    # 📘 حالة القراءة
    is_read = models.BooleanField(default=False, verbose_name="مقروء؟")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ القراءة")

    # 🕒 وقت الإنشاء
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الإنشاء")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "إشعار"
        verbose_name_plural = "الإشعارات"

    # ✔️ علامة مقروء
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def __str__(self):
        return f"{self.title} — {self.recipient}"
