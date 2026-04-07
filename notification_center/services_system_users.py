# ============================================================
# 📂 notification_center/services_system_users.py
# 🧠 System Users Notification Services — Mham Cloud V1.0
# ------------------------------------------------------------
# ✅ طبقة رسمية موحدة لإشعارات المستخدمين الداخليين
# ✅ مبنية فوق Notification Center 2.0
# ✅ بدون أي إرسال مباشر داخل api/system/users.py
# ✅ تدعم:
#    - system_user_created
#    - system_user_password_changed
#    - system_user_role_changed
#    - system_user_status_changed
#    - system_user_deleted
# ✅ جاهزة للربط مع create_notification + event/delivery
# ------------------------------------------------------------

from __future__ import annotations

from typing import Any, Optional

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

try:
    from auth_center.models import UserProfile
except Exception:
    UserProfile = None


# ============================================================
# Constants
# ============================================================
ROLE_SUPER_ADMIN = "SUPER_ADMIN"
ROLE_SYSTEM_ADMIN = "SYSTEM_ADMIN"
ROLE_SUPPORT = "SUPPORT"

DEFAULT_INTERNAL_COMPANY_NAME = "Primey Default Company"


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


def get_system_users_url() -> str:
    return f"{_get_frontend_base_url()}/system/users"


def _get_user_profile(user):
    if not user or UserProfile is None:
        return None

    try:
        return UserProfile.objects.filter(user=user).first()
    except Exception:
        return None


def _get_user_phone(user) -> str:
    """
    محاولة مرنة لاستخراج رقم الجوال/واتساب من المستخدم أو الـ profile.
    """
    if not user:
        return ""

    direct_fields = [
        "phone",
        "phone_number",
        "mobile",
        "mobile_number",
        "whatsapp_number",
    ]

    for field_name in direct_fields:
        value = _clean_text(getattr(user, field_name, ""))
        if value:
            return value

    profile = _get_user_profile(user)
    if not profile:
        return ""

    for field_name in direct_fields:
        value = _clean_text(getattr(profile, field_name, ""))
        if value:
            return value

    return ""


def _resolve_language_code(user=None, default: str = "ar") -> str:
    if not user:
        return default

    preferred_language = _clean_text(getattr(user, "preferred_language", ""))
    if preferred_language in {"ar", "en"}:
        return preferred_language

    profile = _get_user_profile(user)
    if profile:
        profile_language = _clean_text(getattr(profile, "preferred_language", ""))
        if profile_language in {"ar", "en"}:
            return profile_language

    return default


def _get_internal_role(user) -> str:
    """
    أولوية تحديد الدور:
    1) is_superuser => SUPER_ADMIN
    2) Group SYSTEM_ADMIN
    3) Group SUPPORT
    """
    if not user:
        return ROLE_SUPPORT

    try:
        if bool(getattr(user, "is_superuser", False)):
            return ROLE_SUPER_ADMIN
    except Exception:
        pass

    try:
        group_names = set(user.groups.values_list("name", flat=True))
    except Exception:
        group_names = set()

    if ROLE_SYSTEM_ADMIN in group_names:
        return ROLE_SYSTEM_ADMIN

    if ROLE_SUPPORT in group_names:
        return ROLE_SUPPORT

    return ROLE_SUPPORT


def _get_internal_company_for_system_users(actor=None):
    """
    جلب الشركة الداخلية الموجودة أصلًا دون إنشاء شركة جديدة.

    أولوية الاختيار:
    1) شركة باسم Primey Default Company مرتبطة بسوبر أدمن
    2) أول شركة فعّالة مرتبطة بالسوبر أدمن الحالي (actor)
    3) أول شركة فعّالة مرتبطة بأي سوبر أدمن في النظام
    """
    if CompanyUser is None:
        return None

    try:
        default_link = (
            CompanyUser.objects
            .select_related("company", "user")
            .filter(
                user__is_superuser=True,
                is_active=True,
                company__name=DEFAULT_INTERNAL_COMPANY_NAME,
            )
            .order_by("id")
            .first()
        )
        if default_link and getattr(default_link, "company", None):
            return default_link.company
    except Exception:
        pass

    if actor is not None and getattr(actor, "is_superuser", False):
        try:
            actor_link = (
                CompanyUser.objects
                .select_related("company")
                .filter(
                    user=actor,
                    is_active=True,
                )
                .order_by("id")
                .first()
            )
            if actor_link and getattr(actor_link, "company", None):
                return actor_link.company
        except Exception:
            pass

    try:
        any_superadmin_link = (
            CompanyUser.objects
            .select_related("company", "user")
            .filter(
                user__is_superuser=True,
                is_active=True,
            )
            .order_by("id")
            .first()
        )
        if any_superadmin_link and getattr(any_superadmin_link, "company", None):
            return any_superadmin_link.company
    except Exception:
        pass

    return None


def _base_system_user_context(*, user, actor=None, company=None) -> dict:
    resolved_company = company or _get_internal_company_for_system_users(actor=actor)

    return {
        "recipient_name": _get_full_name(user),
        "full_name": _get_full_name(user),
        "username": _clean_text(getattr(user, "username", "")),
        "email": _clean_text(getattr(user, "email", "")),
        "phone": _get_user_phone(user),
        "role": _get_internal_role(user),
        "login_url": get_login_url(),
        "system_users_url": get_system_users_url(),
        "company_name": _clean_text(getattr(resolved_company, "name", "")) if resolved_company else "",
    }


