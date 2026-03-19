import os
import tempfile

from django.conf import settings

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ============================================================
# Google Drive Settings
# ============================================================

SCOPES = ["https://www.googleapis.com/auth/drive"]


# ============================================================
# Drive Service
# ============================================================

def get_drive_service():

    credentials = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )

    service = build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False
    )

    return service


# ============================================================
# Upload File
# ============================================================

def upload_file(file_obj, filename, content_type):

    service = get_drive_service()

    # =========================================
    # Save temp file
    # =========================================

    temp_file = tempfile.NamedTemporaryFile(delete=False)

    for chunk in file_obj.chunks():
        temp_file.write(chunk)

    temp_file.close()

    # =========================================
    # Metadata
    # =========================================

    file_metadata = {
        "name": filename,
        "parents": [settings.GOOGLE_DRIVE_FOLDER_ID],
    }

    media = MediaFileUpload(
        temp_file.name,
        mimetype=content_type,
        resumable=True
    )

    # =========================================
    # Upload
    # =========================================

    uploaded = service.files().create(
        body={
            "name": "shell_test.txt",
            "parents": [settings.GOOGLE_DRIVE_FOLDER_ID]
        },
        media_body=media,
        fields="id",
        supportsAllDrives=True,
        supportsTeamDrives=True
    ).execute()
    
    file_id = uploaded.get("id")

    # =========================================
    # Make public
    # =========================================

    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
        supportsAllDrives=True
    ).execute()

    # =========================================
    # Delete temp file
    # =========================================

    os.unlink(temp_file.name)

    # =========================================
    # Public URL
    # =========================================

    return f"https://drive.google.com/uc?id={file_id}"