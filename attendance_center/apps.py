# ================================================================
# 🕒 Attendance Center — App Config
# 🔥 Auto Sync Scheduler Engine — SAFE BOOT LOADER
# Phase H.7.1 — Production Safe
# ================================================================

from django.apps import AppConfig
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


class AttendanceCenterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "attendance_center"
    verbose_name = "Attendance Center"

    def ready(self):
        """
        🛡️ SAFE APScheduler Boot
        - يعمل مرة واحدة فقط
        - لا DB Access أثناء init
        - لا Circular Imports
        - متوافق مع runserver / autoreload
        """

        # ------------------------------------------------------------
        # 1️⃣ Global Feature Flag
        # ------------------------------------------------------------
        if not getattr(settings, "SCHEDULER_AUTOSTART", False):
            logger.info(
                "⏸️ Attendance APScheduler disabled "
                "(SCHEDULER_AUTOSTART=False)"
            )
            return

        # ------------------------------------------------------------
        # 2️⃣ Prevent double-run (runserver / autoreload)
        # ------------------------------------------------------------
        if os.environ.get("RUN_MAIN") != "true":
            return

        # ------------------------------------------------------------
        # 3️⃣ Lazy Import (NO module-level import)
        # ------------------------------------------------------------
        try:
            from attendance_center.scheduler import start_auto_sync_scheduler
        except Exception as exc:
            logger.error(
                "❌ Failed to import Attendance Scheduler engine",
                exc_info=exc,
            )
            return

        # ------------------------------------------------------------
        # 4️⃣ Start Scheduler (SAFE)
        # ------------------------------------------------------------
        try:
            start_auto_sync_scheduler()
            logger.info("✅ Attendance APScheduler started successfully")
        except Exception as exc:
            logger.exception(
                "❌ Attendance APScheduler failed to start",
                exc_info=exc,
            )
