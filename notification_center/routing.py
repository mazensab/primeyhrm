# 📂 الملف: notification_center/routing.py
# 🧭 Mham Cloud — Notification Routing V4.0
# 🔌 مسؤول عن توجيه قنوات WebSocket إلى مستهلك الإشعارات الذكي.
# ✅ متوافق مع Redis أو InMemory (Auto Layer Detection)
# ✅ يدعم تخصيص المستخدمين عبر الـ Scope (user_id)
# ------------------------------------------------------------

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [

    # 🔔 Primey System Notifications
    re_path(
        r"^ws/system/notifications/$",
        consumers.NotificationConsumer.as_asgi()
    ),

]