# ============================================================
# 📊 Analytics Engine — APScheduler Bootstrap (SAFE MODE)
# Primey HR Cloud
# ------------------------------------------------------------
# ✔ لا يعمل أثناء: check / migrate / shell
# ✔ يعمل فقط عند تشغيل السيرفر فعليًا
# ✔ مفعل عبر ENV: ENABLE_ANALYTICS_SCHEDULER=1
# ✔ متوافق Windows / Linux
# ============================================================

from django.apps import AppConfig
import os
import sys
import threading
import time
import logging


class AnalyticsEngineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analytics_engine"
    verbose_name = "📊 محرك التحليلات الذكية"

    def ready(self):
        """
        🚦 تشغيل APScheduler فقط عند:
        - تشغيل السيرفر (runserver / gunicorn)
        - تفعيل المتغير البيئي ENABLE_ANALYTICS_SCHEDULER
        """

        # --------------------------------------------------
        # 🛑 1) لا تشغل Scheduler أثناء أوامر Django الإدارية
        # --------------------------------------------------
        blocked_commands = {
            "check",
            "makemigrations",
            "migrate",
            "shell",
            "createsuperuser",
            "collectstatic",
        }

        if any(cmd in sys.argv for cmd in blocked_commands):
            return

        # --------------------------------------------------
        # 🔐 2) تحكم صريح عبر Environment Variable
        # --------------------------------------------------
        if os.getenv("ENABLE_ANALYTICS_SCHEDULER") != "1":
            return

        # --------------------------------------------------
        # 🧵 3) تشغيل مؤجل داخل Thread آمن
        # --------------------------------------------------
        def start_scheduler_delayed():
            time.sleep(3)  # انتظار استقرار Django

            try:
                from django.conf import settings
                from apscheduler.schedulers.background import BackgroundScheduler
                from django_apscheduler.jobstores import DjangoJobStore, register_events
                from analytics_engine import tasks

                logger = logging.getLogger(__name__)

                scheduler = BackgroundScheduler(
                    timezone=settings.TIME_ZONE
                )

                # 🗄️ JobStore (Django ORM)
                scheduler.add_jobstore(DjangoJobStore(), "default")

                # --------------------------------------------------
                # 📈 تقرير الأداء اليومي
                # --------------------------------------------------
                scheduler.add_job(
                    tasks.generate_daily_smart_report,
                    trigger="cron",
                    hour=0,
                    minute=0,
                    id="analytics_daily_report",
                    replace_existing=True,
                )

                # --------------------------------------------------
                # 🩺 فحص صحة النظام
                # --------------------------------------------------
                scheduler.add_job(
                    tasks.run_health_check,
                    trigger="cron",
                    hour=1,
                    minute=0,
                    id="analytics_health_check",
                    replace_existing=True,
                )

                # --------------------------------------------------
                # 🧹 تنظيف أسبوعي
                # --------------------------------------------------
                scheduler.add_job(
                    tasks.cleanup_old_jobs,
                    trigger="interval",
                    days=7,
                    id="analytics_cleanup",
                    replace_existing=True,
                )

                register_events(scheduler)
                scheduler.start()

                logger.info("✅ APScheduler (Analytics Engine) started successfully.")
                print("✅ APScheduler يعمل الآن (Analytics Engine).")

            except Exception as e:
                print(f"❌ فشل تشغيل APScheduler (Analytics): {e}")

        threading.Thread(
            target=start_scheduler_delayed,
            daemon=True
        ).start()
