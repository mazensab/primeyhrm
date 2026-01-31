from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from company_manager.models import CompanyUser
from system_log.models import SystemLog

from .utils import (
    last_24h_queryset,
    severity_breakdown,
    top_modules,
)


# ============================================================
# 📈 Monitoring Metrics API — READ ONLY (FINAL)
# ============================================================

@login_required
@require_http_methods(["GET"])
def monitoring_metrics(request):
    cu = CompanyUser.objects.filter(
        user=request.user,
        is_active=True
    ).select_related("company").first()

    if not cu:
        return JsonResponse({"metrics": {}})

    qs = SystemLog.objects.filter(company=cu.company)

    last_24h = last_24h_queryset(qs)

    return JsonResponse({
        "metrics": {
            "total_logs": qs.count(),
            "last_24h": last_24h.count(),
            "severity": severity_breakdown(last_24h),
            "top_modules": top_modules(qs),
        }
    })
