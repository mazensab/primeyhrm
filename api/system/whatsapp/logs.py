# ============================================================
# 📂 api/system/whatsapp/logs.py
# 🛡 System WhatsApp Logs API
# Mham Cloud
# ============================================================

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from whatsapp_center.models import ScopeType, WhatsAppMessageLog
from api.system.whatsapp.helpers import json_ok


@login_required
@require_GET
def system_whatsapp_logs(request):
    logs = (
        WhatsAppMessageLog.objects
        .filter(scope_type=ScopeType.SYSTEM)
        .select_related("template", "company")
        .order_by("-created_at")[:200]
    )

    results = []
    for log in logs:
        results.append({
            "id": log.id,

            # ----------------------------------------------------
            # ✅ مفاتيح أساسية متوافقة مع الفرونت الحالي
            # ----------------------------------------------------
            "status": log.delivery_status,
            "direction": "OUTBOUND",
            "message_type": log.message_type,
            "recipient_phone": log.recipient_phone,
            "template_name": log.template_name_snapshot or (
                getattr(log.template, "template_name", "") if log.template else ""
            ),
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "provider_message_id": log.external_message_id or "",
            "error_message": log.failure_reason or "",
            "company_name": getattr(log.company, "name", "") if log.company else "",
            "payload_summary": log.message_body or "",

            # ----------------------------------------------------
            # ✅ مفاتيح إضافية مفيدة للتوسعة لاحقًا
            # ----------------------------------------------------
            "scope_type": log.scope_type,
            "company_id": log.company_id,
            "event_code": log.event_code,
            "trigger_source": log.trigger_source,
            "recipient_name": log.recipient_name,
            "delivery_status": log.delivery_status,
            "provider_status": log.provider_status,
            "failure_reason": log.failure_reason,
            "message_body": log.message_body,
            "header_text": getattr(log, "header_text", ""),
            "footer_text": getattr(log, "footer_text", ""),
            "attachment_url": getattr(log, "attachment_url", ""),
            "attachment_name": getattr(log, "attachment_name", ""),
            "mime_type": getattr(log, "mime_type", ""),
            "sent_at": log.sent_at.isoformat() if log.sent_at else None,
            "delivered_at": log.delivered_at.isoformat() if log.delivered_at else None,
            "read_at": log.read_at.isoformat() if log.read_at else None,
            "failed_at": log.failed_at.isoformat() if getattr(log, "failed_at", None) else None,
            "response_json": log.response_json if getattr(log, "response_json", None) else {},
            "payload_json": log.payload_json if getattr(log, "payload_json", None) else {},
        })

    return json_ok(
        "System WhatsApp logs loaded successfully",
        data=results,
        results=results,   # ✅ دعم مباشر للفرونت الحالي
        count=len(results),
    )