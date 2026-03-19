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
from attendance_center.services.workday_engine import WorkdayEngine
from datetime import datetime, timedelta
from django.db import models
from whatsapp_center.services import send_attendance_status_whatsapp_notifications

from attendance_center.models import (
    AttendanceRecord,
    WorkSchedule,
)
# ============================================================
# 🔗 Cross App Imports (FIX 500 Errors)
# ============================================================

from company_manager.models import CompanyUser
from employee_center.models import Employee
from biotime_center.models import BiotimeLog

from biotime_center.sync_service import sync_logs
from attendance_center.services.sync_biotime_to_attendance import (
    sync_biotime_logs_to_attendance,
)

from attendance_center.models import (
    AttendanceRecord,
    WorkSchedule,
)

# 🟦 Status Arabic Mapping
from attendance_center.serializers.constants import ATTENDANCE_STATUS_AR

# ============================================================
# 🏢 Company Attendance Setting (NEW CLEAN MODEL)
# ============================================================

from attendance_center.models import CompanyAttendanceSetting

POLICY_ENABLED = True  # أصبح دائمًا مفعل لأن الموديل موجود رسميًا


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

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import transaction
import json
import logging

logger = logging.getLogger(__name__)

# ============================================================
# 📊 company attendance policy
# ============================================================

