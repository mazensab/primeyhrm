# ============================================================
# 📂 api/system/whatsapp/settings.py
# 🛡 System WhatsApp Settings APIs
# Primey HR Cloud
# ============================================================

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from whatsapp_center.models import SystemWhatsAppConfig
from api.system.whatsapp.helpers import (
    bool_or_default,
    get_model_attr,
    json_bad_request,
    json_ok,
    json_server_error,
    mask_secret,
    read_json_body,
    set_model_attr_if_exists,
)


def _serialize_config(config: SystemWhatsAppConfig) -> dict:
    webhook_callback_url = get_model_attr(config, "webhook_callback_url", "") or ""

    return {
        "id": config.id,
        "provider": get_model_attr(config, "provider", "whatsapp_web_session") or "whatsapp_web_session",
        "is_enabled": bool(get_model_attr(config, "is_enabled", False)),
        "is_active": bool(get_model_attr(config, "is_active", False)),
        "app_name": get_model_attr(config, "business_name", "") or "Primey HR Cloud",
        "business_name": get_model_attr(config, "business_name", "") or "Primey HR Cloud",
        "phone_number": get_model_attr(config, "phone_number", "") or "",
        "phone_number_id": get_model_attr(config, "phone_number_id", "") or "",
        "business_account_id": get_model_attr(config, "business_account_id", "") or "",
        "app_id": get_model_attr(config, "app_id", "") or "",
        "api_version": get_model_attr(config, "api_version", "v22.0") or "v22.0",
        "default_language_code": get_model_attr(config, "default_language_code", "ar") or "ar",
        "default_country_code": get_model_attr(config, "default_country_code", "966") or "966",
        "allow_broadcasts": bool(get_model_attr(config, "allow_broadcasts", True)),
        "send_test_enabled": bool(get_model_attr(config, "send_test_enabled", True)),
        "default_test_recipient": get_model_attr(config, "default_test_recipient", "") or "",
        "webhook_callback_url": webhook_callback_url,
        "webhook_verify_token": "",
        "webhook_verify_token_masked": mask_secret(get_model_attr(config, "webhook_verify_token", "") or ""),
        "access_token": "",
        "access_token_masked": mask_secret(get_model_attr(config, "access_token", "") or ""),
        # ----------------------------------------------------
        # Session Settings
        # ----------------------------------------------------
        "session_name": get_model_attr(config, "session_name", "primey-system-session") or "primey-system-session",
        "session_mode": get_model_attr(config, "session_mode", "qr") or "qr",
        "session_status": get_model_attr(config, "session_status", "disconnected") or "disconnected",
        "session_connected_phone": get_model_attr(config, "session_connected_phone", "") or "",
        "session_device_label": get_model_attr(config, "session_device_label", "") or "",
        "session_qr_code": get_model_attr(config, "session_qr_code", "") or "",
        "session_pairing_code": get_model_attr(config, "session_pairing_code", "") or "",
        "session_last_connected_at": (
            config.session_last_connected_at.isoformat()
            if get_model_attr(config, "session_last_connected_at", None)
            else None
        ),
        "last_health_check_at": (
            config.last_health_check_at.isoformat()
            if get_model_attr(config, "last_health_check_at", None)
            else None
        ),
        "last_error_message": get_model_attr(config, "last_error_message", "") or "",
        "created_at": config.created_at.isoformat() if getattr(config, "created_at", None) else None,
        "updated_at": config.updated_at.isoformat() if getattr(config, "updated_at", None) else None,
    }


