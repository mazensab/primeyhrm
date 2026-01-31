"""
====================================================================
📣 Notification Broadcaster (SYNC SAFE)
Primey HR Cloud | System
====================================================================
✔ Optional
✔ Safe to call
✔ No failure impact
====================================================================
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_notification(*, user_id: int, payload: dict) -> None:
    """
    Broadcast notification payload to a single user.
    """

    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "notify",
            "payload": payload,
        }
    )
