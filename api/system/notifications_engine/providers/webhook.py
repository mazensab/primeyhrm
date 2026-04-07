"""
====================================================================
🌐 Webhook Notification Provider (CONTRACT)
Mham Cloud | Notifications Engine
====================================================================
✔ Interface only
✔ No HTTP calls
✔ No retries
✔ Phase C-1
====================================================================
"""

from typing import Dict, Any

from api.system.notifications_engine.constants import NotificationState


def send_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare webhook notification payload.

    No outbound HTTP calls here.
    """

    return {
        "channel": "webhook",
        "state": NotificationState.PENDING,
        "payload": payload,
        "message": "Webhook dispatch planned (no-op)",
    }
