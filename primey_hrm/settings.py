"""
====================================================================
📦 Primey HR Cloud — Global Settings
🛠️ Version: V16.0 Ultra Stable — API + Admin + Email Ready
====================================================================
"""

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ============================================================
# 🧩 ENV HELPERS
# ============================================================

def env(key: str, default=None):
    return os.getenv(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_int(key: str, default: int = 0) -> int:
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# 🌍 ENVIRONMENT
# ============================================================

DJANGO_ENV = env("DJANGO_ENV", "local").strip().lower()
IS_LOCAL = DJANGO_ENV in ("local", "development", "dev")
IS_PRODUCTION = DJANGO_ENV in ("production", "prod")

# ============================================================
# ⚙️ SECURITY & HOSTS
# ============================================================

SECRET_KEY = env("DJANGO_SECRET_KEY", "")

# في اللوكل نجبر DEBUG=True افتراضيًا
# وفي الإنتاج يبقى منضبطًا من .env
DEBUG = env_bool("DJANGO_DEBUG", True if IS_LOCAL else False)

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "160.153.175.81",
    "primeyride.com",
    ".primeyride.com",
]

SECURE_CONTENT_TYPE_NOSNIFF = env_bool("SECURE_CONTENT_TYPE_NOSNIFF", True)
SECURE_BROWSER_XSS_FILTER = env_bool("SECURE_BROWSER_XSS_FILTER", True)
X_FRAME_OPTIONS = env("X_FRAME_OPTIONS", "DENY")

# ------------------------------------------------------------
# HTTPS / SSL
# ------------------------------------------------------------
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
else:
    # حماية صريحة للبيئة المحلية حتى لو دخلت قيم إنتاج في .env بالغلط
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_PROXY_SSL_HEADER = None

# ============================================================
# 🌐 FRONTEND (Next.js)
# ============================================================

FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", "https://primeyride.com")
FRONTEND_LOGIN_URL = f"{FRONTEND_BASE_URL}/login"
FRONTEND_HOME_URL = f"{FRONTEND_BASE_URL}/"



# ============================================================
# 💳 TAMARA SETTINGS
# ============================================================

TAMARA_ENABLED = env_bool("TAMARA_ENABLED", False)
TAMARA_ENVIRONMENT = env("TAMARA_ENVIRONMENT", "sandbox")  # sandbox | production
TAMARA_API_TOKEN = env("TAMARA_API_TOKEN", "")
TAMARA_NOTIFICATION_TOKEN = env("TAMARA_NOTIFICATION_TOKEN", "")
TAMARA_PUBLIC_KEY = env("TAMARA_PUBLIC_KEY", "")
TAMARA_TIMEOUT = env_int("TAMARA_TIMEOUT", 30)

# اختياري:
# إذا تركته فارغًا سيستخدم client.py البيئة تلقائيًا:
# - sandbox  -> https://api-sandbox.tamara.co
# - production -> https://api.tamara.co
TAMARA_API_BASE_URL = env("TAMARA_API_BASE_URL", None)

TAMARA_DEFAULT_CURRENCY = env("TAMARA_DEFAULT_CURRENCY", "SAR")
TAMARA_LOCALE = env("TAMARA_LOCALE", "en_US")

# روابط الرجوع من Tamara إلى الواجهة الأمامية
TAMARA_SUCCESS_URL = env(
    "TAMARA_SUCCESS_URL",
    f"{FRONTEND_BASE_URL}/billing/payment/success"
)

TAMARA_CANCEL_URL = env(
    "TAMARA_CANCEL_URL",
    f"{FRONTEND_BASE_URL}/billing/payment/cancel"
)

TAMARA_FAILURE_URL = env(
    "TAMARA_FAILURE_URL",
    f"{FRONTEND_BASE_URL}/billing/payment/failure"
)

# Webhook يرجع إلى Django Backend وليس Next.js
TAMARA_WEBHOOK_URL = env(
    "TAMARA_WEBHOOK_URL",
    "http://127.0.0.1:8000/api/payments/tamara/webhook/"
)

# ============================================================
# TAP PAYMENTS
# ============================================================

TAP_ENABLED = os.getenv("TAP_ENABLED", "false").lower() == "true"
TAP_SECRET_KEY = os.getenv("TAP_SECRET_KEY", "")
TAP_PUBLIC_KEY = os.getenv("TAP_PUBLIC_KEY", "")
TAP_BASE_URL = os.getenv("TAP_BASE_URL", "https://api.tap.company/v2")
TAP_TIMEOUT = int(os.getenv("TAP_TIMEOUT", "30"))
TAP_VERIFY_WEBHOOK = os.getenv("TAP_VERIFY_WEBHOOK", "true").lower() == "true"

