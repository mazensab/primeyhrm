# ============================================================
# 📂 الملف: attendance_center/services/sync_biotime_to_attendance.py
# 🔄 خدمة المزامنة الذكية بين Biotime Center و Attendance Center
# ------------------------------------------------------------
# 💡 الهدف: تحويل سجلات BiotimeLog إلى AttendanceRecord رسمية
# ✅ آمنة – تحترم Unique Constraint – Idempotent – جاهزة للرواتب
# ✅ Multi-Company Ready
# ✅ Staging Ready (Unmapped Logs Preserved)
# ✔ WorkdayEngine Auto Apply (SAFE)
# ✔ Auto-Recalc Unknown Records (PATCH) 🔒
# ✔ MT-3 Isolation Patch (BiotimeEmployee FK Resolution) 🔥
# ✔ No Breaking Changes
# ✔ WhatsApp Hook for:
#    - Check In
#    - Check Out
#    - Present
#    - Late
#    - Absent
# ✔ Notification Hook for:
#    - In-App
#    - Realtime
#    - Email
# ✔ Absence Escalation:
#    - Employee Email + WhatsApp
#    - Manager Email + WhatsApp
# ============================================================

from datetime import datetime, time, timedelta
import logging

from django.utils import timezone

from biotime_center.models import BiotimeLog, BiotimeEmployee
from attendance_center.models import AttendanceRecord
from employee_center.models import Employee

from attendance_center.services.workday_engine import WorkdayEngine
from attendance_center.services.services import WorkScheduleResolver
from whatsapp_center.services import send_attendance_status_whatsapp_notifications
from notification_center.services_hr import notify_attendance_event


logger = logging.getLogger(__name__)


# ============================================================
# 📲 WhatsApp Attendance Hook Helper
# يمنع تكرار الإرسال داخل نفس دورة المزامنة
# ✅ تم تقييده هنا ليُرسل الغياب فقط من مسار المزامنة/الاعتماد النهائي
# ============================================================

def _send_attendance_whatsapp_once(
    *,
    record,
    company,
    notified_records: set[tuple[int, str]],
) -> int:
    """
    إرسال واتساب مرة واحدة فقط لكل AttendanceRecord + Event داخل نفس sync run.

    ✅ في هذا المسار نعتمد فقط:
    - absent

    ❌ ولا نرسل من المزامنة:
    - check_in
    - check_out
    - present
    - late

    السبب:
    هذا المسار هو مسار المزامنة اليومية / الاعتماد النهائي،
    والمطلوب أن يخرج تنبيه الغياب فقط عندما تصبح الحالة النهائية
    الفعلية في AttendanceRecord = absent.
    """
    try:
        if not record or not getattr(record, "id", None):
            return 0

        status_value = (getattr(record, "status", "") or "").strip().lower()

        # ----------------------------------------------------
        # ✅ نرسل فقط إذا أصبحت الحالة النهائية "absent"
        # ----------------------------------------------------
        if status_value != "absent":
            return 0

        event_key = (record.id, "wa:absent")

        if event_key in notified_records:
            return 0

        result = send_attendance_status_whatsapp_notifications(
            attendance_record=record,
            company=company,
            send_to_employee=True,
            send_to_user=True,
            send_to_manager=True,
            action=None,
            extra_context={
                "sync_source": "biotime",
                "finalized_source": "daily_sync_final",
            },
        )

        # نمنع التكرار داخل نفس الدورة حتى لو لم يتم الإرسال
        notified_records.add(event_key)

        if result and result.get("success") and result.get("sent_count", 0) > 0:
            return 1

        return 0

    except Exception:
        logger.exception(
            "⚠ Attendance WhatsApp hook failed during sync | record_id=%s",
            getattr(record, "id", None),
        )
        return 0


# ============================================================
# 🔔 Notification Attendance Hook Helper
# يمنع تكرار الإشعارات الداخلية/اللحظية/الإيميل داخل نفس الدورة
# ============================================================

