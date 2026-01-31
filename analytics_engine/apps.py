# 📂 الملف: analytics_engine/apps.py
# ⚙️ تهيئة APScheduler بعد اكتمال تحميل Django بالكامل
# 🚀 يدير الجدولة الذكية لتقارير الأداء والفحص الذاتي للنظام
# ✅ متوافق مع Windows وLinux بدون أي أخطاء AppRegistryNotReady

from django.apps import AppConfig
import threading
import time
import logging


class AnalyticsEngineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analytics_engine"
    verbose_name = "📊 محرك التحليلات الذكية"

    def ready(self):
        """🚀 تشغيل الجدولة الذكية بعد اكتمال تحميل جميع التطبيقات"""
        from django.conf import settings

        def start_scheduler_delayed():
            """⏳ تأخير بسيط لتفادي خطأ AppRegistryNotReady"""
            time.sleep(3)  # الانتظار حتى اكتمال تحميل كل التطبيقات
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                from django_apscheduler.jobstores import DjangoJobStore
                from django_apscheduler.jobstores import register_events
                from analytics_engine import tasks

                logger = logging.getLogger(__name__)

                # 🕒 إنشاء مجدول في الخلفية
                scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)

                # 🗄️ إضافة مخزن وظائف Django
                scheduler.add_jobstore(DjangoJobStore(), "default")

                # =======================================================
                # 🧠 المهمة 1️⃣ - توليد التقرير الذكي اليومي
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
                # 🩺 المهمة 2️⃣ - فحص النظام الذكي (HealthCheck)
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
                # 🧹 المهمة 3️⃣ - تنظيف الوظائف القديمة أسبوعيًا
                # =======================================================
                scheduler.add_job(
                    tasks.cleanup_old_jobs,
                    trigger="interval",
                    days=7,
                    id="cleanup_old_jobs",
                    replace_existing=True,
                )

                # تسجيل الأحداث
                register_events(scheduler)

                # 🟢 بدء المجدول
                scheduler.start()

                logger.info("✅ APScheduler بدأ بنجاح مع مهام التقارير والفحص والتنظيف.")
                print("✅ APScheduler يعمل الآن لتوليد التقارير والفحص الذكي يوميًا تلقائيًا.")

            except Exception as e:
                print(f"❌ فشل تشغيل APScheduler: {e}")

        # 🧵 تشغيل المجدول في خيط مستقل لتجنب مشاكل التحميل المبكر
        threading.Thread(target=start_scheduler_delayed, daemon=True).start()
