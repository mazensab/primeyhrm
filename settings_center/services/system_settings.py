# ============================================================
# ⚙️ System Settings Service
# Mham Cloud
# ============================================================

from django.utils import timezone
from settings_center.models import (
    SettingsGeneral,
    SettingsCompany,
    SettingsBranding,
    SettingsEmail,
    SettingsIntegrations,
    SettingsSecurity,
    SettingsBackups,
    SettingsAuditLog,
)


def update_system_setting(
    *,
    section: str,
    field: str,
    value,
    user=None,
    company=None,
    ip_address=None,
):
    """
    تحديث إعداد واحد فقط + تسجيل Audit Log
    """

    MODEL_MAP = {
        "general": SettingsGeneral,
        "company": SettingsCompany,
        "branding": SettingsBranding,
        "email": SettingsEmail,
        "integrations": SettingsIntegrations,
        "security": SettingsSecurity,
        "backups": SettingsBackups,
    }

    model_cls = MODEL_MAP.get(section)
    if not model_cls:
        raise ValueError("Invalid settings section")

    obj = model_cls.get_settings()

    if not hasattr(obj, field):
        raise ValueError("Invalid settings field")

    old_value = getattr(obj, field)
    setattr(obj, field, value)
    obj.updated_at = timezone.now()
    obj.save(update_fields=[field, "updated_at"])

    # 🔐 Audit Log (اختياري لكن مهم)
    if company:
        SettingsAuditLog.objects.create(
            company=company,
            user=user,
            section=section,
            field_name=field,
            old_value=str(old_value),
            new_value=str(value),
            ip_address=ip_address,
        )

    return obj
# ============================================================
# 📖 Read System Settings (Single Source of Truth)
# ============================================================

def get_system_setting():
    """
    قراءة الإعدادات العامة للنظام (Global Settings)

    - Fail-safe: يرجع None إذا لم يوجد سجل
    - يستخدم من API فقط (Read Only)
    """

    try:
        return SettingsGeneral.get_settings()
    except Exception:
        return None
# ============================================================
# 📖 Read System Settings (Single Source of Truth)
# ============================================================

def get_system_setting():
    """
    قراءة الإعدادات العامة للنظام (Global Settings)

    - Fail-safe: يرجع None إذا لم يوجد سجل
    - يستخدم من API فقط (Read Only)
    """

    try:
        return SettingsGeneral.get_settings()
    except Exception:
        return None
