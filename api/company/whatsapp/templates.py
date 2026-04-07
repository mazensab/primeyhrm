# ============================================================
# 📂 api/company/whatsapp/templates.py
# 🏢 Company WhatsApp Templates API
# Mham Cloud
# ============================================================

from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from whatsapp_center.models import ScopeType, WhatsAppTemplate
from whatsapp_center.services import ensure_company_default_whatsapp_templates
from api.company.whatsapp.helpers import (
    json_bad_request,
    json_not_found,
    json_server_error,
    resolve_request_company,
)


# ============================================================
# ✅ Helpers
# ============================================================

def _json_success(message: str, **extra):
    payload = {"success": True, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=200)


def _parse_json_body(request):
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


def _clean_str(value, default=""):
    if value is None:
        return default
    return str(value).strip()


def _clean_bool(value, default=False):
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "on"}:
            return True
        if v in {"0", "false", "no", "off"}:
            return False

    return default


def _next_company_template_version(company, template_key: str) -> int:
    last_version = (
        WhatsAppTemplate.objects
        .filter(
            scope_type=ScopeType.COMPANY,
            company=company,
            template_key=template_key,
        )
        .aggregate(max_version=Max("version"))
        .get("max_version")
    )
    return (last_version or 0) + 1


def _serialize_template(item: WhatsAppTemplate):
    return {
        "id": item.id,
        "name": item.template_name or item.template_key or f"Template #{item.id}",
        "template_name": item.template_name,
        "template_key": item.template_key,
        "template_type": item.message_type,
        "message_type": item.message_type,
        "language": item.language_code,
        "language_code": item.language_code,
        "category": item.event_code,
        "event_code": item.event_code,
        "status": item.approval_status,
        "approval_status": item.approval_status,
        "provider_status": item.provider_status,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        "last_synced_at": item.last_synced_at.isoformat() if getattr(item, "last_synced_at", None) else None,
        "body_preview": item.body_text,
        "body_text": item.body_text,
        "header_text": item.header_text,
        "footer_text": item.footer_text,
        "button_text": item.button_text,
        "button_url": item.button_url,
        "meta_template_name": item.meta_template_name,
        "meta_template_namespace": item.meta_template_namespace,
        "scope_type": item.scope_type,
        "is_default": item.is_default,
        "is_active": item.is_active,
        "version": item.version,
        "rejection_reason": getattr(item, "rejection_reason", "") or "",
    }


def _get_company_owned_template(company, template_id: int):
    return WhatsAppTemplate.objects.filter(
        id=template_id,
        scope_type=ScopeType.COMPANY,
        company=company,
    ).first()


def _apply_template_payload(item: WhatsAppTemplate, payload: dict, company, user=None):
    """
    ============================================================
    ✅ تحديث/تعيين الحقول المسموح بها لقالب الشركة فقط
    ============================================================
    """

    template_name = _clean_str(payload.get("template_name"))
    template_key = _clean_str(payload.get("template_key"))
    message_type = _clean_str(payload.get("message_type"), "TEXT").upper()
    language_code = _clean_str(payload.get("language_code"), "ar")
    event_code = _clean_str(payload.get("event_code"), "general")
    approval_status = _clean_str(payload.get("approval_status"), "DRAFT").upper()
    body_text = _clean_str(payload.get("body_text"))
    header_text = _clean_str(payload.get("header_text"))
    footer_text = _clean_str(payload.get("footer_text"))
    button_text = _clean_str(payload.get("button_text"))
    button_url = _clean_str(payload.get("button_url"))
    is_default = _clean_bool(payload.get("is_default"), False)
    is_active = _clean_bool(payload.get("is_active"), True)

    if not template_name:
        raise ValueError("Template name is required")

    if not template_key:
        raise ValueError("Template key is required")

    if not body_text:
        raise ValueError("Template body is required")

    item.company = company
    item.scope_type = ScopeType.COMPANY
    item.template_name = template_name
    item.template_key = template_key
    item.message_type = message_type
    item.language_code = language_code
    item.event_code = event_code
    item.approval_status = approval_status
    item.body_text = body_text
    item.header_text = header_text
    item.footer_text = footer_text
    item.button_text = button_text
    item.button_url = button_url
    item.is_default = is_default
    item.is_active = is_active

    if hasattr(item, "provider_status"):
        item.provider_status = "NOT_SYNCED"

    if hasattr(item, "meta_template_name") and not item.meta_template_name:
        item.meta_template_name = ""

    if hasattr(item, "meta_template_namespace") and not item.meta_template_namespace:
        item.meta_template_namespace = ""

    if user and getattr(user, "is_authenticated", False):
        if not item.pk and hasattr(item, "created_by") and not item.created_by:
            item.created_by = user
        if hasattr(item, "updated_by"):
            item.updated_by = user

    return item


