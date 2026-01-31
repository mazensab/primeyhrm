# ============================================================
# 📂 Analytics Engine — Views V6 Ultra Pro
# Fully Compatible with Billing Center V7
# ============================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.http import FileResponse, JsonResponse
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
import os
from collections import defaultdict

# 🧩 نماذج التحليلات
from .models import Report, ReportLog
from .services.report_generator import AutoReportGenerator

# 🧩 وحدة الشركات
from company_manager.models import Company

# 🧩 استيراد الموظفين (اختياري)
try:
    from employee_center.models import Employee
    EMPLOYEE_MODEL = Employee
except ImportError:
    EMPLOYEE_MODEL = None

# 🧩 وحدة الفوترة (Billing Center V7)
from billing_center.models import (
    Invoice,
    SubscriptionPlan,
    CompanySubscription,
    Payment,
)

# 🧩 الإشعارات
from notification_center.services import create_notification


# ============================================================
# 📊 1) لوحة التقارير والتحليلات الذكية
# ============================================================
@login_required
def reports_dashboard(request):

    now = timezone.now()
    six_months_ago = now - timedelta(days=180)

    # 📦 إحصاءات الشركات والموظفين
    companies_count = Company.objects.count()
    employees_count = EMPLOYEE_MODEL.objects.count() if EMPLOYEE_MODEL else 0

    # 🔹 الاشتراكات النشطة
    active_subs = CompanySubscription.objects.filter(status="ACTIVE").count()

    # 🔹 الفواتير المدفوعة
    invoices_paid_count = Invoice.objects.filter(status="PAID").count()

    # 💰 الإيرادات آخر 6 أشهر
    invoices = Invoice.objects.filter(
        status="PAID",
        issue_date__gte=six_months_ago
    )
    total_revenue = invoices.aggregate(
        total=models.Sum("total_amount")
    )["total"] or Decimal("0.00")

    # 🗓️ الإيرادات الشهرية
    monthly_revenue = defaultdict(Decimal)
    for inv in invoices:
        label = inv.issue_date.strftime("%b %Y")
        monthly_revenue[label] += inv.total_amount

    months = list(monthly_revenue.keys())
    revenues = [float(monthly_revenue[m]) for m in months]

    # 🧾 أحدث التقارير
    reports = Report.objects.all().order_by("-created_at")[:12]

    # 🤖 ملخص الذكاء الصناعي
    latest_ai_report = Report.objects.filter(report_type="ai_analysis").first()
    ai_summary = latest_ai_report.ai_summary if latest_ai_report else "⚙️ لم يتم إنشاء تقرير ذكي."
    ai_score = latest_ai_report.ai_score if latest_ai_report else 0

    return render(request, "analytics_engine/reports_dashboard.html", {
        "page_title": "لوحة التقارير والتحليلات الذكية",
        "companies_count": companies_count,
        "employees_count": employees_count,
        "subscriptions_count": active_subs,
        "plans_count": SubscriptionPlan.objects.count(),
        "invoices_paid_count": invoices_paid_count,
        "total_revenue": total_revenue,
        "months": months,
        "revenues": revenues,
        "reports": reports,
        "ai_summary": ai_summary,
        "ai_score": ai_score,
        "active_menu": "analytics_dashboard",
    })


# ============================================================
# 🤖 2) توليد تقرير ذكي يدويًا
# ============================================================
@login_required
def generate_report_now(request):

    try:
        report = AutoReportGenerator.generate_summary_report(
            created_by=request.user
        )

        create_notification(
            recipient=request.user,
            title="📈 تم توليد تقرير ذكي جديد",
            message=f"تم إنشاء التقرير '{report.title}' بنجاح.",
            notification_type="report"
        )

        messages.success(request, f"تم توليد التقرير الذكي: {report.title}")

    except Exception as e:
        messages.error(request, f"حدث خطأ أثناء التوليد: {e}")

    return redirect("analytics_engine:reports_dashboard")