# Optional
TAP_SOURCE_ID = os.getenv("TAP_SOURCE_ID", "src_all")
TAP_MERCHANT_ID = os.getenv("TAP_MERCHANT_ID", "")

TAP_SUCCESS_URL = os.getenv(
    "TAP_SUCCESS_URL",
    f"{FRONTEND_BASE_URL}/billing/payment/success",
)

TAP_CANCEL_URL = os.getenv(
    "TAP_CANCEL_URL",
    f"{FRONTEND_BASE_URL}/billing/payment/cancel",
)

TAP_WEBHOOK_URL = os.getenv(
    "TAP_WEBHOOK_URL",
    "http://127.0.0.1:8000/api/system/payments/tap/webhook/",
)

# ============================================================
# 💬 WHATSAPP SESSION GATEWAY
# ============================================================

WHATSAPP_SESSION_GATEWAY_URL = env(
    "WHATSAPP_SESSION_GATEWAY_URL",
    "http://127.0.0.1:3100",
)

WHATSAPP_SESSION_GATEWAY_TOKEN = env(
    "WHATSAPP_SESSION_GATEWAY_TOKEN",
    env("GATEWAY_TOKEN", ""),
)

WHATSAPP_SESSION_GATEWAY_TIMEOUT = env_int(
    "WHATSAPP_SESSION_GATEWAY_TIMEOUT",
    20,
)

# ------------------------------------------------------------
# 🚀 Auto Start Controls
# ------------------------------------------------------------
WHATSAPP_GATEWAY_AUTOSTART = env_bool(
    "WHATSAPP_GATEWAY_AUTOSTART",
    True,
)

WHATSAPP_GATEWAY_AUTOSTART_HEALTH_TIMEOUT = env_int(
    "WHATSAPP_GATEWAY_AUTOSTART_HEALTH_TIMEOUT",
    2,
)

WHATSAPP_GATEWAY_AUTOSTART_BOOT_TIMEOUT = env_int(
    "WHATSAPP_GATEWAY_AUTOSTART_BOOT_TIMEOUT",
    25,
)

WHATSAPP_GATEWAY_DIR = env(
    "WHATSAPP_GATEWAY_DIR",
    str(BASE_DIR / "whatsapp_center" / "session_gateway"),
)

WHATSAPP_GATEWAY_LOG_FILE = env(
    "WHATSAPP_GATEWAY_LOG_FILE",
    str(BASE_DIR / "logs" / "whatsapp_gateway.log"),
)

# ============================================================
# 🌐 ROOT URLS
# ============================================================

ROOT_URLCONF = "primey_hrm.urls"
# ============================================================
# 🔐 AUTH CONFIG
# ============================================================

LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/admin/login/"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# ============================================================
# 📌 INSTALLED APPS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",
    "channels",
    "django_apscheduler",

    # Project Apps
    "control_center",
    "rest_framework",
    "auth_center",
    "company_manager",
    "employee_center",
    "biotime_center.apps.BiotimeCenterConfig",
    "attendance_center.apps.AttendanceCenterConfig",
    "leave_center",
    "notification_center",
    "billing_center.apps.BillingCenterConfig",
    "settings_center",
    "payroll_center",
    "performance_center",
    "whatsapp_center",
    "system_log",
    "api",
]

# ============================================================
# 🔓 CSRF BYPASS (SYSTEM ONLY — SAFE FOR LOCAL & PRODUCTION)
# ============================================================

