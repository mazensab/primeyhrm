# ============================================================
# 📂 api/company/settings.py
# 🏢 Company Settings API
# Mham Cloud
# Version: V2.2 Notification Center Cleanup ✅
# ============================================================

from __future__ import annotations

import json
import logging
import os
import tempfile
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from company_manager.models import CompanyUser, CompanyProfile
from notification_center.services_company import notify_company_settings_updated

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
    + تسجيل Audit
    + إطلاق إشعار رسمي عبر Notification Center
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
                    lambda: notify_company_settings_updated(
                        company=company,
                        changed_fields=changed_fields,
                        actor=request.user,
                        send_email=True,
                        send_in_app=True,
                        extra_context={
                            "ip_address": ip_address,
                        },
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