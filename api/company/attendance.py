#حجم الملف كبي حددمكان التعديل ماهو قبل و ماهو بعده  وارسلي البلوك المعدل او المضاف  كاملا وحدد مكانه


# ============================================================
# 📊 Company Attendance APIs — FINAL (IP LOCATION FIXED)
# Primey HR Cloud
# ============================================================

import logging
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError   # ✅ NEW
from attendance_center.serializers.constants import ATTENDANCE_STATUS_AR


from attendance_center.models import (
    AttendanceRecord,
    WorkSchedule,
)

# 🟦 Status Arabic Mapping
from attendance_center.serializers.constants import ATTENDANCE_STATUS_AR

# ============================================================
# 🏢 Company Attendance Policy (SAFE OPTIONAL IMPORT)
# ============================================================

try:
    from attendance_center.models import AttendancePolicy
    POLICY_ENABLED = True
except ImportError:
    AttendancePolicy = None
    POLICY_ENABLED = False


from attendance_center.services.sync_biotime_to_attendance import (
    sync_biotime_logs_to_attendance,
)

from biotime_center.sync_service import sync_logs
from biotime_center.models import BiotimeLog

from company_manager.models import CompanyUser
from employee_center.models import Employee

logger = logging.getLogger(__name__)


# ============================================================
# 🔐 Resolve Company (SAFE)
# ============================================================

def _resolve_company(request):
    cu = (
        CompanyUser.objects
        .select_related("company")
        .filter(user=request.user, is_active=True)
        .order_by("-id")
        .first()
    )
    return cu.company if cu else None

# ============================================================
# 🏢 Company Attendance Policy — Company Level (READ / UPDATE)
# ============================================================

@login_required
@require_http_methods(["GET", "PUT"])
def company_attendance_policy(request):
    """
    Company Level Attendance Policy
    - Weekly Off (weekend_days)
    - Grace Minutes
    SAFE:
    - لا يكسر النظام لو الموديل غير موجود
    """

    if not POLICY_ENABLED:
        return JsonResponse({
            "status": "disabled",
            "message": "Company Attendance Policy غير مفعلة بعد."
        }, status=200)

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    policy, _ = AttendancePolicy.objects.get_or_create(
        company=company,
        defaults={
            "weekend_days": "fri,sat",
            "grace_minutes": 15,
        }
    )

    # =========================
    # 📄 READ
    # =========================
    if request.method == "GET":
        return JsonResponse({
            "status": "success",
            "policy": {
                "weekend_days": policy.weekend_days,
                "weekend_days_ar": (
                    policy.get_weekend_days_ar_display()
                    if hasattr(policy, "get_weekend_days_ar_display")
                    else policy.weekend_days
                ),
                "grace_minutes": policy.grace_minutes,
            }
        })

    # =========================
    # ✏️ UPDATE
    # =========================
    try:
        body = json.loads(request.body or "{}")

        updated_fields = []

        if "weekend_days" in body:
            policy.weekend_days = body["weekend_days"]
            updated_fields.append("weekend_days")

        if "grace_minutes" in body:
            policy.grace_minutes = body["grace_minutes"]
            updated_fields.append("grace_minutes")

        if updated_fields:
            policy.save(update_fields=updated_fields)

        logger.info(
            "CompanyAttendancePolicy updated | company=%s | fields=%s",
            company.id,
            updated_fields,
        )

        return JsonResponse({
            "status": "success",
            "updated_fields": updated_fields,
        })

    except ValidationError as ve:
        return JsonResponse({
            "status": "error",
            "message": str(ve),
        }, status=400)

    except Exception as exc:
        logger.exception("❌ Failed updating CompanyAttendancePolicy")
        return JsonResponse({
            "status": "error",
            "message": "فشل تحديث سياسة الحضور.",
            "exception": str(exc),
        }, status=500)

# ============================================================
# 📊 Dashboard Snapshot
# ============================================================

@login_required
@require_http_methods(["GET"])
def attendance_dashboard(request):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    qs = AttendanceRecord.objects.filter(
        employee__company=company
    )

    today_date = timezone.now().date()
    today = qs.filter(date=today_date)

    data = {
        "today": {
            "present": today.filter(status="present").count(),
            "absent": today.filter(status="absent").count(),
            "late": today.filter(status="late").count(),
            "leave": today.filter(status="leave").count(),
        },
        "total_records": qs.count(),
    }

    return JsonResponse({"status": "success", "data": data})



