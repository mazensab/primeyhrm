# ============================================================
# 📂 الملف: attendance_center/biotime_api.py
# 🌐 Biotime REST API — V4 Ultra Pro Class-Based
# ------------------------------------------------------------
# يدعم:
#   ✔ تسجيل الدخول والحصول على Token
#   ✔ جلب سجلات الحضور اليومية
#   ✔ جاهز للتوسعة (Employees – Departments – Devices)
# ============================================================

import requests
from datetime import datetime
from django.conf import settings


class BiotimeAPI:
    """
    🧠 محرك الاتصال مع Biotime — V4 Ultra Pro
    - يعتمد على Class واحدة منظمة
    - يدعم Token + GET Requests
    """

    def __init__(self):
        # 🔧 الإعدادات من settings.py
        self.base_url = getattr(settings, "BIOTIME_BASE_URL", "").rstrip("/")
        self.username = getattr(settings, "BIOTIME_USERNAME", "")
        self.password = getattr(settings, "BIOTIME_PASSWORD", "")

        # 🟦 Token يتم تحديثه تلقائيًا
        self.token = None

    # --------------------------------------------------------
    # 🔐 الحصول على Token
    # --------------------------------------------------------
    def authenticate(self):
        """
        🔐 تسجيل الدخول للحصول على Token من Biotime API
        """
        url = f"{self.base_url}/api/token/"
        data = {
            "username": self.username,
            "password": self.password,
        }

        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()

        self.token = response.json().get("access")
        return self.token

    # --------------------------------------------------------
    # 📩 طلب GET مع تضمين Token تلقائيًا
    # --------------------------------------------------------
    def _get(self, path, params=None):
        """
        📡 طلب GET مع Token تلقائي
        """
        if not self.token:
            self.authenticate()

        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.base_url}{path}"

        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    # --------------------------------------------------------
    # 📌 جلب سجلات الحضور اليومية
    # --------------------------------------------------------
    def get_today_attendance(self, date=None):
        """
        📦 جلب سجلات الحضور لليوم المحدد (أو تاريخ اليوم)
        """
        if date is None:
            date = datetime.today().strftime("%Y-%m-%d")

        params = {"date": date}
        data = self._get("/api/attendance/", params)

        return data.get("data", [])


# ============================================================
# ⚡ دوال مختصرة (Compatibility Mode for old integrations)
# ============================================================

def get_biotime_token():
    """
    🔒 توافق مع النظام القديم
    """
    return BiotimeAPI().authenticate()


def fetch_biotime_attendance_records():
    """
    🔄 توافق مع النظام القديم — جلب حضور اليوم
    """
    api = BiotimeAPI()
    return api.get_today_attendance()
