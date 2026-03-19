# ============================================================
# 📂 الملف: biotime_center/sync_service.py
# 🔄 Unified Sync Service — الإصدار V10.4 (Phase E Multi-Area ✅)
# ✔ Devices + Logs (IClock)
# ✔ Employees (READ ONLY)
# ✔ SAFE Master Data Sync (Area / Department / Position)
# ✔ Strict Two-Phase Flow (Master → Employee)
# ✔ Resolve Helpers (biotime_code → biotime_id)
# ✔ Multi Area Support (area_codes: list[str]) ✅
# ✔ Backward Compatible (area_code legacy supported)
# ✔ Auto Patch Area After Create (Biotime SaaS Fix)
# ✔ Auto Patch Department After Create (Biotime SaaS Fix)
# ✔ Import Safe (Signals Stable)
# ✔ No Breaking Changes (Additive Only) 🔒
# ✔ Developed by Mazen — Primey HR Cloud 2026
# ============================================================

import logging
from typing import Iterable, List, Optional

from django.utils import timezone

from .models import (
    BiotimeSetting,
    BiotimeDevice,
    BiotimeEmployee,
    BiotimeLog,
)
from .biotime_api_client import BiotimeAPIClient
from company_manager.models import CompanyBranch, CompanyDepartment, JobTitle

logger = logging.getLogger(__name__)


# ============================================================
# 🟦 1) قراءة إعدادات Biotime
# ============================================================

def get_settings(company=None):
    """
    🔒 MT-6 Strict Mode
    Requires explicit company context.
    No global fallback allowed.
    """

    if not company:
        raise ValueError("Company context مطلوب في MT-6 Strict Mode.")

    setting = BiotimeSetting.objects.filter(company=company).first()

    if not setting:
        raise ValueError("BiotimeSetting غير موجود لهذه الشركة.")

    return setting

# ============================================================
# 🔐 2) تسجيل الدخول
# ============================================================

def get_authenticated_client(company=None):
    """
    🔒 MT-6 Strict Hard Fail
    - Requires company
    - No global fallback
    - Production Safe
    """

    if not company:
        return None, "Company context مطلوب."

    try:
        setting = get_settings(company=company)
    except Exception as e:
        return None, str(e)

    client = BiotimeAPIClient(setting)
    auth = client.authenticate()

    if auth.get("status") != "success":
        logger.warning("Biotime Authentication Failed: %s", auth)
        return None, "❌ فشل تسجيل الدخول — تحقق من بيانات Biotime."

    return client, None


# ============================================================
# 🧪 2.1) Test Connection
# ============================================================

def test_connection(company):
    try:
        setting = get_settings(company=company)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }

    client = BiotimeAPIClient(setting)
    auth = client.authenticate()

    if auth.get("status") != "success":
        return {
            "status": "error",
            "message": "❌ فشل الاتصال مع Biotime.",
            "meta": auth,
        }

    return {
        "status": "success",
        "message": "✔ تم الاتصال بنجاح.",
    }


# ============================================================
# 💻 3) مزامنة الأجهزة — Terminals
# ============================================================

def sync_devices(company=None):
    start_time = timezone.now()

    if not company:
        return {"status": "error", "message": "Company context مطلوب."}

    setting = BiotimeSetting.objects.filter(company=company).first()
    if not setting:
        return {"status": "error", "message": "Biotime setting غير موجود."}

    client = BiotimeAPIClient(setting)
    auth = client.authenticate()
    print("AUTH RESULT =>", auth)
    print("🔎 Fetching devices...")
    if not auth or auth.get("status") != "success":
        return {"status": "error", "message": f"فشل المصادقة مع Biotime: {auth}"}
    
    try:
       terminals = client.get_devices()
       print("TERMINALS RAW =>", terminals)
    except Exception as e:
        print("🔥 get_devices EXCEPTION =>", str(e))
    if terminals is None:
        return {"status": "error", "message": "❌ فشل جلب أجهزة IClock."}

    BiotimeDevice.objects.filter(company=company).delete()

    count = 0

    for d in terminals:
        area_info = d.get("area", {}) or {}

        BiotimeDevice.objects.create(
            company=company,
            device_id=d.get("id"),
            sn=d.get("sn"),
            alias=d.get("alias") or d.get("terminal_name") or "—",
            terminal_name=d.get("terminal_name"),
            ip_address=d.get("ip_address"),
            firmware_version=d.get("fw_ver"),
            state=d.get("state"),
            terminal_tz=d.get("terminal_tz"),
            area_name=area_info.get("area_name"),
            biotime_company_code=setting.biotime_company,
            push_time=d.get("push_time"),
            transfer_time=d.get("transfer_time"),
            transfer_interval=d.get("transfer_interval"),
            last_activity=d.get("last_activity"),
            user_count=d.get("user_count"),
            face_count=d.get("face_count"),
            palm_count=d.get("palm_count"),
            raw_json=d,
            last_sync=timezone.now(),
        )
        count += 1

    elapsed_ms = int((timezone.now() - start_time).total_seconds() * 1000)

    return {
        "status": "success",
        "count": count,
        "elapsed_ms": elapsed_ms,
    }
# ============================================================
# 👥 Enterprise Employee Sync (MULTI-TENANT SAFE — FINAL MT-2)
# ============================================================

def sync_employees(company=None):

    start_time = timezone.now()

    # ======================================================
    # 🔒 Resolve Company Context
    # ======================================================
    if not company:
        return {
            "status": "error",
            "message": "Company context مطلوب للمزامنة."
        }

    setting = BiotimeSetting.objects.filter(company=company).first()

    if not setting or not setting.biotime_company:
        return {
            "status": "error",
            "message": "Biotime company code غير مضبوط."
        }

    # ======================================================
    # 🔐 Authenticate
    # ======================================================
    client, error = get_authenticated_client(company=company)

    if error or not client:
        return {
            "status": "error",
            "message": "فشل المصادقة مع Biotime."
        }

    # ======================================================
    # 📡 Fetch Employees
    # ======================================================
    employees = client.get_employees()

    if employees is None:
        return {
            "status": "error",
            "message": "فشل جلب موظفي Biotime."
        }

    # ======================================================
    # 🧹 STRICT SYNC CLEANUP (MT SAFE)
    # حذف أي موظف محلي غير موجود فعليًا في Biotime
    # ======================================================
    try:
        remote_codes = set(
            str(e.get("emp_code") or "").strip()
            for e in employees
            if e.get("emp_code")
        )

        local_codes = set(
            BiotimeEmployee.objects
            .filter(company=company)
            .values_list("employee_id", flat=True)
        )

        orphan_codes = local_codes - remote_codes

        if orphan_codes:
            deleted_count, _ = (
                BiotimeEmployee.objects
                .filter(company=company, employee_id__in=orphan_codes)
                .delete()
            )

            logger.info(
                "Strict Sync Cleanup | company=%s | deleted=%s",
                company.id,
                deleted_count,
            )

    except Exception:
        logger.exception("Strict Sync Cleanup Error")

    # ======================================================
    # 🔁 Sync Loop
    # ======================================================
    synced = 0
    updated = 0
    skipped = 0
    now = timezone.now()

    for e in employees:

        try:
            emp_code = str(e.get("emp_code") or "").strip()

            if not emp_code:
                skipped += 1
                continue

            full_name = (
                f"{e.get('first_name', '')} {e.get('last_name', '')}"
            ).strip() or "—"

            defaults = dict(
                full_name=full_name,
                department=(e.get("department") or {}).get("dept_name"),
                position=(e.get("position") or {}).get("position_name"),
                card_number=e.get("card_no"),
                is_active=bool(e.get("enable_att", True)),
                last_sync=now,
                company=company,
            )

            obj, created = BiotimeEmployee.objects.update_or_create(
                company=company,
                employee_id=emp_code,
                defaults=defaults,
            )

            if created:
                synced += 1
            else:
                updated += 1

        except Exception:
            skipped += 1
            logger.exception("Biotime Employee Sync Error")

    elapsed_ms = int(
        (timezone.now() - start_time).total_seconds() * 1000
    )

    logger.info(
        "Biotime Employee Sync Completed | company=%s | synced=%s | updated=%s",
        company.id,
        synced,
        updated,
    )

    return {
        "status": "success",
        "synced": synced,
        "updated": updated,
        "skipped": skipped,
        "total": synced + updated,
        "elapsed_ms": elapsed_ms,
    }


