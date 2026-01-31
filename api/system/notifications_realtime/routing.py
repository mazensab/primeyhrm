"""
====================================================================
🔌 WebSocket Routing — Notifications
====================================================================
"""

from django.urls import path
from api.system.notifications_realtime.consumers import NotificationConsumer

websocket_urlpatterns = [
    path(
        "ws/system/notifications/",
        NotificationConsumer.as_asgi(),
    ),
]
