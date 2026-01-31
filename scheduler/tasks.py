# 📂 الملف: scheduler/tasks.py
# ⚡ مهمة توليد التقارير اليومية التلقائية باستخدام Celery

from celery import shared_task
from django.utils.timezone import now
from analytics_engine.services.report_generator import AutoReportGenerator
from notification_center.models import Notification
from billing_center.models import AccountProfile


@shared_task
def auto_generate_reports():
    """🕒 مهمة يومية لتوليد تقرير جديد وإشعار المستخدمين"""
    try:
        report = AutoReportGenerator.generate_summary_report()

        users = AccountProfile.objects.all()
        for user in users:
            Notification.objects.create(
                user=user,
                title="📊 تقرير جديد متاح",
                message=f"تم إنشاء تقرير تحليلي جديد بتاريخ {now().strftime('%Y-%m-%d %H:%M')}.",
                notification_type="report",
            )

        print(f"✅ [{now()}] تم توليد التقرير اليومي ({report.title})")

    except Exception as e:
        print(f"❌ [{now()}] فشل في توليد التقرير التلقائي: {e}")
