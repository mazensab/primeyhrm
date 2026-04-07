# ============================================================
# Tamara Create Checkout API — Company Scope
# Mham Cloud
# Path: api/company/payments/tamara_create_checkout.py
# ------------------------------------------------------------
# Company Payment API
# - Creates Tamara checkout session for existing company invoice
# - Resolves invoice by invoice_id or invoice_number
# - Restricts access to active company context
# - Builds order_reference_id linked to invoice
# - Does NOT mark invoice as paid
# - Does NOT activate subscription directly
# ============================================================

from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from billing_center.models import Invoice
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


def _to_decimal(value: Any, default: str = "0.00") -> Decimal:
    """
    تحويل آمن إلى Decimal.
    """
    try:
        if value is None or value == "":
            return Decimal(default)
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _normalize_payment_method(value: Any) -> str:
    """
    توحيد طريقة الدفع القادمة من الواجهة.
    """
    method = _clean_str(value).upper()
    if not method:
        return "TAMARA"

    allowed = {
        "BANK_TRANSFER",
        "CREDIT_CARD",
        "STC_PAY",
        "APPLE_PAY",
        "TAMARA",
    }

    return method if method in allowed else "TAMARA"


def _get_active_company_id(request) -> Optional[int]:
    """
    محاولة استخراج الشركة النشطة من request / session بشكل مرن.
    """
    possible_values = [
        getattr(request, "active_company_id", None),
        getattr(request, "company_id", None),
        request.session.get("active_company_id"),
        request.session.get("company_id"),
        request.session.get("active_company"),
    ]

    active_company = getattr(request, "active_company", None)
    if active_company is not None:
        possible_values.insert(0, getattr(active_company, "id", active_company))

    for value in possible_values:
        try:
            if value:
                return int(value)
        except (TypeError, ValueError):
            continue

    return None


def _get_invoice_identifier(payload: Dict[str, Any]) -> tuple[Optional[int], Optional[str]]:
    """
    استخراج invoice_id أو invoice_number.
    """
    invoice_id = payload.get("invoice_id")
    invoice_number = _clean_str(payload.get("invoice_number"))

    try:
        invoice_id = int(invoice_id) if invoice_id is not None else None
    except (TypeError, ValueError):
        invoice_id = None

    return invoice_id, invoice_number or None


def _get_invoice_for_company(
    *,
    company_id: int,
    invoice_id: Optional[int],
    invoice_number: Optional[str],
) -> Optional[Invoice]:
    """
    جلب الفاتورة داخل company scope فقط.
    """
    queryset = Invoice.objects.select_related("company", "subscription__plan").filter(
        company_id=company_id
    )

    if invoice_id:
        return queryset.filter(id=invoice_id).first()

    if invoice_number:
        return queryset.filter(invoice_number=invoice_number).first()

    return None


def _get_invoice_reference(invoice: Invoice) -> str:
    """
    المرجع المحلي الذي سيُرسل إلى Tamara ويرتبط بالفاتورة.
    """
    return f"INVOICE-{invoice.id}-{invoice.invoice_number}"


def _get_company_name(invoice: Invoice) -> str:
    company = getattr(invoice, "company", None)
    return _clean_str(getattr(company, "name", None), "Primey Company")


def _get_plan_name(invoice: Invoice) -> str:
    subscription = getattr(invoice, "subscription", None)
    plan = getattr(subscription, "plan", None)
    return _clean_str(getattr(plan, "name", None), "Subscription Plan")


def _get_customer_email(request, invoice: Invoice, payload: Dict[str, Any]) -> str:
    """
    استخراج البريد من:
    - payload
    - user session
    - company object
    """
    company = getattr(invoice, "company", None)
    candidates = [
        payload.get("customer_email"),
        getattr(request.user, "email", None),
        getattr(company, "email", None),
        getattr(company, "company_email", None),
        payload.get("company_email"),
    ]

    for value in candidates:
        cleaned = _clean_str(value)
        if cleaned:
            return cleaned

    return ""


def _get_customer_phone(request, invoice: Invoice, payload: Dict[str, Any]) -> str:
    """
    استخراج رقم الجوال من:
    - payload
    - company object
    - user object
    """
    company = getattr(invoice, "company", None)
    candidates = [
        payload.get("customer_phone"),
        payload.get("phone"),
        getattr(company, "phone", None),
        getattr(company, "mobile_number", None),
        getattr(company, "phone_number", None),
        getattr(company, "contact_phone", None),
        getattr(request.user, "mobile_number", None),
        getattr(request.user, "phone", None),
    ]

    for value in candidates:
        cleaned = _clean_str(value)
        if cleaned:
            return cleaned

    return ""


