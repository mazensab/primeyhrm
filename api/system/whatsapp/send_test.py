# ============================================================
# 📂 api/system/whatsapp/send_test.py
# 🛡 System WhatsApp Test Send API
# Mham Cloud
# ============================================================

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from whatsapp_center.models import ScopeType, TriggerSource
from whatsapp_center.services import send_event_whatsapp_message
from api.system.whatsapp.helpers import clean_phone, json_bad_request, json_ok, read_json_body


@login_required
@require_POST
def system_whatsapp_send_test(request):
    try:
        body = read_json_body(request)
    except ValueError as exc:
        return json_bad_request(str(exc))

    recipient_phone = clean_phone(
        body.get("phone_number")
        or body.get("recipient_phone")
        or ""
    )
    recipient_name = (body.get("recipient_name") or "User").strip()
    message = (body.get("message") or "This is a system WhatsApp test message from Mham Cloud.").strip()

    if not recipient_phone:
        return json_bad_request("phone_number is required")

    log = send_event_whatsapp_message(
        scope_type=ScopeType.SYSTEM,
        trigger_source=TriggerSource.BROADCAST,
        event_code="system_test_message",
        recipient_phone=recipient_phone,
        recipient_name=recipient_name,
        context={
            "recipient_name": recipient_name,
            "message": message,
        },
        related_model="SystemWhatsAppConfig",
        related_object_id="1",
    )

    return json_ok(
        "System WhatsApp test message processed",
        data={
            "log_id": log.id,
            "delivery_status": log.delivery_status,
            "provider_status": log.provider_status,
            "failure_reason": log.failure_reason,
            "recipient_phone": recipient_phone,
        },
    )