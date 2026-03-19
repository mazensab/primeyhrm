# ============================================================
# Tamara API Client
# Primey HR Cloud
# Path: payment_gateways/tamara/client.py
# ------------------------------------------------------------
# HTTP Client Layer only
# - No billing logic here
# - No subscription activation here
# - No invoice state machine here
# ------------------------------------------------------------
# Supported operations:
# - Create Checkout Session
# - Get Order Details
# - Authorise Order
# - Capture Order
# - Refund Order
# - Cancel Order
# - Update Order Reference ID
# ============================================================

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


# ============================================================
# Constants
# ============================================================

TAMARA_SANDBOX_BASE_URL = "https://api-sandbox.tamara.co"
TAMARA_PRODUCTION_BASE_URL = "https://api.tamara.co"

DEFAULT_TIMEOUT = 30


# ============================================================
# Exceptions
# ============================================================

class TamaraError(Exception):
    """Base exception for Tamara client."""


class TamaraConfigurationError(TamaraError):
    """Raised when the client configuration is invalid."""


class TamaraRequestError(TamaraError):
    """Raised when the request to Tamara fails before a valid HTTP response is received."""


class TamaraAPIError(TamaraError):
    """Raised when Tamara returns an error response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


# ============================================================
# Configuration
# ============================================================

@dataclass(slots=True)
class TamaraConfig:
    """
    إعدادات عميل Tamara.

    environment:
        - sandbox
        - production
    """

    api_token: str
    environment: str = "sandbox"
    timeout: int = DEFAULT_TIMEOUT
    base_url: Optional[str] = None
    notification_token: Optional[str] = None
    public_key: Optional[str] = None
    merchant_callback_url: Optional[str] = None
    extra_headers: Dict[str, str] = field(default_factory=dict)

    def resolved_base_url(self) -> str:
        """إرجاع الـ Base URL الصحيح حسب البيئة أو القيمة المخصصة."""
        if self.base_url:
            return self.base_url.rstrip("/")

        env = (self.environment or "").strip().lower()
        if env == "sandbox":
            return TAMARA_SANDBOX_BASE_URL
        if env == "production":
            return TAMARA_PRODUCTION_BASE_URL

        raise TamaraConfigurationError(
            "Invalid Tamara environment. Use 'sandbox' or 'production'."
        )

    def validate(self) -> None:
        """التحقق من صحة الإعدادات قبل بدء الاتصال."""
        if not self.api_token or not self.api_token.strip():
            raise TamaraConfigurationError("Tamara api_token is required.")

        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise TamaraConfigurationError("Tamara timeout must be a positive integer.")

        # يتحقق أيضًا من البيئة
        self.resolved_base_url()


# ============================================================
# Client
# ============================================================

class TamaraClient:
    """
    عميل HTTP احترافي للتعامل مع Tamara API.

    هذا الكلاس مسؤول فقط عن:
    - المصادقة
    - إرسال الطلبات
    - إعادة JSON
    - رفع الأخطاء بشكل واضح

    لا يحتوي أي منطق تجاري خاص بالفواتير أو الاشتراكات.
    """

    def __init__(
        self,
        config: TamaraConfig,
        *,
        session: Optional[Session] = None,
    ) -> None:
        config.validate()
        self.config = config
        self.base_url = config.resolved_base_url()
        self.session = session or self._build_session()

    # --------------------------------------------------------
    # Session / Headers
    # --------------------------------------------------------

    def _build_session(self) -> Session:
        """
        بناء جلسة requests مع Retry آمن للطلبات المؤقتة الفاشلة.
        """
        session = requests.Session()

        retries = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.7,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"}),
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        session.headers.update(self._default_headers())
        return session

    def _default_headers(self) -> Dict[str, str]:
        """
        الهيدرز الافتراضية لكل طلب.
        """
        headers = {
            "Authorization": f"Bearer {self.config.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "PrimeyHRCloud-TamaraClient/1.0",
        }

        if self.config.extra_headers:
            headers.update(self.config.extra_headers)

        return headers

    # --------------------------------------------------------
    # Core Request
    # --------------------------------------------------------

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        تنفيذ طلب HTTP موحد إلى Tamara.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        used_timeout = timeout or self.config.timeout

        logger.info("Tamara request started: %s %s", method.upper(), url)

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                json=payload,
                params=params,
                timeout=used_timeout,
            )
        except requests.Timeout as exc:
            logger.exception("Tamara request timeout: %s %s", method.upper(), url)
            raise TamaraRequestError(
                f"Tamara request timed out after {used_timeout} seconds."
            ) from exc
        except requests.RequestException as exc:
            logger.exception("Tamara request failed: %s %s", method.upper(), url)
            raise TamaraRequestError(f"Tamara request failed: {exc}") from exc

        return self._handle_response(response)

    def _handle_response(self, response: Response) -> Dict[str, Any]:
        """
        معالجة Response وإرجاع JSON أو رفع خطأ واضح.
        """
        status_code = response.status_code
        content_type = response.headers.get("Content-Type", "")

        try:
            data = response.json() if "application/json" in content_type else {}
        except ValueError:
            data = {}

        if 200 <= status_code < 300:
            logger.info("Tamara response success: %s", status_code)
            return data

        message = self._extract_error_message(data, response)
        logger.error(
            "Tamara API error. status=%s message=%s response=%s",
            status_code,
            message,
            data if data else response.text[:1000],
        )
        raise TamaraAPIError(
            message=message,
            status_code=status_code,
            response_data=data,
        )

    @staticmethod
    def _extract_error_message(data: Dict[str, Any], response: Response) -> str:
        """
        استخراج أفضل رسالة خطأ ممكنة من استجابة Tamara.
        """
        possible_keys = (
            "message",
            "error_message",
            "error",
            "detail",
            "errors",
        )

        for key in possible_keys:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

            if isinstance(value, list) and value:
                try:
                    return json.dumps(value, ensure_ascii=False)
                except Exception:
                    return str(value)

            if isinstance(value, dict) and value:
                try:
                    return json.dumps(value, ensure_ascii=False)
                except Exception:
                    return str(value)

        if response.text:
            return response.text[:1000]

        return f"Tamara API returned HTTP {response.status_code}"

    # --------------------------------------------------------
    # Checkout
    # --------------------------------------------------------

    def create_checkout_session(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        إنشاء Checkout Session.

        متوقع من Tamara أن يعيد:
        - order_id
        - checkout_id
        - checkout_url
        - status
        """
        return self._request("POST", "/checkout", payload=payload)

    # --------------------------------------------------------
    # Orders
    # --------------------------------------------------------

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        جلب تفاصيل الطلب من Tamara.
        """
        self._require_value(order_id, "order_id")
        return self._request("GET", f"/orders/{order_id}")

    def authorise_order(self, order_id: str) -> Dict[str, Any]:
        """
        تنفيذ Authorise للطلب بعد approved webhook.
        """
        self._require_value(order_id, "order_id")
        return self._request("POST", f"/orders/{order_id}/authorise")

    def update_order_reference_id(
        self,
        order_id: str,
        order_reference_id: str,
    ) -> Dict[str, Any]:
        """
        تحديث order_reference_id على Tamara.
        """
        self._require_value(order_id, "order_id")
        self._require_value(order_reference_id, "order_reference_id")

        payload = {
            "order_reference_id": order_reference_id,
        }
        return self._request("PUT", f"/orders/{order_id}/reference-id", payload=payload)

    def cancel_order(
        self,
        order_id: str,
        *,
        total_amount: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        items: Optional[list[Dict[str, Any]]] = None,
        shipping_amount: Optional[Dict[str, Any]] = None,
        tax_amount: Optional[Dict[str, Any]] = None,
        discount_amount: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        إلغاء الطلب عند الحاجة.

        ملاحظة:
        قد تختلف الحقول المطلوبة أو الاختيارية بحسب تدفق Tamara الفعلي
        والإصدار المستخدم من الـ API/Portal، لذلك هذا الميثود يدعم payload مرن.
        """
        self._require_value(order_id, "order_id")

        payload: Dict[str, Any] = {}

        if total_amount is not None:
            payload["total_amount"] = total_amount
        if reason:
            payload["reason"] = reason
        if items is not None:
            payload["items"] = items
        if shipping_amount is not None:
            payload["shipping_amount"] = shipping_amount
        if tax_amount is not None:
            payload["tax_amount"] = tax_amount
        if discount_amount is not None:
            payload["discount_amount"] = discount_amount

        return self._request("POST", f"/orders/{order_id}/cancel", payload=payload or None)

    # --------------------------------------------------------
    # Payments
    # --------------------------------------------------------

    def capture_order(
        self,
        *,
        order_id: str,
        total_amount: Dict[str, Any],
        description: Optional[str] = None,
        items: Optional[list[Dict[str, Any]]] = None,
        shipping_info: Optional[Dict[str, Any]] = None,
        discount_amount: Optional[Dict[str, Any]] = None,
        tax_amount: Optional[Dict[str, Any]] = None,
        shipping_amount: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        تنفيذ Capture كامل أو جزئي.

        المتغيرات المهمة:
        - order_id
        - total_amount: {"amount": "100.00", "currency": "SAR"}
        """
        self._require_value(order_id, "order_id")
        self._require_dict(total_amount, "total_amount")

        payload: Dict[str, Any] = {
            "order_id": order_id,
            "total_amount": total_amount,
        }

        if description:
            payload["description"] = description
        if items is not None:
            payload["items"] = items
        if shipping_info is not None:
            payload["shipping_info"] = shipping_info
        if discount_amount is not None:
            payload["discount_amount"] = discount_amount
        if tax_amount is not None:
            payload["tax_amount"] = tax_amount
        if shipping_amount is not None:
            payload["shipping_amount"] = shipping_amount

        return self._request("POST", "/payments/capture", payload=payload)

    def refund_order(
        self,
        *,
        order_id: str,
        total_amount: Dict[str, Any],
        comment: Optional[str] = None,
        items: Optional[list[Dict[str, Any]]] = None,
        shipping_amount: Optional[Dict[str, Any]] = None,
        tax_amount: Optional[Dict[str, Any]] = None,
        discount_amount: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        تنفيذ Refund كامل أو جزئي.
        """
        self._require_value(order_id, "order_id")
        self._require_dict(total_amount, "total_amount")

        payload: Dict[str, Any] = {
            "order_id": order_id,
            "total_amount": total_amount,
        }

        if comment:
            payload["comment"] = comment
        if items is not None:
            payload["items"] = items
        if shipping_amount is not None:
            payload["shipping_amount"] = shipping_amount
        if tax_amount is not None:
            payload["tax_amount"] = tax_amount
        if discount_amount is not None:
            payload["discount_amount"] = discount_amount

        return self._request("POST", "/payments/refund", payload=payload)

    # --------------------------------------------------------
    # Health / Utility
    # --------------------------------------------------------

    def ping_order(self, order_id: str) -> bool:
        """
        فحص بسيط لمعرفة إن كان الوصول للطلب يعمل.
        """
        try:
            self.get_order(order_id)
            return True
        except TamaraError:
            return False

    @staticmethod
    def _require_value(value: Optional[str], field_name: str) -> None:
        if not value or not str(value).strip():
            raise TamaraConfigurationError(f"{field_name} is required.")

    @staticmethod
    def _require_dict(value: Optional[Dict[str, Any]], field_name: str) -> None:
        if not isinstance(value, dict) or not value:
            raise TamaraConfigurationError(f"{field_name} must be a non-empty dict.")