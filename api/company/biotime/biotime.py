# ================================================================
# 📂 api/company/biotime/biotime.py
# 🔌 Biotime Company APIs — JWT Integration
# 🔒 Phase B — Data Integrity Hardening
# ================================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.shortcuts import get_object_or_404

import json
import logging
import uuid
from urllib.parse import urlparse
import re
import requests

from biotime_center.models import (
    BiotimeEmployee,
    BiotimeSyncLog,
    BiotimeSetting,
)

from biotime_center.sync_service import (
    test_connection,
    sync_devices,
    sync_employees,
    append_employee_area,
    push_employee_to_biotime,
    patch_employee_department,
    patch_employee_position,
)

from company_manager.models import CompanyUser
from employee_center.models import Employee

from employee_center.services.biotime_linker import link_biotime_employees

logger = logging.getLogger(__name__)

# ================================================================
# 🔐 Internal Helpers
# ================================================================

TEST_LOCK_KEY = "biotime:test-connection:lock"
TEST_LOCK_TTL = 15

PUSH_LOCK_PREFIX = "biotime:push-employee:"
PUSH_LOCK_TTL = 20


def _trace_id():
    return uuid.uuid4().hex[:12]


def resolve_company_user(request):
    return (
        CompanyUser.objects
        .select_related("company")
        .filter(
            user=request.user,
            is_active=True,
            company__isnull=False,
        )
        .order_by("-id")
        .first()
    )


def api_success(**payload):
    return JsonResponse({"status": "success", **payload}, status=200)


def api_error(message, status=400, **extra):
    return JsonResponse(
        {"status": "error", "message": message, **extra},
        status=status
    )


# ================================================================
# 🚀 API — Push Employee To Biotime (PATCHED FLOW)
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_push_employee(request, employee_id: int):
    """
    إنشاء موظف من Primey HR داخل Biotime.
    - Create Employee
    - Patch Department
    - Patch Position
    - Append Areas
    """

    trace = _trace_id()
    company_user = resolve_company_user(request)

    if not company_user:
        return api_error("Company context not found.", status=403)

    lock_key = f"{PUSH_LOCK_PREFIX}{employee_id}"
    if cache.get(lock_key):
        return api_error(
            "⏳ عملية الإرسال قيد التنفيذ بالفعل.",
            status=429,
            trace_id=trace,
        )

    cache.set(lock_key, True, PUSH_LOCK_TTL)

    try:
        employee = get_object_or_404(
            Employee,
            id=employee_id,
            company=company_user.company,
        )

        if employee.biotime_code:
            return api_error(
                "الموظف مرتبط مسبقًا مع Biotime.",
                status=409,
                trace_id=trace,
            )

        # ======================================================
        # 🔒 Validation
        # ======================================================
        if not employee.full_name:
            return api_error("اسم الموظف مطلوب.", trace_id=trace)

        if not employee.department or not employee.job_title:
            return api_error(
                "يجب تحديد القسم والمسمى الوظيفي.",
                trace_id=trace,
            )

        dept_code = employee.department.biotime_code
        job_code = employee.job_title.biotime_code

        if not dept_code or not job_code:
            return api_error(
                "القسم أو المسمى غير مربوط مع Biotime.",
                trace_id=trace,
            )

        branches = list(employee.branches.all())
        area_codes = [b.biotime_code for b in branches if b.biotime_code]

        if not area_codes:
            return api_error(
                "يجب تحديد فرع واحد على الأقل.",
                trace_id=trace,
            )

        # ======================================================
        # 1️⃣ Create Employee (Do NOT hard-fail here)
        # ======================================================
        name_parts = employee.full_name.strip().split(" ")
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) or "-"

        create_result = push_employee_to_biotime(
            emp_code=str(employee.id),
            first_name=first_name,
            last_name=last_name,
            area_codes=area_codes,
            dept_code=dept_code,
            position_code=job_code,
            is_active=True,
        )

        if create_result.get("status") != "success":
            logger.warning(
                "[%s] Biotime CREATE returned warning: %s",
                trace,
                create_result,
            )

        # ======================================================
        # 2️⃣ Patch Department (MANDATORY)
        # ======================================================
        patch_employee_department(
            employee_biotime_id=str(employee.id),
            new_department_code=dept_code,
        )

        # ======================================================
        # 3️⃣ Patch Position (SAFE)
        # ======================================================
        patch_employee_position(
            employee_biotime_id=str(employee.id),
            new_position_code=job_code,
        )

        # ======================================================
        # 4️⃣ Append Areas (if multiple)
        # ======================================================
        for area_code in area_codes[1:]:
            append_employee_area(
                employee_biotime_id=str(employee.id),
                new_area_code=area_code,
            )

        # ======================================================
        # 💾 Save Local Link
        # ======================================================
        with transaction.atomic():
            employee.biotime_code = str(employee.id)
            employee.save(update_fields=["biotime_code"])

            BiotimeEmployee.objects.create(
                employee_id=str(employee.id),
                full_name=employee.full_name,
                department=dept_code,
                position=job_code,
                is_active=True,
            )

        logger.info(
            "[%s] Biotime PUSH fully completed | employee=%s",
            trace,
            employee.id,
        )

        return api_success(
            message="✔ تم إنشاء وربط الموظف مع Biotime بنجاح.",
            biotime_code=str(employee.id),
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Biotime Push Employee Fatal Error", trace)
        return api_error(
            "❌ حدث خطأ غير متوقع أثناء إرسال الموظف.",
            status=500,
            trace_id=trace,
        )

    finally:
        cache.delete(lock_key)
