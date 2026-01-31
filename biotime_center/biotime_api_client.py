# ================================================================
# 📂 الملف: biotime_center/biotime_api_client.py
# 🌩️ Biotime API Client — الإصدار الرسمي V9.4 (Tenant Subdomain Stable ✅)
# 🚀 يدعم: Session Login + JWT Fallback + Terminals + Transactions + Employees
# 🌀 متوافق 100% مع Biotime Cloud الحقيقي
# ================================================================

import requests
from django.utils import timezone
from datetime import timedelta
import logging
import re

logger = logging.getLogger(__name__)


class BiotimeAPIClient:

    # ============================================================
    # 🚀 1) التهيئة الأساسية (Subdomain Auto Resolve ✅)
    # ============================================================
    def __init__(self, setting):
        self.setting = setting

        raw_base = (setting.server_url or "").rstrip("/")
        company = (setting.biotime_company or "").strip()

        if not raw_base.startswith("https://"):
            raise ValueError("Biotime server_url must start with https://")

        if not company:
            raise ValueError("biotime_company is required")

        # ======================================================
        # ✅ Resolve Company Base URL (Smart Tenant Resolver)
        # ======================================================
        base_host = raw_base.replace("https://", "").strip()

        if company.startswith("http://") or company.startswith("https://"):
            self.base_url = company.rstrip("/")

        elif "." in company:
            self.base_url = f"https://{company}"

        else:
            self.base_url = f"https://{company}.{base_host}"

        self.email = setting.email
        self.password = setting.password
        self.biotime_company = company

        # 🧠 HTTP Session (كوكيز المتصفح)
        self.session = requests.Session()

        logger.info(
            "🌐 Biotime Base URL Resolved: %s (company=%s)",
            self.base_url,
            company,
        )

    # ============================================================
    # 🔐 2) تسجيل الدخول عبر Session الحقيقي (Biotime Cloud)
    # ============================================================
    def _session_login(self) -> bool:
        """
        تسجيل دخول مطابق تمامًا لما يستخدمه المتصفح:
        /accounts/check_pwd/
        """

        if not self.biotime_company:
            logger.error("❌ Session Login aborted: biotime_company is empty")
            return False

        login_url = f"{self.base_url}/accounts/check_pwd/"

        payload = {
            "company_name": self.biotime_company,
            "username": self.email,
            "password": self.password,
            "login_user": "user",
        }

        logger.info(
            "🔵 Attempting Session Login: %s | company=%s",
            login_url,
            self.biotime_company,
        )
        logger.debug("📦 Session Login Payload: %s", payload)

        try:
            res = self.session.post(
                login_url,
                data=payload,
                timeout=20,
            )

            logger.info("📥 Session Login Status: %s", res.status_code)
            logger.debug(
                "🍪 Cookies After Login: %s",
                self.session.cookies.get_dict(),
            )

            if res.status_code != 200:
                logger.error("❌ Session Login HTTP Failed: %s", res.text[:500])
                return False

            if not self.session.cookies:
                logger.error("❌ Session Login Failed: No cookies received")
                return False

            # تحديث حالة الاتصال
            self.setting.last_login_status = "success"
            self.setting.last_login_at = timezone.now()
            self.setting.save(
                update_fields=["last_login_status", "last_login_at"]
            )

            logger.info("✔ Session Login Success")
            return True

        except Exception as e:
            logger.exception("🔥 Session Login Exception: %s", e)
            return False

    # ============================================================
    # 🔐 3) تسجيل الدخول — JWT TOKEN (Fallback فقط)
    # ============================================================
    def authenticate(self):
        # نحاول Session أولاً
        if self._session_login():
            return {"status": "success", "mode": "session"}

        logger.warning("⚠️ Session login failed — trying JWT fallback")

        if not self.biotime_company:
            logger.error("❌ JWT Login aborted: biotime_company is empty")
            return {
                "status": "error",
                "message": "Biotime tenant is not configured",
            }

        login_url = f"{self.base_url}/jwt-api-token-auth/"

        try:
            payload = {
                "company_code": self.biotime_company,
                "company": self.biotime_company,
                "email": self.email,
                "password": self.password,
            }

            logger.debug("📦 JWT Login Payload: %s", payload)

            res = requests.post(
                login_url,
                json=payload,
                timeout=15,
            )

            if res.status_code != 200:
                logger.error("❌ JWT Login Failed: %s", res.text[:500])
                self.setting.last_login_status = "failed"
                self.setting.save(update_fields=["last_login_status"])
                return {"status": "error", "message": res.text}

            data = res.json()
            token = data.get("token")

            if not token:
                logger.error("❌ JWT Login Failed: Token missing in response")
                return {
                    "status": "error",
                    "message": "JWT token not returned from Biotime",
                }

            expiry = timezone.now() + timedelta(hours=8)

            self.setting.jwt_token = token
            self.setting.token_expiry = expiry
            self.setting.last_login_status = "success"
            self.setting.last_login_at = timezone.now()
            self.setting.save()

            logger.info("✔ JWT Login Success | token_expiry=%s", expiry)
            return {"status": "success", "mode": "jwt", "token": token}

        except Exception as e:
            logger.exception("❌ JWT Login Exception: %s", e)
            return {"status": "error", "message": str(e)}

    # ============================================================
    # 🔁 4) الحصول على وضع المصادقة الحالي
    # ============================================================
    def get_token(self):
        if self.session and self.session.cookies:
            return "SESSION"

        if (
            not self.setting.jwt_token or
            not self.setting.token_expiry or
            self.setting.token_expiry <= timezone.now()
        ):
            logger.warning("⚠️ Token/session expired. Re-authenticating...")
            res = self.authenticate()
            if res.get("status") == "success":
                return res.get("mode")
            return None

        return "JWT"

    # ============================================================
    # 🧩 Helper — تنفيذ GET موحد (Session أو JWT)
    # ============================================================
    def _get(self, url, params=None, timeout=20):
        mode = self.get_token()
        if not mode:
            logger.error("❌ Cannot perform GET: No authentication")
            return None

        try:
            if mode == "SESSION":
                return self.session.get(url, params=params, timeout=timeout)

            return requests.get(
                url,
                headers={
                    "Authorization": f"JWT {self.setting.jwt_token}",
                    "Content-Type": "application/json",
                },
                params=params,
                timeout=timeout,
            )

        except Exception as e:
            logger.exception("🔥 HTTP GET Error: %s", e)
            return None

    # ============================================================
    # 🧩 Helper — تنفيذ POST موحد (Session أو JWT)
    # ============================================================
    def _post(self, url, json=None, data=None, timeout=20):
        """
        POST موحد يحافظ على:
        - Session Cookies عند توفرها
        - JWT Authorization عند الحاجة
        - Content-Type ثابت
        - منع تعارض json / data
        """

        mode = self.get_token()
        if not mode:
            logger.error("❌ Cannot perform POST: No authentication")
            return None

        if json is not None and data is not None:
            logger.error("❌ POST payload conflict: both json and data provided")
            return None

        headers = {
            "Content-Type": "application/json",
        }

        try:
            if mode == "SESSION":
                return self.session.post(
                    url,
                    json=json,
                    data=data,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=True,
                )

            headers["Authorization"] = f"JWT {self.setting.jwt_token}"

            return requests.post(
                url,
                json=json,
                data=data,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
            )

        except Exception as e:
            logger.exception("🔥 HTTP POST Transport Error: %s", e)
            return None

    # ============================================================
    # 🧩 Helper — تنفيذ PATCH موحد (Session أو JWT)
    # ============================================================
    def _patch(self, url, json=None, timeout=20):
        """
        PATCH موحد يحافظ على:
        - Session Cookies عند توفرها
        - JWT Authorization عند الحاجة
        - Content-Type ثابت
        - 🔁 Retry ذكي عند فشل Session أو JWT
        """

        mode = self.get_token()
        if not mode:
            logger.error("❌ Cannot perform PATCH: No authentication")
            return None

        headers = {
            "Content-Type": "application/json",
        }

        try:
            # -------------------------------
            # ✅ Session Mode
            # -------------------------------
            if mode == "SESSION":
                res = self.session.patch(
                    url,
                    json=json,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=True,
                )

                # 🔁 إذا فشل Session → نجرب JWT مباشرة
                if res is not None and res.status_code in (401, 403):
                    logger.warning(
                        "⚠️ PATCH Session failed (%s) — retrying with JWT",
                        res.status_code,
                    )

                    auth = self.authenticate()
                    if auth.get("status") != "success":
                        logger.error("❌ JWT Retry Auth Failed during PATCH")
                        return res

                    headers["Authorization"] = f"JWT {self.setting.jwt_token}"

                    return requests.patch(
                        url,
                        json=json,
                        headers=headers,
                        timeout=timeout,
                        allow_redirects=True,
                    )

                return res

            # -------------------------------
            # ✅ JWT Mode
            # -------------------------------
            headers["Authorization"] = f"JWT {self.setting.jwt_token}"

            res = requests.patch(
                url,
                json=json,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
            )

            # 🔁 Retry أخير إذا رجع None أو Unauthorized
            if res is None or res.status_code in (401, 403):
                logger.warning(
                    "⚠️ PATCH JWT failed (%s) — retrying once",
                    getattr(res, "status_code", "NO_RESPONSE"),
                )

                auth = self.authenticate()
                if auth.get("status") != "success":
                    logger.error("❌ JWT Re-Auth Failed during PATCH retry")
                    return res

                headers["Authorization"] = f"JWT {self.setting.jwt_token}"

                return requests.patch(
                    url,
                    json=json,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=True,
                )

            return res

        except Exception as e:
            logger.exception("🔥 HTTP PATCH Transport Error: %s", e)
            return None

    # ============================================================
    # 💻 5) جلب الأجهزة — Terminals
    # ============================================================
    def get_devices(self):
        url = f"{self.base_url}/iclock/api/terminals/"
        logger.info("📡 Fetching Terminals: %s", url)

        res = self._get(url, timeout=15)
        if not res or res.status_code != 200:
            return None

        data = res.json()
        if data.get("code") != 0:
            return None

        return data.get("data", [])

    # ============================================================
    # 💡 5.1) جلب تفاصيل جهاز واحد
    # ============================================================
    def get_device_info(self, device_id):
        url = f"{self.base_url}/iclock/api/terminals/{device_id}/"
        logger.info("📡 Fetching Device Info: %s", url)

        res = self._get(url, timeout=15)
        if not res or res.status_code != 200:
            return None

        data = res.json()
        if data.get("code") != 0:
            return None

        return data.get("data")

    # ============================================================
    # 🕒 6) جلب السجلات — Transactions
    # ============================================================
    def get_logs(self, from_date=None, to_date=None):
        base_endpoint = f"{self.base_url}/iclock/api/transactions/"

        params = {}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date

        all_logs = []
        next_url = base_endpoint

        logger.info("📡 Fetching Logs (Paged): %s", next_url)

        try:
            while next_url:
                res = self._get(next_url, params=params, timeout=20)
                if not res or res.status_code != 200:
                    break

                data = res.json()
                if data.get("code") != 0:
                    break

                logs_page = data.get("data", [])
                all_logs.extend(logs_page)

                next_url = data.get("next")
                params = None

            logger.info("📥 Total Logs Retrieved: %s", len(all_logs))
            return all_logs

        except Exception as e:
            logger.exception("🔥 Logs API Error: %s", e)
            return None

    # ============================================================
    # 👥 7) جلب الموظفين
    # ============================================================
    def get_employees(self):
        endpoint = f"{self.base_url}/personnel/api/employees/"
        all_employees = []
        next_url = endpoint
        page = 1

        logger.info("👥 Fetching Employees (Paged): %s", endpoint)

        try:
            while next_url:
                logger.info("➡️ Employees Page %s: %s", page, next_url)

                res = self._get(next_url, timeout=20)
                if not res or res.status_code != 200:
                    break

                payload = res.json()
                if payload.get("code", 0) != 0:
                    break

                data = payload.get("data") or []
                all_employees.extend(data)

                next_url = payload.get("next")
                page += 1

            logger.info("👥 Total Employees Retrieved: %s", len(all_employees))
            return all_employees

        except Exception as e:
            logger.exception("🔥 Employees API Fatal Error: %s", e)
            return None

    # ============================================================
    # ➕ 8) إنشاء موظف جديد
    # ============================================================
    def create_employee(self, payload: dict):
        """
        إنشاء موظف جديد في Biotime
        - تنظيف emp_code ليكون أرقام فقط
        - عدم المساس بباقي الحقول
        """

        endpoint = f"{self.base_url}/personnel/api/employees/"

        # ----------------------------------
        # 🧼 تنظيف emp_code (أرقام فقط)
        # ----------------------------------
        raw_code = str(payload.get("emp_code", "")).strip()
        clean_code = re.sub(r"[^\d]", "", raw_code)
        payload["emp_code"] = clean_code

        logger.info("🚀 Creating Biotime Employee")
        logger.info("📦 Payload (sanitized): %s", payload)

        try:
            res = self._post(endpoint, json=payload, timeout=20)

            if not res:
                return {
                    "status": "error",
                    "message": "Transport failure (no response)",
                }

            logger.info("📥 Create Employee Status: %s", res.status_code)
            logger.debug("📄 Raw Response: %s", res.text[:800])

            if res.status_code not in (200, 201):
                return {
                    "status": "error",
                    "message": f"HTTP {res.status_code}: {res.text}",
                }

            data = res.json()
            return {
                "status": "success",
                "data": data.get("data") or data,
            }

        except Exception as e:
            logger.exception("🔥 Create Employee API Fatal Error: %s", e)
            return {
                "status": "error",
                "message": str(e),
            }
