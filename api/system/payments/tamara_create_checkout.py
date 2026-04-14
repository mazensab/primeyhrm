# ============================================================
# Tamara Create Checkout API
# Mham Cloud
# Path: api/system/payments/tamara_create_checkout.py
# ------------------------------------------------------------
# System/Public Payment API
# - Creates Tamara checkout session
# - Supports onboarding draft flow directly
# - Builds order_reference_id as DRAFT-<id>
# - Returns checkout_url and tamara identifiers
# - Does NOT mark invoice as paid directly here
# - Does NOT activate subscription directly here
# - Supports public onboarding draft flow safely
# - Returns safer register success/cancel/failure URLs for frontend
# ============================================================

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing_center.models import CompanyOnboardingTransaction
from billing_center.services.tamara_checkout_service import (
    TamaraCheckoutRemoteError,
    TamaraCheckoutService,
    TamaraCheckoutValidationError,
)

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


def _normalize_payment_method(value: Any) -> str:
    """
    توحيد طريقة الدفع القادمة من الطلب.
    """
    method = _clean_str(value).upper()
    if not method:
        return "TAMARA"
    return method


def _is_system_user(request) -> bool:
    """
    حارس بسيط لمستخدمي النظام.
    """
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False):
        return True
    if getattr(user, "is_staff", False):
        return True

    return False


