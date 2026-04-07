# ======================================================
# 👥 Employee API — Company Scope
# Mham Cloud
# Version: D3.15 Ultra Pro (NOTIFICATION CENTER CLEANUP ✅)
# ======================================================

from __future__ import annotations

import json
import logging
import re
from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from auth_center.models import UserProfile
from biotime_center.models import BiotimeEmployee
from company_manager.models import (
    CompanyBranch,
    CompanyDepartment,
    CompanyRole,
    CompanyUser,
    JobTitle,
)
from employee_center.models import (
    Employee,
    EmploymentHistory,
    EmploymentInfo,
    FinancialInfo,
)
from payroll_center.models import PayrollRecord

from attendance_center.models import WorkSchedule
from attendance_center.services.sync_biotime_to_attendance import (
    sync_biotime_logs_to_attendance,
)
from notification_center.services_hr import (
    notify_employee_activated,
    notify_employee_created,
    notify_employee_deactivated,
)
from whatsapp_center.utils import normalize_phone_number

logger = logging.getLogger(__name__)
User = get_user_model()

# ======================================================
# Constants
# ======================================================

ALLOWED_COMPANY_ROLES = {
    "OWNER",
    "ADMIN",
    "HR",
    "MANAGER",
    "EMPLOYEE",
}


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


def _clean_date(value):
    """
    يحول YYYY-MM-DD إلى date
    ويرجع None إذا كانت القيمة فارغة
    """
    value = _clean_str(value)
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {value}")


def _clean_bool(value):
    if isinstance(value, bool):
        return value

    if value in (1, "1", "true", "True", "TRUE", "yes", "YES", "on"):
        return True

    if value in (0, "0", "false", "False", "FALSE", "no", "NO", "off"):
        return False

    return bool(value)


def _clean_float(value, default=0):
    if value in (None, ""):
        return float(default)

    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid numeric value: {value}")


def _generate_next_employee_number(company) -> str:
    """
    توليد رقم موظف تلقائي على مستوى الشركة
    الصيغة: EMP-002-00001
    """
    if not company or not getattr(company, "id", None):
        timestamp_part = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"EMP-GEN-{timestamp_part}"

    prefix = f"EMP-{int(company.id):03d}-"
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")

    existing_numbers = (
        Employee.objects
        .filter(company=company)
        .exclude(employee_number__isnull=True)
        .exclude(employee_number__exact="")
        .values_list("employee_number", flat=True)
    )

    max_seq = 0
    for value in existing_numbers:
        match = pattern.match(str(value).strip())
        if not match:
            continue

        try:
            seq = int(match.group(1))
            if seq > max_seq:
                max_seq = seq
        except (TypeError, ValueError):
            continue

    return f"{prefix}{max_seq + 1:05d}"


def _sync_user_profile_contact(user, mobile_number: str | None) -> None:
    """
    مزامنة رقم الموظف داخل UserProfile حتى تعمل إشعارات واتساب
    في المسارات الأخرى مثل:
    - change_password
    - reset_password
    - profile_update
    """
    if not user:
        return

    raw_phone = _clean_str(mobile_number)
    normalized_phone = normalize_phone_number(raw_phone) if raw_phone else ""

    profile, _ = UserProfile.objects.get_or_create(user=user)

    update_fields = []

    if hasattr(profile, "phone_number"):
        profile.phone_number = raw_phone or None
        update_fields.append("phone_number")

    if hasattr(profile, "whatsapp_number"):
        profile.whatsapp_number = normalized_phone or raw_phone or None
        update_fields.append("whatsapp_number")

    if update_fields:
        profile.save(update_fields=update_fields)


def _resolve_company_user(request) -> CompanyUser | None:
    """
    🔐 Resolve CompanyUser Context (SAFE)
    يعتمد على active_company_id من الجلسة أولًا
    لمنع تعارض الشركة المعروضة مع الشركة المُدارة
    """
    active_company_id = request.session.get("active_company_id")

    qs = (
        CompanyUser.objects
        .select_related("company", "user")
        .filter(
            user=request.user,
            is_active=True,
            company__isnull=False,
        )
    )

    if active_company_id:
        item = qs.filter(company_id=active_company_id).order_by("-id").first()
        if item:
            return item

    return qs.order_by("-id").first()


def _resolve_company(request):
    """
    STRICT Multi-Tenant Resolver

    - Requires active_company_id in session
    - No fallback
    - If no active company → return None (403 in APIs)
    """
    active_company_id = request.session.get("active_company_id")

    if not active_company_id:
        return None

    cu = (
        CompanyUser.objects
        .select_related("company")
        .filter(
            user=request.user,
            company_id=active_company_id,
            is_active=True,
        )
        .first()
    )

    return cu.company if cu else None


def _resolve_active_company_user(request) -> CompanyUser | None:
    """
    ✅ مصدر موحد وآمن لكل عمليات الإدارة داخل الشركة النشطة الحالية
    """
    company = _resolve_company(request)
    if not company:
        return None

    return (
        CompanyUser.objects
        .select_related("company", "user")
        .filter(
            user=request.user,
            company=company,
            is_active=True,
        )
        .order_by("-id")
        .first()
    )


def _map_user_status(user_is_active: bool) -> str:
    return "ACTIVE" if user_is_active else "INACTIVE"


def _serialize_biotime_employee(bio: BiotimeEmployee | None):
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
# 👤 User-driven display helpers
# ======================================================

def _get_user_profile(user):
    return (
        UserProfile.objects
        .filter(user=user)
        .first()
    )


def _get_display_full_name(user) -> str:
    full_name = (user.get_full_name() or "").strip()
    return full_name or user.username


def _get_display_avatar(user) -> str | None:
    profile = (
        UserProfile.objects
        .filter(user=user)
        .only("avatar_url")
        .first()
    )
    if profile and profile.avatar_url:
        return profile.avatar_url
    return None


def _get_display_phone(user) -> str:
    profile = _get_user_profile(user)

    if profile:
        for attr in ["phone", "phone_number", "mobile", "mobile_number"]:
            if hasattr(profile, attr):
                value = getattr(profile, attr, "") or ""
                if value:
                    return str(value)

    try:
        employee = getattr(user, "hr_employee", None)
        if employee and getattr(employee, "mobile_number", None):
            return str(employee.mobile_number)
    except Exception:
        pass

    return ""