# ============================================================
# 🔄 Manual Biotime Sync (SMART PIPELINE)
# ============================================================

@login_required
@require_http_methods(["POST"])
def attendance_sync(request):
    """
    Smart Manual Sync Pipeline:
    1) Incremental sync from Biotime → BiotimeLog
    2) Map BiotimeLog → AttendanceRecord
    3) Return detailed metrics for UI
    """

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)
    # =========================
    # 🔐 Biotime Settings Guard
    # =========================
    if not hasattr(company, "biotime_settings") or not company.biotime_settings.exists():
        return JsonResponse({
        "status": "error",
        "message": "لا توجد إعدادات Biotime لهذه الشركة.",
        }, status=400)


    try:
        logs_result = sync_logs()

        if logs_result.get("status") != "success":
            logger.warning("Biotime sync failed: %s", logs_result)

            return JsonResponse({
                "status": "error",
                "stage": "biotime_sync",
                "message": logs_result.get("message"),
            }, status=500)

        attendance_result = sync_biotime_logs_to_attendance()

        response = {
            "status": "success",
            "biotime": {
                "new": logs_result.get("new"),
                "updated": logs_result.get("updated"),
                "total": logs_result.get("total"),
                "start_date": logs_result.get("start_date"),
            },
            "attendance": {
                "synced": attendance_result.get("synced"),
                "skipped": attendance_result.get("skipped"),
            },
            "message": "✔ تمت مزامنة الحركات وربطها بنجاح.",
        }

        logger.info(
            "Attendance Manual Sync Completed | biotime=%s | attendance=%s",
            logs_result,
            attendance_result,
        )

        return JsonResponse(response)

    except Exception as exc:
        logger.exception("❌ Attendance Manual Sync Fatal Error")

        return JsonResponse({
            "status": "error",
            "stage": "internal",
            "message": "حدث خطأ غير متوقع أثناء تنفيذ المزامنة.",
            "exception": str(exc),
        }, status=500)


# ============================================================
# 🧩 Unmapped Biotime Logs (STAGING — READ ONLY)
# ============================================================

@login_required
@require_http_methods(["GET"])
def attendance_unmapped_logs(request):
    """
    📌 يعرض سجلات Biotime التي لا يوجد لها موظف مربوط
    ولا تم تحويلها إلى AttendanceRecord.
    """

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    try:
        mapped_codes = (
            Employee.objects
            .filter(company=company)
            .exclude(Q(biotime_code__isnull=True) | Q(biotime_code=""))
            .values_list("biotime_code", flat=True)
        )

        mapped_codes = {str(code).strip() for code in mapped_codes if code}

        used_codes = (
            AttendanceRecord.objects
            .filter(employee__company=company)
            .exclude(Q(employee__biotime_code__isnull=True) | Q(employee__biotime_code=""))
            .values_list("employee__biotime_code", flat=True)
        )

        used_codes = {str(code).strip() for code in used_codes if code}

        excluded_codes = mapped_codes.union(used_codes)

        logs = (
            BiotimeLog.objects
            .filter(company=company)   # ✅ FIX: Company Scoped
            .exclude(Q(employee_code__isnull=True) | Q(employee_code=""))
            .exclude(employee_code__in=excluded_codes)
            .order_by("-punch_time")[:300]
        )


        payload = [
            {
                "id": log.id,
                "employee_code": str(log.employee_code).strip(),
                "punch_time": log.punch_time,
                "device_sn": log.device_sn,
                "terminal_alias": log.terminal_alias,
                "device_ip": getattr(log, "device_ip", None),
                "raw_id": log.log_id,
            }
            for log in logs
        ]

        return JsonResponse({
            "status": "success",
            "count": len(payload),
            "records": payload,
        })

    except Exception as exc:
        logger.exception("❌ Failed loading unmapped Biotime logs")

        return JsonResponse({
            "status": "error",
            "message": "فشل تحميل السجلات غير المربوطة.",
            "exception": str(exc),
        }, status=500)
from datetime import timedelta

# ============================================================
# 📊 Attendance Reports — Preview (READ ONLY + CORRECT HOURS)
# ============================================================

