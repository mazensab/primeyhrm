# ======================================================
# 👥 Employee API — Company Scope
# Primey HR Cloud
# Version: D3.10 Ultra Pro (BIOTIME DETAILS READ-ONLY 🔍 + MULTI-BRANCH ✅)
# ======================================================

import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt

from employee_center.models import (
    Employee,
    EmploymentInfo,
    EmploymentHistory,
)

from company_manager.models import (
    CompanyUser,
    CompanyRole,
    CompanyDepartment,
    JobTitle,
    CompanyBranch,   # ✅ Multi-Branch
)

# 🧬 Biotime
from biotime_center.models import BiotimeEmployee

# 🧠 Attendance Mapping
from attendance_center.services.sync_biotime_to_attendance import (
    sync_biotime_logs_to_attendance,
)
# 🕒 Work Schedules
from attendance_center.models import WorkSchedule

logger = logging.getLogger(__name__)
User = get_user_model()

# ======================================================
# Helpers
# ======================================================

def _parse_body(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}

def _clean_str(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None

def _resolve_company_user(request) -> CompanyUser | None:
    """
    🔐 Resolve CompanyUser Context (SAFE)
    """
    return (
        CompanyUser.objects
        .select_related("company", "user")
        .filter(
            user=request.user,
            is_active=True,
            company__isnull=False,
        )
        .order_by("-id")
        .first()
    )

def _resolve_company(request):
    cu = _resolve_company_user(request)
    return cu.company if cu else None

def _map_user_status(user_is_active: bool) -> str:
    """
    🔒 SINGLE SOURCE OF TRUTH — USER STATUS
    """
    return "ACTIVE" if user_is_active else "INACTIVE"


def _serialize_biotime_employee(bio: BiotimeEmployee | None):
    """
    🧬 Serialize BiotimeEmployee (READ ONLY | SAFE)
    """
    if not bio:
        return None

    try:
        return {
            "employee_id": bio.employee_id,
            "full_name": bio.full_name,
            "is_active": bio.is_active,
            "department": bio.department,
            "enrolled_fingers": bio.enrolled_fingers,
            "card_number": bio.card_number,
            "photo_url": bio.photo_url,
            "created_at": bio.created_at,
            "updated_at": bio.updated_at,
        }
    except Exception as exc:
        logger.warning("Failed serializing BiotimeEmployee: %s", exc)
        return None


# ======================================================
# 👥 Employees List
# ======================================================

@require_GET
@login_required
def employees_list(request):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"status": "ok", "employees": []})

    qs = (
        Employee.objects
        .filter(company=company)
        .select_related("department", "job_title", "user")
        .prefetch_related("branches")   # ✅ Multi-Branch
        .order_by("id")
    )

    return JsonResponse({
        "status": "ok",
        "employees": [
            {
                "id": emp.id,

                # ✅ Backward compatibility
                "name": emp.full_name,
                "full_name": emp.full_name,

                "department": emp.department.name if emp.department else None,
                "job_title": emp.job_title.name if emp.job_title else None,

                # ✅ NEW — Branches
                "branches": [
                    {
                        "id": b.id,
                        "name": b.name,
                        "biotime_code": b.biotime_code,
                    }
                    for b in emp.branches.all()
                ],

                "status": _map_user_status(emp.user.is_active),
                "biotime_code": getattr(emp, "biotime_code", None),
                "user": {
                    "id": emp.user.id,
                    "username": emp.user.username,
                    "email": emp.user.email,
                    "is_active": emp.user.is_active,
                },
            }
            for emp in qs
        ]
    })


# ======================================================
# 👁 Employee Detail
# ======================================================