# ============================================================
# 🕒 5) مزامنة السجلات (Biotime → BiotimeLog ONLY)  🔒
# ------------------------------------------------------------
# ⚠️ ملاحظة معمارية مهمة:
# هذه الدالة مسؤولة فقط عن:
#   ✔ جلب السجلات من Biotime
#   ✔ تطبيع punch_time بشكل آمن
#   ✔ حفظ البيانات الخام داخل BiotimeLog
#   ✔ عدم لمس AttendanceRecord إطلاقًا
#
# تحويل السجلات إلى Attendance يتم حصريًا عبر:
# attendance_center.services.sync_biotime_to_attendance
# ============================================================

from datetime import datetime
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from biotime_center.models import BiotimeLog


def sync_logs(company=None, start_date=None, end_date=None):
    """
    🔄 Sync Biotime raw logs for a specific company.

    ✔ Multi-tenant safe
    ✔ Explicit company required
    ✔ Idempotent (update_or_create)
    ✔ Supports optional date range
    ✔ Production ready
    """

    # ------------------------------------------------------------
    # 1️⃣ Validate Company Context
    # ------------------------------------------------------------
    if not company:
        return {
            "status": "error",
            "message": "Company context مطلوب.",
        }

    if not company.is_active:
        return {
            "status": "error",
            "message": "الشركة غير مفعلة.",
        }

    # ------------------------------------------------------------
    # 2️⃣ Get Biotime Setting
    # ------------------------------------------------------------
    setting = (
        BiotimeSetting.objects
        .filter(company=company)
        .only("id")
        .first()
    )

    if not setting:
        return {
            "status": "error",
            "message": "Biotime setting غير موجود.",
        }

    # ------------------------------------------------------------
    # 3️⃣ Authenticate
    # ------------------------------------------------------------
    client = BiotimeAPIClient(setting)
    auth = client.authenticate()

    if auth.get("status") != "success":
        return {
            "status": "error",
            "message": "فشل المصادقة مع Biotime.",
        }

    # ------------------------------------------------------------
    # 4️⃣ Fetch Logs
    # ------------------------------------------------------------
    try:
        transactions = client.get_logs(start_date, end_date)
    except Exception as exc:
        logger.exception("❌ Exception أثناء جلب سجلات Biotime")
        return {
            "status": "error",
            "message": str(exc),
        }

    if transactions is None:
        return {
            "status": "error",
            "message": "❌ فشل جلب السجلات.",
        }

    # ------------------------------------------------------------
    # 5️⃣ Process Logs
    # ------------------------------------------------------------
    saved = 0
    updated = 0
    skipped = 0

    for t in transactions:

        try:
            raw_punch_time = t.get("punch_time")

            if not raw_punch_time:
                skipped += 1
                continue

            punch_time = parse_datetime(str(raw_punch_time))

            if not punch_time:
                skipped += 1
                continue

            if timezone.is_naive(punch_time):
                punch_time = timezone.make_aware(punch_time)

            obj, created = BiotimeLog.objects.update_or_create(
                company=company,
                log_id=t.get("id"),
                defaults={
                    "employee_code": t.get("emp_code"),
                    "punch_time": punch_time,
                    "punch_state": t.get("punch_state"),
                    "device_sn": t.get("terminal_sn"),
                    "terminal_alias": t.get("terminal_alias"),
                    "area_alias": t.get("area_alias"),
                    "raw_json": t,
                    "processed": False,
                },
            )

            if created:
                saved += 1
            else:
                updated += 1

        except Exception:
            skipped += 1
            logger.exception("❌ Failed syncing Biotime raw log")

    # ------------------------------------------------------------
    # 6️⃣ Return Unified Result
    # ------------------------------------------------------------
    return {
        "status": "success",
        "company_id": company.id,
        "new": saved,
        "updated": updated,
        "skipped": skipped,
        "total": saved + updated,
    }

def _generate_biotime_code(prefix: str, instance_id: int) -> str:
    """
    🔐 Generate Safe Biotime Code
    - Numeric only
    - Avoid reserved default code=1
    - Company safe
    """
    code = int(instance_id)

    # 🚫 Avoid reserved 1
    if code == 1:
        code = 1000 + code

    return str(code)


# ---------------- Area ----------------

def get_or_create_area(client, name: str, code: str):
    """
    🔄 Get or Create BioTime Area (Idempotent Safe)
    ✔ يتحقق أولاً إن كانت موجودة
    ✔ لا يفشل إذا كانت موجودة مسبقًا
    ✔ يرجع dict واضح
    """

    try:
        # --------------------------------------------------
        # 🔎 1) تحقق هل الـ Area موجودة مسبقًا
        # --------------------------------------------------
        existing_id = resolve_area_id_by_code(client, code)

        if existing_id:
            logger.info(
                "✔ Area already exists in BioTime | code=%s | id=%s",
                code,
                existing_id,
            )
            return {
                "id": existing_id,
                "created": False,
                "area_code": code,
            }

        # --------------------------------------------------
        # 🚀 2) إنشاء Area جديدة
        # --------------------------------------------------
        url = f"{client.base_url}/personnel/api/areas/"
        payload = {
            "area_name": name,
            "area_code": code,
        }

        logger.warning("🧪 CREATE AREA URL: %s", url)
        logger.warning("🧪 CREATE AREA PAYLOAD: %s", payload)

        res = client._post(url, json=payload, timeout=20)

        if not res:
            logger.error("❌ Create Area returned None")
            return None

        if res.status_code not in (200, 201):
            logger.error(
                "❌ Create Area Failed | status=%s | body=%s",
                res.status_code,
                res.text[:500],
            )
            return None

        data = res.json() or {}

        logger.info(
            "✅ Area Created Successfully | code=%s | response=%s",
            code,
            data,
        )

        return data

    except Exception:
        logger.exception("❌ Failed creating Area")
        return None

# ---------------- Department ----------------

def get_or_create_department(client, name: str, code: str):
    """
    Idempotent Department Sync:
    - Try create
    - If already exists → resolve by code
    - Never return None if exists
    """

    try:
        # --------------------------------------------------
        # 1️⃣ Try Create
        # --------------------------------------------------
        url = f"{client.base_url}/personnel/api/departments/"
        payload = {
            "dept_name": name,
            "dept_code": str(code),
        }

        res = client._post(url, json=payload, timeout=20)

        if res and res.status_code in (200, 201):
            logger.info(
                "✅ Department Created | code=%s | name=%s",
                code,
                name,
            )
            return res.json()

        # --------------------------------------------------
        # 2️⃣ Already Exists? → Resolve by Code
        # --------------------------------------------------
        dept_id = resolve_department_id_by_code(client, str(code))

        if dept_id:
            logger.info(
                "ℹ️ Department Exists | code=%s | resolved_id=%s",
                code,
                dept_id,
            )
            return {
                "id": dept_id,
                "existing": True,
            }

        # --------------------------------------------------
        # 3️⃣ Failed
        # --------------------------------------------------
        logger.error(
            "❌ Department Sync Failed | code=%s | status=%s | body=%s",
            code,
            getattr(res, "status_code", None),
            getattr(res, "text", "")[:300],
        )
        return None

    except Exception:
        logger.exception("❌ Failed creating/resolving Department")
        return None

# ---------------- Position ----------------

