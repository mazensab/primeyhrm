# ============================================================
# 📂 api/company/whatsapp/settings.py
# 🏢 Company WhatsApp Settings APIs
# Primey HR Cloud
# ============================================================

from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse

from whatsapp_center.models import CompanyWhatsAppConfig, SessionStatus, WhatsAppProvider
from api.company.whatsapp.helpers import (
    json_bad_request,
    json_not_found,
    json_server_error,
    resolve_request_company,
)


def _json_success(message: str, **extra):
    payload = {"success": True, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=200)


def _mask_secret(value: str, keep_start: int = 6, keep_end: int = 4) -> str:
    value = (value or "").strip()
    if not value:
        return ""

    if len(value) <= (keep_start + keep_end):
        return "*" * len(value)

    return f"{value[:keep_start]}{'*' * (len(value) - keep_start - keep_end)}{value[-keep_end:]}"


def _build_company_session_name(company) -> str:
    company_id = getattr(company, "id", None) or "company"
    return f"primey-company-{company_id}-session"


@login_required
@require_GET
def company_whatsapp_settings(request):
    company = resolve_request_company(request)
    if not company:
        return json_not_found("No active company found")

    config, _ = CompanyWhatsAppConfig.objects.get_or_create(company=company)

    changed_fields = []

    if not (config.provider or "").strip():
        config.provider = WhatsAppProvider.WEB_SESSION
        changed_fields.append("provider")

    if not (config.session_name or "").strip():
        config.session_name = _build_company_session_name(company)
        changed_fields.append("session_name")

    if not (config.session_mode or "").strip():
        config.session_mode = "qr"
        changed_fields.append("session_mode")

    if changed_fields:
        changed_fields.append("updated_at")
        config.save(update_fields=changed_fields)

    return _json_success(
        "Company WhatsApp settings loaded successfully",
        config={
            "id": config.id,
            "company_id": company.id,
            "company_name": getattr(company, "name", "") or "",
            "provider": config.provider or WhatsAppProvider.WEB_SESSION,
            "is_enabled": bool(config.is_enabled),
            "is_active": bool(config.is_active),
            "display_name": config.display_name or "",
            "phone_number": config.phone_number or "",
            "phone_number_id": config.phone_number_id or "",
            "business_account_id": config.business_account_id or "",
            "app_id": config.app_id or "",
            "access_token_masked": _mask_secret(config.access_token or ""),
            "webhook_verify_token_masked": _mask_secret(config.webhook_verify_token or ""),
            "webhook_callback_url": config.webhook_callback_url or "",
            "webhook_verified": bool(config.webhook_verified),
            "default_language_code": config.default_language_code or "ar",
            "default_country_code": config.default_country_code or "966",
            "allow_templates": bool(config.allow_broadcasts),
            "send_test_enabled": bool(config.send_test_enabled),
            "default_test_recipient": config.default_test_recipient or "",
            "send_employee_alerts": bool(config.send_employee_alerts),
            "send_attendance_alerts": bool(config.send_attendance_alerts),
            "send_leave_alerts": bool(config.send_leave_alerts),
            "send_payroll_alerts": bool(config.send_payroll_alerts),
            "send_billing_alerts": bool(config.send_billing_alerts),
            "send_system_copy_alerts": bool(config.send_system_copy_alerts),
            "session_name": config.session_name or "",
            "session_mode": config.session_mode or "qr",
            "session_status": config.session_status or SessionStatus.DISCONNECTED,
            "session_connected_phone": config.session_connected_phone or "",
            "session_device_label": config.session_device_label or "",
            "session_qr_code": config.session_qr_code or "",
            "session_pairing_code": config.session_pairing_code or "",
            "session_last_connected_at": (
                config.session_last_connected_at.isoformat()
                if config.session_last_connected_at else None
            ),
            "last_health_check_at": (
                config.last_health_check_at.isoformat()
                if config.last_health_check_at else None
            ),
            "last_error_message": config.last_error_message or "",
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        },
    )


