"""
====================================================================
📦 Primey HR Cloud — Global Settings
🛠️ Version: V15.9 Ultra Stable — API + Admin ONLY (PRODUCTION FIX)
====================================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# ⚙️ SECURITY & HOSTS
# ============================================================

SECRET_KEY = "django-insecure-w$^!m!d12n$mg0cy9drt($p#6rxj(8u8*n7y36xi*7=!=9ko1^"
DEBUG = False  # ✅ MUST be False with HTTPS

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "160.153.175.81",
    "primeyride.com",
    ".primeyride.com",
]

# ============================================================
# 🌐 FRONTEND (Next.js)
# ============================================================

FRONTEND_BASE_URL = "https://primeyride.com"
FRONTEND_LOGIN_URL = f"{FRONTEND_BASE_URL}/login"
FRONTEND_HOME_URL = f"{FRONTEND_BASE_URL}/"

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
]

# ============================================================
# 🔓 CSRF BYPASS (SYSTEM ONLY)
# ============================================================

class DisableCSRFMiddleware:
    SAFE_PATH_PREFIXES = (
        "/api/system/payments/confirm-cash/",
        "/api/system/impersonation/start/",
        "/api/system/impersonation/stop/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.SAFE_PATH_PREFIXES):
            request._dont_enforce_csrf_checks = True
        return self.get_response(request)

# ============================================================
# 🌐 MIDDLEWARE (ORDER MATTERS)
# ============================================================

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",

    "api.middleware.company_impersonation.CompanyImpersonationMiddleware",
    "primey_hrm.settings.DisableCSRFMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "control_center.middleware.app_access.AppAccessMiddleware",
    "billing_center.middleware.subscription_enforcement.SubscriptionEnforcementMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "system_log.middleware.SystemLogSniffer",
]

# ============================================================
# 🔧 CORS & CSRF — FIXED FOR HTTPS + NEXT.JS
# ============================================================

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    "https://primeyride.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://primeyride.com",
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
# 🍪 COOKIES — CRITICAL FIX
# ============================================================

SESSION_ENGINE = "django.contrib.sessions.backends.db"

SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "None"

CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "None"

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
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "primey_hr",
        "USER": "primey_user",
        "PASSWORD": "Mhamcloudhrm@1980ا",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}

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
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ============================================================
# 🔑 Default PK
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