@require_GET
@login_required
def employee_detail(request, employee_id):
    company = _resolve_company(request)
    if not company:
        return JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )

    try:
        emp = (
            Employee.objects
            .select_related("department", "job_title", "user")
            .prefetch_related("branches")   # ✅ Multi-Branch
            .get(id=employee_id, company=company)
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employee not found"},
            status=404,
        )

    # --------------------------------------------------
    # 🧬 Resolve Biotime Details (READ ONLY)
    # --------------------------------------------------
    biotime_obj = None
    biotime_code = getattr(emp, "biotime_code", None)

    if biotime_code:
        biotime_obj = (
            BiotimeEmployee.objects
            .filter(employee_id=biotime_code)
            .only(
                "employee_id",
                "full_name",
                "is_active",
                "department",
                "enrolled_fingers",
                "card_number",
                "photo_url",
                "created_at",
                "updated_at",
            )
            .first()
        )

    biotime_payload = _serialize_biotime_employee(biotime_obj)

    return JsonResponse({
        "status": "ok",
        "id": emp.id,

        "name": emp.full_name,
        "full_name": emp.full_name,

        "status": _map_user_status(emp.user.is_active),
        "biotime_code": biotime_code,
        "biotime": biotime_payload,

        "profile": {
            "full_name": emp.full_name,
            "arabic_name": emp.arabic_name,
            "national_id": emp.national_id,
            "passport_number": emp.passport_number,
            "date_of_birth": emp.date_of_birth,
            "nationality": emp.nationality,
            "gender": emp.gender,
            "employment_type": emp.employment_type,
            "join_date": emp.join_date,
            "probation_end_date": emp.probation_end_date,
            "end_date": emp.end_date,
        },

        "department": emp.department.name if emp.department else None,
        "job_title": emp.job_title.name if emp.job_title else None,

        # ✅ NEW — Branches
        "branches": [
            {
                "id": b.id,
                "name": b.name,
                "biotime_code": b.biotime_code,
            }
            for b in emp.branches.all()
        ],

        "user": {
            "id": emp.user.id,
            "username": emp.user.username,
            "email": emp.user.email,
            "is_active": emp.user.is_active,
        },

        "created_at": emp.created_at,
        "updated_at": emp.updated_at,
    })


# ======================================================
# ➕ Create Employee (CSRF SAFE + ROLE FALLBACK + MULTI-BRANCH ✅)
# ======================================================

@csrf_exempt
@require_POST
@login_required
@transaction.atomic
def employee_create(request):
    company = _resolve_company(request)
    if not company:
        return JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )

    payload = _parse_body(request)
    employee_data = payload.get("employee", {})
    user_data = payload.get("user", {})

    full_name = _clean_str(employee_data.get("full_name"))
    username = _clean_str(user_data.get("username"))
    password = user_data.get("password")
    role_id = user_data.get("role_id")

    if not full_name:
        return JsonResponse(
            {"status": "error", "message": "Employee full_name is required"},
            status=400,
        )

    if not username or not password:
        return JsonResponse(
            {"status": "error", "message": "User username & password are required"},
            status=400,
        )

    # --------------------------------------------------
    # 🔐 Resolve Role
    # --------------------------------------------------
    if role_id:
        role = CompanyRole.objects.filter(
            id=role_id,
            company=company,
        ).first()
    else:
        role = (
            CompanyRole.objects
            .filter(company=company)
            .order_by("id")
            .first()
        )

    if not role:
        return JsonResponse(
            {"status": "error", "message": "No role configured for this company"},
            status=400,
        )

    if User.objects.filter(username=username).exists():
        return JsonResponse(
            {"status": "error", "message": "Username already exists"},
            status=400,
        )

    # --------------------------------------------------
    # 👤 Create User
    # --------------------------------------------------
    user = User.objects.create_user(
        username=username,
        password=password,
        email=_clean_str(user_data.get("email")),
        is_active=True,
    )

    # --------------------------------------------------
    # 🏢 Link User to Company
    # --------------------------------------------------
    CompanyUser.objects.create(
        company=company,
        user=user,
        role=role,
        is_active=True,
    )

    # --------------------------------------------------
    # 👥 Create Employee
    # --------------------------------------------------
    emp = Employee.objects.create(
        company=company,
        user=user,
        full_name=full_name,
    )

    emp.department = CompanyDepartment.objects.filter(
        id=employee_data.get("department_id"),
        company=company,
    ).first()

    emp.job_title = JobTitle.objects.filter(
        id=employee_data.get("job_title_id"),
        company=company,
    ).first()

    emp.save()

    # --------------------------------------------------
    # ✅ NEW — Assign Branches (Multi-Branch)
    # --------------------------------------------------
    branch_ids = employee_data.get("branch_ids") or []

    if isinstance(branch_ids, list) and branch_ids:
        branches = CompanyBranch.objects.filter(
            id__in=branch_ids,
            company=company,
        )
        emp.branches.set(branches)

    EmploymentInfo.objects.get_or_create(employee=emp)

    return JsonResponse({
        "status": "success",
        "employee_id": emp.id,
        "user_id": user.id,
    })