@login_required
@require_POST
def company_whatsapp_settings_update(request):
    company = resolve_request_company(request)
    if not company:
        return json_not_found("No active company found")

    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return json_bad_request("Invalid JSON payload")

    config, _ = CompanyWhatsAppConfig.objects.get_or_create(company=company)

    try:
        provider = (
            body.get("provider")
            or config.provider
            or WhatsAppProvider.WEB_SESSION
        ).strip()

        is_active = bool(body.get("is_active", config.is_active))
        is_enabled = bool(body.get("is_enabled", is_active))

        access_token = body.get("access_token")
        webhook_verify_token = body.get("webhook_verify_token")

        config.provider = provider
        config.is_active = is_active
        config.is_enabled = is_enabled
        config.display_name = (body.get("display_name", config.display_name) or "").strip()
        config.phone_number = (body.get("phone_number", config.phone_number) or "").strip()
        config.phone_number_id = (body.get("phone_number_id", config.phone_number_id) or "").strip()
        config.business_account_id = (
            body.get("business_account_id", config.business_account_id) or ""
        ).strip()
        config.app_id = (body.get("app_id", config.app_id) or "").strip()
        config.webhook_callback_url = (
            body.get("webhook_callback_url", config.webhook_callback_url) or ""
        ).strip()
        config.default_language_code = (
            body.get("default_language_code", config.default_language_code) or "ar"
        ).strip()
        config.default_country_code = (
            body.get("default_country_code", config.default_country_code) or "966"
        ).strip()

        config.allow_broadcasts = bool(body.get("allow_templates", config.allow_broadcasts))
        config.send_test_enabled = bool(body.get("send_test_enabled", config.send_test_enabled))
        config.default_test_recipient = (
            body.get("default_test_recipient", config.default_test_recipient) or ""
        ).strip()

        config.send_employee_alerts = bool(
            body.get("send_employee_alerts", config.send_employee_alerts)
        )
        config.send_attendance_alerts = bool(
            body.get("send_attendance_alerts", config.send_attendance_alerts)
        )
        config.send_leave_alerts = bool(
            body.get("send_leave_alerts", config.send_leave_alerts)
        )
        config.send_payroll_alerts = bool(
            body.get("send_payroll_alerts", config.send_payroll_alerts)
        )
        config.send_billing_alerts = bool(
            body.get("send_billing_alerts", config.send_billing_alerts)
        )
        config.send_system_copy_alerts = bool(
            body.get("send_system_copy_alerts", config.send_system_copy_alerts)
        )

        config.session_mode = (body.get("session_mode", config.session_mode) or "qr").strip()

        if isinstance(body.get("session_name"), str) and body.get("session_name", "").strip():
            config.session_name = body["session_name"].strip()
        elif not (config.session_name or "").strip():
            config.session_name = _build_company_session_name(company)

        if isinstance(access_token, str) and access_token.strip():
            config.access_token = access_token.strip()

        if isinstance(webhook_verify_token, str) and webhook_verify_token.strip():
            config.webhook_verify_token = webhook_verify_token.strip()

        config.save()

        return _json_success(
            "Company WhatsApp settings updated successfully",
            config={
                "id": config.id,
                "company_id": company.id,
                "company_name": getattr(company, "name", "") or "",
                "provider": config.provider,
                "is_enabled": bool(config.is_enabled),
                "is_active": bool(config.is_active),
                "phone_number_id": config.phone_number_id or "",
                "business_account_id": config.business_account_id or "",
                "webhook_callback_url": config.webhook_callback_url or "",
                "default_country_code": config.default_country_code or "966",
                "allow_templates": bool(config.allow_broadcasts),
                "send_test_enabled": bool(config.send_test_enabled),
                "default_test_recipient": config.default_test_recipient or "",
                "session_name": config.session_name or "",
                "session_mode": config.session_mode or "qr",
                "access_token_masked": _mask_secret(config.access_token or ""),
                "webhook_verify_token_masked": _mask_secret(config.webhook_verify_token or ""),
                "updated_at": config.updated_at.isoformat() if config.updated_at else None,
            },
        )
    except Exception as exc:
        return json_server_error(
            "Failed to update company WhatsApp settings",
            error=str(exc),
        )