def _extract_invoice_like_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    استخراج بيانات invoice-like بشكل مرن.

    يدعم حالتين:
    1) تمرير payload مباشر يحتوي الحقول نفسها
    2) تمرير invoice_data داخله
    """
    nested = payload.get("invoice_data")
    if isinstance(nested, dict) and nested:
        return nested

    return payload


def _get_frontend_base_url() -> str:
    return _clean_str(
        getattr(settings, "FRONTEND_BASE_URL", None),
        "http://localhost:3000",
    ).rstrip("/")


def _get_backend_base_url() -> str:
    return _clean_str(
        getattr(settings, "BACKEND_BASE_URL", None)
        or getattr(settings, "APP_BASE_URL", None)
        or getattr(settings, "SITE_BASE_URL", None),
        "http://127.0.0.1:8000",
    ).rstrip("/")


def _build_register_return_url(
    *,
    draft_id: int,
    payment: str,
    payment_method: str = "TAMARA",
    gateway_status: str | None = None,
    gateway_transaction_id: str | None = None,
) -> str:
    """
    بناء رابط رجوع مناسب لصفحة /register
    حتى يفهم الفرونت حالة العملية بعد العودة من تمارا.
    """
    base = f"{_get_frontend_base_url()}/register"

    query_data = {
        "draft_id": str(draft_id),
        "payment_method": _normalize_payment_method(payment_method),
        "payment": _clean_str(payment),
    }

    if _clean_str(gateway_status):
        query_data["gateway_status"] = _clean_str(gateway_status).upper()

    if _clean_str(gateway_transaction_id):
        query_data["gateway_transaction_id"] = _clean_str(gateway_transaction_id)

    query = urlencode(query_data)
    return f"{base}?{query}"


def _get_default_success_url(
    *,
    draft_id: Optional[int] = None,
    payment_method: str = "TAMARA",
    gateway_transaction_id: str | None = None,
    gateway_status: str | None = None,
) -> str:
    if draft_id:
        return _build_register_return_url(
            draft_id=draft_id,
            payment="success",
            payment_method=payment_method,
            gateway_status=gateway_status or "APPROVED",
            gateway_transaction_id=gateway_transaction_id,
        )

    return _clean_str(
        getattr(settings, "TAMARA_SUCCESS_URL", None)
        or f"{_get_frontend_base_url()}/billing/payment/success"
    )


def _get_default_cancel_url(
    *,
    draft_id: Optional[int] = None,
    payment_method: str = "TAMARA",
) -> str:
    if draft_id:
        return _build_register_return_url(
            draft_id=draft_id,
            payment="cancelled",
            payment_method=payment_method,
        )

    return _clean_str(
        getattr(settings, "TAMARA_CANCEL_URL", None)
        or f"{_get_frontend_base_url()}/billing/payment/cancel"
    )


def _get_default_failure_url(
    *,
    draft_id: Optional[int] = None,
    payment_method: str = "TAMARA",
) -> str:
    if draft_id:
        return _build_register_return_url(
            draft_id=draft_id,
            payment="failed",
            payment_method=payment_method,
        )

    return _clean_str(
        getattr(settings, "TAMARA_FAILURE_URL", None)
        or _get_default_cancel_url()
    )


def _get_default_notification_url() -> str:
    return _clean_str(
        getattr(settings, "TAMARA_WEBHOOK_URL", None)
        or f"{_get_backend_base_url()}/api/system/payments/tamara/webhook/"
    )


def _build_draft_reference(draft_id: int) -> str:
    """
    المرجع المحلي الذي سيعود لاحقًا عبر webhook.
    """
    return f"DRAFT-{draft_id}"


def _build_draft_invoice_data(
    draft: CompanyOnboardingTransaction,
    *,
    payment_method: str,
) -> Dict[str, Any]:
    """
    تحويل draft onboarding الحالية إلى payload متوافق مع TamaraCheckoutService.
    """
    company_name = _clean_str(getattr(draft, "company_name", None), "Mham Cloud")
    plan_name = _clean_str(getattr(getattr(draft, "plan", None), "name", None), "Primey Plan")
    admin_name = _clean_str(getattr(draft, "admin_name", None), "Customer")
    admin_email = _clean_str(getattr(draft, "admin_email", None))
    phone = _clean_str(getattr(draft, "phone", None))
    city = _clean_str(getattr(draft, "city", None), "Riyadh")
    total_amount = getattr(draft, "total_amount", 0) or 0
    vat_amount = getattr(draft, "vat_amount", 0) or 0
    discount_amount = getattr(draft, "discount_amount", 0) or 0
    base_price = getattr(draft, "base_price", total_amount) or total_amount
    national_address = getattr(draft, "national_address", {}) or {}

    customer_first_name = admin_name.split(" ")[0] if admin_name else company_name
    customer_last_name = (
        " ".join(admin_name.split(" ")[1:]).strip()
        if admin_name and " " in admin_name
        else "Customer"
    )

    order_reference_id = _build_draft_reference(draft.id)

    invoice_data = {
        "draft_id": draft.id,
        "payment_method": payment_method,
        "order_reference_id": order_reference_id,
        "invoice_number": order_reference_id,
        "reference": order_reference_id,
        "description": f"{plan_name} Subscription for {company_name}",
        "title": f"{company_name} — {plan_name}",
        "plan_name": plan_name,
        "currency": "SAR",
        "country_code": "SA",
        "locale": getattr(settings, "TAMARA_LOCALE", "en_US"),
        "total_amount": str(total_amount),
        "amount": str(total_amount),
        "grand_total": str(total_amount),
        "tax_amount": str(vat_amount),
        "shipping_amount": "0.00",
        "discount_amount": str(discount_amount),
        "customer_first_name": customer_first_name,
        "customer_last_name": customer_last_name,
        "customer_email": admin_email or _clean_str(getattr(draft, "email", None)),
        "customer_phone": phone,
        "company_name": company_name,
        "company_email": _clean_str(getattr(draft, "email", None)),
        "company_phone": phone,
        "city": city,
        "success_url": _get_default_success_url(
            draft_id=draft.id,
            payment_method=payment_method,
        ),
        "cancel_url": _get_default_cancel_url(
            draft_id=draft.id,
            payment_method=payment_method,
        ),
        "failure_url": _get_default_failure_url(
            draft_id=draft.id,
            payment_method=payment_method,
        ),
        "notification_url": _get_default_notification_url(),
        "platform": "Mham Cloud",
        "items": [
            {
                "reference_id": order_reference_id,
                "name": f"{plan_name} Subscription",
                "description": f"{plan_name} - {getattr(draft, 'duration', 'subscription')}",
                "sku": order_reference_id,
                "quantity": 1,
                "unit_price": str(base_price),
                "amount": str(base_price),
                "tax_amount": str(vat_amount),
            }
        ],
        "billing_address": {
            "first_name": customer_first_name,
            "last_name": customer_last_name,
            "line1": _clean_str(national_address.get("street")) or company_name,
            "line2": _clean_str(national_address.get("district")),
            "city": city,
            "region": city,
            "country_code": "SA",
            "phone_number": phone,
        },
        "shipping_address": {
            "first_name": customer_first_name,
            "last_name": customer_last_name,
            "line1": _clean_str(national_address.get("street")) or company_name,
            "line2": _clean_str(national_address.get("district")),
            "city": city,
            "region": city,
            "country_code": "SA",
            "phone_number": phone,
        },
    }

    return invoice_data


def _validate_direct_payload(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    تحقق أولي قبل استدعاء الخدمة في حالة direct invoice-like payload.
    """
    if not isinstance(data, dict) or not data:
        return False, "No invoice data provided."

    customer_email = _clean_str(
        data.get("customer_email")
        or (data.get("customer") or {}).get("email")
        or (data.get("company") or {}).get("email")
    )
    customer_phone = _clean_str(
        data.get("customer_phone")
        or (data.get("customer") or {}).get("phone")
        or (data.get("company") or {}).get("phone")
        or (data.get("company") or {}).get("mobile_number")
    )

    amount = data.get("total_amount") or data.get("amount") or data.get("grand_total")

    if not amount:
        return False, "Tamara checkout requires total_amount or amount."

    if not customer_email:
        return False, "Tamara checkout requires customer_email."

    if not customer_phone:
        return False, "Tamara checkout requires customer_phone."

    return True, ""