def _normalize_company_role_value(value) -> str:
    if value is None:
        return "EMPLOYEE"

    raw = str(value).strip().upper()
    return raw or "EMPLOYEE"


def _resolve_company_role_for_create(company, user_data) -> str | None:
    """
    يدعم طريقتين:
    1) role النصي مباشرة من الفرونت
    2) role_id إذا كان موجودًا
    """
    requested_role = _normalize_company_role_value(user_data.get("role"))

    if requested_role in ALLOWED_COMPANY_ROLES:
        return requested_role

    role_id = user_data.get("role_id")
    if role_id:
        role_obj = (
            CompanyRole.objects
            .filter(id=role_id, company=company)
            .first()
        )
        if role_obj:
            role_value = _normalize_company_role_value(
                getattr(role_obj, "code", None)
                or getattr(role_obj, "name", None)
                or getattr(role_obj, "slug", None)
                or str(role_obj)
            )
            if role_value in ALLOWED_COMPANY_ROLES:
                return role_value

    return "EMPLOYEE"


def _get_company_role_for_user(company, user) -> str:
    item = (
        CompanyUser.objects
        .filter(
            company=company,
            user=user,
        )
        .order_by("-id")
        .first()
    )
    return _normalize_company_role_value(item.role if item else "EMPLOYEE")


def _serialize_employee_list_row(company, emp: Employee) -> dict:
    user = emp.user

    display_name = _get_display_full_name(user)
    display_email = user.email or ""
    display_phone = _get_display_phone(user)
    display_avatar = _get_display_avatar(user)
    display_role = _get_company_role_for_user(company, user)

    return {
        "id": emp.id,
        "name": display_name,
        "full_name": display_name,
        "email": display_email,
        "phone": display_phone,
        "avatar": display_avatar,
        "photo_url": display_avatar,
        "username": user.username,
        "role": display_role,
        "department": emp.department.name if emp.department else None,
        "job_title": emp.job_title.name if emp.job_title else None,
        "join_date": emp.join_date,
        "employee_number": emp.employee_number,
        "national_id": emp.national_id,
        "branches": [
            {
                "id": b.id,
                "name": b.name,
                "biotime_code": b.biotime_code,
            }
            for b in emp.branches.all()
        ],
        "status": _map_user_status(user.is_active),
        "is_active": bool(user.is_active),
        "biotime_code": getattr(emp, "biotime_code", None),
        "created_at": user.date_joined.isoformat() if user.date_joined else None,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
        },
    }


def _can_manage_company_users(company_user: CompanyUser) -> bool:
    role = _normalize_company_role_value(company_user.role)
    return role in {"OWNER", "ADMIN", "HR"}


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
        .prefetch_related("branches")
        .order_by("id")
    )

    return JsonResponse({
        "status": "ok",
        "employees": [
            _serialize_employee_list_row(company, emp)
            for emp in qs
        ]
    })


# ======================================================
# 📊 Employees Report — ENTERPRISE ANALYTICS ENGINE
# ======================================================

