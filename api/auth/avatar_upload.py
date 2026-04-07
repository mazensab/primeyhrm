# ============================================================
# Avatar Upload API
# Mham Cloud
# Upload Avatar → Google Drive
# Final Clean Version using notification_center/services_auth.py
# ============================================================

from __future__ import annotations

import logging
import os
import tempfile
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from auth_center.models import UserProfile
from notification_center.services_auth import notify_avatar_updated

logger = logging.getLogger(__name__)


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
# Avatar Upload
# ============================================================

@login_required
def avatar_upload(request):

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "POST required"},
            status=400,
        )

    uploaded_file = request.FILES.get("avatar")

    if not uploaded_file:
        return JsonResponse(
            {"success": False, "error": "No file uploaded"},
            status=400,
        )

    if uploaded_file.content_type not in ALLOWED_TYPES:
        return JsonResponse(
            {"success": False, "error": "Invalid file type"},
            status=400,
        )

    if uploaded_file.size > MAX_FILE_SIZE:
        return JsonResponse(
            {"success": False, "error": "File too large (max 5MB)"},
            status=400,
        )

    temp_path = None

    try:
        credentials_path = settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE

        if not os.path.exists(credentials_path):
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Credentials not found: {credentials_path}",
                },
                status=500,
            )

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

        ext = os.path.splitext(uploaded_file.name)[1]
        file_name = f"user_{request.user.id}_{uuid.uuid4().hex}{ext}"

        temp_path = os.path.join(
            tempfile.gettempdir(),
            f"avatar_{uuid.uuid4().hex}{ext}",
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
                "parents": [settings.GOOGLE_DRIVE_FOLDER_ID],
            },
            media_body=media,
            fields="id, webViewLink",
            supportsAllDrives=True,
            supportsTeamDrives=True,
        ).execute()

        file_id = uploaded.get("id")
        file_url = uploaded.get("webViewLink")

        drive_service.permissions().create(
            fileId=file_id,
            body={
                "type": "anyone",
                "role": "reader",
            },
            supportsAllDrives=True,
        ).execute()

        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        if profile.avatar_url:
            try:
                if "id=" in profile.avatar_url:
                    old_file_id = profile.avatar_url.split("id=")[-1].split("&")[0]
                    drive_service.files().delete(
                        fileId=old_file_id,
                        supportsAllDrives=True,
                    ).execute()
            except Exception:
                logger.warning(
                    "Failed to delete old avatar from Google Drive for user=%s",
                    request.user.id,
                    exc_info=True,
                )

        avatar_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w512"
        profile.avatar_url = avatar_url
        profile.save(update_fields=["avatar_url"])

        dispatch_result = notify_avatar_updated(
            user=request.user,
            avatar_url=avatar_url,
            request=request,
            actor=request.user,
        )

        if dispatch_result["notification_created"]:
            logger.info(
                "Avatar updated and auth notification dispatched successfully for user=%s",
                request.user.username,
            )
        else:
            logger.warning(
                "Avatar updated but auth notification was not created for user=%s",
                request.user.username,
            )

        return JsonResponse(
            {
                "success": True,
                "file_id": file_id,
                "url": file_url,
                "avatar": avatar_url,
                "notification_created": dispatch_result["notification_created"],
                "email_sent": dispatch_result["email_sent"],
                "email_error": dispatch_result["email_error"],
                "whatsapp_sent": dispatch_result["whatsapp_sent"],
                "whatsapp_error": dispatch_result["whatsapp_error"],
            }
        )

    except Exception as e:
        logger.exception("Avatar upload failed: %s", e)
        return JsonResponse(
            {
                "success": False,
                "error": str(e),
            },
            status=500,
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass