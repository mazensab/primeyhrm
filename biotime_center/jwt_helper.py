# ============================================================
# 📂 الملف: biotime_center/jwt_helper.py
# 🔐 Biotime Cloud JWT Helper — Version 7.0 (Official)
# ------------------------------------------------------------
# ✔ تسجيل دخول (company + email + password)
# ✔ تخزين JWT + expiry
# ✔ تجديد تلقائي في حال انتهاء الصلاحية
# ✔ مستخدم من API Client (V7.0)
# Developed by Mazen — Mham Cloud 2026
# ============================================================

import requests
import logging
from django.utils import timezone
from datetime import timedelta

from .models import BiotimeSetting

logger = logging.getLogger(__name__)


class BiotimeJWTHelper:

    # ========================================================
    # 🔑 1) التأكد من صلاحية الـ Token
    # ========================================================
    @staticmethod
    def is_token_valid(setting: BiotimeSetting):
        """يتحقق أن الـ Token موجود ولم ينتهِ."""
        if not setting.jwt_token or not setting.token_expiry:
            return False

        # هل انتهت الصلاحية؟
        return setting.token_expiry > timezone.now()

    # ========================================================
    # 🔒 2) عملية تسجيل الدخول الجديدة (company + email + password)
    # ========================================================
    @staticmethod
    def login(setting: BiotimeSetting):
        """يحصل على JWT Token من Biotime Cloud عبر تسجيل الدخول الكامل."""

        url = f"{setting.server_url.rstrip('/')}/api/v2/login/"

        payload = {
            "company": setting.company,
            "email": setting.email,
            "password": setting.password
        }

        try:
            res = requests.post(url, json=payload, timeout=12)

            if res.status_code != 200:
                logger.error(f"JWT Login Failed: {res.text}")
                return None

            data = res.json()

            token = data.get("token")
            expires_in = data.get("expires_in", 3600)  # ساعة افتراضياً

            if not token:
                return None

            # تخزين بيانات تسجيل الدخول
            setting.jwt_token = token
            setting.token_expiry = timezone.now() + timedelta(seconds=expires_in)
            setting.last_login_status = "success"
            setting.last_login_at = timezone.now()

            setting.save(update_fields=[
                "jwt_token",
                "token_expiry",
                "last_login_status",
                "last_login_at",
            ])

            return token

        except Exception as e:
            logger.error(f"JWT Login Fatal Error: {e}")
            return None

    # ========================================================
    # 🔁 3) تجديد أو إعادة استخدام الـ Token
    # ========================================================
    @staticmethod
    def get_token(setting: BiotimeSetting):
        """يُرجع Token صالح — أو يقوم بتجديده تلقائيًا."""

        # صالح؟ استخدمه مباشرة
        if BiotimeJWTHelper.is_token_valid(setting):
            return setting.jwt_token

        # غير صالح → تسجيل دخول جديد
        return BiotimeJWTHelper.login(setting)

    # ========================================================
    # 🧩 4) بناء Headers للطلبات
    # ========================================================
    @staticmethod
    def build_headers(setting: BiotimeSetting):
        """يُرجع الـ Header الجاهز لإرسال طلبات API."""

        token = BiotimeJWTHelper.get_token(setting)
        if not token:
            return None

        return {
            "Authorization": f"JWT {token}",
            "Content-Type": "application/json",
        }
