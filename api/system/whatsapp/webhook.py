# ============================================================
# 📂 api/system/whatsapp/webhook.py
# 🛡 System WhatsApp Webhook API
# Primey HR Cloud
# ============================================================

from __future__ import annotations

import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from whatsapp_center.webhook_service import apply_status_update_to_message, store_webhook_event


@require_GET
def system_whatsapp_webhook_verify(request):
    verify_token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")

    # TODO:
    # لاحقًا نقارن مع التوكن المحفوظ في SystemWhatsAppConfig
    if verify_token:
        return HttpResponse(challenge or "OK")

    return HttpResponse("Missing verify token", status=400)


@csrf_exempt
@require_POST
def system_whatsapp_webhook_receive(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "message": "Invalid JSON"}, status=400)

    store_webhook_event(
        payload=payload,
        event_type="provider_webhook",
        external_message_id="",
        scope_type="SYSTEM",
        company=None,
        provider="META",
    )

    # Placeholder parsing
    # لاحقًا نقرأ statuses من payload الرسمي لمزود واتساب
    try:
        statuses = payload.get("statuses", []) or []
        for status_item in statuses:
            external_message_id = status_item.get("id") or ""
            new_status = status_item.get("status") or ""
            if external_message_id and new_status:
                apply_status_update_to_message(
                    external_message_id=external_message_id,
                    new_status=new_status,
                )
    except Exception:
        pass

    return JsonResponse({"ok": True, "message": "Webhook received"}, status=200)