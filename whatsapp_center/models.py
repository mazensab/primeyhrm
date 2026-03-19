# ============================================================
# 📂 whatsapp_center/models.py
# Primey HR Cloud - WhatsApp Center Models
# ============================================================
# ✅ يدعم:
# - System Scope
# - Company Scope
# - WhatsApp Templates
# - Message Logs
# - Retry Attempts
# - Webhook Events
# - Broadcast Messaging
# - Subscription Expiry Reminders
# - WhatsApp Web Session (QR / Pairing Code)
# ============================================================

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


# ============================================================
# 🧩 Common Choices
# ============================================================

class WhatsAppProvider(models.TextChoices):
    META = "META", "Meta"
    TWILIO = "TWILIO", "Twilio"
    UNIFONIC = "UNIFONIC", "Unifonic"
    OTHER = "OTHER", "Other"

    # --------------------------------------------------------
    # مزود جديد للجلسة عبر واتساب ويب
    # --------------------------------------------------------
    WEB_SESSION = "whatsapp_web_session", "WhatsApp Web Session"
    META_CLOUD_API = "meta_cloud_api", "Meta Cloud API"


class SessionMode(models.TextChoices):
    QR = "qr", "QR"
    PAIRING_CODE = "pairing_code", "Pairing Code"


class SessionStatus(models.TextChoices):
    DISCONNECTED = "disconnected", "Disconnected"
    QR_PENDING = "qr_pending", "QR Pending"
    PAIR_PENDING = "pair_pending", "Pair Pending"
    CONNECTED = "connected", "Connected"
    FAILED = "failed", "Failed"


class ScopeType(models.TextChoices):
    SYSTEM = "SYSTEM", "System"
    COMPANY = "COMPANY", "Company"


class MessageType(models.TextChoices):
    TEXT = "TEXT", "Text"
    TEMPLATE = "TEMPLATE", "Template"
    DOCUMENT = "DOCUMENT", "Document"


class DeliveryStatus(models.TextChoices):
    QUEUED = "QUEUED", "Queued"
    SENT = "SENT", "Sent"
    DELIVERED = "DELIVERED", "Delivered"
    READ = "READ", "Read"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class TriggerSource(models.TextChoices):
    SYSTEM = "system", "System"
    BILLING = "billing", "Billing"
    ATTENDANCE = "attendance", "Attendance"
    LEAVE = "leave", "Leave"
    PAYROLL = "payroll", "Payroll"
    EMPLOYEE = "employee", "Employee"
    COMPANY = "company", "Company"
    BROADCAST = "broadcast", "Broadcast"


class BroadcastAudienceType(models.TextChoices):
    ALL_COMPANIES = "ALL_COMPANIES", "All Companies"
    ACTIVE_COMPANIES = "ACTIVE_COMPANIES", "Active Companies"
    EXPIRED_COMPANIES = "EXPIRED_COMPANIES", "Expired Companies"
    EXPIRING_COMPANIES = "EXPIRING_COMPANIES", "Expiring Companies"
    COMPANY_ADMINS = "COMPANY_ADMINS", "Company Admins"
    SYSTEM_USERS = "SYSTEM_USERS", "System Users"
    RAW_NUMBERS = "RAW_NUMBERS", "Raw Numbers"


class BroadcastStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SCHEDULED = "SCHEDULED", "Scheduled"
    RUNNING = "RUNNING", "Running"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class RecipientType(models.TextChoices):
    COMPANY = "COMPANY", "Company"
    COMPANY_ADMIN = "COMPANY_ADMIN", "Company Admin"
    USER = "USER", "User"
    EMPLOYEE = "EMPLOYEE", "Employee"
    RAW = "RAW", "Raw Number"


# ============================================================
# 🧾 Template Lifecycle Choices
# ============================================================

