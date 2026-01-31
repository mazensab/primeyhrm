# ===============================================================
# 📂 employee_center/apps.py
# 🧭 Employee Center AppConfig — Signals Loader (FINAL)
# Primey HR Cloud
# ===============================================================

from django.apps import AppConfig


class EmployeeCenterConfig(AppConfig):
    """
    ==========================================================
    🧭 Employee Center Configuration
    ==========================================================
    ✔ Loads signals safely
    ✔ Prevents circular imports
    ✔ Production-ready
    ==========================================================
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "employee_center"
    verbose_name = "Employee Center"

    def ready(self):
        """
        ------------------------------------------------------
        🔔 Load Signals (AUTO USER CREATION)
        ------------------------------------------------------
        """
        try:
            import employee_center.signals  # noqa: F401
        except Exception as e:
            # لا نكسر التشغيل — نسجل فقط
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Failed to load employee_center.signals: {e}")
