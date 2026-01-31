# ============================================================
# 📂 الملف: biotime_center/models.py
# ⚙️ نماذج Biotime Cloud — الإصدار V9.2 (Tenant Separation Fixed 🔒)
# 🚀 متوافق 100% مع IClock API (Terminals + Transactions)
# 🔥 فصل شركة Primey عن Biotime Tenant بشكل آمن
# ============================================================

from django.db import models
from django.utils import timezone


# ------------------------------------------------------------
# ⚙️ إعدادات الاتصال بـ Biotime Cloud — V9.2
# ------------------------------------------------------------
class BiotimeSetting(models.Model):
    """
    🧠 إعدادات ربط خادم Biotime Cloud (JWT + Login)

    ✔ Primey Company  → شركة النظام الداخلية
    ✔ Biotime Tenant → اسم الشركة الحقيقي داخل منصة Biotime
    """

    server_url = models.URLField(
        max_length=255,
        verbose_name="🌐 رابط الخادم"
    )

    # ✅ شركة Primey (ربط داخلي بالنظام)
    company = models.ForeignKey(
        "company_manager.Company",
        on_delete=models.CASCADE,
        related_name="biotime_settings",
        verbose_name="🏢 شركة Primey",
        db_index=True,
    )

    # ✅ شركة Biotime الحقيقية (Tenant Name)
    # مثال: demozkdxb
    biotime_company = models.CharField(
        max_length=150,
        verbose_name="☁️ Biotime Tenant",
        help_text="اسم الشركة داخل منصة Biotime Cloud مثل: demozkdxb",
        db_index=True,
    )

    email = models.CharField(
        max_length=150,
        verbose_name="📧 البريد الإلكتروني"
    )

    password = models.CharField(
        max_length=255,
        verbose_name="🔑 كلمة المرور"
    )

    # 🔐 JWT Token
    jwt_token = models.TextField(
        blank=True,
        null=True,
        verbose_name="🔐 رمز JWT"
    )

    token_expiry = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="⏳ انتهاء صلاحية الرمز"
    )

    # 📡 حالة الاتصال
    last_login_status = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="📡 حالة آخر تسجيل دخول"
    )

    last_login_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="🕒 وقت آخر تسجيل دخول"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Biotime Setting"
        verbose_name_plural = "Biotime Settings"

        # ✅ يمنع تكرار إعدادات Biotime لنفس الشركة
        unique_together = (
            ("company", "biotime_company"),
        )

    def __str__(self):
        return f"Biotime Setting ({self.company} → {self.biotime_company})"


# ------------------------------------------------------------
# 💻 أجهزة Biotime (Terminals) — IClock API — V9.0 (UNCHANGED)
# ------------------------------------------------------------
class BiotimeDevice(models.Model):
    """💻 الأجهزة من IClock API — terminals"""

    device_id = models.IntegerField(unique=True)
    sn = models.CharField(max_length=150)
    alias = models.CharField(max_length=150)
    terminal_name = models.CharField(max_length=150, blank=True, null=True)

    ip_address = models.GenericIPAddressField(blank=True, null=True)
    firmware_version = models.CharField(max_length=100, blank=True, null=True)
    push_ver = models.CharField(max_length=100, blank=True, null=True)

    state = models.IntegerField(default=0)
    terminal_tz = models.IntegerField(blank=True, null=True)

    # المنطقة
    area_id = models.IntegerField(blank=True, null=True)
    area_code = models.CharField(max_length=100, blank=True, null=True)
    area_name = models.CharField(max_length=150, blank=True, null=True)

    # الشركة (كما تعيدها Biotime)
    company_id = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=150, blank=True, null=True)

    # معلومات إضافية
    last_activity = models.CharField(max_length=255, blank=True, null=True)
    user_count = models.IntegerField(blank=True, null=True)
    fp_count = models.IntegerField(blank=True, null=True)
    face_count = models.IntegerField(blank=True, null=True)
    palm_count = models.IntegerField(blank=True, null=True)
    transaction_count = models.IntegerField(blank=True, null=True)

    push_time = models.CharField(max_length=100, blank=True, null=True)
    transfer_time = models.CharField(max_length=100, blank=True, null=True)
    transfer_interval = models.IntegerField(blank=True, null=True)

    # RAW JSON
    raw_json = models.JSONField(blank=True, null=True)

    last_sync = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.alias} ({self.sn})"


# ------------------------------------------------------------
# 👥 موظفون Biotime — V9.0 (UNCHANGED)
# ------------------------------------------------------------
class BiotimeEmployee(models.Model):
    """👥 الموظفون المتزامنون مع Biotime"""

    employee_id = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=150)

    department = models.CharField(max_length=150, blank=True, null=True)
    position = models.CharField(max_length=150, blank=True, null=True)

    card_number = models.CharField(max_length=100, blank=True, null=True)
    enrolled_fingers = models.PositiveIntegerField(default=0)
    photo_url = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"


# ------------------------------------------------------------
# 🕒 سجلات الحضور — Transactions — V9.0 (UNCHANGED)
# ------------------------------------------------------------
class BiotimeLog(models.Model):
    """🕒 السجلات من IClock — transactions"""

    log_id = models.IntegerField(unique=True)
    employee_code = models.CharField(max_length=100)
    punch_time = models.DateTimeField()
    punch_state = models.CharField(max_length=10)
    verify_type = models.IntegerField(default=0)
    work_code = models.CharField(max_length=10, blank=True, null=True)

    device_sn = models.CharField(max_length=150)
    terminal_alias = models.CharField(max_length=150, blank=True, null=True)
    area_alias = models.CharField(max_length=150, blank=True, null=True)

    # RAW JSON
    raw_json = models.JSONField(blank=True, null=True)

    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.employee_code} - {self.punch_time}"


# ------------------------------------------------------------
# 📘 سجل المزامنة — Biotime Sync Log (UNCHANGED)
# ------------------------------------------------------------
class BiotimeSyncLog(models.Model):
    """🧠 سجل عمليات المزامنة"""

    timestamp = models.DateTimeField(default=timezone.now)

    devices_synced = models.PositiveIntegerField(default=0)
    employees_synced = models.PositiveIntegerField(default=0)
    logs_synced = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=[
            ("SUCCESS", "نجاح"),
            ("FAILED", "فشل"),
            ("PARTIAL", "جزئي"),
        ],
        default="SUCCESS"
    )

    message = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Sync {self.status} — {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
