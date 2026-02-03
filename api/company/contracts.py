# ============================================================
# 📄 Contracts API — Minimal Stub (SAFE MODE)
# Primey HR Cloud
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required


@require_GET
@login_required
def company_contracts_list(request):
    """
    Placeholder endpoint to prevent 404
    Used by Employee tabs (Contracts / Job)
    """
    return JsonResponse({
        "status": "ok",
        "contracts": [],
    })
