# ===============================================================
# 👥 Company Users — SYSTEM API (Enhanced Actions + Enter As User)
# Primey HR Cloud
# ===============================================================

from __future__ import annotations

import json
import logging
import secrets
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.utils.html import escape
from django.views.decorators.http import require_GET, require_POST

from company_manager.models import CompanyUser
from auth_center.models import UserProfile, ActiveUserSession

User = get_user_model()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# شعار الإيميل المعتمد
# ---------------------------------------------------------------
LOGO_URL = "https://drive.google.com/uc?export=view&id=1a0Y1SK3n-Hn9QDZa7Ge24r3--B8zXbTd"

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
        or "https://primeyride.com"
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


def _send_html_email(
    *,
    subject: str,
    to_email: str,
    text_content: str,
    html_content: str,
) -> tuple[bool, Optional[str]]:
    """
    إرسال إيميل HTML/TEXT بشكل آمن.
    لا نرمي الاستثناء للأعلى حتى لا نكسر العملية الأساسية.
    """
    if not to_email:
        return False, "Recipient email is empty"

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(
        settings,
        "EMAIL_HOST_USER",
        None,
    )

    if not from_email:
        return False, "DEFAULT_FROM_EMAIL / EMAIL_HOST_USER not configured"

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email],
        )
        message.attach_alternative(html_content, "text/html")
        message.send(fail_silently=False)
        return True, None

    except Exception as exc:
        logger.exception("Company user email send failed: %s", exc)
        return False, str(exc)


def _build_email_shell(
    *,
    title: str,
    intro: str,
    rows: list[tuple[str, str]],
    primary_button_label: str,
    primary_button_url: str,
    note: str = "",
) -> tuple[str, str]:
    """
    بناء HTML بسيط وآمن ومتوافق مع الهوية الحالية.
    """
    safe_title = escape(title)
    safe_intro = escape(intro)
    safe_note = escape(note)
    safe_button_label = escape(primary_button_label)
    safe_button_url = escape(primary_button_url)

    rows_html = ""
    text_rows = []

    for label, value in rows:
        safe_label = escape(label)
        safe_value = escape(value or "")
        rows_html += f"""
            <tr>
                <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;font-weight:700;color:#0f172a;width:160px;">{safe_label}</td>
                <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;color:#475569;">{safe_value}</td>
            </tr>
        """
        text_rows.append(f"{label}: {value}")

    html = f"""
    <div dir="rtl" style="margin:0;padding:24px 12px;background:#f6f8fb;font-family:Tahoma,Arial,'Segoe UI',sans-serif;">
      <div style="max-width:680px;margin:0 auto;background:#ffffff;border:1px solid #e8eef7;border-radius:20px;overflow:hidden;">
        <div style="background:#000000;padding:28px 24px;text-align:center;">
          <img
            src="{escape(LOGO_URL)}"
            alt="Primey HR Cloud"
            width="148"
            height="48"
            style="display:block;margin:0 auto 14px;object-fit:contain;"
          />
          <div style="font-size:14px;color:#cbd5e1;line-height:24px;">نظام احترافي لإدارة الشركات والموظفين والفوترة والاشتراكات</div>
        </div>

        <div style="padding:28px 24px 12px;">
          <div style="margin:0 0 16px;font-size:24px;font-weight:700;color:#0f172a;line-height:1.5;">{safe_title}</div>

          <div style="border:1px solid #e5e7eb;border-radius:16px;padding:24px;">
            <p style="margin:0 0 18px;font-size:15px;line-height:28px;color:#334155;">{safe_intro}</p>

            <table width="100%" cellspacing="0" cellpadding="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:0;border-collapse:collapse;overflow:hidden;">
              {rows_html}
            </table>

            <div style="text-align:center;padding:24px 0 16px;">
              <a href="{safe_button_url}" style="background:#0f172a;color:#ffffff;font-size:14px;font-weight:700;text-decoration:none;border-radius:12px;padding:14px 24px;display:inline-block;">
                {safe_button_label}
              </a>
            </div>

            {f'<p style="margin:0 0 10px;font-size:13px;line-height:24px;color:#b45309;">{safe_note}</p>' if safe_note else ''}
            <p style="margin:0;font-size:13px;color:#64748b;">إذا لم يعمل الزر، استخدم الرابط التالي:</p>
            <p style="margin:8px 0 0;">
              <a href="{safe_button_url}" style="color:#2563eb;font-size:13px;text-decoration:none;">{safe_button_url}</a>
            </p>
          </div>
        </div>

        <div style="padding:8px 24px 26px;text-align:center;">
          <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0 20px;" />
          <p style="margin:0 0 8px;color:#475569;font-size:13px;line-height:22px;">تم إرسال هذه الرسالة من خلال نظام Primey HR Cloud.</p>
          <p style="margin:0 0 8px;color:#475569;font-size:13px;line-height:22px;">الدعم الفني: info@primeyride.com</p>
          <p style="margin:8px 0 0;color:#94a3b8;font-size:12px;line-height:20px;">© 2026 Primey HR Cloud. جميع الحقوق محفوظة.</p>
        </div>
      </div>
    </div>
    """

    text = "\n".join(
        [
            title,
            "",
            intro,
            "",
            *text_rows,
            "",
            f"{primary_button_label}: {primary_button_url}",
            "",
            note or "",
        ]
    )

    return text, html


# ===============================================================
# Email Event Helpers
# ===============================================================

