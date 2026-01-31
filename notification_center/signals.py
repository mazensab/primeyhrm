# 📂 الملف: notification_center/signals.py
# 🧠 إشعارات النظام التلقائية (Smart Notification Signals)
# 🚀 الإصدار V4.1 — متوافق 100% مع الموديل الجديد

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification
from company_manager.models import Company

User = get_user_model()
channel_layer = get_channel_layer()

# ============================================================
# 🏢 1️⃣ إشعار عند إنشاء شركة جديدة
# ============================================================
@receiver(post_save, sender=Company)
def notify_company_created(sender, instance, created, **kwargs):
    if not created:
        return

    # ⚠️ إذا ما فيه أي staff → نوقف بدون إشعار
    admins = User.objects.filter(is_staff=True)
    if not admins.exists():
        return

    title = f"🏢 تم تسجيل شركة جديدة: {instance.name}"
    message = f"تم إنشاء الشركة ({instance.name}) وإضافتها للنظام بنجاح."

    for admin in admins:
        # 📨 إنشاء الإشعار
        Notification.objects.create(
            recipient=admin,
            company=instance,
            title=title,
            message=message,
            notification_type="system",
            severity="success",
        )

        # 📡 إرسال WebSocket مباشر
        async_to_sync(channel_layer.group_send)(
            f"user_{admin.id}",
            {
                "type": "send_notification",
                "data": {
                    "type": "new",
                    "notification": {
                        "title": title,
                        "message": message,
                        "severity": "success",
                    },
                },
            },
        )


# ============================================================
# 👤 2️⃣ إشعار عند إنشاء مستخدم جديد
# ============================================================
@receiver(post_save, sender=User)
def notify_user_created(sender, instance, created, **kwargs):
    if not created:
        return

    admins = User.objects.filter(is_staff=True)
    if not admins.exists():
        return

    title = f"👤 مستخدم جديد: {instance.username}"
    message = (
        f"تم تسجيل المستخدم "
        f"{instance.get_full_name() or instance.username} بنجاح."
    )

    for admin in admins:
        Notification.objects.create(
            recipient=admin,
            title=title,
            message=message,
            notification_type="user",
            severity="info",
        )

        async_to_sync(channel_layer.group_send)(
            f"user_{admin.id}",
            {
                "type": "send_notification",
                "data": {
                    "type": "new",
                    "notification": {
                        "title": title,
                        "message": message,
                        "severity": "info",
                    },
                },
            },
        )
