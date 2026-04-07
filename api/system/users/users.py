# ============================================================
# 📂 api/system/users.py
# Mham Cloud
# System Internal Users API
# ============================================================
# المستخدمون الداخليون:
# - SUPER_ADMIN  -> Django is_superuser = True
# - SYSTEM_ADMIN -> Django Group: SYSTEM_ADMIN
# - SUPPORT      -> Django Group: SUPPORT
#
# هذه الطبقة لا تعتمد على CompanyUser كأساس للصلاحيات،
# بل تعتمد على Django User + Group لإدارة مستخدمي النظام الداخلي.
#
# ✅ القرار المعتمد:
# مستخدمو النظام الداخلي يجب أن يرتبطوا بنفس الشركة الداخلية الموجودة
# أصلًا في النظام (مثل superadmin) — بدون إنشاء شركة جديدة.
# ✅ تم تنظيف الإرسال المباشر للبريد والواتساب من هذا الملف
# ✅ تم الاعتماد على notification_center/services_system_users.py
# ============================================================

from __future__ import annotations

import json
import logging
import secrets
from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from auth_center.models import UserProfile
from company_manager.models import CompanyUser
from notification_center.services_system_users import (
    notify_system_user_created,
    notify_system_user_deleted,
    notify_system_user_password_changed,
    notify_system_user_role_changed,
    notify_system_user_status_changed,
)

User = get_user_model()
logger = logging.getLogger(__name__)

# ============================================================
# Constants
# ============================================================

ROLE_SUPER_ADMIN = "SUPER_ADMIN"
ROLE_SYSTEM_ADMIN = "SYSTEM_ADMIN"
ROLE_SUPPORT = "SUPPORT"

ALLOWED_ROLES = {
    ROLE_SUPER_ADMIN,
    ROLE_SYSTEM_ADMIN,
    ROLE_SUPPORT,
}

DEFAULT_INTERNAL_COMPANY_NAME = "Primey Default Company"


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


def _forbidden(message: str = "Permission denied"):
    return JsonResponse(
        {
            "success": False,
            "error": message,
        },
        status=403,
    )


def _bad_request(message: str = "Bad request", errors: Optional[dict] = None):
    return JsonResponse(
        {
            "success": False,
            "error": message,
            "errors": errors or {},
        },
        status=400,
    )


def _ok(data: Optional[dict] = None, status: int = 200):
    payload = {"success": True}
    if data:
        payload.update(data)
    return JsonResponse(payload, status=status)


def _require_superuser(request):
    if not request.user.is_authenticated:
        return _forbidden("Authentication required")

    if not request.user.is_superuser:
        return _forbidden("Only super admin can manage system users")

    return None


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _normalize_username(value: str) -> str:
    return (value or "").strip().lower()


def _normalize_phone(value: str) -> str:
    return (value or "").strip()


def _split_full_name(full_name: str) -> tuple[str, str]:
    full_name = (full_name or "").strip()
    if not full_name:
        return "", ""

    parts = full_name.split()
    if len(parts) == 1:
        return parts[0], ""

    return parts[0], " ".join(parts[1:])


def _get_full_name(user) -> str:
    full_name = (user.get_full_name() or "").strip()
    return full_name or user.username


def _get_user_avatar(user) -> str | None:
    profile = (
        UserProfile.objects
        .filter(user=user)
        .only("avatar_url")
        .first()
    )

    if profile and profile.avatar_url:
        return profile.avatar_url

    return None


def _get_user_profile(user):
    return UserProfile.objects.filter(user=user).first()


def _get_or_create_user_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _save_user_phone(user, phone: str) -> str:
    """
    حفظ رقم الجوال داخل UserProfile بشكل موحد.
    """
    phone = _normalize_phone(phone)
    if not phone:
        return ""

    profile = _get_or_create_user_profile(user)
    profile.phone_number = phone
    profile.whatsapp_number = phone
    profile.save(update_fields=["phone_number", "whatsapp_number"])
    return phone


def _first_non_empty(*values) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _get_user_whatsapp_phone(user) -> str:
    """
    محاولة آمنة لاستخراج رقم جوال/واتساب من:
    1) حقول شائعة داخل User
    2) حقول شائعة داخل UserProfile
    """
    user_phone = _first_non_empty(
        getattr(user, "phone", ""),
        getattr(user, "phone_number", ""),
        getattr(user, "mobile", ""),
        getattr(user, "mobile_number", ""),
        getattr(user, "whatsapp_number", ""),
    )
    if user_phone:
        return user_phone

    profile = _get_user_profile(user)
    if not profile:
        return ""

    profile_phone = _first_non_empty(
        getattr(profile, "phone", ""),
        getattr(profile, "phone_number", ""),
        getattr(profile, "mobile", ""),
        getattr(profile, "mobile_number", ""),
        getattr(profile, "whatsapp_number", ""),
    )
    return profile_phone