def _apply_config_update(config: SystemWhatsAppConfig, body: dict) -> None:
    # --------------------------------------------------------
    # Basic Activation
    # --------------------------------------------------------
    set_model_attr_if_exists(
        config,
        "provider",
        body.get("provider", get_model_attr(config, "provider", "whatsapp_web_session")),
    )
    set_model_attr_if_exists(
        config,
        "is_enabled",
        bool_or_default(body.get("is_enabled"), get_model_attr(config, "is_enabled", True)),
    )
    set_model_attr_if_exists(
        config,
        "is_active",
        bool_or_default(body.get("is_active"), get_model_attr(config, "is_active", False)),
    )

    # --------------------------------------------------------
    # App / Business Info
    # --------------------------------------------------------
    app_name = (body.get("app_name") or body.get("business_name") or "").strip()
    if app_name:
        set_model_attr_if_exists(config, "business_name", app_name)

    phone_number = (body.get("phone_number") or "").strip()
    if phone_number:
        set_model_attr_if_exists(config, "phone_number", phone_number)

    phone_number_id = (body.get("phone_number_id") or "").strip()
    if phone_number_id:
        set_model_attr_if_exists(config, "phone_number_id", phone_number_id)

    business_account_id = (body.get("business_account_id") or "").strip()
    if business_account_id:
        set_model_attr_if_exists(config, "business_account_id", business_account_id)

    app_id = (body.get("app_id") or "").strip()
    if app_id:
        set_model_attr_if_exists(config, "app_id", app_id)

    # --------------------------------------------------------
    # Tokens / Webhook
    # --------------------------------------------------------
    access_token = (body.get("access_token") or "").strip()
    if access_token:
        set_model_attr_if_exists(config, "access_token", access_token)

    webhook_verify_token = (body.get("webhook_verify_token") or "").strip()
    if webhook_verify_token:
        set_model_attr_if_exists(config, "webhook_verify_token", webhook_verify_token)

    webhook_callback_url = (body.get("webhook_callback_url") or "").strip()
    if webhook_callback_url:
        set_model_attr_if_exists(config, "webhook_callback_url", webhook_callback_url)

    # --------------------------------------------------------
    # Technical Defaults
    # --------------------------------------------------------
    api_version = (body.get("api_version") or "").strip()
    if api_version:
        set_model_attr_if_exists(config, "api_version", api_version)

    default_language_code = (body.get("default_language_code") or "").strip()
    if default_language_code:
        set_model_attr_if_exists(config, "default_language_code", default_language_code)

    default_country_code = (body.get("default_country_code") or "").strip()
    if default_country_code:
        set_model_attr_if_exists(config, "default_country_code", default_country_code)

    # --------------------------------------------------------
    # Feature Flags
    # --------------------------------------------------------
    if "allow_broadcasts" in body:
        set_model_attr_if_exists(config, "allow_broadcasts", bool(body.get("allow_broadcasts")))

    if "send_test_enabled" in body:
        set_model_attr_if_exists(config, "send_test_enabled", bool(body.get("send_test_enabled")))

    default_test_recipient = (body.get("default_test_recipient") or "").strip()
    if default_test_recipient:
        set_model_attr_if_exists(config, "default_test_recipient", default_test_recipient)

    # --------------------------------------------------------
    # Session Settings
    # --------------------------------------------------------
    session_name = (body.get("session_name") or "").strip()
    if session_name:
        set_model_attr_if_exists(config, "session_name", session_name)

    session_mode = (body.get("session_mode") or "").strip()
    if session_mode:
        set_model_attr_if_exists(config, "session_mode", session_mode)

    # --------------------------------------------------------
    # Optional direct session fields update
    # لا نعتمد عليها عادة من الواجهة، لكنها مفيدة للتوافق
    # أو لتحديثات داخلية عند الحاجة
    # --------------------------------------------------------
    if "session_status" in body:
        set_model_attr_if_exists(config, "session_status", (body.get("session_status") or "").strip() or "disconnected")

    if "session_connected_phone" in body:
        set_model_attr_if_exists(config, "session_connected_phone", (body.get("session_connected_phone") or "").strip())

    if "session_device_label" in body:
        set_model_attr_if_exists(config, "session_device_label", (body.get("session_device_label") or "").strip())

    if "session_qr_code" in body:
        set_model_attr_if_exists(config, "session_qr_code", body.get("session_qr_code") or "")

    if "session_pairing_code" in body:
        set_model_attr_if_exists(config, "session_pairing_code", (body.get("session_pairing_code") or "").strip())


@login_required
@require_http_methods(["GET", "POST"])
def system_whatsapp_settings(request):
    config, _ = SystemWhatsAppConfig.objects.get_or_create(id=1)

    if request.method == "GET":
        return json_ok(
            "System WhatsApp settings loaded successfully",
            config=_serialize_config(config),
        )

    try:
        body = read_json_body(request)
    except ValueError as exc:
        return json_bad_request(str(exc))

    try:
        _apply_config_update(config, body)
        config.save()

        return json_ok(
            "System WhatsApp settings updated successfully",
            config=_serialize_config(config),
        )
    except Exception as exc:
        return json_server_error(
            "Failed to update system WhatsApp settings",
            error=str(exc),
        )


@login_required
@require_http_methods(["POST"])
def system_whatsapp_settings_update(request):
    """
    مسار إضافي للتوافق الخلفي إذا كان أي جزء قديم من النظام
    ما زال يرسل إلى /settings/update/
    """
    return system_whatsapp_settings(request)