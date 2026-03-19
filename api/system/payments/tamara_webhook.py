# ============================================================
# Tamara Webhook API
# Primey HR Cloud
# Path: api/system/payments/tamara_webhook.py
# ------------------------------------------------------------
# Webhook Endpoint
# - Receives Tamara notifications
# - Verifies tamaraToken when notification token is configured
# - Parses event / order status safely
# - Resolves onboarding draft_id from order_reference_id
# - Forwards final success to confirm_onboarding_payment
# - Safe first production wiring for current architecture
# ============================================================

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
from typing import Any, Dict, Optional

from django.conf import settings
from django.http import JsonResponse
from django.test.client import RequestFactory
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from api.system.onboarding.confirm_payment import confirm_onboarding_payment

logger = logging.getLogger(__name__)


# ============================================================
# Helpers
# ============================================================

def _json_body(request) -> Dict[str, Any]:
    """
    قراءة JSON body بشكل آمن.
    """
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _clean_str(value: Any, default: str = "") -> str:
    """
    تحويل آمن إلى string.
    """
    if value is None:
        return default
    return str(value).strip()


def _mask_token(value: Optional[str]) -> str:
    """
    إخفاء جزء من التوكن في اللوج.
    """
    if not value:
        return ""
    value = str(value).strip()
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