def _get_internal_role(user) -> Optional[str]:
    """
    أولوية تحديد الدور:
    1) is_superuser => SUPER_ADMIN
    2) Group SYSTEM_ADMIN
    3) Group SUPPORT
    """
    if user.is_superuser:
        return ROLE_SUPER_ADMIN

    group_names = set(user.groups.values_list("name", flat=True))

    if ROLE_SYSTEM_ADMIN in group_names:
        return ROLE_SYSTEM_ADMIN

    if ROLE_SUPPORT in group_names:
        return ROLE_SUPPORT

    return None


def _ensure_group(name: str) -> Group:
    group, _ = Group.objects.get_or_create(name=name)
    return group


def _clear_internal_groups(user):
    user.groups.remove(
        *Group.objects.filter(name__in=[ROLE_SYSTEM_ADMIN, ROLE_SUPPORT])
    )


def _apply_internal_role(user, role: str):
    """
    تطبيق الدور الداخلي على المستخدم:
    - SUPER_ADMIN: is_superuser=True, is_staff=True, إزالة المجموعات الأخرى
    - SYSTEM_ADMIN: is_superuser=False, is_staff=True, Group SYSTEM_ADMIN
    - SUPPORT: is_superuser=False, is_staff=True, Group SUPPORT
    """
    if role not in ALLOWED_ROLES:
        raise ValueError("Invalid role")

    _clear_internal_groups(user)

    if role == ROLE_SUPER_ADMIN:
        user.is_superuser = True
        user.is_staff = True
        user.save(update_fields=["is_superuser", "is_staff"])
        return

    user.is_superuser = False
    user.is_staff = True
    user.save(update_fields=["is_superuser", "is_staff"])

    group = _ensure_group(role)
    user.groups.add(group)


def _is_internal_user(user) -> bool:
    if user.is_superuser or user.is_staff:
        return True

    return user.groups.filter(name__in=[ROLE_SYSTEM_ADMIN, ROLE_SUPPORT]).exists()


def _serialize_user(user) -> dict:
    role = _get_internal_role(user) or ROLE_SUPPORT
    avatar = _get_user_avatar(user)
    phone = _get_user_whatsapp_phone(user)

    return {
        "id": user.id,
        "full_name": _get_full_name(user),
        "username": user.username,
        "email": user.email or "",
        "phone": phone,
        "avatar": avatar,
        "role": role,
        "status": "ACTIVE" if user.is_active else "INACTIVE",
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.date_joined.date().isoformat() if user.date_joined else None,
        "is_superuser": bool(user.is_superuser),
        "is_staff": bool(user.is_staff),
    }


def _generate_temp_password(length: int = 12) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _model_field_names() -> set[str]:
    return {field.name for field in User._meta.get_fields()}


def _get_internal_company_for_system_users(actor=None):
    """
    جلب الشركة الداخلية الموجودة أصلًا دون إنشاء شركة جديدة.

    أولوية الاختيار:
    1) شركة باسم Primey Default Company مرتبطة بسوبر أدمن
    2) أول شركة فعّالة مرتبطة بالسوبر أدمن الحالي (actor)
    3) أول شركة فعّالة مرتبطة بأي سوبر أدمن في النظام
    """
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
    if default_link and default_link.company:
        return default_link.company

    if actor and getattr(actor, "is_superuser", False):
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
        if actor_link and actor_link.company:
            return actor_link.company

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
    if any_superadmin_link and any_superadmin_link.company:
        return any_superadmin_link.company

    return None


def _ensure_internal_company_membership(user, actor=None):
    """
    ربط مستخدم النظام الداخلي بنفس الشركة الداخلية الموجودة أصلًا.
    لا يتم إنشاء شركة جديدة نهائيًا.
    """
    company = _get_internal_company_for_system_users(actor=actor)

    if not company:
        return

    link, created = CompanyUser.objects.get_or_create(
        user=user,
        company=company,
        defaults={
            "role": None,
            "is_active": True,
        },
    )

    if not created and not link.is_active:
        link.is_active = True
        link.save(update_fields=["is_active"])


# ============================================================
# GET /api/system/users/
# ============================================================

@login_required
@require_GET
def system_users_list(request):
    denied = _require_superuser(request)
    if denied:
        return denied

    q = (request.GET.get("q") or "").strip()

    users = User.objects.all().order_by("-date_joined")
    users = [user for user in users if _is_internal_user(user)]

    if q:
        q_lower = q.lower()
        users = [
            user for user in users
            if q_lower in (user.username or "").lower()
            or q_lower in (user.email or "").lower()
            or q_lower in _get_full_name(user).lower()
        ]

    return _ok({
        "users": [_serialize_user(user) for user in users],
        "count": len(users),
        "roles": [
            {"code": ROLE_SUPER_ADMIN, "label": "Super Admin"},
            {"code": ROLE_SYSTEM_ADMIN, "label": "System Admin"},
            {"code": ROLE_SUPPORT, "label": "Support"},
        ],
    })