@login_required
@require_http_methods(["GET"])
def attendance_reports_preview(request):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    try:
        filters = Q(employee__company=company)

        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")
        status = request.GET.get("status")

        if from_date:
            filters &= Q(date__gte=from_date)
        if to_date:
            filters &= Q(date__lte=to_date)
        if status and status != "all":
            filters &= Q(status=status)

        qs = (
            AttendanceRecord.objects
            .filter(filters)
            .select_related("employee", "biotime_log")
            .order_by("-date")[:1000]
        )

        rows = []

        for r in qs:
            biotime = r.biotime_log

            # ===============================
            # ⏱️ CORRECT TIME CALCULATION
            # (TimeField SAFE)
            # ===============================
            work_hours = "00:00"

            if r.check_in and r.check_out:
                try:
                    in_minutes = r.check_in.hour * 60 + r.check_in.minute
                    out_minutes = r.check_out.hour * 60 + r.check_out.minute

                    total_minutes = max(0, out_minutes - in_minutes)

                    hours = total_minutes // 60
                    minutes = total_minutes % 60

                    work_hours = f"{hours:02d}:{minutes:02d}"
                except Exception:
                    work_hours = "00:00"

            rows.append({
                "employee": r.employee.full_name,
                "date": r.date,

                "status": r.status,

                "check_in": r.check_in,
                "check_out": r.check_out,

                # ✅ SOURCE OF TRUTH
                "work_hours": work_hours,

                "device_name": biotime.terminal_alias if biotime else None,
                "device_sn": biotime.device_sn if biotime else None,
                "location": getattr(biotime, "device_ip", None) if biotime else None,
            })

        return JsonResponse({
            "status": "success",
            "count": len(rows),
            "rows": rows,
        })

    except Exception as exc:
        logger.exception("❌ Attendance report failed")
        return JsonResponse({
            "status": "error",
            "message": "فشل تحميل تقرير الحضور",
        }, status=500)

# ============================================================
# 📄 Attendance Records (READ ONLY)
# ============================================================

@login_required
@require_http_methods(["GET"])
def attendance_records(request):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    records = (
        AttendanceRecord.objects
        .filter(employee__company=company)
        .select_related("employee", "biotime_log")
        .order_by("-date")[:500]
    )

    payload = []

    for r in records:
        biotime = r.biotime_log
        status_en = r.status

        payload.append({
            "id": r.id,

            # 👤 Employee
            "employee": r.employee.full_name,
            "employee_name": r.employee.full_name,
            "employee_id": r.employee.id,

            # 📅 Attendance
            "date": r.date,

            # 🔹 Status
            "status": status_en,  # English (Source of Truth)
            "status_ar": ATTENDANCE_STATUS_AR.get(status_en, status_en),

            # ⏰ Times
            "check_in": r.check_in,
            "check_out": r.check_out,

            # 🧮 Calculated (FROM WorkdayEngine — READ ONLY)
            "actual_hours": r.actual_hours,
            "late_minutes": r.late_minutes,
            "overtime_minutes": r.overtime_minutes,

            # 🖥 Device Info
            "device_name": (
                biotime.terminal_alias
                if biotime and biotime.terminal_alias
                else None
            ),
            "device_sn": (
                biotime.device_sn
                if biotime and biotime.device_sn
                else None
            ),

            # 🌐 Location (Device IP)
            "location": (
                biotime.device_ip
                if biotime and getattr(biotime, "device_ip", None)
                else None
            ),
        })

    return JsonResponse({
        "status": "success",
        "records": payload,
    })

# ============================================================
# 👤 Employee Attendance Preview (READ ONLY + STATUS AR)
# ============================================================

@login_required
@require_http_methods(["GET"])
def employee_attendance_preview(request, employee_id):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    try:
        employee = (
            Employee.objects
            .filter(id=employee_id, company=company)
            .first()
        )

        if not employee:
            return JsonResponse({"error": "EMPLOYEE_NOT_FOUND"}, status=404)

        limit = int(request.GET.get("limit", 50))

        qs = (
            AttendanceRecord.objects
            .filter(employee=employee)
            .select_related("biotime_log")
            .order_by("-date", "-check_in")[:limit]
        )

        records = []

        for r in qs:
            biotime = r.biotime_log
            status_en = r.status

            records.append({
                "id": r.id,
                "date": r.date,

                # 🔹 Status
                "status": status_en,
                "status_ar": ATTENDANCE_STATUS_AR.get(status_en, status_en),

                "check_in": r.check_in,
                "check_out": r.check_out,
                "work_hours": r.actual_hours,

                "device_name": biotime.terminal_alias if biotime else None,
                "device_sn": biotime.device_sn if biotime else None,
                "location": getattr(biotime, "device_ip", None) if biotime else None,
                "source": "biotime" if biotime else "attendance",
            })

        return JsonResponse({
            "status": "success",
            "employee_id": employee.id,
            "employee_name": employee.full_name,
            "count": len(records),
            "records": records,
        })

    except Exception as exc:
        logger.exception("❌ Failed loading employee attendance preview")
        return JsonResponse({
            "status": "error",
            "message": "فشل تحميل حركات الموظف.",
            "exception": str(exc),
        }, status=500)

