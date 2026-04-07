# ============================================================
# 📂 api/company/whatsapp/send_test.py
# 🏢 Company WhatsApp Test Send API
# Mham Cloud
# ============================================================

from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from whatsapp_center.models import ScopeType, TriggerSource
from whatsapp_center.services import send_event_whatsapp_message
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


@login_required
@require_POST
def company_whatsapp_send_test(request):
    company = resolve_request_company(request)
    if not company:
        return json_not_found("No active company found")

    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return json_bad_request("Invalid JSON payload")

    recipient_phone = (
        body.get("recipient_phone")
        or body.get("phone_number")
        or body.get("test_phone")
        or ""
    ).strip()

    recipient_name = (body.get("recipient_name") or "").strip()
    custom_message = (body.get("message") or "").strip()

    if not recipient_phone:
        return json_bad_request("recipient_phone is required")

    try:
        log = send_event_whatsapp_message(
            scope_type=ScopeType.COMPANY,
            trigger_source=TriggerSource.BROADCAST,
            event_code="company_test_message",
            recipient_phone=recipient_phone,
            recipient_name=recipient_name,
            company=company,
            context={
                "company_name": getattr(company, "name", "") or "",
                "recipient_name": recipient_name or "User",
                "message": custom_message or (
                    "This is a company WhatsApp test message from Mham Cloud."
                ),
            },
            related_model="Company",
            related_object_id=str(getattr(company, "id", "")),
        )

        return _json_success(
            "Company WhatsApp test message processed",
            data={
                "log_id": log.id,
                "delivery_status": log.delivery_status,
                "provider_status": log.provider_status,
                "failure_reason": log.failure_reason,
                "recipient_phone": recipient_phone,
                "company_id": getattr(company, "id", None),
                "company_name": getattr(company, "name", "") or "",
            },
        )
    except Exception as exc:
        return json_server_error(
            "Failed to process company WhatsApp test message",
            error=str(exc),
        )