# ============================================================
# GET /api/system/users/roles/
# ============================================================

@login_required
@require_GET
def system_user_roles(request):
    denied = _require_superuser(request)
    if denied:
        return denied

    return _ok({
        "roles": [
            {
                "code": ROLE_SUPER_ADMIN,
                "label": "Super Admin",
                "description": "صلاحية كاملة على النظام والإعدادات الحساسة",
            },
            {
                "code": ROLE_SYSTEM_ADMIN,
                "label": "System Admin",
                "description": "إدارة تشغيلية وضبط عام للمنصة",
            },
            {
                "code": ROLE_SUPPORT,
                "label": "Support",
                "description": "دعم العملاء ومتابعة المشاكل التشغيلية",
            },
        ]
    })


# ============================================================
# POST /api/system/users/create/
# ============================================================

@login_required
@require_POST
def system_user_create(request):
    denied = _require_superuser(request)
    if denied:
        return denied

    data = _json_body(request)

    full_name = (data.get("full_name") or "").strip()
    username = _normalize_username(data.get("username"))
    email = _normalize_email(data.get("email"))
    phone = _normalize_phone(data.get("phone"))
    password = (data.get("password") or "").strip()
    role = (data.get("role") or ROLE_SYSTEM_ADMIN).strip().upper()
    status = (data.get("status") or "ACTIVE").strip().upper()

    errors = {}

    if not full_name:
        errors["full_name"] = "Full name is required"

    if not username:
        errors["username"] = "Username is required"
    elif len(username) < 3:
        errors["username"] = "Username must be at least 3 characters"

    if not email:
        errors["email"] = "Email is required"

    if role not in ALLOWED_ROLES:
        errors["role"] = "Invalid role"

    if status not in {"ACTIVE", "INACTIVE"}:
        errors["status"] = "Invalid status"

    if username and User.objects.filter(username__iexact=username).exists():
        errors["username"] = "Username already exists"

    if email and User.objects.filter(email__iexact=email).exists():
        errors["email"] = "Email already exists"

    if errors:
        return _bad_request("Validation error", errors)

    first_name, last_name = _split_full_name(full_name)

    if not password:
        password = _generate_temp_password()

    created_user = None

    try:
        with transaction.atomic():
            field_names = _model_field_names()
            user = User()

            if "username" in field_names:
                user.username = username

            if "email" in field_names:
                user.email = email

            if "first_name" in field_names:
                user.first_name = first_name

            if "last_name" in field_names:
                user.last_name = last_name

            if "is_active" in field_names:
                user.is_active = (status == "ACTIVE")

            if "is_staff" in field_names:
                user.is_staff = True

            user.set_password(password)
            user.save()

            _apply_internal_role(user, role)
            _ensure_internal_company_membership(
                user=user,
                actor=request.user,
            )

            if phone:
                _save_user_phone(user, phone)

            created_user = user

        notify_result = notify_system_user_created(
            user=created_user,
            password=password,
            role=role,
            actor=request.user,
            company=_get_internal_company_for_system_users(actor=request.user),
        )

        return _ok({
            "message": "System user created successfully",
            "user": _serialize_user(created_user),
            "temporary_password": password,
            "notification_created": notify_result.get("notification_created", False),
            "email_sent": notify_result.get("email_sent", False),
            "email_error": notify_result.get("email_error"),
            "whatsapp_sent": notify_result.get("whatsapp_sent", False),
            "whatsapp_error": notify_result.get("whatsapp_error"),
        }, status=201)

    except IntegrityError as exc:
        return JsonResponse(
            {
                "success": False,
                "error": "Failed to create system user",
                "details": str(exc),
            },
            status=400,
        )

    except Exception as exc:
        logger.exception("Failed to create system user: %s", exc)
        return JsonResponse(
            {
                "success": False,
                "error": "Failed to create system user",
                "details": str(exc),
            },
            status=500,
        )


# ============================================================
# POST /api/system/users/toggle-status/
# ============================================================

@login_required
@require_POST
def system_user_toggle_status(request):
    denied = _require_superuser(request)
    if denied:
        return denied

    data = _json_body(request)
    user_id = data.get("user_id")

    if not user_id:
        return _bad_request("user_id is required")

    user = User.objects.filter(id=user_id).first()
    if not user or not _is_internal_user(user):
        return JsonResponse(
            {"success": False, "error": "System user not found"},
            status=404,
        )

    if user.id == request.user.id:
        return _bad_request("You cannot disable your own current account")

    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])

    notify_result = notify_system_user_status_changed(
        user=user,
        is_active=user.is_active,
        actor=request.user,
        company=_get_internal_company_for_system_users(actor=request.user),
    )

    return _ok({
        "message": "User status updated successfully",
        "notification_created": notify_result.get("notification_created", False),
        "email_sent": notify_result.get("email_sent", False),
        "email_error": notify_result.get("email_error"),
        "whatsapp_sent": notify_result.get("whatsapp_sent", False),
        "whatsapp_error": notify_result.get("whatsapp_error"),
        "user": _serialize_user(user),
    })