class TemplateApprovalStatus(models.TextChoices):
    """
    حالة اعتماد القالب داخل النظام / المزود.
    """
    DRAFT = "DRAFT", "Draft"
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class TemplateProviderSyncStatus(models.TextChoices):
    """
    حالة مزامنة القالب مع المزود الخارجي.
    """
    NOT_SYNCED = "NOT_SYNCED", "Not Synced"
    SYNCED = "SYNCED", "Synced"
    FAILED = "FAILED", "Failed"


# ============================================================
# 🔐 Validators
# ============================================================

phone_validator = RegexValidator(
    regex=r"^\+?[1-9]\d{7,14}$",
    message="Phone number must be in international format, e.g. +9665XXXXXXXX",
)


# ============================================================
# 🏢 Lazy reference names
# ============================================================

COMPANY_MODEL = "company_manager.Company"
EMPLOYEE_MODEL = "employee_center.Employee"


# ============================================================
# ⚙️ System WhatsApp Config
# ============================================================

class SystemWhatsAppConfig(models.Model):
    """
    إعدادات واتساب العامة الخاصة بسوبر أدمن النظام.
    غالبًا سيكون هناك سجل واحد فقط نشط داخل النظام.
    """

    provider = models.CharField(
        max_length=50,
        choices=WhatsAppProvider.choices,
        default=WhatsAppProvider.WEB_SESSION,
    )
    is_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    business_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    phone_number_id = models.CharField(max_length=255, blank=True)
    business_account_id = models.CharField(max_length=255, blank=True)
    app_id = models.CharField(max_length=255, blank=True)

    access_token = models.TextField(blank=True)
    webhook_verify_token = models.CharField(max_length=255, blank=True)
    webhook_callback_url = models.URLField(blank=True)
    webhook_verified = models.BooleanField(default=False)

    api_version = models.CharField(max_length=50, default="v22.0")
    default_language_code = models.CharField(max_length=20, default="ar")
    default_country_code = models.CharField(max_length=10, default="966")

    allow_broadcasts = models.BooleanField(default=True)
    send_test_enabled = models.BooleanField(default=True)
    default_test_recipient = models.CharField(max_length=20, blank=True)

    # --------------------------------------------------------
    # إعدادات الجلسة - WhatsApp Web Session
    # --------------------------------------------------------
    session_name = models.CharField(max_length=255, default="primey-system-session")
    session_mode = models.CharField(
        max_length=30,
        choices=SessionMode.choices,
        default=SessionMode.QR,
    )
    session_status = models.CharField(
        max_length=30,
        choices=SessionStatus.choices,
        default=SessionStatus.DISCONNECTED,
    )
    session_connected_phone = models.CharField(max_length=30, blank=True)
    session_device_label = models.CharField(max_length=255, blank=True)
    session_last_connected_at = models.DateTimeField(null=True, blank=True)
    session_qr_code = models.TextField(blank=True)
    session_pairing_code = models.CharField(max_length=100, blank=True)

    last_health_check_at = models.DateTimeField(null=True, blank=True)
    last_error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System WhatsApp Config"
        verbose_name_plural = "System WhatsApp Configs"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"System WhatsApp Config #{self.pk}"


# ============================================================
# 🏢 Company WhatsApp Config
# ============================================================

