"""
====================================================================
🚨 System Alerts API (READ ONLY | Derived)
Primey HR Cloud | System
====================================================================
✔ No DB
✔ No persistence
✔ Derived from current metrics
✔ Uses evaluator engine
====================================================================
"""

from django.http import JsonResponse
from django.utils.timezone import now, timedelta

from biotime_center.models import BiotimeDevice, BiotimeSyncLog

from api.system.alerts.evaluator import evaluate_all_alerts


# ================================================================
# 🚨 GET /api/system/alerts/
# ================================================================
def list_system_alerts(request):
    """
    Returns derived alerts based on current system metrics.
    Read only.
    """

    now_time = now()
    window_start = now_time - timedelta(days=30)

    # ------------------------------------------------------------
    # Metrics (Derived) — mirror Monitoring Overview logic
    # ------------------------------------------------------------
    total_devices = BiotimeDevice.objects.count()
    online_devices = BiotimeDevice.objects.filter(status="connected").count()

    uptime_percent = (
        (online_devices / total_devices) * 100
        if total_devices > 0 else 100
    )

    logs_qs = BiotimeSyncLog.objects.filter(timestamp__gte=window_start)

    total_logs = logs_qs.count()
    error_logs = logs_qs.filter(status="ERROR").count()

    error_rate_percent = (
        (error_logs / total_logs) * 100
        if total_logs > 0 else 0
    )

    sla_percent = round(100 - error_rate_percent, 2)

    # ------------------------------------------------------------
    # Alert Metrics Payload for Evaluator
    # ------------------------------------------------------------
    metrics = {
        "uptime_percent": round(uptime_percent, 2),
        "error_rate_percent": round(error_rate_percent, 2),
        "sla_percent": sla_percent,

        # Fields below are placeholders for later engines:
        # - DEVICE_OFFLINE expects offline_hours per device
        # - SYNC_FAILURE expects failure_count
        #
        # For now, we do not trigger those without real inputs.
    }

    # ------------------------------------------------------------
    # Evaluate Alerts
    # ------------------------------------------------------------
    alerts = evaluate_all_alerts(metrics)

    return JsonResponse(
        {
            "status": "success",
            "window_days": 30,
            "metrics": metrics,
            "alerts": alerts,
        },
        status=200,
    )
