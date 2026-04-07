# ============================================================
# 📂 الملف: biotime_center/apps.py
# 🚀 تهيئة وحدة Biotime Center — الإصدار النهائي V7.1 (Migration Safe)
# ------------------------------------------------------------
# ✔ متوافق مع نظام Mham Cloud V2026
# ✔ يمنع circular imports أثناء migrations
# ✔ يدعم Signals + Services عند التشغيل الطبيعي
# ============================================================

from django.apps import AppConfig
import sys


class BiotimeCenterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "biotime_center"
    verbose_name = "Biotime Cloud Integration"

    # 🚀 تحميل خدمات الوحدة (Signals / Schedulers / Services)
    def ready(self):
        # ----------------------------------------------------
        # 🛡️ حماية أثناء أوامر migrations
        # تمنع تحميل أي imports ثقيلة تكسر StateApps
        # ----------------------------------------------------
        if any(cmd in sys.argv for cmd in ("migrate", "makemigrations", "showmigrations")):
            return

        # ----------------------------------------------------
        # 🔔 تحميل الإشارات (Signals)
        # ----------------------------------------------------
        try:
            import biotime_center.signals  # noqa
        except Exception:
            # لا نكسر الإقلاع — فقط نتجاوز
            pass

        # ----------------------------------------------------
        # 🔁 تحميل طبقة الخدمات (Services / Sync)
        # ----------------------------------------------------
        try:
            import biotime_center.sync_service  # noqa
        except Exception:
            # لا نكسر الإقلاع — فقط نتجاوز
            pass
