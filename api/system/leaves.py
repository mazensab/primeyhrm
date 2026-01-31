# ============================================================
# 🟦 System Leave APIs — FINAL
# Primey HR Cloud
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from leave_center.models import LeaveRequest, LeaveType
from leave_center.engines.reset_balance_engine import ResetBalanceEngine


# ============================================================
# 📊 GET /api/system/leaves/overview/
# ============================================================
@login_required
@require_http_methods(["GET"])
def system_leaves_overview(request):
    stats = (
        LeaveRequest.objects
        .values("status")
        .annotate(count=Count("id"))
    )

    return JsonResponse({
        "stats": list(stats),
        "total": LeaveRequest.objects.count(),
    })


# ============================================================
# 📄 GET /api/system/leaves/types/
# ============================================================
@login_required
@require_http_methods(["GET"])
def system_leave_types(request):
    qs = LeaveType.objects.select_related("company")

    return JsonResponse({
        "types": [
            {
                "id": t.id,
                "company": t.company.name,
                "name": t.name,
                "code": t.code,
                "is_paid": t.is_paid,
                "is_active": t.is_active,
            }
            for t in qs
        ]
    })


# ============================================================
# 🔁 POST /api/system/leaves/reset-balance/
# ============================================================
@login_required
@require_http_methods(["POST"])
def reset_leave_balances(request):
    year = request.POST.get("year")

    ResetBalanceEngine.reset(year=year)

    return JsonResponse({
        "status": "reset_done",
        "year": year,
    })