def _get_customer_names(request, invoice: Invoice) -> tuple[str, str]:
    """
    استخراج اسم العميل بطريقة مرنة.
    """
    first_name = _clean_str(getattr(request.user, "first_name", None))
    last_name = _clean_str(getattr(request.user, "last_name", None))

    if first_name:
        return first_name, last_name or "Customer"

    full_name = _clean_str(
        getattr(request.user, "get_full_name", lambda: "")()
    )
    if full_name:
        parts = full_name.split()
        if len(parts) == 1:
            return parts[0], "Customer"
        return parts[0], " ".join(parts[1:])

    return _get_company_name(invoice), "Customer"


def _get_invoice_money(invoice: Invoice) -> dict[str, Decimal]:
    """
    احتساب القيم بنفس روح invoice detail الحالية.
    """
    subtotal = _to_decimal(getattr(invoice, "subtotal_amount", 0))
    discount = _to_decimal(getattr(invoice, "discount_amount", 0))
    total = _to_decimal(getattr(invoice, "total_amount", 0))
    vat = total - subtotal + discount

    if vat < 0:
        vat = Decimal("0.00")

    return {
        "subtotal": subtotal,
        "discount": discount,
        "vat": vat,
        "total": total,
    }


def _build_backend_base_url(request) -> str:
    configured = _clean_str(
        getattr(settings, "BACKEND_BASE_URL", None)
        or getattr(settings, "APP_BASE_URL", None)
        or getattr(settings, "SITE_BASE_URL", None)
    )
    if configured:
        return configured.rstrip("/")

    scheme = "https" if request.is_secure() else "http"
    host = request.get_host()
    return f"{scheme}://{host}".rstrip("/")


def _build_invoice_urls(request, invoice: Invoice) -> dict[str, str]:
    """
    بناء روابط الرجوع الخاصة بصفحة فاتورة الشركة.
    """
    frontend_base = _clean_str(
        getattr(settings, "FRONTEND_BASE_URL", None),
        "https://mhamcloud.com",
    ).rstrip("/")
    backend_base = _build_backend_base_url(request)

    invoice_path = f"/company/invoices/{invoice.invoice_number}"

    success_url = _clean_str(
        getattr(settings, "COMPANY_TAMARA_SUCCESS_URL", None),
        f"{frontend_base}{invoice_path}?payment=success",
    )
    cancel_url = _clean_str(
        getattr(settings, "COMPANY_TAMARA_CANCEL_URL", None),
        f"{frontend_base}{invoice_path}?payment=cancelled",
    )
    failure_url = _clean_str(
        getattr(settings, "COMPANY_TAMARA_FAILURE_URL", None),
        f"{frontend_base}{invoice_path}?payment=failed",
    )
    notification_url = _clean_str(
        getattr(settings, "COMPANY_TAMARA_WEBHOOK_URL", None)
        or getattr(settings, "TAMARA_COMPANY_WEBHOOK_URL", None)
        or getattr(settings, "TAMARA_WEBHOOK_URL", None),
        f"{backend_base}/api/company/payments/tamara/webhook/",
    )

    return {
        "success_url": success_url,
        "cancel_url": cancel_url,
        "failure_url": failure_url,
        "notification_url": notification_url,
    }


def _build_invoice_checkout_payload(
    request,
    invoice: Invoice,
    payload: Dict[str, Any],
    *,
    payment_method: str,
) -> Dict[str, Any]:
    """
    تحويل الفاتورة الحالية إلى payload متوافق مع TamaraCheckoutService.
    """
    company = getattr(invoice, "company", None)
    customer_email = _get_customer_email(request, invoice, payload)
    customer_phone = _get_customer_phone(request, invoice, payload)

    if not customer_email:
        raise TamaraCheckoutValidationError(
            "Customer email is required for Tamara checkout."
        )

    if not customer_phone:
        raise TamaraCheckoutValidationError(
            "Customer phone number is required for Tamara checkout."
        )

    money = _get_invoice_money(invoice)
    if money["total"] <= Decimal("0.00"):
        raise TamaraCheckoutValidationError(
            "Invoice total amount must be greater than zero."
        )

    first_name, last_name = _get_customer_names(request, invoice)
    urls = _build_invoice_urls(request, invoice)

    company_name = _get_company_name(invoice)
    plan_name = _get_plan_name(invoice)
    city = _clean_str(
        getattr(company, "city", None)
        or payload.get("city"),
        "Riyadh",
    )
    line1 = _clean_str(
        getattr(company, "address", None)
        or payload.get("address_line1"),
        company_name,
    )
    line2 = _clean_str(payload.get("address_line2"))

    order_reference_id = _get_invoice_reference(invoice)

    return {
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "payment_method": payment_method,
        "order_reference_id": order_reference_id,
        "reference": order_reference_id,
        "description": f"Invoice payment for {invoice.invoice_number}",
        "title": f"{company_name} — {plan_name}",
        "plan_name": plan_name,
        "currency": "SAR",
        "country_code": "SA",
        "locale": getattr(settings, "TAMARA_LOCALE", "en_US"),
        "total_amount": str(money["total"]),
        "amount": str(money["total"]),
        "grand_total": str(money["total"]),
        "tax_amount": str(money["vat"]),
        "shipping_amount": "0.00",
        "discount_amount": str(money["discount"]),
        "discount_name": "Invoice Discount",
        "customer_first_name": first_name,
        "customer_last_name": last_name,
        "customer_email": customer_email,
        "customer_phone": customer_phone,
        "company_name": company_name,
        "company_email": _clean_str(getattr(company, "email", None)),
        "company_phone": customer_phone,
        "city": city,
        "success_url": urls["success_url"],
        "cancel_url": urls["cancel_url"],
        "failure_url": urls["failure_url"],
        "notification_url": urls["notification_url"],
        "platform": "Mham Cloud",
        "items": [
            {
                "reference_id": order_reference_id,
                "type": "Digital",
                "name": "Subscription Renewal Invoice",
                "description": f"{plan_name} — {invoice.invoice_number}",
                "sku": invoice.invoice_number,
                "quantity": 1,
                "unit_price": str(money["subtotal"]),
                "amount": str(money["subtotal"]),
                "tax_amount": str(money["vat"]),
                "total_amount": str(money["total"]),
            }
        ],
        "billing_address": {
            "first_name": first_name,
            "last_name": last_name,
            "line1": line1,
            "line2": line2,
            "city": city,
            "region": city,
            "country_code": "SA",
            "phone_number": customer_phone,
        },
        "shipping_address": {
            "first_name": first_name,
            "last_name": last_name,
            "line1": line1,
            "line2": line2,
            "city": city,
            "region": city,
            "country_code": "SA",
            "phone_number": customer_phone,
        },
    }


