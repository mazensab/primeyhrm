from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from company_manager.models import CompanyUser
from system_log.models import SystemLog

from .serializers import serialize_log


# ============================================================
# 📊 Monitoring Logs API — READ ONLY (FINAL)
# ============================================================

@login_required
@require_http_methods(["GET"])
def monitoring_logs(request):
    """
    ترجع آخر السجلات (Super Admin فقط)
    """
    cu = CompanyUser.objects.filter(
        user=request.user,
        is_active=True
    ).select_related("company").first()

    if not cu:
        return JsonResponse({"logs": []})

    logs = (
        SystemLog.objects
        .filter(company=cu.company)
        .order_by("-created_at")[:100]
    )

    return JsonResponse({
        "logs": [serialize_log(l) for l in logs]
    })


@login_required
@require_http_methods(["GET"])
def monitoring_log_detail(request, log_id):
    try:
        log = SystemLog.objects.get(id=log_id)
    except SystemLog.DoesNotExist:
        return JsonResponse({"detail": "Not found"}, status=404)

    return JsonResponse({
        "log": serialize_log(log)
    })
