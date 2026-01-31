"""
====================================================================
📧 Email Notification Provider (CONTRACT)
Primey HR Cloud | Notifications Engine
====================================================================
✔ Interface only
✔ No SMTP
✔ No Celery
✔ Phase C-1
====================================================================
"""

from typing import Dict, Any

from api.system.notifications_engine.constants import NotificationState


def send_email(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare email notification payload.

    No real email sending happens here.
    """

    return {
        "channel": "email",
        "state": NotificationState.PENDING,
        "payload": payload,
        "message": "Email dispatch planned (no-op)",
    }
