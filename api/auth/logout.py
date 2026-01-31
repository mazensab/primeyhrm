# ============================================================
# 🔐 Primey HR Cloud — Logout API
# V4 — HARD LOGOUT (FINAL)
# ============================================================

from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_POST
def logout_api(request):
    """
    POST /api/auth/logout/

    HARD LOGOUT:
    - logout(request)
    - session.flush()
    - delete sessionid cookie
    """

    logout(request)

    try:
        request.session.flush()
    except Exception:
        pass

    response = JsonResponse(
        {"success": True, "message": "تم تسجيل الخروج بنجاح"},
        status=200
    )

    response.delete_cookie("sessionid", path="/")

    return response
