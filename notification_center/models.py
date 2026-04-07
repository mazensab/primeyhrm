from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from company_manager.models import Company

User = get_user_model()


# ================================================================
# 🧭 Notification Enums
# ================================================================
class NotificationSeverity(models.TextChoices):
    INFO = "info", "Info"
    SUCCESS = "success", "Success"
    WARNING = "warning", "Warning"
    ERROR = "error", "Error"
    CRITICAL = "critical", "Critical"


class NotificationEventStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSED = "processed", "Processed"
    PARTIAL = "partial", "Partial"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", "In-App"
    EMAIL = "email", "Email"
    WHATSAPP = "whatsapp", "WhatsApp"
    SMS = "sms", "SMS"
    PUSH = "push", "Push"


class NotificationDeliveryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"
    RETRYING = "retrying", "Retrying"
    CANCELLED = "cancelled", "Cancelled"


# ================================================================
# 🔔 Notification Model — Ultra Pro V2 (Extended Safely)
# ================================================================
class Notification(models.Model):
    """
    نظام الإشعارات الرسمي في Mham Cloud
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
        db_index=True,
        verbose_name="نوع الإشعار"
    )

    # 🚦 مستوى الإشعار
    severity = models.CharField(
        max_length=20,
        default=NotificationSeverity.INFO,
        db_index=True,
        verbose_name="مستوى الإشعار"
    )

    # 🔗 رابط داخلي (اختياري)
    link = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        verbose_name="الرابط الداخلي"
    )

    # 🔗 ربط اختياري مع الحدث الأصلي
    event = models.ForeignKey(
        "NotificationEvent",
        on_delete=models.SET_NULL,
        related_name="notifications",
        null=True,
        blank=True,
        verbose_name="الحدث المرتبط"
    )

    # 📘 حالة القراءة
    is_read = models.BooleanField(default=False, verbose_name="مقروء؟")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ القراءة")

    # 🕒 وقت الإنشاء
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="تاريخ الإنشاء"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "إشعار"
        verbose_name_plural = "الإشعارات"
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["company", "-created_at"]),
            models.Index(fields=["notification_type", "severity"]),
        ]

    # ✔️ علامة مقروء
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def __str__(self):
        return f"{self.title} — {self.recipient}"


# ================================================================
# 🧩 Notification Event — الحدث الأصلي في النظام
# ================================================================
class NotificationEvent(models.Model):
    """
    يمثل الحدث الأصلي في النظام قبل الإرسال عبر القنوات.

    أمثلة:
    - employee_created
    - employee_deactivated
    - leave_requested
    - payroll_record_paid
    - password_changed
    - company_created
    - subscription_renewed
    - payment_confirmed
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="notification_events",
        null=True,
        blank=True,
        verbose_name="الشركة"
    )

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="triggered_notification_events",
        null=True,
        blank=True,
        verbose_name="منفذ الحدث"
    )

    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="targeted_notification_events",
        null=True,
        blank=True,
        verbose_name="المستخدم المستهدف"
    )

    event_code = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="كود الحدث"
    )

    event_group = models.CharField(
        max_length=50,
        default="system",
        db_index=True,
        verbose_name="مجموعة الحدث"
    )

    severity = models.CharField(
        max_length=20,
        choices=NotificationSeverity.choices,
        default=NotificationSeverity.INFO,
        db_index=True,
        verbose_name="مستوى الحدث"
    )

    status = models.CharField(
        max_length=20,
        choices=NotificationEventStatus.choices,
        default=NotificationEventStatus.PENDING,
        db_index=True,
        verbose_name="حالة الحدث"
    )

    language_code = models.CharField(
        max_length=10,
        default="ar",
        db_index=True,
        verbose_name="رمز اللغة"
    )

    target_model = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="اسم الموديل المستهدف"
    )
    target_object_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="معرف الكيان المستهدف"
    )

    title = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="العنوان الافتراضي"
    )
    message = models.TextField(
        null=True,
        blank=True,
        verbose_name="الرسالة الافتراضية"
    )
    link = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        verbose_name="الرابط الداخلي"
    )

    context = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="بيانات الحدث"
    )

    source = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="مصدر الحدث"
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="تاريخ الإنشاء"
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ المعالجة"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "حدث تنبيهي"
        verbose_name_plural = "الأحداث التنبيهية"
        indexes = [
            models.Index(fields=["event_code", "-created_at"]),
            models.Index(fields=["event_group", "-created_at"]),
            models.Index(fields=["company", "-created_at"]),
            models.Index(fields=["target_user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["severity", "-created_at"]),
            models.Index(fields=["language_code", "-created_at"]),
        ]

    def mark_processed(self, status: str = NotificationEventStatus.PROCESSED):
        self.status = status
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at"])

    def mark_failed(self):
        self.status = NotificationEventStatus.FAILED
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at"])

    def __str__(self):
        return f"{self.event_code} #{self.pk}"


# ================================================================
# 🚚 Notification Delivery — تتبع كل قناة بشكل مستقل
# ================================================================
class NotificationDelivery(models.Model):
    """
    يمثل محاولة التسليم لقناة محددة لمستلم محدد.
    """

    event = models.ForeignKey(
        NotificationEvent,
        on_delete=models.CASCADE,
        related_name="deliveries",
        verbose_name="الحدث"
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="notification_deliveries",
        null=True,
        blank=True,
        verbose_name="الشركة"
    )

    recipient = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="notification_deliveries",
        null=True,
        blank=True,
        verbose_name="المستخدم المستلم"
    )

    channel = models.CharField(
        max_length=20,
        choices=NotificationChannel.choices,
        db_index=True,
        verbose_name="القناة"
    )

    status = models.CharField(
        max_length=20,
        choices=NotificationDeliveryStatus.choices,
        default=NotificationDeliveryStatus.PENDING,
        db_index=True,
        verbose_name="حالة التسليم"
    )

    destination = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="الوجهة"
    )

    subject = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="العنوان/الموضوع"
    )
    rendered_message = models.TextField(
        null=True,
        blank=True,
        verbose_name="المحتوى المرسل"
    )

    template_key = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="مفتاح القالب"
    )
    language_code = models.CharField(
        max_length=10,
        default="ar",
        db_index=True,
        verbose_name="رمز اللغة"
    )

    provider_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="اسم المزود"
    )
    provider_message_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="معرف الرسالة عند المزود"
    )
    provider_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="استجابة المزود"
    )

    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name="رسالة الخطأ"
    )
    attempts = models.PositiveIntegerField(
        default=0,
        verbose_name="عدد المحاولات"
    )
    max_attempts = models.PositiveIntegerField(
        default=3,
        verbose_name="أقصى عدد للمحاولات"
    )

    notification = models.ForeignKey(
        Notification,
        on_delete=models.SET_NULL,
        related_name="deliveries",
        null=True,
        blank=True,
        verbose_name="الإشعار الداخلي المرتبط"
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="تاريخ الإنشاء"
    )
    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="آخر محاولة"
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ الإرسال"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "سجل تسليم"
        verbose_name_plural = "سجلات التسليم"
        indexes = [
            models.Index(fields=["event", "channel"]),
            models.Index(fields=["recipient", "channel"]),
            models.Index(fields=["status", "channel"]),
            models.Index(fields=["company", "-created_at"]),
            models.Index(fields=["provider_message_id"]),
            models.Index(fields=["template_key", "language_code"]),
        ]

    def mark_attempt(self):
        self.attempts += 1
        self.last_attempt_at = timezone.now()
        self.save(update_fields=["attempts", "last_attempt_at"])

    def mark_sent(
        self,
        *,
        provider_message_id: str | None = None,
        provider_response: dict | None = None,
    ):
        self.status = NotificationDeliveryStatus.SENT
        self.sent_at = timezone.now()
        self.last_attempt_at = timezone.now()

        if provider_message_id is not None:
            self.provider_message_id = str(provider_message_id).strip()

        if provider_response is not None:
            self.provider_response = provider_response

        self.save(
            update_fields=[
                "status",
                "sent_at",
                "last_attempt_at",
                "provider_message_id",
                "provider_response",
            ]
        )

    def mark_failed(
        self,
        error_message: str | None = None,
        provider_response: dict | None = None,
    ):
        self.status = NotificationDeliveryStatus.FAILED
        self.last_attempt_at = timezone.now()

        if error_message is not None:
            self.error_message = str(error_message).strip()

        if provider_response is not None:
            self.provider_response = provider_response

        self.save(
            update_fields=[
                "status",
                "last_attempt_at",
                "error_message",
                "provider_response",
            ]
        )

    def mark_skipped(self, reason: str | None = None):
        self.status = NotificationDeliveryStatus.SKIPPED
        self.last_attempt_at = timezone.now()

        if reason is not None:
            self.error_message = str(reason).strip()

        self.save(
            update_fields=[
                "status",
                "last_attempt_at",
                "error_message",
            ]
        )

    def should_retry(self) -> bool:
        return (
            self.status in {
                NotificationDeliveryStatus.FAILED,
                NotificationDeliveryStatus.RETRYING,
            }
            and self.attempts < self.max_attempts
        )

    def __str__(self):
        return f"{self.event.event_code} -> {self.channel} -> {self.status}"