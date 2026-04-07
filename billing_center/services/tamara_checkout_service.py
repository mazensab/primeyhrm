# ============================================================
# Tamara Checkout Service
# Mham Cloud
# Path: billing_center/services/tamara_checkout_service.py
# ------------------------------------------------------------
# Service Layer only
# - Builds Tamara checkout payload from local invoice/draft data
# - Calls Tamara client
# - Returns normalized result
# - Does NOT activate subscription
# - Does NOT mark invoice as paid
# ------------------------------------------------------------
# Notes:
# - This file is intentionally defensive and integration-safe.
# - It supports invoice-like objects and dict payloads.
# ============================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Iterable, Optional

from django.conf import settings

from payment_gateways.tamara.client import (
    TamaraClient,
    TamaraConfig,
    TamaraConfigurationError,
    TamaraError,
)

logger = logging.getLogger(__name__)


# ============================================================
# Constants
# ============================================================

DEFAULT_COUNTRY_CODE = "SA"
DEFAULT_CURRENCY = "SAR"
DEFAULT_LOCALE = "en_US"


# ============================================================
# Exceptions
# ============================================================

class TamaraCheckoutServiceError(Exception):
    """Base exception for Tamara checkout service."""


class TamaraCheckoutValidationError(TamaraCheckoutServiceError):
    """Raised when local data is insufficient to create checkout."""


class TamaraCheckoutRemoteError(TamaraCheckoutServiceError):
    """Raised when Tamara API call fails."""


# ============================================================
# DTO
# ============================================================

@dataclass(slots=True)
class TamaraCheckoutResult:
    """
    النتيجة الموحّدة بعد إنشاء Checkout Session.
    """

    success: bool
    checkout_url: str
    tamara_order_id: str
    tamara_checkout_id: Optional[str]
    status: Optional[str]
    raw_response: Dict[str, Any]


# ============================================================
# Helpers
# ============================================================

def _to_decimal(value: Any, *, default: str = "0.00") -> Decimal:
    """
    تحويل آمن إلى Decimal.
    """
    if value is None or value == "":
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def _quantize_money(amount: Any) -> Decimal:
    """
    توحيد الدقة المالية إلى منزلتين عشريتين.
    """
    return _to_decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _decimal_to_number(amount: Any) -> float:
    """
    Tamara expects numeric amount values, not strings.
    """
    return float(_quantize_money(amount))


def _money(amount: Any, currency: str = DEFAULT_CURRENCY) -> Dict[str, Any]:
    """
    بناء كائن المبلغ بالشكل المطلوب لـ Tamara.
    """
    return {
        "amount": _decimal_to_number(amount),
        "currency": currency or DEFAULT_CURRENCY,
    }


def _clean_str(value: Any, default: str = "") -> str:
    """
    تحويل آمن إلى string مع trim.
    """
    if value is None:
        return default
    return str(value).strip()


def _safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """
    قراءة قيمة من dict أو object attribute.
    """
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _coalesce(*values: Any, default: Any = None) -> Any:
    """
    أول قيمة غير فارغة.
    """
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return default


def _build_order_reference_id(invoice_or_data: Any) -> str:
    """
    بناء مرجع الطلب المحلي الذي سيرتبط بـ Tamara.
    """
    for key in ("order_reference_id", "reference", "reference_id", "invoice_number", "number"):
        value = _safe_get(invoice_or_data, key)
        if value:
            return _clean_str(value)

    invoice_id = _safe_get(invoice_or_data, "id")
    if invoice_id:
        return f"INV-{invoice_id}"

    raise TamaraCheckoutValidationError(
        "Unable to build Tamara order_reference_id from invoice/draft data."
    )


def _build_invoice_number(invoice_or_data: Any) -> str:
    """
    رقم/مرجع مناسب لعرضه داخل العنصر.
    """
    return _coalesce(
        _safe_get(invoice_or_data, "invoice_number"),
        _safe_get(invoice_or_data, "number"),
        _safe_get(invoice_or_data, "reference"),
        _safe_get(invoice_or_data, "order_reference_id"),
        default="Primey Invoice",
    )