@require_GET
@login_required
def employees_report(request):
    from django.db.models import DecimalField, Value

    company = _resolve_company(request)
    if not company:
        return JsonResponse({
            "status": "ok",
            "results": [],
            "pagination": {}
        })

    search = request.GET.get("search", "").strip()
    department_id = request.GET.get("department_id")
    branch_id = request.GET.get("branch_id")
    job_title_id = request.GET.get("job_title_id")
    status_filter = (request.GET.get("status") or "").strip().upper()
    hire_from = request.GET.get("hire_from")
    hire_to = request.GET.get("hire_to")
    ordering = request.GET.get("ordering", "id")

    try:
        page = max(int(request.GET.get("page", 1)), 1)
        page_size = min(max(int(request.GET.get("page_size", 20)), 1), 100)
    except ValueError:
        page = 1
        page_size = 20

    qs = (
        Employee.objects
        .filter(company=company)
        .select_related("department", "job_title", "user")
        .prefetch_related("branches")
        .annotate(
            basic_salary_value=Coalesce(
                F("financial_info__basic_salary"),
                Value(0),
                output_field=DecimalField(),
            )
        )
    )

    if search:
        qs = qs.filter(
            Q(full_name__icontains=search)
            | Q(arabic_name__icontains=search)
            | Q(national_id__icontains=search)
            | Q(employee_number__icontains=search)
            | Q(user__username__icontains=search)
            | Q(user__email__icontains=search)
        )

    if department_id:
        qs = qs.filter(department_id=department_id)

    if branch_id:
        qs = qs.filter(branches__id=branch_id)

    if job_title_id:
        qs = qs.filter(job_title_id=job_title_id)

    if status_filter:
        if status_filter == "ACTIVE":
            qs = qs.filter(user__is_active=True)
        elif status_filter == "INACTIVE":
            qs = qs.filter(user__is_active=False)
        else:
            try:
                qs = qs.filter(status=status_filter)
            except Exception:
                pass

    if hire_from:
        qs = qs.filter(join_date__gte=hire_from)

    if hire_to:
        qs = qs.filter(join_date__lte=hire_to)

    qs = qs.distinct()

    ALLOWED_ORDERING = {
        "id": "id",
        "full_name": "full_name",
        "-full_name": "-full_name",
        "join_date": "join_date",
        "-join_date": "-join_date",
        "basic_salary": "basic_salary_value",
        "-basic_salary": "-basic_salary_value",
    }

    ordering_field = ALLOWED_ORDERING.get(ordering, "id")
    qs = qs.order_by(ordering_field)

    total_count = qs.count()

    start = (page - 1) * page_size
    end = start + page_size
    qs = qs[start:end]

    results = []

    for emp in qs:
        row = _serialize_employee_list_row(company, emp)

        results.append({
            "id": emp.id,
            "full_name": row["full_name"],
            "photo_url": row["photo_url"],
            "avatar": row["avatar"],
            "email": row["email"],
            "phone": row["phone"],
            "username": row["username"],
            "role": row["role"],
            "national_id": emp.national_id,
            "employee_number": emp.employee_number,
            "department": emp.department.name if emp.department else None,
            "job_title": emp.job_title.name if emp.job_title else None,
            "branches": [b.name for b in emp.branches.all()],
            "basic_salary": float(emp.basic_salary_value or 0),
            "join_date": emp.join_date,
            "status": row["status"],
            "is_active": row["is_active"],
        })

    return JsonResponse({
        "status": "ok",
        "results": results,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
        }
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
            .select_related(
                "department",
                "job_title",
                "user",
                "default_work_schedule",
            )
            .prefetch_related("branches")
            .get(id=employee_id, company=company)
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employee not found"},
            status=404,
        )

    user = emp.user
    display_name = _get_display_full_name(user)
    display_email = user.email or ""
    display_phone = _get_display_phone(user)
    display_avatar = _get_display_avatar(user)
    display_role = _get_company_role_for_user(company, user)

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

    financial_obj = getattr(emp, "financial_info", None)

    financial_payload = None
    if financial_obj:
        financial_payload = {
            "basic_salary": float(financial_obj.basic_salary or 0),
            "housing_allowance": float(financial_obj.housing_allowance or 0),
            "transport_allowance": float(financial_obj.transport_allowance or 0),
            "food_allowance": float(financial_obj.food_allowance or 0),
            "other_allowances": float(financial_obj.other_allowances or 0),
            "is_gosi_enabled": financial_obj.is_gosi_enabled,
            "is_tax_enabled": financial_obj.is_tax_enabled,
            "bank_name": financial_obj.bank_name,
            "iban": financial_obj.iban,
        }

    payroll_qs = (
        PayrollRecord.objects
        .filter(employee=emp)
        .order_by("-month")[:12]
    )

    payroll_records_payload = [
        {
            "id": record.id,
            "month": record.month.strftime("%Y-%m") if record.month else None,
            "base_salary": float(record.base_salary or 0),
            "allowance": float(record.allowance or 0),
            "bonus": float(record.bonus or 0),
            "overtime": float(record.overtime or 0),
            "deductions": float(record.deductions or 0),
            "net_salary": float(record.net_salary or 0),
            "paid_amount": float(record.paid_amount or 0),
            "remaining_amount": float(record.remaining_amount or 0),
            "is_fully_paid": record.is_fully_paid,
            "status": record.status,
        }
        for record in payroll_qs
    ]

    return JsonResponse({
        "status": "ok",
        "id": emp.id,
        "name": display_name,
        "full_name": display_name,
        "email": display_email,
        "phone": display_phone,
        "avatar": display_avatar,
        "photo_url": display_avatar,
        "role": display_role,
        "status": _map_user_status(user.is_active),
        "biotime_code": biotime_code,
        "biotime": biotime_payload,
        "financial_info": financial_payload,
        "payroll_records": payroll_records_payload,
        "profile": {
            "full_name": display_name,
            "email": display_email,
            "mobile_number": display_phone,
            "avatar": display_avatar,
            "username": user.username,
            "arabic_name": emp.arabic_name,
            "date_of_birth": emp.date_of_birth,
            "nationality": emp.nationality,
            "gender": emp.gender,
            "national_id": emp.national_id,
            "national_id_issue_date": emp.national_id_issue_date,
            "national_id_expiry_date": emp.national_id_expiry_date,
            "passport_number": emp.passport_number,
            "passport_issue_date": emp.passport_issue_date,
            "passport_expiry_date": emp.passport_expiry_date,
            "employment_type": emp.employment_type,
            "employee_number": emp.employee_number,
            "join_date": emp.join_date,
            "work_start_date": emp.work_start_date,
            "probation_end_date": emp.probation_end_date,
            "end_date": emp.end_date,
            "gosi_number": emp.gosi_number,
        },
        "department_id": emp.department.id if emp.department else None,
        "job_title_id": emp.job_title.id if emp.job_title else None,
        "branch_ids": [b.id for b in emp.branches.all()],
        "default_work_schedule_id": emp.default_work_schedule_id,
        "job_info": {
            "department_id": emp.department.id if emp.department else None,
            "job_title_id": emp.job_title.id if emp.job_title else None,
            "work_schedule_id": emp.default_work_schedule_id,
            "branch_ids": [b.id for b in emp.branches.all()],
        },
        "department": (
            {
                "id": emp.department.id,
                "name": emp.department.name,
            }
            if emp.department else None
        ),
        "job_title": (
            {
                "id": emp.job_title.id,
                "name": emp.job_title.name,
            }
            if emp.job_title else None
        ),
        "default_work_schedule": (
            {
                "id": emp.default_work_schedule.id,
                "name": emp.default_work_schedule.name,
                "is_active": emp.default_work_schedule.is_active,
            }
            if emp.default_work_schedule else None
        ),
        "branches": [
            {
                "id": b.id,
                "name": b.name,
                "biotime_code": b.biotime_code,
            }
            for b in emp.branches.all()
        ],
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
        },
        "created_at": emp.created_at,
        "updated_at": emp.updated_at,
    })


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
    employee_data = payload.get("employee", {}) or {}
    user_data = payload.get("user", {}) or {}

    full_name = _clean_str(employee_data.get("full_name"))
    arabic_name = _clean_str(employee_data.get("arabic_name"))
    employee_number = _clean_str(employee_data.get("employee_number"))

    username = _clean_str(user_data.get("username"))
    password = user_data.get("password")
    email = _clean_str(user_data.get("email"))
    mobile_number = _clean_str(
        employee_data.get("mobile_number") or user_data.get("phone")
    )

    department_id = employee_data.get("department_id")
    job_title_id = employee_data.get("job_title_id")
    branch_ids = employee_data.get("branch_ids") or []

    requested_role = _resolve_company_role_for_create(company, user_data)

    requested_status_raw = _clean_str(user_data.get("status")) or "ACTIVE"
    requested_status = requested_status_raw.upper()
    user_is_active = requested_status != "INACTIVE"

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

    if not department_id:
        return JsonResponse(
            {"status": "error", "message": "department_id is required"},
            status=400,
        )

    if requested_role not in ALLOWED_COMPANY_ROLES:
        return JsonResponse(
            {"status": "error", "message": "Invalid role"},
            status=400,
        )

    if User.objects.filter(username=username).exists():
        return JsonResponse(
            {"status": "error", "message": "Username already exists"},
            status=400,
        )

    if email and User.objects.filter(email=email).exists():
        return JsonResponse(
            {"status": "error", "message": "Email already exists"},
            status=400,
        )

    # =====================================================
    # 🔢 Auto Employee Number
    # إذا لم يرسل الفرونت رقم الموظف يتم توليده تلقائيًا
    # =====================================================
    if not employee_number:
        employee_number = _generate_next_employee_number(company)

    if Employee.objects.filter(
        company=company,
        employee_number=employee_number,
    ).exists():
        return JsonResponse(
            {"status": "error", "message": "Employee number already exists"},
            status=400,
        )

    department = CompanyDepartment.objects.filter(
        id=department_id,
        company=company,
    ).first()

    if not department:
        return JsonResponse(
            {"status": "error", "message": "Selected department not found"},
            status=400,
        )

    job_title = None
    if job_title_id:
        job_title = JobTitle.objects.filter(
            id=job_title_id,
            company=company,
        ).first()

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email or "",
        is_active=user_is_active,
    )

    company_user = CompanyUser.objects.create(
        company=company,
        user=user,
        role=requested_role,
        is_active=user_is_active,
    )

    emp = Employee.objects.create(
        company=company,
        user=user,
        full_name=full_name,
        arabic_name=arabic_name,
        employee_number=employee_number,
        mobile_number=mobile_number,
        department=department,
        job_title=job_title,
    )

    if isinstance(branch_ids, list) and branch_ids:
        branches = CompanyBranch.objects.filter(
            id__in=branch_ids,
            company=company,
        )
        emp.branches.set(branches)

    EmploymentInfo.objects.get_or_create(employee=emp)

    # =====================================================
    # 📱 Sync employee mobile into UserProfile
    # حتى تعمل إشعارات واتساب لباقي المسارات لاحقًا
    # =====================================================
    try:
        _sync_user_profile_contact(user, mobile_number)
    except Exception:
        logger.exception(
            "Failed syncing user profile contact after employee create | employee=%s | user=%s",
            getattr(emp, "id", None),
            getattr(user, "id", None),
        )

    # =====================================================
    # 🔔 Notification Center Hook — Employee Created
    # المسار الرسمي الموحد بدل الإرسال المباشر من الـ API
    # =====================================================
    try:
        notify_employee_created(
            emp,
            send_email=True,
            send_whatsapp=True,
        )
    except Exception:
        logger.exception(
            "⚠ Employee created notification hook failed (non-blocking) | employee=%s",
            emp.id,
        )

    return JsonResponse({
        "status": "success",
        "employee_id": emp.id,
        "employee_number": emp.employee_number,
        "user_id": user.id,
        "role": requested_role,
        "is_active": user_is_active,
        "department": {
            "id": department.id,
            "name": department.name,
        },
        "job_title": (
            {
                "id": job_title.id,
                "name": job_title.name,
            }
            if job_title else None
        ),
        "branches_count": emp.branches.count(),
        "company_user_id": company_user.id,
    })

