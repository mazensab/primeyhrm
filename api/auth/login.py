# ============================================================
# 🔐 Primey HR Cloud — Login API (Ultra Stable V7.5 FINAL)
# ============================================================

from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json


@csrf_exempt
@require_POST
def login_api(request):
    """
    POST /api/auth/login/

    ✔ Session-based (Django)
    ✔ JSON only
    ✔ NO redirects
    """

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
            {"message": "Username and password are required"},
            status=400,
        )

    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None:
        return JsonResponse(
            {"message": "Invalid credentials"},
            status=401,
        )

    # 🔥 النقطة الحاسمة
    login(request, user)

    # 🔒 تأكيد حفظ الجلسة
    request.session.save()

    return JsonResponse(
        {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_superuser": user.is_superuser,
            },
        },
        status=200,
    )
