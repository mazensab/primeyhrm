# ============================================================
# 🔐 Primey HR Cloud — Logout API
# AUTH Ω FINAL — Enterprise Hard Logout
# ============================================================

from django.contrib.auth import logout
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from auth_center.models import ActiveUserSession

@csrf_protect
@require_http_methods(["POST", "OPTIONS"])
def logout_api(request):
    """
    POST /api/auth/logout/

    ENTERPRISE LOGOUT FLOW
    ----------------------
    ✔ destroy django session
    ✔ flush session storage
    ✔ delete cookies
    ✔ SPA safe
    ✔ multi-tab safe
    ✔ middleware safe
    """

    # --------------------------------------------------------
    # 🟡 CORS PREFLIGHT
    # --------------------------------------------------------
    if request.method == "OPTIONS":
        response = HttpResponse(status=200)
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        return response
    # --------------------------------------------------------
    # 🔐 Ω+ SESSION DEACTIVATION (PATCH LAYER)
    # --------------------------------------------------------
    try:
        session_key = request.session.session_key

        if session_key:
            ActiveUserSession.objects.filter(
                session_key=session_key,
                is_active=True,
            ).update(
                is_active=False
            )
    except Exception:
        pass
    # --------------------------------------------------------
    # 🔐 DJANGO LOGOUT
    # --------------------------------------------------------
    logout(request)

    try:
        request.session.flush()
    except Exception:
        pass

    # --------------------------------------------------------
    # ✅ RESPONSE
    # --------------------------------------------------------
    response = JsonResponse(
        {
            "success": True,
            "message": "Logout successful",
        },
        status=200,
    )

    # --------------------------------------------------------
    # 🍪 HARD COOKIE DELETE
    # --------------------------------------------------------
    response.delete_cookie(
        "sessionid",
        path="/",
        samesite="Lax",
    )

    response.delete_cookie(
        "csrftoken",
        path="/",
        samesite="Lax",
    )

    response["Access-Control-Allow-Credentials"] = "true"

    return response