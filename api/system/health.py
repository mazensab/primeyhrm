from django.http import JsonResponse
from django.db import connection
from django.utils.timezone import now, timedelta
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token

from django.conf import settings

# ================================================================
# Optional Redis
# ================================================================
try:
    import redis
    redis_client = redis.Redis(host="localhost", port=6379, db=0)
except Exception:
    redis_client = None


# ================================================================
# Helpers (Internal)
# ================================================================
def _is_super_admin(user):
    return user.is_authenticated and user.is_superuser


def _db_status():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
        return "ok"
    except Exception as e:
        return f"error: {e}"


def _redis_status():
    if not redis_client:
        return "not_configured"
    try:
        redis_client.ping()
        return "ok"
    except Exception as e:
        return f"error: {e}"


def _scheduler_status():
    """
    APScheduler snapshot
    مبدئيًا نفترض أنه يعمل طالما السيرفر شغال.
    يمكن ربطه لاحقًا بـ scheduler instance حقيقي.
    """
    return getattr(settings, "SCHEDULER_RUNNING", True)


def _system_flags():
    return {
        "readonly_mode": getattr(settings, "READONLY_MODE", False),
        "safe_mode": getattr(settings, "SAFE_MODE", False),
    }


# ================================================================
# ❤️ System Health — Snapshot (GET)
# ================================================================
@login_required
@require_http_methods(["GET"])
def system_health(request):
    if not _is_super_admin(request.user):
        return JsonResponse({"detail": "Forbidden"}, status=403)

    health = {
        "api": "ok",
        "database": _db_status(),
        "redis": _redis_status(),
        "scheduler": "running" if _scheduler_status() else "stopped",
        "errors_24h": 0,  # Placeholder (System Log لاحقًا)
    }

    flags = _system_flags()

    return JsonResponse(
        {
            "status": "success",
            "health": health,
            "readonly_mode": flags["readonly_mode"],
            "safe_mode": flags["safe_mode"],
            "timestamp": now().isoformat(),
        },
        status=200,
    )


# ================================================================
# 🔄 Action: Refresh Health
# ================================================================
@login_required
@require_http_methods(["POST"])
def health_refresh(request):
    if not _is_super_admin(request.user):
        return JsonResponse({"detail": "Forbidden"}, status=403)

    return JsonResponse(
        {
            "status": "success",
            "message": "Health refreshed",
            "timestamp": now().isoformat(),
        },
        status=200,
    )


# ================================================================
# ⏸️ Action: Pause Scheduler
# ================================================================
@login_required
@require_http_methods(["POST"])
def scheduler_pause(request):
    if not _is_super_admin(request.user):
        return JsonResponse({"detail": "Forbidden"}, status=403)

    settings.SCHEDULER_RUNNING = False

    return JsonResponse(
        {
            "status": "success",
            "scheduler": "stopped",
            "message": "Scheduler paused",
            "timestamp": now().isoformat(),
        },
        status=200,
    )


# ================================================================
# ▶️ Action: Resume Scheduler
# ================================================================
@login_required
@require_http_methods(["POST"])
def scheduler_resume(request):
    if not _is_super_admin(request.user):
        return JsonResponse({"detail": "Forbidden"}, status=403)

    settings.SCHEDULER_RUNNING = True

    return JsonResponse(
        {
            "status": "success",
            "scheduler": "running",
            "message": "Scheduler resumed",
            "timestamp": now().isoformat(),
        },
        status=200,
    )


# ================================================================
# 🔒 Action: Toggle Read-Only Mode
# ================================================================
@login_required
@require_http_methods(["POST"])
def toggle_readonly_mode(request):
    if not _is_super_admin(request.user):
        return JsonResponse({"detail": "Forbidden"}, status=403)

    current = getattr(settings, "READONLY_MODE", False)
    settings.READONLY_MODE = not current

    return JsonResponse(
        {
            "status": "success",
            "readonly_mode": settings.READONLY_MODE,
            "message": "Readonly mode toggled",
            "timestamp": now().isoformat(),
        },
        status=200,
    )


# ================================================================
# 🛡️ Action: Toggle Safe Mode
# ================================================================
@login_required
@require_http_methods(["POST"])
def toggle_safe_mode(request):
    if not _is_super_admin(request.user):
        return JsonResponse({"detail": "Forbidden"}, status=403)

    current = getattr(settings, "SAFE_MODE", False)
    settings.SAFE_MODE = not current

    return JsonResponse(
        {
            "status": "success",
            "safe_mode": settings.SAFE_MODE,
            "message": "Safe mode toggled",
            "timestamp": now().isoformat(),
        },
        status=200,
    )
