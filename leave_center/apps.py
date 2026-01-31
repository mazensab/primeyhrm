# ============================================================
# 📂 leave_center/apps.py — LeaveCenterConfig V3.2 Ultra Safe + Signals
# Primey HR Cloud
# ============================================================
# ✔ Signals loaded ALWAYS (shell / migrate safe)
# ✔ APScheduler guarded from admin commands
# ✔ No double bootstrap
# ✔ Clean logging
# ============================================================

from django.apps import AppConfig
from django.conf import settings
import sys
import logging


logger = logging.getLogger("leave.apps")


class LeaveCenterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "leave_center"
    label = "leave_center"
    verbose_name = "Leave Center"

    # حماية من التحميل المكرر
    _bootstrapped = False

    def ready(self):
        """
        🚀 Leave Center Bootstrap

        المهام:
        1️⃣ تحميل signals دائمًا (حتى في shell والمهاجرشن)
        2️⃣ تشغيل APScheduler بأمان شديد دون كسر Django
        3️⃣ منع التهيئة المكررة داخل نفس العملية
        """

        # ============================================================
        # 🛡️ Prevent Double Initialization
        # ============================================================
        if self.__class__._bootstrapped:
            return

        self.__class__._bootstrapped = True

        # ============================================================
        # 🔔 Load Signals (ALWAYS)
        # ============================================================
        try:
            from . import signals  # noqa: F401
            logger.info("✔ Leave Center Signals Loaded Successfully")
        except Exception as e:
            logger.exception(f"[LeaveCenter Signals Error]: {e}")

        # ============================================================
        # ⛔ Block Scheduler During Admin Commands
        # ============================================================
        if any(cmd in sys.argv for cmd in (
            "migrate",
            "makemigrations",
            "collectstatic",
            "shell",
            "createsuperuser",
        )):
            logger.info("⛔ Leave Center Scheduler skipped (admin command detected)")
            return

        # ============================================================
        # ⛔ Scheduler Disabled by Settings
        # ============================================================
        if not getattr(settings, "SCHEDULER_AUTOSTART", False):
            logger.info("⛔ Leave Center Scheduler disabled by settings")
            return

        # ============================================================
        # 🕒 Start Scheduler Safely
        # ============================================================
        try:
            from .jobs import start_scheduler
            start_scheduler()
            logger.info("✔ APScheduler Started Successfully (Leave Center)")
        except Exception as e:
            logger.exception(f"[LeaveCenter Scheduler Error]: {e}")
