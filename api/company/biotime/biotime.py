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
    get_authenticated_client,
    resolve_employee_biotime_id,
    create_or_sync_department,
    create_or_sync_jobtitle,
    create_or_sync_branch,
    patch_employee_name,
    push_employee_to_biotime,
    patch_employee_department,
    patch_employee_position,
    patch_employee_area,
    append_employee_area,
    sync_employees,
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
# 🔄 API — Sync Existing Employee To Biotime (Replace Mode)
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_sync_employee(request, employee_id: int):
    """
    مزامنة بيانات موظف موجود مسبقًا في BioTime.
    Replace Mode:
        - Name
        - Department
        - Position
        - Areas (Branches)
    Company Scoped
    """

    trace = _trace_id()
    company_user = resolve_company_user(request)

    if not company_user or not company_user.company:
        return api_error(
            "Company context not found.",
            status=403,
            trace_id=trace,
        )

    company = company_user.company

    try:
        # ------------------------------------------------------
        # 🔎 Fetch Employee (Company Strict)
        # ------------------------------------------------------
        employee = get_object_or_404(
            Employee,
            id=employee_id,
            company=company,
        )

        if not employee.biotime_code:
            return api_error(
                "الموظف غير مرتبط مع BioTime.",
                trace_id=trace,
            )

        # ------------------------------------------------------
        # 🔐 Auth Client (Company Scoped)
        # ------------------------------------------------------
        client, error = get_authenticated_client(company=company)
        if error or not client:
            return api_error(
                "فشل المصادقة مع BioTime.",
                trace_id=trace,
            )

        # ------------------------------------------------------
        # 🧠 Name Sync
        # ------------------------------------------------------
        name_ok = patch_employee_name(
            company=company,
            employee_id=employee.biotime_code,
            full_name=employee.full_name,
        )

        # ------------------------------------------------------
        # 🧠 Department Sync
        # ------------------------------------------------------
        dept_ok = patch_employee_department(
            company=company,
            employee_id=employee.biotime_code,
            dept_code=employee.department.biotime_code,
        )

        # ------------------------------------------------------
        # 🧠 Position Sync
        # ------------------------------------------------------
        pos_ok = patch_employee_position(
            company=company,
            employee_id=employee.biotime_code,
            position_code=employee.job_title.biotime_code,
        )

        # ------------------------------------------------------
        # 🧠 Areas Sync (Replace Mode)
        # ------------------------------------------------------
        branches = list(employee.branches.all())
        area_codes = [b.biotime_code for b in branches]

        # تحويل الأكواد إلى IDs
        from biotime_center.sync_service import resolve_area_id_by_code

        area_ids = []
        for code in area_codes:
            area_id = resolve_area_id_by_code(client, str(code))
            if area_id:
                area_ids.append(int(area_id))

        area_ok = True
        if area_ids:
            area_ok = patch_employee_area(
                client,
                employee_id=employee.biotime_code,
                area_ids=area_ids,
            )

        # ------------------------------------------------------
        # 🛡 Final Check
        # ------------------------------------------------------
        if not all([name_ok, dept_ok, pos_ok, area_ok]):
            return api_error(
                "فشل مزامنة بعض البيانات مع BioTime.",
                trace_id=trace,
            )

        logger.info(
            "[%s] Employee synced to BioTime | employee=%s | company=%s",
            trace,
            employee.id,
            company.id,
        )

        return api_success(
            message="✔ تم مزامنة بيانات الموظف بنجاح.",
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Sync Employee Error", trace)
        return api_error(
            "❌ حدث خطأ أثناء مزامنة الموظف.",
            status=500,
            trace_id=trace,
        )

# ================================================================
# 🔄 API — Sync Employees (DRY-RUN ONLY ✅)
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_sync_employees(request):
    """
    مزامنة موظفي Biotime + تحليل الربط مع Primey (Dry-Run فقط).
    - لا تنفيذ فعلي
    - لا تعديل DB
    - متوافقة مع Local & Production
    """

    trace = _trace_id()
    company_user = resolve_company_user(request)

    if not company_user or not company_user.company:
        return api_error(
            "Company context not found.",
            status=403,
            trace_id=trace,
        )

    # ============================================================
    # 🔒 Lock محلي (بدون Global Dependency)
    # ============================================================
    lock_key = f"biotime:sync-employees:lock:{company_user.company_id}"
    lock_ttl = 30  # seconds

    if cache.get(lock_key):
        return api_error(
            "⏳ عملية مزامنة الموظفين قيد التنفيذ حاليًا.",
            status=429,
            trace_id=trace,
        )

    cache.set(lock_key, True, lock_ttl)

    try:
        # --------------------------------------------------------
        # 🔍 Resolve Biotime Settings (Company Scoped – Validation فقط)
        # --------------------------------------------------------
        setting = (
            BiotimeSetting.objects
            .filter(company=company_user.company)
            .first()
        )

        if not setting:
            return api_error(
                "إعدادات Biotime غير مهيأة.",
                trace_id=trace,
            )

        # --------------------------------------------------------
        # 🔁 1) Sync Employees from Biotime → Local DB
        # --------------------------------------------------------
        sync_result = sync_employees(company=company_user.company)

        if not isinstance(sync_result, dict):
            return api_error(
                "استجابة غير صالحة من محرك المزامنة.",
                details=sync_result,
                trace_id=trace,
            )

        if sync_result.get("status") != "success":
            return api_error(
                "فشل جلب موظفي Biotime.",
                details=sync_result,
                trace_id=trace,
            )

        # --------------------------------------------------------
        # 🧠 2) Smart Linking (DRY-RUN ONLY)
        # --------------------------------------------------------
        link_result = link_biotime_employees(
            company=company_user.company,
            execute=False,
        )

        logger.info(
            "[%s] Biotime Sync Employees DRY-RUN completed | company_id=%s | total=%s",
            trace,
            company_user.company_id,
            sync_result.get("total"),
        )

        # --------------------------------------------------------
        # ✅ لا تعتبر total=0 خطأ
        # --------------------------------------------------------
        return api_success(
            message="✔ تم فحص موظفي Biotime وربطهم (Dry-Run فقط).",
            sync=sync_result,
            linking=link_result,
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Biotime Sync Employees Fatal Error", trace)
        return api_error(
            "❌ حدث خطأ غير متوقع أثناء مزامنة الموظفين.",
            status=500,
            trace_id=trace,
        )

    finally:
        cache.delete(lock_key)

# ================================================================
# 📦 API — Unlinked Biotime Employees (SELECT SOURCE)
# ================================================================
@login_required
def company_biotime_employees(request):

    trace = _trace_id()
    company_user = resolve_company_user(request)

    if not company_user or not company_user.company:
        return api_error(
            "Company context not found.",
            status=403,
            trace_id=trace,
        )

    try:
        company = company_user.company

        # --------------------------------------------------
        # 🔗 Get linked codes (Scoped)
        # --------------------------------------------------
        linked_codes = set(
            Employee.objects
            .filter(company=company)
            .exclude(biotime_code__isnull=True)
            .values_list("biotime_code", flat=True)
        )

        # --------------------------------------------------
        # 🧬 Fetch Company-Scoped Biotime Employees
        # 🔒 MT-6 Strict Mode
        # --------------------------------------------------
        bios = (
            BiotimeEmployee.objects
            .filter(company=company)
            .order_by("full_name")
        )

        data = []

        for bio in bios:

            code = (bio.employee_id or "").strip()
            is_linked = code in linked_codes

            data.append({
                "id": bio.id,
                "biotime_code": code,
                "full_name": bio.full_name,
                "department": bio.department,
                "position": bio.position,
                "is_active": bio.is_active,
                "is_linked": is_linked,
            })

        return api_success(
            employees=data,
            total=len(data),
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Load Biotime Employees Error", trace)
        return api_error(
            "❌ فشل تحميل موظفي Biotime.",
            status=500,
            trace_id=trace,
        )

# ================================================================
# 🔌 API — Test Biotime Account Connection (SAFE)
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_test_connection(request):
    """
    اختبار اتصال حساب Biotime (Account-level).
    - يتحقق من الإعدادات
    - يجرب الاتصال الحقيقي
    - يعيد status فقط
    """

    trace = _trace_id()
    company_user = resolve_company_user(request)

    if not company_user or not company_user.company:
        return api_error(
            "Company context not found.",
            status=403,
            trace_id=trace,
        )

    company = company_user.company

    # 🔒 Prevent rapid duplicate tests (Company Scoped)
    lock_key = f"{TEST_LOCK_KEY}:{company.id}"

    if cache.get(lock_key):
        return api_error(
            "⏳ يتم تنفيذ اختبار الاتصال حاليًا، حاول بعد لحظات.",
            status=429,
            trace_id=trace,
        )

    cache.set(lock_key, True, TEST_LOCK_TTL)

    try:
        # --------------------------------------------------------
        # 🔍 Resolve Company-Scoped Biotime Setting
        # --------------------------------------------------------
        setting = (
            BiotimeSetting.objects
            .filter(company=company)
            .first()
        )

        if not setting:
            return api_error(
                "غير مهيأ إعدادات BioTime.",
                status=400,
                trace_id=trace,
            )

        # --------------------------------------------------------
        # 🔗 Actual connection test
        # --------------------------------------------------------
        from biotime_center.sync_service import test_connection

        result = test_connection(company=company)

        if not isinstance(result, dict):
            return api_error(
                "استجابة غير صالحة من محرك الاختبار.",
                status=500,
                trace_id=trace,
            )

        if result.get("status") == "success":
            return api_success(
                connected=True,
                message="✔ تم الاتصال بـ Biotime بنجاح.",
                trace_id=trace,
            )

        return api_error(
            message=result.get("message", "فشل الاتصال بـ Biotime."),
            status=400,
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Biotime Test Connection Fatal Error", trace)
        return api_error(
            "❌ حدث خطأ غير متوقع أثناء اختبار الاتصال.",
            status=500,
            trace_id=trace,
        )

    finally:
        cache.delete(lock_key)

# ================================================================
# 💾 API — Save Biotime Settings (PRODUCTION SAFE ✅)
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_save_settings(request):
    """
    حفظ إعدادات Biotime (Company Scoped).
    - يقبل company أو company_code
    - يقبل email أو username
    - يسمح بالإبقاء على كلمة المرور القديمة إن لم تُرسل
    - يتحقق من HTTPS
    """

    trace = _trace_id()
    company_user = resolve_company_user(request)

    if not company_user or not company_user.company:
        return api_error(
            "Company context not found.",
            status=403,
            trace_id=trace,
        )

    try:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return api_error(
                "JSON payload غير صالح.",
                trace_id=trace,
            )

        server_url = str(payload.get("server_url", "")).strip()
        company_code = str(
            payload.get("company") or payload.get("company_code") or ""
        ).strip()
        email = str(
            payload.get("email") or payload.get("username") or ""
        ).strip()
        password = str(payload.get("password", "")).strip()

        # ======================================================
        # 🔍 Resolve existing setting first
        # ======================================================
        setting, _ = BiotimeSetting.objects.get_or_create(
            company=company_user.company,
        )

        existing_password = str(getattr(setting, "password", "") or "").strip()

        # ======================================================
        # 🔒 Validation
        # ======================================================
        if not server_url:
            return api_error(
                "رابط السيرفر مطلوب.",
                trace_id=trace,
            )

        if not company_code:
            return api_error(
                "رمز الشركة في BioTime مطلوب.",
                trace_id=trace,
            )

        if not email:
            return api_error(
                "البريد الإلكتروني أو اسم المستخدم مطلوب.",
                trace_id=trace,
            )

        if not password:
            password = existing_password

        if not password:
            return api_error(
                "كلمة المرور مطلوبة.",
                trace_id=trace,
            )

        if not server_url.startswith("https://"):
            return api_error(
                "يجب استخدام HTTPS.",
                trace_id=trace,
            )

        # ======================================================
        # 💾 Save Settings
        # ======================================================
        setting.server_url = server_url
        setting.email = email
        setting.password = password
        setting.biotime_company = company_code
        setting.is_active = True
        setting.last_connected_at = timezone.now()
        setting.save()

        logger.info(
            "[%s] Biotime settings saved | company=%s | biotime_company=%s | email=%s",
            trace,
            company_user.company_id,
            company_code,
            email,
        )

        return api_success(
            message="✔ تم حفظ إعدادات Biotime بنجاح.",
            connected=True,
            server_url=setting.server_url,
            email=setting.email,
            biotime_company=getattr(setting, "biotime_company", "") or "",
            trace_id=trace,
        )    
    except Exception:
        logger.exception("[%s] Save Biotime Settings Error", trace)
        return api_error(
            "❌ فشل حفظ إعدادات Biotime.",
            status=500,
            trace_id=trace,
        )


# ================================================================
# 🔎 API — Biotime Status (READ ONLY | DB SOURCE OF TRUTH)
# ================================================================
from django.views.decorators.http import require_GET

@csrf_exempt
@login_required
@require_GET
def company_biotime_status(request):
    """
    حالة اتصال Biotime (DB-Based).
    - لا اختبار اتصال
    - لا calls خارجية
    - يعتمد فقط على BiotimeSetting
    - متوافق مع جميع النسخ (company scoped)
    """

    trace = _trace_id()
    company_user = resolve_company_user(request)

    if not company_user:
        return api_error(
            "Company context not found.",
            status=403,
            trace_id=trace,
        )

    try:
        # ======================================================
        # 🔍 Resolve BiotimeSetting (Company Scoped)
        # ======================================================
        setting = (
            BiotimeSetting.objects
            .filter(company=company_user.company)
            .first()
        )

        # ======================================================
        # ❌ No settings configured
        # ======================================================
        if not setting:
            return api_success(
                connected=False,
                reason="no_settings",
                trace_id=trace,
            )

        # ======================================================
        # 🧠 Optional Fields Safe Access
        # ======================================================
        last_connected_at = getattr(setting, "last_connected_at", None)

        # ======================================================
        # ✅ Connected (DB is source of truth)
        # ======================================================
        return api_success(
            connected=True,
            server_url=setting.server_url,
            email=setting.email,
            biotime_company=getattr(setting, "biotime_company", "") or "",
            last_connected_at=last_connected_at,
            trace_id=trace,
        )
    except Exception:
        logger.exception("[%s] Biotime Status Fatal Error", trace)
        return api_error(
            "❌ Failed to load Biotime status.",
            status=500,
            trace_id=trace,
        )

# ================================================================
# 📜 API — Biotime Sync Logs (READ ONLY | SAFE)
# ================================================================
@login_required
def company_biotime_sync_logs(request):
    """
    عرض سجلات مزامنة Biotime.
    - Read Only
    - بدون company filter (model لا يحتوي company)
    - آخر 20 سجل
    """

    trace = _trace_id()
    company_user = resolve_company_user(request)

    if not company_user:
        return api_error(
            "Company context not found.",
            status=403,
            trace_id=trace,
        )

    try:
        logs = (
            BiotimeSyncLog.objects
            .order_by("-timestamp")[:20]
        )

        data = [
            {
                "id": log.id,
                "status": log.status,
                "message": log.message,
                "devices_synced": log.devices_synced,
                "employees_synced": log.employees_synced,
                "logs_synced": log.logs_synced,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ]

        return api_success(
            logs=data,
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Load Biotime Sync Logs Error", trace)
        return api_error(
            "❌ فشل تحميل سجلات المزامنة.",
            status=500,
            trace_id=trace,
        )
# ================================================================
# 🚀 API — Push Employee To Biotime (STRICT | MT SAFE)
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_push_employee(request, employee_id: int):
    """
    إنشاء موظف في BioTime وربطه محليًا.
    - Company Scoped
    - Lock Protected
    - Idempotent Safe
    """

    trace = _trace_id()
    company_user = resolve_company_user(request)

    if not company_user or not company_user.company:
        return api_error(
            "Company context not found.",
            status=403,
            trace_id=trace,
        )

    company = company_user.company

    # ============================================================
    # 🔒 Lock Per Employee (Company Scoped)
    # ============================================================
    lock_key = f"{PUSH_LOCK_PREFIX}{company.id}:{employee_id}"

    if cache.get(lock_key):
        return api_error(
            "⏳ عملية الإرسال قيد التنفيذ.",
            status=429,
            trace_id=trace,
        )

    cache.set(lock_key, True, PUSH_LOCK_TTL)

    try:
        # --------------------------------------------------------
        # 🔍 Get Employee (Company Strict)
        # --------------------------------------------------------
        employee = get_object_or_404(
            Employee,
            id=employee_id,
            company=company,
        )

        # --------------------------------------------------------
        # 🛡️ Idempotency Guard
        # --------------------------------------------------------
        if employee.biotime_code:
            return api_success(
                message="✔ الموظف مرتبط مسبقًا مع Biotime.",
                biotime_code=employee.biotime_code,
                trace_id=trace,
            )

        if not employee.full_name:
            return api_error("اسم الموظف مطلوب.", trace_id=trace)

        if not employee.department or not employee.job_title:
            return api_error(
                "يجب تحديد القسم والمسمى الوظيفي.",
                trace_id=trace,
            )

        branches = list(employee.branches.all())

        if not branches:
            return api_error(
                "يجب تحديد فرع واحد على الأقل.",
                trace_id=trace,
            )

        # --------------------------------------------------------
        # 🧠 Master Data Sync
        # --------------------------------------------------------
        create_or_sync_department(employee.department)
        create_or_sync_jobtitle(employee.job_title)

        for branch in branches:
            create_or_sync_branch(branch)

        area_codes = [b.biotime_code for b in branches]
        dept_code = employee.department.biotime_code
        job_code = employee.job_title.biotime_code

        # --------------------------------------------------------
        # 🔢 Generate emp_code (Company Scoped)
        # --------------------------------------------------------
        BASE_START = 1001

        local_codes = (
            Employee.objects
            .filter(company=company)
            .exclude(biotime_code__isnull=True)
            .values_list("biotime_code", flat=True)
        )

        local_numbers = [
            int(c) for c in local_codes if str(c).isdigit()
        ]

        max_local = max(local_numbers) if local_numbers else BASE_START - 1
        next_seq = max_local + 1

        biotime_emp_code = str(next_seq)

        # --------------------------------------------------------
        # 🧩 Push To BioTime
        # --------------------------------------------------------
        name_parts = employee.full_name.strip().split(" ")
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) or "-"

        result = push_employee_to_biotime(
            company=company,  # ✅ REQUIRED CONTEXT
            emp_code=biotime_emp_code,
            first_name=first_name,
            last_name=last_name,
            area_codes=area_codes,
            dept_code=dept_code,
            position_code=job_code,
            is_active=True,
        )

        if result.get("status") != "success":
            return api_error(
                result.get("message", "فشل إنشاء الموظف في Biotime."),
                trace_id=trace,
            )

        # --------------------------------------------------------
        # 💾 Save Link
        # --------------------------------------------------------
        with transaction.atomic():
            employee.biotime_code = biotime_emp_code
            employee.save(update_fields=["biotime_code"])

        logger.info(
            "[%s] Employee pushed to BioTime | employee_id=%s | company_id=%s",
            trace,
            employee.id,
            company.id,
        )

        return api_success(
            message="✔ تم إنشاء وربط الموظف مع Biotime بنجاح.",
            biotime_code=biotime_emp_code,
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Push Employee Fatal Error", trace)
        return api_error(
            "❌ حدث خطأ غير متوقع أثناء إرسال الموظف.",
            status=500,
            trace_id=trace,
        )

    finally:
        cache.delete(lock_key)
# ================================================================
# 🔗 API — Link Existing Biotime Employee To System Employee
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_link_employee(request):
    """
    ربط موظف BioTime موجود بموظف في النظام.
    - Company Scoped
    - يمنع التكرار
    - يمنع تضارب الربط
    """

    trace = _trace_id()
    company_user = resolve_company_user(request)

    if not company_user or not company_user.company:
        return api_error(
            "Company context not found.",
            status=403,
            trace_id=trace,
        )

    try:
        payload = json.loads(request.body or "{}")

        employee_id = payload.get("employee_id")
        biotime_code = str(payload.get("biotime_code", "")).strip()

        if not employee_id or not biotime_code:
            return api_error(
                "employee_id و biotime_code مطلوبان.",
                trace_id=trace,
            )

        company = company_user.company

        # ------------------------------------------------------
        # 🔎 Fetch System Employee (Company Scoped)
        # ------------------------------------------------------
        employee = get_object_or_404(
            Employee,
            id=employee_id,
            company=company,
        )

        # ------------------------------------------------------
        # 🛡 Already Linked?
        # ------------------------------------------------------
        if employee.biotime_code:
            return api_error(
                "الموظف مرتبط مسبقًا.",
                trace_id=trace,
            )

        # ------------------------------------------------------
        # 🔒 Prevent Duplicate Linking
        # ------------------------------------------------------
        exists = Employee.objects.filter(
            company=company,
            biotime_code=biotime_code,
        ).exists()

        if exists:
            return api_error(
                "هذا الموظف في BioTime مرتبط مسبقًا بموظف آخر.",
                trace_id=trace,
            )

        # ------------------------------------------------------
        # 🔍 Verify BiotimeEmployee Exists (Company Scoped)
        # ------------------------------------------------------
        bio = BiotimeEmployee.objects.filter(
            company=company,
            employee_id=biotime_code,
        ).first()

        if not bio:
            return api_error(
                "لم يتم العثور على الموظف في BioTime.",
                trace_id=trace,
            )

        # ------------------------------------------------------
        # 💾 Atomic Link
        # ------------------------------------------------------
        with transaction.atomic():
            employee.biotime_code = biotime_code
            employee.save(update_fields=["biotime_code"])

        logger.info(
            "[%s] Linked employee | system_id=%s | biotime_code=%s | company=%s",
            trace,
            employee.id,
            biotime_code,
            company.id,
        )

        return api_success(
            message="✔ تم ربط الموظف بنجاح.",
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Link Biotime Employee Error", trace)
        return api_error(
            "❌ حدث خطأ أثناء الربط.",
            status=500,
            trace_id=trace,
        )