# ============================================================
# 📥 List - Company Only + Auto Bootstrap
# ============================================================

@login_required
@require_GET
def company_whatsapp_templates(request):
    company = resolve_request_company(request)
    if not company:
        return json_not_found("No active company found")

    ensure_company_default_whatsapp_templates(company=company, user=request.user)

    templates = (
        WhatsAppTemplate.objects
        .filter(
            scope_type=ScopeType.COMPANY,
            company=company,
        )
        .order_by("event_code", "-version", "-id")
    )

    results = [_serialize_template(item) for item in templates]

    return _json_success(
        "Company WhatsApp templates loaded successfully",
        count=len(results),
        results=results,
    )


# ============================================================
# ➕ Create
# ============================================================

@login_required
@require_POST
def company_whatsapp_template_create(request):
    company = resolve_request_company(request)
    if not company:
        return json_not_found("No active company found")

    payload = _parse_json_body(request)
    if payload is None:
        return json_bad_request("Invalid JSON body")

    try:
        with transaction.atomic():
            template_key = _clean_str(payload.get("template_key"))
            if not template_key:
                return json_bad_request("Template key is required")

            item = WhatsAppTemplate(
                company=company,
                scope_type=ScopeType.COMPANY,
                version=_next_company_template_version(company, template_key),
            )

            _apply_template_payload(item, payload, company, request.user)
            item.save()

        return _json_success(
            "Company WhatsApp template created successfully",
            item=_serialize_template(item),
        )
    except ValueError as exc:
        return json_bad_request(str(exc))
    except Exception as exc:
        return json_server_error(f"Failed to create template: {exc}")


# ============================================================
# ✏️ Update
# ============================================================

@login_required
@require_POST
def company_whatsapp_template_update(request, template_id: int):
    company = resolve_request_company(request)
    if not company:
        return json_not_found("No active company found")

    payload = _parse_json_body(request)
    if payload is None:
        return json_bad_request("Invalid JSON body")

    item = _get_company_owned_template(company, template_id)
    if not item:
        return json_not_found("Company WhatsApp template not found")

    try:
        with transaction.atomic():
            original_key = item.template_key
            new_key = _clean_str(payload.get("template_key"), original_key)

            if new_key and new_key != original_key:
                item.version = _next_company_template_version(company, new_key)

            _apply_template_payload(item, payload, company, request.user)
            item.save()

        return _json_success(
            "Company WhatsApp template updated successfully",
            item=_serialize_template(item),
        )
    except ValueError as exc:
        return json_bad_request(str(exc))
    except Exception as exc:
        return json_server_error(f"Failed to update template: {exc}")


# ============================================================
# 🔁 Toggle Active
# ============================================================

@login_required
@require_POST
def company_whatsapp_template_toggle(request, template_id: int):
    company = resolve_request_company(request)
    if not company:
        return json_not_found("No active company found")

    item = _get_company_owned_template(company, template_id)
    if not item:
        return json_not_found("Company WhatsApp template not found")

    try:
        item.is_active = not item.is_active

        update_fields = ["is_active", "updated_at"]

        if hasattr(item, "provider_status"):
            item.provider_status = "NOT_SYNCED"
            update_fields.append("provider_status")

        if hasattr(item, "updated_by") and request.user.is_authenticated:
            item.updated_by = request.user
            update_fields.append("updated_by")

        item.save(update_fields=update_fields)

        return _json_success(
            "Company WhatsApp template status updated successfully",
            item=_serialize_template(item),
        )
    except Exception as exc:
        return json_server_error(f"Failed to toggle template: {exc}")


# ============================================================
# 🗑 Delete
# ============================================================

@login_required
@require_POST
def company_whatsapp_template_delete(request, template_id: int):
    company = resolve_request_company(request)
    if not company:
        return json_not_found("No active company found")

    item = _get_company_owned_template(company, template_id)
    if not item:
        return json_not_found("Company WhatsApp template not found")

    try:
        item.delete()
        return _json_success("Company WhatsApp template deleted successfully")
    except Exception as exc:
        return json_server_error(f"Failed to delete template: {exc}")