def _send_company_user_password_reset_email(item: CompanyUser, new_password: str) -> tuple[bool, Optional[str]]:
    user = item.user
    if not user.email:
        return False, "User has no email"

    login_url = _get_login_url()
    full_name = _get_full_name(user)
    company_name = item.company.name if item.company else ""
    role_label = item.role or "EMPLOYEE"

    text_content, html_content = _build_email_shell(
        title="تم تغيير كلمة المرور بنجاح",
        intro="تمت إعادة تعيين كلمة مرور حسابك بنجاح من خلال إدارة النظام. يمكنك الآن تسجيل الدخول باستخدام كلمة المرور الجديدة الموضحة أدناه.",
        rows=[
            ("الشركة", company_name),
            ("الاسم", full_name),
            ("اسم المستخدم", user.username),
            ("البريد الإلكتروني", user.email or ""),
            ("الدور", role_label),
            ("كلمة المرور الجديدة", new_password),
        ],
        primary_button_label="تسجيل الدخول",
        primary_button_url=login_url,
        note="إذا لم تكن تتوقع هذا التغيير، يرجى التواصل مع مسؤول النظام فورًا.",
    )

    return _send_html_email(
        subject="Primey HR Cloud | تم تحديث كلمة المرور",
        to_email=user.email,
        text_content=text_content,
        html_content=html_content,
    )


def _send_company_user_update_email(
    item: CompanyUser,
    old_username: str,
    old_email: str,
    new_username: str,
    new_email: str,
) -> tuple[bool, Optional[str]]:
    target_email = new_email or old_email
    if not target_email:
        return False, "User has no email"

    user = item.user
    login_url = _get_login_url()
    full_name = _get_full_name(user)
    company_name = item.company.name if item.company else ""
    role_label = item.role or "EMPLOYEE"

    text_content, html_content = _build_email_shell(
        title="تم تحديث بيانات حسابك",
        intro="تم تعديل بعض بيانات حسابك من خلال إدارة النظام. نرجو مراجعة التفاصيل التالية والتأكد من صحتها.",
        rows=[
            ("الشركة", company_name),
            ("الاسم", full_name),
            ("اسم المستخدم السابق", old_username or ""),
            ("اسم المستخدم الجديد", new_username or ""),
            ("البريد السابق", old_email or ""),
            ("البريد الجديد", new_email or ""),
            ("الدور الحالي", role_label),
        ],
        primary_button_label="تسجيل الدخول",
        primary_button_url=login_url,
        note="إذا لم تكن تتوقع هذا التحديث، يرجى التواصل مع مسؤول النظام فورًا.",
    )

    return _send_html_email(
        subject="Primey HR Cloud | تم تحديث بيانات الحساب",
        to_email=target_email,
        text_content=text_content,
        html_content=html_content,
    )


def _send_company_user_role_changed_email(
    item: CompanyUser,
    old_role: str,
    new_role: str,
) -> tuple[bool, Optional[str]]:
    user = item.user
    if not user.email:
        return False, "User has no email"

    login_url = _get_login_url()
    full_name = _get_full_name(user)
    company_name = item.company.name if item.company else ""

    text_content, html_content = _build_email_shell(
        title="تم تحديث صلاحية حسابك",
        intro="تم تغيير الدور الوظيفي أو الصلاحية المرتبطة بحسابك من خلال إدارة النظام.",
        rows=[
            ("الشركة", company_name),
            ("الاسم", full_name),
            ("اسم المستخدم", user.username),
            ("الدور السابق", old_role or ""),
            ("الدور الجديد", new_role or ""),
        ],
        primary_button_label="تسجيل الدخول",
        primary_button_url=login_url,
        note="إذا لم تكن تتوقع هذا التغيير، يرجى التواصل مع مسؤول النظام فورًا.",
    )

    return _send_html_email(
        subject="Primey HR Cloud | تم تحديث صلاحية الحساب",
        to_email=user.email,
        text_content=text_content,
        html_content=html_content,
    )


def _send_company_user_status_changed_email(
    item: CompanyUser,
    new_status: bool,
) -> tuple[bool, Optional[str]]:
    user = item.user
    if not user.email:
        return False, "User has no email"

    login_url = _get_login_url()
    full_name = _get_full_name(user)
    company_name = item.company.name if item.company else ""
    status_label = "ACTIVE" if new_status else "INACTIVE"

    text_content, html_content = _build_email_shell(
        title="تم تحديث حالة حسابك",
        intro="تم تغيير حالة حسابك من خلال إدارة النظام. يمكنك مراجعة الحالة الحالية أدناه.",
        rows=[
            ("الشركة", company_name),
            ("الاسم", full_name),
            ("اسم المستخدم", user.username),
            ("الحالة الحالية", status_label),
            ("الدور الحالي", item.role or "EMPLOYEE"),
        ],
        primary_button_label="تسجيل الدخول",
        primary_button_url=login_url,
        note="إذا تم تعطيل الحساب ولم تكن تتوقع ذلك، يرجى التواصل مع مسؤول النظام.",
    )

    return _send_html_email(
        subject="Primey HR Cloud | تم تحديث حالة الحساب",
        to_email=user.email,
        text_content=text_content,
        html_content=html_content,
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
            email_sent, email_error = _send_company_user_update_email(
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
            email_sent, email_error = _send_company_user_role_changed_email(
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
            email_sent, email_error = _send_company_user_status_changed_email(
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
            email_sent, email_error = _send_company_user_password_reset_email(
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