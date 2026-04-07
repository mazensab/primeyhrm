# ================================================================
# 🛰️ System Log Live Consumer — V4 (Mham Cloud)
# ================================================================
# 🔥 يقوم ببث السجلات الجديدة مباشرة إلى المتصفح (Real-Time)
# 🔌 يعمل عبر Django Channels + Redis
# 👤 يدعم ربط المستخدم بالشركة (Company ID)
# 🎯 متوافق مع V1 + V2 + V3 (AJAX + Export + Sniffer)
# ================================================================

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class SystemLogConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        """
        🚀 عند اتصال العميل WebSocket:
        - نحصل على company_id من المسار
        - ننضم لغرفة بث السجلات الخاصة بتلك الشركة
        """

        self.company_id = self.scope["url_route"]["kwargs"]["company_id"]
        self.room_group_name = f"system_log_{self.company_id}"

        # الانضمام لغرفة البث
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # رسالة ترحيب
        await self.send(text_data=json.dumps({
            "type": "connected",
            "message": f"🟢 Connected to System Log Live Stream (Company {self.company_id})"
        }))

    async def disconnect(self, close_code):
        """
        ❌ عند إغلاق الاتصال:
        - مغادرة غرفة البث
        """

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # ============================================================
    # 🟢 استقبال رسالة من الباكند → إرسال للمتصفح
    # ============================================================
    async def stream_log(self, event):
        """
        🔴 يتم استدعاؤها تلقائيًا عندما يقوم Sniffer أو أي جزء من النظام
        بعمل broadcast عبر group_send.
        """

        await self.send(text_data=json.dumps({
            "type": "log",
            "id": event["id"],
            "module": event["module"],
            "action": event["action"],
            "severity": event["severity"],
            "message": event["message"],
            "created_at": event["created_at"],
            "user": event["user"],
        }))
