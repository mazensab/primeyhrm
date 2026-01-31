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
from django.shortcuts import get_object_or_404   # ✅ إضافة آمنة

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
    append_employee_area,        # ✅ Phase E.1
    push_employee_to_biotime,    # ✅ Phase E — Unified Creator
)

from company_manager.models import CompanyUser
from employee_center.models import Employee     # ✅ إضافة آمنة

# ✅ PATCH — Bulk Linker Service
from employee_center.services.biotime_linker import link_biotime_employees

logger = logging.getLogger(__name__)

# ================================================================
# 🔐 Internal Helpers
# ================================================================

TEST_LOCK_KEY = "biotime:test-connection:lock"
TEST_LOCK_TTL = 15  # seconds

# 🔒 PUSH EMPLOYEE LOCK
PUSH_LOCK_PREFIX = "biotime:push-employee:"
PUSH_LOCK_TTL = 20  # seconds

# ================================================================
# 🌍 Geo Resolver — Constants (SAFE)
# ================================================================

GEO_IP_TIMEOUT = 4
GEO_REVERSE_TIMEOUT = 5
GEO_CACHE_TTL = 60 * 60 * 12  # 12h cache


def _trace_id():
    """Generate short trace id for logs."""
    return uuid.uuid4().hex[:12]


def resolve_company_user(request):
    """
    Resolve active company context safely.
    """
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


def normalize_server_url(raw_url: str) -> str:
    """
    Normalize and validate server URL strictly.
    - Enforce HTTPS
    - Allow only scheme + hostname (no path/query/fragment)
    """
    raw_url = (raw_url or "").strip()

    if not raw_url:
        raise ValueError("Server URL is required.")

    if not raw_url.startswith("https://"):
        raise ValueError("Server URL must start with HTTPS.")

    parsed = urlparse(raw_url)

    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid server URL format.")

    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("Server URL must not contain path or query parameters.")

    normalized = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return normalized


def api_success(**payload):
    return JsonResponse({"status": "success", **payload}, status=200)


def api_error(message, status=400, **extra):
    return JsonResponse(
        {"status": "error", "message": message, **extra},
        status=status
    )


# ================================================================
# 🌍 Geo Resolver (FAST + SAFE + FALLBACK)
# ================================================================

_ARABIC_RE = re.compile(r"[\u0600-\u06FF]+")


def _contains_arabic(text: str) -> bool:
    if not text:
        return False
    return bool(_ARABIC_RE.search(text))


def _safe_get_json(url: str, *, params=None, headers=None, timeout=5):
    """
    تنفيذ طلب HTTP آمن مع تسجيل الأخطاء.
    """
    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning("🌍 Geo HTTP Error (%s): %s", url, exc)
        return None


def _resolve_ip_coordinates(ip: str):
    """
    تحويل IP إلى (lat, lon) باستخدام ipapi (HTTPS).
    """
    if not ip:
        return None, None, None

    cache_key = f"geo:ip:{ip}"
    cached = cache.get(cache_key)
    if cached:
        return (
            cached.get("lat"),
            cached.get("lon"),
            cached.get("fallback"),
        )

    url = f"https://ipapi.co/{ip}/json/"
    data = _safe_get_json(url, timeout=GEO_IP_TIMEOUT)
    if not data:
        return None, None, None

    lat = data.get("latitude")
    lon = data.get("longitude")

    # Fallback سريع في حال فشل reverse
    city = data.get("city")
    region = data.get("region")
    fallback_parts = [p for p in [city, region] if p]
    fallback_text = " - ".join(fallback_parts) if fallback_parts else None

    if lat and lon:
        cache.set(
            cache_key,
            {
                "lat": lat,
                "lon": lon,
                "fallback": fallback_text,
            },
            GEO_CACHE_TTL,
        )

    return lat, lon, fallback_text