def _build_customer_payload(invoice_or_data: Any) -> Dict[str, Any]:
    """
    بناء بيانات العميل من الفاتورة أو البيانات الممررة.
    """
    customer = _safe_get(invoice_or_data, "customer", {}) or {}
    company = _safe_get(invoice_or_data, "company", None)

    first_name = _coalesce(
        _safe_get(customer, "first_name"),
        _safe_get(invoice_or_data, "customer_first_name"),
        _safe_get(company, "name"),
        _safe_get(invoice_or_data, "company_name"),
        default="Primey",
    )

    last_name = _coalesce(
        _safe_get(customer, "last_name"),
        _safe_get(invoice_or_data, "customer_last_name"),
        default="Customer",
    )

    email = _coalesce(
        _safe_get(customer, "email"),
        _safe_get(invoice_or_data, "customer_email"),
        _safe_get(company, "email"),
        _safe_get(invoice_or_data, "company_email"),
    )

    phone = _coalesce(
        _safe_get(customer, "phone"),
        _safe_get(invoice_or_data, "customer_phone"),
        _safe_get(company, "phone"),
        _safe_get(company, "mobile_number"),
        _safe_get(invoice_or_data, "company_phone"),
    )

    if not email:
        raise TamaraCheckoutValidationError(
            "Tamara checkout requires a customer email."
        )

    if not phone:
        raise TamaraCheckoutValidationError(
            "Tamara checkout requires a customer phone number."
        )

    return {
        "first_name": _clean_str(first_name, "Primey"),
        "last_name": _clean_str(last_name, "Customer"),
        "phone_number": _clean_str(phone),
        "email": _clean_str(email),
    }


def _build_address_payload(
    invoice_or_data: Any,
    *,
    address_key: str = "billing_address",
) -> Dict[str, Any]:
    """
    بناء عنوان billing/shipping بشكل مرن.
    """
    address = _safe_get(invoice_or_data, address_key, {}) or {}
    company = _safe_get(invoice_or_data, "company", None)

    first_name = _coalesce(
        _safe_get(address, "first_name"),
        _safe_get(invoice_or_data, "customer_first_name"),
        _safe_get(company, "name"),
        default="Primey",
    )
    last_name = _coalesce(
        _safe_get(address, "last_name"),
        _safe_get(invoice_or_data, "customer_last_name"),
        default="Customer",
    )
    line1 = _coalesce(
        _safe_get(address, "line1"),
        _safe_get(address, "address_line1"),
        _safe_get(invoice_or_data, "address_line1"),
        _safe_get(company, "address"),
        default="Riyadh",
    )
    line2 = _coalesce(
        _safe_get(address, "line2"),
        _safe_get(address, "address_line2"),
        _safe_get(invoice_or_data, "address_line2"),
        default="",
    )
    city = _coalesce(
        _safe_get(address, "city"),
        _safe_get(invoice_or_data, "city"),
        _safe_get(company, "city"),
        default="Riyadh",
    )
    region = _coalesce(
        _safe_get(address, "region"),
        _safe_get(address, "state"),
        _safe_get(invoice_or_data, "state"),
        _safe_get(company, "region"),
        default=city or "Riyadh",
    )
    country_code = _coalesce(
        _safe_get(address, "country_code"),
        _safe_get(invoice_or_data, "country_code"),
        _safe_get(company, "country_code"),
        default=DEFAULT_COUNTRY_CODE,
    )
    phone_number = _coalesce(
        _safe_get(address, "phone_number"),
        _safe_get(invoice_or_data, "customer_phone"),
        _safe_get(company, "phone"),
        _safe_get(company, "mobile_number"),
        default="0000000000",
    )

    return {
        "first_name": _clean_str(first_name, "Primey"),
        "last_name": _clean_str(last_name, "Customer"),
        "line1": _clean_str(line1, "Riyadh"),
        "line2": _clean_str(line2),
        "region": _clean_str(region, "Riyadh"),
        "city": _clean_str(city, "Riyadh"),
        "country_code": _clean_str(country_code, DEFAULT_COUNTRY_CODE),
        "phone_number": _clean_str(phone_number, "0000000000"),
    }


