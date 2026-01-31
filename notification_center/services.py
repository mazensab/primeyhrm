# 📂 الملف: notification_center/services.py
# 🧠 Primey HR Cloud — Smart Notification Services V4.6 (Live Sync & Redis Auto-Detect)
# 🚀 المرحلة 21 — بث إشعارات فورية عبر WebSocket + دعم بريد إلكتروني + Logging
# ------------------------------------------------------------
# ✅ إنشاء الإشعارات النظامية والمخصصة
# ✅ بث فوري للمستخدم (Real-time WebSocket Broadcast)
# ✅ تكامل مع Billing / Reports / HR / Assistant
# ✅ متوافق مع Redis أو InMemory (اكتشاف تلقائي من settings)
# ✅ محسّن لتكامل WebSocket الحالي في base_control.html
# ------------------------------------------------------------

import json
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================
# 🧩 1️⃣ الدالة العامة لإنشاء إشعار فردي + بث مباشر
# ============================================================
def create_notification(
    *,
    recipient: User,
    title: str,
    message: str,
    notification_type: str = "system",
    severity: str = "info",
    send_email: bool = False,
    link: str = None,
) -> Notification:
    """
    🧠 إنشاء إشعار جديد وتفعيله فورًا على واجهة المستخدم.
    ✅ يشمل:
        - حفظ في قاعدة البيانات
        - إرسال فوري عبر WebSocket
        - إرسال بريد (اختياري)
    """
    if not recipient:
        logger.warning("🚫 محاولة إنشاء إشعار بدون مستلم.")
        return None

    try:
        note = Notification.objects.create(
            recipient=recipient,
            title=title.strip(),
            message=message.strip(),
            notification_type=notification_type,
            severity=severity,
            link=link or "",
            sent_via_email=False,
        )

        # 🎯 بث الإشعار فوراً عبر WebSocket
        _broadcast_live_notification(note)

        # ✉️ إرسال بريد (اختياري)
        if send_email and recipient.email:
            try:
                send_mail(
                    subject=f"[Primey HR Cloud] {title}",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=True,
                )
                note.mark_as_sent_email()
            except Exception as e:
                logger.warning(f"📭 فشل إرسال بريد إشعار: {e}")

        logger.info(f"✅ إشعار جديد أُرسل للمستخدم {recipient.username}: {title}")
        return note

    except Exception as e:
        logger.error(f"❌ فشل إنشاء الإشعار: {e}")
        return None


# ============================================================
# 🔁 2️⃣ بث مباشر عبر WebSocket Channel Layer
# ============================================================
def _broadcast_live_notification(note: Notification):
    """
    📡 إرسال إشعار جديد للمجموعة المخصصة للمستخدم.
    يعمل مع Redis أو InMemory تلقائيًا.
    متكامل مع front-end listener في base_control.html
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("⚠️ لم يتم العثور على Channel Layer.")
            return

        # 🧩 نفس الاسم المستخدم في الـ frontend
        group_name = f"user_{note.recipient.id}"
        payload = {
            "type": "send_notification",
            "data": {
                "type": "new",
                "notification": {
                    "id": note.id,
                    "title": note.title,
                    "message": note.message,
                    "notification_type": note.notification_type,
                    "severity": note.severity,
                    "created_at": timezone.localtime(note.created_at).strftime("%Y-%m-%d %H:%M"),
                },
            },
        }

        async_to_sync(channel_layer.group_send)(group_name, payload)
        logger.debug(f"📡 بث إشعار مباشر للمجموعة: {group_name}")

    except Exception as e:
        logger.warning(f"⚠️ فشل بث الإشعار الفوري: {e}")


# ============================================================
# 🔔 3️⃣ إشعار جماعي
# ============================================================
def broadcast_notification(
    *,
    users: list[User],
    title: str,
    message: str,
    ntype: str = "system",
    severity: str = "info",
) -> list[Notification]:
    """
    🔔 إرسال إشعار جماعي إلى عدة مستخدمين (مع بث لحظي).
    يستخدم في:
      - الإعلانات العامة
      - تحديثات النظام
      - تنبيهات الإدارة
    """
    notes = []
    for user in users:
        note = create_notification(
            recipient=user,
            title=title,
            message=message,
            notification_type=ntype,
            severity=severity,
        )
        if note:
            notes.append(note)
    return notes


# ============================================================
# 📢 4️⃣ إعلان عام لجميع المستخدمين
# ============================================================
def announce_global(title: str, message: str, severity: str = "info"):
    """
    📢 إرسال إعلان عام لجميع المستخدمين في النظام.
    - يُنشأ إشعار في قاعدة البيانات لكل مستخدم.
    - يُبث فورًا في جميع الجلسات المتصلة.
    """
    users = User.objects.all()
    notes = []
    for user in users:
        try:
            note = Notification.objects.create(
                recipient=user,
                title=title.strip(),
                message=message.strip(),
                notification_type="announcement",
                severity=severity,
            )
            notes.append(note)
            _broadcast_live_notification(note)
        except Exception as e:
            logger.warning(f"⚠️ فشل إرسال إعلان للمستخدم {user.username}: {e}")
    logger.info(f"📢 تم بث إعلان عام لجميع المستخدمين: {title}")
    return notes


# ============================================================
# 💳 5️⃣ إشعار جاهز من نظام الفوترة
# ============================================================
def notify_billing_event(recipient: User, invoice_number: str, status: str):
    """💳 إشعار تلقائي من نظام الفوترة عند إنشاء أو دفع فاتورة."""
    title = f"💳 تحديث حالة الفاتورة رقم {invoice_number}"
    message = f"تم تحديث حالة الفاتورة رقم {invoice_number} إلى: {status}"
    severity = "success" if status.lower() == "paid" else "info"
    return create_notification(
        recipient=recipient,
        title=title,
        message=message,
        notification_type="billing",
        severity=severity,
    )


# ============================================================
# 📈 6️⃣ إشعار من وحدة التقارير والتحليلات
# ============================================================
def notify_report_generated(recipient: User, report_title: str):
    """📊 إشعار عند توليد تقرير جديد في Analytics Engine."""
    return create_notification(
        recipient=recipient,
        title=f"📊 تم إنشاء تقرير جديد: {report_title}",
        message=f"تم توليد التقرير ({report_title}) بنجاح وهو متاح الآن في لوحة التقارير.",
        notification_type="report",
        severity="success",
    )


# ============================================================
# 🤖 7️⃣ إشعارات المساعد الذكي
# ============================================================
def notify_smart_assistant(recipient: User, suggestion: str):
    """🤖 إشعار تلقائي من Smart Assistant يقترح إجراء أو تنبيه."""
    return create_notification(
        recipient=recipient,
        title="🤖 تنبيه من المساعد الذكي",
        message=suggestion,
        notification_type="assistant",
        severity="info",
    )
