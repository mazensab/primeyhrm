"""
====================================================================
🚨 Alerts ACK API (READ ONLY / STATELESS)
Primey HR Cloud | System
====================================================================
✔ Acknowledge alert (contract only)
✔ No DB
✔ No persistence
✔ Placeholder for Phase C
====================================================================
"""

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from api.system.alerts.constants import AlertState


# ================================================================
# 🔕 POST /api/system/alerts/ack/
# ================================================================
@require_POST
def acknowledge_alert(request):
    """
    Acknowledge an alert.

    Expected payload:
    {
        "alert_type": "SLA_BREACH",
        "severity": "CRITICAL"
    }

    NOTE:
    - This endpoint is stateless for now.
    - No alert is persisted or modified.
    """

    alert_type = request.POST.get("alert_type")
    severity = request.POST.get("severity")

    if not alert_type or not severity:
        return JsonResponse(
            {
                "status": "error",
                "message": "alert_type and severity are required",
            },
            status=400,
        )

    return JsonResponse(
        {
            "status": "success",
            "acknowledged": True,
            "alert": {
                "type": alert_type,
                "severity": severity,
                "state": AlertState.ACKNOWLEDGED,
            },
        },
        status=200,
    )
