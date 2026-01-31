# 📂 الملف: analytics_engine/cron.py
# ⏰ مهمة توليد التقرير الذكي التلقائي اليومي - Primey HR Cloud V3

from django.contrib.auth import get_user_model
from analytics_engine.services.report_generator import AutoReportGenerator

User = get_user_model()

def generate_daily_smart_report():
    """🕛 يتم تشغيلها تلقائيًا كل يوم لتوليد تقرير الأداء العام"""
    try:
        # ⚙️ اختيار المستخدم الإداري (أول مستخدم أو مسؤول النظام)
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print("⚠️ لم يتم العثور على مستخدم إداري لتوليد التقرير.")
            return

        # 🚀 تنفيذ المولد الذكي
        AutoReportGenerator.generate_summary_report(created_by=admin_user)
        print("✅ تم توليد التقرير الذكي اليومي بنجاح.")
    except Exception as e:
        print(f"❌ فشل توليد التقرير اليومي: {e}")
