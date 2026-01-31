# ============================================================
# ⏱️ Auto Billing Scheduler — S3-D
# Primey HR Cloud | Ultra Stable V1
# ============================================================
# ✔ Runs daily
# ✔ APScheduler based
# ✔ Sequential execution
# ✔ Idempotent safe
# ✔ No enforcement
# ============================================================

from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler.util import close_old_connections

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from django.utils import timezone

from billing_center.services.billing_cycle_engine import BillingCycleEngine
from billing_center.services.auto_invoice_generator import AutoInvoiceGenerator
from billing_center.services.subscription_state_updater import SubscriptionStateUpdater


# ============================================================
# Scheduler instance (Singleton)
# ============================================================
scheduler = BackgroundScheduler(timezone=timezone.get_current_timezone())


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

    # 1️⃣ Evaluate subscriptions
    BillingCycleEngine().evaluate()

    # 2️⃣ Generate renewal invoices
    AutoInvoiceGenerator().run()

    # 3️⃣ Update subscription states
    SubscriptionStateUpdater().run()


# ============================================================
# Setup Scheduler
# ============================================================
def start():
    """
    Register and start APScheduler jobs.
    """

    # Prevent duplicates
    if scheduler.running:
        return

    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        run_daily_auto_billing,
        trigger=CronTrigger(hour=2, minute=0),  # ⏰ 02:00 AM daily
        id="daily_auto_billing",
        max_instances=1,
        replace_existing=True,
    )

    scheduler.start()
