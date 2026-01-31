# ============================================================
# 📂 Settings Center — Models
# ⚙️ Version: V8 Ultra Pro — Unified Singleton Backend
# ============================================================

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from company_manager.models import Company


# ============================================================
# 🔧 Helper: Singleton Base Class
# ============================================================
class SingletonModel(models.Model):
    """
    🧩 Base Singleton — always returns 1 row only
    """
    class Meta:
        abstract = True

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj


# ============================================================
# ⚙️ 1) GENERAL SETTINGS
# ============================================================
class SettingsGeneral(SingletonModel):
    system_name = models.CharField(max_length=150, default="Primey HR Cloud")
    support_email = models.EmailField(default="support@primeyhrm.com")
    support_phone = models.CharField(max_length=20, blank=True, null=True)
    theme_mode = models.CharField(
        max_length=10,
        choices=[("dark", "الوضع الداكن"), ("light", "الوضع الفاتح")],
        default="dark",
    )
    enable_ai_assistant = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.system_name} ({self.theme_mode})"


# ============================================================
# 🏢 2) COMPANY SETTINGS
# ============================================================
class SettingsCompany(SingletonModel):
    company_name = models.CharField(max_length=255)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to="settings/company/", blank=True, null=True)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.company_name


# ============================================================
# 🎨 3) BRANDING SETTINGS
# ============================================================
class SettingsBranding(SingletonModel):
    theme_color = models.CharField(max_length=20, default="#0d6efd")
    accent_color = models.CharField(max_length=20, default="#1e88e5")
    background_style = models.CharField(
        max_length=20,
        choices=[("glass", "زجاجي"), ("solid", "صلب"), ("gradient", "متدرج")],
        default="glass",
    )
    logo = models.ImageField(upload_to="settings/branding/logo/", blank=True, null=True)
    favicon = models.ImageField(upload_to="settings/branding/favicon/", blank=True, null=True)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"الهوية ({self.background_style})"


# ============================================================
# 📧 4) EMAIL SETTINGS
# ============================================================
class SettingsEmail(SingletonModel):
    smtp_server = models.CharField(max_length=200)
    smtp_port = models.PositiveIntegerField(default=587)
    use_tls = models.BooleanField(default=True)
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=150)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Email: {self.username}"


# ============================================================
# 🔌 5) INTEGRATION SETTINGS
# ============================================================
class SettingsIntegrations(SingletonModel):
    service_name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=255)
    base_url = models.URLField(blank=True, null=True)
    active = models.BooleanField(default=True)
    last_test_status = models.CharField(max_length=50, blank=True, null=True)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.service_name} ({'نشط' if self.active else 'موقوف'})"


# ============================================================
# 🔐 6) SECURITY SETTINGS
# ============================================================
class SettingsSecurity(SingletonModel):
    enforce_2fa = models.BooleanField(default=False)
    session_timeout_minutes = models.PositiveIntegerField(default=30)
    password_min_length = models.PositiveIntegerField(default=8)
    allow_password_reuse = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "Security Settings"


# ============================================================
# 💾 7) BACKUPS SETTINGS
# ============================================================
class SettingsBackups(SingletonModel):
    enable_auto_backup = models.BooleanField(default=False)
    backup_frequency = models.CharField(
        max_length=50,
        choices=[("daily", "يومي"), ("weekly", "أسبوعي"), ("monthly", "شهري")],
        default="weekly",
    )
    last_backup_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "Backups Settings"


# ============================================================
# 📘 8) AUDIT LOG
# ============================================================
class SettingsAuditLog(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="settings_audit_logs"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    section = models.CharField(max_length=50)
    field_name = models.CharField(max_length=200)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.section} — {self.field_name} — {self.timestamp}"


# ============================================================
# 🇸🇦 9) NATIONAL ADDRESS CACHE (SYSTEM LEVEL)
# ============================================================
class NationalAddressCity(models.Model):
    """
    🇸🇦 City Cache
    """
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        verbose_name = "مدينة"
        verbose_name_plural = "المدن"

    def __str__(self):
        return self.name


class NationalAddressDistrict(models.Model):
    """
    🇸🇦 District Cache
    """
    name = models.CharField(max_length=150)
    city = models.ForeignKey(
        NationalAddressCity,
        on_delete=models.CASCADE,
        related_name="districts",
    )

    class Meta:
        unique_together = ("name", "city")
        verbose_name = "حي"
        verbose_name_plural = "الأحياء"

    def __str__(self):
        return f"{self.name} — {self.city.name}"


class NationalAddressStreet(models.Model):
    """
    🇸🇦 Street Cache
    """
    name = models.CharField(max_length=200)
    district = models.ForeignKey(
        NationalAddressDistrict,
        on_delete=models.CASCADE,
        related_name="streets",
    )

    class Meta:
        unique_together = ("name", "district")
        verbose_name = "شارع"
        verbose_name_plural = "الشوارع"

    def __str__(self):
        return self.name
