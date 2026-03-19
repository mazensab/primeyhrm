# ============================================================
# 📂 whatsapp_center/client.py
# Primey HR Cloud - WhatsApp Provider Client
# ============================================================
# ✅ يدعم:
# - مزودات Stub الحالية
# - WhatsApp Web Session Gateway
# - Session Management:
#   * Create QR
#   * Create Pairing Code
#   * Get Session Status
#   * Disconnect Session
# ============================================================

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional, Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


# ============================================================
# 📦 Results
# ============================================================

@dataclass
class WhatsAppSendResult:
    success: bool
    status_code: int
    provider_status: str = ""
    external_message_id: str = ""
    response_data: Optional[dict] = None
    error_message: str = ""


@dataclass
class WhatsAppSessionResult:
    success: bool
    status_code: int
    session_status: str = "disconnected"
    connected: bool = False
    connected_phone: str = ""
    device_label: str = ""
    qr_code: str = ""
    pairing_code: str = ""
    last_connected_at: str = ""
    response_data: Optional[dict] = None
    error_message: str = ""


# ============================================================
# 💬 WhatsApp Client
# ============================================================

class WhatsAppClient:
    """
    عميل إرسال واتساب.

    يدعم:
    - Stub افتراضي للمزودات غير المربوطة بعد
    - WhatsApp Web Session Gateway
    """

    def __init__(
        self,
        *,
        provider: str,
        access_token: str = "",
        phone_number_id: str = "",
        api_version: str = "v22.0",
        session_name: str = "",
    ):
        self.provider = (provider or "").strip()
        self.access_token = access_token or ""
        self.phone_number_id = phone_number_id or ""
        self.api_version = api_version or "v22.0"
        self.session_name = (session_name or "primey-system-session").strip()

    # --------------------------------------------------------
    # ⚙️ Gateway Config
    # --------------------------------------------------------
    @property
    def gateway_base_url(self) -> str:
        return (os.getenv("WHATSAPP_SESSION_GATEWAY_URL") or "").strip().rstrip("/")

    @property
    def gateway_token(self) -> str:
        return (os.getenv("WHATSAPP_SESSION_GATEWAY_TOKEN") or "").strip()

    @property
    def gateway_timeout(self) -> int:
        try:
            timeout = int(os.getenv("WHATSAPP_SESSION_GATEWAY_TIMEOUT", "20"))
            return timeout if timeout > 0 else 20
        except Exception:
            return 20

    def _gateway_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.gateway_token:
            headers["Authorization"] = f"Bearer {self.gateway_token}"

        return headers

    # --------------------------------------------------------
    # 🔐 Provider Detection
    # --------------------------------------------------------
    def _is_web_session_provider(self) -> bool:
        return self.provider in {
            "whatsapp_web_session",
            "WEB_SESSION",
            "web_session",
        }

    # --------------------------------------------------------
    # 🌐 Gateway Core Request
    # --------------------------------------------------------
    def _gateway_post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        استدعاء موحد للـ Session Gateway الخارجي.
        """
        if not self.gateway_base_url:
            return {
                "success": False,
                "message": "WHATSAPP_SESSION_GATEWAY_URL is not configured",
            }

        target_url = urljoin(f"{self.gateway_base_url}/", path.lstrip("/"))

        req = Request(
            target_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._gateway_headers(),
            method="POST",
        )

        try:
            with urlopen(req, timeout=self.gateway_timeout) as response:
                raw = response.read().decode("utf-8") or "{}"

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "message": "Invalid JSON response from gateway",
                        "raw_response": raw,
                    }

                if "success" not in data:
                    data["success"] = True

                if "status_code" not in data:
                    data["status_code"] = getattr(response, "status", 200)

                return data

        except HTTPError as exc:
            try:
                raw = exc.read().decode("utf-8") or "{}"
                parsed = json.loads(raw)
            except Exception:
                parsed = {}

            return {
                "success": False,
                "message": parsed.get("message") or f"Gateway HTTPError {exc.code}",
                "details": parsed,
                "status_code": exc.code,
            }

        except URLError as exc:
            return {
                "success": False,
                "message": f"Gateway connection failed: {exc.reason}",
                "status_code": 503,
            }

        except Exception as exc:
            return {
                "success": False,
                "message": f"Unexpected gateway error: {str(exc)}",
                "status_code": 500,
            }

    # --------------------------------------------------------
    # 🧩 Session Result Mapper
    # --------------------------------------------------------
    def _build_session_result(self, data: dict[str, Any]) -> WhatsAppSessionResult:
        return WhatsAppSessionResult(
            success=bool(data.get("success")),
            status_code=int(data.get("status_code", 200 if data.get("success") else 400)),
            session_status=str(data.get("session_status") or "disconnected"),
            connected=bool(data.get("connected", False)),
            connected_phone=str(data.get("connected_phone") or ""),
            device_label=str(data.get("device_label") or ""),
            qr_code=str(data.get("qr_code") or ""),
            pairing_code=str(data.get("pairing_code") or ""),
            last_connected_at=str(data.get("last_connected_at") or ""),
            response_data=data,
            error_message=str(data.get("message") or ""),
        )

    # --------------------------------------------------------
    # 📲 Create QR Session
    # --------------------------------------------------------
    def create_qr_session(self) -> WhatsAppSessionResult:
        if not self._is_web_session_provider():
            return WhatsAppSessionResult(
                success=False,
                status_code=400,
                session_status="failed",
                error_message="QR session is only supported for whatsapp_web_session provider",
                response_data={},
            )

        data = self._gateway_post(
            "/session/create-qr/",
            {
                "session_name": self.session_name,
                "mode": "qr",
            },
        )
        return self._build_session_result(data)

    # --------------------------------------------------------
    # 🔢 Create Pairing Code Session
    # --------------------------------------------------------
    def create_pairing_code_session(self, *, phone_number: str) -> WhatsAppSessionResult:
        if not self._is_web_session_provider():
            return WhatsAppSessionResult(
                success=False,
                status_code=400,
                session_status="failed",
                error_message="Pairing code is only supported for whatsapp_web_session provider",
                response_data={},
            )

        phone_number = (phone_number or "").strip()
        if not phone_number:
            return WhatsAppSessionResult(
                success=False,
                status_code=400,
                session_status="failed",
                error_message="Missing phone_number",
                response_data={},
            )

        data = self._gateway_post(
            "/session/create-pairing-code/",
            {
                "session_name": self.session_name,
                "phone_number": phone_number,
                "mode": "pairing_code",
            },
        )
        return self._build_session_result(data)

    # --------------------------------------------------------
    # 📡 Get Session Status
    # --------------------------------------------------------
    def get_session_status(self) -> WhatsAppSessionResult:
        if not self._is_web_session_provider():
            return WhatsAppSessionResult(
                success=True,
                status_code=200,
                session_status="disconnected",
                connected=False,
                response_data={
                    "success": True,
                    "session_status": "disconnected",
                    "connected": False,
                    "message": "Non-session provider",
                },
            )

        data = self._gateway_post(
            "/session/status/",
            {
                "session_name": self.session_name,
            },
        )
        return self._build_session_result(data)

    # --------------------------------------------------------
    # 🔌 Disconnect Session
    # --------------------------------------------------------
    def disconnect_session(self) -> WhatsAppSessionResult:
        if not self._is_web_session_provider():
            return WhatsAppSessionResult(
                success=False,
                status_code=400,
                session_status="failed",
                error_message="Disconnect is only supported for whatsapp_web_session provider",
                response_data={},
            )

        data = self._gateway_post(
            "/session/disconnect/",
            {
                "session_name": self.session_name,
            },
        )
        return self._build_session_result(data)

    # --------------------------------------------------------
    # 💬 Send Text Message
    # --------------------------------------------------------
    def send_text_message(self, *, to_phone: str, body: str) -> WhatsAppSendResult:
        if not to_phone or not body:
            return WhatsAppSendResult(
                success=False,
                status_code=400,
                provider_status="validation_failed",
                error_message="Missing to_phone or body",
                response_data={},
            )

        # ----------------------------------------------------
        # WhatsApp Web Session Gateway
        # ----------------------------------------------------
        if self._is_web_session_provider():
            data = self._gateway_post(
                "/messages/send-text/",
                {
                    "session_name": self.session_name,
                    "to_phone": to_phone,
                    "body": body,
                },
            )

            if not data.get("success"):
                return WhatsAppSendResult(
                    success=False,
                    status_code=int(data.get("status_code", 400)),
                    provider_status=str(data.get("provider_status") or "gateway_failed"),
                    error_message=str(data.get("message") or "Session gateway failed"),
                    response_data=data,
                )

            return WhatsAppSendResult(
                success=True,
                status_code=int(data.get("status_code", 200)),
                provider_status=str(data.get("provider_status") or "accepted"),
                external_message_id=str(
                    data.get("external_message_id", "") or data.get("message_id", "")
                ),
                response_data=data,
                error_message="",
            )

        # ----------------------------------------------------
        # Placeholder للمزودات الأخرى
        # ----------------------------------------------------
        return WhatsAppSendResult(
            success=True,
            status_code=200,
            provider_status="accepted_stub",
            external_message_id="stub-message-id",
            response_data={
                "stub": True,
                "provider": self.provider,
                "to": to_phone,
                "body": body,
            },
        )

    # --------------------------------------------------------
    # 📄 Send Document Message
    # --------------------------------------------------------
    def send_document_message(
        self,
        *,
        to_phone: str,
        document_url: str,
        caption: str = "",
        filename: str = "",
    ) -> WhatsAppSendResult:
        if not to_phone or not document_url:
            return WhatsAppSendResult(
                success=False,
                status_code=400,
                provider_status="validation_failed",
                error_message="Missing to_phone or document_url",
                response_data={},
            )

        # ----------------------------------------------------
        # WhatsApp Web Session Gateway
        # ----------------------------------------------------
        if self._is_web_session_provider():
            data = self._gateway_post(
                "/messages/send-document/",
                {
                    "session_name": self.session_name,
                    "to_phone": to_phone,
                    "document_url": document_url,
                    "caption": caption,
                    "filename": filename,
                },
            )

            if not data.get("success"):
                return WhatsAppSendResult(
                    success=False,
                    status_code=int(data.get("status_code", 400)),
                    provider_status=str(data.get("provider_status") or "gateway_failed"),
                    error_message=str(data.get("message") or "Session gateway failed"),
                    response_data=data,
                )

            return WhatsAppSendResult(
                success=True,
                status_code=int(data.get("status_code", 200)),
                provider_status=str(data.get("provider_status") or "accepted"),
                external_message_id=str(
                    data.get("external_message_id", "") or data.get("message_id", "")
                ),
                response_data=data,
                error_message="",
            )

        # ----------------------------------------------------
        # Placeholder للمزودات الأخرى
        # ----------------------------------------------------
        return WhatsAppSendResult(
            success=True,
            status_code=200,
            provider_status="accepted_stub",
            external_message_id="stub-document-id",
            response_data={
                "stub": True,
                "provider": self.provider,
                "to": to_phone,
                "document_url": document_url,
                "caption": caption,
                "filename": filename,
            },
        )