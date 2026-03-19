# ============================================================
# 📂 whatsapp_center/tasks.py
# Primey HR Cloud - WhatsApp Tasks
# ============================================================
# ملاحظة:
# هذه دوال منطقية فقط حاليًا.
# يمكن ربطها لاحقًا مع APScheduler أو Celery.
# ============================================================

from django.utils import timezone

from .event_router import notify_subscription_expiring_7_days
from .models import BroadcastStatus, WhatsAppBroadcast


def run_scheduled_broadcasts():
    """
    تنفيذ الرسائل الجماعية المجدولة.
    مبدئيًا Placeholder.
    """
    now = timezone.now()
    broadcasts = (
        WhatsAppBroadcast.objects
        .filter(status=BroadcastStatus.SCHEDULED, scheduled_at__lte=now)
        .order_by("scheduled_at", "id")
    )

    for broadcast in broadcasts:
        broadcast.status = BroadcastStatus.RUNNING
        broadcast.started_at = now
        broadcast.save(update_fields=["status", "started_at", "updated_at"])

        # لاحقًا:
        # - resolve recipients
        # - create log entries
        # - send messages
        # - update sent/failed counts

        broadcast.status = BroadcastStatus.COMPLETED
        broadcast.completed_at = timezone.now()
        broadcast.save(update_fields=["status", "completed_at", "updated_at"])


def run_subscription_expiry_reminders():
    """
    Placeholder:
    لاحقًا يتم ربطها مع billing_center فعليًا
    والبحث عن الاشتراكات التي تنتهي بعد 7 أيام.
    """
    # TODO:
    # - query subscriptions ending in 7 days
    # - notify company phone
    # - notify company admin phone
    return 0