def _extract_line_items(invoice_or_data: Any, *, currency: str) -> list[dict[str, Any]]:
    """
    استخراج line items من الفاتورة إن وجدت.
    """
    possible_items = _coalesce(
        _safe_get(invoice_or_data, "items"),
        _safe_get(invoice_or_data, "lines"),
        _safe_get(invoice_or_data, "invoice_items"),
        default=[],
    )

    normalized: list[dict[str, Any]] = []

    if isinstance(possible_items, Iterable) and not isinstance(possible_items, (str, bytes, dict)):
        for idx, item in enumerate(possible_items, start=1):
            name = _coalesce(
                _safe_get(item, "name"),
                _safe_get(item, "title"),
                _safe_get(item, "description"),
                default=f"Item {idx}",
            )

            quantity = int(_to_decimal(_safe_get(item, "quantity", 1), default="1"))

            unit_price = _to_decimal(
                _coalesce(
                    _safe_get(item, "unit_price"),
                    _safe_get(item, "price"),
                    _safe_get(item, "amount"),
                    default="0.00",
                )
            )
            tax_amount = _to_decimal(_safe_get(item, "tax_amount"), default="0.00")
            discount_amount = _to_decimal(_safe_get(item, "discount_amount"), default="0.00")

            explicit_total_amount = _safe_get(item, "total_amount", None)
            if explicit_total_amount is not None and explicit_total_amount != "":
                total_amount = _to_decimal(explicit_total_amount)
            else:
                total_amount = (unit_price * quantity) - discount_amount + tax_amount

            normalized_item: dict[str, Any] = {
                "reference_id": _clean_str(
                    _coalesce(
                        _safe_get(item, "reference_id"),
                        _safe_get(item, "sku"),
                        _safe_get(item, "code"),
                        default=f"ITEM-{idx}",
                    )
                ),
                "type": _clean_str(_coalesce(_safe_get(item, "type"), "Digital"), "Digital"),
                "name": _clean_str(name, f"Item {idx}"),
                "sku": _clean_str(
                    _coalesce(
                        _safe_get(item, "sku"),
                        _safe_get(item, "reference_id"),
                        default=f"SKU-{idx}",
                    )
                ),
                "quantity": quantity,
                "unit_price": _money(unit_price, currency),
                "tax_amount": _money(tax_amount, currency),
                "total_amount": _money(total_amount, currency),
            }

            if discount_amount > 0:
                normalized_item["discount_amount"] = _money(discount_amount, currency)

            normalized.append(normalized_item)

    return normalized


def _build_fallback_item(invoice_or_data: Any, *, currency: str) -> Dict[str, Any]:
    """
    عنصر افتراضي إذا لم تكن الفاتورة تحتوي line items صريحة.
    """
    title = _coalesce(
        _safe_get(invoice_or_data, "title"),
        _safe_get(invoice_or_data, "description"),
        _safe_get(invoice_or_data, "plan_name"),
        _safe_get(invoice_or_data, "invoice_title"),
        default="Mham Cloud Subscription",
    )
    reference = _build_order_reference_id(invoice_or_data)

    total = _to_decimal(
        _coalesce(
            _safe_get(invoice_or_data, "total_amount"),
            _safe_get(invoice_or_data, "amount"),
            _safe_get(invoice_or_data, "grand_total"),
            default="0.00",
        )
    )
    tax_amount = _to_decimal(_safe_get(invoice_or_data, "tax_amount"), default="0.00")
    discount_amount = _to_decimal(_safe_get(invoice_or_data, "discount_amount"), default="0.00")
    shipping_amount = _to_decimal(_safe_get(invoice_or_data, "shipping_amount"), default="0.00")

    unit_price = total - tax_amount - shipping_amount + discount_amount
    if unit_price < 0:
        unit_price = Decimal("0.00")

    item: Dict[str, Any] = {
        "reference_id": reference,
        "type": "Digital",
        "name": _clean_str(title, "Mham Cloud Subscription"),
        "sku": _build_invoice_number(invoice_or_data),
        "quantity": 1,
        "unit_price": _money(unit_price, currency),
        "tax_amount": _money(tax_amount, currency),
        "total_amount": _money(total, currency),
    }

    if discount_amount > 0:
        item["discount_amount"] = _money(discount_amount, currency)

    return item


def _build_items_payload(invoice_or_data: Any, *, currency: str) -> list[dict[str, Any]]:
    """
    بناء عناصر الطلب.
    """
    items = _extract_line_items(invoice_or_data, currency=currency)
    if items:
        return items
    return [_build_fallback_item(invoice_or_data, currency=currency)]


