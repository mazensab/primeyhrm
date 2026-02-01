# 📂 الملف: analytics_engine/apps.py
# ⚙️ تهيئة APScheduler بعد اكتمال تحميل Django بالكامل
# 🚀 يدير الجدولة الذكية لتقارير الأداء والفحص الذاتي للنظام
# 🔒 لا يعمل إلا عند تفعيل ENABLE_ANALYTICS_SCHEDULER=1
# ✅ متوافق مع Windows و Linux
# ✅ آمن مع manage.py check / migrate / shell / gunicorn

from django.apps import AppConfig
import threading
import time
import logging
import os


class AnalyticsEngineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analytics_engine"
    verbose_name = "📊 محرك التحليلات الذكية"

    def ready(self):
        """
        🚀 تشغيل الجدولة الذكية بعد اكتمال تحميل جميع التطبيقات
        🔒 محمي بمتغير بيئة لتفادي التشغيل غير المقصود
        """

        # ============================================================
        # 🔒 Guard: لا تشغّل Scheduler إلا إذا تم تفعيله صراحة
        # ============================================================
        if os.environ.get("ENABLE_ANALYTICS_SCHEDULER") != "1":
            return

        from django.conf import settings

        def start_scheduler_delayed():
            """
            ⏳ تأخير بسيط لتفادي AppRegistryNotReady
            🧵 يعمل في Thread مستقل وآمن
            """
            time.sleep(3)

            logger = logging.getLogger(__name__)

            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                from django_apscheduler.jobstores import DjangoJobStore
                from django_apscheduler.jobstores import register_events
                from analytics_engine import tasks

                # 🕒 إنشاء المجدول
                scheduler = BackgroundScheduler(
                    timezone=settings.TIME_ZONE
                )

                # 🗄️ Job Store (Django)
                scheduler.add_jobstore(
                    DjangoJobStore(),
                    "default"
                )

                # =======================================================
                # 🧠 المهمة 1️⃣ - التقرير الذكي اليومي
                # =======================================================
                scheduler.add_job(
                    tasks.generate_daily_smart_report,
                    trigger="cron",
                    hour=0,
                    minute=0,
                    id="daily_smart_report",
                    replace_existing=True,
                )

                # =======================================================
                # 🩺 المهمة 2️⃣ - الفحص الذكي للنظام
                # =======================================================
                scheduler.add_job(
                    tasks.run_health_check,
                    trigger="cron",
                    hour=1,
                    minute=0,
                    id="daily_health_check",
                    replace_existing=True,
                )

                # =======================================================
                # 🧹 المهمة 3️⃣ - تنظيف السجلات أسبوعيًا
                # =======================================================
                scheduler.add_job(
                    tasks.cleanup_old_jobs,
                    trigger="interval",
                    days=7,
                    id="cleanup_old_jobs",
                    replace_existing=True,
                )

                # 🧾 تسجيل أحداث APScheduler
                register_events(scheduler)

                # ▶️ بدء التشغيل
                scheduler.start()

                logger.info(
                    "✅ APScheduler بدأ بنجاح (Analytics Engine) — ENV Guard Enabled"
                )
                print(
                    "✅ APScheduler يعمل الآن لتقارير الأداء والفحص الذكي (Analytics Engine)."
                )

            except Exception as e:
                logger.exception("❌ فشل تشغيل APScheduler (Analytics Engine)")
                print(f"❌ فشل تشغيل APScheduler (Analytics Engine): {e}")

        # 🧵 تشغيل المجدول في Thread مستقل
        threading.Thread(
            target=start_scheduler_delayed,
            daemon=True
        ).start()
