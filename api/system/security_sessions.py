# ============================================================
# 🔐 PRIMEY HR CLOUD — SYSTEM SECURITY SESSIONS (Ω+)
# SuperAdmin Session Monitor
# ============================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_http_methods

from auth_center.models import ActiveUserSession


# ------------------------------------------------------------
# ✅ SuperAdmin Guard
# ------------------------------------------------------------
def superadmin_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser
    )(view_func)


# ============================================================
# 📋 List Active Sessions
# ============================================================
@superadmin_required
@require_http_methods(["GET"])
def list_active_sessions(request):

    sessions = (
        ActiveUserSession.objects
        .select_related("user")
        .filter(is_active=True)
        .order_by("-last_seen")
    )

    data = []

    for s in sessions:
        data.append({
            "id": s.id,
            "username": s.user.username,
            "user_id": s.user.id,
            "ip_address": s.ip_address,
            "user_agent": s.user_agent,
            "session_key": s.session_key,
            "session_version": s.session_version,
            "last_seen": s.last_seen,
            "created_at": s.created_at,
        })

    return JsonResponse(
        {"sessions": data},
        status=200,
    )


# ============================================================
# ❌ Force Logout Session
# ============================================================
@superadmin_required
@require_http_methods(["POST"])
def force_logout_session(request):

    session_id = request.POST.get("session_id")

    if not session_id:
        return JsonResponse(
            {"error": "session_id required"},
            status=400,
        )

    try:
        session = ActiveUserSession.objects.get(
            id=session_id,
            is_active=True,
        )

        session.is_active = False
        session.session_version += 1
        session.save()

        return JsonResponse(
            {"success": True},
            status=200,
        )

    except ActiveUserSession.DoesNotExist:
        return JsonResponse(
            {"error": "Session not found"},
            status=404,
        )