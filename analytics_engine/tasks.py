# 📂 الملف: analytics_engine/tasks.py
# 🧠 مهام النظام المجدولة - Primey HR Cloud V3
# 🚀 يحتوي على المهام الذكية (التقرير اليومي + فحص النظام + تنظيف السجلات)

import logging
from django.core.management import call_command
from django_apscheduler.models import DjangoJobExecution
from django.contrib.auth import get_user_model
from django.utils import timezone
from analytics_engine.services.report_generator import AutoReportGenerator

# 🧩 Logger لتسجيل جميع العمليات في لوحة التحكم والسيرفر
logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================
# 📊 1️⃣ توليد التقرير الذكي اليومي (Daily Smart Report)
# ============================================================
def generate_daily_smart_report():
    """📈 توليد تقرير الأداء العام تلقائيًا كل يوم عند منتصف الليل"""
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            logger.warning("⚠️ لم يتم العثور على مستخدم إداري لتوليد التقرير اليومي.")
            print("⚠️ لم يتم العثور على مستخدم إداري لتوليد التقرير اليومي.")
            return

        AutoReportGenerator.generate_summary_report(created_by=admin_user)
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        logger.info(f"✅ تم توليد التقرير الذكي اليومي بنجاح ({timestamp}).")
        print(f"✅ تم توليد التقرير الذكي اليومي بنجاح ({timestamp}).")

    except Exception as e:
        logger.error(f"❌ فشل توليد التقرير الذكي اليومي: {e}")
        print(f"❌ فشل توليد التقرير الذكي اليومي: {e}")


# ============================================================
# 🩺 2️⃣ فحص النظام التلقائي (System Health Check)
# ============================================================
def run_health_check():
    """🩺 تنفيذ أمر فحص النظام primey_healthcheck يوميًا الساعة 01:00 صباحًا"""
    try:
        call_command("primey_healthcheck")
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        logger.info(f"🩺 تم تنفيذ فحص النظام بنجاح ({timestamp}).")
        print(f"🩺 تم تنفيذ فحص النظام بنجاح ({timestamp}).")
    except Exception as e:
        logger.error(f"❌ فشل تنفيذ فحص النظام: {e}")
        print(f"❌ فشل تنفيذ فحص النظام: {e}")


# ============================================================
# 🧹 3️⃣ تنظيف المهام القديمة أسبوعيًا (Cleanup Jobs)
# ============================================================
def cleanup_old_jobs():
    """🧹 تنظيف سجلات المهام القديمة أسبوعيًا من APScheduler"""
    try:
        DjangoJobExecution.objects.delete_old_job_executions(max_age=7 * 24 * 60 * 60)  # 7 أيام
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        logger.info(f"🧹 تم تنظيف سجلات المهام القديمة بنجاح ({timestamp}).")
        print(f"🧹 تم تنظيف سجلات المهام القديمة بنجاح ({timestamp}).")
    except Exception as e:
        logger.error(f"❌ فشل تنظيف سجلات المهام القديمة: {e}")
        print(f"❌ فشل تنظيف سجلات المهام القديمة: {e}")