# ======================================================
# 🔗 Link Employee with Biotime (STRICT 🔒)
# ======================================================

@csrf_exempt
@require_POST
@login_required
@transaction.atomic
def employee_link_biotime(request, employee_id):
    """
    🔗 ربط موظف النظام مع موظف Biotime عبر biotime_code
    - يمنع إعادة الربط إذا كان الموظف مرتبط مسبقًا
    - يمنع تكرار الكود على أكثر من موظف
    - يشغل المزامنة الموجهة بأمان
    """

    company = _resolve_company(request)
    if not company:
        return JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )

    payload = _parse_body(request)
    biotime_code = _clean_str(payload.get("biotime_code"))

    if not biotime_code:
        return JsonResponse(
            {"status": "error", "message": "biotime_code is required"},
            status=400,
        )

    # --------------------------------------------------
    # 👥 Resolve Employee
    # --------------------------------------------------
    try:
        emp = Employee.objects.get(
            id=employee_id,
            company=company,
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employee not found"},
            status=404,
        )

    # --------------------------------------------------
    # 🔒 Prevent Employee Re-Linking
    # --------------------------------------------------
    if emp.biotime_code:
        return JsonResponse(
            {
                "status": "error",
                "message": "هذا الموظف مرتبط مسبقًا بجهاز ولا يمكن إعادة ربطه",
                "current_biotime_code": emp.biotime_code,
            },
            status=409,
        )

    # --------------------------------------------------
    # 🧬 Validate Biotime Employee Exists
    # --------------------------------------------------
    bio = BiotimeEmployee.objects.filter(
        employee_id=biotime_code,
        is_active=True,
    ).first()

    if not bio:
        return JsonResponse(
            {
                "status": "error",
                "message": "Biotime employee not found or inactive",
            },
            status=404,
        )

    # --------------------------------------------------
    # 🔒 Prevent Duplicate Linking Across Employees
    # --------------------------------------------------
    already_linked = (
        Employee.objects
        .filter(biotime_code=biotime_code)
        .exists()
    )

    if already_linked:
        return JsonResponse(
            {
                "status": "error",
                "message": "هذا الكود مربوط مسبقًا بموظف آخر",
            },
            status=409,
        )

    # --------------------------------------------------
    # ✅ Link
    # --------------------------------------------------
    emp.biotime_code = biotime_code
    emp.save(update_fields=["biotime_code"])

    logger.info(
        "Biotime linked | company=%s | employee=%s | biotime_code=%s",
        company.id,
        emp.id,
        biotime_code,
    )

    # --------------------------------------------------
    # 🔄 Trigger Targeted Mapping (SAFE + FALLBACK)
    # --------------------------------------------------
    try:
        try:
            mapping_result = sync_biotime_logs_to_attendance(
                force_employee_code=biotime_code
            )
        except TypeError:
            mapping_result = sync_biotime_logs_to_attendance()

    except Exception:
        logger.exception("Failed triggering post-link attendance mapping")
        mapping_result = {"synced": 0, "skipped": 0}

    return JsonResponse({
        "status": "success",
        "employee_id": emp.id,
        "biotime_code": biotime_code,
        "biotime_name": bio.full_name,
        "attendance_sync": mapping_result,
    })