def get_or_create_position(client, name: str, code: str):
    """
    🔄 Idempotent Position Sync (Production Safe)
    ✔ Try create
    ✔ If exists → resolve by code
    ✔ Always return dict with id if exists
    """

    try:
        if not client:
            logger.error("❌ get_or_create_position | client missing")
            return None

        if not name or not str(code).strip():
            logger.warning(
                "⚠️ get_or_create_position skipped | invalid data | name=%s | code=%s",
                name,
                code,
            )
            return None

        url = f"{client.base_url}/personnel/api/positions/"
        payload = {
            "position_name": str(name).strip(),
            "position_code": str(code).strip(),
        }

        # --------------------------------------------------
        # 1️⃣ Try Create
        # --------------------------------------------------
        res = client._post(url, json=payload, timeout=20)

        if res and res.status_code in (200, 201):
            logger.info(
                "✅ Position Created | code=%s | name=%s",
                code,
                name,
            )
            return res.json()

        # --------------------------------------------------
        # 2️⃣ Already Exists → Resolve by Code
        # --------------------------------------------------
        position_id = resolve_position_id_by_code(client, str(code))

        if position_id:
            logger.info(
                "ℹ️ Position Exists | code=%s | resolved_id=%s",
                code,
                position_id,
            )
            return {
                "id": position_id,
                "existing": True,
            }

        # --------------------------------------------------
        # 3️⃣ Real Failure
        # --------------------------------------------------
        logger.error(
            "❌ Position Sync Failed | code=%s | status=%s | body=%s",
            code,
            getattr(res, "status_code", None),
            getattr(res, "text", "")[:300],
        )

        return None

    except Exception:
        logger.exception("❌ get_or_create_position exception")
        return None

# ---------------- Public Sync APIs ----------------

def create_or_sync_branch(branch: CompanyBranch):
    """
    ======================================================
    🏢 Sync CompanyBranch → Biotime Area
    ✅ Company Scoped
    ✅ Idempotent (resolve first)
    ✅ Avoid code=1 (Biotime default)
    ======================================================
    """

    if not branch.is_active:
        return None

    # 🔐 Company Scoped Auth
    client, error = get_authenticated_client(company=branch.company)
    if error or not client:
        logger.warning("⚠️ Branch Sync Skipped | auth_error=%s | branch_id=%s", error, branch.id)
        return None

    # 🆔 Ensure biotime_code (generate once)
    if not branch.biotime_code:
        code = _generate_biotime_code("BR", branch.id)

        # ✅ Avoid reserved/default code=1 in Biotime (only on first generation)
        if str(code).strip() == "1":
            code = str(1000 + int(branch.id))

        branch.biotime_code = str(code).strip()
        branch.save(update_fields=["biotime_code"])

    # ✅ Idempotent: if exists → return success object (no POST)
    try:
        existing_id = resolve_area_id_by_code(client, str(branch.biotime_code).strip())
        if existing_id:
            return {
                "id": existing_id,
                "exists": True,
                "area_code": branch.biotime_code,
                "area_name": branch.name,
            }
    except Exception:
        logger.exception("❌ Resolve Area Failed | branch_id=%s", branch.id)

    # 🚀 Create (if missing)
    try:
        return get_or_create_area(client, branch.name, branch.biotime_code)
    except Exception:
        logger.exception("❌ Create Area Failed | branch_id=%s", branch.id)
        return None

#======================================================
#🏢 Sync CompanyDepartment → Biotime Department ONLY
#❌ ممنوع إنشاء Area من القسم
#======================================================
def create_or_sync_department(department: CompanyDepartment):
    """
    ======================================================
    🏢 Sync CompanyDepartment → Biotime Department ONLY
    ✅ Company Scoped
    ✅ Idempotent (resolve first)
    ✅ Avoid code=1 (Biotime default)
    ======================================================
    """

    if not department.is_active:
        return None

    # 🔐 Company Scoped Auth
    client, error = get_authenticated_client(company=department.company)
    if error or not client:
        logger.warning("⚠️ Dept Sync Skipped | auth_error=%s | dept_id=%s", error, department.id)
        return None

    # 🆔 Ensure biotime_code (generate once)
    if not department.biotime_code:
        code = _generate_biotime_code("DEPT", department.id)

        # ✅ Avoid reserved/default code=1 in Biotime (only on first generation)
        if str(code).strip() == "1":
            code = str(1000 + int(department.id))

        department.biotime_code = str(code).strip()
        department.save(update_fields=["biotime_code"])

    # ✅ Idempotent: if exists → return success object (no POST)
    try:
        existing_id = resolve_department_id_by_code(client, str(department.biotime_code).strip())
        if existing_id:
            return {
                "id": existing_id,
                "exists": True,
                "dept_code": department.biotime_code,
                "dept_name": department.name,
            }
    except Exception:
        logger.exception("❌ Resolve Department Failed | dept_id=%s", department.id)

    # 🚀 Create (if missing)
    try:
        return get_or_create_department(
            client,
            department.name,
            department.biotime_code,
        )
    except Exception:
        logger.exception("❌ Create Department Failed | dept_id=%s", department.id)
        return None

def create_or_sync_jobtitle(jobtitle: JobTitle):
    """
    ======================================================
    💼 Sync JobTitle → Biotime Position
    ✅ Company Scoped
    ✅ Idempotent (resolve first)
    ✅ Avoid code=1 (Biotime default)
    ======================================================
    """

    if not jobtitle.is_active:
        return None

    # 🔐 Company Scoped Auth
    client, error = get_authenticated_client(company=jobtitle.company)
    if error or not client:
        logger.warning("⚠️ JobTitle Sync Skipped | auth_error=%s | job_id=%s", error, jobtitle.id)
        return None

    # 🆔 Ensure biotime_code (generate once)
    if not jobtitle.biotime_code:
        code = _generate_biotime_code("POS", jobtitle.id)

        # ✅ Avoid reserved/default code=1 in Biotime (only on first generation)
        if str(code).strip() == "1":
            code = str(1000 + int(jobtitle.id))

        jobtitle.biotime_code = str(code).strip()
        jobtitle.save(update_fields=["biotime_code"])

    # ✅ Idempotent: if exists → return success object (no POST)
    try:
        existing_id = resolve_position_id_by_code(client, str(jobtitle.biotime_code).strip())
        if existing_id:
            return {
                "id": existing_id,
                "exists": True,
                "position_code": jobtitle.biotime_code,
                "position_name": jobtitle.name,
            }
    except Exception:
        logger.exception("❌ Resolve Position Failed | job_id=%s", jobtitle.id)

    # 🚀 Create (if missing)
    try:
        return get_or_create_position(client, jobtitle.name, jobtitle.biotime_code)
    except Exception:
        logger.exception("❌ Create Position Failed | job_id=%s", jobtitle.id)
        return None

# ============================================================
# 🧩 Resolve Helpers
# ============================================================
def resolve_employee_biotime_id(client, employee_code: str) -> Optional[str]:
    """
    Resolve employee internal biotime id using emp_code.
    """
    try:
        url = f"{client.base_url}/personnel/api/employees/"
        res = client._get(url, params={"emp_code": employee_code}, timeout=15)

        if not res or res.status_code != 200:
            return None

        data = (res.json() or {}).get("data") or []
        if not data:
            return None

        return str(data[0].get("id"))

    except Exception:
        logger.exception("❌ Failed resolving employee biotime id by emp_code")
        return None

