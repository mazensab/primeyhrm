# ============================================================
# Tamara Webhook API — Company Scope
# Mham Cloud
# Path: api/company/payments/tamara_webhook.py
# ------------------------------------------------------------
# Company Webhook Endpoint
# - Receives Tamara notifications for company invoice renewals
# - Verifies tamaraToken when notification token is configured
# - Resolves invoice_id from order_reference_id
# - Creates Payment (SOURCE OF TRUTH)
# - Marks invoice as PAID
# - Applies subscription logic (RENEWAL / UPGRADE / NORMAL)
# - Auto activates company
# - Sends Notification Center success event
# - Idempotent and transaction safe
# ============================================================

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
from typing import Any, Dict, Optional

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing_center.models import (
    CompanySubscription,
    Invoice,
    Payment,
    SubscriptionPlan,
)
from notification_center.services import create_notification

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
    """
    configured_token = _clean_str(getattr(settings, "TAMARA_NOTIFICATION_TOKEN", ""))
    if not configured_token:
        logger.warning(
            "Tamara company webhook received without configured TAMARA_NOTIFICATION_TOKEN. "
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
        logger.warning("Tamara company webhook rejected: missing tamaraToken.")
        return False, "missing_tamara_token"

    if _constant_time_compare(incoming_token, configured_token):
        return True, "direct_match"

    raw_body = request.body or b""
    expected_hmac = hmac.new(
        configured_token.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if _constant_time_compare(incoming_token, expected_hmac):
        return True, "hmac_match"

    logger.warning(
        "Tamara company webhook rejected: invalid tamaraToken. incoming=%s configured=%s",
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
    توحيد طريقة الدفع المحلية من Webhook Tamara.
    """
    raw_method = _clean_str(
        payload.get("payment_method")
        or payload.get("method")
        or payload.get("payment_type")
    ).upper()

    if raw_method == "APPLE_PAY":
        return "APPLE_PAY"
    if raw_method == "STC_PAY":
        return "STC_PAY"

    return "CREDIT_CARD"


def _normalize_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    بناء شكل موحد للبيانات القادمة من Tamara.
    """
    return {
        "event_name": _extract_event_name(payload),
        "order_status": _extract_order_status(payload),
        "order_id": _extract_order_id(payload),
        "order_reference_id": _extract_order_reference_id(payload),
        "checkout_id": _extract_checkout_id(payload),
        "payment_method": _extract_payment_method(payload),
        "raw_payload": payload,
    }


def _extract_invoice_id(order_reference_id: str) -> Optional[int]:
    """
    استخراج invoice_id من order_reference_id.

    أمثلة مدعومة:
    - INVOICE-12-INV-R-12345
    - invoice-12-INV-...
    - INVOICE_12_...
    - invoice:12:...
    - 12
    """
    ref = _clean_str(order_reference_id)
    if not ref:
        return None

    if ref.isdigit():
        return int(ref)

    patterns = [
        r"^INVOICE[-_:](\d+)(?:[-_:].*)?$",
        r".*?INVOICE[-_:](\d+)(?:[-_:].*)?$",
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
    تحويل حالة Tamara إلى حالة داخلية مبسطة.
    """
    status = _clean_str(order_status).upper()

    if status in {"CAPTURED", "FULLY_CAPTURED", "PARTIALLY_CAPTURED", "PAID", "SUCCESS"}:
        return "CAPTURED"

    if status in {"APPROVED", "AUTHORISED", "AUTHORIZED", "NEW", "PENDING", "WAITING", "PROCESSING", "INITIATED"}:
        return "PROCESSING"

    if status in {"DECLINED", "REJECTED", "EXPIRED", "CANCELED", "CANCELLED", "FAILED", "REFUNDED", "FULLY_REFUNDED", "PARTIALLY_REFUNDED"}:
        return "FAILED"

    return "PROCESSING"


def _build_reference_number(normalized: Dict[str, Any]) -> str:
    """
    بناء مرجع Payment محليًا.
    """
    primary = _clean_str(normalized["order_id"]) or _clean_str(normalized["checkout_id"])
    if primary:
        return f"TAMARA-{primary}"
    return f"TAMARA-REF-{_clean_str(normalized['order_reference_id'], 'UNKNOWN')}"


def _ensure_company_active(invoice: Invoice) -> None:
    """
    تفعيل الشركة بعد أول دفع ناجح.
    """
    company = getattr(invoice, "company", None)
    if company and not company.is_active:
        company.is_active = True
        company.save(update_fields=["is_active"])


