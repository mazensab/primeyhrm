# ============================================================
# 🔔 Notifications API — System Level (V1.1)
# Primey HR Cloud
# ============================================================
# ✔ Session-based Auth
# ✔ SAFE MODE friendly
# ✔ Read / Actions only
# ✔ Multi-user safe
# ✔ WebSocket compatible
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from notification_center.models import Notification


# ============================================================
# 📥 GET /api/system/notifications/
# ============================================================

@login_required
@require_http_methods(["GET"])
def notifications_list(request):
    """
    Return latest notifications for current user
    """

    qs = (
        Notification.objects
        .filter(recipient=request.user)
        .only(
            "id",
            "title",
            "message",
            "severity",
            "notification_type",
            "is_read",
            "link",
            "created_at",
        )
        .order_by("-created_at")[:20]
    )

    data = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "severity": n.severity,
            "notification_type": n.notification_type,
            "is_read": n.is_read,
            "link": n.link,
            "created_at": n.created_at.isoformat(),
        }
        for n in qs
    ]

    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return JsonResponse(
        {
            "results": data,
            "unread_count": unread_count,
        }
    )


# ============================================================
# 📌 POST /api/system/notifications/read/<id>/
# ============================================================

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """
    Mark a single notification as read
    """

    updated = Notification.objects.filter(
        id=notification_id,
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    if not updated:
        return JsonResponse(
            {"error": "Notification not found"},
            status=404
        )

    return JsonResponse(
        {"status": "ok"}
    )


# ============================================================
# 📌 POST /api/system/notifications/read-all/
# ============================================================

@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """
    Mark all user notifications as read
    """

    updated = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    return JsonResponse(
        {
            "status": "ok",
            "updated": updated,
        }
    )