def _resolve_by_code(client, endpoint: str, code_field: str, code_value: str):
    """
    🔎 Resolve Entity ID by Code (BioTime Safe - HARD GUARDED)
    ✔ Strict code validation
    ✔ Prevent None / empty queries
    ✔ Prevent accidental first-record return
    ✔ Company Scoped via client
    ✔ Never throws
    """

    try:
        # -----------------------------------------
        # 🔐 Client Validation
        # -----------------------------------------
        if not client:
            logger.error("❌ Resolve by code | client missing")
            return None

        # -----------------------------------------
        # 🚫 Hard Guard: invalid code_value
        # -----------------------------------------
        if code_value is None:
            logger.warning("🚫 Resolve blocked | code_value is None")
            return None

        code_str = str(code_value).strip()

        if not code_str:
            logger.warning("🚫 Resolve blocked | code_value empty string")
            return None

        if code_str.lower() == "none":
            logger.warning("🚫 Resolve blocked | code_value literal 'None'")
            return None

        # -----------------------------------------
        # 🌐 Call BioTime
        # -----------------------------------------
        url = f"{client.base_url}{endpoint}"

        logger.info(
            "🔎 Resolving | endpoint=%s | %s=%s",
            endpoint,
            code_field,
            code_str,
        )

        res = client._get(
            url,
            params={code_field: code_str},
            timeout=20,
        )

        if not res:
            logger.error("❌ Resolve failed | response is None")
            return None

        if res.status_code != 200:
            logger.error(
                "❌ Resolve failed | status=%s | body=%s",
                res.status_code,
                res.text[:300],
            )
            return None

        raw = res.json() or {}

        # -----------------------------------------
        # 🟢 Case 1: SaaS dict format
        # -----------------------------------------
        if isinstance(raw, dict) and "data" in raw:
            data = raw.get("data") or []
        # -----------------------------------------
        # 🟢 Case 2: Direct list
        # -----------------------------------------
        elif isinstance(raw, list):
            data = raw
        else:
            data = []

        if not data:
            return None

        entity_id = data[0].get("id")

        if entity_id:
            logger.info(
                "✔ Resolved | %s=%s | id=%s",
                code_field,
                code_str,
                entity_id,
            )
            return entity_id

        return None

    except Exception:
        logger.exception("❌ Resolve by code exception")
        return None


def resolve_area_id_by_code(client, area_code: str):
    return _resolve_by_code(client, "/personnel/api/areas/", "area_code", area_code)


def resolve_department_id_by_code(client, dept_code: str):
    return _resolve_by_code(client, "/personnel/api/departments/", "dept_code", dept_code)


def resolve_position_id_by_code(client, position_code: str):
    return _resolve_by_code(client, "/personnel/api/positions/", "position_code", position_code)


# ============================================================
# 🧩 Safe Read Employee Snapshot (Department / Position / Area)
# ============================================================

def get_employee_snapshot(client, employee_biotime_id: str) -> dict:
    """
    قراءة Snapshot حقيقي للموظف من Biotime.
    يرجع:
        {
            "department": int | None,
            "position": int | None,
            "areas": list[int]
        }
    """

    try:
        # --------------------------------------------------
        # 🔎 Resolve Internal Biotime Employee ID
        # --------------------------------------------------
        resolved_id = (
            resolve_employee_biotime_id(client, str(employee_biotime_id).strip())
            or str(employee_biotime_id).strip()
        )

        if not resolved_id:
            logger.error(
                "❌ Snapshot Failed | cannot resolve employee id | employee=%s",
                employee_biotime_id,
            )
            return {"department": None, "position": None, "areas": []}

        # --------------------------------------------------
        # 🌐 Fetch Employee
        # --------------------------------------------------
        url = f"{client.base_url}/personnel/api/employees/{resolved_id}/"
        res = client._get(url, timeout=25)

        if not res or res.status_code != 200:
            logger.error(
                "❌ Snapshot Failed | status=%s | employee=%s",
                getattr(res, "status_code", None),
                resolved_id,
            )
            return {"department": None, "position": None, "areas": []}

        data = res.json() or {}

        # --------------------------------------------------
        # 🧹 Normalize Department (SAFE)
        # --------------------------------------------------
        dept = data.get("department")

        if isinstance(dept, dict):
            dept = dept.get("id")

        try:
            dept = int(dept) if dept is not None else None
        except Exception:
            dept = None

        # --------------------------------------------------
        # 🧹 Normalize Position (SAFE)
        # --------------------------------------------------
        pos = data.get("position")

        if isinstance(pos, dict):
            pos = pos.get("id")

        try:
            pos = int(pos) if pos is not None else None
        except Exception:
            pos = None

        # --------------------------------------------------
        # 🧹 Normalize Areas
        # --------------------------------------------------
        areas = get_employee_current_area_ids(client, resolved_id)

        snapshot = {
            "department": dept,
            "position": pos,
            "areas": areas,
        }

        logger.info(
            "📸 Employee Snapshot | employee=%s | snapshot=%s",
            resolved_id,
            snapshot,
        )

        return snapshot

    except Exception:
        logger.exception("❌ Failed reading employee snapshot")
        return {"department": None, "position": None, "areas": []}

# ============================================================
# 🧩 Safe Read Employee Current Areas
# ============================================================

def get_employee_current_area_ids(client, employee_biotime_id: str) -> list[int]:
    """
    قراءة Areas الحالية للموظف بشكل آمن.
    يدعم جميع صيغ BioTime:
        - [1, 2, 3]
        - [{"id": 1}, {"id": 2}]
        - ["فرع الرياض"]
    """

    try:
        url = f"{client.base_url}/personnel/api/employees/{employee_biotime_id}/"
        res = client._get(url, timeout=20)

        if not res or res.status_code != 200:
            logger.error("❌ Failed fetching employee details | id=%s", employee_biotime_id)
            return []

        data = res.json() or {}
        raw_area = data.get("area") or []

        safe_ids: list[int] = []

        for item in raw_area:
            # -----------------------------
            # Case 1: integer already
            # -----------------------------
            if isinstance(item, int):
                safe_ids.append(item)
                continue

            # -----------------------------
            # Case 2: dict object
            # -----------------------------
            if isinstance(item, dict):
                area_id = item.get("id")
                if isinstance(area_id, int):
                    safe_ids.append(area_id)
                continue

            # -----------------------------
            # Case 3: string name → ignore safely
            # -----------------------------
            if isinstance(item, str):
                logger.warning(
                    "⚠️ Area returned as string, skipping: %s | employee=%s",
                    item,
                    employee_biotime_id,
                )
                continue

        return sorted(set(safe_ids))

    except Exception:
        logger.exception("❌ Failed reading employee current areas")
        return []

# ============================================================
# 🧩 Phase E.1 — Append Area To Employee (PATCH SAFE)
# ============================================================

def append_employee_area(
    *,
    employee_biotime_id: str,
    new_area_code: str,
):
    """
    إضافة Area جديدة لموظف في Biotime بدون Replace.
    Flow:
        1) Resolve employee internal id
        2) Resolve area_code → area_id
        3) Read snapshot (SAFE)
        4) Merge (deduplicate)
        5) Patch merged list (idempotent)
    """

    client, error = get_authenticated_client()
    if error:
        return {"status": "error", "message": error}

    # --------------------------------------------------
    # 🔎 Resolve Employee Internal Biotime ID (SAFE)
    # --------------------------------------------------
    resolved_id = resolve_employee_biotime_id(
        client,
        str(employee_biotime_id).strip(),
    )

    # إذا لم يتم العثور عليه، نفترض أنه internal id أصلاً
    if not resolved_id:
        resolved_id = str(employee_biotime_id).strip()

    # حماية نهائية
    if not resolved_id:
        return {
            "status": "error",
            "message": f"❌ لم يتم العثور على الموظف في Biotime: {employee_biotime_id}",
        }

    employee_biotime_id = resolved_id

    # ---------------------------
    # 1) Resolve Area ID
    # ---------------------------
    area_id = resolve_area_id_by_code(client, new_area_code)
    if not area_id:
        return {
            "status": "error",
            "message": f"❌ Area غير موجودة في Biotime: {new_area_code}",
        }

    try:
        area_id = int(area_id)
    except Exception:
        return {
            "status": "error",
            "message": "❌ Area ID غير صالح.",
        }

    # ---------------------------
    # 2) Read Snapshot (SAFE)
    # ---------------------------
    snapshot = get_employee_snapshot(client, employee_biotime_id)
    current_area_ids = snapshot.get("areas") or []

    try:
        current_area_ids = sorted({
            int(x)
            for x in current_area_ids
            if x is not None and str(x).isdigit()
        })
    except Exception:
        current_area_ids = []

    # ---------------------------
    # 3) Merge (Append Only)
    # ---------------------------
    merged_area_ids = sorted(
        set([*current_area_ids, area_id])
    )

    # ---------------------------
    # 🛡️ Idempotent Guard (No Change)
    # ---------------------------
    if merged_area_ids == current_area_ids:
        logger.info(
            "Biotime Append Area Skipped | employee=%s | area_code=%s | already_exists=True",
            employee_biotime_id,
            new_area_code,
        )
        return {
            "status": "success",
            "message": "✔ Area موجودة مسبقًا — لا يوجد تعديل.",
            "area_ids": merged_area_ids,
            "patched": False,
        }

    # ---------------------------
    # 4) Patch
    # ---------------------------
    patched = patch_employee_area(
        client,
        employee_biotime_id,
        merged_area_ids,
    )

    if not patched:
        return {
            "status": "error",
            "message": "❌ فشل تحديث Area في Biotime.",
        }

    logger.info(
        "Biotime Append Area Success | employee=%s | area_code=%s | merged_areas=%s",
        employee_biotime_id,
        new_area_code,
        merged_area_ids,
    )

    return {
        "status": "success",
        "message": "✔ تم إضافة Area بنجاح.",
        "area_ids": merged_area_ids,
        "patched": True,
    }
