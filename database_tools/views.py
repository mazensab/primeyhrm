# 📂 الملف: database_tools/views.py
# 🧭 واجهة إدارة قاعدة البيانات (نسخ احتياطي وتجريبي)
# 🚀 الإصدار V3.71 — دعم التحميل المباشر للنسخة الاحتياطية

from django.shortcuts import render
from django.http import JsonResponse, FileResponse, Http404
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
import os
import time

# ✅ السماح للمشرف فقط
def superuser_required(user):
    return user.is_superuser


@login_required
@user_passes_test(superuser_required)
def database_dashboard(request):
    """📊 صفحة إدارة قاعدة البيانات"""
    db_info = settings.DATABASES['default']
    context = {
        "db_name": db_info['NAME'],
        "db_user": db_info['USER'],
        "db_host": db_info['HOST'],
        "db_engine": db_info['ENGINE'],
        "db_port": db_info['PORT'],
    }
    return render(request, "database_tools/database_dashboard.html", context)


@login_required
@user_passes_test(superuser_required)
def create_backup_ajax(request):
    """📦 إنشاء نسخة احتياطية (محاكاة فعلية + تحميل مباشر)"""
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql"
    backup_dir = os.path.join(settings.BASE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    fake_path = os.path.join(backup_dir, filename)
    with open(fake_path, "w", encoding="utf-8") as f:
        f.write("-- 🔒 Mham Cloud Backup (Simulated)\n")
        f.write(f"-- Database: {settings.DATABASES['default']['NAME']}\n")
        f.write(f"-- Created: {timezone.now()}\n")
        f.write("-- Content: [Simulated dump data]\n")

    time.sleep(1.5)  # محاكاة وقت النسخ
    return JsonResponse({
        "status": "success",
        "message": f"✅ تم إنشاء النسخة الاحتياطية بنجاح: {filename}",
        "filename": filename,
        "download_url": f"/database-tools/download/{filename}",
        "time": timezone.now().strftime("%Y-%m-%d %H:%M"),
    })


@login_required
@user_passes_test(superuser_required)
def download_backup(request, filename):
    """⬇️ تحميل النسخة الاحتياطية"""
    backup_dir = os.path.join(settings.BASE_DIR, "backups")
    file_path = os.path.join(backup_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), as_attachment=True, filename=filename)
    raise Http404("⚠️ النسخة غير موجودة.")
