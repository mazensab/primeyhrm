# ============================================================
# 📂 api/company/whatsapp/status.py
# 🏢 Company WhatsApp Status + Session APIs
# Mham Cloud
# ============================================================

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST

from whatsapp_center.models import CompanyWhatsAppConfig, ScopeType, WhatsAppProvider
from whatsapp_center.services import (
    create_whatsapp_pairing_code_session,
    create_whatsapp_qr_session,
    disconnect_whatsapp_session,
    get_whatsapp_session_status,
)
from api.company.whatsapp.helpers import (
    clean_phone,
    get_model_attr,
    json_bad_request,
    json_not_found,
    json_ok,
    json_server_error,
    read_json_body,
    resolve_request_company,
)


# ============================================================
# 🔒 ثابت مزود الجلسة
# ============================================================

WEB_SESSION_PROVIDER = "whatsapp_web_session"
DEFAULT_SESSION_MODE = "qr"


# ============================================================
# 🔧 Internal Helpers
# ============================================================

def _get_company_config(company):
    config, _ = CompanyWhatsAppConfig.objects.get_or_create(
        company=company,
        defaults={
            "provider": WEB_SESSION_PROVIDER,
            "session_name": f"primey-company-{company.id}-session",
            "session_mode": DEFAULT_SESSION_MODE,
        },
    )
    return config


def _default_session_name(company) -> str:
    return f"primey-company-{company.id}-session"


def _session_name_from_body_or_config(body: dict, config, company) -> str:
    session_name = (
        body.get("session_name")
        or get_model_attr(config, "session_name", "")
        or _default_session_name(company)
    ).strip()
    return session_name or _default_session_name(company)


def _session_mode_from_body_or_config(body: dict, config) -> str:
    session_mode = (
        body.get("mode")
        or body.get("session_mode")
        or get_model_attr(config, "session_mode", "")
        or DEFAULT_SESSION_MODE
    ).strip()

    if session_mode not in {"qr", "pairing_code"}:
        return DEFAULT_SESSION_MODE

    return session_mode


def _update_config_fields_if_needed(config, **values) -> None:
    update_fields: list[str] = []

    for field_name, field_value in values.items():
        if hasattr(config, field_name):
            current_value = getattr(config, field_name, None)
            if current_value != field_value:
                setattr(config, field_name, field_value)
                update_fields.append(field_name)

    if update_fields:
        config.save(update_fields=update_fields)


def _ensure_web_session_config(
    config,
    *,
    company,
    session_name: str,
    session_mode: str,
    force_enabled: bool = False,
) -> None:
    values = {
        "provider": WEB_SESSION_PROVIDER,
        "session_name": session_name or _default_session_name(company),
        "session_mode": session_mode or DEFAULT_SESSION_MODE,
    }

    if force_enabled:
        values["is_enabled"] = True

    _update_config_fields_if_needed(config, **values)


def _extract_error_message(session_data: dict, default_message: str) -> str:
    return (
        session_data.get("error_message")
        or session_data.get("message")
        or session_data.get("details")
        or default_message
    )


