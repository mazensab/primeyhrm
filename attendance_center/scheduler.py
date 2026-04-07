# ================================================================
# 🕒 Auto Sync Scheduler Engine — V13 Ultra Pro (HARDENED)
# Mham Cloud — Attendance Center
# ================================================================

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from django.conf import settings

from .models import AttendanceSetting, AttendanceRecord
from company_manager.models import Company, CompanyUser
from notification_center.services import create_notification, broadcast_notification


# ================================================================
# 🧠 Global Scheduler (Singleton)
# ================================================================
scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)


# ================================================================
# 🔔 Helpers — تحديد مستلمي الإشعار
# ================================================================
def get_admin_recipients(company):
    return CompanyUser.objects.filter(
        company=company,
        is_active=True,
        role__in=["SYSTEM_OWNER", "COMPANY_ADMIN"],
    )


# ================================================================
# 🔔 إرسال إشعار فشل
# ================================================================
def send_failure_notification(company, message):
    recipients = get_admin_recipients(company)

    for cu in recipients:
        create_notification(
            user=cu.user,
            title="❌ فشل مزامنة الحضور",
            message=message,
            category="error",
            link="/attendance/dashboard/",
        )
        broadcast_notification(
            cu.user.id,
            {
                "title": "❌ فشل مزامنة الحضور",
                "message": message,
                "type": "error",
            },
        )


# ================================================================
# 🔧 مزامنة سجلات Biotime (Per Company)
# ================================================================
def sync_company_attendance(company, settings_obj):
    """
    🔒 Sync آمن لشركة واحدة فقط
    """

    if not company or not settings_obj:
        return False, "Invalid company or attendance settings."

    try:
        response = requests.get(
            f"{settings_obj.biotime_server_url}/logs",
            headers={"Authorization": f"Bearer {settings_obj.api_key}"},
            timeout=8,
        )

        if response.status_code != 200:
            return False, f"Invalid response: {response.status_code}"

        logs = response.json().get("logs", [])
        imported = 0

        for log in logs:
            AttendanceRecord.objects.update_or_create(
                employee_id=log.get("employee_id"),
                date=log.get("punch_time", "")[:10],
                defaults={
                    "status": "present",
                    "synced_from_biotime": True,
                },
            )
            imported += 1

        settings_obj.last_sync = timezone.now()
        settings_obj.save(update_fields=["last_sync"])

        return True, f"Imported {imported} entries."

    except Exception as exc:
        return False, str(exc)


# ================================================================
# 🔒 SAFE JOB WRAPPER — Per Company Isolation
# ================================================================
def auto_sync_job_runner():
    """
    🔒 Wrapper آمن:
    - يعزل كل شركة
    - يمنع سقوط الـ scheduler بالكامل
    - يمنع التوازي غير المقصود
    """

    companies = Company.objects.filter(is_active=True)

    for company in companies:
        try:
            settings_obj = AttendanceSetting.objects.filter(
                company=company,
                auto_sync_enabled=True,
            ).first()

            if not settings_obj:
                continue

            ok, message = sync_company_attendance(company, settings_obj)

            if not ok:
                send_failure_notification(company, message)

        except Exception as exc:
            send_failure_notification(
                company,
                f"خطأ غير متوقع أثناء المزامنة: {exc}",
            )
            continue


# ================================================================
# 🚀 تشغيل Auto Sync Scheduler (SAFE BOOT)
# ================================================================
def start_auto_sync_scheduler():
    """
    🔒 Safe Scheduler Bootstrap
    """

    if scheduler.running:
        return  # 🔒 Prevent double start

    print("🔥 [Scheduler] Starting Auto Sync Engine…")

    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        auto_sync_job_runner,
        trigger="interval",
        minutes=50,
        id="auto_sync_job",
        replace_existing=True,
        max_instances=1,          # 🔒 no parallel runs
        coalesce=True,            # 🔒 merge delayed executions
        misfire_grace_time=300,   # 🔒 5 minutes grace
    )

    try:
        scheduler.start()
        print("🚀 Scheduler Started Successfully.")
        print(f"🟢 Active Jobs: {[job.id for job in scheduler.get_jobs()]}")
    except Exception as exc:
        print("❌ Failed to start Scheduler:", exc)
