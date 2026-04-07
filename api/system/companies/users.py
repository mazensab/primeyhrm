# ===============================================================
# 👥 Company Users — SYSTEM API (Enhanced Actions + Enter As User)
# Mham Cloud
# ===============================================================

from __future__ import annotations

import json
import logging
import secrets
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from auth_center.models import ActiveUserSession, UserProfile
from company_manager.models import CompanyUser
from notification_center import services_auth as auth_notification_services
from notification_center import services_company as company_notification_services

User = get_user_model()
logger = logging.getLogger(__name__)

# ===============================================================
# Constants
# ===============================================================

ALLOWED_COMPANY_ROLES = {
    "OWNER",
    "ADMIN",
    "HR",
    "MANAGER",
    "EMPLOYEE",
}

IMPERSONATION_SESSION_KEYS = [
    "impersonation_active",
    "impersonation_source_user_id",
    "impersonation_source_username",
    "impersonation_source_email",
    "impersonation_company_id",
    "impersonation_company_name",
    "impersonation_company_user_id",
    "impersonation_target_user_id",
    "impersonation_target_username",
    "impersonation_target_role",
    "active_company_id",
]

# ===============================================================
# Helpers
# ===============================================================

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
            "error": message,
            "errors": errors or {},
        },
        status=400,
    )


def _not_found(message: str = "Not found"):
    return JsonResponse(
        {
            "success": False,
            "error": message,
        },
        status=404,
    )


def _forbidden(message: str = "Permission denied"):
    return JsonResponse(
        {
            "success": False,
            "error": message,
        },
        status=403,
    )


def _require_superuser(request):
    if not request.user.is_authenticated:
        return _forbidden("Authentication required")

    if not request.user.is_superuser:
        return _forbidden("Only super admin can manage company users")

    return None


def _require_internal_system_user(request):
    """
    السماح فقط لمستخدمي النظام الداخلي:
    - Super Admin
    - SYSTEM_ADMIN
    - SUPPORT
    """
    if not request.user.is_authenticated:
        return _forbidden("Authentication required")

    group_names = set(request.user.groups.values_list("name", flat=True))

    is_internal_system_user = (
        request.user.is_superuser
        or "SYSTEM_ADMIN" in group_names
        or "SUPPORT" in group_names
    )

    if not is_internal_system_user:
        return _forbidden("Only internal system users can enter company sessions")

    return None


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _normalize_username(value: str) -> str:
    return (value or "").strip().lower()


def _safe_value(value):
    return value if value not in (None, "") else "-"


def _generate_temp_password(length: int = 12) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _get_user_profile(user):
    return (
        UserProfile.objects
        .filter(user=user)
        .first()
    )


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


def _get_user_phone(user) -> str:
    # -----------------------------------------------------------
    # 1) نحاول أولًا من UserProfile لو وُجد لاحقًا فيه رقم
    # -----------------------------------------------------------
    profile = _get_user_profile(user)

    if profile:
        for attr in ["phone", "phone_number", "mobile", "mobile_number"]:
            if hasattr(profile, attr):
                value = getattr(profile, attr, "") or ""
                if value:
                    return str(value)

    # -----------------------------------------------------------
    # 2) Fallback إلى Employee.mobile_number
    # related_name في Employee هو: hr_employee
    # -----------------------------------------------------------
    try:
        employee = getattr(user, "hr_employee", None)
        if employee and getattr(employee, "mobile_number", None):
            return str(employee.mobile_number)
    except Exception:
        pass

    return ""


def _serialize_company_user(item: CompanyUser) -> dict:
    user = item.user

    return {
        "id": item.id,
        "user_id": user.id,
        "full_name": _get_full_name(user),
        "username": user.username,
        "email": user.email or "",
        "phone": _get_user_phone(user),
        "avatar": _get_user_avatar(user),
        "role": item.role or "EMPLOYEE",
        "is_active": bool(item.is_active),
        "created_at": user.date_joined.date().isoformat() if user.date_joined else None,
    }


def _get_company_user(company_id: int, company_user_id: int) -> Optional[CompanyUser]:
    return (
        CompanyUser.objects
        .select_related("user", "company")
        .filter(company_id=company_id, id=company_user_id)
        .first()
    )


def _get_frontend_base_url() -> str:
    """
    جلب رابط الفرونت بشكل آمن.
    """
    return (
        getattr(settings, "FRONTEND_BASE_URL", None)
        or getattr(settings, "FRONTEND_URL", None)
        or getattr(settings, "NEXT_PUBLIC_APP_URL", None)
        or "https://mhamcloud.com"
    ).rstrip("/")