# ============================================================
# API
# ============================================================

@login_required
@require_POST
def tamara_create_checkout(request):
    """
    إنشاء Checkout Session في Tamara لفاتورة شركة موجودة.

    المدخلات المقبولة:
    - invoice_id
    - أو invoice_number

    اختياري:
    - payment_method
    - customer_email
    - customer_phone
    """
    if not getattr(settings, "TAMARA_ENABLED", False):
        return JsonResponse(
            {
                "status": "error",
                "message": "Tamara payment gateway is disabled.",
            },
            status=503,
        )

    active_company_id = _get_active_company_id(request)
    if not active_company_id:
        return JsonResponse(
            {
                "status": "error",
                "message": "No active company context found.",
            },
            status=400,
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

    invoice_id, invoice_number = _get_invoice_identifier(payload)
    if not invoice_id and not invoice_number:
        return JsonResponse(
            {
                "status": "error",
                "message": "invoice_id or invoice_number is required.",
            },
            status=400,
        )

    invoice = _get_invoice_for_company(
        company_id=active_company_id,
        invoice_id=invoice_id,
        invoice_number=invoice_number,
    )
    if not invoice:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invoice not found for the active company.",
            },
            status=404,
        )

    if _clean_str(invoice.status).upper() == "PAID":
        return JsonResponse(
            {
                "status": "error",
                "message": "Invoice is already paid.",
            },
            status=409,
        )

    payment_method = _normalize_payment_method(payload.get("payment_method"))

    try:
        invoice_data = _build_invoice_checkout_payload(
            request,
            invoice,
            payload,
            payment_method=payment_method,
        )

        service = TamaraCheckoutService()
        result = service.create_checkout(invoice_data)

        logger.info(
            "Company Tamara checkout created successfully. company_id=%s invoice_id=%s order_id=%s checkout_id=%s",
            active_company_id,
            invoice.id,
            result.tamara_order_id,
            result.tamara_checkout_id,
        )

        return JsonResponse(
            {
                "status": "ok",
                "message": "Tamara checkout created successfully.",
                "source": "company_invoice",
                "company_id": active_company_id,
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "order_reference_id": invoice_data["order_reference_id"],
                "payment_method": payment_method,
                "checkout_url": result.checkout_url,
                "tamara_order_id": result.tamara_order_id,
                "tamara_checkout_id": result.tamara_checkout_id,
                "tamara_status": result.status,
                "raw_response": result.raw_response,
            },
            status=200,
        )

    except TamaraCheckoutValidationError as exc:
        logger.warning(
            "Company Tamara checkout validation error. company_id=%s invoice_id=%s error=%s",
            active_company_id,
            invoice.id,
            exc,
        )
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
            },
            status=400,
        )

    except TamaraCheckoutRemoteError as exc:
        logger.exception(
            "Company Tamara remote error while creating checkout. company_id=%s invoice_id=%s",
            active_company_id,
            invoice.id,
        )
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
            },
            status=502,
        )

    except Exception as exc:
        logger.exception(
            "Unexpected error while creating company Tamara checkout. company_id=%s invoice_id=%s",
            active_company_id,
            invoice.id,
        )
        return JsonResponse(
            {
                "status": "error",
                "message": "Unexpected server error while creating Tamara checkout.",
                "details": str(exc) if settings.DEBUG else "",
            },
            status=500,
        )