# ======================================================
# ✏️ Update Employee (CSRF SAFE + BIOTIME AUTO SYNC ✅)
# ======================================================

@csrf_exempt
@require_POST
@login_required
def employee_update(request, employee_id):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"status": "error"}, status=403)

    payload = _parse_body(request)

    try:
        emp = Employee.objects.get(id=employee_id, company=company)
    except Employee.DoesNotExist:
        return JsonResponse({"status": "error"}, status=404)

    changed_fields = set()

    # ---------------------------
    # 📝 Core Fields
    # ---------------------------
    if "full_name" in payload:
        emp.full_name = _clean_str(payload["full_name"])
        changed_fields.add("full_name")

    if "department_id" in payload:
        emp.department = CompanyDepartment.objects.filter(
            id=payload["department_id"],
            company=company,
        ).first()
        changed_fields.add("department")

    if "job_title_id" in payload:
        emp.job_title = JobTitle.objects.filter(
            id=payload["job_title_id"],
            company=company,
        ).first()
        changed_fields.add("job_title")

    # --------------------------------------------------
    # ✅ FIXED — Update Branches (Multi-Branch SAFE)
    # --------------------------------------------------
    if "branch_ids" in payload:
        branch_ids = payload.get("branch_ids") or []

        if isinstance(branch_ids, list):
            branches = CompanyBranch.objects.filter(
                id__in=branch_ids,
                company=company,
            )
            emp.branches.set(branches)
            changed_fields.add("branches")

    emp.save()

    # --------------------------------------------------
    # 🔄 Auto Sync To Biotime (ONLY IF LINKED)
    # --------------------------------------------------
    if emp.biotime_code and changed_fields:
        try:
            from biotime_center.sync_service import (
                patch_employee_department,
                patch_employee_position,
                patch_employee_name,        # ✅ Name Sync
                append_employee_area,       # ✅ Append Area (Phase E.1)
            )

            logger.info(
                "Biotime Auto Sync | employee=%s | fields=%s",
                emp.id,
                sorted(changed_fields),
            )

            # ============================
            # ✅ Name Sync
            # ============================
            if "full_name" in changed_fields:
                if emp.full_name:
                    logger.info(
                        "Biotime Name Sync | employee=%s | name=%s",
                        emp.id,
                        emp.full_name,
                    )

                    patch_employee_name(
                        employee_id=emp.biotime_code,
                        full_name=emp.full_name,
                    )

            # ============================
            # ✅ Department Sync
            # ============================
            if "department" in changed_fields:
                if emp.department and emp.department.biotime_code:
                    logger.info(
                        "Biotime Department Sync | employee=%s | dept=%s",
                        emp.id,
                        emp.department.biotime_code,
                    )

                    patch_employee_department(
                        employee_id=str(emp.biotime_code),
                        dept_code=str(emp.department.biotime_code),
                    )
                else:
                    logger.warning(
                        "Biotime Department Sync Skipped | employee=%s | missing biotime_code",
                        emp.id,
                    )

            # ============================
            # ✅ Position Sync (JobTitle)
            # ============================
            if "job_title" in changed_fields:
                position_id = None

                if emp.job_title:
                    position_id = (
                        emp.job_title.biotime_position_id
                        or emp.job_title.biotime_code
                    )

                if position_id and str(position_id).isdigit():
                    logger.info(
                        "Biotime Position Sync | employee=%s | position_id=%s",
                        emp.id,
                        position_id,
                    )

                    patch_employee_position(
                        employee_id=emp.biotime_code,
                        position_code=str(position_id),
                    )
                else:
                    logger.warning(
                        "Biotime Position Sync Skipped | employee=%s | invalid position_id=%s",
                        emp.id,
                        position_id,
                    )
            # ============================================================
            # ✅ Area Sync (Biotime Areas — REPLACE MODE)
            # ============================================================

            if "branches" in changed_fields:

                try:
                    from biotime_center.sync_service import patch_employee_areas_replace

                    area_codes = [
                        b.biotime_code
                        for b in emp.branches.all()
                        if b.biotime_code
                    ]

                    logger.info(
                        "Biotime Area Replace Sync | employee=%s | areas=%s",
                        emp.id,
                        area_codes,
                    )

                    patch_employee_areas_replace(
                        employee_id=str(emp.biotime_code),
                        area_codes=area_codes,
                    )

                except Exception:
                    logger.exception(
                        "❌ Biotime Area Replace Sync Failed | employee=%s",
                        emp.id,
                    )

            # ============================
            # ✅ Branches → Areas Sync (APPEND SAFE)
            # ============================
            if "branches" in changed_fields:
                raw_area_codes = [
                    b.biotime_code
                    for b in emp.branches.all()
                    if b.biotime_code and str(b.biotime_code).isdigit()
                ]

                if raw_area_codes:
                    logger.info(
                        "Biotime Area Append | employee=%s | area_codes=%s",
                        emp.id,
                        raw_area_codes,
                    )

                    # 🔁 Append كل Area بدون Replace
                    for area_code in raw_area_codes:
                        append_employee_area(
                            employee_biotime_id=emp.biotime_code,
                            new_area_code=str(area_code),
                        )

                else:
                    logger.warning(
                        "Biotime Area Sync Skipped | employee=%s | no valid areas",
                        emp.id,
                    )

        except Exception:
            # 🛡️ لا نكسر حفظ النظام بسبب فشل خارجي
            logger.exception(
                "Biotime Auto Sync Failed | employee=%s",
                emp.id,
            )

    return JsonResponse({"status": "success"})


