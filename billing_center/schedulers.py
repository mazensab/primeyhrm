# ===============================================================
# ⏰ Billing Scheduler
# ===============================================================

from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: call_command("renew_subscriptions"),
        trigger="cron",
        hour=1,
        minute=0,
    )
    scheduler.start()
