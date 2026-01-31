# 📂 الملف: notification_center/routing.py
# 🧭 Primey HR Cloud — Notification Routing V4.0
# 🔌 مسؤول عن توجيه قنوات WebSocket إلى مستهلك الإشعارات الذكي.
# ✅ متوافق مع Redis أو InMemory (Auto Layer Detection)
# ✅ يدعم تخصيص المستخدمين عبر الـ Scope (user_id)
# ------------------------------------------------------------

from django.urls import re_path
from . import consumers

# ============================================================
# 🔌 خريطة مسارات WebSocket لتطبيق Notification Center
# ============================================================
websocket_urlpatterns = [
    # 🧠 قناة عامة لكل المستخدمين — تُدار حسب الـ Scope.user
    re_path(r"^ws/notifications/$", consumers.NotificationConsumer.as_asgi()),

    # 💡 يمكن مستقبلاً إضافة مسارات إضافية مثل:
    # re_path(r"^ws/assistant/$", consumers.AssistantConsumer.as_asgi()),
    # re_path(r"^ws/analytics/$", consumers.AnalyticsConsumer.as_asgi()),
]
