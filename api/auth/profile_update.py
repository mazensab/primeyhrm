# ============================================================
# 📂 api/auth/profile_update.py
# Mham Cloud
# Update Current User Profile
# Final Clean Version using notification_center/services_auth.py
# يدعم:
# - مستخدمي النظام
# - مستخدمي الشركات لاحقًا
# ============================================================

from __future__ import annotations

import json
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from auth_center.models import UserProfile
from notification_center.services_auth import notify_profile_updated
from whatsapp_center.utils import normalize_phone_number

logger = logging.getLogger(__name__)
User = get_user_model()

try:
    from employee_center.models import Employee
except Exception:
    Employee = None


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


def _normalize_text(value: str) -> str:
    return (value or "").strip()


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _normalize_phone(value: str) -> str:
    return (value or "").strip()


def _split_full_name(full_name: str) -> tuple[str, str]:
    full_name = _normalize_text(full_name)

    if not full_name:
        return "", ""

    parts = full_name.split()

    if len(parts) == 1:
        return parts[0], ""

    return parts[0], " ".join(parts[1:])


def _bad_request(message: str, errors: dict | None = None):
    return JsonResponse(
        {
            "success": False,
            "error": message,
            "errors": errors or {},
        },
        status=400,
    )


def _ok(data: dict | None = None, status: int = 200):
    payload = {"success": True}
    if data:
        payload.update(data)
    return JsonResponse(payload, status=status)


# ============================================================
# Update Current User Profile
# ============================================================

@login_required
@require_POST
@csrf_exempt
def profile_update(request):
    payload = _json_body(request)

    full_name = _normalize_text(payload.get("full_name"))
    email = _normalize_email(payload.get("email"))
    phone = _normalize_phone(payload.get("phone"))

    errors = {}

    if not full_name:
        errors["full_name"] = "Full name is required"

    if not email:
        errors["email"] = "Email is required"
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors["email"] = "Invalid email format"

    if errors:
        return _bad_request("Validation failed", errors)

    existing = (
        User.objects
        .filter(email__iexact=email)
        .exclude(id=request.user.id)
        .exists()
    )
    if existing:
        return _bad_request(
            "Email already in use",
            {"email": "This email is already used by another account"},
        )

    first_name, last_name = _split_full_name(full_name)
    user = request.user
    old_email = user.email or ""

    normalized_whatsapp_phone = normalize_phone_number(phone) if phone else ""
    stored_phone = phone or ""
    stored_whatsapp_phone = normalized_whatsapp_phone or ""

    with transaction.atomic():
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save(update_fields=["first_name", "last_name", "email"])

        if Employee is not None:
            active_company_id = request.session.get("active_company_id")
            if active_company_id:
                Employee.objects.filter(
                    user=user,
                    company_id=active_company_id,
                ).update(full_name=full_name)

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.phone_number = stored_phone or None
        profile.whatsapp_number = stored_whatsapp_phone or None
        profile.save(update_fields=["phone_number", "whatsapp_number"])

        transaction.on_commit(
            lambda: notify_profile_updated(
                user=user,
                request=request,
                actor=user,
                old_email=old_email,
                new_email=email,
                full_name=full_name,
                phone=stored_whatsapp_phone or stored_phone,
            )
        )

    return _ok(
        {
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email or "",
                "full_name": full_name,
                "phone": stored_whatsapp_phone or stored_phone,
            },
        }
    )