def _safe_notify_company_payment_success(
    *,
    invoice: Invoice,
    payment: Payment,
    subscription: Optional[CompanySubscription],
    action: str,
) -> None:
    """
    إرسال إشعار نجاح الدفع عبر Notification Center بشكل fail-safe.
    """
    try:
        company = getattr(invoice, "company", None)
        recipient = getattr(company, "owner", None) if company else None

        if not recipient:
            logger.info(
                "Skipping Tamara success notification because company owner is missing. invoice_id=%s",
                getattr(invoice, "id", None),
            )
            return

        plan_name = ""
        if subscription and getattr(subscription, "plan", None):
            plan_name = _clean_str(getattr(subscription.plan, "name", ""))

        title = f"تم تأكيد دفع الفاتورة {invoice.invoice_number}"
        message = (
            f"تم تأكيد سداد الفاتورة {invoice.invoice_number} بنجاح"
            f" بمبلغ {invoice.total_amount} ريال، وتم تحديث حالة الاشتراك."
        )

        create_notification(
            recipient=recipient,
            title=title,
            message=message,
            notification_type="billing",
            severity="success",
            send_email=True,
            send_whatsapp=True,
            link=f"/company/invoices/{invoice.invoice_number}",
            company=company,
            event_code="payment_confirmed_company_activated",
            event_group="billing",
            actor=None,
            target_user=recipient,
            language_code="ar",
            source="api.company.payments.tamara_webhook.success",
            context={
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "payment_id": getattr(payment, "id", None),
                "payment_method": _clean_str(getattr(payment, "method", "")),
                "amount": str(getattr(invoice, "total_amount", "")),
                "billing_reason": _clean_str(getattr(invoice, "billing_reason", "")),
                "action": _clean_str(action),
                "company_name": _clean_str(getattr(company, "name", "")) if company else "",
                "company_active": bool(getattr(company, "is_active", False)) if company else False,
                "subscription_status": _clean_str(getattr(subscription, "status", "")) if subscription else "",
                "active_plan": plan_name,
            },
            target_object=invoice,
            template_key="payment_confirmed_company_activated",
        )

    except Exception:
        logger.warning(
            "Failed to dispatch Tamara success notification for invoice_id=%s",
            getattr(invoice, "id", None),
            exc_info=True,
        )


def _apply_subscription_logic(invoice: Invoice) -> Optional[CompanySubscription]:
    """
    منطق الاشتراك مطابق لروح confirm_cash_payment الحالية:
    - UPGRADE
    - RENEWAL
    - NORMAL
    """
    subscription = invoice.subscription

    if not subscription:
        return None

    if invoice.billing_reason == "UPGRADE":
        snapshot = invoice.subscription_snapshot or {}
        target_plan_data = snapshot.get("target_plan") or {}
        target_plan_id = target_plan_data.get("id")

        if not target_plan_id:
            raise ValueError("Upgrade target plan not found in invoice snapshot")

        try:
            target_plan = SubscriptionPlan.objects.get(id=target_plan_id)
        except SubscriptionPlan.DoesNotExist as exc:
            raise ValueError("Target upgrade plan does not exist") from exc

        subscription.plan = target_plan

        if subscription.status != "ACTIVE":
            subscription.status = "ACTIVE"

        if not subscription.start_date:
            subscription.start_date = now().date()

        subscription.save(update_fields=["plan", "status", "start_date"])
        return subscription

    if invoice.billing_reason == "RENEWAL":
        subscription.status = "EXPIRED"
        subscription.save(update_fields=["status"])

        new_subscription = CompanySubscription.objects.create(
            company=subscription.company,
            plan=subscription.plan,
            start_date=now().date(),
            end_date=subscription.end_date,
            status="ACTIVE",
            apps_snapshot=subscription.apps_snapshot,
        )
        return new_subscription

    if subscription.status != "ACTIVE":
        subscription.status = "ACTIVE"
        subscription.start_date = subscription.start_date or now().date()
        subscription.save(update_fields=["status", "start_date"])

    return subscription


