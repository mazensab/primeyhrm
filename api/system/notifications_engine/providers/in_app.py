"""
====================================================================
📥 In-App Notification Provider (CONTRACT)
Primey HR Cloud | Notifications Engine
====================================================================
✔ Interface only
✔ No DB
✔ No Django
✔ Phase C-1
====================================================================
"""

from typing import Dict, Any

from api.system.notifications_engine.constants import NotificationState


def send_in_app(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare in-app notification payload.

    This does NOT create Notification records yet.
    """

    return {
        "channel": "in_app",
        "state": NotificationState.PENDING,
        "payload": payload,
        "message": "In-app notification queued (no-op)",
    }