def _build_base_payload(config, company) -> dict:
    return {
        "configured": True,
        "company_id": getattr(company, "id", None),
        "company_name": getattr(company, "name", "") or "",
        "is_enabled": bool(get_model_attr(config, "is_enabled", False)),
        "is_active": bool(get_model_attr(config, "is_active", False)),
        "provider": get_model_attr(config, "provider", WEB_SESSION_PROVIDER) or WEB_SESSION_PROVIDER,
        "phone_number": get_model_attr(config, "phone_number", "") or None,
        "phone_number_id": get_model_attr(config, "phone_number_id", "") or None,
        "business_account_id": get_model_attr(config, "business_account_id", "") or None,
        "last_check_at": (
            config.last_health_check_at.isoformat()
            if get_model_attr(config, "last_health_check_at", None)
            else None
        ),
        "last_error_message": get_model_attr(config, "last_error_message", "") or "",
        "webhook_verified": bool(get_model_attr(config, "webhook_verified", False)),
        "session_name": get_model_attr(config, "session_name", _default_session_name(company)) or _default_session_name(company),
        "session_mode": get_model_attr(config, "session_mode", DEFAULT_SESSION_MODE) or DEFAULT_SESSION_MODE,
        "session_status": get_model_attr(config, "session_status", "disconnected") or "disconnected",
        "connected": False,
        "qr_code": get_model_attr(config, "session_qr_code", "") or None,
        "pairing_code": get_model_attr(config, "session_pairing_code", "") or None,
        "connected_phone": get_model_attr(config, "session_connected_phone", "") or None,
        "last_connected_at": (
            config.session_last_connected_at.isoformat()
            if get_model_attr(config, "session_last_connected_at", None)
            else None
        ),
        "device_label": get_model_attr(config, "session_device_label", "") or None,
    }


# ============================================================
# 📡 Status API
# ============================================================

@login_required
@require_GET
def company_whatsapp_status(request):
    company = resolve_request_company(request)
    if not company:
        return json_not_found("No active company found")

    try:
        config = _get_company_config(company)

        _ensure_web_session_config(
            config,
            company=company,
            session_name=get_model_attr(config, "session_name", _default_session_name(company)) or _default_session_name(company),
            session_mode=get_model_attr(config, "session_mode", DEFAULT_SESSION_MODE) or DEFAULT_SESSION_MODE,
            force_enabled=False,
        )

        base_payload = _build_base_payload(config, company)
        provider = base_payload["provider"]

        if provider != WEB_SESSION_PROVIDER:
            return json_ok(
                "Company WhatsApp status loaded successfully",
                **base_payload,
            )

        if not base_payload["is_active"]:
            payload = dict(base_payload)
            payload["gateway_message"] = "WhatsApp is inactive"
            return json_ok(
                "Company WhatsApp status loaded successfully",
                **payload,
            )

        if not base_payload["is_enabled"]:
            _update_config_fields_if_needed(config, is_enabled=True)
            base_payload = _build_base_payload(config, company)

        session_data = get_whatsapp_session_status(
            scope_type=ScopeType.COMPANY,
            company=company,
        ) or {}

        payload = dict(base_payload)
        payload.update(
            {
                "provider": session_data.get("provider") or payload["provider"],
                "session_name": session_data.get("session_name") or payload["session_name"],
                "connected": bool(session_data.get("connected", False)),
                "session_status": session_data.get("session_status") or payload["session_status"],
                "qr_code": session_data.get("qr_code") or None,
                "pairing_code": session_data.get("pairing_code") or None,
                "connected_phone": session_data.get("connected_phone") or None,
                "last_connected_at": session_data.get("last_connected_at") or payload["last_connected_at"],
                "device_label": session_data.get("device_label") or None,
                "gateway_message": session_data.get("error_message", "") or session_data.get("message", ""),
            }
        )

        return json_ok(
            session_data.get("message") or "Company WhatsApp status loaded successfully",
            **payload,
        )

    except Exception as exc:
        return json_server_error(
            "Failed to load company WhatsApp status",
            details=str(exc),
            session_status="failed",
            connected=False,
        )


# ============================================================
# 📲 Create QR Session
# ============================================================