# ======================================================
# 🔗 Link Employee with Biotime
# ======================================================

@csrf_exempt
@require_POST
@login_required
@transaction.atomic
def employee_link_biotime(request, employee_id):
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

    if emp.biotime_code:
        return JsonResponse(
            {
                "status": "error",
                "message": "هذا الموظف مرتبط مسبقًا بجهاز ولا يمكن إعادة ربطه",
                "current_biotime_code": emp.biotime_code,
            },
            status=409,
        )

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

    emp.biotime_code = biotime_code
    emp.save(update_fields=["biotime_code"])

    logger.info(
        "Biotime linked | company=%s | employee=%s | biotime_code=%s",
        company.id,
        emp.id,
        biotime_code,
    )

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
# ✏️ Update Employee
# ======================================================

@csrf_exempt
@require_http_methods(["POST", "PATCH", "PUT"])
@login_required
@transaction.atomic
def employee_update(request, employee_id):
    company_user = _resolve_active_company_user(request)
    if not company_user:
        return JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403
        )

    if not _can_manage_company_users(company_user):
        return JsonResponse(
            {
                "status": "error",
                "message": "You do not have permission to update employee data",
            },
            status=403
        )

    company = company_user.company

    try:
        emp = (
            Employee.objects
            .select_related("department", "job_title", "user", "default_work_schedule")
            .prefetch_related("branches")
            .get(id=employee_id, company=company)
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employee not found"},
            status=404
        )

    payload = _parse_body(request)
    section = _clean_str(payload.get("section")) or "generic"

    changed_fields = set()
    biotime_sync_required = False

    try:
        # ==================================================
        # PERSONAL
        # ==================================================
        if section == "personal":
            profile = payload.get("profile") or {}

            if "full_name" in profile:
                emp.full_name = _clean_str(profile.get("full_name"))
                changed_fields.add("full_name")
                biotime_sync_required = True

            if "arabic_name" in profile:
                emp.arabic_name = _clean_str(profile.get("arabic_name"))
                changed_fields.add("arabic_name")

            if "nationality" in profile:
                emp.nationality = _clean_str(profile.get("nationality"))
                changed_fields.add("nationality")

            if "gender" in profile:
                emp.gender = _clean_str(profile.get("gender"))
                changed_fields.add("gender")

            if "date_of_birth" in profile:
                emp.date_of_birth = _clean_date(profile.get("date_of_birth"))
                changed_fields.add("date_of_birth")

            if "gosi_number" in profile:
                emp.gosi_number = _clean_str(profile.get("gosi_number"))
                changed_fields.add("gosi_number")

            if "mobile_number" in profile:
                emp.mobile_number = _clean_str(profile.get("mobile_number"))
                changed_fields.add("mobile_number")

            if emp.user:
                user_changed = False

                if "username" in profile:
                    username = _clean_str(profile.get("username"))
                    if username and username != emp.user.username:
                        exists = User.objects.exclude(id=emp.user_id).filter(username=username).exists()
                        if exists:
                            return JsonResponse(
                                {"status": "error", "message": "Username already exists"},
                                status=409
                            )
                        emp.user.username = username
                        user_changed = True

                if "email" in profile:
                    emp.user.email = _clean_str(profile.get("email")) or ""
                    user_changed = True

                if user_changed:
                    emp.user.save()

        # ==================================================
        # EMPLOYMENT
        # ==================================================
        elif section == "employment":
            profile = payload.get("profile") or {}

            if "employee_number" in profile:
                new_employee_number = _clean_str(profile.get("employee_number"))

                if new_employee_number:
                    exists = (
                        Employee.objects
                        .filter(company=company, employee_number=new_employee_number)
                        .exclude(id=emp.id)
                        .exists()
                    )
                    if exists:
                        return JsonResponse(
                            {"status": "error", "message": "Employee number already exists"},
                            status=409
                        )

                emp.employee_number = new_employee_number
                changed_fields.add("employee_number")

            if "employment_type" in profile:
                emp.employment_type = _clean_str(profile.get("employment_type"))
                changed_fields.add("employment_type")

            if "join_date" in profile:
                emp.join_date = _clean_date(profile.get("join_date"))
                changed_fields.add("join_date")

            if "work_start_date" in profile:
                emp.work_start_date = _clean_date(profile.get("work_start_date"))
                changed_fields.add("work_start_date")

            if "probation_end_date" in profile:
                emp.probation_end_date = _clean_date(profile.get("probation_end_date"))
                changed_fields.add("probation_end_date")

            if "end_date" in profile:
                emp.end_date = _clean_date(profile.get("end_date"))
                changed_fields.add("end_date")

            department_name = _clean_str(payload.get("department_name"))
            if department_name is not None:
                department = (
                    CompanyDepartment.objects
                    .filter(company=company, name__iexact=department_name)
                    .first()
                )
                emp.department = department
                changed_fields.add("department")
                biotime_sync_required = True

            job_title_name = _clean_str(payload.get("job_title_name"))
            if job_title_name is not None:
                job_title = (
                    JobTitle.objects
                    .filter(company=company, name__iexact=job_title_name)
                    .first()
                )
                emp.job_title = job_title
                changed_fields.add("job_title")
                biotime_sync_required = True

            work_schedule_name = _clean_str(payload.get("work_schedule_name"))
            if work_schedule_name is not None:
                schedule = (
                    WorkSchedule.objects
                    .filter(company=company, name__iexact=work_schedule_name)
                    .first()
                )
                emp.default_work_schedule = schedule
                changed_fields.add("default_work_schedule")

            work_schedule_status = _clean_str(payload.get("work_schedule_status"))
            if work_schedule_status and emp.default_work_schedule:
                desired = work_schedule_status.upper() == "ACTIVE"
                if emp.default_work_schedule.is_active != desired:
                    emp.default_work_schedule.is_active = desired
                    emp.default_work_schedule.save(update_fields=["is_active"])

        # ==================================================
        # DOCUMENTS
        # ==================================================
        elif section == "documents":
            profile = payload.get("profile") or {}

            if "national_id" in profile:
                emp.national_id = _clean_str(profile.get("national_id"))
                changed_fields.add("national_id")

            if "national_id_issue_date" in profile:
                emp.national_id_issue_date = _clean_date(profile.get("national_id_issue_date"))
                changed_fields.add("national_id_issue_date")

            if "national_id_expiry_date" in profile:
                emp.national_id_expiry_date = _clean_date(profile.get("national_id_expiry_date"))
                changed_fields.add("national_id_expiry_date")

            if "passport_number" in profile:
                emp.passport_number = _clean_str(profile.get("passport_number"))
                changed_fields.add("passport_number")

            if "passport_issue_date" in profile:
                emp.passport_issue_date = _clean_date(profile.get("passport_issue_date"))
                changed_fields.add("passport_issue_date")

            if "passport_expiry_date" in profile:
                emp.passport_expiry_date = _clean_date(profile.get("passport_expiry_date"))
                changed_fields.add("passport_expiry_date")

        # ==================================================
        # FINANCIAL
        # ==================================================
        elif section == "financial":
            financial_payload = payload.get("financial_info") or {}
            financial_obj, _ = FinancialInfo.objects.get_or_create(employee=emp)

            if "basic_salary" in financial_payload:
                financial_obj.basic_salary = _clean_float(financial_payload.get("basic_salary"), 0)

            if "housing_allowance" in financial_payload:
                financial_obj.housing_allowance = _clean_float(financial_payload.get("housing_allowance"), 0)

            if "transport_allowance" in financial_payload:
                financial_obj.transport_allowance = _clean_float(financial_payload.get("transport_allowance"), 0)

            if "food_allowance" in financial_payload:
                financial_obj.food_allowance = _clean_float(financial_payload.get("food_allowance"), 0)

            if "other_allowances" in financial_payload:
                financial_obj.other_allowances = _clean_float(financial_payload.get("other_allowances"), 0)

            if "bank_name" in financial_payload:
                financial_obj.bank_name = _clean_str(financial_payload.get("bank_name"))

            if "iban" in financial_payload:
                financial_obj.iban = _clean_str(financial_payload.get("iban"))

            if "is_gosi_enabled" in financial_payload:
                financial_obj.is_gosi_enabled = _clean_bool(financial_payload.get("is_gosi_enabled"))

            if "is_tax_enabled" in financial_payload:
                financial_obj.is_tax_enabled = _clean_bool(financial_payload.get("is_tax_enabled"))

            financial_obj.save()

        # ==================================================
        # LEGACY / GENERIC SUPPORT
        # ==================================================
        else:
            if "full_name" in payload:
                emp.full_name = _clean_str(payload["full_name"])
                changed_fields.add("full_name")
                biotime_sync_required = True

            if "department_id" in payload:
                emp.department = CompanyDepartment.objects.filter(
                    id=payload["department_id"],
                    company=company,
                ).first()
                changed_fields.add("department")
                biotime_sync_required = True

            if "job_title_id" in payload:
                emp.job_title = JobTitle.objects.filter(
                    id=payload["job_title_id"],
                    company=company,
                ).first()
                changed_fields.add("job_title")
                biotime_sync_required = True

            if "branch_ids" in payload:
                branch_ids = payload.get("branch_ids") or []
                if isinstance(branch_ids, list):
                    branches = CompanyBranch.objects.filter(
                        id__in=branch_ids,
                        company=company,
                    )
                    emp.branches.set(branches)
                    changed_fields.add("branches")
                    biotime_sync_required = True

        if changed_fields:
            emp.save()

        # ----------------------------------------------
        # Auto Sync State Handler
        # ----------------------------------------------
        try:
            from biotime_center.services.sync_state_handler import handle_employee_sync_event
            handle_employee_sync_event(emp)
        except Exception:
            logger.exception("Employee sync state handler failed | employee=%s", emp.id)

        # ----------------------------------------------
        # Biotime Auto Sync
        # ----------------------------------------------
        if emp.biotime_code and biotime_sync_required:
            try:
                from biotime_center.sync_service import (
                    patch_employee_areas_replace,
                    patch_employee_department,
                    patch_employee_name,
                    patch_employee_position,
                )

                logger.info(
                    "Biotime Auto Sync | company=%s | employee=%s | fields=%s",
                    company.id,
                    emp.id,
                    sorted(changed_fields),
                )

                if "full_name" in changed_fields and emp.full_name:
                    patch_employee_name(
                        company=company,
                        employee_id=str(emp.biotime_code),
                        full_name=emp.full_name,
                    )

                if "department" in changed_fields:
                    if emp.department and emp.department.biotime_code:
                        patch_employee_department(
                            company=company,
                            employee_id=str(emp.biotime_code),
                            dept_code=str(emp.department.biotime_code),
                        )

                if "job_title" in changed_fields:
                    position_id = None
                    if emp.job_title:
                        position_id = (
                            emp.job_title.biotime_position_id
                            or emp.job_title.biotime_code
                        )

                    if position_id:
                        patch_employee_position(
                            company=company,
                            employee_id=str(emp.biotime_code),
                            position_code=str(position_id),
                        )

                if "branches" in changed_fields:
                    area_codes = [
                        b.biotime_code
                        for b in emp.branches.all()
                        if b.biotime_code
                    ]

                    patch_employee_areas_replace(
                        company=company,
                        employee_id=str(emp.biotime_code),
                        area_codes=area_codes,
                    )

            except Exception:
                logger.exception(
                    "Biotime Auto Sync Failed | employee=%s",
                    emp.id,
                )

        # ----------------------------------------------
        # Return Fresh Detail Payload
        # ----------------------------------------------
        user = emp.user
        display_name = _get_display_full_name(user)
        display_email = user.email or ""
        display_phone = _get_display_phone(user)
        display_avatar = _get_display_avatar(user)
        display_role = _get_company_role_for_user(company, user)

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

        financial_obj = getattr(emp, "financial_info", None)
        financial_payload = None
        if financial_obj:
            financial_payload = {
                "basic_salary": float(financial_obj.basic_salary or 0),
                "housing_allowance": float(financial_obj.housing_allowance or 0),
                "transport_allowance": float(financial_obj.transport_allowance or 0),
                "food_allowance": float(financial_obj.food_allowance or 0),
                "other_allowances": float(financial_obj.other_allowances or 0),
                "is_gosi_enabled": financial_obj.is_gosi_enabled,
                "is_tax_enabled": financial_obj.is_tax_enabled,
                "bank_name": financial_obj.bank_name,
                "iban": financial_obj.iban,
            }

        return JsonResponse({
            "status": "success",
            "message": "Employee updated successfully",
            "employee": {
                "id": emp.id,
                "name": display_name,
                "full_name": display_name,
                "email": display_email,
                "phone": display_phone,
                "avatar": display_avatar,
                "photo_url": display_avatar,
                "role": display_role,
                "status_label": _map_user_status(user.is_active),
                "status": _map_user_status(user.is_active),
                "biotime_code": biotime_code,
                "biotime": biotime_payload,
                "financial_info": financial_payload,
                "profile": {
                    "full_name": display_name,
                    "email": display_email,
                    "mobile_number": display_phone,
                    "avatar": display_avatar,
                    "username": user.username,
                    "arabic_name": emp.arabic_name,
                    "date_of_birth": emp.date_of_birth,
                    "nationality": emp.nationality,
                    "gender": emp.gender,
                    "national_id": emp.national_id,
                    "national_id_issue_date": emp.national_id_issue_date,
                    "national_id_expiry_date": emp.national_id_expiry_date,
                    "passport_number": emp.passport_number,
                    "passport_issue_date": emp.passport_issue_date,
                    "passport_expiry_date": emp.passport_expiry_date,
                    "employment_type": emp.employment_type,
                    "employee_number": emp.employee_number,
                    "join_date": emp.join_date,
                    "work_start_date": emp.work_start_date,
                    "probation_end_date": emp.probation_end_date,
                    "end_date": emp.end_date,
                    "gosi_number": emp.gosi_number,
                },
                "department": (
                    {
                        "id": emp.department.id,
                        "name": emp.department.name,
                    }
                    if emp.department else None
                ),
                "job_title": (
                    {
                        "id": emp.job_title.id,
                        "name": emp.job_title.name,
                    }
                    if emp.job_title else None
                ),
                "default_work_schedule": (
                    {
                        "id": emp.default_work_schedule.id,
                        "name": emp.default_work_schedule.name,
                        "is_active": emp.default_work_schedule.is_active,
                    }
                    if emp.default_work_schedule else None
                ),
                "branches": [
                    {
                        "id": b.id,
                        "name": b.name,
                        "biotime_code": b.biotime_code,
                    }
                    for b in emp.branches.all()
                ],
                "created_at": emp.created_at,
                "updated_at": emp.updated_at,
            },
            "updated_fields": sorted(changed_fields),
            "section": section,
        })

    except ValueError as exc:
        return JsonResponse(
            {"status": "error", "message": str(exc)},
            status=400
        )
    except Exception:
        logger.exception("Employee update failed | employee=%s", employee_id)
        return JsonResponse(
            {"status": "error", "message": "Unexpected server error"},
            status=500
        )


