from django.urls import path
from . import views

app_name = "system_log"

# ================================================================
# 🌐 System Log URLs — V3 (Mham Cloud)
# ================================================================

urlpatterns = [
    # ------------------------------------------------------------
    # 📊 Dashboard
    # ------------------------------------------------------------
    path(
        "dashboard/<int:company_id>/",
        views.log_dashboard,
        name="log_dashboard"
    ),

    # ------------------------------------------------------------
    # 📄 Log List
    # ------------------------------------------------------------
    path(
        "list/<int:company_id>/",
        views.log_list,
        name="log_list"
    ),

    # ------------------------------------------------------------
    # 🔍 Detail
    # ------------------------------------------------------------
    path(
        "detail/<int:log_id>/",
        views.log_detail,
        name="log_detail"
    ),

    # ------------------------------------------------------------
    # 🚀 V2 — AJAX Filter API
    # ------------------------------------------------------------
    path(
        "api/filter/<int:company_id>/",
        views.api_filter_logs,
        name="api_filter_logs"
    ),

    # ------------------------------------------------------------
    # 📤 V3 — Export Excel
    # ------------------------------------------------------------
    path(
        "export/excel/<int:company_id>/",
        views.export_logs_excel,
        name="export_logs_excel"
    ),

    # ------------------------------------------------------------
    # 📄 V3 — Export PDF
    # ------------------------------------------------------------
    path(
        "export/pdf/<int:company_id>/",
        views.export_logs_pdf,
        name="export_logs_pdf"
    ),

    # ------------------------------------------------------------
    # 🗑️ V3 — Clear Logs
    # ------------------------------------------------------------
    path(
        "clear/<int:company_id>/",
        views.clear_logs,
        name="clear_logs"
    ),

    # ------------------------------------------------------------
    # 🛰️ V4 — Live Streaming Logs Page
    # ------------------------------------------------------------
    path(
        "live/<int:company_id>/",
        views.log_live_view,
        name="log_live"
    ),

]
