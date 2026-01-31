# ============================================================
# 📂 analytics_engine/urls.py — V4 Ultra Fixed
# ============================================================

from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = "analytics_engine"

urlpatterns = [

    # 📊 لوحة التحليلات العامة
    path("dashboard/", views.analytics_dashboard, name="analytics_dashboard"),

    # 🏠 إعادة توجيه الجذر → لوحة التقارير
    path("", lambda request: redirect("analytics_engine:reports_dashboard"), name="analytics_root"),

    # 📊 لوحة التقارير والتحليلات
    path("reports/", views.reports_dashboard, name="reports_dashboard"),

    # ⚙️ توليد تقرير ذكي يدويًا
    path("reports/generate-now/", views.generate_report_now, name="generate_report_now"),

    # 📄 إنشاء ملف PDF رسمي
    path("reports/pdf/<int:report_id>/", views.generate_report_pdf, name="generate_report_pdf"),

    # 🤖 التحليلات الذكية
    path("smart/", views.smart_analytics_dashboard, name="smart_analytics_dashboard"),

    # 🧪 اختبار الوحدة
    path("test/", views.test_analytics_engine, name="test_analytics_engine"),
]
