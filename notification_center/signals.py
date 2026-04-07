# 📂 الملف: notification_center/signals.py
# 🧠 إشعارات النظام التلقائية (Smart Notification Signals)
# 🚀 الإصدار V6.0 — Event/Delivery Ready
# ------------------------------------------------------------
# ✅ توحيد الإشعار عبر services.create_notification
# ✅ دعم البريد الاختياري من نفس المحرك الرسمي
# ✅ دعم NotificationEvent + NotificationDelivery
# ✅ إزالة التكرار اليدوي لـ Notification.objects.create + WebSocket
# ✅ Fail-Safe: أي خطأ في الإشعارات لا يكسر إنشاء الشركة أو المستخدم
# ------------------------------------------------------------

from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from company_manager.models import Company
from .services import create_notification

logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================
# 🧩 Helpers
# ============================================================
def _email_enabled_for_signals() -> bool:
    """
    تفعيل البريد في الـ signals يكون اختياريًا.
    افتراضيًا:
    - في DEBUG: بدون بريد لتجنب الإزعاج أثناء التطوير
    - في الإنتاج: يمكن تفعيله من الإعدادات العامة للبريد
    """
    if getattr(settings, "DEBUG", False):
        return False

    return bool(getattr(settings, "EMAIL_NOTIFICATIONS_ENABLED", True))


def _system_staff_users():
    """
    جلب مستخدمي النظام الداخلي الذين يستلمون تنبيهات عامة.
    """
    return User.objects.filter(is_staff=True)


# ============================================================
# 🏢 1️⃣ إشعار عند إنشاء شركة جديدة
# ============================================================
@receiver(post_save, sender=Company)
def notify_company_created(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        admins = _system_staff_users()
        if not admins.exists():
            logger.info("ℹ️ لا يوجد مستخدمو نظام staff لاستلام إشعار إنشاء الشركة.")
            return

        title = f"🏢 تم تسجيل شركة جديدة: {instance.name}"
        message = f"تم إنشاء الشركة ({instance.name}) وإضافتها للنظام بنجاح."

        for admin in admins:
            create_notification(
                recipient=admin,
                title=title,
                message=message,
                notification_type="system",
                severity="success",
                send_email=_email_enabled_for_signals(),
                company=instance,
                event_code="company_created",
                event_group="company",
                source="signals.notify_company_created",
                context={
                    "company_id": getattr(instance, "id", None),
                    "company_name": getattr(instance, "name", ""),
                },
                target_object=instance,
                target_user=admin,
            )

        logger.info(f"✅ تم إرسال إشعارات إنشاء الشركة: {instance.name}")

    except Exception as e:
        logger.warning(f"⚠️ فشل Signal إشعار إنشاء الشركة (غير حرج): {e}")


# ============================================================
# 👤 2️⃣ إشعار عند إنشاء مستخدم جديد
# ============================================================
@receiver(post_save, sender=User)
def notify_user_created(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        admins = _system_staff_users()
        if not admins.exists():
            logger.info("ℹ️ لا يوجد مستخدمو نظام staff لاستلام إشعار إنشاء المستخدم.")
            return

        display_name = instance.get_full_name() or instance.username
        title = f"👤 مستخدم جديد: {instance.username}"
        message = f"تم تسجيل المستخدم {display_name} بنجاح."

        user_company = getattr(instance, "company", None)

        for admin in admins:
            # تجنب إرسال إشعار للمستخدم نفسه لو كان staff وتم إنشاؤه الآن
            if admin.id == instance.id:
                continue

            create_notification(
                recipient=admin,
                title=title,
                message=message,
                notification_type="user",
                severity="info",
                send_email=_email_enabled_for_signals(),
                company=user_company,
                event_code="user_created",
                event_group="auth",
                source="signals.notify_user_created",
                context={
                    "user_id": getattr(instance, "id", None),
                    "username": getattr(instance, "username", ""),
                    "display_name": display_name,
                    "email": getattr(instance, "email", ""),
                    "company_id": getattr(user_company, "id", None) if user_company else None,
                },
                target_object=instance,
                target_user=admin,
            )

        logger.info(f"✅ تم إرسال إشعارات إنشاء المستخدم: {instance.username}")

    except Exception as e:
        logger.warning(f"⚠️ فشل Signal إشعار إنشاء المستخدم (غير حرج): {e}")