@transaction.atomic
def _confirm_company_invoice_payment(normalized: Dict[str, Any]) -> Dict[str, Any]:
    """
    تأكيد دفع الفاتورة عند وصول نجاح نهائي من Tamara.
    """
    invoice_id = _extract_invoice_id(normalized["order_reference_id"])
    if not invoice_id:
        raise ValueError("Unable to resolve invoice_id from order_reference_id")

    invoice = (
        Invoice.objects
        .select_for_update()
        .select_related("subscription__plan", "company__owner")
        .filter(id=invoice_id)
        .first()
    )
    if not invoice:
        raise Invoice.DoesNotExist("Invoice not found")

    if invoice.status == "PAID":
        existing_payment = (
            Payment.objects
            .filter(invoice=invoice)
            .order_by("-paid_at", "-id")
            .first()
        )

        return {
            "handled": True,
            "action": "already_confirmed",
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "payment_id": existing_payment.id if existing_payment else None,
            "payment_method": existing_payment.method if existing_payment else None,
            "billing_reason": invoice.billing_reason,
            "subscription_status": invoice.subscription.status if invoice.subscription else None,
            "company_active": invoice.company.is_active if invoice.company else False,
        }

    payment = Payment.objects.create(
        invoice=invoice,
        amount=invoice.total_amount,
        method=normalized["payment_method"],
        reference_number=_build_reference_number(normalized),
        paid_at=now(),
        created_by=None,
    )

    invoice.status = "PAID"
    invoice.save(update_fields=["status"])

    subscription = _apply_subscription_logic(invoice)
    _ensure_company_active(invoice)

    transaction.on_commit(
        lambda: _safe_notify_company_payment_success(
            invoice=invoice,
            payment=payment,
            subscription=subscription,
            action="payment_confirmed_and_activated",
        )
    )

    return {
        "handled": True,
        "action": "payment_confirmed_and_activated",
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "payment_id": payment.id,
        "payment_method": payment.method,
        "billing_reason": invoice.billing_reason,
        "subscription_status": subscription.status if subscription else None,
        "active_plan": subscription.plan.name if subscription and subscription.plan else None,
        "company_active": invoice.company.is_active if invoice.company else False,
    }


# ============================================================
# API
# ============================================================

@csrf_exempt
@require_POST
def tamara_webhook(request):
    """
    استقبال Webhook من Tamara لفواتير الشركة.

    ملاحظات:
    - لا يحتاج login
    - CSRF disabled لأنه endpoint خارجي
    - النجاح النهائي فقط هو الذي يؤكد الفاتورة
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
        logger.warning("Tamara company webhook received empty or invalid JSON payload.")
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
                "Tamara company webhook rejected: missing order identifiers. payload=%s",
                payload,
            )
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Missing Tamara order identifiers.",
                },
                status=400,
            )

        mapped_gateway_status = _map_gateway_status(normalized["order_status"])

        response_payload: Dict[str, Any] = {
            "verification_mode": verification_mode,
            "event_name": normalized["event_name"],
            "order_status": normalized["order_status"],
            "mapped_gateway_status": mapped_gateway_status,
            "order_id": normalized["order_id"],
            "order_reference_id": normalized["order_reference_id"],
            "checkout_id": normalized["checkout_id"],
        }

        if mapped_gateway_status == "CAPTURED":
            result = _confirm_company_invoice_payment(normalized)
            response_payload.update(result)

            logger.info(
                "Tamara company webhook success. invoice_id=%s order_id=%s ref=%s action=%s",
                result.get("invoice_id"),
                normalized["order_id"],
                normalized["order_reference_id"],
                result.get("action"),
            )

            return JsonResponse(
                {
                    "status": "ok",
                    "message": "Tamara company webhook processed successfully.",
                    **response_payload,
                },
                status=200,
            )

        if mapped_gateway_status == "FAILED":
            logger.warning(
                "Tamara company webhook failed payment. order_id=%s ref=%s status=%s",
                normalized["order_id"],
                normalized["order_reference_id"],
                normalized["order_status"],
            )
            return JsonResponse(
                {
                    "status": "ok",
                    "message": "Tamara company webhook received as failed payment state.",
                    "handled": True,
                    "action": "payment_failed",
                    **response_payload,
                },
                status=200,
            )

        logger.info(
            "Tamara company webhook pending state. order_id=%s ref=%s status=%s",
            normalized["order_id"],
            normalized["order_reference_id"],
            normalized["order_status"],
        )
        return JsonResponse(
            {
                "status": "ok",
                "message": "Tamara company webhook received as pending state.",
                "handled": True,
                "action": "payment_pending",
                **response_payload,
            },
            status=200,
        )

    except Invoice.DoesNotExist:
        logger.warning(
            "Tamara company webhook failed: invoice not found. ref=%s",
            _extract_order_reference_id(payload),
        )
        return JsonResponse(
            {
                "status": "error",
                "message": "Invoice not found for Tamara company webhook.",
            },
            status=404,
        )

    except Exception as exc:
        logger.exception("Unexpected error while processing Tamara company webhook.")
        return JsonResponse(
            {
                "status": "error",
                "message": "Unexpected server error while processing Tamara company webhook.",
                "details": str(exc) if settings.DEBUG else "",
            },
            status=500,
        )