# ============================================================
# 🕒 WorkSchedule CRUD APIs — Phase F.5.1 (Hardened)
# ============================================================

@login_required
@require_http_methods(["GET", "POST"])
def work_schedules(request):
    """
    GET  → List schedules
    POST → Create schedule
    """

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    # =========================
    # 📄 LIST
    # =========================
    if request.method == "GET":
        schedules = WorkSchedule.objects.filter(company=company).order_by("name")

        payload = [{
            "id": s.id,
            "name": s.name,
            "schedule_type": s.schedule_type,
            "period1_start": s.period1_start,
            "period1_end": s.period1_end,
            "period2_start": s.period2_start,
            "period2_end": s.period2_end,

            # 🔹 Raw (Backward compatible)
            "weekend_days": s.weekend_days,

            # 🔹 Arabic display for UI
            "weekend_days_ar": s.get_weekend_days_ar_display(),

            "target_daily_hours": s.target_daily_hours,
            "allow_night_overlap": s.allow_night_overlap,
            "early_arrival_minutes": s.early_arrival_minutes,
            "early_exit_minutes": s.early_exit_minutes,
            "is_active": s.is_active,
        } for s in schedules]

        return JsonResponse({"status": "success", "schedules": payload})

    # =========================
    # ➕ CREATE
    # =========================
    try:
        body = json.loads(request.body or "{}")

        name = (body.get("name") or "").strip()
        if not name:
            return JsonResponse({"error": "NAME_REQUIRED"}, status=400)

        try:
            schedule = WorkSchedule.objects.create(
                company=company,
                name=name,
                schedule_type=body.get("schedule_type", "FULL_TIME"),
                period1_start=body.get("period1_start"),
                period1_end=body.get("period1_end"),
                period2_start=body.get("period2_start"),
                period2_end=body.get("period2_end"),
                weekend_days=body.get("weekend_days", "fri,sat"),
                target_daily_hours=body.get("target_daily_hours"),
                allow_night_overlap=body.get("allow_night_overlap", True),
                early_arrival_minutes=body.get("early_arrival_minutes", 0),
                early_exit_minutes=body.get("early_exit_minutes", 0),
                is_active=True,
            )
        except ValidationError as ve:
            return JsonResponse({
                "status": "error",
                "message": str(ve),
            }, status=400)

        logger.info("WorkSchedule created | id=%s | company=%s", schedule.id, company.id)
        return JsonResponse({"status": "success", "id": schedule.id})

    except Exception as exc:
        logger.exception("❌ Failed creating WorkSchedule")
        return JsonResponse({
            "status": "error",
            "message": "فشل إنشاء جدول الدوام.",
            "exception": str(exc),
        }, status=500)


@login_required
@require_http_methods(["PUT", "DELETE"])
def work_schedule_detail(request, schedule_id):
    """
    PUT    → Update schedule
    DELETE → Delete schedule (guarded)
    """

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    schedule = WorkSchedule.objects.filter(
        id=schedule_id,
        company=company
    ).first()

    if not schedule:
        return JsonResponse({"error": "NOT_FOUND"}, status=404)

    # =========================
    # ✏️ UPDATE
    # =========================
    if request.method == "PUT":
        try:
            body = json.loads(request.body or "{}")

            editable_fields = [
                "name",
                "schedule_type",
                "period1_start",
                "period1_end",
                "period2_start",
                "period2_end",
                "weekend_days",
                "target_daily_hours",
                "allow_night_overlap",
                "early_arrival_minutes",
                "early_exit_minutes",
                "is_active",
            ]

            updated = []

            for field in editable_fields:
                if field in body:
                    setattr(schedule, field, body[field])
                    updated.append(field)

            if updated:
                try:
                    schedule.save(update_fields=updated)
                except ValidationError as ve:
                    return JsonResponse({
                        "status": "error",
                        "message": str(ve),
                    }, status=400)

            logger.info("WorkSchedule updated | id=%s", schedule.id)
            return JsonResponse({"status": "success"})

        except Exception as exc:
            logger.exception("❌ Failed updating WorkSchedule")
            return JsonResponse({
                "status": "error",
                "message": "فشل تحديث جدول الدوام.",
                "exception": str(exc),
            }, status=500)

    # =========================
    # 🗑️ DELETE (GUARDED)
    # =========================
    try:
        if Employee.objects.filter(default_work_schedule=schedule).exists():
            return JsonResponse({
                "status": "error",
                "message": "لا يمكن حذف جدول مرتبط بموظفين.",
            }, status=409)

        schedule.delete()
        logger.info("WorkSchedule deleted | id=%s", schedule_id)

        return JsonResponse({"status": "success"})

    except Exception as exc:
        logger.exception("❌ Failed deleting WorkSchedule")
        return JsonResponse({
            "status": "error",
            "message": "فشل حذف جدول الدوام.",
            "exception": str(exc),
        }, status=500)


