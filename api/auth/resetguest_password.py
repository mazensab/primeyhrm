# ============================================================
# Reset Guest Password API
# Mham Cloud
# Reset Password by Username or Email (Guest Flow)
# Final Clean Version using notification_center/services_auth.py
# ============================================================

from __future__ import annotations

import json
import logging
from typing import Optional

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from notification_center.services_auth import notify_password_reset_completed

User = get_user_model()
logger = logging.getLogger(__name__)


# ============================================================
# Helpers
# ============================================================

def _json_body(request) -> dict:
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


def _ok(data: Optional[dict] = None, status: int = 200):
    payload = {"success": True}
    if data:
        payload.update(data)
    return JsonResponse(payload, status=status)


def _bad_request(message: str = "Bad request", errors: Optional[dict] = None):
    return JsonResponse(
        {
            "success": False,
            "message": message,
            "errors": errors or {},
        },
        status=400,
    )


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


def _normalize_identifier(value: str) -> str:
    return _clean_text(value).lower()


# ============================================================
# POST /api/auth/resetguest-password/
# ============================================================

@require_POST
def resetguest_password(request):
    data = _json_body(request)

    identifier = _normalize_identifier(data.get("identifier"))
    new_password = _clean_text(data.get("new_password"))
    confirm_password = _clean_text(data.get("confirm_password"))

    errors = {}

    if not identifier:
        errors["identifier"] = "Username or email is required"

    if not new_password:
        errors["new_password"] = "New password is required"
    elif len(new_password) < 8:
        errors["new_password"] = "New password must be at least 8 characters"

    if not confirm_password:
        errors["confirm_password"] = "Confirm password is required"
    elif new_password != confirm_password:
        errors["confirm_password"] = "Passwords do not match"

    if errors:
        return _bad_request("Validation error", errors)

    try:
        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(username__iexact=identifier).first()

        if not user:
            return JsonResponse(
                {
                    "success": False,
                    "message": "User not found",
                },
                status=404,
            )

        if not user.is_active:
            return JsonResponse(
                {
                    "success": False,
                    "message": "User account is inactive",
                },
                status=400,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        dispatch_result = notify_password_reset_completed(
            user=user,
            request=request,
            actor=None,
            reset_flow="guest_reset",
        )

        if dispatch_result["notification_created"]:
            logger.info(
                "Guest password reset completed and auth notification dispatched successfully for user=%s",
                user.username,
            )
        else:
            logger.warning(
                "Guest password reset completed but auth notification was not created for user=%s",
                user.username,
            )

        return _ok(
            {
                "message": "Password reset successfully",
                "notification_created": dispatch_result["notification_created"],
                "email_sent": dispatch_result["email_sent"],
                "email_error": dispatch_result["email_error"],
                "whatsapp_sent": dispatch_result["whatsapp_sent"],
                "whatsapp_error": dispatch_result["whatsapp_error"],
            }
        )

    except Exception as exc:
        logger.exception("Failed to reset guest password: %s", exc)
        return JsonResponse(
            {
                "success": False,
                "message": "Failed to reset password",
                "details": str(exc),
            },
            status=500,
        )