def _send_attendance_notifications_once(
    *,
    record,
    notified_records: set[tuple[int, str]],
) -> int:
    """
    إرسال إشعارات الحضور مرة واحدة فقط لكل AttendanceRecord + Event داخل نفس sync run.

    القنوات المغطاة عبر notification_center.services_hr:
    - In-app
    - Realtime
    - Email
    - WhatsApp

    ✅ في الغياب النهائي:
    - Email للموظف
    - WhatsApp للموظف
    - Email للمدير
    - WhatsApp للمدير

    ✅ في بقية الحالات:
    - نبقي السلوك محافظًا كما كان قدر الإمكان
    """
    try:
        if not record or not getattr(record, "id", None):
            return 0

        sent_count = 0
        status_value = (getattr(record, "status", "") or "").strip().lower()

        def _dispatch(*, action=None, dedupe_key: str) -> int:
            event_key = (record.id, f"notify:{dedupe_key}")

            if event_key in notified_records:
                return 0

            is_absent_event = dedupe_key == "absent"

            notify_attendance_event(
                record,
                action=action,
                send_email_to_employee=True,
                send_email_to_managers=is_absent_event,
                send_whatsapp_to_employee=is_absent_event,
                send_whatsapp_to_managers=is_absent_event,
                extra_context={
                    "sync_source": "biotime",
                    "finalized_source": "daily_sync_final",
                    "attendance_event_key": dedupe_key,
                },
            )

            notified_records.add(event_key)
            return 1

        # ----------------------------------------------------
        # 1) حركة الدخول
        # ----------------------------------------------------
        if getattr(record, "check_in", None):
            sent_count += _dispatch(
                action="check_in",
                dedupe_key="check_in",
            )

        # ----------------------------------------------------
        # 2) حركة الخروج
        # ----------------------------------------------------
        if getattr(record, "check_out", None):
            sent_count += _dispatch(
                action="check_out",
                dedupe_key="check_out",
            )

        # ----------------------------------------------------
        # 3) الحالة النهائية بعد WorkdayEngine
        # ----------------------------------------------------
        if status_value == "present":
            sent_count += _dispatch(
                action="present",
                dedupe_key="present",
            )

        elif status_value == "late":
            sent_count += _dispatch(
                action=None,
                dedupe_key="late",
            )

        elif status_value == "absent":
            sent_count += _dispatch(
                action=None,
                dedupe_key="absent",
            )

        return sent_count

    except Exception:
        logger.exception(
            "⚠ Attendance Notification hook failed during sync | record_id=%s",
            getattr(record, "id", None),
        )
        return 0


# ============================================================
# 🧠 AttendanceSyncService (V4.9 Stable)
# ============================================================
class AttendanceSyncService:

    def sync(self, company=None, start_date=None, end_date=None):
        return sync_biotime_logs_to_attendance(
            company=company,
            start_date=start_date,
            end_date=end_date,
        )

    def sync_today(self, company=None):
        today = timezone.now().date()
        return sync_biotime_logs_to_attendance(
            company=company,
            start_date=today,
            end_date=today,
        )


# ============================================================
# 🧠 Smart Employee Resolver (MT-3 Multi-Tenant Safe)
# ============================================================

def resolve_employee_from_log(log):

    raw_code = getattr(log, "employee_code", None)
    if not raw_code:
        return None

    emp_code = str(raw_code).strip()
    emp_code = emp_code.lstrip("0") or emp_code

    # =====================================================
    # 🥇 PRIMARY RESOLUTION
    # BiotimeEmployee → Employee (Scoped + FK Driven)
    # =====================================================
    try:

        bt_emp = (
            BiotimeEmployee.objects
            .filter(employee_id__iexact=emp_code)
            .select_related("company")
            .first()
        )

        if bt_emp:
            employee = (
                Employee.objects
                .filter(biotime_employee=bt_emp)
                .select_related("company")
                .first()
            )

            if employee:
                return employee

    except Exception:
        logger.exception("❌ MT-3 Resolver Failed (Primary)")

    # =====================================================
    # 🥈 CARD NUMBER FALLBACK (Scoped through FK)
    # =====================================================
    try:

        bt_emp = (
            BiotimeEmployee.objects
            .filter(card_number=emp_code)
            .first()
        )

        if bt_emp:
            employee = (
                Employee.objects
                .filter(biotime_employee=bt_emp)
                .select_related("company")
                .first()
            )

            if employee:
                return employee

    except Exception:
        logger.exception("❌ Failed resolving employee via card_number fallback")

    # =====================================================
    # 🥉 LEGACY FALLBACK (TEST ONLY)
    # =====================================================
    try:

        employee = (
            Employee.objects
            .filter(biotime_code=emp_code)
            .select_related("company")
            .first()
        )

        if employee:
            return employee

        if emp_code.isdigit():
            employee = (
                Employee.objects
                .filter(id=int(emp_code))
                .select_related("company")
                .first()
            )
            if employee:
                return employee

    except Exception:
        logger.exception("❌ Legacy fallback failed")

    return None


