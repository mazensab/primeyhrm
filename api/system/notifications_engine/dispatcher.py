"""
====================================================================
📤 Notifications Engine — Dispatcher (ABSTRACTION LAYER)
Mham Cloud | System
====================================================================
✔ Unified send interface
✔ Channel-based dispatching
✔ No real sending (Phase C-1)
✔ No DB
✔ No side effects
====================================================================
"""

from typing import Dict, List, Any

from api.system.notifications_engine.constants import (
    NotificationChannel,
    NotificationState,
)


# ============================================================
# 📦 Dispatch Single Notification Plan
# ============================================================
def dispatch_notification(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatch a single notification plan.

    This is a placeholder dispatcher.
    No real sending happens here.

    Returns unified dispatch result.
    """

    channels: List[str] = plan.get("channels", [])
    results: List[Dict[str, Any]] = []

    for channel in channels:
        results.append({
            "channel": channel,
            "state": NotificationState.PENDING,
            "message": "Dispatch scheduled (no-op)",
        })

    return {
        "alert_type": plan.get("alert_type"),
        "priority": plan.get("priority"),
        "results": results,
    }


# ============================================================
# 📦 Dispatch Multiple Notification Plans
# ============================================================
def dispatch_notifications(
    plans: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Dispatch multiple notification plans.
    """

    dispatched: List[Dict[str, Any]] = []

    for plan in plans:
        dispatched.append(dispatch_notification(plan))

    return dispatched
