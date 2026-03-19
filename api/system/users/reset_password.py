# ============================================================
# Reset User Password
# Primey HR Cloud
# Legacy / Compatibility Endpoint
# ============================================================

from __future__ import annotations

import json
import logging
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.utils.html import escape
from django.views.decorators.http import require_POST

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


def _generate_temp_password(length: int = 12) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _get_frontend_base_url() -> str:
    return (
        getattr(settings, "FRONTEND_BASE_URL", None)
        or getattr(settings, "FRONTEND_URL", None)
        or getattr(settings, "NEXT_PUBLIC_APP_URL", None)
        or "https://primeyride.com"
    ).rstrip("/")


def _get_login_url() -> str:
    return f"{_get_frontend_base_url()}/login"


def _send_html_email(
    *,
    subject: str,
    to_email: str,
    text_content: str,
    html_content: str,
) -> tuple[bool, str | None]:
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
        logger.exception("Legacy reset email send failed: %s", exc)
        return False, str(exc)


def _send_password_reset_email(user, new_password: str) -> tuple[bool, str | None]:
    full_name = (user.get_full_name() or "").strip() or user.username
    login_url = _get_login_url()

    rows_html = f"""
        <tr>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;font-weight:700;color:#0f172a;width:160px;">الاسم</td>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;color:#475569;">{escape(full_name)}</td>
        </tr>
        <tr>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;font-weight:700;color:#0f172a;">اسم المستخدم</td>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;color:#475569;">{escape(user.username)}</td>
        </tr>
        <tr>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;font-weight:700;color:#0f172a;">البريد الإلكتروني</td>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;color:#475569;">{escape(user.email or "")}</td>
        </tr>
        <tr>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;font-weight:700;color:#0f172a;">كلمة المرور الجديدة</td>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;color:#475569;">{escape(new_password)}</td>
        </tr>
    """

    html_content = f"""
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
          <div style="font-size:14px;color:#cbd5e1;line-height:24px;">تم تحديث كلمة المرور بنجاح</div>
        </div>

        <div style="padding:28px 24px 12px;">
          <div style="margin:0 0 16px;font-size:24px;font-weight:700;color:#0f172a;line-height:1.5;">تم تغيير كلمة المرور بنجاح</div>

          <div style="border:1px solid #e5e7eb;border-radius:16px;padding:24px;">
            <p style="margin:0 0 18px;font-size:15px;line-height:28px;color:#334155;">
              تمت إعادة تعيين كلمة مرور حسابك بنجاح من خلال إدارة النظام. يمكنك الآن تسجيل الدخول باستخدام كلمة المرور الجديدة الموضحة أدناه.
            </p>

            <table width="100%" cellspacing="0" cellpadding="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:0;border-collapse:collapse;overflow:hidden;">
              {rows_html}
            </table>

            <div style="text-align:center;padding:24px 0 16px;">
              <a href="{escape(login_url)}" style="background:#0f172a;color:#ffffff;font-size:14px;font-weight:700;text-decoration:none;border-radius:12px;padding:14px 24px;display:inline-block;">
                تسجيل الدخول
              </a>
            </div>

            <p style="margin:0 0 10px;font-size:13px;line-height:24px;color:#b45309;">
              إذا لم تكن تتوقع هذا التغيير، يرجى التواصل مع مسؤول النظام فورًا.
            </p>
          </div>
        </div>
      </div>
    </div>
    """

    text_content = "\n".join(
        [
            "تم تغيير كلمة المرور بنجاح",
            "",
            f"الاسم: {full_name}",
            f"اسم المستخدم: {user.username}",
            f"البريد الإلكتروني: {user.email or ''}",
            f"كلمة المرور الجديدة: {new_password}",
            "",
            f"تسجيل الدخول: {login_url}",
        ]
    )

    return _send_html_email(
        subject="Primey HR Cloud | تم تحديث كلمة المرور",
        to_email=user.email,
        text_content=text_content,
        html_content=html_content,
    )


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

        email_sent = False
        email_error = None

        if user.email:
            email_sent, email_error = _send_password_reset_email(
                user=user,
                new_password=password,
            )

        return JsonResponse({
            "success": True,
            "message": "Password updated successfully",
            "email_sent": email_sent,
            "email_error": email_error,
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