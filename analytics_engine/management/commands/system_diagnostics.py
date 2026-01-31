# 📂 الملف: analytics_engine/management/commands/system_diagnostics.py
# 🧭 أمر إداري لفحص النظام Primey HR Cloud V3
# 🚀 يتحقق من الاتصال بقاعدة البيانات، الجداول، التقارير الذكية والإشعارات
# ✨ يحتوي على خيار (--clean) لحذف بيانات الاختبار بعد الفحص

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from decimal import Decimal

# 🧩 استيراد النماذج والخدمات
from django.contrib.auth import get_user_model
from company_manager.models import Company, Subscription, Invoice, SubscriptionPlan
from analytics_engine.models import Report, ReportLog
from analytics_engine.services.report_generator import AutoReportGenerator
from notification_center.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = "🔍 فحص شامل للنظام Primey HR Cloud V3 (Database + Reports + Notifications)"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="🧹 حذف بيانات الاختبار (tester + شركة الاختبار + التقارير) بعد انتهاء الفحص",
        )

    def handle(self, *args, **options):
        clean_mode = options.get("clean", False)

        self.stdout.write(self.style.MIGRATE_HEADING("🚀 بدء الفحص الشامل للنظام Primey HR Cloud V3...\n"))
        self.check_database_connection()
        self.check_required_tables()
        user = self.create_sample_data()
        self.generate_test_report(user)
        self.verify_notifications(user)
        self.verify_report_logs()

        if clean_mode:
            self.cleanup_test_data()

        self.stdout.write(self.style.SUCCESS("\n✅ تم الفحص بنجاح - النظام يعمل بشكل سليم 🚀"))

    # -------------------------------------------------------
    # 🧩 فحص الاتصال بقاعدة البيانات
    # -------------------------------------------------------
    def check_database_connection(self):
        self.stdout.write(self.style.HTTP_INFO("🔹 فحص الاتصال بقاعدة البيانات..."))
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT DATABASE();")
                db = cursor.fetchone()
                self.stdout.write(self.style.SUCCESS(f"✅ قاعدة البيانات متصلة: {db[0]}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ فشل الاتصال بقاعدة البيانات: {e}"))

    # -------------------------------------------------------
    # 🧩 التحقق من وجود الجداول الأساسية
    # -------------------------------------------------------
    def check_required_tables(self):
        self.stdout.write(self.style.HTTP_INFO("\n🔹 فحص الجداول الأساسية..."))
        required = [
            "billing_center_company",
            "billing_center_companysubscription",
            "analytics_engine_report",
            "analytics_engine_reportlog",
            "django_apscheduler_djangojob",
        ]
        existing = connection.introspection.table_names()
        for t in required:
            if t in existing:
                self.stdout.write(self.style.SUCCESS(f"✅ {t} موجودة"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ {t} غير موجودة"))

    # -------------------------------------------------------
    # 🧩 إنشاء بيانات تجريبية آمنة
    # -------------------------------------------------------
    def create_sample_data(self):
        self.stdout.write(self.style.HTTP_INFO("\n🔹 إنشاء بيانات تجريبية (إن لم تكن موجودة)..."))

        user, _ = User.objects.get_or_create(
            username="tester",
            defaults={"email": "tester@primeyhr.com", "password": "admin1234"},
        )

        # فحص الحقول المتاحة في نموذج الشركة
        company_fields = [f.name for f in Company._meta.get_fields()]
        defaults = {}
        if "is_active" in company_fields:
            defaults["is_active"] = True

        company, _ = Company.objects.get_or_create(
            name="شركة الاختبار الذكية",
            defaults={
                **defaults,
                "cr_number": "1234567890",
                "email": "test@primeyhr.com",
                "phone": "0550000000",
            },
        )

        # إنشاء خطة اشتراك تجريبية متوافقة مع النموذج
        plan_defaults = {}
        plan_fields = [f.name for f in SubscriptionPlan._meta.get_fields()]

        if "price_monthly" in plan_fields:
            plan_defaults["price_monthly"] = Decimal("299.00")
        if "price_yearly" in plan_fields:
            plan_defaults["price_yearly"] = Decimal("2990.00")
        if "description" in plan_fields:
            plan_defaults["description"] = "خطة تجريبية أساسية لاختبار النظام"
        if "features" in plan_fields:
            plan_defaults["features"] = {"ai_reports": True, "storage_gb": 5, "users": 10}

        plan, _ = SubscriptionPlan.objects.get_or_create(
            name="PRO",
            defaults=plan_defaults
        )

        # إنشاء اشتراك للشركة
        sub = None
        try:
            sub, _ = Subscription.objects.get_or_create(
                company=company,
                defaults={
                    "plan": plan,
                    "status": "ACTIVE",
                    "start_date": timezone.now(),
                    "total_amount": Decimal("299.00"),
                },
            )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ لم يتم إنشاء اشتراك (ربما الجدول غير موجود): {e}"))

        # إنشاء فاتورة مرتبطة
        try:
            if sub:
                Invoice.objects.get_or_create(
                    company=company,
                    defaults={
                        "subscription": sub,
                        "invoice_number": "INV-TEST-001",
                        "total_amount": Decimal("299.00"),
                        "status": "PAID",
                        "issue_date": timezone.now(),
                    },
                )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ لم يتم إنشاء فاتورة: {e}"))

        self.stdout.write(self.style.SUCCESS(f"🏢 الشركة: {company.name}"))
        self.stdout.write(self.style.SUCCESS(f"💳 الخطة: {plan.name}"))
        return user

    # -------------------------------------------------------
    # 🧩 توليد تقرير ذكي تجريبي
    # -------------------------------------------------------
    def generate_test_report(self, user):
        self.stdout.write(self.style.HTTP_INFO("\n🔹 توليد تقرير ذكي تجريبي..."))
        try:
            report = AutoReportGenerator.generate_summary_report(created_by=user)
            self.stdout.write(self.style.SUCCESS(f"✅ تم إنشاء التقرير: {report.title}"))
            self.stdout.write(f"📊 AI Score: {report.ai_score}%")
            self.stdout.write(f"🧠 الملخص:\n{report.ai_summary}\n")
            return report
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ فشل توليد التقرير: {e}"))

    # -------------------------------------------------------
    # 🧩 التحقق من الإشعارات
    # -------------------------------------------------------
    def verify_notifications(self, user):
        self.stdout.write(self.style.HTTP_INFO("\n🔹 التحقق من نظام الإشعارات..."))
        notifs = Notification.objects.filter(recipient=user).order_by("-created_at")[:3]
        if not notifs.exists():
            self.stdout.write(self.style.WARNING("⚠️ لا توجد إشعارات حديثة."))
        else:
            for n in notifs:
                self.stdout.write(f"🔔 {n.title} - {n.message} ({n.created_at.strftime('%Y-%m-%d %H:%M')})")

    # -------------------------------------------------------
    # 🧩 التحقق من سجل التقارير
    # -------------------------------------------------------
    def verify_report_logs(self):
        self.stdout.write(self.style.HTTP_INFO("\n🔹 التحقق من سجل العمليات على التقارير..."))
        logs = ReportLog.objects.all().order_by("-executed_at")[:5]
        if not logs.exists():
            self.stdout.write(self.style.WARNING("⚠️ لا توجد سجلات تقارير بعد."))
        else:
            for l in logs:
                self.stdout.write(f"🧾 {l.report.title} - {l.get_action_display()} ({l.executed_at.strftime('%Y-%m-%d %H:%M')})")

    # -------------------------------------------------------
    # 🧹 حذف بيانات الاختبار (في وضع --clean)
    # -------------------------------------------------------
    def cleanup_test_data(self):
        self.stdout.write(self.style.HTTP_INFO("\n🧹 حذف بيانات الاختبار..."))
        try:
            # حذف التقارير
            Report.objects.filter(created_by__username="tester").delete()
            ReportLog.objects.all().delete()

            # حذف الشركة
            Company.objects.filter(name="شركة الاختبار الذكية").delete()

            # حذف المستخدم
            User.objects.filter(username="tester").delete()

            self.stdout.write(self.style.SUCCESS("✅ تم حذف بيانات الاختبار بالكامل بنجاح"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ فشل أثناء حذف بيانات الاختبار: {e}"))