def _reverse_geocode(lat: float, lon: float):
    """
    تحويل الإحداثيات إلى عنوان فعلي عبر OpenStreetMap.
    """
    if not lat or not lon:
        return None

    cache_key = f"geo:reverse:{lat}:{lon}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "json",
        "lat": lat,
        "lon": lon,
        "zoom": 18,
        "addressdetails": 1,
    }

    headers = {"User-Agent": "PrimeyHR-GeoResolver/1.1"}

    data = _safe_get_json(
        url,
        params=params,
        headers=headers,
        timeout=GEO_REVERSE_TIMEOUT,
    )

    if not data:
        return None

    address = data.get("address") or {}
    cache.set(cache_key, address, GEO_CACHE_TTL)
    return address


def build_location_text_from_ip(ip: str) -> str | None:
    """
    🎯 الناتج النهائي:
    شارع ... - حي ... - المدينة
    مع Fallback سريع إذا فشل Reverse Geocode.
    """

    try:
        lat, lon, fallback_text = _resolve_ip_coordinates(ip)
        if not lat or not lon:
            return fallback_text

        address = _reverse_geocode(lat, lon)

        if not address:
            return fallback_text

        road = address.get("road") or address.get("street")
        district = (
            address.get("neighbourhood")
            or address.get("suburb")
            or address.get("quarter")
            or address.get("city_district")
        )
        city = (
            address.get("city")
            or address.get("town")
            or address.get("municipality")
        )

        # تجاهل القيم غير العربية
        road = road if _contains_arabic(road or "") else None
        district = district if _contains_arabic(district or "") else None
        city = city if _contains_arabic(city or "") else None

        parts = []
        if road:
            parts.append(road)
        if district:
            parts.append(f"حي {district}")
        if city:
            parts.append(city)

        if parts:
            return " - ".join(parts)

        return fallback_text

    except Exception:
        logger.exception("🌍 Geo Resolver Fatal Error (ip=%s)", ip)
        return None


# ================================================================
# 🔄 Company Biotime Sync Logs API (READ ONLY)
# ================================================================
@login_required
def company_biotime_sync_logs(request):
    """
    يقدم سجل عمليات المزامنة.
    - Read Only
    """
    company_user = resolve_company_user(request)
    if not company_user:
        return api_error("Company context not found.", status=403)

    logs_qs = (
        BiotimeSyncLog.objects
        .order_by("-timestamp")[:50]
    )

    normalized = []

    for log in logs_qs.values(
        "timestamp",
        "devices_synced",
        "employees_synced",
        "logs_synced",
        "status",
        "message",
    ):
        normalized.append({
            "time": log["timestamp"],
            "status": (log["status"] or "").lower(),
            "message": log["message"] or "—",
            "records": log["logs_synced"] or 0,
            "devices": log["devices_synced"] or 0,
            "employees": log["employees_synced"] or 0,
        })

    return api_success(
        count=len(normalized),
        logs=normalized,
    )


