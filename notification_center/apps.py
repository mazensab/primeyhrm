# 📂 الملف: notification_center/apps.py
# 🧭 إعداد تهيئة تطبيق مركز الإشعارات الذكي (Notification Center V5.6)
# 🚀 يدعم البث الفوري عبر WebSocket + اكتشاف Redis التلقائي + تكامل ذكي مع النظام
# ===============================================================

from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class NotificationCenterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notification_center"
    verbose_name = "🧭 مركز الإشعارات الذكي"

    def ready(self):
        """
        ⚙️ يتم تنفيذها تلقائيًا عند تحميل التطبيق:
        - اختبار جاهزية Redis أو InMemory Channel Layer
        - تهيئة إشعارات WebSocket الفورية
        - تحميل إشارات النظام (Signals)
        """
        # =========================================================
        # 🔌 اكتشاف نوع الـ Channel Layer
        # =========================================================
        try:
            from channels.layers import get_channel_layer
            layer = get_channel_layer()

            if hasattr(layer, "hosts"):
                logger.info("✅ Redis Channel Layer مفعل على 127.0.0.1:6379")
            else:
                logger.info("⚙️ InMemory Channel Layer مفعل (بدون Redis).")

        except Exception as e:
            logger.warning(f"⚠️ فشل اكتشاف Channel Layer: {e}")
            logger.info("🔄 سيتم استخدام InMemory Layer بشكل افتراضي.")

        # =========================================================
        # 💡 اختبار تحميل المستهلك (Consumer)
        # =========================================================
        try:
            from . import consumers  # تحميل مستهلك الإشعارات WebSocket
            logger.info("💡 NotificationConsumer تم تحميله بنجاح.")
        except Exception as e:
            logger.error(f"❌ خطأ أثناء تحميل NotificationConsumer: {e}")

        # =========================================================
        # 🧠 تحميل إشارات النظام الذكية
        # =========================================================
        try:
            import notification_center.signals
            logger.info("📡 إشارات النظام (signals) تم تفعيلها بنجاح.")
        except Exception as e:
            logger.error(f"❌ خطأ أثناء تحميل إشارات النظام: {e}")
