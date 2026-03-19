# ============================================================
# Tap Create Checkout API
# Primey HR Cloud
# Path: api/system/payments/tap_create_checkout.py
# ------------------------------------------------------------
# System Payment API
# - Creates Tap hosted checkout charge
# - Supports onboarding draft flow directly
# - Builds reference.order as DRAFT-<id>
# - Updates onboarding draft locally
# - Creates local PaymentTransaction pending record
# - Does NOT mark invoice as paid
# - Does NOT activate subscription directly
# ============================================================

from __future__ import annotations

import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from billing_center.models import CompanyOnboardingTransaction, PaymentTransaction
from payment_gateways.tap.client import (
    TapAPIError,
    TapClient,
    TapConfig,
    TapConfigurationError,
    TapRequestError,
)

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


def _normalize_payment_method(value: Any) -> str:
    """
    Tap-backed online card flow داخل النظام يعتمد رسميًا على CREDIT_CARD.
    """
    method = _clean_str(value).upper()
    if method in {"", "TAP", "CARD", "CARD_PAYMENT"}:
        return "CREDIT_CARD"
    return method


def _is_system_user(request) -> bool:
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return False

    if getattr(user, "is_superuser", False):
        return True
    if getattr(user, "is_staff", False):
        return True

    return False


def _to_decimal_str(value: Any, places: str = "0.00") -> str:
    try:
        dec = Decimal(str(value or 0)).quantize(Decimal(places))
        return format(dec, "f")
    except (InvalidOperation, ValueError, TypeError):
        return "0.00"


def _split_admin_name(full_name: str, company_name: str) -> tuple[str, str]:
    full_name = _clean_str(full_name)
    if not full_name:
        return company_name, "Admin"

    parts = full_name.split()
    if len(parts) == 1:
        return parts[0], "Admin"

    return parts[0], " ".join(parts[1:])


def _normalize_sa_phone(raw_phone: str) -> Dict[str, str]:
    """
    Tap expects:
    phone: {"country_code": "966", "number": "5xxxxxxxx"}
    """
    phone = "".join(ch for ch in _clean_str(raw_phone) if ch.isdigit())

    if phone.startswith("966"):
        local_number = phone[3:]
    elif phone.startswith("00966"):
        local_number = phone[5:]
    elif phone.startswith("0"):
        local_number = phone[1:]
    else:
        local_number = phone

    return {
        "country_code": "966",
        "number": local_number,
    }


def _get_default_success_url() -> str:
    return _clean_str(
        getattr(settings, "TAP_SUCCESS_URL", None)
        or f"{getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')}/billing/payment/success"
    )


def _get_default_cancel_url() -> str:
    return _clean_str(
        getattr(settings, "TAP_CANCEL_URL", None)
        or f"{getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')}/billing/payment/cancel"
    )


def _get_default_webhook_url() -> str:
    return _clean_str(
        getattr(settings, "TAP_WEBHOOK_URL", None)
        or "http://127.0.0.1:8000/api/system/payments/tap/webhook/"
    )


def _build_draft_reference(draft_id: int) -> str:
    return f"DRAFT-{draft_id}"


def _get_draft_for_checkout(draft_id: Any) -> Optional[CompanyOnboardingTransaction]:
    try:
        if not draft_id:
            return None

        return (
            CompanyOnboardingTransaction.objects
            .select_related("plan", "owner")
            .get(id=draft_id)
        )
    except CompanyOnboardingTransaction.DoesNotExist:
        return None


def _validate_draft_for_checkout(draft: CompanyOnboardingTransaction) -> tuple[bool, str]:
    if draft.status not in {"DRAFT", "CONFIRMED", "PENDING_PAYMENT"}:
        return False, "Draft status does not allow Tap checkout."

    if not _clean_str(getattr(draft, "admin_email", None)):
        return False, "Draft admin_email is required for Tap checkout."

    if not _clean_str(getattr(draft, "phone", None)):
        return False, "Draft phone is required for Tap checkout."

    if not getattr(draft, "total_amount", None):
        return False, "Draft total_amount is required for Tap checkout."

    return True, ""


def _build_draft_charge_payload(
    draft: CompanyOnboardingTransaction,
    *,
    payment_method: str,
) -> Dict[str, Any]:
    company_name = _clean_str(getattr(draft, "company_name", None), "Primey HR Cloud")
    plan_name = _clean_str(getattr(getattr(draft, "plan", None), "name", None), "Primey Plan")
    admin_name = _clean_str(getattr(draft, "admin_name", None), "Customer")
    admin_email = _clean_str(getattr(draft, "admin_email", None))
    phone = _clean_str(getattr(draft, "phone", None))
    total_amount = _to_decimal_str(getattr(draft, "total_amount", 0))
    order_reference_id = _build_draft_reference(draft.id)
    transaction_reference = f"draft-{draft.id}"

    first_name, last_name = _split_admin_name(admin_name, company_name)

    payload = {
        "amount": float(total_amount),
        "currency": "SAR",
        "threeDSecure": True,
        "save_card": False,
        "description": f"{plan_name} Subscription for {company_name}",
        "statement_descriptor": "PrimeyHR",
        "metadata": {
            "draft_id": str(draft.id),
            "platform": "Primey HR Cloud",
            "module": "system_onboarding",
            "payment_method": payment_method,
        },
        "reference": {
            "transaction": transaction_reference,
            "order": order_reference_id,
        },
        "receipt": {
            "email": False,
            "sms": False,
        },
        "customer": {
            "first_name": first_name,
            "last_name": last_name,
            "email": admin_email or _clean_str(getattr(draft, "email", None)),
            "phone": _normalize_sa_phone(phone),
        },
        "merchant": {
            "id": _clean_str(getattr(settings, "TAP_MERCHANT_ID", "")),
        },
        "source": {
            "id": _clean_str(getattr(settings, "TAP_SOURCE_ID", "src_all")),
        },
        "redirect": {
            "url": _get_default_success_url(),
        },
        "post": {
            "url": _get_default_webhook_url(),
        },
    }

    if not payload["merchant"]["id"]:
        payload.pop("merchant", None)

    payload["metadata"]["cancel_url"] = _get_default_cancel_url()

    return payload


