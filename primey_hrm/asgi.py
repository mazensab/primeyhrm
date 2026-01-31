# ================================================================
# 📂 الملف: primey_hrm/asgi.py
# 🧭 ASGI Configuration — Primey HR Cloud V7 Ultra Pro
# ---------------------------------------------------------------
# 🚀 يدعم: HTTP + WebSocket
# 🔔 الإشعارات الحية (NotificationCenter V1)
# 🤖 المساعد الذكي (SmartAssistant)
# 📜 النظام الفوري للسجلات (SystemLog Live)
# ---------------------------------------------------------------
# 🧠 يعتمد Redis Channel Layer عند توفره – ويسقط تلقائياً إلى InMemory
# ================================================================

import os
import django
import logging

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# ================================================================
# 1️⃣ ضبط إعدادات Django
# ================================================================
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primey_hrm.settings")
django.setup()

logger = logging.getLogger("primey.asgi")


# ================================================================
# 2️⃣ تحميل مسارات WebSocket لجميع الوحدات (Auto Merge)
# ================================================================
websocket_routes = []

def safe_import_routes(app_path, name):
    """
    🛡 دالة آمنة لاستيراد مسارات WebSocket بدون كسر النظام.
    """
    try:
        module = __import__(f"{app_path}.routing", fromlist=["websocket_urlpatterns"])
        if hasattr(module, "websocket_urlpatterns"):
            logger.info(f"✅ تم تحميل مسارات WebSocket من الوحدة: {name}")
            return module.websocket_urlpatterns
        else:
            logger.warning(f"⚠️ الوحدة {name} لا تحتوي على websocket_urlpatterns")
    except Exception as e:
        logger.warning(f"⚠️ فشل تحميل مسارات WebSocket لوحدة {name}: {e}")
    return []


# وحدات النظام المعتمدة
APPS_WITH_SOCKETS = {
    "notification_center": "Notifications",
    "smart_assistant": "Smart Assistant",
    "system_log": "System Log",
}

for app, label in APPS_WITH_SOCKETS.items():
    websocket_routes += safe_import_routes(app, label)


# ================================================================
# 3️⃣ التطبيق الرئيسي ASGI
# ================================================================
application = ProtocolTypeRouter({
    "http": get_asgi_application(),

    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_routes)
    ),
})

logger.info("🚀 Primey HRM ASGI Layer جاهز للعمل — HTTP + WebSocket فعالان.")


# ================================================================
# 4️⃣ فحص جاهزية Redis أو Channel Layer
# ================================================================
try:
    from channels.layers import get_channel_layer
    layer = get_channel_layer()

    if hasattr(layer, "hosts"):
        logger.info("🔌 Redis Channel Layer مفعل بنجاح (Real-Time Production Mode)")
    else:
        logger.info("⚙️ InMemory Channel Layer مفعل — وضع التطوير (بدون Redis)")

except Exception as e:
    logger.error(f"❌ فشل اكتشاف Channel Layer: {e}")
