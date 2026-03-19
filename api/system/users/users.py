# ============================================================
# 📂 api/system/users.py
# Primey HR Cloud
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
# ============================================================

from __future__ import annotations

import json
import logging
import secrets
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.mail import EmailMultiAlternatives
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.http import require_GET, require_POST

from company_manager.models import CompanyUser
from auth_center.models import UserProfile
from whatsapp_center.models import ScopeType, TriggerSource
from whatsapp_center.services import send_event_whatsapp_message

User = get_user_model()
logger = logging.getLogger(__name__)
LOGO_URL = "https://drive.google.com/uc?export=view&id=1a0Y1SK3n-Hn9QDZa7Ge24r3--B8zXbTd"

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
    user.groups.remove(*Group.objects.filter(name__in=[ROLE_SYSTEM_ADMIN, ROLE_SUPPORT]))


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


def _get_system_users_url() -> str:
    return f"{_get_frontend_base_url()}/system/users"


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
        logger.exception("Email send failed: %s", exc)
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
    بناء HTML بسيط وآمن كمرحلة تشغيلية مستقرة.
    لاحقًا يمكن استبداله بـ React Email render بدون تغيير الـ API.
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


def _send_system_whatsapp_notification(
    *,
    user,
    event_code: str,
    context: dict,
    recipient_role: str = "",
    language_code: str = "ar",
) -> tuple[bool, Optional[str]]:
    """
    إرسال واتساب داخلي بشكل Fail-Safe.
    لا يكسر العملية الأساسية عند عدم وجود رقم أو إعداد نشط.
    """
    recipient_phone = _get_user_whatsapp_phone(user)

    if not recipient_phone:
        return False, "User has no WhatsApp phone number"

    try:
        log = send_event_whatsapp_message(
            scope_type=ScopeType.SYSTEM,
            event_code=event_code,
            recipient_phone=recipient_phone,
            recipient_name=_get_full_name(user),
            recipient_role=recipient_role or (_get_internal_role(user) or ROLE_SUPPORT),
            trigger_source=TriggerSource.SYSTEM,
            language_code=language_code or "ar",
            context=context,
            related_model="User",
            related_object_id=str(user.id),
        )

        delivery_status = getattr(log, "delivery_status", "")
        failure_reason = getattr(log, "failure_reason", "")

        if str(delivery_status).upper() == "FAILED":
            return False, failure_reason or "WhatsApp delivery failed"

        return True, None

    except Exception as exc:
        logger.exception("WhatsApp send failed for event %s: %s", event_code, exc)
        return False, str(exc)


# ============================================================
# Email Event Helpers
# ============================================================

def _send_system_user_created_email(user, password: str, role: str) -> tuple[bool, Optional[str]]:
    """
    إيميل إنشاء مستخدم نظام داخلي.
    """
    if not user.email:
        return False, "User has no email"

    full_name = _get_full_name(user)
    login_url = _get_login_url()

    text_content, html_content = _build_email_shell(
        title="تم إنشاء حسابك في Primey HR Cloud",
        intro="تم إنشاء حسابك بنجاح كمستخدم داخلي في النظام. يمكنك تسجيل الدخول باستخدام البيانات التالية، ونوصي بتغيير كلمة المرور فور أول دخول.",
        rows=[
            ("الاسم", full_name),
            ("اسم المستخدم", user.username),
            ("البريد الإلكتروني", user.email or ""),
            ("الدور", role),
            ("كلمة المرور المؤقتة", password),
        ],
        primary_button_label="تسجيل الدخول",
        primary_button_url=login_url,
        note="تنبيه أمني: لا تشارك كلمة المرور مع أي شخص غير مخوّل.",
    )

    return _send_html_email(
        subject="Primey HR Cloud | تم إنشاء حسابك",
        to_email=user.email,
        text_content=text_content,
        html_content=html_content,
    )


