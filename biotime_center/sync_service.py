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

logger = logging.getLogger(__name__)


# ============================================================
# 🟦 1) قراءة إعدادات Biotime
# ============================================================

def get_settings():
    return BiotimeSetting.objects.first()


# ============================================================
# 🔐 2) تسجيل الدخول
# ============================================================

def get_authenticated_client():
    setting = get_settings()
    if not setting:
        return None, "⚠️ إعدادات الاتصال غير موجودة."

    client = BiotimeAPIClient(setting)
    auth = client.authenticate()

    if auth.get("status") != "success":
        logger.warning("Biotime Authentication Failed: %s", auth)
        return None, "❌ فشل تسجيل الدخول — تحقق من بيانات Biotime."

    return client, None


# ============================================================
# 🧪 2.1) Test Connection
# ============================================================

def test_connection():
    try:
        setting = get_settings()
        if not setting:
            return {"status": "error", "message": "⚠️ إعدادات Biotime غير موجودة."}

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
            "message": "✔ تم الاتصال بـ Biotime بنجاح.",
            "meta": {"token_expiry": str(setting.token_expiry)},
        }

    except Exception as exc:
        logger.exception("Biotime Test Connection Service Error")
        return {
            "status": "error",
            "message": "⚠️ خطأ غير متوقع أثناء اختبار الاتصال.",
            "exception": str(exc),
        }


# ============================================================
# 💻 3) مزامنة الأجهزة — Terminals
# ============================================================

