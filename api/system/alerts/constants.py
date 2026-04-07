"""
====================================================================
🚨 Alerts & Thresholds — Constants (SINGLE SOURCE OF TRUTH)
Mham Cloud | System
====================================================================
✔ Alert Types
✔ Severity Levels
✔ Alert States
✔ SLA / Threshold Defaults
✔ Locked Architecture — Phase B
====================================================================
"""

# ============================================================
# 🔔 Alert Types
# ============================================================
class AlertType:
    """
    أنواع التنبيهات المدعومة في النظام
    """
    SYSTEM_HEALTH = "SYSTEM_HEALTH"
    SLA_BREACH = "SLA_BREACH"
    HIGH_ERROR_RATE = "HIGH_ERROR_RATE"
    DEVICE_OFFLINE = "DEVICE_OFFLINE"
    SYNC_FAILURE = "SYNC_FAILURE"


ALERT_TYPES = (
    AlertType.SYSTEM_HEALTH,
    AlertType.SLA_BREACH,
    AlertType.HIGH_ERROR_RATE,
    AlertType.DEVICE_OFFLINE,
    AlertType.SYNC_FAILURE,
)


# ============================================================
# 🚦 Severity Levels
# ============================================================
class AlertSeverity:
    """
    درجة خطورة التنبيه
    """
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


ALERT_SEVERITIES = (
    AlertSeverity.INFO,
    AlertSeverity.WARNING,
    AlertSeverity.CRITICAL,
)


# ============================================================
# 🔁 Alert State Machine
# ============================================================
class AlertState:
    """
    دورة حياة التنبيه
    """
    OK = "OK"
    TRIGGERED = "TRIGGERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


ALERT_STATES = (
    AlertState.OK,
    AlertState.TRIGGERED,
    AlertState.ACKNOWLEDGED,
    AlertState.RESOLVED,
)


# ============================================================
# 📊 Default Thresholds (LOCKED)
# ============================================================
"""
جميع القيم هنا هي القيم الافتراضية الرسمية للنظام
ولا يتم تعديلها إلا بقرار معماري صريح
"""

DEFAULT_THRESHOLDS = {

    # --------------------------------------------------------
    # SLA
    # --------------------------------------------------------
    AlertType.SLA_BREACH: {
        "warning_below": 99.0,     # %
        "critical_below": 98.5,    # %
    },

    # --------------------------------------------------------
    # Error Rate
    # --------------------------------------------------------
    AlertType.HIGH_ERROR_RATE: {
        "warning_above": 1.0,      # %
        "critical_above": 5.0,     # %
    },

    # --------------------------------------------------------
    # Devices Offline
    # --------------------------------------------------------
    AlertType.DEVICE_OFFLINE: {
        "warning_after_hours": 24,
        "critical_after_hours": 48,
    },

    # --------------------------------------------------------
    # Sync Failures
    # --------------------------------------------------------
    AlertType.SYNC_FAILURE: {
        "warning_after_failures": 3,
        "critical_after_failures": 5,
    },
}


# ============================================================
# 🧱 Global Alert Rules
# ============================================================
ALERT_RULES = {
    "cooldown_minutes": 30,   # منع التكرار المزعج
    "auto_resolve": False,    # لا يوجد Auto Resolve بدون منطق صريح
    "allow_delete": False,    # التنبيهات لا تُحذف
}
