# ============================================================
# 🔐 Mham Cloud — Login API
# Ultra Stable V10 (SPA + SESSION + CSRF FINAL)
# ============================================================

from django.contrib.auth import authenticate, login
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import (
    ensure_csrf_cookie,
    csrf_protect,
)
import json
from auth_center.models import ActiveUserSession
from django.utils import timezone

# ============================================================
# ✅ CSRF BOOTSTRAP ENDPOINT
# ============================================================

@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf_api(request):
    """
    GET /api/auth/csrf/

    ✔ Forces csrftoken cookie
    ✔ Required for Next.js SPA
    ✔ Must be called before login
    """

    return JsonResponse(
        {"csrf": "ok"},
        status=200,
    )


# ============================================================
# ✅ LOGIN API
# ============================================================

@csrf_protect
@require_http_methods(["POST", "OPTIONS"])
def login_api(request):
    """
    POST /api/auth/login/

    ✔ Django Session Authentication
    ✔ CSRF Protected
    ✔ SPA Compatible
    ✔ Multi-Tenant Ready
    ✔ Production Safe
    """

    # ---------------------------------------------------------
    # 🟡 CORS PREFLIGHT
    # ---------------------------------------------------------
    if request.method == "OPTIONS":
        response = HttpResponse(status=200)
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        return response

    # ---------------------------------------------------------
    # 📦 Parse JSON
    # ---------------------------------------------------------
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse(
            {"message": "Invalid JSON"},
            status=400,
        )

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return JsonResponse(
            {"message": "Username and password required"},
            status=400,
        )

    # ---------------------------------------------------------
    # 🔐 AUTHENTICATION
    # ---------------------------------------------------------


    user = authenticate(
        request=request,
        username=username,
        password=password,
        backend="django.contrib.auth.backends.ModelBackend",
    )

    if not user:
        return JsonResponse(
            {"message": "Invalid credentials"},
            status=401,
        )

    # ---------------------------------------------------------
    # 🔥 CREATE SESSION
    # ---------------------------------------------------------
    login(request, user)

    # ---------------------------------------------------------
    # 🔐 Ω+ SESSION REGISTRY (PATCH LAYER)
    # ---------------------------------------------------------
    try:
        session_key = request.session.session_key

        # تأكد أن session_key موجود
        if not session_key:
            request.session.save()
            session_key = request.session.session_key

        # استخراج معلومات الجهاز
        ip_address = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # إنشاء سجل جلسة جديد (Multi-Login allowed)
        ActiveUserSession.objects.create(
            user=user,
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent,
            session_version=1,
            is_active=True,
        )

        # تخزين version داخل Django session
        request.session["session_version"] = 1

    except Exception:
        pass

    # ---------------------------------------------------------
    # 🏢 AUTO COMPANY BIND
    # ---------------------------------------------------------
    try:
        from company_manager.models import CompanyUser

        company_user = (
            CompanyUser.objects
            .filter(user=user, is_active=True)
            .order_by("id")
            .first()
        )

        if company_user:
            request.session["active_company_id"] = (
                company_user.company_id
            )

    except Exception:
        pass

    # ---------------------------------------------------------
    # ✅ FORCE SESSION SAVE
    # ---------------------------------------------------------
    request.session.modified = True
    request.session.save()

    # ---------------------------------------------------------
    # ✅ RESPONSE
    # ---------------------------------------------------------
    response = JsonResponse(
        {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_superuser": user.is_superuser,
            },
        }
    )

    response["Access-Control-Allow-Credentials"] = "true"
    response.set_cookie(
        "sessionid",
        request.session.session_key,
        httponly=True,
        secure=False,   # اجعله True في الإنتاج مع HTTPS
        samesite="Lax",
    )

    return response