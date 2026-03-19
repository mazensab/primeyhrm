# ============================================================
# Avatar Upload API
# Primey HR Cloud
# Upload Avatar → Google Drive
# ============================================================

import logging
import os
import tempfile
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.utils.html import escape

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from auth_center.models import UserProfile

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# شعار الإيميل المعتمد
# ------------------------------------------------------------
LOGO_URL = "https://drive.google.com/uc?export=view&id=1a0Y1SK3n-Hn9QDZa7Ge24r3--B8zXbTd"

# ============================================================
# Allowed Types
# ============================================================

ALLOWED_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp",
]

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


# ============================================================
# Email Helpers
# ============================================================

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


def _get_profile_url() -> str:
    return f"{_get_frontend_base_url()}/system/profile"


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
        logger.exception("Avatar update email send failed: %s", exc)
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


def _send_avatar_updated_email(user, avatar_url: str) -> tuple[bool, str | None]:
    if not user.email:
        return False, "User has no email"

    full_name = _get_full_name(user)
    profile_url = _get_profile_url()

    text_content, html_content = _build_email_shell(
        title="تم تحديث الصورة الشخصية لحسابك",
        intro="تم تغيير الصورة الشخصية المرتبطة بحسابك بنجاح. يمكنك مراجعة حسابك والتأكد من أن هذا التغيير تم بمعرفتك.",
        rows=[
            ("الاسم", full_name),
            ("اسم المستخدم", user.username or ""),
            ("البريد الإلكتروني", user.email or ""),
            ("رابط الصورة الجديدة", avatar_url or ""),
        ],
        primary_button_label="فتح الملف الشخصي",
        primary_button_url=profile_url,
        note="إذا لم تكن أنت من قام بهذا التغيير، يرجى التواصل مع مسؤول النظام فورًا.",
    )

    return _send_html_email(
        subject="Primey HR Cloud | تم تحديث الصورة الشخصية",
        to_email=user.email,
        text_content=text_content,
        html_content=html_content,
    )


# ============================================================
# Avatar Upload
# ============================================================

@login_required
def avatar_upload(request):

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "POST required"},
            status=400
        )

    uploaded_file = request.FILES.get("avatar")

    if not uploaded_file:
        return JsonResponse(
            {"success": False, "error": "No file uploaded"},
            status=400
        )

    # ========================================================
    # Validate File
    # ========================================================

    if uploaded_file.content_type not in ALLOWED_TYPES:
        return JsonResponse(
            {"success": False, "error": "Invalid file type"},
            status=400
        )

    if uploaded_file.size > MAX_FILE_SIZE:
        return JsonResponse(
            {"success": False, "error": "File too large (max 5MB)"},
            status=400
        )

    temp_path = None

    try:

        # ====================================================
        # Google Credentials
        # ====================================================

        credentials_path = settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE

        if not os.path.exists(credentials_path):
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Credentials not found: {credentials_path}"
                },
                status=500
            )

        creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/drive"]
        )

        drive_service = build(
            "drive",
            "v3",
            credentials=creds,
            cache_discovery=False
        )

        # ====================================================
        # Generate Safe File Name
        # ====================================================

        ext = os.path.splitext(uploaded_file.name)[1]
        file_name = f"user_{request.user.id}_{uuid.uuid4().hex}{ext}"

        # ====================================================
        # Save Temp File
        # ====================================================

        temp_path = os.path.join(
            tempfile.gettempdir(),
            f"avatar_{uuid.uuid4().hex}{ext}"
        )

        with open(temp_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # ====================================================
        # Upload To Drive
        # ====================================================

        media = MediaFileUpload(
            temp_path,
            mimetype=uploaded_file.content_type,
            resumable=True
        )

        uploaded = drive_service.files().create(
            body={
                "name": file_name,
                "parents": [settings.GOOGLE_DRIVE_FOLDER_ID]
            },
            media_body=media,
            fields="id, webViewLink",
            supportsAllDrives=True,
            supportsTeamDrives=True
        ).execute()

        file_id = uploaded.get("id")
        file_url = uploaded.get("webViewLink")

        # ====================================================
        # Make file public
        # ====================================================

        drive_service.permissions().create(
            fileId=file_id,
            body={
                "type": "anyone",
                "role": "reader"
            },
            supportsAllDrives=True
        ).execute()

        # ====================================================
        # Save Avatar URL to UserProfile
        # ====================================================

        profile, created = UserProfile.objects.get_or_create(
            user=request.user
        )

        # ====================================================
        # Delete old avatar from Google Drive
        # ====================================================

        if profile.avatar_url:
            try:
                if "id=" in profile.avatar_url:
                    old_file_id = profile.avatar_url.split("id=")[-1].split("&")[0]
                    drive_service.files().delete(
                        fileId=old_file_id,
                        supportsAllDrives=True
                    ).execute()
            except Exception:
                pass

        avatar_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w512"
        profile.avatar_url = avatar_url
        profile.save(update_fields=["avatar_url"])

        # ====================================================
        # Email Notification
        # ====================================================

        email_sent = False
        email_error = None

        if request.user.email:
            email_sent, email_error = _send_avatar_updated_email(
                user=request.user,
                avatar_url=avatar_url,
            )

        # ====================================================
        # Response
        # ====================================================

        return JsonResponse({
            "success": True,
            "file_id": file_id,
            "url": file_url,
            "avatar": avatar_url,
            "email_sent": email_sent,
            "email_error": email_error,
        })

    except Exception as e:
        logger.exception("Avatar upload failed: %s", e)
        return JsonResponse(
            {
                "success": False,
                "error": str(e)
            },
            status=500
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass