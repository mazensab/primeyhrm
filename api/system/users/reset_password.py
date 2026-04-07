# ============================================================
# Reset User Password
# Mham Cloud
# Legacy / Compatibility Endpoint
# ============================================================
# ✅ تم تنظيف الإرسال المباشر للبريد من هذا الملف
# ✅ تم الاعتماد على notification_center/services_system_users.py
# ✅ الحفاظ على التوافق مع الـ legacy endpoint الحالي
# ============================================================

from __future__ import annotations

import json
import logging
import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from notification_center.services_system_users import (
    notify_system_user_password_changed,
)

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


def _generate_temp_password(length: int = 12) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ============================================================
# Endpoint
# ============================================================

@login_required
@require_POST
def reset_password(request):
    try:
        data = _json_body(request)

        user_id = data.get("user_id")
        password = (data.get("new_password") or data.get("password") or "").strip()

        if not user_id:
            return JsonResponse({
                "success": False,
                "error": "Missing user_id",
            }, status=400)

        user = User.objects.get(id=user_id)

        # ----------------------------------------------------
        # حماية السوبر ادمن
        # فقط سوبر ادمن يستطيع تغيير كلمة مرور سوبر ادمن
        # ----------------------------------------------------
        if user.is_superuser and not request.user.is_superuser:
            return JsonResponse({
                "success": False,
                "error": "Only Super Admin can change this password",
            }, status=403)

        # ----------------------------------------------------
        # إذا لم يتم تمرير كلمة مرور نولد مؤقتة
        # ----------------------------------------------------
        if not password:
            password = _generate_temp_password()

        # ----------------------------------------------------
        # تشفير كلمة المرور
        # ----------------------------------------------------
        user.set_password(password)
        user.save(update_fields=["password"])

        notify_result = notify_system_user_password_changed(
            user=user,
            actor=request.user,
            temporary_password=password,
        )

        return JsonResponse({
            "success": True,
            "message": "Password updated successfully",
            "notification_created": notify_result.get("notification_created", False),
            "email_sent": notify_result.get("email_sent", False),
            "email_error": notify_result.get("email_error"),
            "whatsapp_sent": notify_result.get("whatsapp_sent", False),
            "whatsapp_error": notify_result.get("whatsapp_error"),
            "temporary_password": password,
        })

    except User.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "User not found",
        }, status=404)

    except Exception as exc:
        logger.exception("Legacy reset_password failed: %s", exc)
        return JsonResponse({
            "success": False,
            "error": str(exc),
        }, status=500)