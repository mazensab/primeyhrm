# ============================================================
# 🕒 Auto Reset Leave Balance — Cron Job V6.1 Ultra Pro (Fixed)
# 📦 Primey HR Cloud — Leave Center Auto Scheduler Engine
# + Notification Center Integration (create_notification)
# ============================================================

from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from datetime import date

from .models import LeaveBalance
from notification_center.services import create_notification  # ← الإشعارات


# ============================================================
# 🧹 تنظيف سجلات الجدولة القديمة
# ============================================================
@util.close_old_connections
def delete_old_job_executions(max_age=86400):
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


# ============================================================
# 🔄 الوظيفة الأساسية — إعادة ضبط رصيد الإجازات + إرسال تنبيهات
# ============================================================
@util.close_old_connections
def auto_reset_leave_balances():
    today = date.today()

    # يعمل فقط يوم 1 يناير
    if today.month == 1 and today.day == 1:

        balances = LeaveBalance.objects.select_related("employee", "company")

        notified_companies = set()  # منع تكرار إشعارات HR

        for bal in balances:

            # ====================================================
            # 🟦 إعادة ضبط كامل للأرصدة — نظام العمل 2025
            # ====================================================
            bal.annual_balance = 21
            bal.sick_balance = 30
            bal.maternity_balance = 10
            bal.marriage_balance = 5
            bal.death_balance = 3
            bal.hajj_balance = 10
            bal.study_balance = 15

            bal.last_reset = today
            bal.save()

            employee = bal.employee
            company = employee.company

            # ----------------------------------------------------
            # 🔔 1) إشعار الموظف
            # ----------------------------------------------------
            create_notification(
                recipient=employee.user,
                title="🔄 تم تحديث رصيد الإجازات",
                message=f"تم إعادة ضبط رصيد إجازاتك السنوي إلى {bal.annual_balance} يومًا.",
                severity="info",
                link="/leave-center/"
            )

            notified_companies.add(company)

        # ----------------------------------------------------
        # 🔔 2) إشعار HR — مرة واحدة لكل شركة
        # ----------------------------------------------------
        for company in notified_companies:

            # جلب جميع مستخدمين HR للشركة
            hr_users = company.companyuser_set.filter(role__name="HR")

            for hr in hr_users:
                create_notification(
                    recipient=hr.user,
                    title="✔ تمت إعادة ضبط أرصدة الإجازات",
                    message="تم إعادة ضبط أرصدة الإجازات السنوية لجميع الموظفين لهذا العام.",
                    severity="success",
                    link="/leave-center/"
                )

        print("✔ Auto Reset + Notifications Done Successfully!")


# ============================================================
# 🚀 Boot APScheduler
# ============================================================
scheduler_started = False


def start_scheduler():
    global scheduler_started
    if scheduler_started:
        return

    scheduler_started = True

    try:
        scheduler = BackgroundScheduler(
            timezone=str(timezone.get_current_timezone())
        )

        scheduler.add_jobstore(DjangoJobStore(), "default")

        # ===== Reset Job =====
        scheduler.add_job(
            auto_reset_leave_balances,
            trigger="cron",
            hour=3,
            minute=0,
            id="auto_reset_leave_balances",
            max_instances=1,
            replace_existing=True,
        )

        # ===== Cleanup Job =====
        scheduler.add_job(
            delete_old_job_executions,
            trigger="cron",
            day_of_week="sun",
            hour=4,
            minute=0,
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )

        scheduler.start()
        print("✔ APScheduler Started Successfully (Leave Center)")

    except Exception as e:
        print(f"❌ Scheduler Error: {e}")
