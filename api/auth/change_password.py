# ============================================================
# Change Password API
# Mham Cloud
# Self Service Password Change for Current User
# Final Clean Version using notification_center/services_auth.py
# ============================================================

from __future__ import annotations

import json
import logging
from typing import Optional

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from notification_center.services_auth import notify_password_changed

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


# ============================================================
# POST /api/auth/change-password/
# ============================================================

@login_required
@require_POST
def change_password(request):
    data = _json_body(request)

    current_password = _clean_text(data.get("current_password"))
    new_password = _clean_text(data.get("new_password"))

    errors = {}

    if not current_password:
        errors["current_password"] = "Current password is required"

    if not new_password:
        errors["new_password"] = "New password is required"
    elif len(new_password) < 8:
        errors["new_password"] = "New password must be at least 8 characters"

    if errors:
        return _bad_request("Validation error", errors)

    user = request.user

    if not user.check_password(current_password):
        return JsonResponse(
            {
                "success": False,
                "message": "Current password is incorrect",
            },
            status=400,
        )

    if current_password == new_password:
        return JsonResponse(
            {
                "success": False,
                "message": "New password must be different from current password",
            },
            status=400,
        )

    try:
        user.set_password(new_password)
        user.save(update_fields=["password"])

        dispatch_result = notify_password_changed(
            user=user,
            request=request,
            actor=user,
        )

        if dispatch_result["notification_created"]:
            logger.info(
                "Password changed and auth notification dispatched successfully for user=%s",
                user.username,
            )
        else:
            logger.warning(
                "Password changed but auth notification was not created for user=%s",
                user.username,
            )

        return _ok(
            {
                "message": "Password updated successfully",
                "notification_created": dispatch_result["notification_created"],
                "email_sent": dispatch_result["email_sent"],
                "email_error": dispatch_result["email_error"],
                "whatsapp_sent": dispatch_result["whatsapp_sent"],
                "whatsapp_error": dispatch_result["whatsapp_error"],
            }
        )

    except Exception as exc:
        logger.exception("Failed to change password: %s", exc)
        return JsonResponse(
            {
                "success": False,
                "message": "Failed to change password",
                "details": str(exc),
            },
            status=500,
        )