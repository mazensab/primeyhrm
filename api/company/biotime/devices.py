# ================================================================
# 📂 api/company/biotime/devices.py
# ⚙️ Version: V17.4 FINAL — SMART DEVICE THRESHOLD (SAFE) 🔒
# Primey HR Cloud
# ================================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta, datetime
import logging

from biotime_center.models import BiotimeDevice, BiotimeSetting
from biotime_center.biotime_api_client import BiotimeAPIClient
from company_manager.models import CompanyUser

# 🌍 Geo Resolver Service (Pure Additive)



# ================================================================
# 🔐 Helpers (SAFE / DRY)
# ================================================================

def resolve_company(request):
    """
    استخراج الشركة الحالية بشكل آمن.
    """
    company_user = (
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
    return company_user.company if company_user else None


def get_biotime_client():
    """
    إنشاء عميل Biotime بعد التحقق من الإعدادات.
    """
    setting = BiotimeSetting.objects.first()
    if not setting:
        raise RuntimeError("Biotime settings not configured.")
    return BiotimeAPIClient(setting)


# ================================================================
# 🧠 Device Online Resolver (LEGACY — DO NOT TOUCH)
# ================================================================

def is_device_online(last_activity, threshold_minutes=5):
    """
    ⚠️ منطقك القديم — لا يتم المساس به إطلاقًا (Backward Compatible)
    """
    if not last_activity:
        return False

    try:
        now = timezone.now()
        delta = now - last_activity
        return delta <= timedelta(minutes=threshold_minutes)
    except Exception:
        return False


# ================================================================
# 🧩 NEW — Safe Datetime Parser
# ================================================================

def parse_biotime_datetime(value):
    """
    تحويل قيمة last_activity القادمة من Biotime إلى datetime بشكل آمن.
    """
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    try:
        value = str(value).replace("T", " ").split(".")[0]
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except Exception:
        logger.warning(f"⚠️ Failed to parse Biotime datetime: {value}")
        return None


# ================================================================
# 🧠 NEW — Dynamic Threshold Resolver
# ================================================================

def resolve_device_threshold(device: BiotimeDevice) -> int:
    """
    تحديد Threshold ذكي حسب نوع الجهاز وقدرته.
    """
    try:
        if (device.face_count or 0) > 0:
            return 2
        if (device.palm_count or 0) > 0:
            return 2
        if (device.fp_count or 0) > 0:
            return 5
        return 10
    except Exception:
        return 10


# ================================================================
# 🟢 NEW — Smart Device Status Engine (SAFE FALLBACK)
# ================================================================

def resolve_device_status(device: BiotimeDevice):
    """
    محرك ذكي لتحديد حالة الجهاز مع Fallback تلقائي.
    """
    threshold_minutes = resolve_device_threshold(device)

    try:
        last_activity_dt = parse_biotime_datetime(device.last_activity)

        if not last_activity_dt:
            return {
                "online": is_device_online(device.last_activity),
                "reason": "legacy_fallback",
                "threshold_minutes": threshold_minutes,
                "last_activity_minutes": None,
            }

        now = timezone.now()
        aware_dt = timezone.make_aware(last_activity_dt)
        delta = now - aware_dt
        minutes = int(delta.total_seconds() / 60)

        if delta <= timedelta(minutes=threshold_minutes):
            return {
                "online": True,
                "reason": "recent_activity",
                "threshold_minutes": threshold_minutes,
                "last_activity_minutes": minutes,
            }

        return {
            "online": False,
            "reason": "threshold_timeout",
            "threshold_minutes": threshold_minutes,
            "last_activity_minutes": minutes,
        }

    except Exception:
        logger.exception("⚠️ Device Status Resolver Error")

        return {
            "online": is_device_online(device.last_activity),
            "reason": "legacy_exception_fallback",
            "threshold_minutes": threshold_minutes,
            "last_activity_minutes": None,
        }


# ================================================================
# 🖥️ Company Biotime Devices API (READ ONLY — LIST)
# ================================================================

@login_required
def company_biotime_devices(request):

    company = resolve_company(request)
    if not company:
        return JsonResponse({
            "status": "error",
            "message": "Company context not found."
        }, status=403)

    devices_qs = (
        BiotimeDevice.objects
        .filter(company_name=company.name)
        .order_by("alias")
    )

    normalized = []
    total_users = 0

    for device in devices_qs:
        users = int(device.user_count or 0)
        total_users += users

        status_meta = resolve_device_status(device)

        # 🌍 Resolve Geo Location (Non-blocking)
        geo_location = build_location_text_from_ip(device.ip_address)

        normalized.append({
            "id": device.device_id,
            "name": device.alias,
            "sn": device.sn,
            "ip": device.ip_address,
            "location": device.area_name,      # 🔒 ثابت
            "geo_location": geo_location,      # 🌍 جديد

            # ✅ الحقل الأساسي محفوظ
            "status": "online" if status_meta["online"] else "offline",

            # 🧠 معلومات إضافية ذكية
            "status_reason": status_meta["reason"],
            "threshold_minutes": status_meta["threshold_minutes"],
            "last_activity_minutes": status_meta["last_activity_minutes"],

            "last_sync": device.last_sync,
            "last_activity": device.last_activity,
            "users": users,
        })

    return JsonResponse({
        "status": "success",
        "company": company.name,
        "count": len(normalized),
        "total_users": total_users,
        "devices": normalized,
    }, status=200)


# ================================================================
# 🔍 API — Device Details (Company Scoped)
# ================================================================

@login_required
def company_biotime_device_detail(request, device_id: int):

    company = resolve_company(request)
    if not company:
        return JsonResponse({
            "status": "error",
            "message": "Company context not found."
        }, status=403)

    device = (
        BiotimeDevice.objects
        .filter(
            device_id=device_id,
            company_name=company.name,
        )
        .first()
    )

    if not device:
        return JsonResponse({
            "status": "error",
            "message": "Device not found."
        }, status=404)

    status_meta = resolve_device_status(device)

    # 🌍 Resolve Geo Location (Non-blocking)
    geo_location = build_location_text_from_ip(device.ip_address)

    payload = {
        "id": device.device_id,
        "name": device.alias,
        "sn": device.sn,
        "ip": device.ip_address,
        "location": device.area_name,      # 🔒 ثابت
        "geo_location": geo_location,      # 🌍 جديد

        # ✅ لم يتغير
        "status": "online" if status_meta["online"] else "offline",

        # 🧠 إضافات
        "status_reason": status_meta["reason"],
        "threshold_minutes": status_meta["threshold_minutes"],
        "last_activity_minutes": status_meta["last_activity_minutes"],

        "last_sync": device.last_sync,
        "last_activity": device.last_activity,
        "users": int(device.user_count or 0),
    }

    return JsonResponse({
        "status": "success",
        "device": payload,
    }, status=200)


# ================================================================
# 🔄 API — Sync Devices From Biotime (GLOBAL)
# ================================================================

@csrf_exempt
@login_required
@require_POST
def company_biotime_sync_devices(request):

    start_time = timezone.now()

    try:
        company = resolve_company(request)
        if not company:
            return JsonResponse({
                "status": "error",
                "message": "Company context not found."
            }, status=403)

        client = get_biotime_client()
        devices_data = client.get_devices() or []

        if not devices_data:
            logger.error("❌ No devices returned from Biotime API")
            return JsonResponse({
                "status": "error",
                "message": "Failed to fetch devices from Biotime."
            }, status=502)

        synced = 0
        total_users = 0
        now = timezone.now()

        for raw in devices_data:
            try:
                device_id = raw.get("id")
                if not device_id:
                    continue

                area = raw.get("area") or {}
                users_count = int(raw.get("user_count") or 0)
                total_users += users_count

                BiotimeDevice.objects.update_or_create(
                    device_id=device_id,
                    defaults={
                        "sn": raw.get("sn"),
                        "alias": raw.get("alias") or raw.get("terminal_name"),
                        "terminal_name": raw.get("terminal_name"),
                        "ip_address": raw.get("ip_address"),
                        "firmware_version": raw.get("fw_ver"),
                        "push_ver": raw.get("push_ver"),
                        "state": raw.get("state", 0),
                        "terminal_tz": raw.get("terminal_tz"),

                        "area_id": area.get("id"),
                        "area_code": area.get("area_code"),
                        "area_name": area.get("area_name"),

                        "company_name": company.name,

                        "last_activity": raw.get("last_activity"),
                        "user_count": users_count,
                        "fp_count": raw.get("fp_count"),
                        "face_count": raw.get("face_count"),
                        "palm_count": raw.get("palm_count"),
                        "transaction_count": raw.get("transaction_count"),

                        "push_time": raw.get("push_time"),
                        "transfer_time": raw.get("transfer_time"),
                        "transfer_interval": raw.get("transfer_interval"),
                        "raw_json": raw,
                        "last_sync": now,
                    }
                )

                synced += 1

            except Exception as e:
                logger.exception(
                    f"❌ Device Sync Error (device_id={raw.get('id')}): {e}"
                )

        elapsed_ms = int(
            (timezone.now() - start_time).total_seconds() * 1000
        )

        return JsonResponse({
            "status": "success",
            "company": company.name,
            "synced": synced,
            "total_users": total_users,
            "elapsed_ms": elapsed_ms,
        }, status=200)

    except Exception as e:
        logger.exception("🔥 Biotime Sync Devices Fatal Error")

        return JsonResponse({
            "status": "error",
            "message": "Unexpected error while syncing devices.",
            "exception": str(e),
        }, status=500)


# ================================================================
# 🔄 API — Sync Single Device (Company Scoped)
# ================================================================

@csrf_exempt
@login_required
@require_POST
def company_biotime_sync_single_device(request, device_id: int):

    start_time = timezone.now()

    try:
        company = resolve_company(request)
        if not company:
            return JsonResponse({
                "status": "error",
                "message": "Company context not found."
            }, status=403)

        client = get_biotime_client()
        devices_data = client.get_devices() or []

        target = next(
            (d for d in devices_data if int(d.get("id", 0)) == int(device_id)),
            None
        )

        if not target:
            return JsonResponse({
                "status": "error",
                "message": "Device not found in Biotime cloud."
            }, status=404)

        area = target.get("area") or {}
        users_count = int(target.get("user_count") or 0)
        now = timezone.now()

        device, _ = BiotimeDevice.objects.update_or_create(
            device_id=device_id,
            defaults={
                "sn": target.get("sn"),
                "alias": target.get("alias") or target.get("terminal_name"),
                "terminal_name": target.get("terminal_name"),
                "ip_address": target.get("ip_address"),
                "firmware_version": target.get("fw_ver"),
                "push_ver": target.get("push_ver"),
                "state": target.get("state", 0),
                "terminal_tz": target.get("terminal_tz"),

                "area_id": area.get("id"),
                "area_code": area.get("area_code"),
                "area_name": area.get("area_name"),

                "company_name": company.name,

                "last_activity": target.get("last_activity"),
                "user_count": users_count,
                "fp_count": target.get("fp_count"),
                "face_count": target.get("face_count"),
                "palm_count": target.get("palm_count"),
                "transaction_count": target.get("transaction_count"),

                "push_time": target.get("push_time"),
                "transfer_time": target.get("transfer_time"),
                "transfer_interval": target.get("transfer_interval"),
                "raw_json": target,
                "last_sync": now,
            }
        )

        elapsed_ms = int(
            (timezone.now() - start_time).total_seconds() * 1000
        )

        status_meta = resolve_device_status(device)

        # 🌍 Resolve Geo Location (Non-blocking)
        geo_location = build_location_text_from_ip(device.ip_address)

        payload = {
            "id": device.device_id,
            "name": device.alias,
            "sn": device.sn,
            "ip": device.ip_address,
            "location": device.area_name,      # 🔒 ثابت
            "geo_location": geo_location,      # 🌍 جديد
            "status": "online" if status_meta["online"] else "offline",
            "status_reason": status_meta["reason"],
            "threshold_minutes": status_meta["threshold_minutes"],
            "last_activity_minutes": status_meta["last_activity_minutes"],
            "last_sync": device.last_sync,
            "last_activity": device.last_activity,
            "users": int(device.user_count or 0),
        }

        return JsonResponse({
            "status": "success",
            "device": payload,
            "elapsed_ms": elapsed_ms,
        }, status=200)

    except Exception as e:
        logger.exception("🔥 Biotime Single Device Sync Error")

        return JsonResponse({
            "status": "error",
            "message": "Failed to sync device.",
            "exception": str(e),
        }, status=500)


# ================================================================
# 🔌 API — Test Single Device (Company Scoped)
# ================================================================

@csrf_exempt
@login_required
@require_POST
def company_biotime_test_single_device(request, device_id: int):

    try:
        company = resolve_company(request)
        if not company:
            return JsonResponse({
                "status": "error",
                "message": "Company context not found."
            }, status=403)

        client = get_biotime_client()
        devices_data = client.get_devices() or []

        exists = any(
            int(d.get("id", 0)) == int(device_id)
            for d in devices_data
        )

        if not exists:
            return JsonResponse({
                "status": "error",
                "message": "Device not reachable in Biotime Cloud."
            }, status=404)

        return JsonResponse({
            "status": "success",
            "device_id": device_id,
            "reachable": True,
        }, status=200)

    except Exception as e:
        logger.exception("🔥 Device Test Connection Error")

        return JsonResponse({
            "status": "error",
            "message": "Failed to test device connection.",
            "exception": str(e),
        }, status=500)
