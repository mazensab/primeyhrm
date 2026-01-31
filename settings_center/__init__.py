# 📂 الملف: settings_center/__init__.py
# ⚙️ Settings Center V7.7 — Glass Light Core Initialization
# 🚀 إعداد الوحدة عند بدء التحميل وربطها بسجل العمليات

import logging
from django.utils import timezone
from django.conf import settings

# ============================================================
# 🧩 تعريف النسخة الرسمية لمركز الإعدادات
# ============================================================
SETTINGS_CENTER_VERSION = "7.7"
SETTINGS_CENTER_BUILD = "Glass Light Final"
SETTINGS_CENTER_RELEASE_DATE = "2025-11-07"

# ============================================================
# 🧠 تهيئة نظام التسجيل (Logging)
# ============================================================
logger = logging.getLogger("settings_center")
if not logger.handlers:
    handler = logging.FileHandler(
        getattr(settings, "SETTINGS_LOG_FILE", "logs/settings_center.log"),
        encoding="utf-8"
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

logger.info(f"🔹 Settings Center V{SETTINGS_CENTER_VERSION} ({SETTINGS_CENTER_BUILD}) initialized.")


# ============================================================
# 🧾 وظيفة مساعدة لتسجيل الأحداث في قاعدة البيانات
# ============================================================
def log_action(user, action):
    """
    🕓 تسجيل عملية داخل سجل الإعدادات.
    مثال:
        log_action(request.user, "تم تحديث الهوية البصرية")
    """
    try:
        from .models import SettingsLog
        SettingsLog.objects.create(
            action=action,
            changed_by=str(user),
            timestamp=timezone.now()
        )
        logger.info(f"{user} | {action}")
    except Exception as e:
        logger.error(f"⚠️ فشل تسجيل الحدث في SettingsLog: {e}")