def _get_login_url() -> str:
    return f"{_get_frontend_base_url()}/login"


def _get_company_dashboard_url() -> str:
    return f"{_get_frontend_base_url()}/company"


def _get_system_companies_url() -> str:
    return f"{_get_frontend_base_url()}/system/companies"


def _get_auth_backend_path() -> str:
    backends = getattr(settings, "AUTHENTICATION_BACKENDS", None) or []
    if backends:
        return backends[0]
    return "django.contrib.auth.backends.ModelBackend"


def _clear_impersonation_session(request):
    for key in IMPERSONATION_SESSION_KEYS:
        if key in request.session:
            del request.session[key]


def _ensure_active_session_registry(request, user, *, session_version: int = 1):
    """
    تسجيل الجلسة الحالية داخل ActiveUserSession حتى لا يقوم whoami بعمل flush.
    """
    session_key = request.session.session_key

    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    if not session_key:
        return

    ip_address = request.META.get("REMOTE_ADDR")
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    ActiveUserSession.objects.filter(
        session_key=session_key
    ).update(is_active=False)

    ActiveUserSession.objects.create(
        user=user,
        session_key=session_key,
        ip_address=ip_address,
        user_agent=user_agent,
        session_version=session_version,
        is_active=True,
    )

    request.session["session_version"] = session_version
    request.session.modified = True


# ===============================================================
# Notification Helpers
# ===============================================================

def _dispatch_with_candidates(module, candidate_function_names, **kwargs) -> tuple[bool, Optional[str]]:
    """
    استدعاء مرن للطبقة الرسمية حتى لا ينكسر المسار أثناء مرحلة cleanup.
    """
    notify_func = None

    for func_name in candidate_function_names:
        notify_func = getattr(module, func_name, None)
        if callable(notify_func):
            break

    if not callable(notify_func):
        return False, f"Notification service not found: {', '.join(candidate_function_names)}"

    try:
        notify_func(**kwargs)
        return True, None
    except TypeError:
        pass

    fallback_kwargs = dict(kwargs)

    # extra_context -> context
    if "extra_context" in fallback_kwargs:
        fallback_context = fallback_kwargs.pop("extra_context")
        try:
            notify_func(**fallback_kwargs, context=fallback_context)
            return True, None
        except TypeError:
            pass

    # actor قد لا يكون مدعومًا في بعض الإصدارات
    if "actor" in fallback_kwargs:
        fallback_kwargs_no_actor = dict(fallback_kwargs)
        fallback_kwargs_no_actor.pop("actor", None)

        try:
            notify_func(**fallback_kwargs_no_actor)
            return True, None
        except TypeError:
            pass

        if "extra_context" in kwargs:
            try:
                notify_func(
                    **{
                        k: v for k, v in fallback_kwargs_no_actor.items()
                        if k != "context"
                    },
                    context=kwargs["extra_context"],
                )
                return True, None
            except TypeError:
                pass

    try:
        minimal_kwargs = {}
        for key in ("company", "company_user", "user", "target_user", "new_password"):
            if key in kwargs:
                minimal_kwargs[key] = kwargs[key]

        if minimal_kwargs:
            notify_func(**minimal_kwargs)
            return True, None
    except Exception as exc:
        logger.exception("Notification dispatch failed: %s", exc)
        return False, str(exc)

    return False, "Notification dispatch signature mismatch"


def _build_company_user_common_context(item: CompanyUser) -> dict:
    user = item.user
    company = item.company

    return {
        "company_id": getattr(company, "id", None),
        "company_name": _safe_value(getattr(company, "name", None) if company else None),
        "company_user_id": item.id,
        "target_user_id": getattr(user, "id", None),
        "full_name": _safe_value(_get_full_name(user)),
        "username": _safe_value(getattr(user, "username", None)),
        "email": _safe_value(getattr(user, "email", None)),
        "phone": _safe_value(_get_user_phone(user)),
        "role": _safe_value(item.role or "EMPLOYEE"),
        "login_url": _get_login_url(),
        "company_dashboard_url": _get_company_dashboard_url(),
        "system_companies_url": _get_system_companies_url(),
    }


