# ================================================================
# 📂 control_center/urls.py — V13 Ultra Pro (API ONLY)
# ---------------------------------------------------------------
# ❌ HTML Dashboards DISABLED (410 Gone)
# ✅ Routes preserved to avoid breaking old links
# ✅ Django = API + Admin ONLY
# ================================================================

from django.urls import path
from . import views

# ================================================================
# 🚫 Disabled Dashboards (Preserved Routes)
# ================================================================

urlpatterns = [

    # 🔵 Super Admin Dashboard (HTML REMOVED)
    path(
        "system/dashboard/",
        views.system_dashboard,
        name="system_dashboard_disabled"
    ),

    # 🟢 System Owner Dashboard (HTML REMOVED)
    path(
        "dashboard/system-owner/",
        views.dashboard_system_owner,
        name="dashboard_system_owner_disabled"
    ),

    # ============================================================
    # 🔌 System Health APIs (ACTIVE)
    # ============================================================

    # AJAX — Health Snapshot
    path(
        "system-health/",
        views.system_health_api,
        name="system_health_api"
    ),

    # API (Backup Route) — Prevent JS 404
    path(
        "api/system-health/",
        views.system_health_api,
        name="system_health_api_alt"
    ),
]