def _build_totals(invoice_or_data: Any, *, currency: str) -> Dict[str, Dict[str, Any]]:
    """
    بناء totals للطلب.
    """
    total_amount = _coalesce(
        _safe_get(invoice_or_data, "total_amount"),
        _safe_get(invoice_or_data, "amount"),
        _safe_get(invoice_or_data, "grand_total"),
        default="0.00",
    )
    shipping_amount = _coalesce(
        _safe_get(invoice_or_data, "shipping_amount"),
        default="0.00",
    )
    tax_amount = _coalesce(
        _safe_get(invoice_or_data, "tax_amount"),
        default="0.00",
    )
    discount_amount = _coalesce(
        _safe_get(invoice_or_data, "discount_amount"),
        default="0.00",
    )

    return {
        "total_amount": _money(total_amount, currency),
        "shipping_amount": _money(shipping_amount, currency),
        "tax_amount": _money(tax_amount, currency),
        "discount_amount": _money(discount_amount, currency),
    }


def _build_urls(invoice_or_data: Any) -> Dict[str, str]:
    """
    بناء روابط العودة للواجهة.
    """
    success_url = _coalesce(
        _safe_get(invoice_or_data, "success_url"),
        getattr(settings, "TAMARA_SUCCESS_URL", None),
        getattr(settings, "PAYMENT_SUCCESS_URL", None),
    )
    cancel_url = _coalesce(
        _safe_get(invoice_or_data, "cancel_url"),
        getattr(settings, "TAMARA_CANCEL_URL", None),
        getattr(settings, "PAYMENT_CANCEL_URL", None),
    )
    failure_url = _coalesce(
        _safe_get(invoice_or_data, "failure_url"),
        getattr(settings, "TAMARA_FAILURE_URL", None),
        cancel_url,
    )
    notification_url = _coalesce(
        _safe_get(invoice_or_data, "notification_url"),
        getattr(settings, "TAMARA_WEBHOOK_URL", None),
    )

    if not success_url:
        raise TamaraCheckoutValidationError("Tamara success_url is required.")
    if not cancel_url:
        raise TamaraCheckoutValidationError("Tamara cancel_url is required.")
    if not failure_url:
        raise TamaraCheckoutValidationError("Tamara failure_url is required.")
    if not notification_url:
        raise TamaraCheckoutValidationError("Tamara notification_url is required.")

    return {
        "success_url": _clean_str(success_url),
        "cancel_url": _clean_str(cancel_url),
        "failure_url": _clean_str(failure_url),
        "notification_url": _clean_str(notification_url),
    }


def _get_tamara_config() -> TamaraConfig:
    """
    تحميل إعدادات Tamara من Django settings.
    """
    api_token = getattr(settings, "TAMARA_API_TOKEN", "")
    environment = getattr(settings, "TAMARA_ENVIRONMENT", "sandbox")
    timeout = int(getattr(settings, "TAMARA_TIMEOUT", 30) or 30)
    base_url = getattr(settings, "TAMARA_API_BASE_URL", None)
    notification_token = getattr(settings, "TAMARA_NOTIFICATION_TOKEN", None)
    public_key = getattr(settings, "TAMARA_PUBLIC_KEY", None)

    return TamaraConfig(
        api_token=api_token,
        environment=environment,
        timeout=timeout,
        base_url=base_url,
        notification_token=notification_token,
        public_key=public_key,
    )


# ============================================================
# Service
# ============================================================

