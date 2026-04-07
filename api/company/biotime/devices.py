# ================================================================
# 📂 api/company/biotime/devices.py
# ⚙️ Version: V17.6 FINAL — PRODUCTION SAFE 🔒
# Mham Cloud
# ================================================================

import logging
from datetime import timedelta, datetime

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from biotime_center.models import BiotimeDevice, BiotimeSetting
from biotime_center.biotime_api_client import BiotimeAPIClient
from company_manager.models import CompanyUser
from biotime_center.sync_service import (
    create_or_sync_department,
    create_or_sync_jobtitle,
    create_or_sync_branch,
)
from company_manager.models import (
    CompanyDepartment,
    JobTitle,
    CompanyBranch,
)



# ================================================================
# 🌍 Geo Resolver (LIVE READ ONLY — NO STORAGE)
# ================================================================

import requests

def build_location_text_from_ip(ip_address: str | None):
    """
    🔹 Resolve Public IP to City + District (Live Only)
    🔹 No DB storage
    🔹 Safe Fail
    """

    if not ip_address:
        return None

    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip_address}",
            timeout=2,
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if data.get("status") != "success":
            return None

        city = data.get("city")
        region = data.get("regionName")

        if city and region:
            return f"{city} - {region}"

        if city:
            return city

        return None

    except Exception:
        logger.warning(f"Geo lookup failed for IP: {ip_address}")
        return None


# ================================================================
# 🔐 Helpers
# ================================================================

def resolve_company(request):
    company_user = (
        CompanyUser.objects
        .select_related("company")
        .filter(user=request.user, is_active=True, company__isnull=False)
        .order_by("-id")
        .first()
    )
    return company_user.company if company_user else None


def get_biotime_client(company):
    """
    إنشاء Biotime API Client بشكل آمن ومتوافق مع Multi-Company.
    """

    setting = (
        BiotimeSetting.objects
        .filter(company=company)
        .first()
    )

    if not setting:
        raise RuntimeError("Biotime settings not configured for company.")

    # ✅ Guard: منع التشغيل إذا الحساب مفصول
    if not setting.biotime_company:
        raise RuntimeError("Biotime account not connected for this company.")

    return BiotimeAPIClient(setting)

    # ✅ biotime_company REQUIRED
    return BiotimeAPIClient(setting)



# ================================================================
# 🧠 Legacy Online Resolver (DO NOT TOUCH)
# ================================================================

def is_device_online(last_activity, threshold_minutes=5):
    if not last_activity:
        return False
    try:
        return timezone.now() - last_activity <= timedelta(minutes=threshold_minutes)
    except Exception:
        return False


# ================================================================
# 🧩 Safe Datetime Parser
# ================================================================

def parse_biotime_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        value = str(value).replace("T", " ").split(".")[0]
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except Exception:
        logger.warning(f"Failed to parse Biotime datetime: {value}")
        return None


# ================================================================
# 🧠 Threshold Resolver
# ================================================================

def resolve_device_threshold(device: BiotimeDevice) -> int:
    if (device.face_count or 0) > 0:
        return 2
    if (device.palm_count or 0) > 0:
        return 2
    if (device.fp_count or 0) > 0:
        return 5
    return 10


# ================================================================
# 🟢 Device Status Engine
# ================================================================

def resolve_device_status(device: BiotimeDevice):
    threshold = resolve_device_threshold(device)
    try:
        dt = parse_biotime_datetime(device.last_activity)
        if not dt:
            return {
                "online": is_device_online(device.last_activity),
                "reason": "legacy_fallback",
                "threshold_minutes": threshold,
                "last_activity_minutes": None,
            }

        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)

        delta = timezone.now() - dt
        minutes = int(delta.total_seconds() / 60)

        return {
            "online": delta <= timedelta(minutes=threshold),
            "reason": "recent_activity" if delta <= timedelta(minutes=threshold) else "threshold_timeout",
            "threshold_minutes": threshold,
            "last_activity_minutes": minutes,
        }
    except Exception:
        logger.exception("Device status resolver error")
        return {
            "online": is_device_online(device.last_activity),
            "reason": "legacy_exception",
            "threshold_minutes": threshold,
            "last_activity_minutes": None,
        }


# ================================================================
# 🖥️ Devices List
# ================================================================

@login_required
def company_biotime_devices(request):
    company = resolve_company(request)
    if not company:
        return JsonResponse({"status": "error", "message": "Company context not found"}, status=403)

    devices = BiotimeDevice.objects.filter(company_name=company.name).order_by("alias")

    payload = []
    total_users = 0

    for d in devices:
        users = int(d.user_count or 0)
        total_users += users
        meta = resolve_device_status(d)

        payload.append({
            "id": d.device_id,
            "name": d.alias,
            "sn": d.sn,
            "ip": d.ip_address,
            "location": d.area_name,
            "geo_location": build_location_text_from_ip(d.ip_address),
            "status": "online" if meta["online"] else "offline",
            "status_reason": meta["reason"],
            "threshold_minutes": meta["threshold_minutes"],
            "last_activity_minutes": meta["last_activity_minutes"],
            "last_sync": d.last_sync,
            "last_activity": d.last_activity,
            "users": users,
        })

    return JsonResponse({
        "status": "success",
        "company": company.name,
        "count": len(payload),
        "total_users": total_users,
        "devices": payload,
    })