# ============================================================
# POST /api/system/users/change-role/
# ============================================================

@login_required
@require_POST
def system_user_change_role(request):
    denied = _require_superuser(request)
    if denied:
        return denied

    data = _json_body(request)
    user_id = data.get("user_id")
    role = (data.get("role") or "").strip().upper()

    if not user_id:
        return _bad_request("user_id is required")

    if role not in ALLOWED_ROLES:
        return _bad_request("Invalid role")

    user = User.objects.filter(id=user_id).first()
    if not user or not _is_internal_user(user):
        return JsonResponse(
            {"success": False, "error": "System user not found"},
            status=404,
        )

    old_role = _get_internal_role(user) or ROLE_SUPPORT

    try:
        with transaction.atomic():
            _apply_internal_role(user, role)
            _ensure_internal_company_membership(
                user=user,
                actor=request.user,
            )

        notify_result = notify_system_user_role_changed(
            user=user,
            old_role=old_role,
            new_role=role,
            actor=request.user,
            company=_get_internal_company_for_system_users(actor=request.user),
        )

        return _ok({
            "message": "User role updated successfully",
            "notification_created": notify_result.get("notification_created", False),
            "email_sent": notify_result.get("email_sent", False),
            "email_error": notify_result.get("email_error"),
            "whatsapp_sent": notify_result.get("whatsapp_sent", False),
            "whatsapp_error": notify_result.get("whatsapp_error"),
            "user": _serialize_user(user),
        })

    except Exception as exc:
        logger.exception("Failed to update role: %s", exc)
        return JsonResponse(
            {
                "success": False,
                "error": "Failed to update role",
                "details": str(exc),
            },
            status=500,
        )


# ============================================================
# POST /api/system/users/reset-password/
# ============================================================

@login_required
@require_POST
def system_user_reset_password(request):
    denied = _require_superuser(request)
    if denied:
        return denied

    data = _json_body(request)
    user_id = data.get("user_id")
    new_password = (data.get("new_password") or "").strip()

    if not user_id:
        return _bad_request("user_id is required")

    user = User.objects.filter(id=user_id).first()
    if not user or not _is_internal_user(user):
        return JsonResponse(
            {"success": False, "error": "System user not found"},
            status=404,
        )

    if not new_password:
        new_password = _generate_temp_password()

    try:
        user.set_password(new_password)
        user.save(update_fields=["password"])

        notify_result = notify_system_user_password_changed(
            user=user,
            actor=request.user,
            company=_get_internal_company_for_system_users(actor=request.user),
            temporary_password=new_password,
        )

        return _ok({
            "message": "Password reset successfully",
            "user_id": user.id,
            "temporary_password": new_password,
            "notification_created": notify_result.get("notification_created", False),
            "email_sent": notify_result.get("email_sent", False),
            "email_error": notify_result.get("email_error"),
            "whatsapp_sent": notify_result.get("whatsapp_sent", False),
            "whatsapp_error": notify_result.get("whatsapp_error"),
        })

    except Exception as exc:
        logger.exception("Failed to reset password: %s", exc)
        return JsonResponse(
            {
                "success": False,
                "error": "Failed to reset password",
                "details": str(exc),
            },
            status=500,
        )


# ============================================================
# POST /api/system/users/delete/
# ============================================================

@login_required
@require_POST
def system_user_delete(request):
    denied = _require_superuser(request)
    if denied:
        return denied

    data = _json_body(request)
    user_id = data.get("user_id")

    if not user_id:
        return _bad_request("user_id is required")

    user = User.objects.filter(id=user_id).first()
    if not user or not _is_internal_user(user):
        return JsonResponse(
            {"success": False, "error": "System user not found"},
            status=404,
        )

    if user.id == request.user.id:
        return _bad_request("You cannot delete your own current account")

    username = user.username or ""

    notify_result = notify_system_user_deleted(
        user=user,
        actor=request.user,
        company=_get_internal_company_for_system_users(actor=request.user),
    )

    user.delete()

    return _ok({
        "message": "System user deleted successfully",
        "username": username,
        "notification_created": notify_result.get("notification_created", False),
        "email_sent": notify_result.get("email_sent", False),
        "email_error": notify_result.get("email_error"),
        "whatsapp_sent": notify_result.get("whatsapp_sent", False),
        "whatsapp_error": notify_result.get("whatsapp_error"),
    })