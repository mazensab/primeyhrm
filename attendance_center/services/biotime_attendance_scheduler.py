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
    🔄 Main pipeline (Multi-Tenant Safe):

        1) Loop active companies
        2) Sync Biotime Logs per company
        3) Link Logs → Attendance per company
        4) Persist per-company summary
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

        from company_manager.models import Company

        companies = Company.objects.filter(
            is_active=True,
            biotime_settings__isnull=False
        ).distinct()

        if not companies.exists():
            logger.info("ℹ️ No active companies found.")
            return

        # --------------------------------------------------------
        # 🔁 Process Each Company
        # --------------------------------------------------------
        for company in companies:

            logger.info(
                "🏢 Processing company ID=%s | %s",
                company.id,
                company.name if hasattr(company, "name") else ""
            )

            # ---------------------------
            # 1️⃣ Sync Logs
            # ---------------------------
            logs_result = sync_logs(company=company)

            if logs_result.get("status") != "success":
                logger.warning(
                    "⚠️ Logs sync failed for company %s: %s",
                    company.id,
                    logs_result.get("message"),
                )

                BiotimeSyncLog.objects.create(
                    company=company,
                    timestamp=timezone.now(),
                    devices_synced=0,
                    employees_synced=0,
                    logs_synced=0,
                    status="FAILED",
                    message=logs_result.get("message"),
                )
                continue

            # ---------------------------
            # 2️⃣ Link to Attendance
            # ---------------------------
            attendance_result = sync_biotime_logs_to_attendance(
                company=company
            )

            # ---------------------------
            # 3️⃣ Persist Company Summary
            # ---------------------------
            BiotimeSyncLog.objects.create(
                company=company,
                timestamp=timezone.now(),
                devices_synced=0,
                employees_synced=0,
                logs_synced=attendance_result.get("synced", 0),
                status="SUCCESS",
                message=(
                    f"Logs synced & linked successfully | "
                    f"new={logs_result.get('new')} | "
                    f"updated={logs_result.get('updated')} | "
                    f"attendance_synced={attendance_result.get('synced')}"
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

    finally:
        cache.delete(JOB_LOCK_KEY)


# ================================================================
# 🚀 Scheduler Bootstrap
# ================================================================
def start_biotime_attendance_scheduler():
    """
    Starts APScheduler safely (idempotent).
    """

    global scheduler

    # إذا كان scheduler يعمل بالفعل
    if scheduler.running:
        # تأكد أن الجوب غير موجود
        existing_job = scheduler.get_job("biotime_attendance_job")
        if existing_job:
            logger.info("⚠️ Biotime Attendance job already registered.")
            return

    logger.info("🔥 Initializing Biotime Attendance Scheduler…")

    try:
        if not scheduler.running:
            scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            run_biotime_attendance_pipeline,
            trigger="interval",
            minutes=10,
            id="biotime_attendance_job",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

        if not scheduler.running:
            scheduler.start()

        logger.info("🚀 Biotime Attendance Scheduler started successfully.")

    except Exception:
        logger.exception("❌ Failed to start Biotime Attendance Scheduler")