class CompanyWhatsAppConfig(models.Model):
    """
    إعدادات واتساب الخاصة بكل شركة.
    كل شركة لها سجل إعداد واحد مستقل.
    """

    company = models.OneToOneField(
        COMPANY_MODEL,
        on_delete=models.CASCADE,
        related_name="whatsapp_config",
    )

    provider = models.CharField(
        max_length=50,
        choices=WhatsAppProvider.choices,
        default=WhatsAppProvider.WEB_SESSION,
    )
    is_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    display_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    phone_number_id = models.CharField(max_length=255, blank=True)
    business_account_id = models.CharField(max_length=255, blank=True)
    app_id = models.CharField(max_length=255, blank=True)

    access_token = models.TextField(blank=True)
    webhook_verify_token = models.CharField(max_length=255, blank=True)
    webhook_callback_url = models.URLField(blank=True)
    webhook_verified = models.BooleanField(default=False)

    default_language_code = models.CharField(max_length=20, default="ar")
    default_country_code = models.CharField(max_length=10, default="966")

    # --------------------------------------------------------
    # سياسات التنبيهات على مستوى الشركة
    # --------------------------------------------------------
    send_employee_alerts = models.BooleanField(default=True)
    send_attendance_alerts = models.BooleanField(default=True)
    send_leave_alerts = models.BooleanField(default=True)
    send_payroll_alerts = models.BooleanField(default=False)
    send_billing_alerts = models.BooleanField(default=False)
    send_system_copy_alerts = models.BooleanField(default=False)
    allow_broadcasts = models.BooleanField(default=True)
    send_test_enabled = models.BooleanField(default=True)
    default_test_recipient = models.CharField(max_length=20, blank=True)

    # --------------------------------------------------------
    # إعدادات الجلسة على مستوى الشركة
    # --------------------------------------------------------
    session_name = models.CharField(max_length=255, blank=True)
    session_mode = models.CharField(
        max_length=30,
        choices=SessionMode.choices,
        default=SessionMode.QR,
    )
    session_status = models.CharField(
        max_length=30,
        choices=SessionStatus.choices,
        default=SessionStatus.DISCONNECTED,
    )
    session_connected_phone = models.CharField(max_length=30, blank=True)
    session_device_label = models.CharField(max_length=255, blank=True)
    session_last_connected_at = models.DateTimeField(null=True, blank=True)
    session_qr_code = models.TextField(blank=True)
    session_pairing_code = models.CharField(max_length=100, blank=True)

    last_health_check_at = models.DateTimeField(null=True, blank=True)
    last_error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company WhatsApp Config"
        verbose_name_plural = "Company WhatsApp Configs"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["is_enabled"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["provider"]),
            models.Index(fields=["session_status"]),
        ]

    def __str__(self) -> str:
        company_name = getattr(self.company, "name", None) or f"Company #{self.company_id}"
        return f"{company_name} - WhatsApp Config"


# ============================================================
# 🧾 WhatsApp Template
# ============================================================