def _constant_time_compare(a: str, b: str) -> bool:
    """
    مقارنة آمنة ضد timing attacks.
    """
    if not a or not b:
        return False
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _verify_tamara_token(request, payload: Dict[str, Any]) -> tuple[bool, str]:
    """
    التحقق من tamaraToken إن كان Notification Token مفعلاً في الإعدادات.

    آلية التحقق الحالية:
    1) إذا لا يوجد TAMARA_NOTIFICATION_TOKEN -> نتجاوز التحقق مع تحذير واضح.
    2) نحاول قراءة tamaraToken من body أو headers.
    3) نقبل حالتين:
       - token المباشر يساوي notification token
       - أو HMAC SHA256 للـ raw body باستخدام notification token
    """
    configured_token = _clean_str(getattr(settings, "TAMARA_NOTIFICATION_TOKEN", ""))
    if not configured_token:
        logger.warning(
            "Tamara webhook received without configured TAMARA_NOTIFICATION_TOKEN. "
            "Verification skipped."
        )
        return True, "verification_skipped"

    body_token = _clean_str(payload.get("tamaraToken"))
    header_token = _clean_str(
        request.headers.get("tamaraToken")
        or request.headers.get("TamaraToken")
        or request.headers.get("X-Tamara-Token")
        or request.META.get("HTTP_TAMARATOKEN")
        or request.META.get("HTTP_X_TAMARA_TOKEN")
    )

    incoming_token = body_token or header_token
    if not incoming_token:
        logger.warning("Tamara webhook rejected: missing tamaraToken.")
        return False, "missing_tamara_token"

    # الحالة 1: توكن مباشر
    if _constant_time_compare(incoming_token, configured_token):
        return True, "direct_match"

    # الحالة 2: HMAC SHA256 للـ raw body
    raw_body = request.body or b""
    expected_hmac = hmac.new(
        configured_token.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if _constant_time_compare(incoming_token, expected_hmac):
        return True, "hmac_match"

    logger.warning(
        "Tamara webhook rejected: invalid tamaraToken. incoming=%s configured=%s",
        _mask_token(incoming_token),
        _mask_token(configured_token),
    )
    return False, "invalid_tamara_token"


def _extract_event_name(payload: Dict[str, Any]) -> str:
    """
    استخراج اسم الحدث بشكل مرن.
    """
    return _clean_str(
        payload.get("event_type")
        or payload.get("event")
        or payload.get("notification_type")
        or payload.get("type")
        or "unknown"
    )


def _extract_order_status(payload: Dict[str, Any]) -> str:
    """
    استخراج حالة الطلب بشكل مرن.
    """
    order = payload.get("order") if isinstance(payload.get("order"), dict) else {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

    return _clean_str(
        payload.get("order_status")
        or payload.get("status")
        or order.get("status")
        or data.get("status")
        or "unknown"
    )


def _extract_order_id(payload: Dict[str, Any]) -> str:
    """
    استخراج order_id بشكل مرن.
    """
    order = payload.get("order") if isinstance(payload.get("order"), dict) else {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

    return _clean_str(
        payload.get("order_id")
        or payload.get("tamara_order_id")
        or order.get("order_id")
        or order.get("id")
        or data.get("order_id")
        or data.get("id")
    )


def _extract_order_reference_id(payload: Dict[str, Any]) -> str:
    """
    استخراج order_reference_id المحلي بشكل مرن.
    """
    order = payload.get("order") if isinstance(payload.get("order"), dict) else {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

    return _clean_str(
        payload.get("order_reference_id")
        or payload.get("reference_id")
        or order.get("order_reference_id")
        or order.get("reference_id")
        or data.get("order_reference_id")
        or data.get("reference_id")
    )


def _extract_checkout_id(payload: Dict[str, Any]) -> str:
    """
    استخراج checkout_id بشكل مرن.
    """
    order = payload.get("order") if isinstance(payload.get("order"), dict) else {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

    return _clean_str(
        payload.get("checkout_id")
        or payload.get("tamara_checkout_id")
        or order.get("checkout_id")
        or data.get("checkout_id")
    )


def _extract_payment_method(payload: Dict[str, Any]) -> str:
    """
    استخراج/توحيد طريقة الدفع المحلية.

    confirm_onboarding_payment لا يقبل "TAMARA" حاليًا،
    لذلك نمرر CREDIT_CARD كأقرب تمثيل متوافق إلى أن
    نوسّع allowed_payment_methods لاحقًا.
    """
    raw_method = _clean_str(
        payload.get("payment_method")
        or payload.get("method")
        or payload.get("payment_type")
    ).upper()

    allowed = {"BANK_TRANSFER", "CREDIT_CARD", "APPLE_PAY", "STC_PAY"}
    if raw_method in allowed:
        return raw_method

    return "CREDIT_CARD"


def _normalize_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    بناء شكل موحد للبيانات القادمة من Tamara.
    """
    event_name = _extract_event_name(payload)
    order_status = _extract_order_status(payload)
    order_id = _extract_order_id(payload)
    order_reference_id = _extract_order_reference_id(payload)
    checkout_id = _extract_checkout_id(payload)
    payment_method = _extract_payment_method(payload)

    return {
        "event_name": event_name,
        "order_status": order_status,
        "order_id": order_id,
        "order_reference_id": order_reference_id,
        "checkout_id": checkout_id,
        "payment_method": payment_method,
        "raw_payload": payload,
    }


def _extract_draft_id(order_reference_id: str) -> Optional[int]:
    """
    استخراج draft_id من order_reference_id.

    يدعم أمثلة مثل:
    - 123
    - DRAFT-123
    - draft-123
    - ONBOARDING-DRAFT-123
    - draft:123
    - onboarding_draft_123
    """
    ref = _clean_str(order_reference_id)
    if not ref:
        return None

    if ref.isdigit():
        return int(ref)

    patterns = [
        r"^DRAFT[-_:]?(\d+)$",
        r"^ONBOARDING[-_]?DRAFT[-_:]?(\d+)$",
        r"^ONBOARDING_DRAFT[-_:]?(\d+)$",
        r".*?DRAFT[-_:]?(\d+).*",
        r".*?(\d+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, ref, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (TypeError, ValueError):
                continue

    return None


def _map_gateway_status(order_status: str) -> str:
    """
    تحويل حالة Tamara إلى الحالة المتوقعة في confirm_onboarding_payment.
    """
    status = _clean_str(order_status).upper()

    success_map = {
        "SUCCESS": "SUCCESS",
        "PAID": "PAID",
        "CAPTURED": "CAPTURED",
        "FULLY_CAPTURED": "CAPTURED",
        "PARTIALLY_CAPTURED": "CAPTURED",
    }

    pending_map = {
        "NEW": "INITIATED",
        "PENDING": "PENDING",
        "INITIATED": "INITIATED",
        "WAITING": "WAITING",
        "PROCESSING": "PROCESSING",
        "APPROVED": "PROCESSING",
        "AUTHORISED": "PROCESSING",
        "AUTHORIZED": "PROCESSING",
    }

    failed_map = {
        "DECLINED": "FAILED",
        "REJECTED": "FAILED",
        "EXPIRED": "FAILED",
        "CANCELED": "FAILED",
        "CANCELLED": "FAILED",
        "FAILED": "FAILED",
        "REFUNDED": "FAILED",
        "FULLY_REFUNDED": "FAILED",
        "PARTIALLY_REFUNDED": "FAILED",
    }

    if status in success_map:
        return success_map[status]

    if status in pending_map:
        return pending_map[status]

    if status in failed_map:
        return failed_map[status]

    return "PROCESSING"


def _build_internal_confirm_payload(normalized: Dict[str, Any], draft_id: int) -> Dict[str, Any]:
    """
    بناء payload داخلي لإعادة استخدام confirm_onboarding_payment.
    """
    gateway_status = _map_gateway_status(normalized["order_status"])
    gateway_transaction_id = _clean_str(normalized["order_id"]) or _clean_str(normalized["checkout_id"])

    if gateway_transaction_id:
        gateway_transaction_id = f"TAMARA:{gateway_transaction_id}"

    return {
        "draft_id": draft_id,
        "payment_method": normalized["payment_method"],
        "gateway_status": gateway_status,
        "gateway_transaction_id": gateway_transaction_id,
    }


def _call_confirm_onboarding_payment(payload: Dict[str, Any]) -> JsonResponse:
    """
    استدعاء داخلي لنفس منطق تأكيد الدفع الموجود أصلًا في النظام.
    """
    factory = RequestFactory()
    request = factory.post(
        "/api/system/onboarding/confirm-payment/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    return confirm_onboarding_payment(request)


def _handle_webhook_event(normalized: Dict[str, Any]) -> Dict[str, Any]:
    """
    معالجة الحدث وربطه مع تدفق Onboarding الحالي.
    """
    event_name = normalized["event_name"]
    order_status = normalized["order_status"]
    order_reference_id = normalized["order_reference_id"]
    order_id = normalized["order_id"]

    gateway_status = _map_gateway_status(order_status)
    draft_id = _extract_draft_id(order_reference_id)

    action = "logged_only"
    forwarded = False
    internal_status_code = None
    internal_body: Dict[str, Any] | None = None

    if gateway_status == "CAPTURED":
        action = "payment_success_received"

        if not draft_id:
            action = "success_but_missing_draft_reference"
        else:
            internal_payload = _build_internal_confirm_payload(normalized, draft_id=draft_id)
            internal_response = _call_confirm_onboarding_payment(internal_payload)

            forwarded = True
            internal_status_code = getattr(internal_response, "status_code", None)

            try:
                internal_body = json.loads(internal_response.content.decode("utf-8"))
            except Exception:
                internal_body = {"raw": internal_response.content.decode("utf-8", errors="ignore")}

            # 200 = نجاح فعلي
            # 409 = سبق التأكيد، وهذا مقبول كـ idempotent success
            if internal_status_code == 200:
                action = "payment_confirmed_and_activated"
            elif internal_status_code == 409:
                action = "already_confirmed"
            elif internal_status_code == 202:
                action = "payment_pending_in_internal_flow"
            else:
                action = "internal_confirmation_failed"

    elif gateway_status in {"INITIATED", "PENDING", "WAITING", "PROCESSING"}:
        action = "payment_pending"

    elif gateway_status == "FAILED":
        action = "payment_failed"

    logger.info(
        "Tamara webhook processed. event=%s status=%s mapped=%s order_id=%s ref=%s draft_id=%s action=%s",
        event_name,
        order_status,
        gateway_status,
        order_id,
        order_reference_id,
        draft_id,
        action,
    )

    return {
        "handled": True,
        "action": action,
        "draft_id": draft_id,
        "mapped_gateway_status": gateway_status,
        "forwarded_to_confirm_payment": forwarded,
        "internal_status_code": internal_status_code,
        "internal_body": internal_body,
    }


# ============================================================
# API
# ============================================================

@csrf_exempt
@require_POST
def tamara_webhook(request):
    """
    استقبال Webhook من Tamara.

    ملاحظات:
    - لا يحتاج login
    - CSRF disabled لأنه endpoint خارجي
    - التحقق يعتمد على tamaraToken عند وجوده في settings
    - النجاح النهائي فقط هو الذي يمرّر التنفيذ إلى confirm_onboarding_payment
    """
    if not getattr(settings, "TAMARA_ENABLED", False):
        return JsonResponse(
            {
                "status": "error",
                "message": "Tamara gateway is disabled.",
            },
            status=503,
        )

    payload = _json_body(request)
    if not payload:
        logger.warning("Tamara webhook received empty or invalid JSON payload.")
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid or empty JSON payload.",
            },
            status=400,
        )

    is_valid, verification_mode = _verify_tamara_token(request, payload)
    if not is_valid:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid Tamara webhook token.",
            },
            status=403,
        )

    try:
        normalized = _normalize_webhook_payload(payload)

        if not normalized["order_id"] and not normalized["order_reference_id"]:
            logger.warning(
                "Tamara webhook rejected: missing order identifiers. payload=%s",
                payload,
            )
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Missing Tamara order identifiers.",
                },
                status=400,
            )

        result = _handle_webhook_event(normalized)

        response_status = 200
        if result["action"] == "internal_confirmation_failed":
            response_status = 500

        return JsonResponse(
            {
                "status": "ok" if response_status == 200 else "error",
                "message": "Tamara webhook received successfully." if response_status == 200 else "Tamara webhook received but internal confirmation failed.",
                "verification_mode": verification_mode,
                "event_name": normalized["event_name"],
                "order_status": normalized["order_status"],
                "mapped_gateway_status": result["mapped_gateway_status"],
                "order_id": normalized["order_id"],
                "order_reference_id": normalized["order_reference_id"],
                "checkout_id": normalized["checkout_id"],
                "draft_id": result["draft_id"],
                "handled": result["handled"],
                "action": result["action"],
                "forwarded_to_confirm_payment": result["forwarded_to_confirm_payment"],
                "internal_status_code": result["internal_status_code"],
                "internal_body": result["internal_body"],
            },
            status=response_status,
        )

    except Exception as exc:
        logger.exception("Unexpected error while processing Tamara webhook.")
        return JsonResponse(
            {
                "status": "error",
                "message": "Unexpected server error while processing Tamara webhook.",
                "details": str(exc) if settings.DEBUG else "",
            },
            status=500,
        )