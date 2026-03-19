# ============================================================
# 📂 api/company/whatsapp/helpers.py
# Primey HR Cloud - Company WhatsApp API Helpers
# ============================================================

from __future__ import annotations

import json
import re

from django.http import JsonResponse

from company_manager.models import Company


def json_ok(message: str = "OK", **extra):
    payload = {"ok": True, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=200)


def json_bad_request(message: str = "Bad request", **extra):
    payload = {"ok": False, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=400)


def json_forbidden(message: str = "Forbidden", **extra):
    payload = {"ok": False, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=403)


def json_not_found(message: str = "Not found", **extra):
    payload = {"ok": False, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=404)


def json_server_error(message: str = "Server error", **extra):
    payload = {"ok": False, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=500)


def read_json_body(request) -> dict:
    try:
        raw_body = (request.body or b"").decode("utf-8").strip()
    except Exception:
        raw_body = ""

    if not raw_body:
        return {}

    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON body")

    if not isinstance(data, dict):
        raise ValueError("JSON body must be an object")

    return data


def clean_phone(value) -> str:
    value = str(value or "").strip()
    if not value:
        return ""
    return re.sub(r"[^\d]", "", value)


def get_model_attr(obj, field_name: str, default=None):
    if obj is None:
        return default
    return getattr(obj, field_name, default)


def resolve_request_company(request):
    """
    ============================================================
    🎯 Resolve current company safely for company-scope APIs
    ============================================================
    Resolution order:
    1) user.active_company
    2) user.company_user.company
    3) user.company_users.first().company
    4) user.hr_employee.company
    5) session['active_company_id']
    6) session['company_id']
    ============================================================
    """
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return None

    company = getattr(user, "active_company", None)
    if company:
        return company

    company_user = getattr(user, "company_user", None)
    if company_user and getattr(company_user, "company", None):
        return company_user.company

    company_users_qs = getattr(user, "company_users", None)
    if company_users_qs is not None:
        first_company_user = company_users_qs.select_related("company").first()
        if first_company_user and getattr(first_company_user, "company", None):
            return first_company_user.company

    hr_employee = getattr(user, "hr_employee", None)
    if hr_employee and getattr(hr_employee, "company", None):
        return hr_employee.company

    session = getattr(request, "session", None)
    if session is not None:
        company_id = session.get("active_company_id") or session.get("company_id")
        if company_id:
            try:
                return Company.objects.filter(id=company_id).first()
            except Exception:
                return None

    return None