@login_required
@require_POST
def company_whatsapp_session_create_qr(request):
    company = resolve_request_company(request)
    if not company:
        return json_not_found("No active company found")

    config = _get_company_config(company)

    try:
        body = read_json_body(request)
    except ValueError as exc:
        return json_bad_request(str(exc))

    session_name = _session_name_from_body_or_config(body, config, company)
    session_mode = "qr"

    _ensure_web_session_config(
        config,
        company=company,
        session_name=session_name,
        session_mode=session_mode,
        force_enabled=True,
    )

    session_data = create_whatsapp_qr_session(
        scope_type=ScopeType.COMPANY,
        company=company,
    )

    if not session_data.get("success"):
        return json_bad_request(
            _extract_error_message(session_data, "Failed to create QR session"),
            session_name=session_name,
            session_mode=session_mode,
            session_status=session_data.get("session_status") or "failed",
        )

    return json_ok(
        session_data.get("message") or "QR session created successfully",
        session_name=session_data.get("session_name") or session_name,
        session_mode=session_mode,
        session_status=session_data.get("session_status") or "qr_pending",
        qr_code=session_data.get("qr_code"),
        pairing_code=session_data.get("pairing_code"),
        connected_phone=session_data.get("connected_phone"),
        device_label=session_data.get("device_label"),
        last_connected_at=session_data.get("last_connected_at"),
    )


# ============================================================
# 🔢 Create Pairing Code Session
# ============================================================

@login_required
@require_POST
def company_whatsapp_session_create_pairing_code(request):
    company = resolve_request_company(request)
    if not company:
        return json_not_found("No active company found")

    config = _get_company_config(company)

    try:
        body = read_json_body(request)
    except ValueError as exc:
        return json_bad_request(str(exc))

    session_name = _session_name_from_body_or_config(body, config, company)
    session_mode = "pairing_code"
    phone_number = clean_phone(body.get("phone_number"))

    if not phone_number:
        return json_bad_request("phone_number is required")

    _ensure_web_session_config(
        config,
        company=company,
        session_name=session_name,
        session_mode=session_mode,
        force_enabled=True,
    )

    session_data = create_whatsapp_pairing_code_session(
        scope_type=ScopeType.COMPANY,
        company=company,
        phone_number=phone_number,
    )

    if not session_data.get("success"):
        return json_bad_request(
            _extract_error_message(session_data, "Failed to create pairing code"),
            session_name=session_name,
            session_mode=session_mode,
            session_status=session_data.get("session_status") or "failed",
        )

    return json_ok(
        session_data.get("message") or "Pairing code created successfully",
        session_name=session_data.get("session_name") or session_name,
        session_mode=session_mode,
        session_status=session_data.get("session_status") or "pair_pending",
        qr_code=session_data.get("qr_code"),
        pairing_code=session_data.get("pairing_code"),
        connected_phone=session_data.get("connected_phone"),
        device_label=session_data.get("device_label"),
        last_connected_at=session_data.get("last_connected_at"),
    )


# ============================================================
# 🔌 Disconnect Session
# ============================================================

@login_required
@require_POST
def company_whatsapp_session_disconnect(request):
    company = resolve_request_company(request)
    if not company:
        return json_not_found("No active company found")

    config = _get_company_config(company)

    try:
        body = read_json_body(request)
    except ValueError as exc:
        return json_bad_request(str(exc))

    session_name = _session_name_from_body_or_config(body, config, company)
    session_mode = _session_mode_from_body_or_config(body, config)

    _ensure_web_session_config(
        config,
        company=company,
        session_name=session_name,
        session_mode=session_mode,
        force_enabled=True,
    )

    session_data = disconnect_whatsapp_session(
        scope_type=ScopeType.COMPANY,
        company=company,
    )

    if not session_data.get("success"):
        return json_bad_request(
            _extract_error_message(session_data, "Failed to disconnect session"),
            session_name=session_name,
            session_mode=session_mode,
            session_status=session_data.get("session_status") or "failed",
        )

    return json_ok(
        session_data.get("message") or "Session disconnected successfully",
        session_name=session_data.get("session_name") or session_name,
        session_mode=session_mode,
        session_status=session_data.get("session_status") or "disconnected",
        connected=bool(session_data.get("connected", False)),
        qr_code=session_data.get("qr_code"),
        pairing_code=session_data.get("pairing_code"),
        connected_phone=session_data.get("connected_phone"),
        device_label=session_data.get("device_label"),
        last_connected_at=session_data.get("last_connected_at"),
    )