def _dispatch_system_user_notification(
    *,
    user,
    actor=None,
    title: str,
    message: str,
    event_code: str,
    context: dict | None = None,
    company=None,
    severity: str = "success",
    template_key: str | None = None,
    send_email: bool = True,
    send_whatsapp: bool = True,
    link: str | None = None,
) -> dict:
    resolved_company = company or _get_internal_company_for_system_users(actor=actor)
    language_code = _resolve_language_code(user)

    final_context = _base_system_user_context(
        user=user,
        actor=actor,
        company=resolved_company,
    )
    if isinstance(context, dict):
        final_context.update(context)

    note = create_notification(
        recipient=user,
        title=title,
        message=message,
        notification_type="system_user",
        severity=severity,
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        link=link or get_system_users_url(),
        company=resolved_company,
        event_code=event_code,
        event_group="system_user",
        actor=actor,
        target_user=user,
        language_code=language_code,
        source=f"notification_center.services_system_users.{event_code}",
        context=final_context,
        target_object=user,
        template_key=template_key or event_code,
        whatsapp_recipient_name=_get_full_name(user),
        whatsapp_recipient_role=_get_internal_role(user),
    )

    return {
        "notification_created": bool(note),
        "email_sent": bool(note) if send_email else False,
        "email_error": None,
        "whatsapp_sent": bool(note) if send_whatsapp else False,
        "whatsapp_error": None,
    }


# ============================================================
# Public System User Notification APIs
# ============================================================
def notify_system_user_created(
    *,
    user,
    password: str,
    role: str,
    actor=None,
    company=None,
) -> dict:
    return _dispatch_system_user_notification(
        user=user,
        actor=actor,
        company=company,
        title="تم إنشاء حسابك في Mham Cloud",
        message=(
            "تم إنشاء حسابك بنجاح كمستخدم داخلي في النظام. "
            "يمكنك تسجيل الدخول باستخدام البيانات المرسلة لك، "
            "ونوصي بتغيير كلمة المرور فور أول دخول."
        ),
        event_code="system_user_created",
        template_key="system_user_created",
        severity="success",
        context={
            "temporary_password": _clean_text(password),
            "role": _clean_text(role) or _get_internal_role(user),
        },
    )


def notify_system_user_password_changed(
    *,
    user,
    actor=None,
    company=None,
    temporary_password: str = "",
) -> dict:
    return _dispatch_system_user_notification(
        user=user,
        actor=actor,
        company=company,
        title="تم تغيير كلمة المرور بنجاح",
        message=(
            "تمت إعادة تعيين كلمة مرور حسابك بنجاح من خلال إدارة النظام. "
            "إذا لم تكن أنت من قام بهذا الإجراء، يرجى التواصل مع مسؤول النظام فورًا."
        ),
        event_code="system_user_password_changed",
        template_key="system_user_password_changed",
        severity="warning",
        context={
            "temporary_password": _clean_text(temporary_password),
        },
    )


def notify_system_user_role_changed(
    *,
    user,
    old_role: str,
    new_role: str,
    actor=None,
    company=None,
) -> dict:
    return _dispatch_system_user_notification(
        user=user,
        actor=actor,
        company=company,
        title="تم تحديث صلاحية حسابك",
        message=(
            "تم تغيير الدور أو الصلاحية المرتبطة بحسابك من خلال إدارة النظام. "
            "يرجى مراجعة بيانات الحساب الحالية."
        ),
        event_code="system_user_role_changed",
        template_key="system_user_role_changed",
        severity="info",
        context={
            "old_role": _clean_text(old_role),
            "new_role": _clean_text(new_role),
            "role": _clean_text(new_role) or _get_internal_role(user),
        },
    )


def notify_system_user_status_changed(
    *,
    user,
    is_active: bool,
    actor=None,
    company=None,
) -> dict:
    status_label = "ACTIVE" if bool(is_active) else "INACTIVE"

    return _dispatch_system_user_notification(
        user=user,
        actor=actor,
        company=company,
        title="تم تحديث حالة حسابك",
        message=(
            "تم تغيير حالة حسابك من خلال إدارة النظام. "
            "يرجى مراجعة الحالة الحالية لحسابك."
        ),
        event_code="system_user_status_changed",
        template_key="system_user_status_changed",
        severity="success" if bool(is_active) else "warning",
        context={
            "is_active": bool(is_active),
            "status": status_label,
        },
    )


def notify_system_user_deleted(
    *,
    user,
    actor=None,
    company=None,
) -> dict:
    """
    يستخدم قبل حذف المستخدم من قاعدة البيانات.
    """
    return _dispatch_system_user_notification(
        user=user,
        actor=actor,
        company=company,
        title="تم حذف حسابك من النظام",
        message=(
            "تم حذف حسابك الداخلي من نظام Mham Cloud من خلال إدارة النظام. "
            "إذا لم تكن تتوقع هذا الإجراء، يرجى التواصل مع مسؤول النظام فورًا."
        ),
        event_code="system_user_deleted",
        template_key="system_user_deleted",
        severity="error",
        context={},
    )