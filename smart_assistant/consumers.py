# 📂 الملف: smart_assistant/consumers.py
# 🤖 Smart Assistant Live Consumer (WebSocket Real-Time Engine)
# 🚀 الإصدار 6.0 — بث حي تفاعلي مع المستخدمين + تكامل مع Notification Center

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from asgiref.sync import sync_to_async

from notification_center.services import create_notification
from .services import SmartQueryEngine

logger = logging.getLogger(__name__)


class SmartAssistantConsumer(AsyncWebsocketConsumer):
    """
    🧠 مستهلك WebSocket للمحادثة التفاعلية مع المساعد الذكي.
    - يستقبل أوامر المستخدم.
    - يرسل الرد فوراً.
    - يربط الرد بإشعار ذكي في النظام.
    """

    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.user = user
        self.group_name = f"user_{user.id}_assistant"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send_json({
            "reply": f"👋 مرحبًا {user.username}! أنا المساعد الذكي الخاص بـ Primey HR Cloud.",
            "time": timezone.now().strftime("%H:%M"),
        })

        logger.info(f"✅ WebSocket Connected for user {user.username}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"🔌 WebSocket Disconnected for {self.user.username}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            command = data.get("command", "").strip()
            if not command:
                await self.send_json({"reply": "❌ لم يتم إدخال أي استفسار."})
                return

            logger.info(f"🤖 Received command from {self.user.username}: {command}")

            # 🔍 تحليل الاستفسار باستخدام SmartQueryEngine
            reply = await sync_to_async(self._process_query)(command)

            # 📡 إرسال الرد للمستخدم
            await self.send_json({
                "reply": reply,
                "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

            # 🔔 إنشاء إشعار فوري في النظام
            await sync_to_async(create_notification)(
                recipient=self.user,
                title="💬 رد جديد من المساعد الذكي",
                message=f"سؤالك: {command}\nالرد: {reply}",
                notification_type="assistant",
                severity="info",
            )

        except Exception as e:
            logger.error(f"❌ خطأ أثناء استقبال الرسالة: {e}")
            await self.send_json({"reply": "⚠️ حدث خطأ أثناء تحليل الأمر."})

    def _process_query(self, query):
        """
        ⚙️ تشغيل محرك التحليل الذكي بشكل متزامن.
        """
        engine = SmartQueryEngine(self.user)
        return engine.analyze(query)