class WhatsAppTemplate(models.Model):
    """
    قوالب الرسائل.
    يمكن أن تكون:
    - System Scope
    - Company Scope
    """

    scope_type = models.CharField(
        max_length=20,
        choices=ScopeType.choices,
        default=ScopeType.SYSTEM,
    )
    company = models.ForeignKey(
        COMPANY_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="whatsapp_templates",
    )

    event_code = models.CharField(max_length=100)
    template_key = models.CharField(max_length=100)
    template_name = models.CharField(max_length=255, blank=True)
    language_code = models.CharField(max_length=20, default="ar")

    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )

    header_text = models.TextField(blank=True)
    body_text = models.TextField()
    footer_text = models.TextField(blank=True)

    button_text = models.CharField(max_length=255, blank=True)
    button_url = models.URLField(blank=True)

    meta_template_name = models.CharField(max_length=255, blank=True)
    meta_template_namespace = models.CharField(max_length=255, blank=True)

    # --------------------------------------------------------
    # دورة حياة القالب داخل Primey + حالة المزامنة مع المزود
    # --------------------------------------------------------
    approval_status = models.CharField(
        max_length=20,
        choices=TemplateApprovalStatus.choices,
        default=TemplateApprovalStatus.DRAFT,
    )
    provider_status = models.CharField(
        max_length=20,
        choices=TemplateProviderSyncStatus.choices,
        default=TemplateProviderSyncStatus.NOT_SYNCED,
    )
    rejection_reason = models.TextField(blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_whatsapp_templates",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_whatsapp_templates",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "WhatsApp Template"
        verbose_name_plural = "WhatsApp Templates"
        ordering = ["scope_type", "event_code", "-version", "-id"]
        indexes = [
            models.Index(fields=["scope_type", "event_code"]),
            models.Index(fields=["company", "event_code"]),
            models.Index(fields=["language_code"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["approval_status"]),
            models.Index(fields=["provider_status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["scope_type", "company", "event_code", "language_code", "version"],
                name="uniq_whatsapp_template_scope_company_event_lang_version",
            )
        ]

    def __str__(self) -> str:
        return f"{self.scope_type} | {self.event_code} | v{self.version}"


# ============================================================
# 📨 WhatsApp Message Log
# ============================================================

class WhatsAppMessageLog(models.Model):
    """
    السجل المركزي لكل رسالة واتساب.
    """

    scope_type = models.CharField(
        max_length=20,
        choices=ScopeType.choices,
        default=ScopeType.SYSTEM,
    )
    company = models.ForeignKey(
        COMPANY_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="whatsapp_message_logs",
    )

    trigger_source = models.CharField(
        max_length=50,
        choices=TriggerSource.choices,
        default=TriggerSource.SYSTEM,
    )
    event_code = models.CharField(max_length=100, blank=True)

    recipient_name = models.CharField(max_length=255, blank=True)
    recipient_phone = models.CharField(max_length=20, validators=[phone_validator])
    recipient_role = models.CharField(max_length=100, blank=True)

    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )

    template = models.ForeignKey(
        "WhatsAppTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="message_logs",
    )
    template_name_snapshot = models.CharField(max_length=255, blank=True)
    language_code = models.CharField(max_length=20, default="ar")

    message_subject = models.CharField(max_length=255, blank=True)
    header_text = models.TextField(blank=True)
    message_body = models.TextField(blank=True)
    footer_text = models.TextField(blank=True)

    attachment_url = models.URLField(blank=True)
    attachment_name = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)

    external_message_id = models.CharField(max_length=255, blank=True)
    provider_status = models.CharField(max_length=255, blank=True)
    delivery_status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.QUEUED,
    )

    failure_reason = models.TextField(blank=True)
    failure_code = models.CharField(max_length=100, blank=True)

    related_model = models.CharField(max_length=100, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)

    payload_json = models.JSONField(default=dict, blank=True)
    response_json = models.JSONField(default=dict, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "WhatsApp Message Log"
        verbose_name_plural = "WhatsApp Message Logs"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["company", "created_at"]),
            models.Index(fields=["scope_type", "created_at"]),
            models.Index(fields=["event_code"]),
            models.Index(fields=["delivery_status"]),
            models.Index(fields=["recipient_phone"]),
            models.Index(fields=["external_message_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.recipient_phone} | {self.delivery_status} | {self.created_at:%Y-%m-%d %H:%M}"


# ============================================================
# 🔁 WhatsApp Message Attempt
# ============================================================

class WhatsAppMessageAttempt(models.Model):
    """
    كل محاولة إرسال مستقلة تسجل هنا.
    """

    message_log = models.ForeignKey(
        WhatsAppMessageLog,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    attempt_number = models.PositiveIntegerField(default=1)

    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)

    status_code = models.PositiveIntegerField(null=True, blank=True)
    provider_status = models.CharField(max_length=255, blank=True)
    is_success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "WhatsApp Message Attempt"
        verbose_name_plural = "WhatsApp Message Attempts"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["message_log", "attempt_number"],
                name="uniq_whatsapp_attempt_per_message",
            )
        ]

    def __str__(self) -> str:
        return f"Attempt #{self.attempt_number} for Log #{self.message_log_id}"


# ============================================================
# 🌐 WhatsApp Webhook Event
# ============================================================

