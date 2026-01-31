# ============================================================
# 📂 الملف: biotime_center/urls.py
# 🔗 روابط وحدة Biotime Cloud — الإصدار V9.0 (IClock Edition)
# ============================================================

from django.urls import path
from . import views

app_name = "biotime_center"

urlpatterns = [

    # ================================
    # 🧊 لوحات المراقبة
    # ================================
    path("dashboard/", views.biotime_glass_dashboard, name="dashboard"),
    path("glass-dashboard/", views.biotime_glass_dashboard, name="glass_dashboard"),

    # ================================
    # ⚙️ الإعدادات
    # ================================
    path("settings/", views.biotime_settings_view, name="biotime_settings_view"),

    # ================================
    # 🔐 اختبار تسجيل الدخول عبر JWT
    # ================================
    path("api/jwt/test-login/", views.jwt_test_login, name="jwt_test_login"),

    path("api/test-connection/", views.api_biotime_test_connection, name="api_biotime_test_connection"),
    path("api/save-settings/", views.api_biotime_save_settings, name="api_biotime_save_settings"),

  
    # ================================
    # 🟣 (المسار الجديد المطلوب) — Sync Logs JWT
    # ================================
    path("api/jwt/sync-logs/", views.api_sync_logs, name="jwt_sync_logs"),

    path("devices/<int:device_id>/", views.biotime_device_detail, name="biotime_device_detail"),
    path("api/device/live/<int:device_id>/", views.api_device_live, name="api_device_live"),

    # ================================
    # 💻 مزامنة الأجهزة
    # ================================
    path("api/sync-devices/", views.api_sync_devices, name="api_sync_devices"),
    path("api/device/sync/<int:device_id>/", views.api_device_sync, name="api_device_sync"),
    path("api/device/restart/<int:device_id>/", views.api_device_restart, name="api_device_restart"),
    path("api/device/pull-logs/<int:device_id>/", views.api_device_pull_logs, name="api_device_pull_logs"),

    # ================================
    # 👨‍💼 مزامنة الموظفين
    # ================================
    path("api/sync-employees/", views.api_sync_employees, name="api_sync_employees"),

    # ================================
    # 🕒 مزامنة السجلات
    # ================================
    path("api/sync-logs/", views.api_sync_logs, name="api_sync_logs"),

    # ================================
    # 🔄 المزامنة الشاملة Full Sync
    # ================================
    path("api/full-sync/", views.api_full_sync, name="api_full_sync"),

    # ================================
    # 💻 واجهة الأجهزة UI
    # ================================
    path("devices/", views.biotime_devices_view, name="devices"),

    # ================================
    # 🕒 واجهة السجلات UI
    # ================================
    path("logs/", views.biotime_logs_view, name="logs"),

    # ================================
    # 🧪 Debug
    # ================================
    path("api/debug/devices/", views.api_debug_devices, name="api_debug_devices"),

    # ================================
    # 🌐 حالة الاتصال
    # ================================
    path("status/", views.biotime_status_api, name="biotime_status_api"),
]