class TamaraCheckoutService:
    """
    خدمة إنشاء Checkout Session في Tamara.

    تستخدم داخل الـ Billing Flow:
    - invoice / payment draft -> build payload
    - call Tamara client
    - return normalized result

    لا تقوم بـ:
    - اعتماد الفاتورة
    - تفعيل الاشتراك
    - تسجيل الدفع النهائي
    """

    def __init__(self, *, client: Optional[TamaraClient] = None) -> None:
        self.client = client or TamaraClient(_get_tamara_config())

    def build_checkout_payload(self, invoice_or_data: Any) -> Dict[str, Any]:
        """
        بناء Payload كامل لـ Tamara Checkout.
        """
        currency = _coalesce(
            _safe_get(invoice_or_data, "currency"),
            getattr(settings, "TAMARA_DEFAULT_CURRENCY", None),
            DEFAULT_CURRENCY,
        )

        order_reference_id = _build_order_reference_id(invoice_or_data)
        order_number = _build_invoice_number(invoice_or_data)

        description = _coalesce(
            _safe_get(invoice_or_data, "description"),
            _safe_get(invoice_or_data, "invoice_description"),
            f"Payment for {order_reference_id}",
        )

        customer = _build_customer_payload(invoice_or_data)
        billing_address = _build_address_payload(invoice_or_data, address_key="billing_address")
        shipping_address = _build_address_payload(invoice_or_data, address_key="shipping_address")
        items = _build_items_payload(invoice_or_data, currency=currency)
        totals = _build_totals(invoice_or_data, currency=currency)
        urls = _build_urls(invoice_or_data)

        country_code = _coalesce(
            _safe_get(invoice_or_data, "country_code"),
            _safe_get(shipping_address, "country_code"),
            DEFAULT_COUNTRY_CODE,
        )
        locale = _coalesce(
            _safe_get(invoice_or_data, "locale"),
            getattr(settings, "TAMARA_LOCALE", None),
            DEFAULT_LOCALE,
        )

        discount_decimal = _to_decimal(
            _coalesce(_safe_get(invoice_or_data, "discount_amount"), default="0.00")
        )

        payload: Dict[str, Any] = {
            "order_reference_id": order_reference_id,
            "order_number": _clean_str(order_number),
            "description": _clean_str(description),
            "country_code": _clean_str(country_code, DEFAULT_COUNTRY_CODE),
            "payment_type": "PAY_BY_INSTALMENTS",
            "instalments": int(_coalesce(_safe_get(invoice_or_data, "instalments"), 3)),
            "locale": _clean_str(locale, DEFAULT_LOCALE),
            "items": items,
            "consumer": customer,
            "billing_address": billing_address,
            "shipping_address": shipping_address,
            "tax_amount": totals["tax_amount"],
            "shipping_amount": totals["shipping_amount"],
            "total_amount": totals["total_amount"],
            "merchant_url": {
                "success": urls["success_url"],
                "failure": urls["failure_url"],
                "cancel": urls["cancel_url"],
                "notification": urls["notification_url"],
            },
            "platform": _clean_str(
                _coalesce(_safe_get(invoice_or_data, "platform"), "Mham Cloud")
            ),
        }

        if discount_decimal > 0:
            payload["discount"] = {
                "amount": totals["discount_amount"],
                "name": _clean_str(
                    _coalesce(_safe_get(invoice_or_data, "discount_name"), "Primey Discount")
                ),
            }

        return payload

    def create_checkout(self, invoice_or_data: Any) -> TamaraCheckoutResult:
        """
        إنشاء Checkout Session فعليًا وإرجاع نتيجة موحّدة.
        """
        payload = self.build_checkout_payload(invoice_or_data)
        logger.info(
            "Creating Tamara checkout for reference=%s",
            payload.get("order_reference_id"),
        )

        try:
            response = self.client.create_checkout_session(payload)
        except (TamaraConfigurationError, TamaraError) as exc:
            logger.exception("Tamara checkout remote error")
            raise TamaraCheckoutRemoteError(str(exc)) from exc

        checkout_url = _coalesce(
            response.get("checkout_url"),
            response.get("url"),
        )
        tamara_order_id = _coalesce(
            response.get("order_id"),
            response.get("tamara_order_id"),
        )
        tamara_checkout_id = _coalesce(
            response.get("checkout_id"),
            response.get("tamara_checkout_id"),
        )
        status = _coalesce(
            response.get("status"),
            response.get("order_status"),
        )

        if not checkout_url:
            raise TamaraCheckoutRemoteError(
                "Tamara response did not include checkout_url."
            )
        if not tamara_order_id:
            raise TamaraCheckoutRemoteError(
                "Tamara response did not include order_id."
            )

        return TamaraCheckoutResult(
            success=True,
            checkout_url=_clean_str(checkout_url),
            tamara_order_id=_clean_str(tamara_order_id),
            tamara_checkout_id=_clean_str(tamara_checkout_id) if tamara_checkout_id else None,
            status=_clean_str(status) if status else None,
            raw_response=response,
        )


# ============================================================
# Convenience Function
# ============================================================

def create_tamara_checkout(invoice_or_data: Any) -> TamaraCheckoutResult:
    """
    اختصار سريع للاستخدام المباشر.
    """
    service = TamaraCheckoutService()
    return service.create_checkout(invoice_or_data)