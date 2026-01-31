# ============================================================
# 🔐 CSRF Bootstrap API (PUBLIC) — FINAL STABLE
# Primey HR Cloud
# ============================================================
# ✔ Sets csrftoken cookie correctly
# ✔ Public (NO AUTH required)
# ✔ Safe for Next.js Proxy
# ✔ Same-Origin compatible
# ✔ Cache disabled
# ✔ Production ready
# ============================================================

from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache


# ============================================================
# 🔐 GET /api/auth/csrf/
# ============================================================

@require_GET
@ensure_csrf_cookie
@never_cache
def csrf(request):
    """
    🔐 CSRF Bootstrap Endpoint

    - يقوم بزرع csrftoken داخل Cookie
    - يعمل بدون تسجيل دخول
    - آمن للاستخدام مع Next.js عبر Proxy
    - يمنع التخزين المؤقت نهائياً
    """

    response = JsonResponse({
        "status": "ok",
        "csrf": "initialized",
    })

    # 🔒 حماية إضافية للمتصفح (اختياري لكن صحي)
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response
