"""
====================================================================
📦 Primey HR Cloud — Global Settings
🛠️ Version: V15.8 Ultra Stable — API + Admin ONLY (FINAL)
====================================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# ⚙️ SECURITY & HOSTS
# ============================================================

SECRET_KEY = "django-insecure-w$^!m!d12n$mg0cy9drt($p#6rxj(8u8*n7y36xi*7=!=9ko1^"
DEBUG = True  # ⚠️ اجعلها False في Production النهائي مع HTTPS

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "160.153.175.81",          # IP السيرفر
    ".primeyhr.com",           # عند إضافة الدومين لاحقًا
]

# ============================================================
# 🌐 FRONTEND (Next.js)
# ============================================================

FRONTEND_BASE_URL = "http://160.153.175.81:3000"  # عدّل البورت إذا لزم
FRONTEND_LOGIN_URL = f"{FRONTEND_BASE_URL}/login"
FRONTEND_HOME_URL = f"{FRONTEND_BASE_URL}/"

# ============================================================
# 🌐 ROOT URLS
# ============================================================

ROOT_URLCONF = "primey_hrm.urls"

# ============================================================
# 🔐 AUTH CONFIG (Admin ONLY)
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
    "django_extensions",

    # Project Apps
    "control_center",
    "auth_center",
    "company_manager",
    "employee_center",
    "biotime_center.apps.BiotimeCenterConfig",
    "attendance_center",
    "leave_center",
    "notification_center",
    "billing_center.apps.BillingCenterConfig",
    "settings_center",
    "analytics_engine",
    "payroll_center",
    "smart_assistant",
    "printing_engine",
    "system_log",
    "api",

    # External
    "django_apscheduler",
    "corsheaders",
    "channels",
]

# ============================================================
# 🔓 CSRF BYPASS — SYSTEM INTERNAL ONLY (HARD GUARANTEE)
# ============================================================

class DisableCSRFMiddleware:
    """
    تعطيل CSRF لمسارات System الداخلية الحساسة فقط
    (Session-based, Super Admin actions)
    """

    SAFE_PATH_PREFIXES = (
        "/api/system/payments/confirm-cash/",
        "/api/system/impersonation/start/",
        "/api/system/impersonation/stop/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for path in self.SAFE_PATH_PREFIXES:
            if request.path.startswith(path):
                request._dont_enforce_csrf_checks = True
                break
        return self.get_response(request)

# ============================================================
# 🌐 MIDDLEWARE (ORDER IS CRITICAL — DO NOT TOUCH)
# ============================================================

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",

    # 🔐 Company Impersonation Context
    "api.middleware.company_impersonation.CompanyImpersonationMiddleware",

    # 🔓 Explicit CSRF bypass (internal system only)
    "primey_hrm.settings.DisableCSRFMiddleware",

    # 🛡️ Global CSRF protection
    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # App-level guards
    "control_center.middleware.app_access.AppAccessMiddleware",
    "billing_center.middleware.subscription_enforcement.SubscriptionEnforcementMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "system_log.middleware.SystemLogSniffer",
]

# ============================================================
# 🔧 CORS & CSRF — Next.js + Session Auth (FINAL)
# ============================================================

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://160.153.175.81:3000",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://160.153.175.81:3000",
]

CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"

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
# 🍪 COOKIES & SESSIONS — Next.js Compatible
# ============================================================

SESSION_ENGINE = "django.contrib.sessions.backends.db"

SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False   # 🔒 True مع HTTPS
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = False      # 🔒 True مع HTTPS
CSRF_COOKIE_SAMESITE = "Lax"

CSRF_USE_SESSIONS = False

# ============================================================
# 🔌 CHANNELS
# ============================================================

ASGI_APPLICATION = "primey_hrm.asgi.application"
WSGI_APPLICATION = "primey_hrm.wsgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    }
}

# ============================================================
# 🗄️ DATABASE
# ============================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "primey_hrm",
        "USER": "root",
        "PASSWORD": "1234",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# ============================================================
# 🎨 TEMPLATES (Admin ONLY — No Frontend)
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
# ⏱️ APScheduler — Feature Flags
# ============================================================

SCHEDULER_AUTOSTART = True

# ============================================================
# 🔁 Billing
# ============================================================

BILLING_RENEW_WINDOW_DAYS = 5

# ============================================================
# 🇸🇦 National Address (Saudi Post / SPL)
# ============================================================

NATIONAL_ADDRESS_API_KEY = "b9eb3a2f08e74c4ba81b32f6bf4f3d99"
NATIONAL_ADDRESS_BASE_URL = "https://api.address.gov.sa"
NATIONAL_ADDRESS_TIMEOUT = 8  # seconds

# ============================================================
# 📂 Static Files
# ============================================================

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ============================================================
# 🔑 Default PK
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
