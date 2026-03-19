# ============================================================
# Tap Webhook API
# Primey HR Cloud
# Path: api/system/payments/tap_webhook.py
# ------------------------------------------------------------
# Webhook Endpoint
# - Receives Tap charge notifications
# - Verifies Tap hashstring when enabled
# - Resolves onboarding draft_id from metadata/reference
# - Forwards final success to confirm_onboarding_payment
# ============================================================

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
from decimal import Decimal, InvalidOperation
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
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _clean_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _constant_time_compare(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _currency_decimals(currency: str) -> int:
    currency = _clean_str(currency).upper()
    three_decimals = {"BHD", "KWD", "OMR", "JOD"}
    return 3 if currency in three_decimals else 2


def _format_amount_for_hash(amount: Any, currency: str) -> str:
    decimals = _currency_decimals(currency)
    quant = Decimal("1." + ("0" * decimals))

    try:
        value = Decimal(str(amount)).quantize(quant)
        return f"{value:.{decimals}f}"
    except (InvalidOperation, ValueError, TypeError):
        return f"{Decimal('0').quantize(quant):.{decimals}f}"


def _extract_header_hashstring(request) -> str:
    return _clean_str(
        request.headers.get("hashstring")
        or request.headers.get("Hashstring")
        or request.headers.get("X-Hashstring")
        or request.META.get("HTTP_HASHSTRING")
        or request.META.get("HTTP_X_HASHSTRING")
    )


def _build_charge_hashstring(payload: Dict[str, Any], secret_key: str) -> str:
    charge_id = _clean_str(payload.get("id"))
    amount = _format_amount_for_hash(payload.get("amount"), _clean_str(payload.get("currency")))
    currency = _clean_str(payload.get("currency")).upper()

    reference = payload.get("reference") if isinstance(payload.get("reference"), dict) else {}
    transaction_data = payload.get("transaction") if isinstance(payload.get("transaction"), dict) else {}

    gateway_reference = _clean_str(reference.get("gateway"))
    payment_reference = _clean_str(reference.get("payment"))
    status = _clean_str(payload.get("status")).upper()
    created = _clean_str(transaction_data.get("created"))

    to_be_hashed = (
        f"x_id{charge_id}"
        f"x_amount{amount}"
        f"x_currency{currency}"
        f"x_gateway_reference{gateway_reference}"
        f"x_payment_reference{payment_reference}"
        f"x_status{status}"
        f"x_created{created}"
    )

    return hmac.new(
        secret_key.encode("utf-8"),
        to_be_hashed.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _verify_tap_hashstring(request, payload: Dict[str, Any]) -> tuple[bool, str]:
    if not getattr(settings, "TAP_VERIFY_WEBHOOK", True):
        logger.warning("Tap webhook verification is disabled by TAP_VERIFY_WEBHOOK=False")
        return True, "verification_disabled"

    secret_key = _clean_str(getattr(settings, "TAP_SECRET_KEY", ""))
    if not secret_key:
        logger.warning("Tap webhook verification skipped: TAP_SECRET_KEY is empty.")
        return True, "secret_missing"

    header_hash = _extract_header_hashstring(request)
    if not header_hash:
        logger.warning("Tap webhook rejected: missing hashstring header.")
        return False, "missing_hashstring"

    expected_hash = _build_charge_hashstring(payload, secret_key)
    if _constant_time_compare(header_hash, expected_hash):
        return True, "hashstring_valid"

    logger.warning("Tap webhook rejected: invalid hashstring.")
    return False, "invalid_hashstring"


def _extract_reference(payload: Dict[str, Any]) -> Dict[str, Any]:
    return payload.get("reference") if isinstance(payload.get("reference"), dict) else {}


def _extract_metadata(payload: Dict[str, Any]) -> Dict[str, Any]:
    return payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}


def _extract_draft_id(payload: Dict[str, Any]) -> Optional[int]:
    metadata = _extract_metadata(payload)
    reference = _extract_reference(payload)

    candidate_values = [
        metadata.get("draft_id"),
        reference.get("order"),
        reference.get("transaction"),
    ]

    for value in candidate_values:
        value_str = _clean_str(value)
        if not value_str:
            continue

        if value_str.isdigit():
            return int(value_str)

        match = re.search(r"(\d+)", value_str)
        if match:
            try:
                return int(match.group(1))
            except Exception:
                pass

    return None


def _map_gateway_status(status: str) -> str:
    status = _clean_str(status).upper()

    mapping = {
        "CAPTURED": "CAPTURED",
        "AUTHORIZED": "AUTHORIZED",
        "APPROVED": "APPROVED",
        "INITIATED": "INITIATED",
        "PENDING": "PENDING",
        "ABANDONED": "FAILED",
        "FAILED": "FAILED",
        "DECLINED": "FAILED",
        "CANCELLED": "FAILED",
        "VOID": "FAILED",
    }
    return mapping.get(status, status or "UNKNOWN")


def _build_internal_confirm_payload(payload: Dict[str, Any], *, draft_id: int) -> Dict[str, Any]:
    """
    مهم:
    confirm_onboarding_payment يعتمد رسميًا على CREDIT_CARD كتدفق Tap-backed.
    """
    return {
        "draft_id": draft_id,
        "payment_method": "CREDIT_CARD",
        "gateway_status": _map_gateway_status(payload.get("status")),
        "gateway_transaction_id": _clean_str(payload.get("id")),
        "gateway_reference": _clean_str((_extract_reference(payload)).get("gateway")),
        "payment_reference": _clean_str((_extract_reference(payload)).get("payment")),
        "raw_gateway_payload": payload,
    }


def _call_confirm_onboarding_payment(payload: Dict[str, Any]):
    factory = RequestFactory()
    request = factory.post(
        "/api/system/onboarding/confirm-payment/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    return confirm_onboarding_payment(request)


def _handle_webhook_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    charge_id = _clean_str(payload.get("id"))
    charge_status = _clean_str(payload.get("status")).upper()
    draft_id = _extract_draft_id(payload)
    gateway_status = _map_gateway_status(charge_status)

    action = "logged_only"
    forwarded = False
    internal_status_code = None
    internal_body: Dict[str, Any] | None = None

    if gateway_status in {"CAPTURED", "AUTHORIZED", "APPROVED"}:
        action = "payment_success_received"

        if not draft_id:
            action = "success_but_missing_draft_reference"
        else:
            internal_payload = _build_internal_confirm_payload(payload, draft_id=draft_id)
            internal_response = _call_confirm_onboarding_payment(internal_payload)

            forwarded = True
            internal_status_code = getattr(internal_response, "status_code", None)

            try:
                internal_body = json.loads(internal_response.content.decode("utf-8"))
            except Exception:
                internal_body = {
                    "raw": internal_response.content.decode("utf-8", errors="ignore")
                }

            if internal_status_code == 200:
                action = "payment_confirmed_and_activated"
            elif internal_status_code == 409:
                action = "already_confirmed"
            elif internal_status_code == 202:
                action = "payment_pending_in_internal_flow"
            else:
                action = "internal_confirmation_failed"

    elif gateway_status in {"INITIATED", "PENDING"}:
        action = "payment_pending"

    else:
        action = "payment_failed"

    logger.info(
        "Tap webhook processed. charge_id=%s status=%s mapped=%s draft_id=%s action=%s",
        charge_id,
        charge_status,
        gateway_status,
        draft_id,
        action,
    )

    return {
        "handled": True,
        "action": action,
        "draft_id": draft_id,
        "tap_charge_id": charge_id,
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
def tap_webhook(request):
    if not getattr(settings, "TAP_ENABLED", False):
        return JsonResponse(
            {
                "status": "error",
                "message": "Tap gateway is disabled.",
            },
            status=503,
        )

    payload = _json_body(request)
    if not payload:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid or empty JSON payload.",
            },
            status=400,
        )

    is_verified, verification_reason = _verify_tap_hashstring(request, payload)
    if not is_verified:
        return JsonResponse(
            {
                "status": "error",
                "message": "Tap webhook verification failed.",
                "verification_reason": verification_reason,
            },
            status=403,
        )

    try:
        result = _handle_webhook_event(payload)

        return JsonResponse(
            {
                "status": "ok",
                "message": "Tap webhook processed successfully.",
                "verification_reason": verification_reason,
                "result": result,
            },
            status=200,
        )

    except Exception as exc:
        logger.exception("Unexpected error while processing Tap webhook")
        return JsonResponse(
            {
                "status": "error",
                "message": f"Unexpected error while processing Tap webhook: {exc}",
            },
            status=500,
        )