def _notify_company_user_updated(
    *,
    actor,
    item: CompanyUser,
    old_username: str,
    old_email: str,
    new_username: str,
    new_email: str,
) -> tuple[bool, Optional[str]]:
    context = _build_company_user_common_context(item)
    context.update({
        "old_username": _safe_value(old_username),
        "old_email": _safe_value(old_email),
        "new_username": _safe_value(new_username),
        "new_email": _safe_value(new_email),
    })

    return _dispatch_with_candidates(
        company_notification_services,
        [
            "notify_company_user_updated",
            "notify_system_company_user_updated",
            "send_company_user_updated_notification",
        ],
        actor=actor,
        company=item.company,
        company_user=item,
        user=item.user,
        target_user=item.user,
        extra_context=context,
    )


def _notify_company_user_role_changed(
    *,
    actor,
    item: CompanyUser,
    old_role: str,
    new_role: str,
) -> tuple[bool, Optional[str]]:
    context = _build_company_user_common_context(item)
    context.update({
        "old_role": _safe_value(old_role),
        "new_role": _safe_value(new_role),
    })

    return _dispatch_with_candidates(
        company_notification_services,
        [
            "notify_company_user_role_changed",
            "notify_system_company_user_role_changed",
            "send_company_user_role_changed_notification",
        ],
        actor=actor,
        company=item.company,
        company_user=item,
        user=item.user,
        target_user=item.user,
        extra_context=context,
    )


def _notify_company_user_status_changed(
    *,
    actor,
    item: CompanyUser,
    new_status: bool,
) -> tuple[bool, Optional[str]]:
    context = _build_company_user_common_context(item)
    context.update({
        "is_active": bool(new_status),
        "status_label": "ACTIVE" if new_status else "INACTIVE",
    })

    return _dispatch_with_candidates(
        company_notification_services,
        [
            "notify_company_user_status_changed",
            "notify_system_company_user_status_changed",
            "send_company_user_status_changed_notification",
        ],
        actor=actor,
        company=item.company,
        company_user=item,
        user=item.user,
        target_user=item.user,
        extra_context=context,
    )


def _notify_company_user_password_reset(
    *,
    actor,
    item: CompanyUser,
    new_password: str,
) -> tuple[bool, Optional[str]]:
    context = _build_company_user_common_context(item)
    context.update({
        "new_password": _safe_value(new_password),
    })

    # ------------------------------------------------------------
    # نبدأ بطبقة auth لأنها الأقرب منطقيًا لحدث كلمة المرور
    # ثم fallback إلى company services لو كانت هي المعتمدة حاليًا
    # ------------------------------------------------------------
    sent, error = _dispatch_with_candidates(
        auth_notification_services,
        [
            "notify_password_reset_by_admin",
            "notify_user_password_reset",
            "notify_company_user_password_reset",
            "send_password_reset_notification",
        ],
        actor=actor,
        company=item.company,
        company_user=item,
        user=item.user,
        target_user=item.user,
        new_password=new_password,
        extra_context=context,
    )
    if sent:
        return sent, error

    return _dispatch_with_candidates(
        company_notification_services,
        [
            "notify_company_user_password_reset",
            "notify_system_company_user_password_reset",
            "send_company_user_password_reset_notification",
        ],
        actor=actor,
        company=item.company,
        company_user=item,
        user=item.user,
        target_user=item.user,
        new_password=new_password,
        extra_context=context,
    )


# ===============================================================
# GET /api/system/companies/<company_id>/users/
# ===============================================================

