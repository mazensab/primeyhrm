# ============================================================
# 📂 api/system/settings.py
# ⚙️ Primey HR Cloud — System + Email Settings API
# Version: V3.0 Ultra Stable
# ============================================================

import json

from django.conf import settings as django_settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage, get_connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from settings_center.models import SettingsEmail
from settings_center.services.system_settings import (
    get_system_setting,
    update_system_setting,
)


# ============================================================
# 🧩 Helpers
# ============================================================

GENERAL_BOOL_FIELDS = {
    "platform_active",
    "maintenance_mode",
    "readonly_mode",
    "billing_enabled",
}

EMAIL_BOOL_FIELDS = {
    "use_tls",
}

EMAIL_ALLOWED_FIELDS = {
    "smtp_server",
    "smtp_port",
    "use_tls",
    "username",
    "password",
}


def _json_payload(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


def _to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _serialize_general_settings():
    system = get_system_setting()

    if not system:
        return {
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
        }

    return {
        "platform_active": getattr(system, "platform_active", True),
        "maintenance_mode": getattr(system, "maintenance_mode", False),
        "readonly_mode": getattr(system, "readonly_mode", False),
        "billing_enabled": getattr(system, "billing_enabled", True),
        "modules": getattr(system, "modules", {}) or {
            "companies": True,
            "billing": True,
            "users": True,
            "devices": True,
            "health": True,
            "settings": True,
        },
    }


def _serialize_email_settings():
    email_cfg = SettingsEmail.get_settings()

    smtp_server = (email_cfg.smtp_server or "").strip() or getattr(
        django_settings, "EMAIL_HOST", ""
    )
    smtp_port = email_cfg.smtp_port or getattr(django_settings, "EMAIL_PORT", 587)
    use_tls = bool(
        email_cfg.use_tls
        if email_cfg.pk
        else getattr(django_settings, "EMAIL_USE_TLS", True)
    )
    username = (email_cfg.username or "").strip() or getattr(
        django_settings, "EMAIL_HOST_USER", ""
    )
    password = (email_cfg.password or "").strip() or getattr(
        django_settings, "EMAIL_HOST_PASSWORD", ""
    )
    from_email = username or getattr(django_settings, "DEFAULT_FROM_EMAIL", "")

    is_ready = bool(smtp_server and smtp_port and username and password)

    return {
        "smtp_server": smtp_server,
        "smtp_port": smtp_port,
        "use_tls": use_tls,
        "username": username,
        "password": password,
        "password_masked": "•" * 10 if password else "",
        "from_email": from_email,
        "is_ready": is_ready,
        "status": "ready" if is_ready else "incomplete",
        "updated_at": email_cfg.updated_at.isoformat() if email_cfg.updated_at else None,
    }


# ============================================================
# 🌐 GET /api/system/settings/
# ============================================================

@require_GET
@login_required
def system_settings_api(request):
    general_payload = _serialize_general_settings()
    email_payload = _serialize_email_settings()

    return JsonResponse({
        **general_payload,
        "email": email_payload,
    })


# ============================================================
# 💾 POST /api/system/settings/update/
# ============================================================

@require_POST
@login_required
def update_system_setting_api(request):
    payload = _json_payload(request)

    if not payload:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid JSON payload",
            },
            status=400,
        )

    section = (payload.get("section") or "general").strip().lower()
    field = payload.get("field")
    value = payload.get("value")

    if not field:
        return JsonResponse(
            {
                "status": "error",
                "message": "Missing field",
            },
            status=400,
        )

    try:
        # ----------------------------------------------------
        # 🟦 General Settings
        # ----------------------------------------------------
        if section == "general":
            if field not in GENERAL_BOOL_FIELDS:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Invalid general field",
                    },
                    status=400,
                )

            normalized_value = _to_bool(value)

            result_obj = update_system_setting(
                section="general",
                field=field,
                value=normalized_value,
                user=request.user,
                company=None,
                ip_address=_get_client_ip(request),
            )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "System setting updated successfully",
                    "data": {
                        "section": "general",
                        "field": field,
                        "value": getattr(result_obj, field),
                    },
                },
                status=200,
            )

        # ----------------------------------------------------
        # 📧 Email Settings
        # ----------------------------------------------------
        if section == "email":
            if field not in EMAIL_ALLOWED_FIELDS:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Invalid email field",
                    },
                    status=400,
                )

            if field in EMAIL_BOOL_FIELDS:
                normalized_value = _to_bool(value)
            elif field == "smtp_port":
                try:
                    normalized_value = int(value)
                except Exception:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "SMTP port must be a valid number",
                        },
                        status=400,
                    )

                if normalized_value <= 0 or normalized_value > 65535:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "SMTP port must be between 1 and 65535",
                        },
                        status=400,
                    )
            else:
                normalized_value = str(value or "").strip()

            result_obj = update_system_setting(
                section="email",
                field=field,
                value=normalized_value,
                user=request.user,
                company=None,
                ip_address=_get_client_ip(request),
            )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Email setting updated successfully",
                    "data": {
                        "section": "email",
                        "field": field,
                        "value": getattr(result_obj, field),
                    },
                    "email": _serialize_email_settings(),
                },
                status=200,
            )

        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid settings section",
            },
            status=400,
        )

    except PermissionDenied:
        return JsonResponse(
            {
                "status": "forbidden",
                "message": "You are not allowed to modify system settings",
            },
            status=403,
        )

    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "message": str(e),
            },
            status=400,
        )


# ============================================================
# 🧪 POST /api/system/settings/email/test/
# ============================================================

@require_POST
@login_required
def test_email_settings_api(request):
    payload = _json_payload(request) or {}

    recipient = (
        payload.get("to")
        or payload.get("email")
        or request.user.email
        or _serialize_email_settings().get("username")
    )

    if not recipient:
        return JsonResponse(
            {
                "status": "error",
                "message": "No recipient email available for test",
            },
            status=400,
        )

    email_cfg = _serialize_email_settings()

    if not email_cfg["is_ready"]:
        return JsonResponse(
            {
                "status": "error",
                "message": "Email settings are incomplete",
            },
            status=400,
        )

    try:
        connection = get_connection(
            host=email_cfg["smtp_server"],
            port=int(email_cfg["smtp_port"]),
            username=email_cfg["username"],
            password=email_cfg["password"],
            use_tls=bool(email_cfg["use_tls"]),
            fail_silently=False,
        )

        message = EmailMessage(
            subject="Primey HR Cloud — Test Email",
            body=(
                "تم إرسال رسالة الاختبار بنجاح من إعدادات البريد داخل Primey HR Cloud.\n\n"
                f"SMTP Host: {email_cfg['smtp_server']}\n"
                f"Port: {email_cfg['smtp_port']}\n"
                f"TLS: {'Enabled' if email_cfg['use_tls'] else 'Disabled'}\n"
                f"Username: {email_cfg['username']}\n"
            ),
            from_email=email_cfg["from_email"],
            to=[recipient],
            connection=connection,
        )
        message.send(fail_silently=False)

        return JsonResponse(
            {
                "status": "success",
                "message": f"Test email sent successfully to {recipient}",
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "message": str(e),
            },
            status=400,
        )