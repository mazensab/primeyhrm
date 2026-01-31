# ============================================================
# 📂 settings_center/services.py
# 🧠 Version: V13.1 Ultra Stable
# 🔒 Compatible with Settings Center (No SystemSetting Model)
# ============================================================

from functools import lru_cache

from django.core.mail import EmailMessage

# ============================================================
# 🟦 Settings Center Models (Single Source of Truth)
# ============================================================

from .models import (
    SettingsGeneral,
    SettingsCompany,
    SettingsBranding,
    SettingsEmail,
    SettingsIntegrations,
    SettingsSecurity,
    SettingsBackups,
    SettingsAuditLog,
)

# ============================================================
# 🧱 1) Helpers — Singleton Getters
# ============================================================

def get_general_settings():
    return SettingsGeneral.get_settings()


def get_company_settings():
    return SettingsCompany.get_settings()


def get_branding_settings():
    return SettingsBranding.get_settings()


def get_email_settings():
    return SettingsEmail.get_settings()


def get_integrations_settings():
    return SettingsIntegrations.get_settings()


def get_security_settings():
    return SettingsSecurity.get_settings()


def get_backups_settings():
    return SettingsBackups.get_settings()


# ============================================================
# 🟩 2) SMTP Email Testing
# ============================================================

def test_smtp():
    """
    📧 اختبار إعدادات SMTP فعليًا
    """
    cfg = get_email_settings()

    email = EmailMessage(
        subject="Test SMTP — Primey HR Cloud",
        body="✔ تم إرسال رسالة الاختبار بنجاح",
        to=[cfg.username],
    )
    email.send(fail_silently=False)

    return "✔ تم إرسال رسالة الاختبار بنجاح"


# ============================================================
# 🟪 3) ZATCA Integration Test
# ============================================================

def test_zatca():
    """
    🟪 اختبار اتصال تجريبي بزاتكا
    """
    cfg = get_integrations_settings()

    if not cfg.base_url:
        return "❌ لم يتم ضبط عنوان زاتكا"

    return f"✔ تم الاتصال التجريبي بزاتكا عبر: {cfg.base_url}"


# ============================================================
# 👥 4) Sync External Employees (Placeholder)
# ============================================================

def sync_external_employees():
    """
    👥 مزامنة الموظفين من أنظمة خارجية (تجريبي)
    """
    cfg = get_integrations_settings()

    if not cfg.active:
        return 0

    # TODO: API Integration
    return 0


# ============================================================
# 🧩 5) Unified Settings Getter — For Templates
# ============================================================

def get_all_settings():
    return {
        "general": get_general_settings(),
        "company": get_company_settings(),
        "branding": get_branding_settings(),
        "email": get_email_settings(),
        "integrations": get_integrations_settings(),
        "security": get_security_settings(),
        "backups": get_backups_settings(),
    }


# ============================================================
# 📝 6) Audit Log Creator
# ============================================================

def add_audit_log(company, user, section, field, old, new, ip):
    SettingsAuditLog.objects.create(
        company=company,
        user=user,
        section=section,
        field_name=field,
        old_value=old,
        new_value=new,
        ip_address=ip,
    )


# ============================================================
# 🔒 7) System Governance — Derived From Settings
# ============================================================

@lru_cache(maxsize=1)
def get_system_flags():
    """
    🔒 Cached System Flags
    - Derived from SettingsGeneral + SettingsSecurity
    """
    general = get_general_settings()
    security = get_security_settings()

    return {
        "platform_active": general.platform_active,
        "maintenance_mode": general.maintenance_mode,
        "readonly_mode": security.readonly_mode,
        "billing_enabled": general.billing_enabled,
        "enforce_subscription": general.enforce_subscription,
    }


def clear_system_flags_cache():
    get_system_flags.cache_clear()


# ============================================================
# 🧠 Flags Helpers
# ============================================================

def is_platform_active() -> bool:
    return get_system_flags()["platform_active"]


def is_maintenance_mode() -> bool:
    return get_system_flags()["maintenance_mode"]


def is_readonly_mode() -> bool:
    return get_system_flags()["readonly_mode"]


def is_billing_enabled() -> bool:
    return get_system_flags()["billing_enabled"]


def is_subscription_enforced() -> bool:
    return get_system_flags()["enforce_subscription"]


# ============================================================
# 🧩 Modules Kill Switch (via SettingsGeneral)
# ============================================================

def is_module_enabled(module_key: str) -> bool:
    """
    module_key examples:
        - employee
        - attendance
        - leave
        - payroll
        - performance
    """
    general = get_general_settings()

    attr = f"module_{module_key}"
    return bool(getattr(general, attr, True))

# ============================================================
# ⚙️ System Settings — Service Layer
# Version: V1.0 Ultra Stable
# ============================================================

from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .models import SettingsGeneral, SettingsAuditLog


def get_system_setting():
    """
    🔍 Return single system settings row (or None)
    """
    return SettingsGeneral.objects.first()


def update_system_setting(*, user, field: str, value):
    """
    🔐 Update global system setting (Super Admin only)

    - Writes to SettingsGeneral
    - Audit logged
    - Single Source of Truth
    """

    # --------------------------------------------------------
    # 1) Permission (Super Admin only)
    # --------------------------------------------------------
    if not user.is_superuser:
        raise PermissionDenied("Super admin privileges required")

    # --------------------------------------------------------
    # 2) Get or Create Settings Row
    # --------------------------------------------------------
    settings = SettingsGeneral.objects.first()
    if not settings:
        settings = SettingsGeneral.objects.create()

    # --------------------------------------------------------
    # 3) Validate Field
    # --------------------------------------------------------
    if not hasattr(settings, field):
        raise ValueError(f"Invalid system setting field: {field}")

    old_value = getattr(settings, field)

    # --------------------------------------------------------
    # 4) Update Value
    # --------------------------------------------------------
    setattr(settings, field, value)
    settings.save(update_fields=[field])

    # --------------------------------------------------------
    # 5) Audit Log
    # --------------------------------------------------------
    SettingsAuditLog.objects.create(
        company=None,  # Global / System
        user=user,
        section="system",
        field_name=field,
        old_value=str(old_value),
        new_value=str(value),
        ip_address=None,
    )

    return {
        "field": field,
        "old": old_value,
        "new": value,
        "updated_at": timezone.now().isoformat(),
    }