@login_required
@require_http_methods(["POST"])
def work_schedule_toggle(request, schedule_id):
    """
    🔁 Activate / Deactivate Schedule
    """

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    schedule = WorkSchedule.objects.filter(
        id=schedule_id,
        company=company
    ).first()

    if not schedule:
        return JsonResponse({"error": "NOT_FOUND"}, status=404)

    schedule.is_active = not schedule.is_active
    schedule.save(update_fields=["is_active"])

    logger.info(
        "WorkSchedule toggled | id=%s | active=%s",
        schedule.id,
        schedule.is_active,
    )

    return JsonResponse({
        "status": "success",
        "is_active": schedule.is_active,
    })


# ============================================================
# 🔗 Assign Work Schedule To Employee — Phase F.3
# ============================================================

@login_required
@require_http_methods(["POST"])
def employee_assign_work_schedule(request):
    """
    🎯 Assign active WorkSchedule to Employee (Idempotent + Safe)

    Payload:
    {
        "employee_id": 8,
        "schedule_id": 1
    }
    """

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    try:
        body = json.loads(request.body or "{}")

        employee_id = body.get("employee_id")
        schedule_id = body.get("schedule_id")

        if not employee_id or not schedule_id:
            return JsonResponse({
                "status": "error",
                "message": "employee_id و schedule_id مطلوبة.",
            }, status=400)

        # =========================
        # 👤 Load Employee (Company Scoped)
        # =========================
        employee = (
            Employee.objects
            .filter(id=employee_id, company=company)
            .select_related("default_work_schedule")
            .first()
        )

        if not employee:
            return JsonResponse({
                "status": "error",
                "message": "الموظف غير موجود.",
            }, status=404)

        # =========================
        # 🕒 Load Schedule (Active + Company Scoped)
        # =========================
        schedule = (
            WorkSchedule.objects
            .filter(
                id=schedule_id,
                company=company,
                is_active=True,
            )
            .first()
        )

        if not schedule:
            return JsonResponse({
                "status": "error",
                "message": "جدول الدوام غير موجود أو غير نشط.",
            }, status=404)

        # =========================
        # ♻️ Idempotency Guard
        # =========================
        if employee.default_work_schedule_id == schedule.id:
            return JsonResponse({
                "status": "success",
                "message": "الجدول مربوط مسبقًا بهذا الموظف.",
                "employee_id": employee.id,
                "schedule_id": schedule.id,
                "idempotent": True,
            })

        # =========================
        # 🔗 Assign
        # =========================
        employee.default_work_schedule = schedule
        employee.save(update_fields=["default_work_schedule"])

        logger.info(
            "Employee WorkSchedule assigned | employee=%s | schedule=%s",
            employee.id,
            schedule.id,
        )

        return JsonResponse({
            "status": "success",
            "message": "تم ربط جدول الدوام بالموظف بنجاح.",
            "employee_id": employee.id,
            "schedule_id": schedule.id,
            "schedule_type": schedule.schedule_type,
            "target_daily_hours": schedule.target_daily_hours,
        })

    except Exception as exc:
        logger.exception("❌ Failed assigning WorkSchedule to Employee")
        return JsonResponse({
            "status": "error",
            "message": "حدث خطأ أثناء ربط جدول الدوام.",
            "exception": str(exc),
        }, status=500)