# 📂 الملف: primey_hrm/celery.py
# 🧠 نظام الجدولة التلقائية للتقارير (Celery + Beat)

import os
from celery import Celery
from celery.schedules import crontab

# 🔧 تعيين إعدادات Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primey_hrm.settings")

# 🧩 إنشاء تطبيق Celery
app = Celery("primey_hrm")

# تحميل الإعدادات من Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# تحميل المهام من جميع التطبيقات
app.autodiscover_tasks()

# 🕒 جدولة المهمة اليومية
app.conf.beat_schedule = {
    "generate-daily-report": {
        "task": "scheduler.tasks.auto_generate_reports",
        "schedule": crontab(hour=0, minute=0),  # كل يوم عند منتصف الليل
    },
}
