# ============================================================
# 🔐 System Settings API — Update Endpoint
# Version: V2.1 Ultra Stable
# Primey HR Cloud | Super Admin
# ============================================================

import json

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from settings_center.services.system_settings import get_system_setting

from settings_center.services import update_system_setting


# ============================================================
# 🔐 Update System Setting (Super Admin Only)
# ============================================================

@csrf_exempt  # لأننا نستقبل JSON من Frontend (Next.js)
@require_POST
@login_required
def update_system_setting_api(request):
    """
    POST (JSON):
    {
        "field": "platform_active",
        "value": true
    }

    - Super Admin only
    - Audit Logged
    - Cache Cleared
    """

    # --------------------------------------------------------
    # 1) Parse JSON
    # --------------------------------------------------------
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid JSON payload",
            },
            status=400,
        )

    field = payload.get("field")
    value = payload.get("value")

    if field is None or value is None:
        return JsonResponse(
            {
                "status": "error",
                "message": "Missing field or value",
            },
            status=400,
        )

    # --------------------------------------------------------
    # 2) Normalize Boolean
    # --------------------------------------------------------
    if isinstance(value, bool):
        normalized_value = value
    else:
        normalized_value = str(value).lower() in ("1", "true", "yes", "on")

    # --------------------------------------------------------
    # 3) Execute Update via Service Layer
    # --------------------------------------------------------
    try:
        result = update_system_setting(
            user=request.user,
            field=field,
            value=normalized_value,
        )

        return JsonResponse(
            {
                "status": "success",
                "data": result,
            },
            status=200,
        )

    # --------------------------------------------------------
    # 4) Permission
    # --------------------------------------------------------
    except PermissionDenied:
        return JsonResponse(
            {
                "status": "forbidden",
                "message": "You are not allowed to modify system settings",
            },
            status=403,
        )

    # --------------------------------------------------------
    # 5) Business / Validation Errors
    # --------------------------------------------------------
    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "message": str(e),
            },
            status=400,
        )

# ============================================================
# 🌐 Get System Settings (Read Only)
# Used by Frontend (Next.js)
# ============================================================

from settings_center import services
from django.views.decorators.http import require_GET


@require_GET
@login_required
def system_settings_api(request):
    """
    GET /api/system/settings/

    - Global System Governance
    - Kill Switch
    - Maintenance Mode
    - Readonly Mode
    """

    system = get_system_setting()

    # --------------------------------------------------------
    # Fail-Safe Defaults (First Run)
    # --------------------------------------------------------
    if not system:
        return JsonResponse({
            "platform_active": True,
            "maintenance_mode": False,
            "readonly_mode": False,
            "billing_enabled": True,
            "modules": {
                "companies": True,
                "billing": True,
                "users": True,
                "devices": True,
                "health": True,
                "settings": True,
            },
        })

    return JsonResponse({
        "platform_active": getattr(system, "platform_active", True),
        "maintenance_mode": getattr(system, "maintenance_mode", False),
        "readonly_mode": getattr(system, "readonly_mode", False),
        "billing_enabled": getattr(system, "billing_enabled", True),
        "modules": getattr(system, "modules", {}) or {},
    })