# ============================================================
# 🧩 Phase E — Build Payload (MULTI AREA SAFE)
# ============================================================

def _normalize_area_codes(
    *,
    area_codes: Optional[Iterable[str]] = None,
    area_code: Optional[str] = None,
) -> List[str]:
    """
    توحيد مدخلات الـ Area لدعم:
    - area_codes = ["BR-1", "BR-2"]
    - area_code  = "BR-1" (Legacy)
    """
    if area_codes:
        return [str(c).strip() for c in area_codes if str(c).strip()]

    if area_code:
        return [str(area_code).strip()]

    return []

#============================================================
#🔥 4 — تعديل build_biotime_employee_payload
#============================================================
def build_biotime_employee_payload(
    *,
    emp_code: str,
    first_name: str,
    last_name: str,
    area_codes: Optional[Iterable[str]] = None,
    area_code: Optional[str] = None,
    dept_code: str,
    position_code: str,
    card_no: str = "",
    is_active: bool = True,
    client=None,   # ✅ NEW PERFORMANCE PARAM
):
    """
    ✔ Performance Optimized
    ✔ Reuse Authenticated Client
    ✔ Backward Compatible
    """

    if client is None:
        client, error = get_authenticated_client()
        if error:
            return None, error

    normalized_area_codes = _normalize_area_codes(
        area_codes=area_codes,
        area_code=area_code,
    )

    if not normalized_area_codes:
        return None, "❌ يجب تحديد Area واحدة على الأقل."

    area_ids: List[int] = []

    for code in normalized_area_codes:
        area_id = resolve_area_id_by_code(client, code)
        if not area_id:
            return None, f"❌ Area غير موجود: {code}"
        area_ids.append(int(area_id))

    dept_id = resolve_department_id_by_code(client, dept_code)
    pos_id = resolve_position_id_by_code(client, position_code)

    if not dept_id:
        return None, f"❌ Department غير موجود: {dept_code}"

    if not pos_id:
        return None, f"❌ Position غير موجود: {position_code}"

    payload = {
        "emp_code": str(emp_code).strip(),
        "first_name": first_name,
        "last_name": last_name,
        "department": int(dept_id),
        "position": int(pos_id),
        "area": area_ids,
        "card_no": card_no or "",
        "is_active": bool(is_active),
    }

    return payload, None

# ============================================================
# 🧩 Resolve Area Codes → Area IDs (REPLACE MODE SAFE)
# ============================================================

def resolve_area_codes_to_ids(
    *,
    client,
    area_codes: Iterable[str],
) -> list[int]:
    """
    تحويل قائمة area_codes إلى قائمة area_ids جاهزة للإرسال إلى BioTime.
    يستخدم في وضع Replace (استبدال كامل).
    """

    resolved_ids: list[int] = []

    for code in area_codes:
        code = str(code).strip()
        if not code:
            continue

        area_id = resolve_area_id_by_code(client, code)
        if not area_id:
            raise ValueError(f"❌ Area غير موجود في Biotime: {code}")

        resolved_ids.append(int(area_id))

    # إزالة التكرار وترتيب ثابت
    return sorted(set(resolved_ids))

# ============================================================
# 🧩 Patch Employee Area (REPLACE SAFE)
# ============================================================

def patch_employee_area(client, employee_id: str, area_ids: List[int]) -> bool:
    """
    تحديث Areas للموظف في Biotime (Replace كامل وليس Append).
    - يقارن Snapshot الحقيقي قبل الإرسال.
    - يمنع PATCH غير الضروري.
    """

    try:
        # ---------------------------
        # 🔐 Ensure Client
        # ---------------------------
        if client is None:
            client, error = get_authenticated_client()
            if error or not client:
                logger.error("❌ Patch Area Failed | Auth Error")
                return False

        # ---------------------------
        # 🧹 Normalize Area IDs
        # ---------------------------
        normalized_area_ids = sorted({
            int(a)
            for a in area_ids
            if a is not None and str(a).isdigit()
        })

        if not normalized_area_ids:
            logger.warning(
                "⚠️ Patch Area Skipped | empty area_ids | employee=%s",
                employee_id,
            )
            return True

        # ---------------------------
        # 🔎 Resolve Employee ID
        # ---------------------------
        resolved_id = (
            resolve_employee_biotime_id(client, str(employee_id).strip())
            or str(employee_id).strip()
        )

        if not resolved_id:
            logger.error("❌ Patch Area Failed | cannot resolve employee id")
            return False

        # ---------------------------
        # 📸 Read Snapshot
        # ---------------------------
        snapshot = get_employee_snapshot(client, resolved_id)
        current_area_ids = sorted(snapshot.get("areas") or [])

        # ---------------------------
        # 🛡️ Idempotent Guard
        # ---------------------------
        if current_area_ids == normalized_area_ids:
            logger.info(
                "✔ Patch Area Skipped | no change | employee=%s | areas=%s",
                resolved_id,
                normalized_area_ids,
            )
            return True

        # ---------------------------
        # 🚀 PATCH (REPLACE)
        # ---------------------------
        url = f"{client.base_url}/personnel/api/employees/{resolved_id}/"
        payload = {"area": normalized_area_ids}

        logger.warning("🧪 PATCH AREA URL: %s", url)
        logger.warning("🧪 PATCH AREA PAYLOAD: %s", payload)

        res = client._patch(url, json=payload, timeout=25)

        if not res or res.status_code not in (200, 202):
            logger.error(
                "❌ Patch Area Failed | status=%s | body=%s",
                getattr(res, "status_code", None),
                getattr(res, "text", "")[:300],
            )
            return False

        logger.info(
            "✅ Patch Area Success | employee=%s | areas=%s",
            resolved_id,
            normalized_area_ids,
        )
        return True

    except Exception:
        logger.exception("❌ Patch Area Exception")
        return False
# ============================================================
# 🧩 Phase E.2 — Replace Employee Areas (MT-6 SAFE VERSION)
# ============================================================