# ======================================================
# 🧍 Profile Update
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
        "work_start_date",
        "mobile_number",
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

    if emp.biotime_code and "full_name" in updated_fields:
        try:
            from biotime_center.sync_service import patch_employee_name

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
# 🔁 Toggle User Status
# ======================================================

@csrf_exempt
@require_POST
@login_required
def employee_toggle_status(request, employee_id):
    company_user = _resolve_active_company_user(request)
    if not company_user:
        return JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )

    try:
        emp = Employee.objects.select_related("user").get(
            id=employee_id,
            company=company_user.company,
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employee not found"},
            status=404,
        )

    new_state = not emp.user.is_active
    emp.user.is_active = new_state
    emp.user.save(update_fields=["is_active"])

    target_company_user = (
        CompanyUser.objects
        .filter(
            user=emp.user,
            company=company_user.company,
        )
        .order_by("-id")
        .first()
    )

    if not target_company_user:
        logger.warning(
            "CompanyUser missing for status toggle | company=%s | employee=%s | user=%s | auto-heal=create",
            company_user.company.id,
            emp.id,
            emp.user_id,
        )
        CompanyUser.objects.create(
            company=company_user.company,
            user=emp.user,
            role="EMPLOYEE",
            is_active=new_state,
        )
    else:
        target_company_user.is_active = new_state
        target_company_user.save(update_fields=["is_active"])

    # =====================================================
    # 🔔 Notification Center Hook — Employee Status
    # المسار الرسمي الموحد بدل الإرسال المباشر من الـ API
    # =====================================================
    try:
        if new_state:
            notify_employee_activated(
                emp,
                send_email_to_employee=True,
                send_email_to_managers=False,
                send_whatsapp_to_employee=True,
                send_whatsapp_to_managers=True,
            )
        else:
            notify_employee_deactivated(
                emp,
                send_email_to_employee=True,
                send_email_to_managers=False,
                send_whatsapp_to_employee=True,
                send_whatsapp_to_managers=True,
            )
    except Exception:
        logger.exception(
            "⚠ Employee status notification hook failed (non-blocking) | employee=%s",
            emp.id,
        )

    return JsonResponse({
        "status": "success",
        "employee_status": _map_user_status(new_state),
        "is_active": new_state,
    })