def _get_draft_for_checkout(draft_id: Any) -> Optional[CompanyOnboardingTransaction]:
    """
    جلب draft onboarding الحالية إن تم تمرير draft_id.
    """
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
    """
    التحقق من صلاحية draft قبل إنشاء checkout.
    """
    if draft.status not in {"DRAFT", "CONFIRMED", "PENDING_PAYMENT"}:
        return False, "Draft status does not allow Tamara checkout."

    if not _clean_str(getattr(draft, "admin_email", None)):
        return False, "Draft admin_email is required for Tamara checkout."

    if not _clean_str(getattr(draft, "phone", None)):
        return False, "Draft phone is required for Tamara checkout."

    if not getattr(draft, "total_amount", None):
        return False, "Draft total_amount is required for Tamara checkout."

    return True, ""


# ============================================================
# API
# ============================================================

@csrf_exempt
@require_POST
def tamara_create_checkout(request):
    """
    إنشاء Checkout Session في Tamara.

    يدعم حالتين:
    1) payload مباشر invoice-like
    2) تمرير draft_id لربط Tamara مع onboarding flow الحالي

    ملاحظة:
    - public onboarding draft flow مسموح بدون login
    - direct/system mode يبقى متاحًا للمستخدمين الداخليين فقط
    """

    if not getattr(settings, "TAMARA_ENABLED", False):
        return JsonResponse(
            {
                "status": "error",
                "message": "Tamara payment gateway is disabled.",
            },
            status=503,
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

    try:
        service = TamaraCheckoutService()

        # ====================================================
        # Draft Flow — Public + Internal
        # ====================================================
        if draft_id:
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

            invoice_data = _build_draft_invoice_data(
                draft,
                payment_method=payment_method,
            )

            result = service.create_checkout(invoice_data)

            logger.info(
                "Tamara checkout created from draft successfully. draft_id=%s order_id=%s checkout_id=%s",
                draft.id,
                result.tamara_order_id,
                result.tamara_checkout_id,
            )

            return JsonResponse(
                {
                    "status": "ok",
                    "message": "Tamara checkout created successfully.",
                    "source": "draft",
                    "draft_id": draft.id,
                    "draft_status": draft.status,
                    "order_reference_id": invoice_data["order_reference_id"],
                    "payment_method": payment_method,
                    "checkout_url": result.checkout_url,
                    "tamara_order_id": result.tamara_order_id,
                    "tamara_checkout_id": result.tamara_checkout_id,
                    "tamara_status": result.status,
                    "success_return_url": invoice_data["success_url"],
                    "cancel_return_url": invoice_data["cancel_url"],
                    "failure_return_url": invoice_data["failure_url"],
                    "raw_response": result.raw_response,
                },
                status=200,
            )

        # ====================================================
        # Direct invoice-like payload — Internal only
        # ====================================================
        if not _is_system_user(request):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "You do not have permission to create Tamara checkout from system scope.",
                },
                status=403,
            )

        invoice_data = _extract_invoice_like_data(payload)

        is_valid, validation_message = _validate_direct_payload(invoice_data)
        if not is_valid:
            return JsonResponse(
                {
                    "status": "error",
                    "message": validation_message,
                },
                status=400,
            )

        if (
            not _clean_str(invoice_data.get("order_reference_id"))
            and invoice_data.get("draft_id")
        ):
            invoice_data["order_reference_id"] = _build_draft_reference(
                int(invoice_data["draft_id"])
            )

        result = service.create_checkout(invoice_data)

        logger.info(
            "Tamara checkout created successfully. order_id=%s checkout_id=%s",
            result.tamara_order_id,
            result.tamara_checkout_id,
        )

        return JsonResponse(
            {
                "status": "ok",
                "message": "Tamara checkout created successfully.",
                "source": "direct",
                "order_reference_id": invoice_data.get("order_reference_id"),
                "checkout_url": result.checkout_url,
                "tamara_order_id": result.tamara_order_id,
                "tamara_checkout_id": result.tamara_checkout_id,
                "tamara_status": result.status,
                "raw_response": result.raw_response,
            },
            status=200,
        )

    except TamaraCheckoutValidationError as exc:
        logger.warning("Tamara checkout validation error: %s", exc)
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
            },
            status=400,
        )

    except TamaraCheckoutRemoteError as exc:
        logger.exception("Tamara remote error while creating checkout")
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
            },
            status=502,
        )

    except Exception as exc:
        logger.exception("Unexpected error while creating Tamara checkout")
        return JsonResponse(
            {
                "status": "error",
                "message": "Unexpected server error while creating Tamara checkout.",
                "details": str(exc) if settings.DEBUG else "",
            },
            status=500,
        )