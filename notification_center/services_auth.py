# ============================================================
# 📂 notification_center/services_auth.py
# 🧠 Auth Notification Services — Mham Cloud V1.1
# ------------------------------------------------------------
# ✅ طبقة رسمية موحدة لإشعارات Auth
# ✅ مبنية فوق Notification Center 2.0
# ✅ بدون أي إرسال مباشر داخل ملفات API
# ✅ تدعم:
#    - password_changed
#    - password_reset_completed
#    - profile_updated
#    - avatar_updated
# ------------------------------------------------------------

from __future__ import annotations

from typing import Any

from django.conf import settings

from notification_center.services import create_notification

try:
    from company_manager.models import CompanyUser
except Exception:
    CompanyUser = None

try:
    from company_manager.models import Company
except Exception:
    Company = None


# ============================================================
# Helpers
# ============================================================

def _clean_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _get_full_name(user) -> str:
    if not user:
        return "User"

    try:
        full_name = (user.get_full_name() or "").strip()
    except Exception:
        full_name = ""

    return (
        full_name
        or _clean_text(getattr(user, "full_name", ""))
        or _clean_text(getattr(user, "username", ""))
        or _clean_text(getattr(user, "email", ""))
        or "User"
    )


def _get_frontend_base_url() -> str:
    return (
        getattr(settings, "FRONTEND_BASE_URL", None)
        or getattr(settings, "FRONTEND_URL", None)
        or getattr(settings, "NEXT_PUBLIC_APP_URL", None)
        or "https://mhamcloud.com"
    ).rstrip("/")


def get_login_url() -> str:
    return f"{_get_frontend_base_url()}/login"


def get_profile_url(*, user=None, request=None) -> str:
    base_url = _get_frontend_base_url()

    active_company_id = None
    if request is not None:
        try:
            active_company_id = request.session.get("active_company_id")
        except Exception:
            active_company_id = None

    is_company_user = False

    if active_company_id:
        is_company_user = True

    if not is_company_user and user is not None and CompanyUser is not None:
        try:
            is_company_user = CompanyUser.objects.filter(
                user=user,
                is_active=True,
            ).exists()
        except Exception:
            is_company_user = False

    if is_company_user:
        return f"{base_url}/company/profile"

    return f"{base_url}/system/profile"


def get_active_company_from_request(*, request=None, user=None):
    active_company_id = None

    if request is not None:
        try:
            active_company_id = request.session.get("active_company_id")
        except Exception:
            active_company_id = None

    if active_company_id and Company is not None:
        try:
            company = Company.objects.filter(id=active_company_id).first()
            if company:
                return company
        except Exception:
            pass

    if user is not None and CompanyUser is not None:
        try:
            link = (
                CompanyUser.objects
                .select_related("company")
                .filter(
                    user=user,
                    is_active=True,
                    company__isnull=False,
                )
                .order_by("-id")
                .first()
            )
            if link and link.company:
                return link.company
        except Exception:
            pass

    return None


def resolve_language_code(user=None) -> str:
    """
    اعتماد لغة المستخدم إن وجدت، وإلا العربية افتراضيًا.
    """
    if not user:
        return "ar"

    preferred_language = _clean_text(getattr(user, "preferred_language", ""))
    if preferred_language in {"ar", "en"}:
        return preferred_language

    for profile_attr in ["profile", "userprofile"]:
        profile = getattr(user, profile_attr, None)
        if not profile:
            continue

        profile_language = _clean_text(getattr(profile, "preferred_language", ""))
        if profile_language in {"ar", "en"}:
            return profile_language

    return "ar"


def _base_auth_context(*, user, request=None, company=None) -> dict:
    resolved_company = company or get_active_company_from_request(
        request=request,
        user=user,
    )

    return {
        "recipient_name": _get_full_name(user),
        "username": _clean_text(getattr(user, "username", "")),
        "email": _clean_text(getattr(user, "email", "")),
        "login_url": get_login_url(),
        "profile_url": get_profile_url(user=user, request=request),
        "company_name": _clean_text(getattr(resolved_company, "name", "")) if resolved_company else "",
    }


