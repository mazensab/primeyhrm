"""
====================================================================
🔔 Notifications Engine — Constants (SINGLE SOURCE OF TRUTH)
Primey HR Cloud | System
====================================================================
✔ Notification Channels
✔ Priority Levels
✔ Notification States
✔ Alert → Notification Mapping
✔ Anti-Spam Defaults
✔ Phase C-1 (Architecture & Contracts)
====================================================================
"""

# ============================================================
# 📣 Notification Channels
# ============================================================
class NotificationChannel:
    """
    قنوات الإشعارات المدعومة
    """
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"


NOTIFICATION_CHANNELS = (
    NotificationChannel.IN_APP,
    NotificationChannel.EMAIL,
    NotificationChannel.WEBHOOK,
)


# ============================================================
# 🚦 Notification Priority
# ============================================================
class NotificationPriority:
    """
    أولوية الإشعار (تُشتق من Alert Severity)
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


NOTIFICATION_PRIORITIES = (
    NotificationPriority.LOW,
    NotificationPriority.MEDIUM,
    NotificationPriority.HIGH,
)


# ============================================================
# 🔁 Notification State
# ============================================================
class NotificationState:
    """
    حالة الإشعار داخل النظام
    """
    PENDING = "PENDING"      # تم إنشاؤه ولم يُرسل
    SENT = "SENT"            # تم الإرسال
    FAILED = "FAILED"        # فشل الإرسال
    READ = "READ"            # مقروء (In-App)


NOTIFICATION_STATES = (
    NotificationState.PENDING,
    NotificationState.SENT,
    NotificationState.FAILED,
    NotificationState.READ,
)


# ============================================================
# 🚨 Alert → Notification Priority Mapping
# ============================================================
"""
ربط صريح بين Severity الخاصة بالـ Alert
وأولوية الإشعار
"""

ALERT_SEVERITY_TO_PRIORITY = {
    "INFO": NotificationPriority.LOW,
    "WARNING": NotificationPriority.MEDIUM,
    "CRITICAL": NotificationPriority.HIGH,
}


# ============================================================
# 📊 Default Channels per Alert Type
# ============================================================
"""
أي Alert ينتج إشعارًا عبر هذه القنوات افتراضيًا
(قابل للتوسعة لاحقًا من Settings)
"""

DEFAULT_ALERT_CHANNELS = {
    # System level
    "SYSTEM_HEALTH": [NotificationChannel.IN_APP],
    "SLA_BREACH": [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
    "HIGH_ERROR_RATE": [NotificationChannel.IN_APP],
    "DEVICE_OFFLINE": [NotificationChannel.IN_APP],
    "SYNC_FAILURE": [NotificationChannel.IN_APP],
}


# ============================================================
# 🧱 Anti-Spam / Cooldown Policy (DEFAULTS)
# ============================================================
NOTIFICATION_POLICY = {
    # لا يُعاد إرسال نفس الإشعار لنفس القناة
    # خلال هذه المدة
    "cooldown_minutes": 30,

    # لا يتم إرسال إشعار إذا كان Alert في حالة ACK
    "skip_acknowledged_alerts": True,

    # الحد الأقصى للإشعارات المتشابهة في نافذة زمنية
    "max_duplicates_per_window": 1,
}
