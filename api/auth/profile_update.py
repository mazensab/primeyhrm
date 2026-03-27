# ============================================================
# 📂 api/auth/profile_update.py
# Primey HR Cloud
# Update Current User Profile
# يدعم:
# - مستخدمي النظام
# - مستخدمي الشركات لاحقًا
# ============================================================

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from auth_center.models import UserProfile
from whatsapp_center.utils import normalize_phone_number

logger = logging.getLogger(__name__)
User = get_user_model()

try:
    from employee_center.models import Employee
except Exception:
    Employee = None

try:
    from company_manager.models import CompanyUser
except Exception:
    CompanyUser = None


# ============================================================
# Branding
# ============================================================

LOGO_URL = getattr(
    settings,
    "PRIMEY_EMAIL_LOGO_URL",
    getattr(
        settings,
        "EMAIL_LOGO_URL",
        "https://drive.google.com/uc?export=view&id=1a0Y1SK3n-Hn9QDZa7Ge24r3--B8zXbTd",
    ),
)

DEFAULT_FROM_EMAIL = getattr(
    settings,
    "DEFAULT_FROM_EMAIL",
    getattr(settings, "EMAIL_HOST_USER", "no-reply@primeyhr.com"),
)


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


def _get_full_name(user) -> str:
    full_name = (user.get_full_name() or "").strip()
    return full_name or user.username or "User"


def _get_frontend_base_url() -> str:
    return (
        getattr(settings, "FRONTEND_BASE_URL", None)
        or getattr(settings, "FRONTEND_URL", None)
        or getattr(settings, "NEXT_PUBLIC_APP_URL", None)
        or "https://primeyride.com"
    ).rstrip("/")


def _get_profile_url(user=None, request=None) -> str:
    base_url = _get_frontend_base_url()

    active_company_id = None
    if request is not None:
        active_company_id = request.session.get("active_company_id")

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


def _build_email_shell(
    *,
    title: str,
    intro: str,
    rows: list[tuple[str, str]],
    primary_button_label: str,
    primary_button_url: str,
    note: str = "",
) -> tuple[str, str]:
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


def _send_html_email(
    *,
    subject: str,
    to_email: str,
    text_content: str,
    html_content: str,
) -> tuple[bool, str | None]:
    if not to_email:
        return False, "Recipient email is empty"

    if not DEFAULT_FROM_EMAIL:
        return False, "DEFAULT_FROM_EMAIL not configured"

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        message.attach_alternative(html_content, "text/html")
        message.send(fail_silently=False)
        return True, None

    except Exception as exc:
        logger.exception("Profile update email send failed: %s", exc)
        return False, str(exc)


def _send_profile_updated_email(
    user,
    old_email: str,
    new_email: str,
    full_name: str,
    phone: str,
    request=None,
):
    target_email = new_email or old_email

    if not target_email:
        return False, "User has no email"

    profile_url = _get_profile_url(user=user, request=request)

    text_content, html_content = _build_email_shell(
        title="تم تحديث بيانات الملف الشخصي",
        intro="تم تحديث بيانات ملفك الشخصي بنجاح. يمكنك مراجعة حسابك والتأكد من أن هذا التغيير تم بمعرفتك.",
        rows=[
            ("الاسم الكامل", full_name or ""),
            ("اسم المستخدم", user.username or ""),
            ("البريد السابق", old_email or ""),
            ("البريد الحالي", new_email or ""),
            ("رقم الجوال", phone or ""),
        ],
        primary_button_label="فتح الملف الشخصي",
        primary_button_url=profile_url,
        note="إذا لم تكن أنت من قام بهذا التغيير، يرجى تغيير كلمة المرور والتواصل مع مسؤول النظام فورًا.",
    )

    return _send_html_email(
        subject="Primey HR Cloud | تم تحديث بيانات الملف الشخصي",
        to_email=target_email,
        text_content=text_content,
        html_content=html_content,
    )


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

    # --------------------------------------------------------
    # 📱 Normalize phone for WhatsApp-compatible storage
    # --------------------------------------------------------
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
            lambda: _send_profile_updated_email(
                user=user,
                old_email=old_email,
                new_email=email,
                full_name=full_name,
                phone=stored_whatsapp_phone or stored_phone,
                request=request,
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