@login_required
@require_GET
def system_company_users(request, company_id):
    denied = _require_superuser(request)
    if denied:
        return denied

    try:
        qs = (
            CompanyUser.objects
            .select_related("user")
            .filter(company_id=company_id)
            .order_by("user__username")
        )

        results = [_serialize_company_user(item) for item in qs]

        return _ok({
            "results": results,
            "count": qs.count(),
            "roles": [
                {"code": "OWNER", "label": "Owner"},
                {"code": "ADMIN", "label": "Admin"},
                {"code": "HR", "label": "HR"},
                {"code": "MANAGER", "label": "Manager"},
                {"code": "EMPLOYEE", "label": "Employee"},
            ]
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


# ===============================================================
# POST /api/system/companies/<company_id>/users/<company_user_id>/update/
# ===============================================================

@login_required
@require_POST
def system_company_user_update(request, company_id, company_user_id):
    denied = _require_superuser(request)
    if denied:
        return denied

    item = _get_company_user(company_id, company_user_id)
    if not item:
        return _not_found("Company user not found")

    data = _json_body(request)

    username = _normalize_username(data.get("username"))
    email = _normalize_email(data.get("email"))

    errors = {}

    if not username:
        errors["username"] = "Username is required"
    elif len(username) < 3:
        errors["username"] = "Username must be at least 3 characters"

    if not email:
        errors["email"] = "Email is required"

    if username and User.objects.filter(username__iexact=username).exclude(id=item.user_id).exists():
        errors["username"] = "Username already exists"

    if email and User.objects.filter(email__iexact=email).exclude(id=item.user_id).exists():
        errors["email"] = "Email already exists"

    if errors:
        return _bad_request("Validation error", errors)

    try:
        user = item.user

        old_username = user.username or ""
        old_email = user.email or ""

        user.username = username
        user.email = email
        user.save(update_fields=["username", "email"])

        email_sent = False
        email_error = None

        if email or old_email:
            email_sent, email_error = _notify_company_user_updated(
                actor=request.user,
                item=item,
                old_username=old_username,
                old_email=old_email,
                new_username=username,
                new_email=email,
            )

        return _ok({
            "message": "Company user updated successfully",
            "email_sent": email_sent,
            "email_error": email_error,
            "user": _serialize_company_user(item),
        })

    except Exception as e:
        logger.exception("Failed to update company user: %s", e)
        return JsonResponse({
            "success": False,
            "error": "Failed to update company user",
            "details": str(e),
        }, status=500)


# ===============================================================
# POST /api/system/companies/<company_id>/users/<company_user_id>/change-role/
# ===============================================================

@login_required
@require_POST
def system_company_user_change_role(request, company_id, company_user_id):
    denied = _require_superuser(request)
    if denied:
        return denied

    item = _get_company_user(company_id, company_user_id)
    if not item:
        return _not_found("Company user not found")

    data = _json_body(request)
    role = (data.get("role") or "").strip().upper()

    if role not in ALLOWED_COMPANY_ROLES:
        return _bad_request("Invalid role")

    try:
        old_role = item.role or "EMPLOYEE"
        item.role = role
        item.save(update_fields=["role"])

        email_sent = False
        email_error = None

        if item.user.email:
            email_sent, email_error = _notify_company_user_role_changed(
                actor=request.user,
                item=item,
                old_role=old_role,
                new_role=role,
            )

        return _ok({
            "message": "Company user role updated successfully",
            "email_sent": email_sent,
            "email_error": email_error,
            "user": _serialize_company_user(item),
        })

    except Exception as e:
        logger.exception("Failed to update company user role: %s", e)
        return JsonResponse({
            "success": False,
            "error": "Failed to update company user role",
            "details": str(e),
        }, status=500)


# ===============================================================
# POST /api/system/companies/<company_id>/users/<company_user_id>/toggle-status/
# ===============================================================

@login_required
@require_POST
def system_company_user_toggle_status(request, company_id, company_user_id):
    denied = _require_superuser(request)
    if denied:
        return denied

    item = _get_company_user(company_id, company_user_id)
    if not item:
        return _not_found("Company user not found")

    try:
        item.is_active = not item.is_active
        item.save(update_fields=["is_active"])

        email_sent = False
        email_error = None

        if item.user.email:
            email_sent, email_error = _notify_company_user_status_changed(
                actor=request.user,
                item=item,
                new_status=item.is_active,
            )

        return _ok({
            "message": "Company user status updated successfully",
            "email_sent": email_sent,
            "email_error": email_error,
            "user": _serialize_company_user(item),
        })

    except Exception as e:
        logger.exception("Failed to update company user status: %s", e)
        return JsonResponse({
            "success": False,
            "error": "Failed to update company user status",
            "details": str(e),
        }, status=500)


# ===============================================================
# POST /api/system/companies/<company_id>/users/<company_user_id>/reset-password/
# ===============================================================

@login_required
@require_POST
def system_company_user_reset_password(request, company_id, company_user_id):
    denied = _require_superuser(request)
    if denied:
        return denied

    item = _get_company_user(company_id, company_user_id)
    if not item:
        return _not_found("Company user not found")

    data = _json_body(request)
    new_password = (data.get("new_password") or "").strip()

    if not new_password:
        new_password = _generate_temp_password()

    if len(new_password) < 6:
        return _bad_request(
            "Validation error",
            {"new_password": "Password must be at least 6 characters"}
        )

    try:
        user = item.user
        user.set_password(new_password)
        user.save(update_fields=["password"])

        email_sent = False
        email_error = None

        if user.email:
            email_sent, email_error = _notify_company_user_password_reset(
                actor=request.user,
                item=item,
                new_password=new_password,
            )

        return _ok({
            "message": "Password updated successfully",
            "temporary_password": new_password,
            "email_sent": email_sent,
            "email_error": email_error,
            "user": _serialize_company_user(item),
        })

    except Exception as e:
        logger.exception("Failed to reset company user password: %s", e)
        return JsonResponse({
            "success": False,
            "error": "Failed to reset company user password",
            "details": str(e),
        }, status=500)


# ===============================================================
# POST /api/system/companies/<company_id>/users/<company_user_id>/enter/
# ===============================================================

@login_required
@require_POST
def system_company_user_enter(request, company_id, company_user_id):
    """
    الدخول إلى الشركة بهوية مستخدم الشركة الحقيقي.
    هذا لا يغير البيانات، بل يبدل الجلسة إلى المستخدم المستهدف
    مع حفظ معلومات المصدر للرجوع لاحقًا.
    """
    denied = _require_internal_system_user(request)
    if denied:
        return denied

    item = _get_company_user(company_id, company_user_id)
    if not item:
        return _not_found("Company user not found")

    if not item.company:
        return _bad_request("Target company not found")

    if not item.is_active:
        return _bad_request("Company user is disabled")

    if not item.user.is_active:
        return _bad_request("Target auth user is disabled")

    source_user = request.user

    try:
        backend_path = _get_auth_backend_path()
        target_user = item.user
        target_user.backend = backend_path

        login(request, target_user, backend=backend_path)

        request.session["impersonation_active"] = True
        request.session["impersonation_source_user_id"] = source_user.id
        request.session["impersonation_source_username"] = source_user.username
        request.session["impersonation_source_email"] = source_user.email or ""
        request.session["impersonation_company_id"] = item.company_id
        request.session["impersonation_company_name"] = item.company.name
        request.session["impersonation_company_user_id"] = item.id
        request.session["impersonation_target_user_id"] = target_user.id
        request.session["impersonation_target_username"] = target_user.username
        request.session["impersonation_target_role"] = item.role or "EMPLOYEE"
        request.session["active_company_id"] = item.company_id

        _ensure_active_session_registry(
            request,
            target_user,
            session_version=1,
        )

        request.session.modified = True
        request.session.save()

        return _ok({
            "message": "Entered company session successfully",
            "redirect_to": "/company",
            "company": {
                "id": item.company.id,
                "name": item.company.name,
            },
            "target_user": {
                "id": target_user.id,
                "username": target_user.username,
                "email": target_user.email or "",
                "role": item.role or "EMPLOYEE",
            },
        })

    except Exception as exc:
        logger.exception("Failed to enter company session: %s", exc)
        return JsonResponse(
            {
                "success": False,
                "error": "Failed to enter company session",
                "details": str(exc),
            },
            status=500,
        )


# ===============================================================
# POST /api/system/companies/exit-session/
# ===============================================================

@login_required
@require_POST
def system_company_exit_session(request):
    """
    الرجوع من جلسة الشركة إلى مستخدم النظام الأصلي.
    """
    if not request.session.get("impersonation_active"):
        return _bad_request("No active company session found")

    source_user_id = request.session.get("impersonation_source_user_id")
    if not source_user_id:
        return _bad_request("Original system user not found in session")

    source_user = User.objects.filter(id=source_user_id, is_active=True).first()
    if not source_user:
        return _not_found("Original system user not found")

    try:
        backend_path = _get_auth_backend_path()
        source_user.backend = backend_path

        login(request, source_user, backend=backend_path)
        _clear_impersonation_session(request)

        try:
            company_user = (
                CompanyUser.objects
                .filter(user=source_user, is_active=True)
                .order_by("id")
                .first()
            )

            if company_user:
                request.session["active_company_id"] = company_user.company_id
        except Exception:
            pass

        _ensure_active_session_registry(
            request,
            source_user,
            session_version=1,
        )

        request.session.modified = True
        request.session.save()

        return _ok({
            "message": "Returned to system session successfully",
            "redirect_to": "/system/companies",
        })

    except Exception as exc:
        logger.exception("Failed to exit company session: %s", exc)
        return JsonResponse(
            {
                "success": False,
                "error": "Failed to exit company session",
                "details": str(exc),
            },
            status=500,
        )