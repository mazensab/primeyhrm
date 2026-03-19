# ============================================================
# 📂 api/company/settings.py
# 🏢 Company Settings API
# Primey HR Cloud
# Version: V2.1 Google Drive Logo via CompanyProfile.settings
# ============================================================

from __future__ import annotations

import json
import logging
import os
import tempfile
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.http import JsonResponse
from django.utils.html import escape
from django.views.decorators.http import require_GET, require_POST

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from company_manager.models import CompanyUser, CompanyProfile

logger = logging.getLogger(__name__)

# ============================================================
# Optional Audit Import
# ============================================================
try:
    from settings_center.services import add_audit_log as settings_add_audit_log
except Exception:
    settings_add_audit_log = None


# ============================================================
# Constants
# ============================================================
ALLOWED_IMAGE_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp",
]

MAX_LOGO_FILE_SIZE = 5 * 1024 * 1024  # 5MB

PRIMEY_EMAIL_LOGO_URL = getattr(
    settings,
    "PRIMEY_EMAIL_LOGO_URL",
    "https://drive.google.com/uc?export=view&id=1a0Y1SK3n-Hn9QDZa7Ge24r3--B8zXbTd",
)

DEFAULT_FROM_EMAIL = getattr(
    settings,
    "DEFAULT_FROM_EMAIL",
    getattr(settings, "EMAIL_HOST_USER", "no-reply@primeyhr.com"),
)


# ============================================================
# Helpers
# ============================================================

def _request_payload(request) -> dict:
    """
    يدعم:
    - application/json
    - multipart/form-data
    - x-www-form-urlencoded
    """
    content_type = (request.content_type or "").lower()

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        return request.POST.dict()

    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


def _normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _safe_value(value):
    return value if value not in (None, "") else "-"


def _get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_active_company(request):
    """
    إرجاع الشركة النشطة للمستخدم الحالي ضمن company context
    """
    company_user = (
        CompanyUser.objects
        .select_related("company")
        .filter(user=request.user, is_active=True)
        .first()
    )
    return company_user.company if company_user else None


def _get_or_create_company_profile(company):
    profile, _created = CompanyProfile.objects.get_or_create(company=company)
    return profile


def _safe_add_audit_log(*, company, user, section, field, old, new, ip):
    """
    تسجيل Audit Log بشكل آمن دون كسر النظام
    """
    if not settings_add_audit_log:
        logger.warning(
            "settings_center.services.add_audit_log is not available. "
            "Skipping audit log for section=%s field=%s",
            section,
            field,
        )
        return

    try:
        settings_add_audit_log(
            company=company,
            user=user,
            section=section,
            field=field,
            old=old,
            new=new,
            ip=ip,
        )
    except Exception:
        logger.warning(
            "Audit log failed for section=%s field=%s",
            section,
            field,
            exc_info=True,
        )


def _safe_file_url(file_field):
    """
    دعم الحالات التالية:
    - FileField / ImageField عادي
    - قيمة نصية مباشرة
    - None
    """
    try:
        if not file_field:
            return None

        if isinstance(file_field, str):
            return file_field.strip() or None

        file_name = getattr(file_field, "name", None)
        if not file_name:
            return None

        if isinstance(file_name, str) and file_name.startswith(("http://", "https://")):
            return file_name

        return file_field.url
    except Exception:
        return None


def _extract_drive_file_id(url: str | None) -> str | None:
    if not url:
        return None

    try:
        if "id=" in url:
            return url.split("id=")[-1].split("&")[0].strip()

        if "/d/" in url:
            return url.split("/d/")[-1].split("/")[0].strip()

        return None
    except Exception:
        return None


def _get_drive_service():
    credentials_path = getattr(settings, "GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE", None)
    folder_id = getattr(settings, "GOOGLE_DRIVE_FOLDER_ID", None)

    if not credentials_path:
        raise ValueError("GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE is not configured")

    if not folder_id:
        raise ValueError("GOOGLE_DRIVE_FOLDER_ID is not configured")

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(f"Google credentials not found: {credentials_path}")

    creds = Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/drive"],
    )

    drive_service = build(
        "drive",
        "v3",
        credentials=creds,
        cache_discovery=False,
    )

    return drive_service, folder_id


