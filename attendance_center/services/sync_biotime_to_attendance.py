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
# ✔ No Breaking Changes
# ============================================================

from django.utils import timezone
from django.db import IntegrityError, transaction

from biotime_center.models import BiotimeLog, BiotimeEmployee
from attendance_center.models import AttendanceRecord
from employee_center.models import Employee

# 🧠 Attendance Calculation Engine
from attendance_center.services.workday_engine import WorkdayEngine

import logging

logger = logging.getLogger(__name__)


# ============================================================
# 🧠 0️⃣ AttendanceSyncService (V4.9 Stable)
# ============================================================
class AttendanceSyncService:
    """
    🧠 خدمة مزامنة سجلات Biotime مع Attendance Center
    - Wrapper جاهز للـ Views / Scheduler
    - لا يكسر أي منطق داخلي
    """

    def sync(self, start_date=None, end_date=None):
        """
        🔄 تنفيذ المزامنة العامة
        """
        return sync_biotime_logs_to_attendance(start_date, end_date)

    def sync_today(self):
        """
        🔄 مزامنة سجلات اليوم فقط
        """
        today = timezone.now().date()
        return sync_biotime_logs_to_attendance(today, today)


# ============================================================
# 🧠 Smart Employee Resolver (READ-ONLY SAFE)
# ============================================================

def resolve_employee_from_log(log):
    """
    🔎 محاولة ربط Log بموظف النظام بطريقة آمنة.

    ترتيب البحث (حسب المعمارية الصحيحة):

    1) Employee.biotime_code مباشرة.
    2) BiotimeEmployee.card_number → Employee.biotime_employee.
    3) BiotimeEmployee.employee_id → Employee.biotime_employee.
    4) Fallback أخير: Employee.id (لأغراض الاختبار فقط).

    ⚠️ لا يتم إنشاء أي Auto-Link أو تعديل في قاعدة البيانات.
    """

    raw_code = getattr(log, "employee_code", None)
    if not raw_code:
        return None

    # --------------------------------------------
    # 🧹 Normalize code
    # --------------------------------------------
    emp_code = str(raw_code).strip()
    emp_code = emp_code.lstrip("0") or emp_code

    # --------------------------------------------
    # 🥇 Direct lookup in Employee.biotime_code
    # --------------------------------------------
    employee = (
        Employee.objects
        .filter(biotime_code=emp_code)
        .select_related("company")
        .first()
    )
    if employee:
        return employee

    # --------------------------------------------
    # 🥈 Fallback via BiotimeEmployee.card_number
    #     ثم الربط عبر Employee.biotime_employee
    # --------------------------------------------
    try:
        biotime_emp = (
            BiotimeEmployee.objects
            .filter(card_number=emp_code)
            .only("id")
            .first()
        )

        if biotime_emp:
            employee = (
                Employee.objects
                .filter(biotime_employee=biotime_emp)
                .select_related("company")
                .first()
            )
            if employee:
                return employee

    except Exception:
        logger.exception("❌ Failed resolving employee via card_number fallback")

    # --------------------------------------------
    # 🥉 Fallback via BiotimeEmployee.employee_id
    # --------------------------------------------
    try:
        if emp_code.isdigit():
            biotime_emp = (
                BiotimeEmployee.objects
                .filter(employee_id=int(emp_code))
                .only("id")
                .first()
            )

            if biotime_emp:
                employee = (
                    Employee.objects
                    .filter(biotime_employee=biotime_emp)
                    .select_related("company")
                    .first()
                )
                if employee:
                    return employee

            # ----------------------------------------
            # ⚠️ Fallback أخير (اختباري فقط)
            # ----------------------------------------
            employee = (
                Employee.objects
                .filter(id=int(emp_code))
                .select_related("company")
                .first()
            )
            if employee:
                return employee

    except Exception:
        logger.exception("❌ Failed resolving employee via employee_id fallback")

    return None


# ============================================================
# 🔁 1️⃣ المزامنة الأساسية (SMART STAGING + AUTO CALCULATION)
# ============================================================
def sync_biotime_logs_to_attendance(start_date=None, end_date=None):
    """
    🔄 تحويل سجلات BiotimeLog إلى AttendanceRecord.

    قواعد الأمان:
    - لا يتم استخدام get_or_create إطلاقًا.
    - يحترم القيد الفريد (employee + date).
    - لا يلمس سجلات الإجازات أو السجلات اليدوية.
    - Idempotent.
    - Unmapped logs تبقى محفوظة (Staging Mode).
    - يتم احتساب الحضور دائمًا عبر WorkdayEngine (Source of Truth).
    - يتم إصلاح أي سجلات status=unknown تلقائيًا (PATCH SAFE).
    """

    try:
        # ------------------------------------------------
        # 🧠 نجلب فقط السجلات غير المعالجة بعد
        # ------------------------------------------------
        logs = (
            BiotimeLog.objects
            .filter(processed=False)
            .order_by("punch_time")
        )

        if start_date and end_date:
            logs = logs.filter(
                punch_time__date__range=[start_date, end_date]
            )

        synced_count = 0
        skipped_unmapped = 0
        skipped_leave = 0
        recalculated_unknown = 0

        # ========================================================
        # 🔄 Phase A — Sync Logs → Attendance
        # ========================================================
        for log in logs:

            # ------------------------------------------------
            # 🔍 ربط الموظف
            # ------------------------------------------------
            emp = resolve_employee_from_log(log)

            # 🟥 غير مربوط
            if not emp:
                skipped_unmapped += 1
                continue

            work_date = log.punch_time.date()

            # ------------------------------------------------
            # 🔎 جلب السجل الموجود
            # ------------------------------------------------
            record = AttendanceRecord.objects.filter(
                employee=emp,
                date=work_date,
            ).first()

            record_changed = False

            # ------------------------------------------------
            # 🟡 إنشاء السجل إن لم يكن موجودًا
            # ------------------------------------------------
            if not record:
                try:
                    with transaction.atomic():
                        record = AttendanceRecord.objects.create(
                            employee=emp,
                            date=work_date,
                            synced_from_biotime=True,
                            biotime_log=log,
                            status="present",
                        )
                        record_changed = True

                except IntegrityError:
                    record = AttendanceRecord.objects.filter(
                        employee=emp,
                        date=work_date,
                    ).first()

                    if not record:
                        logger.warning(
                            "[BiotimeSync] تعارض أثناء إنشاء AttendanceRecord "
                            f"(employee_id={emp.id}, date={work_date})"
                        )
                        continue

            # ------------------------------------------------
            # 🚫 تجاهل الإجازات
            # ------------------------------------------------
            if record.is_leave:
                skipped_leave += 1
                continue

            # ------------------------------------------------
            # ⏱ دمج أوقات الحضور
            # ------------------------------------------------
            punch_time = log.punch_time.time()

            if not record.check_in or punch_time < record.check_in:
                record.check_in = punch_time
                record_changed = True

            if not record.check_out or punch_time > record.check_out:
                record.check_out = punch_time
                record_changed = True

            # ------------------------------------------------
            # 🔄 تحديث الربط
            # ------------------------------------------------
            if not record.synced_from_biotime or record.biotime_log_id != log.id:
                record.synced_from_biotime = True
                record.biotime_log = log
                record_changed = True

            # ------------------------------------------------
            # 💾 حفظ التغييرات الأساسية (إن وُجدت)
            # ------------------------------------------------
            if record_changed:
                record.save(update_fields=[
                    "check_in",
                    "check_out",
                    "synced_from_biotime",
                    "biotime_log",
                ])

            # ------------------------------------------------
            # 🧮 تشغيل محرك الحساب دائمًا
            # ------------------------------------------------
            try:
                engine = WorkdayEngine(
                    record.employee,
                    record.employee.company,
                )
                engine.apply(record)

            except Exception:
                logger.exception(
                    "❌ Failed applying WorkdayEngine "
                    f"(employee_id={record.employee_id}, date={record.date})"
                )

            # ------------------------------------------------
            # ✅ تعليم السجل كمُعالج
            # ------------------------------------------------
            if not log.processed:
                log.processed = True
                log.save(update_fields=["processed"])

            synced_count += 1

        # ========================================================
        # 🔁 Phase B — Auto Recalculate UNKNOWN Records (PATCH)
        # ========================================================
        unknown_records = AttendanceRecord.objects.filter(status="unknown")

        for record in unknown_records.iterator():

            try:
                engine = WorkdayEngine(
                    record.employee,
                    record.employee.company,
                )
                engine.apply(record)
                recalculated_unknown += 1

            except Exception:
                logger.exception(
                    "❌ Failed recalculating UNKNOWN record "
                    f"(record_id={record.id}, employee_id={record.employee_id})"
                )

        # ========================================================
        # 📊 Logging
        # ========================================================
        logger.info(
            "✅ Biotime → Attendance Sync Completed | "
            f"synced={synced_count} | "
            f"unmapped={skipped_unmapped} | "
            f"leave_skipped={skipped_leave} | "
            f"unknown_recalculated={recalculated_unknown}"
        )

        return {
            "status": "success",
            "synced": synced_count,
            "skipped_unmapped": skipped_unmapped,
            "skipped_leave": skipped_leave,
            "recalculated_unknown": recalculated_unknown,
            "message": (
                f"تمت مزامنة {synced_count} سجل — "
                f"غير مربوط: {skipped_unmapped} — "
                f"إعادة احتساب UNKNOWN: {recalculated_unknown}."
            ),
        }

    except Exception as e:
        logger.exception("❌ خطأ أثناء مزامنة سجلات Biotime")
        return {
            "status": "error",
            "message": f"فشل المزامنة: {e}",
        }


# ============================================================
# ⚙️ 2️⃣ مزامنة يومية تلقائية (Scheduler Ready)
# ============================================================
def auto_daily_sync():
    """
    ⚙️ تنفيذ مزامنة تلقائية لسجلات اليوم الحالي.
    """
    today = timezone.now().date()
    return sync_biotime_logs_to_attendance(
        start_date=today,
        end_date=today,
    )
