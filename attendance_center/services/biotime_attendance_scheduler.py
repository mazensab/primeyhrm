# ================================================================
# 📂 Path: attendance_center/services/biotime_attendance_scheduler.py
# 🕒 Biotime → Attendance Auto Scheduler — V1 Ultra Stable
# ================================================================
# ✔ Uses official sync_service (JWT)
# ✔ Links logs to Attendance Engine
# ✔ Safe anti-duplicate execution
# ✔ Production ready
# ✔ Does NOT touch legacy scheduler.py
# ================================================================

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from biotime_center.sync_service import sync_logs
from attendance_center.services.sync_biotime_to_attendance import (
    sync_biotime_logs_to_attendance
)
from biotime_center.models import BiotimeSyncLog

logger = logging.getLogger(__name__)

# ================================================================
# 🧠 Scheduler Singleton
# ================================================================
scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)

# ================================================================
# 🔒 Runtime Locks
# ================================================================
JOB_LOCK_KEY = "scheduler:biotime_attendance:running"
JOB_LOCK_TTL = 60 * 30   # 30 minutes safety lock


# ================================================================
# 🧩 Core Job
# ================================================================
def run_biotime_attendance_pipeline():
    """
    🔄 Main pipeline:
        1) Sync Biotime Logs
        2) Link Logs → Attendance
        3) Store unified result
    """

    # ------------------------------------------------------------
    # 🔒 Prevent double execution
    # ------------------------------------------------------------
    if cache.get(JOB_LOCK_KEY):
        logger.warning("⏳ Biotime Attendance Job already running — skipped.")
        return

    cache.set(JOB_LOCK_KEY, True, JOB_LOCK_TTL)
    start_time = timezone.now()

    try:
        logger.info("🚀 Biotime Attendance Pipeline started")

        # ---------------------------
        # 1️⃣ Sync Logs
        # ---------------------------
        logs_result = sync_logs()

        if logs_result.get("status") != "success":
            raise RuntimeError(
                f"Logs sync failed: {logs_result.get('message')}"
            )

        # ---------------------------
        # 2️⃣ Link to Attendance
        # ---------------------------
        attendance_result = sync_biotime_logs_to_attendance()

        # ---------------------------
        # 3️⃣ Persist Sync Summary
        # ---------------------------
        BiotimeSyncLog.objects.create(
            timestamp=timezone.now(),
            devices_synced=0,
            employees_synced=0,
            logs_synced=attendance_result.get("synced", 0),
            status="SUCCESS",
            message=(
                f"Logs synced & linked successfully | "
                f"synced={attendance_result.get('synced')} | "
                f"skipped={attendance_result.get('skipped')}"
            ),
        )

        elapsed_ms = int(
            (timezone.now() - start_time).total_seconds() * 1000
        )

        logger.info(
            "✅ Biotime Attendance Pipeline completed | %sms",
            elapsed_ms
        )

    except Exception as exc:
        logger.exception("❌ Biotime Attendance Pipeline failed")

        BiotimeSyncLog.objects.create(
            timestamp=timezone.now(),
            devices_synced=0,
            employees_synced=0,
            logs_synced=0,
            status="FAILED",
            message=str(exc),
        )

    finally:
        cache.delete(JOB_LOCK_KEY)


# ================================================================
# 🚀 Scheduler Bootstrap
# ================================================================
def start_biotime_attendance_scheduler():
    """
    Starts APScheduler safely (idempotent).
    """

    if scheduler.running:
        logger.info("⚠️ Biotime Scheduler already running.")
        return

    logger.info("🔥 Starting Biotime Attendance Scheduler…")

    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        run_biotime_attendance_pipeline,
        trigger="interval",
        minutes=30,                 # 🔁 قابل للتعديل لاحقًا
        id="biotime_attendance_job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    try:
        scheduler.start()
        logger.info("🚀 Biotime Attendance Scheduler started successfully.")
    except Exception:
        logger.exception("❌ Failed to start Biotime Attendance Scheduler")
