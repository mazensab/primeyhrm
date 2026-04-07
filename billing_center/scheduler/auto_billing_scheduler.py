# ============================================================
# ⏱️ Auto Billing Scheduler — S3-D
# Mham Cloud | Ultra Stable V2
# ============================================================
# ✔ Runs daily
# ✔ APScheduler based
# ✔ Sequential execution
# ✔ Idempotent safe
# ✔ No enforcement
# ✔ Clear execution summary
# ============================================================

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.utils import timezone
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler.util import close_old_connections

from billing_center.services.auto_invoice_generator import AutoInvoiceGenerator
from billing_center.services.billing_cycle_engine import BillingCycleEngine
from billing_center.services.subscription_state_updater import SubscriptionStateUpdater

logger = logging.getLogger(__name__)


# ============================================================
# Scheduler instance (Singleton)
# ============================================================
scheduler = BackgroundScheduler(timezone=timezone.get_current_timezone())


# ============================================================
# Helpers
# ============================================================
def _cleanup_old_job_executions(max_age_seconds: int = 7 * 24 * 60 * 60) -> int:
    """
    حذف سجلات تنفيذ APScheduler القديمة بشكل آمن.
    """
    try:
        deleted_count, _ = DjangoJobExecution.objects.delete_old_job_executions(max_age_seconds)
        return int(deleted_count or 0)
    except Exception:
        logger.exception("❌ فشل تنظيف سجلات APScheduler القديمة.")
        return 0


# ============================================================
# Main Job
# ============================================================
@close_old_connections
def run_daily_auto_billing():
    """
    ============================================================
    Daily Auto Billing Job
    ------------------------------------------------------------
    Execution order:
    1️⃣ BillingCycleEngine (evaluate)
    2️⃣ AutoInvoiceGenerator (create invoices)
    3️⃣ SubscriptionStateUpdater (expire)
    ============================================================
    """
    logger.info("🚀 بدء تشغيل مهمة الفوترة اليومية التلقائية.")

    result = {
        "success": True,
        "evaluated_count": 0,
        "created_invoices_count": 0,
        "expired_count": 0,
        "deleted_job_executions_count": 0,
    }

    try:
        # 1️⃣ Evaluate subscriptions
        evaluation_results = BillingCycleEngine().evaluate()
        result["evaluated_count"] = len(evaluation_results)

        # 2️⃣ Generate renewal invoices
        created_invoices = AutoInvoiceGenerator().run()
        result["created_invoices_count"] = len(created_invoices)

        # 3️⃣ Update subscription states
        state_changes = SubscriptionStateUpdater().run()
        result["expired_count"] = len(state_changes)

        # 4️⃣ Cleanup old scheduler execution logs
        result["deleted_job_executions_count"] = _cleanup_old_job_executions()

        logger.info(
            "✅ اكتملت مهمة الفوترة اليومية | evaluated=%s | invoices=%s | expired=%s | cleaned_logs=%s",
            result["evaluated_count"],
            result["created_invoices_count"],
            result["expired_count"],
            result["deleted_job_executions_count"],
        )
        return result

    except Exception:
        logger.exception("❌ فشل تنفيذ مهمة الفوترة اليومية التلقائية.")
        result["success"] = False
        return result


# ============================================================
# Setup Scheduler
# ============================================================
def start():
    """
    Register and start APScheduler jobs.
    """

    # Prevent duplicates
    if scheduler.running:
        logger.info("ℹ️ Auto Billing Scheduler يعمل بالفعل، تم تجاهل إعادة التشغيل.")
        return

    try:
        scheduler.add_jobstore(DjangoJobStore(), "default")
    except Exception:
        logger.exception("❌ فشل إضافة DjangoJobStore إلى Auto Billing Scheduler.")
        return

    scheduler.add_job(
        run_daily_auto_billing,
        trigger=CronTrigger(hour=2, minute=0),  # ⏰ 02:00 AM daily
        id="daily_auto_billing",
        max_instances=1,
        replace_existing=True,
    )

    scheduler.start()
    logger.info("✅ تم تشغيل Auto Billing Scheduler بنجاح.")