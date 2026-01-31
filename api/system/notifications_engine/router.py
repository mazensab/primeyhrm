"""
====================================================================
🔀 Notifications Engine — Router (DECISION LAYER)
Primey HR Cloud | System
====================================================================
✔ Alert → Notification routing
✔ Channel selection
✔ Priority derivation
✔ Anti-spam checks (static)
✔ No sending
✔ Phase C-1 Core
====================================================================
"""

from typing import Dict, List, Any

from api.system.notifications_engine.constants import (
    NotificationChannel,
    NotificationPriority,
    ALERT_SEVERITY_TO_PRIORITY,
    DEFAULT_ALERT_CHANNELS,
    NOTIFICATION_POLICY,
)
from api.system.alerts.constants import AlertState


# ============================================================
# 🧠 Route Single Alert
# ============================================================
def route_alert(alert: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Build notification routing plan for a single alert.

    Returns:
    {
        "alert_type": str,
        "severity": str,
        "priority": str,
        "channels": [str],
    }
    """

    # --------------------------------------------------------
    # Skip acknowledged alerts if policy says so
    # --------------------------------------------------------
    if (
        NOTIFICATION_POLICY.get("skip_acknowledged_alerts")
        and alert.get("state") == AlertState.ACKNOWLEDGED
    ):
        return None

    alert_type = alert.get("type")
    severity = alert.get("severity")

    if not alert_type or not severity:
        return None

    # --------------------------------------------------------
    # Determine priority
    # --------------------------------------------------------
    priority = ALERT_SEVERITY_TO_PRIORITY.get(
        severity,
        NotificationPriority.LOW,
    )

    # --------------------------------------------------------
    # Determine channels
    # --------------------------------------------------------
    channels: List[str] = DEFAULT_ALERT_CHANNELS.get(
        alert_type,
        [NotificationChannel.IN_APP],
    )

    return {
        "alert_type": alert_type,
        "severity": severity,
        "priority": priority,
        "channels": channels,
    }


# ============================================================
# 🧭 Route Multiple Alerts
# ============================================================
def route_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build notification routing plans for multiple alerts.
    """

    plans: List[Dict[str, Any]] = []

    for alert in alerts:
        plan = route_alert(alert)
        if plan:
            plans.append(plan)

    return plans