# ======================================================
# 🔐 Change Company User Role
# ======================================================

@csrf_exempt
@require_POST
@login_required
def employee_change_role(request, employee_id):
    company_user = _resolve_active_company_user(request)
    if not company_user:
        return JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )

    if not _can_manage_company_users(company_user):
        return JsonResponse(
            {"status": "error", "message": "You do not have permission to change roles"},
            status=403,
        )

    payload = _parse_body(request)
    new_role = _normalize_company_role_value(payload.get("role"))

    if new_role not in ALLOWED_COMPANY_ROLES:
        return JsonResponse(
            {"status": "error", "message": "Invalid role"},
            status=400,
        )

    try:
        emp = Employee.objects.select_related("user").get(
            id=employee_id,
            company=company_user.company,
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employee not found"},
            status=404,
        )

    # --------------------------------------------------
    # ✅ Auto-Heal Legacy Data
    # إذا لم يوجد CompanyUser لهذا الموظف داخل نفس الشركة
    # يتم إنشاؤه تلقائيًا بدور EMPLOYEE بدل الفشل
    # --------------------------------------------------
    target_company_user = (
        CompanyUser.objects
        .select_related("user")
        .filter(
            company=company_user.company,
            user=emp.user,
        )
        .order_by("-id")
        .first()
    )

    if not target_company_user:
        logger.warning(
            "CompanyUser missing for employee role change | company=%s | employee=%s | user=%s | auto-heal=create",
            company_user.company.id,
            emp.id,
            emp.user_id,
        )

        target_company_user = CompanyUser.objects.create(
            company=company_user.company,
            user=emp.user,
            role="EMPLOYEE",
            is_active=bool(emp.user.is_active),
        )

    current_actor_role = _normalize_company_role_value(company_user.role)
    current_target_role = _normalize_company_role_value(target_company_user.role)

    if target_company_user.user_id == request.user.id and current_actor_role == "OWNER":
        return JsonResponse(
            {"status": "error", "message": "Owner cannot change their own role"},
            status=409,
        )

    if current_actor_role != "OWNER" and current_target_role == "OWNER":
        return JsonResponse(
            {"status": "error", "message": "Only owner can modify owner role"},
            status=403,
        )

    if current_actor_role != "OWNER" and new_role == "OWNER":
        return JsonResponse(
            {"status": "error", "message": "Only owner can assign owner role"},
            status=403,
        )

    if current_target_role == new_role:
        return JsonResponse({
            "status": "success",
            "message": "Role already assigned",
            "role": current_target_role,
        })

    target_company_user.role = new_role
    target_company_user.is_active = bool(emp.user.is_active)
    target_company_user.save(update_fields=["role", "is_active"])

    return JsonResponse({
        "status": "success",
        "message": "User role updated successfully",
        "role": new_role,
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

    if not schedule.is_active:
        return JsonResponse(
            {
                "status": "error",
                "message": "لا يمكن ربط جدول غير نشط",
            },
            status=409,
        )

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


# ======================================================
# 🔗 Adapter — Update Job Info
# ======================================================

@csrf_exempt
@require_POST
@login_required
@transaction.atomic
def employee_update_job_info(request, employee_id):
    company = _resolve_company(request)
    if not company:
        return JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )

    try:
        payload = _parse_body(request)
    except Exception:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON payload"},
            status=400,
        )

    try:
        response = employee_update(request, employee_id)

        if response.status_code != 200:
            return response

    except Exception:
        logger.exception(
            "Adapter failed at employee_update | employee=%s",
            employee_id,
        )
        return JsonResponse(
            {
                "status": "error",
                "message": "Failed updating job core data",
            },
            status=500,
        )

    schedule_id = payload.get("work_schedule_id")

    if schedule_id:
        try:
            from django.test.client import RequestFactory

            factory = RequestFactory()

            schedule_request = factory.post(
                "/internal/assign-work-schedule/",
                data=json.dumps({"schedule_id": schedule_id}),
                content_type="application/json",
            )

            schedule_request.user = request.user
            schedule_request.session = request.session

            schedule_response = employee_assign_work_schedule(
                schedule_request,
                employee_id,
            )

            if schedule_response.status_code not in (200, 201):
                return schedule_response

        except Exception:
            logger.exception(
                "Adapter failed at assign_work_schedule | employee=%s",
                employee_id,
            )
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Failed assigning work schedule",
                },
                status=500,
            )

    return JsonResponse(
        {
            "status": "success",
            "message": "Employee job info updated successfully",
        }
    )


