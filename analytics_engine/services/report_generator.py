# 📂 الملف: analytics_engine/services/report_generator.py
# 🤖 Auto Report Generator V4 — متوافق مع الهيكل الجديد للـ Billing Center

from django.utils.timezone import now
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from analytics_engine.models import Report, ReportLog
from company_manager.models import Company   # ✔ فقط Company
from employee_center.models import Employee  # ✔ موظفين من المسار الصحيح

# إشعارات النظام
try:
    from notification_center.services import create_notification
except ImportError:
    create_notification = None

User = get_user_model()


# =====================================================================
# ⚙️ وحدة التوليد الذكي للتقارير (Auto Report Generator V4)
# =====================================================================
class AutoReportGenerator:

    @classmethod
    @transaction.atomic
    def generate_summary_report(cls, created_by: User):
        """🧠 توليد تقرير الأداء العام التلقائي."""

        # -----------------------------------------------------------------
        # 🔹 جمع البيانات الأساسية
        # -----------------------------------------------------------------
        total_companies = Company.objects.count()
        total_employees = Employee.objects.count()

        # 🔸 مبدئيًا: بدلاً من الاشتراكات (لأن CompanySubscription لم يعد موجودًا)
        active_subs = total_companies         # افتراضيًا كل الشركات نشطة
        expired_subs = 0
        suspended_subs = 0

        # -----------------------------------------------------------------
        # 🧮 التحليل الذكي
        # -----------------------------------------------------------------
        if total_companies > 0:
            active_ratio = (active_subs / total_companies) * 100
            performance_index = active_ratio
            ai_score = max(0, min(100, round(performance_index, 2)))
        else:
            ai_score = 0

        ai_summary = (
            "📊 **تحليل الأداء العام (Auto Generated Report)**\n\n"
            f"🏢 عدد الشركات المسجلة: {total_companies}\n"
            f"👥 إجمالي الموظفين: {total_employees}\n\n"
            f"💡 مؤشر الأداء الكلي (AI Score): {ai_score}%\n"
        )

        # -----------------------------------------------------------------
        # 🧾 إنشاء التقرير
        # -----------------------------------------------------------------
        report = Report.objects.create(
            title=f"📈 تقرير الأداء العام - {now().strftime('%Y-%m-%d')}",
            report_type="ai_analysis",
            created_by=created_by,
            ai_summary=ai_summary,
            ai_score=ai_score,
            auto_generated=True,
            status="READY",
        )

        # -----------------------------------------------------------------
        # 🧾 تسجيل العملية في سجل التقارير
        # -----------------------------------------------------------------
        ReportLog.objects.create(
            report=report,
            action="GENERATE_AI",
            executed_by=created_by,
            details="تم توليد تقرير الأداء العام بواسطة AutoReportGenerator.",
        )

        # -----------------------------------------------------------------
        # 🔔 إشعار النظام
        # -----------------------------------------------------------------
        if create_notification:
            create_notification(
                recipient=created_by,
                title="📈 تم إنشاء تقرير تحليلي جديد",
                message=f"تم إنشاء تقرير أداء عام ({report.title}) بنجاح.",
                notification_type="report",
                link="/analytics/reports/",
            )

        # -----------------------------------------------------------------
        # 📧 البريد الإلكتروني
        # -----------------------------------------------------------------
        if created_by.email:
            send_mail(
                subject="📊 تقرير تحليلي جديد في Primey HR Cloud",
                message=f"تم إنشاء تقرير تحليلي جديد:\n{report.title}\n\n{ai_summary}",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@primeyhr.com"),
                recipient_list=[created_by.email],
                fail_silently=True,
            )

        return report
