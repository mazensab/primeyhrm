# ============================================================
# 📂 api/company/whatsapp/logs.py
# 🏢 Company WhatsApp Logs API
# Primey HR Cloud
# ============================================================

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import JsonResponse

from company_manager.models import Company
from whatsapp_center.models import WhatsAppMessageLog
from api.company.whatsapp.helpers import json_not_found


def _json_success(message: str, **extra):
    payload = {"success": True, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=200)


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _get_company_from_session(request):
    """
    نحاول استخراج الشركة النشطة من الـ session
    باستخدام أكثر المفاتيح احتمالًا داخل النظام
    بدون كسر أي منطق سابق.
    """
    session = getattr(request, "session", None)
    if not session:
        return None

    possible_keys = [
        "active_company_id",
        "company_id",
        "current_company_id",
        "selected_company_id",
    ]

    for key in possible_keys:
        company_id = _safe_int(session.get(key))
        if company_id:
            company = Company.objects.filter(id=company_id).first()
            if company:
                return company

    return None


def _get_active_company(request):
    """
    ترتيب آمن ومرن لاستخراج الشركة النشطة:
    1) user.active_company
    2) user.company_user.company
    3) session keys
    """
    user = request.user

    company = getattr(user, "active_company", None)
    if company:
        return company

    company_user = getattr(user, "company_user", None)
    if company_user and getattr(company_user, "company", None):
        return company_user.company

    company = _get_company_from_session(request)
    if company:
        return company

    return None


@login_required
@require_GET
def company_whatsapp_logs(request):
    company = _get_active_company(request)
    if not company:
        return json_not_found("No active company found")

    logs = (
        WhatsAppMessageLog.objects
        .filter(company=company)
        .select_related("template", "company")
        .order_by("-created_at")[:100]
    )

    results = []
    for log in logs:
        results.append({
            "id": log.id,
            "status": log.delivery_status,
            "delivery_status": log.delivery_status,
            "direction": "OUTBOUND",
            "message_type": log.message_type,
            "recipient_name": log.recipient_name,
            "recipient_phone": log.recipient_phone,
            "template_name": log.template_name_snapshot,
            "provider_message_id": log.external_message_id,
            "provider_status": log.provider_status,
            "error_message": log.failure_reason,
            "payload_summary": log.message_body,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "sent_at": log.sent_at.isoformat() if log.sent_at else None,
            "delivered_at": log.delivered_at.isoformat() if log.delivered_at else None,
            "read_at": log.read_at.isoformat() if log.read_at else None,
            "event_code": log.event_code,
            "trigger_source": log.trigger_source,
        })

    return _json_success(
        "Company WhatsApp logs loaded successfully",
        count=len(results),
        results=results,
    )