# ============================================================
# 📄 3) توليد PDF رسمي
# ============================================================
@login_required
def generate_report_pdf(request, report_id):

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    report = get_object_or_404(Report, id=report_id)

    reports_dir = os.path.join(settings.MEDIA_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    pdf_path = os.path.join(reports_dir, f"report_{report.id}.pdf")

    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    c.setFont("HeiseiMin-W3", 16)
    c.drawCentredString(width / 2, height - 40, "📊 تقرير الأداء والتحليل الذكي")

    # 🔹 الملخصات الأساسية
    c.setFont("HeiseiMin-W3", 12)
    c.drawString(30 * mm, 260 * mm, f"عنوان التقرير: {report.title}")
    c.drawString(30 * mm, 250 * mm, f"تاريخ الإنشاء: {report.created_at.strftime('%Y-%m-%d %H:%M')}")

    # 🧾 بيانات مالية
    total_invoices = Invoice.objects.count()
    paid_invoices = Invoice.objects.filter(status="PAID").count()
    active_subs = CompanySubscription.objects.filter(status="ACTIVE").count()
    total_companies = Company.objects.count()
    total_revenue = Invoice.objects.filter(status="PAID").aggregate(
        total=models.Sum("total_amount")
    )["total"] or 0.00

    text = c.beginText(30 * mm, 210 * mm)
    text.setFont("HeiseiMin-W3", 11)
    text.textLines(f"""
🔹 الشركات: {total_companies}
🔹 اشتراكات نشطة: {active_subs}
🔹 الفواتير الصادرة: {total_invoices}
🔹 الفواتير المدفوعة: {paid_invoices}
💰 إجمالي الإيرادات: {total_revenue} ر.س
""")

    # 🔹 ملخص الذكاء الصناعي
    if report.ai_summary:
        text.textLine("")
        text.textLine("🧠 التحليل الذكي:")
        text.textLines(report.ai_summary.splitlines())

    c.drawText(text)
    c.showPage()
    c.save()

    report.file_path = f"reports/report_{report.id}.pdf"
    report.save(update_fields=["file_path"])

    create_notification(
        recipient=request.user,
        title="📄 تم إنشاء تقرير PDF",
        message=f"تم إنشاء التقرير '{report.title}' بنجاح.",
        notification_type="report"
    )

    return FileResponse(open(pdf_path, "rb"), content_type="application/pdf")


# ============================================================
# 🤖 4) Smart Analytics Dashboard
# ============================================================
@login_required
def smart_analytics_dashboard(request):

    recent = Report.objects.filter(
        report_type="ai_analysis"
    ).order_by("-created_at")[:5]

    ai_scores = [r.ai_score for r in recent]
    avg_score = round(sum(ai_scores) / len(ai_scores), 2) if ai_scores else 0

    return render(request, "analytics_engine/smart_analytics_dashboard.html", {
        "page_title": "Smart Analytics",
        "recent_reports": recent,
        "avg_score": avg_score,
        "active_menu": "smart_analytics_dashboard",
    })


# ============================================================
# 🧪 5) Test API
# ============================================================
def test_analytics_engine(request):
    return JsonResponse({
        "status": "Ready",
        "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    })


# ============================================================
# 📊 6) Analytics Dashboard V5.7
# ============================================================
@login_required
def analytics_dashboard(request):

    now = timezone.now()
    six_months_ago = now - timedelta(days=180)

    companies_count = Company.objects.count()
    invoices_paid = Invoice.objects.filter(status="PAID").count()
    active_subs = CompanySubscription.objects.filter(status="ACTIVE").count()
    ai_reports = Report.objects.filter(report_type="ai_analysis").count()

    invoices = Invoice.objects.filter(
        status="PAID",
        issue_date__gte=six_months_ago
    )

    monthly = defaultdict(float)
    for inv in invoices:
        lbl = inv.issue_date.strftime("%b %Y")
        monthly[lbl] += float(inv.total_amount)

    return render(request, "analytics_engine/dashboard.html", {
        "page_title": "لوحة التحليلات العامة",
        "active_tab": "analytics",
        "companies_count": companies_count,
        "invoices_paid": invoices_paid,
        "total_revenue": sum(monthly.values()),
        "active_subs": active_subs,
        "ai_reports": ai_reports,
        "months": list(monthly.keys()),
        "revenues": list(monthly.values()),
        "active_menu": "analytics_dashboard",
    })