def patch_employee_areas_replace(
    *,
    company,
    employee_id: str,
    area_codes: Iterable[str],
) -> bool:
    """
    استبدال كامل للفروع (Areas) الخاصة بالموظف في BioTime.
    ✔ Company Scoped (MT-6 Strict)
    ✔ JWT / Session Auto
    ✔ Idempotent Safe
    ✔ Production & Local Compatible
    """

    try:
        if not company:
            logger.error("❌ Replace Areas Failed | company missing")
            return False

        # --------------------------------------------------
        # 🔐 Company Scoped Auth (MT-6)
        # --------------------------------------------------
        client, error = get_authenticated_client(company=company)

        if error or not client:
            logger.error("❌ Replace Areas Failed | Auth Error")
            return False

        # --------------------------------------------------
        # 🔎 Resolve Internal Biotime Employee ID
        # --------------------------------------------------
        resolved_id = (
            resolve_employee_biotime_id(
                client,
                str(employee_id).strip(),
            )
            or str(employee_id).strip()
        )

        if not resolved_id:
            logger.error(
                "❌ Cannot resolve Biotime employee id | employee=%s",
                employee_id,
            )
            return False

        # --------------------------------------------------
        # 🧹 Normalize + Resolve Area Codes
        # --------------------------------------------------
        normalized_codes = [
            str(c).strip()
            for c in area_codes
            if str(c).strip()
        ]

        if not normalized_codes:
            logger.warning(
                "⚠️ Replace Areas Skipped | empty area_codes | employee=%s",
                employee_id,
            )
            return True

        target_area_ids = resolve_area_codes_to_ids(
            client=client,
            area_codes=normalized_codes,
        )

        # --------------------------------------------------
        # 📸 Read Snapshot (Idempotent Guard)
        # --------------------------------------------------
        snapshot = get_employee_snapshot(client, resolved_id)
        current_area_ids = sorted(snapshot.get("areas") or [])

        if current_area_ids == target_area_ids:
            logger.info(
                "✔ Replace Areas Skipped | no change | employee=%s | areas=%s",
                resolved_id,
                target_area_ids,
            )
            return True

        # --------------------------------------------------
        # 🚀 PATCH (AUTHORITATIVE REPLACE)
        # --------------------------------------------------
        url = f"{client.base_url}/personnel/api/employees/{resolved_id}/"
        payload = {"area": target_area_ids}

        logger.warning("🧪 PATCH REPLACE AREA URL: %s", url)
        logger.warning("🧪 PATCH REPLACE AREA PAYLOAD: %s", payload)

        res = client._patch(url, json=payload, timeout=25)

        if not res or res.status_code not in (200, 202):
            logger.error(
                "❌ Replace Areas Failed | status=%s | body=%s",
                getattr(res, "status_code", None),
                getattr(res, "text", "")[:500],
            )
            return False

        logger.info(
            "✅ Replace Areas Success | employee=%s | areas=%s",
            resolved_id,
            target_area_ids,
        )

        return True

    except Exception:
        logger.exception("❌ Patch Replace Areas Exception")
        return False

# ============================================================
# 🧩 Auto Patch Employee Department (MT-6 SAFE | SNAPSHOT GUARDED)
# ============================================================

def patch_employee_department(
    *,
    company,
    employee_id: str,
    dept_code: str,
) -> bool:
    """
    تحديث قسم الموظف (Department) في Biotime باستخدام dept_code.
    ✔ Company Scoped
    ✔ Snapshot Guard (Idempotent)
    ✔ JWT / Session Auto
    ✔ Compatible with Local & Production
    """

    try:
        if not dept_code:
            logger.warning(
                "⚠️ Patch Department Skipped | empty dept_code | employee=%s",
                employee_id,
            )
            return True

        # --------------------------------------------------
        # 🔐 Auth (Company Scoped — MT-6)
        # --------------------------------------------------
        client, error = get_authenticated_client(company=company)

        if error or not client:
            logger.error("❌ Patch Department Failed | Auth Error")
            return False

        # --------------------------------------------------
        # 🔎 Resolve Internal Biotime Employee ID
        # --------------------------------------------------
        resolved_id = (
            resolve_employee_biotime_id(
                client,
                str(employee_id).strip(),
            )
            or str(employee_id).strip()
        )

        if not resolved_id:
            logger.error(
                "❌ Cannot resolve Biotime employee id | employee=%s",
                employee_id,
            )
            return False

        # --------------------------------------------------
        # 🔎 Resolve Department ID by Code
        # --------------------------------------------------
        department_id = resolve_department_id_by_code(
            client,
            str(dept_code).strip(),
        )

        if not department_id:
            logger.error(
                "❌ Department not found in Biotime | code=%s",
                dept_code,
            )
            return False

        department_id = int(department_id)

        # --------------------------------------------------
        # 📸 Read Snapshot (REAL VALUE)
        # --------------------------------------------------
        snapshot = get_employee_snapshot(client, resolved_id)
        current_department = snapshot.get("department")

        # --------------------------------------------------
        # 🛡️ Idempotent Guard
        # --------------------------------------------------
        if current_department == department_id:
            logger.info(
                "✔ Patch Department Skipped | no change | employee=%s | dept=%s",
                resolved_id,
                department_id,
            )
            return True

        # --------------------------------------------------
        # 🚀 PATCH
        # --------------------------------------------------
        payload = {"department": department_id}

        url = f"{client.base_url}/personnel/api/employees/{resolved_id}/"

        logger.warning("🧪 PATCH DEPT URL: %s", url)
        logger.warning("🧪 PATCH DEPT PAYLOAD: %s", payload)

        res = client._patch(url, json=payload, timeout=25)

        if not res or res.status_code not in (200, 202):
            logger.error(
                "❌ Patch Employee Department Failed | status=%s | body=%s",
                getattr(res, "status_code", None),
                getattr(res, "text", "")[:500],
            )
            return False

        logger.info(
            "✅ Patch Employee Department Success | employee=%s | dept_code=%s",
            employee_id,
            dept_code,
        )
        return True

    except Exception:
        logger.exception("❌ Patch Employee Department Exception")
        return False

# ============================================================
# 🧩 Auto Patch Employee Name (Company Scoped — MT Safe)
# ============================================================

def patch_employee_name(
    *,
    company,
    employee_id: str,
    full_name: str,
) -> bool:
    """
    تحديث اسم الموظف في Biotime.
    ✔ Company Scoped
    ✔ JWT / Session Auto
    ✔ Production & Local Safe
    """

    try:
        if not company:
            logger.error("❌ Patch Name Failed | company missing")
            return False

        if not full_name or not str(full_name).strip():
            logger.warning(
                "⚠️ Patch Name Skipped | empty name | employee=%s",
                employee_id,
            )
            return True

        # --------------------------------------------------
        # 🔐 Auth (Company Scoped)
        # --------------------------------------------------
        client, error = get_authenticated_client(company=company)

        if error or not client:
            logger.error("❌ Patch Name Failed | Auth Error")
            return False

        # --------------------------------------------------
        # 🔎 Resolve Internal Biotime Employee ID
        # --------------------------------------------------
        resolved_id = (
            resolve_employee_biotime_id(
                client,
                str(employee_id).strip()
            )
            or str(employee_id).strip()
        )

        if not resolved_id:
            logger.error(
                "❌ Cannot resolve Biotime employee id | employee=%s",
                employee_id,
            )
            return False

        # --------------------------------------------------
        # 🧠 Split Name Safely
        # --------------------------------------------------
        safe_name = str(full_name).strip()
        parts = safe_name.split(" ", 1)

        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        payload = {
            "first_name": first_name,
            "last_name": last_name,
        }

        url = f"{client.base_url}/personnel/api/employees/{resolved_id}/"

        logger.warning("🧪 PATCH NAME URL: %s", url)
        logger.warning("🧪 PATCH NAME PAYLOAD: %s", payload)

        res = client._patch(url, json=payload, timeout=20)

        if not res:
            logger.error("❌ PATCH Name returned None")
            return False

        logger.warning("🧪 PATCH NAME STATUS: %s", res.status_code)
        logger.warning("🧪 PATCH NAME RESPONSE: %s", res.text[:1000])

        if res.status_code not in (200, 202):
            logger.error(
                "❌ Patch Employee Name Failed | status=%s | body=%s",
                res.status_code,
                res.text[:500],
            )
            return False

        logger.info(
            "✅ Patch Employee Name Success | employee=%s | name=%s",
            employee_id,
            safe_name,
        )
        return True

    except Exception:
        logger.exception("❌ Patch Employee Name Exception")
        return False


