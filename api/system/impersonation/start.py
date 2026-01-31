from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST

from company_manager.models import Company


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def start_impersonation(request):
    """
    ============================================================
    🔐 Start Company Impersonation (System Level)
    ============================================================
    ✔ Super Admin only
    ✔ Session-based
    ✔ CSRF bypassed via middleware (SAFE)
    ✔ Prevents double impersonation
    """

    if request.session.get("impersonated_company_id"):
        return JsonResponse(
            {"status": "error", "message": "Already impersonating"},
            status=409,
            json_dumps_params={"ensure_ascii": False},
        )

    company_id = request.POST.get("company_id")
    if not company_id:
        return JsonResponse(
            {"status": "error", "message": "company_id is required"},
            status=400,
            json_dumps_params={"ensure_ascii": False},
        )

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Company not found"},
            status=404,
            json_dumps_params={"ensure_ascii": False},
        )

    request.session["impersonated_company_id"] = company.id
    request.session["impersonated_by"] = request.user.id

    return JsonResponse(
        {
            "status": "success",
            "company": {"id": company.id, "name": company.name},
        },
        json_dumps_params={"ensure_ascii": False},
    )