# ============================================================
# 🔁 Sync Logs → Attendance (Multi-Tenant Safe)
# ============================================================

def sync_biotime_logs_to_attendance(
    company=None,
    start_date=None,
    end_date=None,
):
    """
    ✔ Multi-tenant safe
    ✔ Explicit company required
    ✔ Incremental generation preserved
    ✔ WorkdayEngine untouched
    ✔ Production ready
    ✔ WhatsApp notifications for:
      - check_in
      - check_out
      - present
      - late
      - absent
    ✔ Notification hooks for:
      - in-app
      - realtime
      - email
      - whatsapp
    ✔ Absence escalation:
      - employee + manager
    """

    if not company:
        return {
            "status": "error",
            "message": "Company context مطلوب.",
        }

    try:

        # =====================================================
        # 🔎 Fetch Unprocessed Logs (Company Scoped)
        # =====================================================
        logs = (
            BiotimeLog.objects
            .filter(company=company, processed=False)
            .order_by("punch_time")
        )

        # =====================================================
        # 🔥 SAFE RANGE FILTER (Timezone-Aware)
        # =====================================================
        if start_date and end_date:
            start_dt = timezone.make_aware(
                datetime.combine(start_date, time.min)
            )
            end_dt = timezone.make_aware(
                datetime.combine(end_date, time.max)
            )

            logs = logs.filter(
                punch_time__range=(start_dt, end_dt)
            )

        synced_count = 0
        skipped_unmapped = 0
        skipped_leave = 0
        recalculated_unknown = 0
        whatsapp_sent_count = 0
        notification_sent_count = 0
        notified_records: set[tuple[int, str]] = set()

        # =====================================================
        # Phase A — Sync Logs
        # =====================================================
        for log in logs.iterator():

            emp = resolve_employee_from_log(log)

            if not emp or emp.company_id != company.id:
                skipped_unmapped += 1
                continue

            local_dt = timezone.localtime(log.punch_time)
            work_date = local_dt.date()

            # ⛔ Ignore logs before employee work start
            if emp.work_start_date and work_date < emp.work_start_date:
                log.processed = True
                log.save(update_fields=["processed"])
                continue

            punch_time_value = local_dt.time()

            record = AttendanceRecord.objects.filter(
                employee=emp,
                date=work_date,
            ).first()

            if not record:
                record = AttendanceRecord.objects.create(
                    employee=emp,
                    date=work_date,
                )

            record_changed = False

            # Check-in
            if log.punch_state == "0":
                if not record.check_in or punch_time_value < record.check_in:
                    record.check_in = punch_time_value
                    record_changed = True

            # Check-out
            elif log.punch_state == "1":
                if not record.check_out or punch_time_value > record.check_out:
                    record.check_out = punch_time_value
                    record_changed = True

            # Link Biotime
            if (
                not record.synced_from_biotime
                or record.biotime_log_id != log.id
            ):
                record.synced_from_biotime = True
                record.biotime_log = log
                record_changed = True

            if record_changed:
                record.save(update_fields=[
                    "check_in",
                    "check_out",
                    "synced_from_biotime",
                    "biotime_log",
                ])

            if not log.processed:
                log.processed = True
                log.save(update_fields=["processed"])

            synced_count += 1

        # =====================================================
        # Phase A.5 — Full Generator From Work Start (Scoped)
        # =====================================================

        today = timezone.localdate()

        employees = (
            Employee.objects
            .filter(company=company)
            .select_related("company", "default_work_schedule")
        )

        for emp in employees:

            work_start = getattr(emp, "work_start_date", None)
            end_date_emp = getattr(emp, "end_date", None)

            if not work_start:
                continue

            current_date = work_start

            while current_date <= today:

                if end_date_emp and current_date > end_date_emp:
                    break

                record = AttendanceRecord.objects.filter(
                    employee=emp,
                    date=current_date,
                ).first()

                if not record:

                    schedule = WorkScheduleResolver.resolve(emp)

                    if schedule:
                        if schedule.is_weekend(current_date):
                            AttendanceRecord.objects.create(
                                employee=emp,
                                date=current_date,
                                status="weekend",
                                reason_code="auto_weekend",
                            )
                        else:
                            AttendanceRecord.objects.create(
                                employee=emp,
                                date=current_date,
                                status="unknown",
                                reason_code="auto_generated_no_logs",
                            )

                current_date += timedelta(days=1)

        # =====================================================
        # Phase B — Apply Workday Engine (Scoped)
        # =====================================================
        if start_date and end_date:
            records = AttendanceRecord.objects.filter(
                employee__company=company,
                date__range=(start_date, end_date),
            )
        else:
            today = timezone.localdate()
            yesterday = today - timedelta(days=1)

            records = AttendanceRecord.objects.filter(
                employee__company=company,
                date__gte=yesterday,
                is_finalized=False,
            )

        for record in records.iterator():

            if record.is_leave:
                skipped_leave += 1
                continue

            try:
                engine = WorkdayEngine(
                    record.employee,
                    company,
                )
                engine.apply(record)

                record.refresh_from_db()

                whatsapp_sent_count += _send_attendance_whatsapp_once(
                    record=record,
                    company=company,
                    notified_records=notified_records,
                )

                notification_sent_count += _send_attendance_notifications_once(
                    record=record,
                    notified_records=notified_records,
                )

            except Exception:
                logger.exception(
                    "❌ Failed applying WorkdayEngine "
                    f"(employee_id={record.employee_id}, date={record.date})"
                )

        # =====================================================
        # Phase C — Recalculate UNKNOWN (Scoped)
        # =====================================================
        unknown_records = AttendanceRecord.objects.filter(
            employee__company=company,
            status="unknown",
        )

        for record in unknown_records.iterator():
            try:
                engine = WorkdayEngine(
                    record.employee,
                    company,
                )
                engine.apply(record)
                recalculated_unknown += 1

                record.refresh_from_db()

                whatsapp_sent_count += _send_attendance_whatsapp_once(
                    record=record,
                    company=company,
                    notified_records=notified_records,
                )

                notification_sent_count += _send_attendance_notifications_once(
                    record=record,
                    notified_records=notified_records,
                )

            except Exception:
                logger.exception(
                    "❌ Failed recalculating UNKNOWN record "
                    f"(record_id={record.id})"
                )

        logger.info(
            "✅ Biotime → Attendance Sync Completed | "
            f"company={company.id} | "
            f"synced={synced_count} | "
            f"unmapped={skipped_unmapped} | "
            f"leave_skipped={skipped_leave} | "
            f"unknown_recalculated={recalculated_unknown} | "
            f"whatsapp_sent={whatsapp_sent_count} | "
            f"notifications_sent={notification_sent_count}"
        )

        return {
            "status": "success",
            "synced": synced_count,
            "skipped_unmapped": skipped_unmapped,
            "skipped_leave": skipped_leave,
            "recalculated_unknown": recalculated_unknown,
            "whatsapp_sent": whatsapp_sent_count,
            "notifications_sent": notification_sent_count,
        }

    except Exception as e:
        logger.exception("❌ خطأ أثناء مزامنة سجلات Biotime")
        return {
            "status": "error",
            "message": str(e),
        }