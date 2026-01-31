# 📂 الملف: database_tools/urls.py
# 🧭 نظام المسارات - وحدة إدارة قاعدة البيانات
# 🚀 الإصدار V3.71 — دعم التحميل المباشر للنسخ الاحتياطية

from django.urls import path
from . import views

app_name = "database_tools"

urlpatterns = [
    path("", views.database_dashboard, name="database_dashboard"),
    path("backup/", views.create_backup_ajax, name="create_backup_ajax"),
    path("download/<str:filename>/", views.download_backup, name="download_backup"),
]
