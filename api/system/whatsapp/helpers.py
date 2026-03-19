# ============================================================
# 📂 api/system/whatsapp/helpers.py
# Primey HR Cloud - System WhatsApp API Helpers
# ============================================================

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from django.http import JsonResponse


def json_ok(message: str = "OK", **extra):
    payload = {"ok": True, "success": True, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=200)


def json_bad_request(message: str = "Bad request", **extra):
    payload = {"ok": False, "success": False, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=400)


def json_forbidden(message: str = "Forbidden", **extra):
    payload = {"ok": False, "success": False, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=403)


def json_not_found(message: str = "Not found", **extra):
    payload = {"ok": False, "success": False, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=404)


def json_server_error(message: str = "Server error", **extra):
    payload = {"ok": False, "success": False, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=500)


def read_json_body(request) -> dict[str, Any]:
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON payload")


def mask_secret(value: str | None, keep_start: int = 4, keep_end: int = 4) -> str:
    value = (value or "").strip()
    if not value:
        return ""

    if len(value) <= keep_start + keep_end:
        return "*" * len(value)

    return f"{value[:keep_start]}{'*' * max(6, len(value) - (keep_start + keep_end))}{value[-keep_end:]}"


def clean_phone(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""

    allowed = []
    for ch in raw:
        if ch.isdigit():
            allowed.append(ch)

    return "".join(allowed)


def get_model_attr(instance, field_name: str, default=None):
    return getattr(instance, field_name, default)


def set_model_attr_if_exists(instance, field_name: str, value) -> None:
    if hasattr(instance, field_name):
        setattr(instance, field_name, value)


def bool_or_default(value, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def get_session_gateway_base_url() -> str:
    return (os.getenv("WHATSAPP_SESSION_GATEWAY_URL") or "").strip().rstrip("/")


def _gateway_headers() -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    token = (os.getenv("WHATSAPP_SESSION_GATEWAY_TOKEN") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def call_session_gateway(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    يربط Django مع خدمة خارجية مسؤولة عن:
    - إنشاء QR
    - إنشاء Pairing Code
    - جلب حالة الجلسة
    - فصل الجلسة

    المتغير المطلوب:
      WHATSAPP_SESSION_GATEWAY_URL=http://127.0.0.1:3100

    المسارات المتوقعة على الـ gateway:
      POST /session/create-qr/
      POST /session/create-pairing-code/
      POST /session/disconnect/
      POST /session/status/
    """
    base_url = get_session_gateway_base_url()
    if not base_url:
        return {
            "success": False,
            "message": "WHATSAPP_SESSION_GATEWAY_URL is not configured",
            "session_status": "disconnected",
        }

    path_map = {
        "create_qr": "/session/create-qr/",
        "create_pairing_code": "/session/create-pairing-code/",
        "disconnect": "/session/disconnect/",
        "status": "/session/status/",
    }

    if action not in path_map:
        return {
            "success": False,
            "message": f"Unsupported gateway action: {action}",
            "session_status": "failed",
        }

    target_url = urljoin(f"{base_url}/", path_map[action].lstrip("/"))
    request_body = json.dumps(payload or {}).encode("utf-8")

    req = Request(
        target_url,
        data=request_body,
        headers=_gateway_headers(),
        method="POST",
    )

    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8") or "{}"
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "message": "Invalid JSON response from session gateway",
                    "raw_response": raw,
                    "session_status": "failed",
                }

            if "success" not in data:
                data["success"] = True

            return data

    except HTTPError as exc:
        try:
            body = exc.read().decode("utf-8") or ""
            parsed = json.loads(body) if body else {}
        except Exception:
            parsed = {}

        return {
            "success": False,
            "message": parsed.get("message") or f"Gateway HTTPError {exc.code}",
            "details": parsed,
            "session_status": "failed",
        }

    except URLError as exc:
        return {
            "success": False,
            "message": f"Session gateway connection failed: {exc.reason}",
            "session_status": "failed",
        }

    except Exception as exc:
        return {
            "success": False,
            "message": f"Unexpected session gateway error: {str(exc)}",
            "session_status": "failed",
        }