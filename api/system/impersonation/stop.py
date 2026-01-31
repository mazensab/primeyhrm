from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


@login_required
@require_POST
def stop_impersonation(request):
    """
    ============================================================
    🔐 Stop Company Impersonation
    ============================================================
    ✔ Session-based
    ✔ CSRF bypassed via middleware
    ✔ Safe permission check
    """

    impersonated_company_id = request.session.get("impersonated_company_id")
    impersonated_by = request.session.get("impersonated_by")

    if not impersonated_company_id:
        return JsonResponse(
            {"status": "error", "message": "No active impersonation"},
            status=409,
            json_dumps_params={"ensure_ascii": False},
        )

    if impersonated_by and impersonated_by != request.user.id and not request.user.is_superuser:
        return JsonResponse(
            {"status": "error", "message": "Not allowed"},
            status=403,
            json_dumps_params={"ensure_ascii": False},
        )

    request.session.pop("impersonated_company_id", None)
    request.session.pop("impersonated_by", None)

    return JsonResponse(
        {"status": "success"},
        json_dumps_params={"ensure_ascii": False},
    )