class WhatsAppWebhookEvent(models.Model):
    """
    تخزين webhook الخام القادم من المزود ثم معالجته لاحقًا.
    """

    scope_type = models.CharField(
        max_length=20,
        choices=ScopeType.choices,
        default=ScopeType.SYSTEM,
    )
    company = models.ForeignKey(
        COMPANY_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="whatsapp_webhook_events",
    )

    provider = models.CharField(
        max_length=50,
        choices=WhatsAppProvider.choices,
        default=WhatsAppProvider.META,
    )
    event_type = models.CharField(max_length=100, blank=True)
    external_message_id = models.CharField(max_length=255, blank=True)

    payload_json = models.JSONField(default=dict, blank=True)

    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "WhatsApp Webhook Event"
        verbose_name_plural = "WhatsApp Webhook Events"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["external_message_id"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["is_processed"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Webhook {self.event_type or 'unknown'} #{self.pk}"


# ============================================================
# 📢 WhatsApp Broadcast
# ============================================================

class WhatsAppBroadcast(models.Model):
    """
    رسالة جماعية من Super Admin.
    """

    scope_type = models.CharField(
        max_length=20,
        choices=ScopeType.choices,
        default=ScopeType.SYSTEM,
    )

    title = models.CharField(max_length=255)
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )

    template = models.ForeignKey(
        WhatsAppTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="broadcasts",
    )

    message_body = models.TextField(blank=True)
    attachment_url = models.URLField(blank=True)
    attachment_name = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)

    audience_type = models.CharField(
        max_length=50,
        choices=BroadcastAudienceType.choices,
        default=BroadcastAudienceType.ALL_COMPANIES,
    )
    raw_numbers = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=20,
        choices=BroadcastStatus.choices,
        default=BroadcastStatus.DRAFT,
    )

    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_whatsapp_broadcasts",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "WhatsApp Broadcast"
        verbose_name_plural = "WhatsApp Broadcasts"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["audience_type"]),
            models.Index(fields=["scheduled_at"]),
        ]

    def __str__(self) -> str:
        return self.title


# ============================================================
# 👥 WhatsApp Broadcast Recipient
# ============================================================

class WhatsAppBroadcastRecipient(models.Model):
    """
    المستلمون الناتجون عن كل Broadcast.
    """

    broadcast = models.ForeignKey(
        WhatsAppBroadcast,
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    company = models.ForeignKey(
        COMPANY_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whatsapp_broadcast_recipients",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whatsapp_broadcast_recipients",
    )
    employee = models.ForeignKey(
        EMPLOYEE_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whatsapp_broadcast_recipients",
    )

    recipient_name = models.CharField(max_length=255, blank=True)
    recipient_phone = models.CharField(max_length=20, validators=[phone_validator])
    recipient_type = models.CharField(
        max_length=30,
        choices=RecipientType.choices,
        default=RecipientType.RAW,
    )

    delivery_status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.QUEUED,
    )
    external_message_id = models.CharField(max_length=255, blank=True)
    failure_reason = models.TextField(blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "WhatsApp Broadcast Recipient"
        verbose_name_plural = "WhatsApp Broadcast Recipients"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["broadcast", "delivery_status"]),
            models.Index(fields=["recipient_phone"]),
            models.Index(fields=["company"]),
        ]

    def __str__(self) -> str:
        return f"{self.recipient_phone} ({self.delivery_status})"


# ============================================================
# ⏰ WhatsApp Reminder Rule
# ============================================================

class WhatsAppReminderRule(models.Model):
    """
    قاعدة تذكير قابلة للتوسع.
    مثال:
    - تنبيه الاشتراك قبل 7 أيام
    """

    scope_type = models.CharField(
        max_length=20,
        choices=ScopeType.choices,
        default=ScopeType.SYSTEM,
    )
    event_code = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    days_before = models.PositiveIntegerField(default=7)

    send_to_company = models.BooleanField(default=True)
    send_to_company_admin = models.BooleanField(default=True)
    send_to_system_copy = models.BooleanField(default=False)

    template = models.ForeignKey(
        WhatsAppTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reminder_rules",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "WhatsApp Reminder Rule"
        verbose_name_plural = "WhatsApp Reminder Rules"
        ordering = ["event_code", "days_before", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["scope_type", "event_code", "days_before"],
                name="uniq_whatsapp_reminder_rule",
            )
        ]

    def __str__(self) -> str:
        return f"{self.event_code} - {self.days_before} days"