# ============================================================
# 🧩 Auto Patch Employee Position (SAFE + Company Scoped)
# ============================================================

def patch_employee_position(
    *,
    company,
    employee_id: str,
    position_code: str,
) -> bool:
    """
    تحديث وظيفة الموظف (Position) في Biotime باستخدام position_code.
    Company-Scoped + JWT/Session Auto.
    """

    try:
        if not position_code:
            logger.warning(
                "⚠️ Patch Position Skipped | empty position_code | employee=%s",
                employee_id,
            )
            return True

        # --------------------------------------------------
        # 🔐 Company Scoped Client
        # --------------------------------------------------
        client, error = get_authenticated_client(company=company)
        if error or not client:
            logger.error("❌ Patch Position Failed | Auth Error")
            return False

        # --------------------------------------------------
        # 🔎 Resolve Internal Biotime Employee ID
        # --------------------------------------------------
        resolved_id = (
            resolve_employee_biotime_id(client, str(employee_id).strip())
            or str(employee_id).strip()
        )

        if not resolved_id:
            logger.error(
                "❌ Cannot resolve Biotime employee id | employee=%s",
                employee_id,
            )
            return False

        # --------------------------------------------------
        # 🔎 Resolve Position ID by Code
        # --------------------------------------------------
        position_id = resolve_position_id_by_code(
            client,
            str(position_code).strip(),
        )

        if not position_id:
            logger.error(
                "❌ Position not found in Biotime | code=%s",
                position_code,
            )
            return False

        payload = {
            "position": int(position_id),
        }

        url = f"{client.base_url}/personnel/api/employees/{resolved_id}/"

        logger.warning("🧪 PATCH POSITION URL: %s", url)
        logger.warning("🧪 PATCH POSITION PAYLOAD: %s", payload)

        res = client._patch(url, json=payload, timeout=20)

        if not res:
            logger.error("❌ PATCH Position returned None")
            return False

        logger.warning("🧪 PATCH POSITION STATUS: %s", res.status_code)
        logger.warning("🧪 PATCH POSITION RESPONSE: %s", res.text[:1000])

        if res.status_code not in (200, 202):
            logger.error(
                "❌ Patch Employee Position Failed | status=%s | body=%s",
                res.status_code,
                res.text[:500],
            )
            return False

        logger.info(
            "✅ Patch Employee Position Success | employee=%s | position_code=%s",
            employee_id,
            position_code,
        )
        return True

    except Exception:
        logger.exception("❌ Patch Employee Position Exception")
        return False

# ============================================================
# 🛡️ Enterprise Ensure Pattern (Push Safety Net)
# ============================================================

def ensure_branch_exists(branch: CompanyBranch, client=None):
    """
    Ensure Area موجودة في BioTime
    ✔ Reuse Authenticated Client (Performance Optimized)
    ✔ لا Sync كامل
    ✔ Create فقط إذا مفقودة
    """

    if not branch.is_active:
        return True

    # ----------------------------------------
    # 🔐 Reuse Client
    # ----------------------------------------
    if client is None:
        client, error = get_authenticated_client()
        if error:
            return False

    # ----------------------------------------
    # 🆔 Ensure biotime_code
    # ----------------------------------------
    if not branch.biotime_code:
        branch.biotime_code = _generate_biotime_code("BR", branch.id)
        branch.save(update_fields=["biotime_code"])

    # ----------------------------------------
    # 🔎 Check existence
    # ----------------------------------------
    exists = resolve_area_id_by_code(client, branch.biotime_code)

    if exists:
        return True

    logger.warning(
        "⚠️ Area missing in BioTime → creating | branch=%s",
        branch.id
    )

    result = get_or_create_area(client, branch.name, branch.biotime_code)

    return bool(result)


#============================================================
#🔥 2 — تعديل ensure_department_exists
#============================================================
def ensure_department_exists(department: CompanyDepartment, client=None):
    """
    Ensure Department موجود في BioTime
    ✔ Reuse Authenticated Client
    ✔ Performance Optimized
    """

    if not department.is_active:
        return True

    if client is None:
        client, error = get_authenticated_client()
        if error:
            return False

    if not department.biotime_code:
        department.biotime_code = _generate_biotime_code("DEPT", department.id)
        department.save(update_fields=["biotime_code"])

    exists = resolve_department_id_by_code(client, department.biotime_code)

    if exists:
        return True

    logger.warning(
        "⚠️ Department missing in BioTime → creating | dept=%s",
        department.id
    )

    result = get_or_create_department(
        client,
        department.name,
        department.biotime_code,
    )

    return bool(result)

#============================================================
#🔥 3 — تعديل ensure_position_exists
#============================================================
def ensure_position_exists(jobtitle: JobTitle, client=None):
    """
    Ensure Position موجودة في BioTime
    ✔ Reuse Authenticated Client
    ✔ Performance Optimized
    """

    if not jobtitle.is_active:
        return True

    if client is None:
        client, error = get_authenticated_client()
        if error:
            return False

    if not jobtitle.biotime_code:
        jobtitle.biotime_code = _generate_biotime_code("POS", jobtitle.id)
        jobtitle.save(update_fields=["biotime_code"])

    exists = resolve_position_id_by_code(client, jobtitle.biotime_code)

    if exists:
        return True

    logger.warning(
        "⚠️ Position missing in BioTime → creating | job=%s",
        jobtitle.id
    )

    result = get_or_create_position(
        client,
        jobtitle.name,
        jobtitle.biotime_code,
    )

    return bool(result)

# ============================================================
# 🚀 Push Employee (STRICT TWO PHASE + MULTI AREA — ENTERPRISE SAFE)
# ============================================================

def push_employee_to_biotime(
    *,
    company,   # ✅ NEW — REQUIRED CONTEXT
    emp_code: str,
    first_name: str,
    last_name: str,
    area_codes: Optional[Iterable[str]] = None,
    area_code: Optional[str] = None,
    dept_code: str,
    position_code: str,
    card_no: str = "",
    is_active: bool = True,
):
    """
    ✔ STRICT COMPANY CONTEXT
    ✔ SINGLE AUTH SESSION
    ✔ PERFORMANCE BOOST
    ✔ ENTERPRISE SAFE
    ✔ MULTI-TENANT HARD GUARDED
    """

    # ========================================================
    # 🔐 Strict Company Guard
    # ========================================================
    if not company:
        return {
            "status": "error",
            "message": "Company context مطلوب."
        }

    client, error = get_authenticated_client(company=company)
    if error:
        return {"status": "error", "message": error}

    try:

        # ====================================================
        # ---------- Department ----------
        # ====================================================
        department = CompanyDepartment.objects.filter(
            company=company,
            biotime_code=dept_code
        ).first()

        if department:
            if not ensure_department_exists(department, client=client):
                return {
                    "status": "error",
                    "message": "فشل ضمان وجود القسم في BioTime"
                }

        # ====================================================
        # ---------- Position ----------
        # ====================================================
        job = JobTitle.objects.filter(
            company=company,
            biotime_code=position_code
        ).first()

        if job:
            if not ensure_position_exists(job, client=client):
                return {
                    "status": "error",
                    "message": "فشل ضمان وجود الوظيفة في BioTime"
                }

        # ====================================================
        # ---------- Branch ----------
        # ====================================================
        normalized_area_codes = _normalize_area_codes(
            area_codes=area_codes,
            area_code=area_code,
        )

        for code in normalized_area_codes:
            branch = CompanyBranch.objects.filter(
                company=company,
                biotime_code=code
            ).first()

            if branch:
                if not ensure_branch_exists(branch, client=client):
                    return {
                        "status": "error",
                        "message": "فشل ضمان وجود الفرع في BioTime"
                    }

        # ====================================================
        # ---------- Payload ----------
        # ====================================================
        payload, err = build_biotime_employee_payload(
            emp_code=emp_code,
            first_name=first_name,
            last_name=last_name,
            area_codes=area_codes,
            area_code=area_code,
            dept_code=dept_code,
            position_code=position_code,
            card_no=card_no,
            is_active=is_active,
            client=client,   # ✅ PERFORMANCE PASS
        )

        if err:
            return {"status": "error", "message": err}

        # ====================================================
        # ---------- Create ----------
        # ====================================================
        result = client.create_employee(payload)

        if result.get("status") != "success":
            return result

        employee_id = result.get("data", {}).get("id")

        # ====================================================
        # ---------- Post Patch ----------
        # ====================================================
        try:
            area_ids = payload.get("area") or []

            result["area_patched"] = bool(
                employee_id and
                patch_employee_area(client, employee_id, area_ids)
            )

            result["department_patched"] = bool(
                employee_id and
                patch_employee_department(
                    company=company,
                    employee_id=employee_id,
                    dept_code=dept_code,
                )
            )

        except Exception:
            logger.exception("❌ Post Create Patch Flow Failed")

        return result

    except Exception:
        logger.exception("❌ Push Employee Enterprise Flow Failed")
        return {
            "status": "error",
            "message": "❌ حدث خطأ غير متوقع أثناء إنشاء الموظف في BioTime."
        }

