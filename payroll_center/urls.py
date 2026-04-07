# ============================================================
# 📂 الملف: payroll_center/urls.py — V12.7 FINAL STABLE
# Mham Cloud | Payroll Module Routing
# ============================================================

from django.urls import path
from . import views

app_name = "payroll_center"

urlpatterns = [

    # ============================================================
    # 📊 DASHBOARD & READ
    # ============================================================

    # 🧾 لوحة الرواتب
    path(
        "",
        views.payroll_dashboard,
        name="payroll_dashboard"
    ),

    # 🧾 قائمة الرواتب العامة
    path(
        "list/",
        views.payroll_list,
        name="payroll_list"
    ),

    # 👤 تفاصيل راتب فردي
    path(
        "detail/<int:pk>/",
        views.payroll_detail,
        name="payroll_detail"
    ),

    # 🧠 Attendance ↔ Payroll Analysis
    path(
        "attendance-analysis/",
        views.payroll_attendance_analysis,
        name="payroll_attendance_analysis"
    ),

    # ⚖️ فحص الالتزام
    path(
        "compliance-check/",
        views.payroll_compliance_check,
        name="payroll_compliance_check"
    ),

    # ============================================================
    # 🧾 PAYROLL RUNS — READ
    # ============================================================

    # 📋 قائمة دورات الرواتب
    path(
        "runs/",
        views.payroll_run_list,
        name="payroll_run_list"
    ),

    # 📄 تفاصيل دورة رواتب
    path(
        "runs/<int:pk>/",
        views.payroll_run_detail,
        name="payroll_run_detail"
    ),

    # ============================================================
    # ⚙️ PAYROLL RUN ACTIONS (STATE MACHINE)
    # ============================================================

    # 🧮 حساب + تثبيت الرواتب
    # DRAFT → CALCULATED
    path(
        "runs/<int:pk>/calculate/",
        views.payroll_run_calculate_commit,
        name="payroll_run_calculate_commit"
    ),

    # ✅ اعتماد دورة الرواتب
    # CALCULATED → APPROVED
    path(
        "runs/<int:pk>/approve/",
        views.payroll_run_approve,
        name="payroll_run_approve"
    ),

    # 💸 صرف الرواتب
    # APPROVED → PAID
    path(
        "runs/<int:pk>/pay/",
        views.payroll_run_pay,
        name="payroll_run_pay"
    ),

    # ============================================================
    # ⚙️ LEGACY / OPTIONAL
    # ============================================================

    # ⚙️ التوليد الذكي (قديمة / اختيارية)
    path(
        "auto-generate/",
        views.payroll_auto_generate,
        name="payroll_auto_generate"
    ),

    # ============================================================
    # 🖨️ PRINTING ENGINE — PAYSLIPS
    # ============================================================

    # ✔ PDF قياسي
    path(
        "payslip/<int:pk>/pdf/",
        views.payroll_payslip_pdf,
        name="payroll_payslip_pdf"
    ),

    # ✔ V2 — Glass Edition
    path(
        "payslip/<int:pk>/v2/",
        views.payroll_payslip_v2,
        name="payroll_payslip_v2"
    ),

    # ✔ V5 — Signature Edition
    path(
        "payslip/<int:pk>/v5/",
        views.payroll_payslip_v5_signature,
        name="payroll_payslip_v5"
    ),

    # ✔ Thermal Receipt
    path(
        "payslip/<int:pk>/thermal/",
        views.payroll_payslip_thermal,
        name="payroll_payslip_thermal"
    ),

    # ✔ Quick Print
    path(
        "payslip/<int:pk>/quick/",
        views.payroll_quick_print,
        name="payroll_quick_print"
    ),

    # ✔ Download Direct
    path(
        "payslip/<int:pk>/download/",
        views.payroll_payslip_download,
        name="payroll_payslip_download"
    ),

    # 🔁 Reset Payroll Run
    path(
        "runs/<int:run_id>/reset/",
        views.payroll_run_reset,
        name="payroll_run_reset"
    ),

]
