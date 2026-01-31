# ============================================================
# 🔔 Notifications API — System Level (V1.0)
# Primey HR Cloud
# ============================================================
# ✔ Session-based
# ✔ SAFE MODE friendly
# ✔ Read / Actions only
# ✔ Does NOT interfere with WebSocket
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
    qs = Notification.objects.filter(
        recipient=request.user
    ).order_by("-created_at")[:20]

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

    return JsonResponse({
        "results": data,
        "unread_count": unread_count
    })


# ============================================================
# 📌 POST /api/system/notifications/mark-read/
# ============================================================
@login_required
@require_http_methods(["POST"])
def mark_notification_read(request):
    note_id = request.POST.get("id")

    if not note_id:
        return JsonResponse(
            {"error": "notification_id required"},
            status=400
        )

    Notification.objects.filter(
        id=note_id,
        recipient=request.user
    ).update(is_read=True)

    return JsonResponse({"status": "ok"})


# ============================================================
# 📌 POST /api/system/notifications/mark-all-read/
# ============================================================
@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    return JsonResponse({"status": "ok"})