# ================================================================
# 🔍 Device Detail  ✅ (المفقودة سابقًا)
# ================================================================

@login_required
def company_biotime_device_detail(request, device_id: int):
    company = resolve_company(request)
    if not company:
        return JsonResponse({"status": "error", "message": "Company context not found"}, status=403)

    device = BiotimeDevice.objects.filter(
        device_id=device_id,
        company_name=company.name,
    ).first()

    if not device:
        return JsonResponse({"status": "error", "message": "Device not found"}, status=404)

    meta = resolve_device_status(device)

    return JsonResponse({
        "status": "success",
        "device": {
            "id": device.device_id,
            "name": device.alias,
            "sn": device.sn,
            "ip": device.ip_address,
            "location": device.area_name,
            "geo_location": build_location_text_from_ip(device.ip_address),
            "status": "online" if meta["online"] else "offline",
            "status_reason": meta["reason"],
            "threshold_minutes": meta["threshold_minutes"],
            "last_activity_minutes": meta["last_activity_minutes"],
            "last_sync": device.last_sync,
            "last_activity": device.last_activity,
            "users": int(device.user_count or 0),
        }
    })

def bootstrap_company_master_data(company):
    """
    Sync Company Master Data to Biotime:
    - Departments
    - Job Titles
    - Branches
    """

    # 🔹 Departments
    for dept in CompanyDepartment.objects.filter(company=company, is_active=True):
        create_or_sync_department(dept)

    # 🔹 Job Titles
    for job in JobTitle.objects.filter(company=company, is_active=True):
        create_or_sync_jobtitle(job)

    # 🔹 Branches
    for branch in CompanyBranch.objects.filter(company=company, is_active=True):
        create_or_sync_branch(branch)

# ================================================================
# 🔄 Sync Devices
# ================================================================
from biotime_center.sync_service import sync_devices

@csrf_exempt
@login_required
@require_POST
def company_biotime_sync_devices(request):

    company = resolve_company(request)
    if not company:
        return JsonResponse(
            {"status": "error", "message": "Company context not found"},
            status=403
        )

    # ✅ 1) Master Data Sync
    bootstrap_company_master_data(company)

    # ✅ 2) Devices Sync
    result = sync_devices(company=company)

    if result.get("status") != "success":
        return JsonResponse(result, status=500)

    return JsonResponse(result)

# ================================================================
# 🔄 Sync Single Device
# ================================================================

@csrf_exempt
@login_required
@require_POST
def company_biotime_sync_single_device(request, device_id: int):
    company = resolve_company(request)
    if not company:
        return JsonResponse({"status": "error", "message": "Company context not found"}, status=403)

    client = get_biotime_client(company)
    devices = client.get_devices() or []

    target = next((d for d in devices if int(d.get("id", 0)) == int(device_id)), None)
    if not target:
        return JsonResponse({"status": "error", "message": "Device not found in Biotime"}, status=404)

    area = target.get("area") or {}
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
            "user_count": int(target.get("user_count") or 0),
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

    return JsonResponse({"status": "success", "device_id": device.device_id})

# ================================================================
# 🔌 Reset Biotime Connection (FINAL FIX)
# ================================================================

@csrf_exempt
@login_required
@require_POST
def company_biotime_reset_connection(request):

    try:
        company = resolve_company(request)

        if not company:
            return JsonResponse(
                {"status": "error", "message": "Company context not found"},
                status=403
            )

        setting = (
            BiotimeSetting.objects
            .filter(company=company)
            .first()
        )

        if not setting:
            return JsonResponse({"status": "success"})

        # ✅ IMPORTANT FIX
        setting.biotime_company = ""

        # تنظيف التوكنات إن وجدت
        for field in [
            "api_token",
            "jwt_token",
            "session_token",
            "access_token",
            "refresh_token",
        ]:
            if hasattr(setting, field):
                setattr(setting, field, None)

        setting.save()

        return JsonResponse({
            "status": "success",
            "message": "Biotime connection reset successfully."
        })

    except Exception as e:
        logger.exception("Biotime reset connection error")

        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

# ================================================================
# 🔌 Test Single Device
# ================================================================

@csrf_exempt
@login_required
@require_POST
def company_biotime_test_single_device(request, device_id: int):
    company = resolve_company(request)
    if not company:
        return JsonResponse({"status": "error", "message": "Company context not found"}, status=403)

    client = get_biotime_client(company)
    devices = client.get_devices() or []

    exists = any(int(d.get("id", 0)) == int(device_id) for d in devices)

    if not exists:
        return JsonResponse({"status": "error", "message": "Device not reachable"}, status=404)

    return JsonResponse({"status": "success", "device_id": device_id, "reachable": True})