# ======================================================
# 🧍 Profile Update (CSRF SAFE + BIOTIME AUTO SYNC ✅)
# ======================================================

@csrf_exempt
@require_POST
@login_required
def employee_profile_update(request, employee_id):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"status": "error"}, status=403)

    payload = _parse_body(request)

    try:
        emp = Employee.objects.get(id=employee_id, company=company)
    except Employee.DoesNotExist:
        return JsonResponse({"status": "error"}, status=404)

    allowed_fields = {
        "full_name",
        "arabic_name",
        "national_id",
        "passport_number",
        "date_of_birth",
        "nationality",
        "gender",
        "employment_type",
        "join_date",
        "probation_end_date",
        "end_date",
    }

    updated_fields = set()
    updated = False

    for field in allowed_fields:
        if field in payload:
            setattr(emp, field, payload.get(field))
            updated = True
            updated_fields.add(field)

    if not updated:
        return JsonResponse(
            {"status": "error", "message": "No valid fields provided"},
            status=400,
        )

    emp.save()

    # --------------------------------------------------
    # 🔄 Auto Sync Name To Biotime (ONLY IF LINKED)
    # --------------------------------------------------
    if emp.biotime_code and "full_name" in updated_fields:
        try:
            from biotime_center.sync_service import patch_employee_name

            logger.info(
                "Biotime Auto Sync Name | employee=%s",
                emp.id,
            )

            patch_employee_name(
                employee_id=emp.biotime_code,
                full_name=emp.full_name,
            )

        except Exception:
            logger.exception(
                "Biotime Name Sync Failed | employee=%s",
                emp.id,
            )

    return JsonResponse({"status": "success", "employee_id": emp.id})


# ======================================================
# 🔁 Toggle User Status (CSRF SAFE)
# ======================================================

