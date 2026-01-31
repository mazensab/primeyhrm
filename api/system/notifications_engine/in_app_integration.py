"""
====================================================================
🔔 In-App Notifications Integration (Phase C-2)
Primey HR Cloud | System
====================================================================
✔ Alert → Notification record
✔ Uses Notifications Engine contracts
✔ Writes to notification_center
✔ No WebSocket
✔ No async
✔ SAFE MODE compatible
====================================================================
"""

from typing import Dict, Any

from django.contrib.auth import get_user_model

from notification_center.models import Notification

from api.system.notifications_engine.router import route_alert
from api.system.notifications_engine.dispatcher import dispatch_notification
from api.system.notifications_engine.providers.in_app import send_in_app
from api.system.notifications_engine.constants import NotificationPriority


User = get_user_model()


# ============================================================
# 🔁 Process Single Alert → In-App Notification
# ============================================================
def process_alert_in_app(
    *,
    alert: Dict[str, Any],
    recipient: User,
) -> None:
    """
    Convert evaluated alert into in-app notification.
    """

    # --------------------------------------------------------
    # 1) Build routing plan
    # --------------------------------------------------------
    plan = route_alert(alert)
    if not plan:
        return

    # --------------------------------------------------------
    # 2) Dispatch (no-op, contract)
    # --------------------------------------------------------
    dispatch_notification(plan)

    # --------------------------------------------------------
    # 3) Only handle in-app channel here
    # --------------------------------------------------------
    if "in_app" not in plan.get("channels", []):
        return

    # --------------------------------------------------------
    # 4) Prepare payload
    # --------------------------------------------------------
    payload = {
        "title": alert.get("title", "System Alert"),
        "message": alert.get("message", ""),
        "severity": alert.get("severity"),
        "alert_type": alert.get("type"),
        "priority": plan.get("priority", NotificationPriority.LOW),
    }

    send_in_app(payload)

    # --------------------------------------------------------
    # 5) Create Notification record
    # --------------------------------------------------------
    Notification.objects.create(
        recipient=recipient,
        title=payload["title"],
        message=payload["message"],
        severity=payload["severity"],
        notification_type="alert",
        link=None,
    )
