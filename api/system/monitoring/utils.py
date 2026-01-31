from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Count
from system_log.models import SystemLog


# ============================================================
# 🧠 Monitoring Utils — FINAL
# ============================================================

def last_24h_queryset(qs):
    return qs.filter(created_at__gte=now() - timedelta(hours=24))


def severity_breakdown(qs):
    return {
        "info": qs.filter(severity="info").count(),
        "warning": qs.filter(severity="warning").count(),
        "error": qs.filter(severity="error").count(),
        "critical": qs.filter(severity="critical").count(),
    }


def top_modules(qs, limit=5):
    return list(
        qs.values("module")
        .annotate(total=Count("id"))
        .order_by("-total")[:limit]
    )