def _build_tap_client() -> TapClient:
    config = TapConfig(
        secret_key=_clean_str(getattr(settings, "TAP_SECRET_KEY", "")),
        public_key=_clean_str(getattr(settings, "TAP_PUBLIC_KEY", "")),
        timeout=int(getattr(settings, "TAP_TIMEOUT", 30) or 30),
        base_url=_clean_str(getattr(settings, "TAP_BASE_URL", "")) or "https://api.tap.company/v2",
    )
    return TapClient(config)


def _extract_checkout_url(response_data: Dict[str, Any]) -> str:
    transaction_data = response_data.get("transaction") if isinstance(response_data.get("transaction"), dict) else {}
    redirect_data = response_data.get("redirect") if isinstance(response_data.get("redirect"), dict) else {}

    return _clean_str(
        transaction_data.get("url")
        or redirect_data.get("url")
        or response_data.get("url")
    )


def _upsert_local_payment_tracking(
    *,
    draft: CompanyOnboardingTransaction,
    request_user,
    payment_method: str,
    tap_charge_id: str,
    tap_status: str,
) -> None:
    """
    حفظ تتبع محلي بدون الحاجة لتغيير الموديل الحالي.
    """
    PaymentTransaction.objects.create(
        company=None,
        invoice=None,
        amount=draft.total_amount,
        payment_method="card",
        status="pending" if _clean_str(tap_status).upper() in {"INITIATED", "PENDING"} else "success",
        transaction_id=tap_charge_id or None,
        description=f"Onboarding draft #{draft.id} - Tap checkout",
        created_by=request_user if getattr(request_user, "is_authenticated", False) else None,
    )

    draft.payment_method = payment_method
    draft.status = "PENDING_PAYMENT"
    draft.save(update_fields=["payment_method", "status"])


# ============================================================
# API
# ============================================================

@login_required
@require_POST
def tap_create_checkout(request):
    if not getattr(settings, "TAP_ENABLED", False):
        return JsonResponse(
            {
                "status": "error",
                "message": "Tap payment gateway is disabled.",
            },
            status=503,
        )

    if not _is_system_user(request):
        return JsonResponse(
            {
                "status": "error",
                "message": "You do not have permission to create Tap checkout from system scope.",
            },
            status=403,
        )

    payload = _json_body(request)
    if not payload:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid JSON payload.",
            },
            status=400,
        )

    payment_method = _normalize_payment_method(payload.get("payment_method"))
    draft_id = payload.get("draft_id")

    if not draft_id:
        return JsonResponse(
            {
                "status": "error",
                "message": "draft_id is required.",
            },
            status=400,
        )

    draft = _get_draft_for_checkout(draft_id)
    if not draft:
        return JsonResponse(
            {
                "status": "error",
                "message": "Draft not found.",
            },
            status=404,
        )

    is_valid_draft, draft_validation_message = _validate_draft_for_checkout(draft)
    if not is_valid_draft:
        return JsonResponse(
            {
                "status": "error",
                "message": draft_validation_message,
            },
            status=400,
        )

    try:
        client = _build_tap_client()
        charge_payload = _build_draft_charge_payload(
            draft,
            payment_method=payment_method,
        )
        result = client.create_charge(charge_payload)
        checkout_url = _extract_checkout_url(result)
        tap_charge_id = _clean_str(result.get("id"))
        tap_status = _clean_str(result.get("status")).upper()

        with transaction.atomic():
            draft = CompanyOnboardingTransaction.objects.select_for_update().get(id=draft.id)
            _upsert_local_payment_tracking(
                draft=draft,
                request_user=getattr(request, "user", None),
                payment_method=payment_method,
                tap_charge_id=tap_charge_id,
                tap_status=tap_status,
            )

        logger.info(
            "Tap checkout created from draft successfully. draft_id=%s charge_id=%s status=%s",
            draft.id,
            tap_charge_id,
            tap_status,
        )

        return JsonResponse(
            {
                "status": "ok",
                "message": "Tap checkout created successfully.",
                "source": "draft",
                "draft_id": draft.id,
                "draft_status": draft.status,
                "order_reference_id": charge_payload["reference"]["order"],
                "transaction_reference": charge_payload["reference"]["transaction"],
                "payment_method": payment_method,
                "checkout_url": checkout_url,
                "tap_charge_id": tap_charge_id,
                "tap_status": tap_status,
                "raw_response": result,
            },
            status=200,
        )

    except TapConfigurationError as exc:
        logger.warning("Tap checkout configuration error: %s", exc)
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
            },
            status=400,
        )

    except TapAPIError as exc:
        logger.exception("Tap API error while creating checkout")
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
                "tap_status_code": exc.status_code,
                "tap_response": exc.response_data,
            },
            status=502,
        )

    except TapRequestError as exc:
        logger.exception("Tap request error while creating checkout")
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
            },
            status=502,
        )

    except Exception as exc:
        logger.exception("Unexpected error while creating Tap checkout")
        return JsonResponse(
            {
                "status": "error",
                "message": f"Unexpected error while creating Tap checkout: {exc}",
            },
            status=500,
        )