# ============================================================
# 🧩 Employee Profile Update API
# ============================================================

@csrf_exempt
@login_required
@require_POST
@transaction.atomic
def update_employee_profile(request, employee_id):
    company_user = _resolve_active_company_user(request)
    if not company_user:
        return JsonResponse(
            {"message": "Company context not found"},
            status=403
        )

    company = company_user.company

    try:
        employee = Employee.objects.select_for_update().get(
            id=employee_id,
            company=company
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"message": "Employee not found"},
            status=404
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse(
            {"message": "Invalid JSON payload"},
            status=400
        )

    ALLOWED_FIELDS = {
        "full_name",
        "arabic_name",
        "national_id",
        "national_id_issue_date",
        "national_id_expiry_date",
        "passport_number",
        "passport_issue_date",
        "passport_expiry_date",
        "nationality",
        "gender",
        "employment_type",
        "employee_number",
        "join_date",
        "probation_end_date",
        "end_date",
        "gosi_number",
        "work_start_date",
        "mobile_number",
    }

    DATE_FIELDS = {
        "join_date",
        "probation_end_date",
        "end_date",
        "national_id_issue_date",
        "national_id_expiry_date",
        "passport_issue_date",
        "passport_expiry_date",
        "work_start_date",
    }

    updated_fields = []

    for field, value in payload.items():
        if field not in ALLOWED_FIELDS:
            continue

        if not hasattr(employee, field):
            continue

        if value in (None, ""):
            continue

        if field == "employee_number":
            exists = (
                Employee.objects
                .filter(company=company, employee_number=value)
                .exclude(id=employee.id)
                .exists()
            )
            if exists:
                return JsonResponse(
                    {"message": "Employee number already exists"},
                    status=409
                )

        if field in DATE_FIELDS:
            try:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse(
                    {"message": f"Invalid date format for {field}"},
                    status=400
                )

        setattr(employee, field, value)
        updated_fields.append(field)

    if updated_fields:
        employee.save(update_fields=updated_fields)

    if (
        "full_name" in updated_fields
        and employee.biotime_code
        and employee.full_name
    ):
        try:
            from biotime_center.sync_service import patch_employee_name

            patch_employee_name(
                company=company,
                employee_id=str(employee.biotime_code),
                full_name=str(employee.full_name),
            )

        except Exception:
            logger.exception(
                "Biotime Name Sync Failed | employee=%s",
                employee.id,
            )

    return JsonResponse(
        {
            "status": "updated",
            "updated_fields": updated_fields,
        },
        status=200
    )


