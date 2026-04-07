# 📂 الملف: notification_center/consumers.py
# 🧠 Mham Cloud — Notification Consumer V5.0 (Unified Channel Naming)
# 🚀 متوافق 100% مع services.py + signals.py + Frontend

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Notification

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        """🔌 عند الاتصال — ربط المستخدم بالمجموعة الموحّدة user_{id}"""

        user = self.scope.get("user")

        if not user or user.is_anonymous:
            await self.close()
            return

        self.user = user

        # 🟢 اسم المجموعة الموحد (يستخدم في signals.py + services.py)
        self.group_name = f"user_{user.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        logger.info(f"🔗 WebSocket Connected for: {user.username}")

        # إرسال الإشعارات غير المقروءة
        await self.send_initial_unread()


    async def disconnect(self, close_code):
        """🔒 عند قطع الاتصال"""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)


    async def receive(self, text_data):
        """📨 استقبال أوامر العميل (mark_read)"""
        data = json.loads(text_data)

        if data.get("action") == "mark_read":
            note_id = data.get("id")
            if note_id:
                await self.mark_as_read(note_id)
                await self.send_json({"status": "ok"})


    async def send_initial_unread(self):
        """📬 إرسال آخر 5 إشعارات غير مقروءة + العدد"""
        unread = await self.get_latest_unread()
        count = await self.get_unread_count()

        await self.send_json({
            "type": "init",
            "unread_count": count,
            "unread": unread
        })


    async def send_notification(self, event):
        """
        🚨 يستقبل الأحداث القادمة من:
         - services.py  (broadcast_live_notification)
         - signals.py   (group_send)
        """
        note = event.get("data", {}).get("notification")

        if not note:
            return

        unread_count = await self.get_unread_count()

        await self.send_json({
            "type": "new",
            "notification": note,
            "unread_count": unread_count
        })


    # ============================================================
    # 🧩 DB Operations (Async)
    # ============================================================

    @database_sync_to_async
    def get_latest_unread(self):
        notes = Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).order_by("-created_at")[:5]

        return [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "severity": n.severity,
                "created_at": n.created_at.strftime("%Y-%m-%d %H:%M")
            }
            for n in notes
        ]


    @database_sync_to_async
    def get_unread_count(self):
        return Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()


    @database_sync_to_async
    def mark_as_read(self, pk):
        Notification.objects.filter(
            id=pk,
            recipient=self.user
        ).update(is_read=True)


    # Helper
    async def send_json(self, data: dict):
        await self.send(text_data=json.dumps(data, ensure_ascii=False))