@csrf_exempt
@require_POST
@login_required
def employee_toggle_status(request, employee_id):
    company_user = _resolve_company_user(request)
    if not company_user:
        return JsonResponse({"status": "error"}, status=403)

    try:
        emp = Employee.objects.select_related("user").get(
            id=employee_id,
            company=company_user.company,
        )
    except Employee.DoesNotExist:
        return JsonResponse({"status": "error"}, status=404)

    new_state = not emp.user.is_active
    emp.user.is_active = new_state
    emp.user.save(update_fields=["is_active"])

    CompanyUser.objects.filter(
        user=emp.user,
        company=company_user.company,
    ).update(is_active=new_state)

    return JsonResponse({
        "status": "success",
        "employee_status": _map_user_status(new_state),
        "is_active": new_state,
    })


# ======================================================
# 🕒 Employment History
# ======================================================

@require_GET
@login_required
def employee_history(request, employee_id):
    company = _resolve_company(request)
    if not company:
        return JsonResponse({"status": "error"}, status=403)

    try:
        emp = Employee.objects.get(id=employee_id, company=company)
    except Employee.DoesNotExist:
        return JsonResponse({"status": "error"}, status=404)

    qs = (
        EmploymentHistory.objects
        .filter(employee=emp)
        .order_by("-effective_date", "-created_at")
    )

    return JsonResponse({
        "status": "ok",
        "items": [
            {
                "id": item.id,
                "action_type": item.action_type,
                "description": item.description,
                "effective_date": item.effective_date,
                "created_at": item.created_at,
            }
            for item in qs
        ],
    })
# ======================================================
# 🚀 Phase F.3 — Assign Work Schedule To Employee
# ======================================================

@csrf_exempt
@require_POST
@login_required
@transaction.atomic
def employee_assign_work_schedule(request, employee_id):
    """
    🕒 ربط جدول دوام افتراضي للموظف (SAFE + IDEMPOTENT)

    Payload:
    {
        "schedule_id": 3
    }

    Rules:
    - يجب أن يكون الجدول ضمن نفس الشركة
    - يمنع ربط جدول غير نشط
    - Idempotent (لو نفس الجدول لا يعيد الحفظ)
    """

    company = _resolve_company(request)
    if not company:
        return JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )

    payload = _parse_body(request)
    schedule_id = payload.get("schedule_id")

    if not schedule_id:
        return JsonResponse(
            {"status": "error", "message": "schedule_id is required"},
            status=400,
        )

    # --------------------------------------------------
    # 👤 Resolve Employee
    # --------------------------------------------------
    try:
        emp = Employee.objects.select_for_update().get(
            id=employee_id,
            company=company,
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employee not found"},
            status=404,
        )

    # --------------------------------------------------
    # 🕒 Resolve Schedule
    # --------------------------------------------------
    try:
        schedule = WorkSchedule.objects.get(
            id=schedule_id,
            company=company,
        )
    except WorkSchedule.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Work schedule not found"},
            status=404,
        )

    # --------------------------------------------------
    # 🔒 Validate Active
    # --------------------------------------------------
    if not schedule.is_active:
        return JsonResponse(
            {
                "status": "error",
                "message": "لا يمكن ربط جدول غير نشط",
            },
            status=409,
        )

    # --------------------------------------------------
    # ♻️ Idempotency Guard
    # --------------------------------------------------
    if emp.default_work_schedule_id == schedule.id:
        return JsonResponse(
            {
                "status": "ok",
                "message": "Schedule already assigned",
                "schedule": {
                    "id": schedule.id,
                    "name": schedule.name,
                    "is_active": schedule.is_active,
                },
            }
        )

    # --------------------------------------------------
    # ✅ Assign
    # --------------------------------------------------
    emp.default_work_schedule = schedule
    emp.save(update_fields=["default_work_schedule"])

    logger.info(
        "WorkSchedule Assigned | company=%s | employee=%s | schedule=%s",
        company.id,
        emp.id,
        schedule.id,
    )

    return JsonResponse({
        "status": "success",
        "employee_id": emp.id,
        "schedule": {
            "id": schedule.id,
            "name": schedule.name,
            "is_active": schedule.is_active,
        },
    })