# ============================================================
# 💰 Employee Financial Update API
# ============================================================

@csrf_exempt
@login_required
@require_POST
@transaction.atomic
def update_employee_financial(request, employee_id):
    company_user = _resolve_active_company_user(request)
    if not company_user:
        return JsonResponse(
            {"message": "Company context not found"},
            status=403
        )

    company = company_user.company

    try:
        employee = Employee.objects.select_for_update().get(
            id=employee_id,
            company=company
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"message": "Employee not found"},
            status=404
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse(
            {"message": "Invalid JSON payload"},
            status=400
        )

    financial_obj, _ = FinancialInfo.objects.get_or_create(
        employee=employee
    )

    ALLOWED_FIELDS = {
        "basic_salary",
        "housing_allowance",
        "transport_allowance",
        "food_allowance",
        "other_allowances",
        "is_gosi_enabled",
        "is_tax_enabled",
        "bank_name",
        "iban",
    }

    numeric_fields = {
        "basic_salary",
        "housing_allowance",
        "transport_allowance",
        "food_allowance",
        "other_allowances",
    }

    updated_fields = []

    for field, value in payload.items():
        if field not in ALLOWED_FIELDS:
            continue

        if not hasattr(financial_obj, field):
            continue

        if field in numeric_fields:
            try:
                value = float(value or 0)
            except (TypeError, ValueError):
                return JsonResponse(
                    {"message": f"Invalid number for {field}"},
                    status=400
                )

        if field in {"bank_name", "iban"}:
            value = _clean_str(value)

        setattr(financial_obj, field, value)
        updated_fields.append(field)

    if updated_fields:
        financial_obj.save(update_fields=updated_fields)

    return JsonResponse(
        {
            "status": "updated",
            "updated_fields": updated_fields,
        },
        status=200
    )


# ============================================================
# 🔎 Employee Search API
# ============================================================

@require_GET
@login_required
def employee_search(request):
    company = _resolve_company(request)

    if not company:
        return JsonResponse(
            {"error": "NO_COMPANY_CONTEXT"},
            status=403
        )

    query = request.GET.get("q", "").strip()
    query = query.replace("/", "")

    if not query:
        return JsonResponse([], safe=False)

    employees = (
        Employee.objects
        .filter(company=company)
        .filter(
            Q(full_name__icontains=query)
            | Q(arabic_name__icontains=query)
            | Q(employee_number__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__email__icontains=query)
        )
        .order_by("full_name")[:20]
    )

    data = [
        {
            "id": e.id,
            "name": _get_display_full_name(e.user),
        }
        for e in employees
    ]

    return JsonResponse(data, safe=False)


# ======================================================
# 🔄 POST /api/company/switch/
# ======================================================

@require_POST
@login_required
def switch_company(request):
    company_id = None

    content_type = request.headers.get("Content-Type", "")

    if "application/json" in content_type:
        try:
            body = request.body.decode("utf-8")
            if body:
                data = json.loads(body)
                company_id = data.get("company_id")
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "invalid JSON payload"},
                status=400
            )

    if not company_id:
        company_id = request.POST.get("company_id")

    if not company_id:
        return JsonResponse(
            {"error": "company_id required"},
            status=400
        )

    try:
        company_id = int(company_id)
    except (ValueError, TypeError):
        return JsonResponse(
            {"error": "invalid company_id"},
            status=400
        )

    company_user = (
        CompanyUser.objects
        .select_related("company")
        .filter(
            user=request.user,
            company_id=company_id,
            is_active=True,
            company__isnull=False,
        )
        .first()
    )

    if not company_user:
        return JsonResponse(
            {"error": "unauthorized company"},
            status=403
        )

    request.session["active_company_id"] = company_id
    request.session.modified = True

    return JsonResponse({
        "status": "switched",
        "company_id": company_id,
    })