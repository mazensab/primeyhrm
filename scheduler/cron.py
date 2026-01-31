# 📂 الملف: scheduler/cron.py
# 🕒 مهمة مجدولة لتوليد التقارير اليومية تلقائيًا

from django.utils.timezone import now
from analytics_engine.services.report_generator import AutoReportGenerator
from notification_center.models import Notification
from billing_center.models import AccountProfile


def auto_generate_reports():
    """🔄 يتم تنفيذها يوميًا لتوليد تقرير جديد وإشعار المستخدمين"""
    try:
        # 🧠 توليد التقرير
        report = AutoReportGenerator.generate_summary_report()

        # 📣 إرسال إشعارات للمستخدمين
        users = AccountProfile.objects.all()
        for user in users:
            Notification.objects.create(
                user=user,
                title="📊 تقرير جديد متاح",
                message=f"تم إنشاء تقرير تحليلي جديد بتاريخ {now().strftime('%Y-%m-%d %H:%M')}.",
                notification_type="report"
            )

        print(f"✅ [{now()}] تم توليد التقرير اليومي بنجاح ({report.title})")

    except Exception as e:
        print(f"❌ [{now()}] فشل في إنشاء التقرير التلقائي: {e}")
