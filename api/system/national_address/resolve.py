# ============================================================================
# 🇸🇦 Saudi National Address — Resolve Short Address API
# Primey HR Cloud | System Layer
# Version: V1.1 Ultra Stable (CACHE ENABLED)
# ============================================================================
# ✔ Secure proxy to api.address.gov.sa
# ✔ Short Address → Full National Address
# ✔ Auto cache City / District / Street (System Level)
# ✔ Timeout + Validation + Safe errors
# ✔ NO direct frontend exposure
# ============================================================================

import json
import requests

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.conf import settings

from settings_center.services.national_address_cache import cache_address


# ============================================================================
# 🔐 Configuration (OFFICIAL)
# ============================================================================
NATIONAL_ADDRESS_BASE_URL = "https://api.address.gov.sa"
RESOLVE_ENDPOINT = "/api/v3.1/Address/address-by-short-address"

DEFAULT_TIMEOUT = 8  # seconds


# ============================================================================
# 🧠 Helpers
# ============================================================================
def _json_payload(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


def _error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def _get_api_key():
    """
    🔐 API Key must be stored in settings:
    NATIONAL_ADDRESS_API_KEY = "xxxx"
    """
    return getattr(settings, "NATIONAL_ADDRESS_API_KEY", None)


# ============================================================================
# 🚀 API — Resolve Short Address
# URL: POST /api/system/national_address/resolve/
# ============================================================================
@login_required
@require_POST
def resolve_short_address(request):
    """
    Input:
    {
        "short_address": "RDKD1234"
    }

    Output:
    {
        building_no,
        street,
        district,
        city,
        postal_code,
        additional_code,
        latitude,
        longitude,
        raw
    }
    """

    payload = _json_payload(request)
    if not payload:
        return _error("Invalid JSON payload")

    short_address = payload.get("short_address")
    if not short_address:
        return _error("short_address مطلوب")

    api_key = _get_api_key()
    if not api_key:
        return _error("National Address API key not configured", status=500)

    # ------------------------------------------------------------------
    # 🔗 External API Call (OFFICIAL CONTRACT)
    # ------------------------------------------------------------------
    try:
        response = requests.get(
            NATIONAL_ADDRESS_BASE_URL + RESOLVE_ENDPOINT,
            params={"shortAddress": short_address.strip()},
            headers={
                "api_key": api_key,
                "Accept": "application/json",
            },
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        return _error("National Address service timeout", status=504)
    except requests.exceptions.RequestException:
        return _error("Failed to connect to National Address service", status=502)

    if response.status_code != 200:
        return _error("Invalid response from National Address service", status=502)

    try:
        data = response.json()
    except ValueError:
        return _error("Invalid JSON from National Address service", status=502)

    addresses = data.get("Addresses") or []
    if not addresses:
        return _error("لم يتم العثور على عنوان مطابق")

    # ------------------------------------------------------------------
    # 📦 Normalize First Result (Single Source of Truth)
    # ------------------------------------------------------------------
    addr = addresses[0]

    result = {
        "building_no": addr.get("BuildingNumber"),
        "street": addr.get("Street"),
        "district": addr.get("District"),
        "city": addr.get("City"),
        "postal_code": addr.get("PostCode"),
        "additional_code": addr.get("AdditionalNumber"),
        "latitude": addr.get("Latitude"),
        "longitude": addr.get("Longitude"),

        # 🔎 Keep raw for auditing / debugging
        "raw": addr,
    }

    # ------------------------------------------------------------------
    # 🧠 Cache City / District / Street (NON-BLOCKING)
    # ------------------------------------------------------------------
    try:
        cache_address(
            city_name=result.get("city"),
            district_name=result.get("district"),
            street_name=result.get("street"),
        )
    except Exception:
        # ❗ لا نكسر التجربة أبداً بسبب الكاش
        pass

    return JsonResponse(result, status=200)
