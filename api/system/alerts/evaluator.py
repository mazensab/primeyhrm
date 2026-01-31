"""
====================================================================
🚨 Alerts Engine — Threshold Evaluator (STATELESS)
Primey HR Cloud | System
====================================================================
✔ Evaluates metrics against thresholds
✔ No persistence
✔ No side effects
✔ Deterministic output
✔ Phase B Core Engine
====================================================================
"""

from typing import Dict, List, Any

from api.system.alerts.constants import (
    AlertType,
    AlertSeverity,
    AlertState,
)
from api.system.alerts.thresholds import THRESHOLD_RULES


# ============================================================
# 🧠 Operator Evaluation
# ============================================================
def _compare(operator: str, actual: float, expected: float) -> bool:
    """
    Compare actual value with expected based on operator.
    """
    if operator == "<":
        return actual < expected
    if operator == "<=":
        return actual <= expected
    if operator == ">":
        return actual > expected
    if operator == ">=":
        return actual >= expected
    if operator == "==":
        return actual == expected

    raise ValueError(f"Unsupported operator: {operator}")


# ============================================================
# 🚨 Evaluate Single Alert Type
# ============================================================
def evaluate_alert_type(
    alert_type: str,
    metrics: Dict[str, Any],
) -> Dict[str, Any] | None:
    """
    Evaluate one alert type against its rules.
    Returns alert dict if triggered, otherwise None.
    """

    rules = THRESHOLD_RULES.get(alert_type, [])
    triggered_rule = None

    for rule in rules:
        key = rule["condition_key"]

        if key not in metrics:
            continue

        actual_value = metrics[key]

        if actual_value is None:
            continue

        if _compare(
            operator=rule["operator"],
            actual=actual_value,
            expected=rule["value"],
        ):
            triggered_rule = rule
            break

    if not triggered_rule:
        return None

    return {
        "type": alert_type,
        "severity": triggered_rule["severity"],
        "state": AlertState.TRIGGERED,
        "condition_key": triggered_rule["condition_key"],
        "actual_value": metrics.get(triggered_rule["condition_key"]),
        "threshold": triggered_rule["value"],
        "operator": triggered_rule["operator"],
    }


# ============================================================
# 🚨 Evaluate All Alerts
# ============================================================
def evaluate_all_alerts(
    metrics: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Evaluate all alert types against provided metrics.
    Returns list of triggered alerts.
    """

    alerts: List[Dict[str, Any]] = []

    for alert_type in THRESHOLD_RULES.keys():
        alert = evaluate_alert_type(alert_type, metrics)
        if alert:
            alerts.append(alert)

    return alerts
