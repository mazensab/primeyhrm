# ============================================================
# 📂 Settings Center — URLs
# ⚙️ Version: V10.1 Ultra Pro — Unified & Clean (Stable)
# ============================================================

from django.urls import path
from . import views

app_name = "settings_center"

urlpatterns = [

    # ============================================================
    # 🏠 1) Settings Dashboard (UI)
    # ============================================================
    path(
        "",
        views.settings_dashboard,
        name="settings_dashboard",
    ),

    # ============================================================
    # 🟦 2) Unified AJAX Tabs Loader
    # مثال:
    # /settings/api/tabs/general/
    # ============================================================
    path(
        "api/tabs/<str:section>/",
        views.settings_tabs_api,
        name="settings_tabs_api",
    ),

    # ============================================================
    # 📘 3) Audit Log (Company Scope — AJAX)
    # ============================================================
    path(
        "api/audit-log/",
        views.settings_audit_log_api,
        name="settings_audit_log_api",
    ),

    # ============================================================
    # 💾 4) Unified Update API (Company Scope)
    # ============================================================
    path(
        "api/update/",
        views.settings_update_api,
        name="settings_update_api",
    ),

    # ============================================================
    # 🌐 5) System Settings — Global (READ ONLY)
    # يستخدم من:
    # - Next.js (SystemSettingsContext)
    # - GlobalSystemBanner
    # المسار النهائي:
    # /settings/api/system/settings/
    # ============================================================
    path(
        "api/system/settings/",
        views.system_settings_api,
        name="system_settings_api",
    ),

    # ============================================================
    # 🟦 6) System Audit Log — Super Admin (اختياري)
    # ============================================================
    path(
        "api/system/audit-log/",
        views.system_audit_log_api,
        name="system_audit_log_api",
    ),
]