def _send_system_user_password_reset_email(user, new_password: str) -> tuple[bool, Optional[str]]:
    """
    إيميل إعادة تعيين كلمة المرور.
    """
    if not user.email:
        return False, "User has no email"

    full_name = _get_full_name(user)
    login_url = _get_login_url()

    text_content, html_content = _build_email_shell(
        title="تم تغيير كلمة المرور بنجاح",
        intro="تمت إعادة تعيين كلمة مرور حسابك بنجاح من خلال إدارة النظام. يمكنك الآن تسجيل الدخول باستخدام كلمة المرور الجديدة الموضحة أدناه.",
        rows=[
            ("الاسم", full_name),
            ("اسم المستخدم", user.username),
            ("البريد الإلكتروني", user.email or ""),
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


def _send_system_user_role_changed_email(
    user,
    old_role: str,
    new_role: str,
) -> tuple[bool, Optional[str]]:
    """
    إشعار تغيير الدور.
    """
    if not user.email:
        return False, "User has no email"

    full_name = _get_full_name(user)
    login_url = _get_login_url()

    text_content, html_content = _build_email_shell(
        title="تم تحديث صلاحية حسابك",
        intro="تم تغيير الدور أو الصلاحية المرتبطة بحسابك من خلال إدارة النظام. نرجو مراجعة التفاصيل التالية.",
        rows=[
            ("الاسم", full_name),
            ("اسم المستخدم", user.username),
            ("البريد الإلكتروني", user.email or ""),
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


def _send_system_user_status_changed_email(
    user,
    new_status: bool,
) -> tuple[bool, Optional[str]]:
    """
    إشعار تفعيل/تعطيل الحساب.
    """
    if not user.email:
        return False, "User has no email"

    full_name = _get_full_name(user)
    login_url = _get_login_url()
    current_role = _get_internal_role(user) or ROLE_SUPPORT
    status_label = "ACTIVE" if new_status else "INACTIVE"

    text_content, html_content = _build_email_shell(
        title="تم تحديث حالة حسابك",
        intro="تم تغيير حالة حسابك من خلال إدارة النظام. نرجو مراجعة الحالة الحالية أدناه.",
        rows=[
            ("الاسم", full_name),
            ("اسم المستخدم", user.username),
            ("البريد الإلكتروني", user.email or ""),
            ("الدور الحالي", current_role),
            ("الحالة الحالية", status_label),
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


def _send_system_user_deleted_email(
    *,
    username: str,
    email: str,
    full_name: str,
) -> tuple[bool, Optional[str]]:
    """
    إشعار حذف الحساب الداخلي.
    """
    if not email:
        return False, "User has no email"

    login_url = _get_login_url()

    text_content, html_content = _build_email_shell(
        title="تم حذف حسابك من النظام",
        intro="تم حذف حسابك الداخلي من نظام Primey HR Cloud من خلال إدارة النظام.",
        rows=[
            ("الاسم", full_name or username),
            ("اسم المستخدم", username),
            ("البريد الإلكتروني", email or ""),
        ],
        primary_button_label="صفحة تسجيل الدخول",
        primary_button_url=login_url,
        note="إذا لم تكن تتوقع هذا الإجراء، يرجى التواصل مع مسؤول النظام فورًا.",
    )

    return _send_html_email(
        subject="Primey HR Cloud | تم حذف الحساب",
        to_email=email,
        text_content=text_content,
        html_content=html_content,
    )


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

        email_sent = False
        email_error = None
        whatsapp_sent = False
        whatsapp_error = None

        if created_user and created_user.email:
            email_sent, email_error = _send_system_user_created_email(
                user=created_user,
                password=password,
                role=role,
            )

        if created_user:
            whatsapp_sent, whatsapp_error = _send_system_whatsapp_notification(
                user=created_user,
                event_code="system_user_created",
                recipient_role=role,
                language_code="ar",
                context={
                    "full_name": _get_full_name(created_user),
                    "username": created_user.username or "",
                    "email": created_user.email or "",
                    "temporary_password": password,
                    "login_url": _get_login_url(),
                },
            )

        return _ok({
            "message": "System user created successfully",
            "user": _serialize_user(created_user),
            "temporary_password": password,
            "email_sent": email_sent,
            "email_error": email_error,
            "whatsapp_sent": whatsapp_sent,
            "whatsapp_error": whatsapp_error,
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

    email_sent = False
    email_error = None

    if user.email:
        email_sent, email_error = _send_system_user_status_changed_email(
            user=user,
            new_status=user.is_active,
        )

    return _ok({
        "message": "User status updated successfully",
        "email_sent": email_sent,
        "email_error": email_error,
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

        email_sent = False
        email_error = None

        if user.email:
            email_sent, email_error = _send_system_user_role_changed_email(
                user=user,
                old_role=old_role,
                new_role=role,
            )

        return _ok({
            "message": "User role updated successfully",
            "email_sent": email_sent,
            "email_error": email_error,
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

        email_sent = False
        email_error = None
        whatsapp_sent = False
        whatsapp_error = None

        if user.email:
            email_sent, email_error = _send_system_user_password_reset_email(
                user=user,
                new_password=new_password,
            )

        whatsapp_sent, whatsapp_error = _send_system_whatsapp_notification(
            user=user,
            event_code="system_user_password_changed",
            recipient_role=_get_internal_role(user) or ROLE_SUPPORT,
            language_code="ar",
            context={
                "full_name": _get_full_name(user),
                "username": user.username or "",
                "email": user.email or "",
                "changed_at": timezone.now().strftime("%Y-%m-%d %H:%M"),
                "login_url": _get_login_url(),
            },
        )

        return _ok({
            "message": "Password reset successfully",
            "user_id": user.id,
            "temporary_password": new_password,
            "email_sent": email_sent,
            "email_error": email_error,
            "whatsapp_sent": whatsapp_sent,
            "whatsapp_error": whatsapp_error,
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
    email = user.email or ""
    full_name = _get_full_name(user)

    email_sent = False
    email_error = None

    if email:
        email_sent, email_error = _send_system_user_deleted_email(
            username=username,
            email=email,
            full_name=full_name,
        )

    user.delete()

    return _ok({
        "message": "System user deleted successfully",
        "username": username,
        "email_sent": email_sent,
        "email_error": email_error,
    })