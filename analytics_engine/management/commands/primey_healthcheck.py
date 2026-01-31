# 📂 الملف: analytics_engine/management/commands/primey_healthcheck.py
# 🧭 أمر إداري لفحص صحة النظام Primey HR Cloud V3
# 🚀 يتحقق من جاهزية الوحدات الأساسية (Database + Tables + Scheduler + Reports)
# 💌 يرسل إشعارًا للمسؤول عند وجود أي خلل

from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth import get_user_model
from django.utils import timezone
from notification_center.models import Notification
from company_manager.models import Company, Subscription, Invoice
from analytics_engine.models import Report, ReportLog
from django_apscheduler.models import DjangoJob
from django.core.mail import send_mail

User = get_user_model()


class Command(BaseCommand):
    help = "💡 فحص صحة النظام Primey HR Cloud V3 (Health Check Monitor)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("🩺 بدء فحص Primey HealthCheck...\n"))

        status = {
            "db_connected": self.check_database(),
            "tables_ok": self.check_tables(),
            "scheduler_ok": self.check_scheduler(),
            "reports_ok": self.check_reports(),
        }

        self.summarize(status)

    # --------------------------------------------------------
    # 🧩 فحص قاعدة البيانات
    # --------------------------------------------------------
    def check_database(self):
        self.stdout.write(self.style.HTTP_INFO("🔹 فحص الاتصال بقاعدة البيانات..."))
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT DATABASE();")
                db = cursor.fetchone()
                self.stdout.write(self.style.SUCCESS(f"✅ قاعدة البيانات متصلة ({db[0]})"))
                return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ فشل الاتصال بقاعدة البيانات: {e}"))
            self.notify_admin("فشل الاتصال بقاعدة البيانات", str(e))
            return False

    # --------------------------------------------------------
    # 🧩 فحص الجداول الأساسية
    # --------------------------------------------------------
    def check_tables(self):
        self.stdout.write(self.style.HTTP_INFO("\n🔹 فحص الجداول الأساسية..."))
        required_tables = [
            "billing_center_company",
            "billing_center_companysubscription",
            "billing_center_invoice",
            "analytics_engine_report",
            "analytics_engine_reportlog",
            "django_apscheduler_djangojob",
        ]
        existing = connection.introspection.table_names()
        missing = [t for t in required_tables if t not in existing]

        if missing:
            for t in missing:
                self.stdout.write(self.style.WARNING(f"⚠️ الجدول مفقود: {t}"))
            self.notify_admin("جداول ناقصة في قاعدة البيانات", f"الجداول المفقودة: {', '.join(missing)}")
            return False

        self.stdout.write(self.style.SUCCESS("✅ جميع الجداول الأساسية موجودة"))
        return True

    # --------------------------------------------------------
    # 🕒 فحص جدولة المهام (APScheduler)
    # --------------------------------------------------------
    def check_scheduler(self):
        self.stdout.write(self.style.HTTP_INFO("\n🔹 فحص مهام APScheduler..."))
        try:
            job_count = DjangoJob.objects.count()
            if job_count == 0:
                self.stdout.write(self.style.WARNING("⚠️ لا توجد مهام مجدولة."))
                self.notify_admin("لا توجد مهام APScheduler", "تحقق من وحدة الجدولة اليومية.")
                return False
            self.stdout.write(self.style.SUCCESS(f"✅ عدد المهام المجدولة: {job_count}"))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ فشل فحص APScheduler: {e}"))
            self.notify_admin("فشل فحص APScheduler", str(e))
            return False

    # --------------------------------------------------------
    # 📊 فحص التقارير الذكية
    # --------------------------------------------------------
    def check_reports(self):
        self.stdout.write(self.style.HTTP_INFO("\n🔹 فحص نظام التقارير..."))
        try:
            count_reports = Report.objects.count()
            count_logs = ReportLog.objects.count()
            self.stdout.write(self.style.SUCCESS(f"✅ عدد التقارير: {count_reports} | السجلات: {count_logs}"))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ خطأ في نظام التقارير: {e}"))
            self.notify_admin("فشل فحص نظام التقارير", str(e))
            return False

    # --------------------------------------------------------
    # 🧠 تلخيص الفحص العام
    # --------------------------------------------------------
    def summarize(self, status):
        self.stdout.write(self.style.HTTP_INFO("\n📋 ملخص الفحص النهائي:"))
        ok = all(status.values())

        for key, val in status.items():
            mark = "✅" if val else "❌"
            self.stdout.write(f"  {mark} {key}")

        if ok:
            self.stdout.write(self.style.SUCCESS("\n✅ النظام في حالة ممتازة - لا توجد أخطاء 🚀"))
            self.notify_admin("فحص النظام ناجح ✅", "تم فحص Primey HR Cloud وجميع المكونات تعمل بكفاءة.")
        else:
            self.stdout.write(self.style.WARNING("\n⚠️ النظام يحتوي على أخطاء - راجع السجل أعلاه."))

    # --------------------------------------------------------
    # 🔔 إرسال إشعار للمسؤولين عند وجود خلل
    # --------------------------------------------------------
    def notify_admin(self, title, message):
        try:
            admins = User.objects.filter(is_superuser=True)
            for admin in admins:
                Notification.objects.create(
                    recipient=admin,
                    title=f"🚨 تنبيه النظام: {title}",
                    message=message,
                )
            # إرسال بريد إلكتروني أيضًا
            send_mail(
                subject=f"⚠️ تنبيه Primey HR Cloud: {title}",
                message=f"{message}\n\nتم التحقق في {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                from_email="Primey HR Cloud <noreply@primeyhr.com>",
                recipient_list=[a.email for a in admins if a.email],
                fail_silently=True,
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ فشل إرسال الإشعار: {e}"))
