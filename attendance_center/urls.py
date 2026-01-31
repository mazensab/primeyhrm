# ============================================================
# 📂 Attendance Center — URLs
# 🧭 Attendance Center — V15 Ultra Pro (Final Fixed)
# ------------------------------------------------------------
#   - Attendance Records
#   - Dashboard
#   - Analytics
#   - Settings
#   - Devices
#   - Policies V3 Ultra Pro
#   - Printing Engine Integration
# ============================================================

from django.urls import path
from . import views

app_name = "attendance_center"

urlpatterns = [

    # ------------------------------------------------------------
    # 🏠 Smart Redirect → قائمة الحضور
    # ------------------------------------------------------------
    path("", views.attendance_list, name="attendance_list"),
    path("records/", views.attendance_list, name="attendance_records"),

    # ------------------------------------------------------------
    # 📊 Attendance Dashboard
    # ------------------------------------------------------------
    path("dashboard/", views.attendance_dashboard, name="attendance_dashboard"),

    # ------------------------------------------------------------
    # 👤 Employee Detailed Attendance
    # ------------------------------------------------------------
    path("employee/<int:employee_id>/", views.attendance_detail, name="attendance_detail"),

    # ------------------------------------------------------------
    # 🔄 Primary Sync System
    # ------------------------------------------------------------
    path("sync/", views.attendance_sync, name="attendance_sync"),
    path("api/sync/", views.attendance_sync, name="api_attendance_sync"),

    # ------------------------------------------------------------
    # ⚡ Live Sync Endpoint
    # ------------------------------------------------------------
    path("api/live-sync/", views.live_sync_biotime, name="live_sync_biotime"),

    # ------------------------------------------------------------
    # 📈 Analytics
    # ------------------------------------------------------------
    path("analytics/", views.attendance_analytics, name="attendance_analytics"),
    path("analytics/filter/", views.attendance_filter, name="attendance_filter"),

    # ============================================================
    # ⚙️ Attendance Settings Center — V13 Ultra Pro
    # ============================================================
    path("settings/", views.attendance_settings, name="attendance_settings"),
    path("settings/edit/", views.attendance_settings_edit, name="attendance_settings_edit"),
    path("settings/test-connection/", views.attendance_settings_connection_test, name="attendance_settings_connection_test"),
    path("api/settings/test-connection/", views.test_biotime_connection, name="api_test_biotime_connection"),
    path("settings/devices/", views.attendance_settings_devices, name="attendance_settings_devices"),
    path("api/settings/devices/sync/", views.sync_attendance_devices, name="sync_attendance_devices"),

    # ==============================
    # 📡 Dashboard API V15 Ultra Pro
    # ==============================
    path("api/dashboard/<int:company_id>/", views.attendance_dashboard_api, name="attendance_dashboard_api"),

    # ============================================================
    # 📘 Attendance Policies V3 Ultra Pro
    # ============================================================

    # 📋 قائمة السياسات
    path("policies/", views.attendance_policies_list, name="attendance_policies_list"),

    # ➕ إضافة سياسة
    path("policies/add/", views.attendance_policy_add, name="attendance_policy_add"),

    # ✏ تعديل سياسة
    path("policies/<int:policy_id>/edit/", views.attendance_policy_edit, name="attendance_policy_edit"),

    # 👥 ربط موظفين بالسياسة
    path("policies/<int:policy_id>/assign/", views.attendance_policy_assign, name="attendance_policy_assign"),

    # 🎯 تجاوز سياسة لموظف محدد
    path("policies/<int:policy_id>/override/", views.attendance_employee_override, name="attendance_employee_override"),

    # ============================================================
    # 📡 Unified API — Attendance Policies
    # ============================================================
    path("api/policies/", views.attendance_policies_api, name="attendance_policies_api"),

    # ============================================================
    # 📤 Export Engine — CSV + Excel + PDF
    # ============================================================
    path("policies/export/csv/", views.attendance_policies_export_csv, name="attendance_policies_export_csv"),
    path("policies/export/excel/", views.attendance_policies_export_excel, name="attendance_policies_export_excel"),
    path("policies/export/pdf/", views.attendance_policies_export_pdf, name="attendance_policies_export_pdf"),

    # ============================================================
    # 🖨 Printing Engine — Attendance Reports
    # ============================================================

    # 1️⃣ Monthly Company Report
    path("print/<int:company_id>/monthly/", views.attendance_print_monthly, name="attendance_print_monthly"),

    # 2️⃣ Range Report (start, end via GET)
    path("print/<int:company_id>/range/", views.attendance_print_range, name="attendance_print_range"),

    # 3️⃣ Employee Detailed Report
    path("print/employee/<int:employee_id>/", views.attendance_print_employee, name="attendance_print_employee"),
]

# ============================================================
# التوافق الرسمي:
#   - Biotime V4.8 🔗
#   - Employee Center V13.x 👥
#   - Payroll Center V7.2 💰
#   - Attendance Policies V3 Ultra Pro 🧭
# ============================================================