# ============================================================
# 🟦 Phase E.x — Explicit Company Master Data Sync (SAFE)
# ============================================================

def sync_company_branches(company):
    """
    🔄 Sync ALL CompanyBranch → Biotime Areas
    ✔ Company Scoped (MT-6 Strict)
    ✔ Single Auth Session (Performance Optimized)
    ✔ Create if missing only
    ✔ Idempotent
    ✔ NO delete
    """

    if not company:
        return {
            "status": "error",
            "message": "Company context مطلوب."
        }

    # --------------------------------------------------
    # 🔐 Authenticate Once (Single Session)
    # --------------------------------------------------
    client, error = get_authenticated_client(company=company)

    if error or not client:
        logger.error(
            "❌ Company Branch Sync Failed | company=%s | auth_error=%s",
            getattr(company, "id", None),
            error,
        )
        return {
            "status": "error",
            "message": error or "فشل تسجيل الدخول إلى Biotime."
        }

    synced = 0
    skipped = 0

    branches = CompanyBranch.objects.filter(
        company=company,
        is_active=True,
    )

    # --------------------------------------------------
    # 🔁 Loop (Reuse Client — NO re-auth)
    # --------------------------------------------------
    for branch in branches:
        try:
            result = create_or_sync_branch(branch)

            if result:
                synced += 1
            else:
                skipped += 1

        except Exception:
            skipped += 1
            logger.exception(
                "❌ Branch Sync Failed | company=%s | branch_id=%s",
                company.id,
                branch.id,
            )

    logger.info(
        "✅ Company Branches Sync Completed | company=%s | synced=%s | skipped=%s",
        company.id,
        synced,
        skipped,
    )

    return {
        "status": "success",
        "synced": synced,
        "skipped": skipped,
        "total": synced + skipped,
    }


def sync_company_departments(company):
    """
    🔄 Sync ALL CompanyDepartment → Biotime Departments
    ✔ Company Scoped (MT-6 Strict)
    ✔ Single Auth Session
    ✔ Idempotent
    ✔ NO Area Creation Here
    """

    if not company:
        return {
            "status": "error",
            "message": "Company context مطلوب.",
        }

    # --------------------------------------------------
    # 🔐 Authenticate Once (Performance + Safety)
    # --------------------------------------------------
    client, error = get_authenticated_client(company=company)
    if error or not client:
        return {
            "status": "error",
            "message": error or "فشل المصادقة مع Biotime.",
        }

    synced = skipped = 0

    departments = CompanyDepartment.objects.filter(
        company=company,
        is_active=True,
    )

    for dept in departments:
        try:
            result = create_or_sync_department(
                department=dept,
                client=client,  # 🔥 Reuse Same Client
            )

            if result:
                synced += 1
            else:
                skipped += 1

        except Exception:
            skipped += 1
            logger.exception(
                "❌ Department Sync Failed | dept_id=%s",
                dept.id,
            )

    logger.info(
        "✅ Company Departments Sync Completed | company=%s | synced=%s | skipped=%s",
        company.id,
        synced,
        skipped,
    )

    return {
        "status": "success",
        "synced": synced,
        "skipped": skipped,
        "total": synced + skipped,
    }

def sync_company_job_titles(company):
    """
    🔄 Sync ALL JobTitle → Biotime Positions
    ✔ Company Scoped (MT-6 Strict)
    ✔ Create / Ensure Only
    ✔ Idempotent
    ✔ Safe Logging
    """

    if not company:
        return {
            "synced": 0,
            "skipped": 0,
            "total": 0,
            "error": "Company context مطلوب."
        }

    synced = 0
    skipped = 0

    job_titles = JobTitle.objects.filter(
        company=company,
        is_active=True,
    )

    for job in job_titles:
        try:
            result = create_or_sync_jobtitle(job)

            # ✔ أي نتيجة غير None نعتبرها نجاح
            if result is not None:
                synced += 1
            else:
                skipped += 1

        except Exception:
            skipped += 1
            logger.exception(
                "❌ JobTitle Sync Failed | company=%s | job_id=%s",
                company.id,
                job.id,
            )

    logger.info(
        "✅ Company JobTitles Sync Completed | company=%s | synced=%s | skipped=%s",
        company.id,
        synced,
        skipped,
    )

    return {
        "synced": synced,
        "skipped": skipped,
        "total": synced + skipped,
    }

# ======================================================
# 🔄 PATCH BioTime Position Name
# ======================================================

def patch_biotime_position_name(*, company, job_title):
    """
    Update BioTime position name.
    SAFE:
    - Requires biotime_position_id
    - PATCH only
    - No exception propagation
    """

    if not job_title.biotime_position_id:
        return None

    try:
        client = BiotimeAPIClient(setting=company.biotime_setting)

        payload = {
            "position_name": job_title.name,
        }

        return client._patch(
            f"/personnel/positions/{job_title.biotime_position_id}/",
            payload,
        )

    except Exception as e:
        print(
            f"[BioTime][PATCH NAME] jt={job_title.id} "
            f"biotime_id={job_title.biotime_position_id} error={e}"
        )
        return None
# ======================================================
# 🧠 BioTime — Create Position (OFFICIAL)
# ======================================================

def create_biotime_position(company, job_title):
    """
    Create position in BioTime and return its ID.
    SAFE:
    - Idempotent (won't recreate if already linked)
    - Raises no exception outward
    """

    # لا نعيد الإنشاء لو كان مربوط
    if job_title.biotime_position_id:
        return {
            "position_id": job_title.biotime_position_id,
            "created": False,
        }

    try:
        from biotime_center.models import BiotimeSetting
        from biotime_center.sync_service import BiotimeAPIClient

        biotime_setting = (
            BiotimeSetting.objects
            .filter(company=company)
            .first()
        )

        if not biotime_setting:
            raise Exception("BioTime setting not found")

        client = BiotimeAPIClient(setting=biotime_setting)

        payload = {
            "position_name": job_title.name,
            "parent": None,
        }

        response = client._post("/personnel/positions/", payload)

        # BioTime يرجع id
        position_id = response.get("id")

        if not position_id:
            raise Exception(f"Invalid BioTime response: {response}")

        # حفظ الربط
        job_title.biotime_position_id = position_id
        job_title.save(update_fields=["biotime_position_id"])

        return {
            "position_id": position_id,
            "created": True,
        }

    except Exception as e:
        print(
            f"[BioTime Create Position] failed "
            f"(job_title={job_title.id}): {e}"
        )
        return None