class DisableCSRFMiddleware:
    """
    تعطيل CSRF فقط لمسارات نظام محددة (System APIs)
    - آمن للإنتاج
    - لا يؤثر على تسجيل الدخول أو الجلسات
    """

    SAFE_PATH_PREFIXES = (
        "/api/system/payments/confirm-cash/",
        "/api/system/impersonation/start/",
        "/api/system/impersonation/stop/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # تعطيل CSRF فقط إذا كان المسار System محدد
        for prefix in self.SAFE_PATH_PREFIXES:
            if request.path.startswith(prefix):
                request._dont_enforce_csrf_checks = True
                break

        return self.get_response(request)

# ============================================================
# 🌐 MIDDLEWARE (ORDER MATTERS) — FIXED FOR NEXT.JS
# ============================================================

MIDDLEWARE = [
    # 🔹 CORS MUST BE FIRST
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",

    # 🔐 CSRF — BEFORE any custom middleware
    "django.middleware.csrf.CsrfViewMiddleware",

    # 🔑 Auth
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # 🧠 Company Context
    "api.middleware.company_impersonation.CompanyImpersonationMiddleware",

    # 🟡 Access / Subscription Guards
    "control_center.middleware.app_access.AppAccessMiddleware",
    "billing_center.middleware.subscription_enforcement.SubscriptionEnforcementMiddleware",

    # 📣 Messages
    "django.contrib.messages.middleware.MessageMiddleware",

    # 🖼 Security Headers
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # 🧾 Logs
    "system_log.middleware.SystemLogSniffer",

    # 🚫 CSRF Disable (LAST — SAFE)
    "primey_hrm.settings.DisableCSRFMiddleware",
]

# ============================================================
# 🔧 CORS & CSRF — NEXT.JS (FINAL / PRODUCTION SAFE)
# ============================================================

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",     # Local Next.js
    "https://primeyride.com",    # Production
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://primeyride.com",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "content-type",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

# ============================================================
# 🍪 SESSION & CSRF COOKIES — NEXT.JS (LOCAL + PROD SAFE)
# ============================================================

SESSION_ENGINE = "django.contrib.sessions.backends.db"

# -----------------------------
# Session Cookie
# -----------------------------
SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", True) if IS_PRODUCTION else False

# -----------------------------
# CSRF Cookie
# -----------------------------
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", True) if IS_PRODUCTION else False

# -----------------------------
# CSRF Behavior
# -----------------------------
CSRF_USE_SESSIONS = False
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"

# ============================================================
# 🔌 CHANNELS
# ============================================================

ASGI_APPLICATION = "primey_hrm.asgi.application"
WSGI_APPLICATION = "primey_hrm.wsgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(
                env("REDIS_HOST", "127.0.0.1"),
                env_int("REDIS_PORT", 6379),
            )],
        },
    }
}

# ============================================================
# 🗄️ DATABASE — MariaDB 10.11
# ============================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME", "primey_hrm"),
        "USER": env("DB_USER", "primey_user"),
        "PASSWORD": env("DB_PASSWORD", "StrongPass123"),
        "HOST": env("DB_HOST", "127.0.0.1"),
        "PORT": env("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

# ============================================================
# ☁️ GOOGLE DRIVE STORAGE (Employee Photos)
# ============================================================

GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE = BASE_DIR / "credentials" / "google-drive.json"
GOOGLE_DRIVE_FOLDER_ID = env(
    "GOOGLE_DRIVE_FOLDER_ID",
    "1emUXvcjnRvlIz0qnKEZDovtZnhPg2XH-"
)

# ============================================================
# 📧 EMAIL / SMTP
# ============================================================
# الفكرة:
# - في التطوير المحلي: نستخدم Console Backend افتراضيًا حتى تظهر الرسائل في terminal
# - في الإنتاج: غيّر EMAIL_BACKEND إلى SMTP عبر .env
# - بهذا الشكل create_notification(..., send_email=True) سيعمل مباشرة

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_HOST = env("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 20)

DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    "Primey HR Cloud <info@primeyride.com>"
)
SERVER_EMAIL = env("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
# اسم افتراضي مرسل يمكن استخدامه في أي templates أو helpers لاحقًا
EMAIL_FROM_NAME = env("EMAIL_FROM_NAME", "Primey HR Cloud")

# تفعيل/تعطيل البريد على مستوى النظام
EMAIL_NOTIFICATIONS_ENABLED = env_bool("EMAIL_NOTIFICATIONS_ENABLED", True)

# نسخة مخفية اختيارية لكل الرسائل المهمة
EMAIL_AUDIT_BCC = [
    email.strip()
    for email in env("EMAIL_AUDIT_BCC", "").split(",")
    if email.strip()
]

# ============================================================
# 🎨 TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ============================================================
# 🌍 Localization
# ============================================================

LANGUAGE_CODE = "ar"
TIME_ZONE = "Asia/Riyadh"
USE_I18N = True
USE_TZ = True

# ============================================================
# 📂 Static Files
# ============================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

# ============================================================
# ⏱️ ATTENDANCE SCHEDULER
# ============================================================

# تشغيل مزامنة الحضور التلقائية
SCHEDULER_AUTOSTART = True

# ============================================================
# 🔑 Default PK
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"