def sync_devices():
    start_time = timezone.now()

    client, error = get_authenticated_client()
    if error:
        return {"status": "error", "message": error}

    terminals = client.get_devices()
    if terminals is None:
        return {"status": "error", "message": "❌ فشل جلب أجهزة IClock."}

    BiotimeDevice.objects.all().delete()
    count = 0

    for d in terminals:
        area_info = d.get("area", {}) or {}

        BiotimeDevice.objects.create(
            device_id=d.get("id"),
            sn=d.get("sn"),
            alias=d.get("alias") or d.get("terminal_name") or "—",
            terminal_name=d.get("terminal_name"),
            ip_address=d.get("ip_address"),
            firmware_version=d.get("fw_ver"),
            state=d.get("state"),
            terminal_tz=d.get("terminal_tz"),
            area_name=area_info.get("area_name"),
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

    logger.info(
        "Biotime Devices Sync Completed | count=%s | %sms",
        count,
        elapsed_ms,
    )

    return {
        "status": "success",
        "count": count,
        "elapsed_ms": elapsed_ms,
        "message": f"✔ تمت مزامنة {count} جهاز IClock بنجاح.",
    }


# ============================================================
# 👥 4) مزامنة الموظفين (READ ONLY)
# ============================================================

def sync_employees():
    start_time = timezone.now()

    client, error = get_authenticated_client()
    if error:
        return {"status": "error", "message": error}

    employees = client.get_employees()
    if employees is None:
        return {"status": "error", "message": "❌ فشل جلب الموظفين."}

    synced = updated = skipped = 0
    now = timezone.now()

    for e in employees:
        try:
            employee_id = e.get("emp_code") or e.get("id")
            if not employee_id:
                skipped += 1
                continue

            defaults = {
                "full_name": f"{e.get('first_name', '')} {e.get('last_name', '')}".strip(),
                "department": e.get("department"),
                "position": e.get("position"),
                "card_number": e.get("card_no"),
                "is_active": bool(e.get("is_active", True)),
                "last_sync": now,
            }

            _, created = BiotimeEmployee.objects.update_or_create(
                employee_id=employee_id,
                defaults=defaults,
            )

            if created:
                synced += 1
            else:
                updated += 1

        except Exception:
            skipped += 1
            logger.exception("❌ Employee Sync Error")

    elapsed_ms = int((timezone.now() - start_time).total_seconds() * 1000)

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


def sync_logs(start_date=None, end_date=None):
    """
    🔄 مزامنة سجلات Biotime الخام إلى جدول BiotimeLog فقط (Staging Layer).

    خصائص:
    - Idempotent (update_or_create على log_id)
    - لا يكتب في AttendanceRecord إطلاقًا
    - آمن للتشغيل المتكرر
    - يدعم range filtering
    """

    client, error = get_authenticated_client()
    if error:
        return {"status": "error", "message": error}

    transactions = client.get_logs(start_date, end_date)
    if transactions is None:
        return {"status": "error", "message": "❌ فشل جلب السجلات من Biotime."}

    saved = updated = skipped = 0

    for t in transactions:
        try:
            # ======================================================
            # 🧩 1) تجهيز punch_time بشكل آمن 100%
            # ======================================================
            raw_punch_time = t.get("punch_time")
            punch_time = None

            if raw_punch_time:
                parsed = parse_datetime(str(raw_punch_time))

                if isinstance(parsed, datetime):
                    punch_time = parsed
                    if timezone.is_naive(punch_time):
                        punch_time = timezone.make_aware(punch_time)
                else:
                    logger.warning(
                        "⚠️ Invalid punch_time skipped: %s",
                        raw_punch_time,
                    )
                    skipped += 1
                    continue

            if not punch_time:
                skipped += 1
                continue

            # ======================================================
            # 🧩 2) حفظ السجل الخام فقط داخل BiotimeLog
            # ======================================================
            biotime_log, created = BiotimeLog.objects.update_or_create(
                log_id=t.get("id"),
                defaults={
                    "employee_code": t.get("emp_code"),
                    "punch_time": punch_time,
                    "punch_state": t.get("punch_state"),
                    "device_sn": t.get("terminal_sn"),
                    "terminal_alias": t.get("terminal_alias"),
                    "area_alias": t.get("area_alias"),
                    "raw_json": t,
                    "processed": False,   # سيتم معالجته لاحقًا في Attendance Sync
                },
            )

            if created:
                saved += 1
            else:
                updated += 1

        except Exception:
            skipped += 1
            logger.exception("❌ Failed syncing Biotime raw log")

    return {
        "status": "success",
        "new": saved,
        "updated": updated,
        "skipped": skipped,
        "total": saved + updated,
        "message": (
            f"✔ Raw Logs Sync Completed | new={saved} | "
            f"updated={updated} | skipped={skipped}"
        ),
    }

# ============================================================
# 🧩 Unified Master Sync Service (SAFE)
# ============================================================

from company_manager.models import CompanyBranch, CompanyDepartment, JobTitle


def _generate_biotime_code(prefix: str, instance_id: int) -> str:
    """
    توليد كود رقمي فقط بدون Default
    """
    return str(instance_id)


# ---------------- Area ----------------

def get_or_create_area(client, name: str, code: str):
    try:
        url = f"{client.base_url}/personnel/api/areas/"
        payload = {"area_name": name, "area_code": code}
        res = client._post(url, json=payload, timeout=20)

        if not res or res.status_code not in (200, 201):
            return None

        return res.json()

    except Exception:
        logger.exception("❌ Failed creating Area")
        return None


# ---------------- Department ----------------

def get_or_create_department(client, name: str, code: str):
    try:
        url = f"{client.base_url}/personnel/api/departments/"
        payload = {"dept_name": name, "dept_code": code}
        res = client._post(url, json=payload, timeout=20)

        if not res or res.status_code not in (200, 201):
            return None

        return res.json()

    except Exception:
        logger.exception("❌ Failed creating Department")
        return None


# ---------------- Position ----------------

def get_or_create_position(client, name: str, code: str):
    try:
        url = f"{client.base_url}/personnel/api/positions/"
        payload = {"position_name": name, "position_code": code}
        res = client._post(url, json=payload, timeout=20)

        if not res or res.status_code not in (200, 201):
            return None

        return res.json()

    except Exception:
        logger.exception("❌ Failed creating Position")
        return None


# ---------------- Public Sync APIs ----------------

def create_or_sync_branch(branch: CompanyBranch):
    if not branch.is_active:
        return None

    client, error = get_authenticated_client()
    if error:
        return None

    if not branch.biotime_code:
        branch.biotime_code = _generate_biotime_code("BR", branch.id)
        branch.save(update_fields=["biotime_code"])

    return get_or_create_area(client, branch.name, branch.biotime_code)


def create_or_sync_department(department: CompanyDepartment):
    """
    ======================================================
    🏢 Sync CompanyDepartment → Biotime Department ONLY
    ❌ ممنوع إنشاء Area من القسم
    ======================================================
    """

    if not department.is_active:
        return None

    client, error = get_authenticated_client()
    if error:
        return None

    # --------------------------------------------------
    # 🆔 Generate biotime_code once
    # --------------------------------------------------
    if not department.biotime_code:
        department.biotime_code = _generate_biotime_code("DEPT", department.id)
        department.save(update_fields=["biotime_code"])

    # --------------------------------------------------
    # ✅ Department ONLY (NO AREA HERE)
    # --------------------------------------------------
    return get_or_create_department(
        client,
        department.name,
        department.biotime_code,
    )

def create_or_sync_jobtitle(jobtitle: JobTitle):
    if not jobtitle.is_active:
        return None

    client, error = get_authenticated_client()
    if error:
        return None

    if not jobtitle.biotime_code:
        jobtitle.biotime_code = _generate_biotime_code("POS", jobtitle.id)
        jobtitle.save(update_fields=["biotime_code"])

    return get_or_create_position(client, jobtitle.name, jobtitle.biotime_code)


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
    try:
        url = f"{client.base_url}{endpoint}"
        res = client._get(url, params={code_field: code_value}, timeout=15)

        if not res or res.status_code != 200:
            return None

        data = (res.json() or {}).get("data") or []
        if not data:
            return None

        return data[0].get("id")

    except Exception:
        logger.exception("❌ Resolve by code failed")
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
        # 🧹 Normalize Department
        # --------------------------------------------------
        dept = data.get("department")
        try:
            dept = int(dept) if dept is not None else None
        except Exception:
            dept = None

        # --------------------------------------------------
        # 🧹 Normalize Position
        # --------------------------------------------------
        pos = data.get("position")
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


def build_biotime_employee_payload(
    *,
    emp_code: str,
    first_name: str,
    last_name: str,
    area_codes: Optional[Iterable[str]] = None,
    area_code: Optional[str] = None,   # Legacy Support
    dept_code: str,
    position_code: str,
    card_no: str = "",
    is_active: bool = True,
):
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
        "area": area_ids,     # ✅ Multi Area
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
# 🧩 Phase E.2 — Replace Employee Areas (AUTHORITATIVE MODE)
# ============================================================

def patch_employee_areas_replace(
    *,
    employee_id: str,
    area_codes: Iterable[str],
) -> bool:
    """
    استبدال كامل للفروع (Areas) الخاصة بالموظف في BioTime.
    ✔ يحذف الفروع القديمة.
    ✔ يطابق الواجهة كنقطة حقيقة (Source of Truth).
    ✔ آمن — يعتمد على Snapshot قبل التعديل.
    """

    try:
        client, error = get_authenticated_client()
        if error or not client:
            logger.error("❌ Patch Replace Areas Failed | Auth Error")
            return False

        # --------------------------------------------------
        # 🔎 Resolve Internal Employee ID
        # --------------------------------------------------
        resolved_id = (
            resolve_employee_biotime_id(client, str(employee_id).strip())
            or str(employee_id).strip()
        )

        if not resolved_id:
            logger.error("❌ Cannot resolve employee id | employee=%s", employee_id)
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
        # 📸 Read Snapshot
        # --------------------------------------------------
        snapshot = get_employee_snapshot(client, resolved_id)
        current_area_ids = sorted(snapshot.get("areas") or [])

        # --------------------------------------------------
        # 🛡️ Idempotent Guard
        # --------------------------------------------------
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
# 🧩 Auto Patch Employee Department (SAFE)
# ============================================================

def patch_employee_department(
    *,
    employee_id: str,
    dept_code: str,
) -> bool:
    """
    تحديث قسم الموظف (Department) في Biotime باستخدام dept_code.
    """

    try:
        if not dept_code:
            logger.warning(
                "⚠️ Patch Department Skipped | empty dept_code | employee=%s",
                employee_id,
            )
            return True

        client, error = get_authenticated_client()
        if error or not client:
            logger.error("❌ Patch Department Failed | Auth Error")
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

        payload = {
            "department": int(department_id),
        }

        url = f"{client.base_url}/personnel/api/employees/{resolved_id}/"

        logger.warning("🧪 PATCH DEPT URL: %s", url)
        logger.warning("🧪 PATCH DEPT PAYLOAD: %s", payload)

        res = client._patch(url, json=payload, timeout=20)

        if not res:
            logger.error("❌ PATCH Department returned None")
            return False

        if res.status_code not in (200, 202):
            logger.error(
                "❌ Patch Employee Department Failed | status=%s | body=%s",
                res.status_code,
                res.text[:500],
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
# 🧩 Auto Patch Employee Name
# ============================================================

def patch_employee_name(*, employee_id: str, full_name: str) -> bool:
    """
    تحديث اسم الموظف في Biotime.
    يستخدم PATCH آمن (JWT / Session Auto).
    """
    try:
        if not full_name or not str(full_name).strip():
            logger.warning(
                "⚠️ Patch Name Skipped | empty name | employee=%s",
                employee_id,
            )
            return True

        client, error = get_authenticated_client()
        if error or not client:
            logger.error("❌ Patch Name Failed | Auth Error")
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
        # 🧠 Split Name Safely (Biotime يحتاج first / last)
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
# 🧩 Auto Patch Employee Position
# ============================================================

def patch_employee_position(*, employee_id: str, position_code: str) -> bool:
    """
    تحديث وظيفة الموظف (Position) في Biotime باستخدام position_code.
    """
    try:
        if not position_code:
            logger.warning(
                "⚠️ Patch Position Skipped | empty position_code | employee=%s",
                employee_id,
            )
            return True

        client, error = get_authenticated_client()
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
# 🚀 Push Employee (STRICT TWO PHASE + MULTI AREA)
# ============================================================

def push_employee_to_biotime(
    *,
    emp_code: str,
    first_name: str,
    last_name: str,
    area_codes: Optional[Iterable[str]] = None,
    area_code: Optional[str] = None,   # Legacy
    dept_code: str,
    position_code: str,
    card_no: str = "",
    is_active: bool = True,
):
    client, error = get_authenticated_client()
    if error:
        return {"status": "error", "message": error}

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
    )
    if err:
        return {"status": "error", "message": err}

    result = client.create_employee(payload)
    if result.get("status") != "success":
        return result

    # ============================
    # 🧩 Post Create Auto Patch
    # ============================
    try:
        employee_id = result.get("data", {}).get("id")
        area_ids = payload.get("area") or []
        dept_id = payload.get("department")

        # --- Patch Area (MULTI) ---
        result["area_patched"] = bool(
            employee_id and
            patch_employee_area(client, employee_id, area_ids)
        )

        # --- Patch Department ---
        result["department_patched"] = bool(
            employee_id and dept_id and
            patch_employee_department(client, employee_id, dept_id)
        )

    except Exception:
        logger.exception("❌ Post Create Patch Flow Failed")
        result["area_patched"] = False
        result["department_patched"] = False

    return result
