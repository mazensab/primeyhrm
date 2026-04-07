"""
====================================================================
🚨 Alerts & Thresholds — Definitions (RULES ONLY)
Mham Cloud | System
====================================================================
✔ Threshold rules per alert type
✔ No execution logic
✔ Pure configuration layer
✔ Consumes constants.py only
====================================================================
"""

from api.system.alerts.constants import (
    AlertType,
    AlertSeverity,
    DEFAULT_THRESHOLDS,
)


# ============================================================
# 📊 Threshold Rules Registry
# ============================================================
"""
كل Alert Type له مجموعة Rules
كل Rule:
- condition_key   → اسم القيمة التي سيقرأها evaluator
- operator        → نوع المقارنة
- value           → القيمة المرجعية
- severity        → مستوى الخطورة
"""

THRESHOLD_RULES = {

    # --------------------------------------------------------
    # SLA Breach
    # --------------------------------------------------------
    AlertType.SLA_BREACH: [
        {
            "condition_key": "sla_percent",
            "operator": "<",
            "value": DEFAULT_THRESHOLDS[AlertType.SLA_BREACH]["critical_below"],
            "severity": AlertSeverity.CRITICAL,
        },
        {
            "condition_key": "sla_percent",
            "operator": "<",
            "value": DEFAULT_THRESHOLDS[AlertType.SLA_BREACH]["warning_below"],
            "severity": AlertSeverity.WARNING,
        },
    ],

    # --------------------------------------------------------
    # High Error Rate
    # --------------------------------------------------------
    AlertType.HIGH_ERROR_RATE: [
        {
            "condition_key": "error_rate_percent",
            "operator": ">",
            "value": DEFAULT_THRESHOLDS[AlertType.HIGH_ERROR_RATE]["critical_above"],
            "severity": AlertSeverity.CRITICAL,
        },
        {
            "condition_key": "error_rate_percent",
            "operator": ">",
            "value": DEFAULT_THRESHOLDS[AlertType.HIGH_ERROR_RATE]["warning_above"],
            "severity": AlertSeverity.WARNING,
        },
    ],

    # --------------------------------------------------------
    # Device Offline
    # --------------------------------------------------------
    AlertType.DEVICE_OFFLINE: [
        {
            "condition_key": "offline_hours",
            "operator": ">=",
            "value": DEFAULT_THRESHOLDS[AlertType.DEVICE_OFFLINE]["critical_after_hours"],
            "severity": AlertSeverity.CRITICAL,
        },
        {
            "condition_key": "offline_hours",
            "operator": ">=",
            "value": DEFAULT_THRESHOLDS[AlertType.DEVICE_OFFLINE]["warning_after_hours"],
            "severity": AlertSeverity.WARNING,
        },
    ],

    # --------------------------------------------------------
    # Sync Failures
    # --------------------------------------------------------
    AlertType.SYNC_FAILURE: [
        {
            "condition_key": "failure_count",
            "operator": ">=",
            "value": DEFAULT_THRESHOLDS[AlertType.SYNC_FAILURE]["critical_after_failures"],
            "severity": AlertSeverity.CRITICAL,
        },
        {
            "condition_key": "failure_count",
            "operator": ">=",
            "value": DEFAULT_THRESHOLDS[AlertType.SYNC_FAILURE]["warning_after_failures"],
            "severity": AlertSeverity.WARNING,
        },
    ],
}
