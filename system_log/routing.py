# ================================================================
# 🌐 System Log WebSocket Routing — V4 (Primey HR Cloud)
# ================================================================
# يربط Consumer بالمسار:
#    /ws/system_log/live/<company_id>/
# ================================================================

from django.urls import re_path
from .consumers import SystemLogConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/system_log/live/(?P<company_id>\d+)/$",
        SystemLogConsumer.as_asgi()
    ),
]