def _dispatch_auth_notification(
    *,
    user,
    request=None,
    title: str,
    message: str,
    event_code: str,
    context: dict | None = None,
    company=None,
    actor=None,
    severity: str = "success",
    template_key: str | None = None,
) -> dict:
    resolved_company = company or get_active_company_from_request(
        request=request,
        user=user,
    )
    language_code = resolve_language_code(user)

    final_context = _base_auth_context(
        user=user,
        request=request,
        company=resolved_company,
    )
    if context:
        final_context.update(context)

    note = create_notification(
        recipient=user,
        title=title,
        message=message,
        notification_type="auth",
        severity=severity,
        send_email=True,
        send_whatsapp=True,
        company=resolved_company,
        event_code=event_code,
        event_group="auth",
        actor=actor,
        target_user=user,
        language_code=language_code,
        source=f"notification_center.services_auth.{event_code}",
        context=final_context,
        target_object=user,
        template_key=template_key or event_code,
    )

    return {
        "notification_created": bool(note),
        "email_sent": bool(note),
        "email_error": None,
        "whatsapp_sent": bool(note),
        "whatsapp_error": None,
    }


# ============================================================
# Public Auth Notification APIs
# ============================================================

def notify_password_changed(
    *,
    user,
    request=None,
    actor=None,
) -> dict:
    return _dispatch_auth_notification(
        user=user,
        request=request,
        actor=actor or user,
        title="تم تغيير كلمة المرور بنجاح",
        message=(
            "تم تغيير كلمة مرور حسابك بنجاح. "
            "إذا لم تكن أنت من قام بهذا التغيير، يرجى التواصل مع مسؤول النظام فورًا."
        ),
        event_code="password_changed",
        template_key="password_changed",
    )


def notify_password_reset_completed(
    *,
    user,
    request=None,
    actor=None,
    reset_flow: str = "guest_reset",
) -> dict:
    return _dispatch_auth_notification(
        user=user,
        request=request,
        actor=actor,
        title="تمت إعادة تعيين كلمة المرور بنجاح",
        message=(
            "تمت إعادة تعيين كلمة مرور حسابك بنجاح. "
            "إذا لم تكن أنت من قام بهذا الإجراء، يرجى التواصل مع مسؤول النظام فورًا."
        ),
        event_code="password_reset_completed",
        template_key="password_reset_completed",
        context={
            "reset_flow": _clean_text(reset_flow),
        },
    )


def notify_profile_updated(
    *,
    user,
    request=None,
    actor=None,
    old_email: str = "",
    new_email: str = "",
    full_name: str = "",
    phone: str = "",
) -> dict:
    return _dispatch_auth_notification(
        user=user,
        request=request,
        actor=actor or user,
        title="تم تحديث بيانات الملف الشخصي",
        message=(
            "تم تحديث بيانات ملفك الشخصي بنجاح. "
            "إذا لم تكن أنت من قام بهذا التغيير، يرجى تغيير كلمة المرور والتواصل مع مسؤول النظام فورًا."
        ),
        event_code="profile_updated",
        template_key="profile_updated",
        context={
            "old_email": _clean_text(old_email),
            "new_email": _clean_text(new_email),
            "full_name": _clean_text(full_name),
            "phone": _clean_text(phone),
        },
    )


def notify_avatar_updated(
    *,
    user,
    avatar_url: str,
    request=None,
    actor=None,
) -> dict:
    return _dispatch_auth_notification(
        user=user,
        request=request,
        actor=actor or user,
        title="تم تحديث الصورة الشخصية لحسابك",
        message=(
            "تم تحديث الصورة الشخصية المرتبطة بحسابك بنجاح. "
            "إذا لم تكن أنت من قام بهذا التغيير، يرجى التواصل مع مسؤول النظام فورًا."
        ),
        event_code="avatar_updated",
        template_key="avatar_updated",
        context={
            "avatar_url": _clean_text(avatar_url),
        },
    )