def _delete_drive_file_if_exists(file_url: str | None):
    file_id = _extract_drive_file_id(file_url)
    if not file_id:
        return

    try:
        drive_service, _folder_id = _get_drive_service()
        drive_service.files().delete(
            fileId=file_id,
            supportsAllDrives=True,
        ).execute()
    except Exception:
        logger.warning("Failed to delete old logo from Google Drive", exc_info=True)


def _upload_company_logo_to_drive(*, company, uploaded_file):
    """
    رفع شعار الشركة إلى Google Drive
    وإرجاع:
    - thumbnail_url
    - file_id
    - web_view_link
    """
    if uploaded_file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("نوع ملف الشعار غير مدعوم. المسموح: JPG / PNG / WEBP")

    if uploaded_file.size > MAX_LOGO_FILE_SIZE:
        raise ValueError("حجم الشعار كبير جدًا. الحد الأقصى 5MB")

    drive_service, folder_id = _get_drive_service()

    temp_path = None
    try:
        ext = os.path.splitext(uploaded_file.name or "")[1] or ".png"
        file_name = f"company_logo_{company.id}_{uuid.uuid4().hex}{ext}"

        temp_path = os.path.join(
            tempfile.gettempdir(),
            f"company_logo_{uuid.uuid4().hex}{ext}",
        )

        with open(temp_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        media = MediaFileUpload(
            temp_path,
            mimetype=uploaded_file.content_type,
            resumable=True,
        )

        uploaded = drive_service.files().create(
            body={
                "name": file_name,
                "parents": [folder_id],
            },
            media_body=media,
            fields="id, webViewLink",
            supportsAllDrives=True,
            supportsTeamDrives=True,
        ).execute()

        file_id = uploaded.get("id")
        web_view_link = uploaded.get("webViewLink")

        drive_service.permissions().create(
            fileId=file_id,
            body={
                "type": "anyone",
                "role": "reader",
            },
            supportsAllDrives=True,
        ).execute()

        thumbnail_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w512"

        return {
            "file_id": file_id,
            "web_view_link": web_view_link,
            "thumbnail_url": thumbnail_url,
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass


def _get_company_logo_url(company) -> str | None:
    """
    مصدر الشعار النهائي:
    1) CompanyProfile.settings.logo_url
    2) Company.logo المحلي (إن وجد)
    3) CompanyProfile.logo المحلي (إن وجد)
    """
    try:
        profile = getattr(company, "profile", None)
    except Exception:
        profile = None

    if profile:
        profile_settings = getattr(profile, "settings", None) or {}
        logo_url = profile_settings.get("logo_url")
        if logo_url:
            return logo_url

    company_logo = _safe_file_url(getattr(company, "logo", None))
    if company_logo:
        return company_logo

    if profile:
        profile_logo = _safe_file_url(getattr(profile, "logo", None))
        if profile_logo:
            return profile_logo

    return None


def _save_company_logo_url(*, company, logo_url: str, file_id: str | None = None, web_view_link: str | None = None):
    """
    حفظ رابط شعار Google Drive داخل CompanyProfile.settings
    بدون الاعتماد على ImageField المحلي.
    """
    profile = _get_or_create_company_profile(company)
    profile_settings = dict(getattr(profile, "settings", None) or {})

    profile_settings["logo_url"] = logo_url
    if file_id:
        profile_settings["logo_file_id"] = file_id
    if web_view_link:
        profile_settings["logo_web_view_link"] = web_view_link

    profile.settings = profile_settings
    profile.save(update_fields=["settings", "updated_at"])


def _build_company_updated_email_html(
    *,
    owner_name: str,
    company_name: str,
    company_email: str,
    company_phone: str,
    commercial_number: str,
    vat_number: str,
    building_number: str,
    street: str,
    district: str,
    city: str,
    postal_code: str,
    short_address: str,
    changed_fields: list[dict],
    logo_url: str | None,
) -> str:
    logo_header_url = escape(PRIMEY_EMAIL_LOGO_URL)
    owner_name = escape(owner_name or "User")
    company_name = escape(_safe_value(company_name))
    company_email = escape(_safe_value(company_email))
    company_phone = escape(_safe_value(company_phone))
    commercial_number = escape(_safe_value(commercial_number))
    vat_number = escape(_safe_value(vat_number))
    building_number = escape(_safe_value(building_number))
    street = escape(_safe_value(street))
    district = escape(_safe_value(district))
    city = escape(_safe_value(city))
    postal_code = escape(_safe_value(postal_code))
    short_address = escape(_safe_value(short_address))
    safe_logo_url = escape(logo_url or "")

    changes_rows = ""
    for item in changed_fields:
        field_name = escape(item.get("field", ""))
        old_value = escape(_safe_value(item.get("old", "")))
        new_value = escape(_safe_value(item.get("new", "")))
        changes_rows += f"""
        <tr>
          <td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">{field_name}</td>
          <td style="padding:10px 12px;border:1px solid #e5e7eb;">{old_value}</td>
          <td style="padding:10px 12px;border:1px solid #e5e7eb;">{new_value}</td>
        </tr>
        """

    logo_block = ""
    if safe_logo_url:
        logo_block = f"""
        <div style="margin-top:20px;text-align:center;">
          <div style="font-size:14px;color:#374151;margin-bottom:10px;">الشعار الحالي</div>
          <img src="{safe_logo_url}" alt="Company Logo"
               style="max-height:90px;max-width:220px;width:auto;border:1px solid #e5e7eb;border-radius:12px;padding:10px;background:#ffffff;" />
        </div>
        """

    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>تم تحديث بيانات الشركة</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f7fb;font-family:Tahoma,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f7fb;margin:0;padding:24px 0;">
    <tr>
      <td align="center">
        <table width="680" cellpadding="0" cellspacing="0"
               style="max-width:680px;width:100%;background:#ffffff;border-radius:18px;overflow:hidden;border:1px solid #e5e7eb;">

          <tr>
            <td align="center" style="background:#000000;padding:28px 24px;">
              <img src="{logo_header_url}" alt="Primey"
                   style="max-height:56px;width:auto;display:block;margin:0 auto 12px auto;" />
              <div style="color:#ffffff;font-size:22px;font-weight:700;line-height:1.6;">
                Primey HR Cloud
              </div>
              <div style="color:#d1d5db;font-size:14px;line-height:1.8;">
                تم تحديث بيانات الشركة بنجاح
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:32px 28px 20px 28px;">
              <div style="font-size:16px;color:#111827;line-height:2;">
                أهلاً <strong>{owner_name}</strong>،
              </div>

              <div style="margin-top:10px;font-size:15px;color:#374151;line-height:2;">
                تم إجراء تعديل على بيانات الشركة داخل النظام، وهذه الرسالة للتأكيد فقط.
              </div>

              <div style="margin-top:22px;font-size:15px;font-weight:700;color:#111827;">
                بيانات الشركة الحالية
              </div>

              <table width="100%" cellpadding="0" cellspacing="0"
                     style="margin-top:12px;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;">
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">اسم الشركة</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{company_name}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">البريد الإلكتروني</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{company_email}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">الهاتف</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{company_phone}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">السجل التجاري</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{commercial_number}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">الرقم الضريبي</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{vat_number}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">رقم المبنى</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{building_number}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">الشارع</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{street}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">الحي</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{district}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">المدينة</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{city}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">الرمز البريدي</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{postal_code}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">العنوان المختصر</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{short_address}</td></tr>
              </table>

              <div style="margin-top:24px;font-size:15px;font-weight:700;color:#111827;">
                الحقول التي تغيرت
              </div>

              <table width="100%" cellpadding="0" cellspacing="0"
                     style="margin-top:12px;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;">
                <tr>
                  <td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f1f5f9;">الحقل</td>
                  <td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f1f5f9;">القيمة السابقة</td>
                  <td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f1f5f9;">القيمة الجديدة</td>
                </tr>
                {changes_rows or '<tr><td colspan="3" style="padding:12px;border:1px solid #e5e7eb;">لا توجد تغييرات معروضة</td></tr>'}
              </table>

              {logo_block}

              <div style="margin-top:22px;font-size:13px;color:#b45309;line-height:2;">
                إذا لم تكن أنت من قام بهذا التغيير، يرجى مراجعة مسؤول النظام فورًا.
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:20px 28px 30px 28px;">
              <div style="border-top:1px solid #e5e7eb;padding-top:18px;font-size:12px;color:#9ca3af;line-height:1.9;text-align:center;">
                هذه رسالة آلية من Primey HR Cloud — يرجى عدم الرد عليها مباشرة.
              </div>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
""".strip()


def _send_company_updated_email(*, company, changed_fields: list[dict]) -> None:
    """
    إرسال إيميل عند تحديث بيانات الشركة.
    الإرسال إلى:
    - مالك الشركة إن وجد
    - إيميل الشركة نفسه إن كان مختلفًا
    """
    recipients = []

    owner = getattr(company, "owner", None)
    owner_email = getattr(owner, "email", None) if owner else None
    if owner_email:
        recipients.append(owner_email)

    company_email = getattr(company, "email", None)
    if company_email and company_email not in recipients:
        recipients.append(company_email)

    if not recipients:
        logger.warning(
            "Company update email skipped: no recipients found. company_id=%s",
            getattr(company, "id", None),
        )
        return

    owner_name = (
        owner.get_full_name().strip()
        if owner and hasattr(owner, "get_full_name") and owner.get_full_name()
        else getattr(owner, "username", "User") if owner else "User"
    )

    subject = f"Primey HR Cloud | تم تحديث بيانات الشركة - {company.name}"

    text_changes = []
    for item in changed_fields:
        text_changes.append(
            f"- {item.get('field', '')}: {_safe_value(item.get('old', ''))} → {_safe_value(item.get('new', ''))}"
        )

    text_body = (
        f"مرحباً {owner_name},\n\n"
        f"تم تحديث بيانات الشركة بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_value(company.name)}\n"
        f"البريد الإلكتروني: {_safe_value(company.email)}\n"
        f"رقم الجوال: {_safe_value(company.phone)}\n"
        f"السجل التجاري: {_safe_value(company.commercial_number)}\n"
        f"الرقم الضريبي: {_safe_value(company.vat_number)}\n"
        f"رقم المبنى: {_safe_value(company.building_number)}\n"
        f"الشارع: {_safe_value(company.street)}\n"
        f"الحي: {_safe_value(company.district)}\n"
        f"المدينة: {_safe_value(company.city)}\n"
        f"الرمز البريدي: {_safe_value(company.postal_code)}\n"
        f"العنوان المختصر: {_safe_value(company.short_address)}\n\n"
        f"الحقول المتغيرة:\n"
        f"{chr(10).join(text_changes) if text_changes else '- لا توجد تغييرات معروضة'}\n\n"
        f"مع تحيات Primey HR Cloud"
    )

    html_body = _build_company_updated_email_html(
        owner_name=owner_name,
        company_name=company.name,
        company_email=company.email,
        company_phone=company.phone,
        commercial_number=company.commercial_number,
        vat_number=company.vat_number,
        building_number=company.building_number,
        street=company.street,
        district=company.district,
        city=company.city,
        postal_code=company.postal_code,
        short_address=company.short_address,
        changed_fields=changed_fields,
        logo_url=_get_company_logo_url(company),
    )

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)

        logger.info(
            "Company update email sent successfully. company_id=%s recipients=%s",
            getattr(company, "id", None),
            recipients,
        )
    except Exception:
        logger.exception(
            "Failed to send company update email. company_id=%s",
            getattr(company, "id", None),
        )


def _company_payload(company) -> dict:
    """
    Payload آمن ومتوافق مع حقول الشركة الحالية
    """
    return {
        "id": company.id,
        "name": getattr(company, "name", "") or "",
        "email": getattr(company, "email", "") or "",
        "phone": getattr(company, "phone", "") or "",
        "commercial_number": getattr(company, "commercial_number", "") or "",
        "vat_number": getattr(company, "vat_number", "") or "",
        "building_number": getattr(company, "building_number", "") or "",
        "street": getattr(company, "street", "") or "",
        "district": getattr(company, "district", "") or "",
        "city": getattr(company, "city", "") or "",
        "postal_code": getattr(company, "postal_code", "") or "",
        "short_address": getattr(company, "short_address", "") or "",
        "is_active": getattr(company, "is_active", False),
        "logo": _get_company_logo_url(company),
    }


# ============================================================
# GET — Company Settings Overview
# ============================================================

@login_required
@require_GET
def company_settings_overview(request):
    """
    جلب بيانات إعدادات الشركة الحالية
    """
    try:
        company = _get_active_company(request)

        if not company:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "لم يتم العثور على شركة نشطة للمستخدم الحالي.",
                },
                status=404,
            )

        return JsonResponse(
            {
                "status": "ok",
                "company": _company_payload(company),
            }
        )

    except Exception as exc:
        logger.exception("company_settings_overview failed: %s", exc)
        return JsonResponse(
            {
                "status": "error",
                "message": "تعذر تحميل إعدادات الشركة.",
            },
            status=500,
        )


# ============================================================
# POST — Update Company Settings
# يدعم:
# - JSON
# - FormData
# - رفع الشعار عبر المفتاح logo
# ============================================================

@login_required
@require_POST
def company_settings_update(request):
    """
    تحديث بيانات الشركة الأساسية بشكل آمن
    + دعم رفع شعار الشركة إلى Google Drive
    + حفظ رابطه داخل CompanyProfile.settings
    + إرسال إيميل عند أي تعديل
    """
    try:
        company = _get_active_company(request)

        if not company:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "لم يتم العثور على شركة نشطة للمستخدم الحالي.",
                },
                status=404,
            )

        payload = _request_payload(request)
        uploaded_logo = request.FILES.get("logo")

        allowed_fields = [
            "name",
            "email",
            "phone",
            "commercial_number",
            "vat_number",
            "building_number",
            "street",
            "district",
            "city",
            "postal_code",
            "short_address",
        ]

        changed_fields = []

        with transaction.atomic():
            for field in allowed_fields:
                if field not in payload:
                    continue

                if not hasattr(company, field):
                    continue

                old_value = getattr(company, field, None)
                new_value = _normalize_text(payload.get(field))

                if old_value != new_value:
                    setattr(company, field, new_value)
                    changed_fields.append(
                        {
                            "field": field,
                            "old": "" if old_value is None else str(old_value),
                            "new": str(new_value),
                        }
                    )

            # ------------------------------------------------
            # Logo Upload → Google Drive → CompanyProfile.settings
            # ------------------------------------------------
            if uploaded_logo:
                old_logo_url = _get_company_logo_url(company)

                uploaded_logo_data = _upload_company_logo_to_drive(
                    company=company,
                    uploaded_file=uploaded_logo,
                )

                new_logo_url = uploaded_logo_data["thumbnail_url"]
                new_file_id = uploaded_logo_data.get("file_id")
                new_web_view_link = uploaded_logo_data.get("web_view_link")

                _save_company_logo_url(
                    company=company,
                    logo_url=new_logo_url,
                    file_id=new_file_id,
                    web_view_link=new_web_view_link,
                )

                changed_fields.append(
                    {
                        "field": "logo",
                        "old": old_logo_url or "",
                        "new": new_logo_url,
                    }
                )

                if old_logo_url and old_logo_url != new_logo_url:
                    _delete_drive_file_if_exists(old_logo_url)

            if changed_fields:
                update_fields = []

                for item in changed_fields:
                    field_name = item["field"]
                    if field_name != "logo" and field_name not in update_fields and hasattr(company, field_name):
                        update_fields.append(field_name)

                if update_fields:
                    company.save(update_fields=update_fields)

                ip_address = _get_client_ip(request)

                for item in changed_fields:
                    _safe_add_audit_log(
                        company=company,
                        user=request.user,
                        section="company_settings",
                        field=item["field"],
                        old=item["old"],
                        new=item["new"],
                        ip=ip_address,
                    )

                transaction.on_commit(
                    lambda: _send_company_updated_email(
                        company=company,
                        changed_fields=changed_fields,
                    )
                )

        return JsonResponse(
            {
                "status": "ok",
                "message": "تم تحديث إعدادات الشركة بنجاح.",
                "company": _company_payload(company),
                "changed_fields": changed_fields,
            }
        )

    except Exception as exc:
        logger.exception("company_settings_update failed: %s", exc)
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc) if settings.DEBUG else "تعذر تحديث إعدادات الشركة.",
            },
            status=500,
        )