# ================================================================
# 🔐 API — Test Biotime Connection (JWT)
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_test_connection(request):
    """
    اختبار الاتصال مع Biotime عبر Service Layer.
    """

    trace = _trace_id()

    if cache.get(TEST_LOCK_KEY):
        return api_error(
            "⏳ اختبار الاتصال قيد التنفيذ بالفعل، حاول بعد لحظات.",
            status=429,
        )

    cache.set(TEST_LOCK_KEY, True, TEST_LOCK_TTL)

    try:
        start_time = timezone.now()
        result = test_connection()

        latency_ms = int(
            (timezone.now() - start_time).total_seconds() * 1000
        )

        if result.get("status") != "success":
            return api_error(
                result.get("message") or "❌ فشل الاتصال مع Biotime.",
                status=502,
                connected=False,
                latency_ms=latency_ms,
                trace_id=trace,
            )

        return api_success(
            connected=True,
            latency_ms=latency_ms,
            message=result.get("message") or "✔ تم الاتصال بـ Biotime بنجاح.",
            meta=result.get("meta") or {},
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Biotime Test Connection API Error", trace)

        return api_error(
            "⚠️ خطأ غير متوقع أثناء اختبار الاتصال.",
            status=500,
            trace_id=trace,
        )

    finally:
        cache.delete(TEST_LOCK_KEY)


# ================================================================
# 💾 API — Save Biotime Settings + Test Connection
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_save_settings(request):
    """
    حفظ إعدادات Biotime ثم اختبار الاتصال مباشرة.
    """

    trace = _trace_id()

    try:
        payload = json.loads(request.body.decode() or "{}")

        server_url_raw = payload.get("server_url")

        # ✅ PATCH: يقبل company من الواجهة + يبقى متوافق مع biotime_company
        biotime_company = (
            (payload.get("company") or "").strip()
            or (payload.get("biotime_company") or "").strip()
        )

        email = (payload.get("email") or "").strip()
        password = (payload.get("password") or "").strip()

        # ✅ Validation
        if not all([server_url_raw, biotime_company, email, password]):
            return api_error("⚠️ جميع الحقول مطلوبة.", status=400)

        if len(password) < 6:
            return api_error("⚠️ كلمة المرور قصيرة جدًا.", status=400)

        try:
            server_url = normalize_server_url(server_url_raw)
        except ValueError as exc:
            return api_error(f"⚠️ {exc}", status=400)

        # ======================================================
        # 🏢 Resolve Company Context (STRICT)
        # ======================================================
        company_user = resolve_company_user(request)
        if not company_user or not company_user.company:
            return api_error(
                "Company context not found.",
                status=403,
                trace_id=trace,
            )

        company_obj = company_user.company

        # ======================================================
        # 💾 Phase 1 — Save Settings (COMMIT FIRST)
        # ======================================================
        with transaction.atomic():
            setting, _ = BiotimeSetting.objects.get_or_create(
                company=company_obj,
                biotime_company=biotime_company,
                defaults={
                    "server_url": server_url,
                    "email": email,
                    "password": password,
                },
            )

            setting.server_url = server_url
            setting.email = email
            setting.password = password
            setting.biotime_company = biotime_company

            setting.save(update_fields=[
                "server_url",
                "email",
                "password",
                "biotime_company",
            ])

        # ======================================================
        # 🔌 Phase 2 — Test Connection (OUTSIDE TRANSACTION)
        # ======================================================
        result = test_connection()

        if result.get("status") != "success":
            return api_error(
                result.get("message") or "❌ فشل الاتصال مع Biotime.",
                status=502,
                connected=False,
                trace_id=trace,
            )

        return api_success(
            connected=True,
            message="✔ تم حفظ الإعدادات والاتصال بنجاح.",
            meta=result.get("meta") or {},
            trace_id=trace,
        )

    except Exception as exc:
        logger.exception("[%s] Biotime Save Settings Error", trace)

        return api_error(
            "❌ تم رفض حفظ الإعدادات بسبب فشل الاتصال أو خطأ داخلي.",
            status=502,
            trace_id=trace,
            details=str(exc),
        )


# ================================================================
# 👥 API — List Biotime Employees (READ ONLY)
# ================================================================
@login_required
def company_biotime_employees(request):
    """
    إرجاع قائمة موظفي Biotime المتزامنين.
    """

    trace = _trace_id()
    company_user = resolve_company_user(request)

    if not company_user:
        return api_error("Company context not found.", status=403)

    try:
        qs = (
            BiotimeEmployee.objects
            .order_by("employee_id")
            .values(
                "id",
                "employee_id",
                "full_name",
                "position",
                "department",
                "is_active",
            )
        )

        employees = []

        for row in qs:
            name = (row.get("full_name") or "").strip()

            if not name:
                position_raw = (row.get("position") or "").strip()
                name = position_raw or "غير مسمى"

            employees.append({
                "id": row["id"],
                "code": row["employee_id"],
                "name": name,
                "department": row["department"],
                "position": row["position"],
                "is_active": row["is_active"],
            })

        return api_success(
            count=len(employees),
            employees=employees,
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Biotime Employees List API Error", trace)

        return api_error(
            "⚠️ تعذر تحميل موظفي Biotime.",
            status=500,
            trace_id=trace,
        )


# ================================================================
# 👥 API — Sync Employees
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_sync_employees(request):
    """
    تشغيل مزامنة موظفي Biotime عبر Service Layer.
    """

    trace = _trace_id()
    company_user = resolve_company_user(request)

    if not company_user:
        return api_error("Company context not found.", status=403)

    start_time = timezone.now()

    try:
        result = sync_employees()

        elapsed_ms = int(
            (timezone.now() - start_time).total_seconds() * 1000
        )

        status = result.get("status")
        total = result.get("total") or 0
        message = result.get("message") or "—"

        BiotimeSyncLog.objects.create(
            timestamp=timezone.now(),
            devices_synced=0,
            employees_synced=total,
            logs_synced=0,
            status=status,
            message=message,
        )

        if status != "success":
            return api_error(
                message,
                status=502,
                elapsed_ms=elapsed_ms,
                trace_id=trace,
            )

        return api_success(
            total=total,
            elapsed_ms=elapsed_ms,
            message=message,
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Biotime Sync Employees API Error", trace)

        return api_error(
            "⚠️ حدث خطأ غير متوقع أثناء مزامنة الموظفين.",
            status=500,
            trace_id=trace,
        )


# ================================================================
# 🚀 API — Push Employee To Biotime (CREATE) — MULTI AREA SAFE
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_push_employee(request, employee_id: int):
    """
    إنشاء موظف من النظام داخل Biotime (Push).
    - Multi-Branch → Multi-Area
    - Unified Service Layer
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

        # 🔒 منع التكرار
        if employee.biotime_code:
            return api_error(
                "الموظف مرتبط مسبقًا مع Biotime.",
                status=409,
                trace_id=trace,
            )

        # ======================================================
        # ✅ Hard Validation — Business Integrity
        # ======================================================
        if not employee.full_name:
            return api_error(
                "اسم الموظف مطلوب للإرسال إلى Biotime.",
                status=400,
                trace_id=trace,
            )

        if not employee.department:
            return api_error(
                "يجب تحديد القسم للموظف قبل الإرسال إلى Biotime.",
                status=400,
                trace_id=trace,
            )

        if not employee.job_title:
            return api_error(
                "يجب تحديد المسمى الوظيفي للموظف قبل الإرسال إلى Biotime.",
                status=400,
                trace_id=trace,
            )

        # ======================================================
        # ✅ Biotime Codes Mapping
        # ======================================================
        dept_code = getattr(employee.department, "biotime_code", None)
        job_code = getattr(employee.job_title, "biotime_code", None)

        if not dept_code:
            return api_error(
                "القسم غير مربوط مع Biotime (biotime_code مفقود).",
                status=400,
                trace_id=trace,
            )

        if not job_code:
            return api_error(
                "المسمى الوظيفي غير مربوط مع Biotime (biotime_code مفقود).",
                status=400,
                trace_id=trace,
            )

        # ======================================================
        # 🧬 Resolve Multi-Area (Branches → Areas)
        # ======================================================
        branches = list(employee.branches.all())

        area_codes = [
            b.biotime_code
            for b in branches
            if b.biotime_code
        ]

        if not area_codes:
            return api_error(
                "يجب تحديد فرع واحد على الأقل ومربوط مع Biotime.",
                status=400,
                trace_id=trace,
            )

        # ======================================================
        # 🚀 Push Employee (Unified Service Layer)
        # ======================================================
        name_parts = employee.full_name.strip().split(" ")
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) or "-"

        result = push_employee_to_biotime(
            emp_code=str(employee.id),
            first_name=first_name,
            last_name=last_name,
            area_codes=area_codes,          # ✅ Multi Area
            dept_code=dept_code,
            position_code=job_code,
            is_active=True,
        )

        if result.get("status") != "success":
            logger.error(
                "[%s] Biotime PUSH failed: %s",
                trace,
                result,
            )
            return api_error(
                result.get("message") or "فشل إنشاء الموظف داخل Biotime.",
                status=502,
                trace_id=trace,
            )

        # ======================================================
        # 💾 حفظ الربط محليًا
        # ======================================================
        biotime_code = str(employee.id)

        with transaction.atomic():
            employee.biotime_code = biotime_code
            employee.save(update_fields=["biotime_code"])

            BiotimeEmployee.objects.create(
                employee_id=biotime_code,
                full_name=employee.full_name,
                department=dept_code,
                position=job_code,
                is_active=True,
            )

        logger.info(
            "[%s] Biotime PUSH success | employee_id=%s | biotime_code=%s",
            trace,
            employee.id,
            biotime_code,
        )

        return api_success(
            message="✔ تم إنشاء الموظف في Biotime بنجاح.",
            biotime_code=biotime_code,
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Biotime Push Employee Error", trace)

        return api_error(
            "❌ حدث خطأ غير متوقع أثناء إرسال الموظف.",
            status=500,
            trace_id=trace,
        )

    finally:
        cache.delete(lock_key)


# ================================================================
# ➕ API — Append Area To Biotime Employee (PATCH SAFE) 🟦 Phase E.1
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_append_employee_area(request, employee_id: int):
    """
    إضافة Area إضافية لموظف مرتبط مع Biotime (Append فقط — بدون Replace).
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
        payload = json.loads(request.body.decode() or "{}")
        area_code = (payload.get("area_code") or "").strip()

        if not area_code:
            return api_error(
                "⚠️ area_code مطلوب.",
                status=400,
                trace_id=trace,
            )

        employee = get_object_or_404(
            Employee,
            id=employee_id,
            company=company_user.company,
        )

        if not employee.biotime_code:
            return api_error(
                "الموظف غير مرتبط مع Biotime.",
                status=409,
                trace_id=trace,
            )

        result = append_employee_area(
            employee_biotime_id=str(employee.biotime_code),
            new_area_code=area_code,
        )

        if result.get("status") != "success":
            return api_error(
                result.get("message") or "❌ فشل تحديث Area.",
                status=502,
                trace_id=trace,
            )

        return api_success(
            message=result.get("message") or "✔ تم تحديث Area بنجاح.",
            patched=result.get("patched"),
            area_ids=result.get("area_ids") or [],
            trace_id=trace,
        )

    except Exception:
        logger.exception("[%s] Append Employee Area API Error", trace)

        return api_error(
            "❌ حدث خطأ غير متوقع أثناء تحديث Area.",
            status=500,
            trace_id=trace,
        )


# ================================================================
# 🔗 API — Bulk Link Employees (Dry-Run + Execute) ✅ PATCH
# ================================================================
@csrf_exempt
@login_required
@require_POST
def company_biotime_link_employees(request):
    """
    ربط جماعي بين:
    Employee  ↔  BiotimeEmployee
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
    execute = request.GET.get("execute") == "true"

    try:
        logger.info(
            "[%s] Bulk Biotime Link Started | company=%s | execute=%s",
            trace,
            company.id,
            execute,
        )

        result = link_biotime_employees(
            company=company,
            execute=execute,
        )

        return api_success(
            trace_id=trace,
            execute=execute,
            **(result or {}),
        )

    except Exception as exc:
        logger.exception("[%s] Bulk Biotime Link API Error", trace)

        return api_error(
            "❌ حدث خطأ غير متوقع أثناء تنفيذ الربط الجماعي.",
            status=500,
            trace_id=trace,
            details=str(exc),
        )
