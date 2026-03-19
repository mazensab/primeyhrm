# ================================================================
# 🕒 Attendance Center — App Config
# 🔥 Scheduler Boot Loader (Stable Local + Production)
# Version: H.9 — Clean & Deterministic
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

    if not getattr(settings, "SCHEDULER_AUTOSTART", False):
        logger.info("⏸️ Attendance Scheduler disabled")
        return

    try:
        from attendance_center.services.biotime_attendance_scheduler import (
            start_biotime_attendance_scheduler
        )

        start_biotime_attendance_scheduler()

        logger.info("🚀 Attendance Scheduler started successfully")

    except Exception as exc:
        logger.exception(
            "❌ Attendance Scheduler failed to start",
            exc_info=exc,
        )

