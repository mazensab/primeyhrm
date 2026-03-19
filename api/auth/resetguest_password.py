# ============================================================
# Reset Guest Password API
# Primey HR Cloud
# Reset Password by Username or Email (Guest Flow)
# ============================================================

from __future__ import annotations

import json
import logging
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.utils.html import escape
from django.views.decorators.http import require_POST

from auth_center.models import UserProfile

try:
    from company_manager.models import CompanyUser
except Exception:
    CompanyUser = None

try:
    from company_manager.models import Company
except Exception:
    Company = None

User = get_user_model()
logger = logging.getLogger(__name__)

LOGO_URL = "https://drive.google.com/uc?export=view&id=1a0Y1SK3n-Hn9QDZa7Ge24r3--B8zXbTd"


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


def _normalize_identifier(value: str) -> str:
    return (value or "").strip().lower()


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


def _get_login_url() -> str:
    return f"{_get_frontend_base_url()}/login"


def _get_profile_url(user=None, request=None) -> str:
    base_url = _get_frontend_base_url()

    active_company_id = None
    if request is not None:
        active_company_id = request.session.get("active_company_id")

    is_company_user = False

    if active_company_id:
        is_company_user = True

    if not is_company_user and user is not None:
        try:
            if CompanyUser is not None:
                is_company_user = CompanyUser.objects.filter(
                    user=user,
                    is_active=True,
                ).exists()
        except Exception:
            is_company_user = False

    if is_company_user:
        return f"{base_url}/company/profile"

    return f"{base_url}/system/profile"


def _send_html_email(
    *,
    subject: str,
    to_email: str,
    text_content: str,
    html_content: str,
) -> tuple[bool, Optional[str]]:
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
        logger.exception("Reset guest password email send failed: %s", exc)
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


def _send_password_reset_notification(user) -> tuple[bool, Optional[str]]:
    if not user.email:
        return False, "User has no email"

    full_name = _get_full_name(user)
    login_url = _get_login_url()

    text_content, html_content = _build_email_shell(
        title="تمت إعادة تعيين كلمة المرور",
        intro="تم تغيير كلمة مرور حسابك بنجاح من خلال صفحة إعادة تعيين كلمة المرور.",
        rows=[
            ("الاسم", full_name),
            ("اسم المستخدم", user.username or ""),
            ("البريد الإلكتروني", user.email or ""),
        ],
        primary_button_label="تسجيل الدخول",
        primary_button_url=login_url,
        note="إذا لم تكن أنت من قام بهذا التغيير، يرجى التواصل مع مسؤول النظام فورًا.",
    )

    return _send_html_email(
        subject="Primey HR Cloud | Password Reset Completed",
        to_email=user.email,
        text_content=text_content,
        html_content=html_content,
    )


# ============================================================
# WhatsApp Helpers
# ============================================================

def _get_user_whatsapp_number(user) -> str:
    profile = (
        UserProfile.objects
        .filter(user=user)
        .only("whatsapp_number", "phone_number")
        .first()
    )

    if not profile:
        return ""

    return (
        getattr(profile, "whatsapp_number", None)
        or getattr(profile, "phone_number", None)
        or ""
    ).strip()


def _get_active_company_from_request(request, user=None):
    active_company_id = None

    if request is not None:
        active_company_id = request.session.get("active_company_id")

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


def _resolve_whatsapp_language(user) -> str:
    return "ar"


def _send_password_reset_whatsapp(user, request=None) -> tuple[bool, Optional[str]]:
    phone = _get_user_whatsapp_number(user)

    if not phone:
        return False, "User has no WhatsApp number"

    try:
        from whatsapp_center.models import ScopeType, TriggerSource
        from whatsapp_center.services import send_event_whatsapp_message
    except Exception as exc:
        logger.exception("Failed importing WhatsApp event service: %s", exc)
        return False, str(exc)

    company = _get_active_company_from_request(request, user=user)
    scope_type = ScopeType.COMPANY if company else ScopeType.SYSTEM
    language_code = _resolve_whatsapp_language(user)

    try:
        result_log = send_event_whatsapp_message(
            scope_type=scope_type,
            company=company,
            event_code="password_changed",
            recipient_phone=phone,
            recipient_name=_get_full_name(user),
            recipient_role="USER",
            trigger_source=TriggerSource.COMPANY if company else TriggerSource.SYSTEM,
            language_code=language_code,
            context={
                "recipient_name": _get_full_name(user),
                "username": user.username or "",
                "email": user.email or "",
                "login_url": _get_login_url(),
                "profile_url": _get_profile_url(user=user, request=request),
                "company_name": getattr(company, "name", "") if company else "",
            },
            related_model="auth.User",
            related_object_id=str(user.id),
        )

        delivery_status = getattr(result_log, "delivery_status", "") or ""
        failure_reason = getattr(result_log, "failure_reason", "") or ""

        if delivery_status.upper() == "SENT":
            return True, None

        return False, failure_reason or f"WhatsApp delivery status: {delivery_status}"

    except Exception as exc:
        logger.exception("Password reset WhatsApp send failed: %s", exc)
        return False, str(exc)


# ============================================================
# POST /api/auth/resetguest-password/
# ============================================================

@require_POST
def resetguest_password(request):
    data = _json_body(request)

    identifier = _normalize_identifier(data.get("identifier"))
    new_password = (data.get("new_password") or "").strip()
    confirm_password = (data.get("confirm_password") or "").strip()

    errors = {}

    if not identifier:
        errors["identifier"] = "Username or email is required"

    if not new_password:
        errors["new_password"] = "New password is required"
    elif len(new_password) < 8:
        errors["new_password"] = "New password must be at least 8 characters"

    if not confirm_password:
        errors["confirm_password"] = "Confirm password is required"
    elif new_password != confirm_password:
        errors["confirm_password"] = "Passwords do not match"

    if errors:
        return _bad_request("Validation error", errors)

    try:
        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(username__iexact=identifier).first()

        if not user:
            return JsonResponse(
                {
                    "success": False,
                    "message": "User not found",
                },
                status=404,
            )

        if not user.is_active:
            return JsonResponse(
                {
                    "success": False,
                    "message": "User account is inactive",
                },
                status=400,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        email_sent = False
        email_error = None
        whatsapp_sent = False
        whatsapp_error = None

        if user.email:
            email_sent, email_error = _send_password_reset_notification(user)

        whatsapp_sent, whatsapp_error = _send_password_reset_whatsapp(
            user,
            request=request,
        )

        if whatsapp_sent:
            logger.info(
                "Password reset WhatsApp sent successfully to user=%s",
                user.username,
            )
        else:
            logger.warning(
                "Password reset WhatsApp failed for user=%s error=%s",
                user.username,
                whatsapp_error,
            )

        return _ok({
            "message": "Password reset successfully",
            "email_sent": email_sent,
            "email_error": email_error,
            "whatsapp_sent": whatsapp_sent,
            "whatsapp_error": whatsapp_error,
        })

    except Exception as exc:
        logger.exception("Failed to reset guest password: %s", exc)
        return JsonResponse(
            {
                "success": False,
                "message": "Failed to reset password",
                "details": str(exc),
            },
            status=500,
        )