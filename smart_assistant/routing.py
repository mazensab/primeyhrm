# 📂 الملف: smart_assistant/routing.py
# 🔌 توجيه WebSocket الخاص بالمساعد الذكي التفاعلي

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/assistant/$", consumers.SmartAssistantConsumer.as_asgi()),
]