@login_required
@require_http_methods(["GET", "PUT", "PATCH"])
def company_attendance_policy(request):
    """
    Company Level Attendance Setting

    READ:
        - grace_minutes
        - late_after_minutes
        - absence_after_minutes
        - auto_absent_if_no_checkin

    UPDATE:
        - same fields only

    SAFE:
        - Multi-Tenant Safe
        - Production Ready
    """

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    # 🔹 Clean Model — No weekend here
    policy, _ = CompanyAttendanceSetting.objects.get_or_create(
        company=company,
        defaults={
            "grace_minutes": 15,
            "late_after_minutes": 30,
            "absence_after_minutes": 180,
            "auto_absent_if_no_checkin": True,
        }
    )

    # =========================================================
    # 📄 READ
    # =========================================================
    if request.method == "GET":
        return JsonResponse({
            "status": "success",
            "policy": {
                "grace_minutes": policy.grace_minutes,
                "late_after_minutes": policy.late_after_minutes,
                "absence_after_minutes": policy.absence_after_minutes,
                "auto_absent_if_no_checkin": policy.auto_absent_if_no_checkin,
                "overtime_enabled": policy.overtime_enabled,
            }
        })

    # =========================================================
    # ✏️ UPDATE
    # =========================================================
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")

        if not isinstance(body, dict):
            return JsonResponse({
                "status": "error",
                "message": "بيانات غير صالحة."
            }, status=400)

        updated_fields = []

        # -------------------------
        # Grace Minutes
        # -------------------------
        if "grace_minutes" in body:
            try:
                grace = int(body["grace_minutes"])
                if grace < 0:
                    raise ValueError
                policy.grace_minutes = grace
                updated_fields.append("grace_minutes")
            except (ValueError, TypeError):
                return JsonResponse({
                    "status": "error",
                    "message": "Grace Minutes يجب أن يكون رقم صحيح موجب."
                }, status=400)

        # -------------------------
        # Late Threshold
        # -------------------------
        if "late_after_minutes" in body:
            try:
                value = int(body["late_after_minutes"])
                if value < 0:
                    raise ValueError
                policy.late_after_minutes = value
                updated_fields.append("late_after_minutes")
            except (ValueError, TypeError):
                return JsonResponse({
                    "status": "error",
                    "message": "Late After Minutes غير صالح."
                }, status=400)

        # -------------------------
        # Absence Threshold
        # -------------------------
        if "absence_after_minutes" in body:
            try:
                value = int(body["absence_after_minutes"])
                if value < 0:
                    raise ValueError
                policy.absence_after_minutes = value
                updated_fields.append("absence_after_minutes")
            except (ValueError, TypeError):
                return JsonResponse({
                    "status": "error",
                    "message": "Absence After Minutes غير صالح."
                }, status=400)

        # -------------------------
        # Auto Absent Flag
        # -------------------------
        if "auto_absent_if_no_checkin" in body:
            policy.auto_absent_if_no_checkin = bool(
                body["auto_absent_if_no_checkin"]
            )
            updated_fields.append("auto_absent_if_no_checkin")
        # -------------------------
        # Overtime Enabled Flag
        # -------------------------
        if "overtime_enabled" in body:
            policy.overtime_enabled = bool(
                body["overtime_enabled"]
            )
            updated_fields.append("overtime_enabled")

        if updated_fields:
            policy.save(update_fields=updated_fields)

        logger.info(
            "CompanyAttendanceSetting updated | company=%s | fields=%s",
            company.id,
            updated_fields,
        )

        # 🔥 IMPORTANT: Always return fresh policy for frontend sync
        return JsonResponse({
            "status": "success",
            "policy": {
                "grace_minutes": policy.grace_minutes,
                "late_after_minutes": policy.late_after_minutes,
                "absence_after_minutes": policy.absence_after_minutes,
                "auto_absent_if_no_checkin": policy.auto_absent_if_no_checkin,
                "overtime_enabled": policy.overtime_enabled,
            }
        })
    
    except Exception:
        logger.exception("❌ Failed updating CompanyAttendanceSetting")
        return JsonResponse({
            "status": "error",
            "message": "فشل تحديث سياسة الحضور.",
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


# ============================================================
# 📊 Attendance Reports — Preview V2 (ENGINE BASED + MERGED SCHEDULE)
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
            .filter(
                Q(employee__work_start_date__isnull=True) |
                Q(date__gte=models.F("employee__work_start_date"))
            )
            .select_related(
                "employee",
                "employee__default_work_schedule",
                "biotime_log",
            )
                .order_by("-date")[:1000]
            
        )

        rows = []
        today = timezone.localdate()

        for r in qs:
            biotime = r.biotime_log
            schedule = getattr(r.employee, "default_work_schedule", None)

            # =====================================================
            # 🕓 Schedule Mapping
            # =====================================================
            schedule_type = None
            schedule_label = None
            period_display = None

            if schedule:
                schedule_type = schedule.schedule_type

                if schedule.schedule_type == "FULL_TIME":
                    schedule_label = "دوام كامل"
                    if schedule.period1_start and schedule.period1_end:
                        period_display = (
                            f"{schedule.period1_start.strftime('%H:%M')} "
                            f"→ {schedule.period1_end.strftime('%H:%M')}"
                        )

                elif schedule.schedule_type == "PART_TIME":
                    schedule_label = "فترتين"
                    periods = []

                    if schedule.period1_start and schedule.period1_end:
                        periods.append(
                            f"{schedule.period1_start.strftime('%H:%M')} "
                            f"→ {schedule.period1_end.strftime('%H:%M')}"
                        )

                    if schedule.period2_start and schedule.period2_end:
                        periods.append(
                            f"{schedule.period2_start.strftime('%H:%M')} "
                            f"→ {schedule.period2_end.strftime('%H:%M')}"
                        )

                    period_display = "\n".join(periods) if periods else None

                elif schedule.schedule_type == "HOURLY":
                    schedule_label = "بالساعات"
                    if schedule.target_daily_hours:
                        period_display = (
                            f"{schedule.target_daily_hours} ساعات مطلوبة"
                        )

                else:
                    schedule_label = schedule.schedule_type

            # =====================================================
            # 🧠 Engine Results (Source of Truth)
            # =====================================================
            actual_hours = r.actual_hours if r.actual_hours is not None else 0
            late_minutes = r.late_minutes if r.late_minutes else 0
            overtime_minutes = r.overtime_minutes if r.overtime_minutes else 0

            # =====================================================
            # 🧠 Smart Display Status Layer (REPORT ONLY)
            # =====================================================
            display_status = r.status
            display_status_ar = ATTENDANCE_STATUS_AR.get(r.status, r.status)

            # ⚫ Terminated Employee (SAFE — Supports different Employee schemas)
            if r.employee.status and str(r.employee.status).upper() == "TERMINATED":
                display_status = "terminated"
                display_status_ar = "منتهي خدمة"

            # 🟣 Weekend
            elif schedule and schedule.is_weekend(r.date):
                display_status = "weekend"
                display_status_ar = "عطلة"

            # ⏳ Before Start (Today Only)
            elif (
                r.date == today
                and not r.check_in
                and not r.is_finalized
                and schedule
                and schedule.period1_start
            ):
                now_time = timezone.localtime().time()
                if now_time < schedule.period1_start:
                    display_status = "before_start"
                    display_status_ar = "قبل المباشرة"

            # =====================================================
            # 📦 Append Row
            # =====================================================
            rows.append({
                # 👤 Employee
                "employee": r.employee.full_name,
                "employee_id": r.employee.id,
                "photo_url": r.employee.photo_url,

                # 📅 Date
                "date": r.date,

                # 🔹 Status (Smart Layer)
                "status": display_status,
                "status_ar": display_status_ar,

                # 🕓 Schedule
                "schedule_type": schedule_type,
                "schedule_label": schedule_label,
                "period_display": period_display,

                # ⏰ Times
                "check_in": r.check_in,
                "check_out": r.check_out,

                # 🧮 Engine Calculations
                "actual_hours": actual_hours,
                "late_minutes": late_minutes,
                "overtime_minutes": overtime_minutes,

                # 🌍 Location
                "location": (
                    biotime.device_ip
                    if biotime and getattr(biotime, "device_ip", None)
                    else None
                ),
            })

        return JsonResponse({
            "status": "success",
            "count": len(rows),
            "rows": rows,
        })

    except Exception:
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
# 🗓 Employee Schedule Preview (SMART — For Manual Entry UI)
# ============================================================

@login_required
@require_http_methods(["GET"])
def employee_schedule_preview(request):
    """
    Returns employee schedule snapshot for a specific date.

    Query Params:
        - employee_id
        - date (YYYY-MM-DD)

    Response:
    {
        schedule_type,
        periods: [],
        is_weekend,
        target_daily_hours
    }
    """

    from django.http import JsonResponse
    from django.utils.dateparse import parse_date

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    employee_id = request.GET.get("employee_id")
    date_str = request.GET.get("date")

    if not employee_id or not date_str:
        return JsonResponse({
            "status": "error",
            "message": "employee_id و date مطلوبة.",
        }, status=400)

    # ========================================================
    # 🔧 Clean Date (fix trailing slash issue)
    # ========================================================
    date_str = date_str.strip().rstrip("/")

    work_date = parse_date(date_str)
    if not work_date:
        return JsonResponse({
            "status": "error",
            "message": "تاريخ غير صالح.",
        }, status=400)

    # ========================================================
    # 👤 Get Employee
    # ========================================================
    employee = (
        Employee.objects
        .select_related("default_work_schedule")
        .filter(id=employee_id, company=company)
        .first()
    )

    if not employee:
        return JsonResponse({
            "status": "error",
            "message": "الموظف غير موجود.",
        }, status=404)

    schedule = employee.default_work_schedule

    if not schedule:
        return JsonResponse({
            "status": "success",
            "schedule_type": None,
            "periods": [],
            "is_weekend": False,
            "target_daily_hours": None,
        })

    # ========================================================
    # 🕒 Build Periods
    # ========================================================
    periods = []

    if schedule.schedule_type == "FULL_TIME":
        if schedule.period1_start and schedule.period1_end:
            periods.append({
                "start": schedule.period1_start.strftime("%H:%M"),
                "end": schedule.period1_end.strftime("%H:%M"),
            })

    elif schedule.schedule_type == "PART_TIME":
        if schedule.period1_start and schedule.period1_end:
            periods.append({
                "start": schedule.period1_start.strftime("%H:%M"),
                "end": schedule.period1_end.strftime("%H:%M"),
            })

        if schedule.period2_start and schedule.period2_end:
            periods.append({
                "start": schedule.period2_start.strftime("%H:%M"),
                "end": schedule.period2_end.strftime("%H:%M"),
            })

    elif schedule.schedule_type == "HOURLY":
        periods = []  # hourly has no fixed periods

    # ========================================================
    # 🟣 Weekend Detection (Safe)
    # ========================================================
    weekday_code = work_date.strftime("%a").lower()

    weekend_raw = schedule.weekend_days or ""
    weekend_days = weekend_raw.lower() if isinstance(weekend_raw, str) else ""

    is_weekend = weekday_code in weekend_days

    # ========================================================
    # ✅ Final Response
    # ========================================================
    return JsonResponse({
        "status": "success",
        "schedule_type": schedule.schedule_type,
        "periods": periods,
        "is_weekend": is_weekend,
        "target_daily_hours": (
            str(schedule.target_daily_hours)
            if getattr(schedule, "target_daily_hours", None)
            else None
        ),
    })

# ============================================================
# 🕒 WorkSchedule CRUD APIs — Phase F.5.1 (Hardened + Update Safe)
# ============================================================

@login_required
@require_http_methods(["GET", "POST"])
def work_schedules(request):
    """
    GET  → List schedules
    POST → Create OR Update schedule
    """

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    # ============================================================
    # 📄 LIST
    # ============================================================
    if request.method == "GET":
        schedules = WorkSchedule.objects.filter(
            company=company
        ).order_by("name")

        payload = [{
            "id": s.id,
            "name": s.name,
            "schedule_type": s.schedule_type,
            "period1_start": s.period1_start,
            "period1_end": s.period1_end,
            "period2_start": s.period2_start,
            "period2_end": s.period2_end,
            "weekend_days": s.weekend_days,
            "weekend_days_ar": s.get_weekend_days_ar_display(),
            "target_daily_hours": s.target_daily_hours,
            "allow_night_overlap": s.allow_night_overlap,
            "early_arrival_minutes": s.early_arrival_minutes,
            "early_exit_minutes": s.early_exit_minutes,
            "is_active": s.is_active,
        } for s in schedules]

        return JsonResponse({
            "status": "success",
            "schedules": payload
        })

    # ============================================================
    # ➕ CREATE / ✏️ UPDATE
    # ============================================================
    try:
        body = json.loads(request.body or "{}")

        name = (body.get("name") or "").strip()
        if not name:
            return JsonResponse({"error": "NAME_REQUIRED"}, status=400)

        schedule_id = body.get("id")

        # ========================================================
        # ✏️ UPDATE MODE
        # ========================================================
        if schedule_id:
            schedule = WorkSchedule.objects.filter(
                id=schedule_id,
                company=company
            ).first()

            if not schedule:
                return JsonResponse({"error": "NOT_FOUND"}, status=404)

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
            ]

            updated_fields = []

            for field in editable_fields:
                if field in body:
                    setattr(schedule, field, body.get(field))
                    updated_fields.append(field)

            schedule.save(update_fields=updated_fields)

            logger.info(
                "WorkSchedule updated | id=%s | company=%s",
                schedule.id,
                company.id
            )

            return JsonResponse({
                "status": "success",
                "mode": "updated",
                "id": schedule.id
            })

        # ========================================================
        # ➕ CREATE MODE
        # ========================================================
        try:
            schedule = WorkSchedule.objects.create(
                company=company,
                name=name,
                schedule_type=body.get("schedule_type", "FULL_TIME"),
                period1_start=body.get("period1_start"),
                period1_end=body.get("period1_end"),
                period2_start=body.get("period2_start"),
                period2_end=body.get("period2_end"),
                weekend_days=body.get("weekend_days", ""),
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

        logger.info(
            "WorkSchedule created | id=%s | company=%s",
            schedule.id,
            company.id
        )

        return JsonResponse({
            "status": "success",
            "mode": "created",
            "id": schedule.id
        })

    except Exception as exc:
        logger.exception("❌ Failed saving WorkSchedule")
        return JsonResponse({
            "status": "error",
            "message": "فشل حفظ جدول الدوام.",
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
    
# ============================================================
# 🟦 Manual Attendance Entry — Phase M1 (Safe + Finalization Aware)
# ============================================================

@login_required
@require_http_methods(["POST"])
def attendance_manual_entry(request):
    """
    Manual Attendance Entry (Single Employee)

    Payload:
    {
        "employee_id": 12,
        "date": "2026-02-18",
        "check_in": "09:05",      # optional
        "check_out": "17:10"      # optional
    }

    Features:
    - Multi-tenant safe
    - Respects Finalization
    - Uses WorkdayEngine as source of truth
    - Allows check-in only / check-out only
    """

    
    from django.utils.dateparse import parse_date, parse_time

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    try:
        body = json.loads(request.body or "{}")

        employee_id = body.get("employee_id")
        date_str = body.get("date")
        check_in_str = body.get("check_in")
        check_out_str = body.get("check_out")

        if not employee_id or not date_str:
            return JsonResponse({
                "status": "error",
                "message": "employee_id و date مطلوبة.",
            }, status=400)

        # =========================
        # 🔒 Resolve Employee (Company Scoped)
        # =========================
        employee = (
            Employee.objects
            .filter(id=employee_id, company=company)
            .first()
        )

        if not employee:
            return JsonResponse({
                "status": "error",
                "message": "الموظف غير موجود.",
            }, status=404)

        work_date = parse_date(date_str)
        if not work_date:
            return JsonResponse({
                "status": "error",
                "message": "تاريخ غير صالح.",
            }, status=400)

        # منع التاريخ المستقبلي
        if work_date > timezone.localdate():
            return JsonResponse({
                "status": "error",
                "message": "لا يمكن إدخال حركة بتاريخ مستقبلي.",
            }, status=400)

        # =========================
        # 📝 Get or Create Record
        # =========================
        record, _ = AttendanceRecord.objects.get_or_create(
            employee=employee,
            date=work_date,
        )

        # =========================
        # ⏱ Parse Times
        # =========================
        if check_in_str:
            t = parse_time(check_in_str)
            if not t:
                return JsonResponse({
                    "status": "error",
                    "message": "وقت دخول غير صالح.",
                }, status=400)
            record.check_in = t

        if check_out_str:
            t = parse_time(check_out_str)
            if not t:
                return JsonResponse({
                    "status": "error",
                    "message": "وقت خروج غير صالح.",
                }, status=400)
            record.check_out = t

        # =========================
        # 🔓 Handle Finalization
        # =========================
        was_finalized = record.is_finalized

        if was_finalized:
            record.is_finalized = False

        # حفظ أولي بدون تشغيل Engine
        record.save(skip_engine=True)

        # =========================
        # 🧠 Apply Engine (Force Mode)
        # =========================
        WorkdayEngine.apply(record, force=True)

        # =========================
        # 📲 WhatsApp Attendance Hook
        # يرسل فقط عند late / absent
        # =========================
        try:
            send_attendance_status_whatsapp_notifications(
                attendance_record=record,
                company=company,
                send_to_employee=True,
                send_to_user=True,
            )
        except Exception:
            logger.exception(
                "⚠ Attendance WhatsApp hook failed (manual_entry) | record_id=%s",
                record.id,
            )

        # =========================
        # 🔒 Re-Finalize if needed
        # =========================
        if was_finalized:
            record.is_finalized = True
            record.finalized_at = timezone.now()
            record.save(
                update_fields=["is_finalized", "finalized_at"],
                skip_engine=True,
            )
        logger.info(
            "Manual attendance entry | employee=%s | date=%s | finalized=%s",
            employee.id,
            work_date,
            was_finalized,
        )

        return JsonResponse({
            "status": "success",
            "employee_id": employee.id,
            "date": work_date,
            "check_in": record.check_in,
            "check_out": record.check_out,
            "actual_hours": record.actual_hours,
            "late_minutes": record.late_minutes,
            "overtime_minutes": record.overtime_minutes,
            "is_finalized": record.is_finalized,
        })

    except Exception as exc:
        logger.exception("❌ Manual attendance entry failed")
        return JsonResponse({
            "status": "error",
            "message": "فشل إدخال الحركة اليدوية.",
            "exception": str(exc),
        }, status=500)

@login_required
@require_http_methods(["POST"])
def attendance_manual_action(request):

    company = _resolve_company(request)
    if not company:
        return JsonResponse({"error": "NO_COMPANY"}, status=403)

    try:
        body = json.loads(request.body or "{}")

        mode = body.get("mode", "commit")
        employee_ids = body.get("employee_ids", [])
        date_str = body.get("date")
        check_in_raw = body.get("check_in")
        check_out_raw = body.get("check_out")
        force_reopen = bool(body.get("force_reopen", False))

        if not date_str:
            return JsonResponse({
                "status": "error",
                "message": "التاريخ مطلوب."
            }, status=400)

        work_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # =====================================================
        # 🔎 Resolve Employees
        # =====================================================
        if employee_ids == ["all"]:
            employees = Employee.objects.filter(company=company)
        else:
            employees = Employee.objects.filter(
                company=company,
                id__in=employee_ids
            )

        if not employees.exists():
            return JsonResponse({
                "status": "error",
                "message": "لا يوجد موظفين مطابقين."
            }, status=404)

        preview_rows = []
        updated = 0

        # =====================================================
        # 🔄 Loop Employees
        # =====================================================
        for emp in employees:

            schedule = getattr(emp, "default_work_schedule", None)
            schedule_type = schedule.schedule_type if schedule else None

            record = AttendanceRecord.objects.filter(
                employee=emp,
                date=work_date
            ).first()

            existing_in = record.check_in if record else None
            existing_out = record.check_out if record else None

            # ===============================
            # 🟡 PREVIEW
            # ===============================
            if mode == "preview":
                preview_rows.append({
                    "employee_id": emp.id,
                    "employee_name": emp.full_name,
                    "schedule_type": schedule_type,
                    "existing_check_in": existing_in,
                    "existing_check_out": existing_out,
                })
                continue

            # ===============================
            # 🟢 COMMIT
            # ===============================

            record, _ = AttendanceRecord.objects.get_or_create(
                employee=emp,
                date=work_date,
            )

            # 🔓 Reopen If Needed
            if hasattr(record, "is_finalized"):
                if record.is_finalized and force_reopen:
                    record.is_finalized = False
                    if hasattr(record, "finalized_at"):
                        record.finalized_at = None

            # -------------------------------------------------
            # 🟢 HOURLY (Use check-in/out like FULL_TIME)
            # -------------------------------------------------
            if schedule_type == "HOURLY":

                if check_in_raw:
                    record.check_in = datetime.strptime(
                        check_in_raw, "%H:%M"
                    ).time()

                if check_out_raw:
                    record.check_out = datetime.strptime(
                        check_out_raw, "%H:%M"
                    ).time()

            # -------------------------------------------------
            # 🟢 FULL_TIME + FLEXIBLE
            # -------------------------------------------------
            else:
                if check_in_raw:
                    record.check_in = datetime.strptime(
                        check_in_raw, "%H:%M"
                    ).time()

                if check_out_raw:
                    record.check_out = datetime.strptime(
                        check_out_raw, "%H:%M"
                    ).time()

            record.save(skip_engine=True)

            # 🔁 Apply Engine (Force Mode — Idempotent Safe)
            try:
                WorkdayEngine.apply(record, force=True)
            except Exception:
                logger.exception(
                    "❌ Manual Engine Apply Failed | record_id=%s",
                    record.id
                )
            else:
                # =========================
                # 📲 WhatsApp Attendance Hook
                # يرسل فقط عند late / absent
                # =========================
                try:
                    send_attendance_status_whatsapp_notifications(
                        attendance_record=record,
                        company=company,
                        send_to_employee=True,
                        send_to_user=True,
                    )
                except Exception:
                    logger.exception(
                        "⚠ Attendance WhatsApp hook failed (manual_action) | record_id=%s",
                        record.id,
                    )

            updated += 1
        # ===============================
        # 🔁 Return
        # ===============================
        if mode == "preview":
            return JsonResponse({
                "status": "success",
                "mode": "preview",
                "count": len(preview_rows),
                "rows": preview_rows,
            })

        return JsonResponse({
            "status": "success",
            "mode": "commit",
            "updated_records": updated,
        })

    except Exception as exc:
        logger.exception("❌ Manual Attendance Action Failed")
        return JsonResponse({
            "status": "error",
            "message": "فشل تنفيذ الحركة اليدوية.",
            "exception": str(exc),
        }, status=500)
