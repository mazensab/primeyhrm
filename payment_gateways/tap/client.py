# ============================================================
# Tap API Client
# Primey HR Cloud
# Path: payment_gateways/tap/client.py
# ------------------------------------------------------------
# HTTP Client Layer only
# - No billing logic here
# - No subscription activation here
# - No invoice state machine here
# ------------------------------------------------------------
# Supported operations:
# - Create Charge
# - Retrieve Charge
# - Void / Refund can be added later
# ============================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

TAP_BASE_URL = "https://api.tap.company/v2"
DEFAULT_TIMEOUT = 30


# ============================================================
# Exceptions
# ============================================================

class TapError(Exception):
    """Base exception for Tap client."""


class TapConfigurationError(TapError):
    """Raised when Tap client configuration is invalid."""


class TapRequestError(TapError):
    """Raised when HTTP request fails before valid response."""


class TapAPIError(TapError):
    """Raised when Tap returns non-2xx response."""

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
class TapConfig:
    secret_key: str
    public_key: Optional[str] = None
    timeout: int = DEFAULT_TIMEOUT
    base_url: str = TAP_BASE_URL
    extra_headers: Dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.secret_key or not self.secret_key.strip():
            raise TapConfigurationError("Tap secret_key is required.")

        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise TapConfigurationError("Tap timeout must be a positive integer.")

        if not self.base_url or not str(self.base_url).strip():
            raise TapConfigurationError("Tap base_url is required.")


# ============================================================
# Client
# ============================================================

class TapClient:
    """
    عميل HTTP احترافي للتعامل مع Tap API.

    مسؤول فقط عن:
    - المصادقة
    - إرسال الطلبات
    - إرجاع JSON
    - رفع أخطاء واضحة
    """

    def __init__(
        self,
        config: TapConfig,
        *,
        session: Optional[Session] = None,
    ) -> None:
        config.validate()
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.session = session or self._build_session()

    # --------------------------------------------------------
    # Session / Headers
    # --------------------------------------------------------

    def _build_session(self) -> Session:
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
        headers = {
            "Authorization": f"Bearer {self.config.secret_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "PrimeyHRCloud-TapClient/1.0",
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
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        used_timeout = timeout or self.config.timeout

        logger.info("Tap request started: %s %s", method.upper(), url)

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                json=payload,
                params=params,
                timeout=used_timeout,
            )
        except requests.Timeout as exc:
            logger.exception("Tap request timeout: %s %s", method.upper(), url)
            raise TapRequestError(f"Tap request timed out after {used_timeout} seconds.") from exc
        except requests.RequestException as exc:
            logger.exception("Tap request failed: %s %s", method.upper(), url)
            raise TapRequestError(f"Tap request failed: {exc}") from exc

        return self._handle_response(response)

    def _handle_response(self, response: Response) -> Dict[str, Any]:
        status_code = response.status_code
        content_type = response.headers.get("Content-Type", "")

        try:
            data = response.json() if "application/json" in content_type else {}
        except ValueError:
            data = {}

        if 200 <= status_code < 300:
            logger.info("Tap response success: %s", status_code)
            return data

        message = self._extract_error_message(data, response)

        logger.error(
            "Tap API error. status=%s message=%s response=%s",
            status_code,
            message,
            data if data else response.text[:1000],
        )
        raise TapAPIError(
            message,
            status_code=status_code,
            response_data=data,
        )

    @staticmethod
    def _extract_error_message(data: Dict[str, Any], response: Response) -> str:
        if isinstance(data, dict):
            for key in ("message", "error", "description", "errors"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
                if isinstance(value, list) and value:
                    return str(value[0])

        text = (response.text or "").strip()
        if text:
            return text[:500]

        return f"Tap API returned HTTP {response.status_code}."

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def create_charge(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict) or not payload:
            raise TapConfigurationError("Tap create_charge payload must be a non-empty dict.")

        return self._request("POST", "/charges", payload=payload)

    def retrieve_charge(self, charge_id: str) -> Dict[str, Any]:
        if not charge_id or not str(charge_id).strip():
            raise TapConfigurationError("Tap charge_id is required.")

        return self._request("GET", f"/charges/{charge_id}")

    def ping_charge(self, charge_id: str) -> bool:
        try:
            self.retrieve_charge(charge_id)
            return True
        except TapError:
            return False