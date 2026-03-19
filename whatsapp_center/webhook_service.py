# ============================================================
# 📂 whatsapp_center/webhook_service.py
# Primey HR Cloud - WhatsApp Webhook Service
# ============================================================

from django.utils import timezone

from .models import DeliveryStatus, WhatsAppMessageLog, WhatsAppWebhookEvent


def store_webhook_event(*, payload: dict, event_type: str = "", external_message_id: str = "", scope_type="SYSTEM", company=None, provider="META"):
    return WhatsAppWebhookEvent.objects.create(
        scope_type=scope_type,
        company=company,
        provider=provider,
        event_type=event_type,
        external_message_id=external_message_id,
        payload_json=payload or {},
    )


def apply_status_update_to_message(*, external_message_id: str, new_status: str):
    if not external_message_id:
        return None

    log = (
        WhatsAppMessageLog.objects
        .filter(external_message_id=external_message_id)
        .order_by("-id")
        .first()
    )
    if not log:
        return None

    status = (new_status or "").lower().strip()

    if status == "sent":
        log.delivery_status = DeliveryStatus.SENT
        if not log.sent_at:
            log.sent_at = timezone.now()

    elif status == "delivered":
        log.delivery_status = DeliveryStatus.DELIVERED
        if not log.delivered_at:
            log.delivered_at = timezone.now()

    elif status == "read":
        log.delivery_status = DeliveryStatus.READ
        if not log.read_at:
            log.read_at = timezone.now()

    elif status == "failed":
        log.delivery_status = DeliveryStatus.FAILED
        if not log.failed_at:
            log.failed_at = timezone.now()

    log.provider_status = new_status
    log.save()
    return log