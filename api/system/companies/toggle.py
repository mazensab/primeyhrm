from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from company_manager.models import Company


@login_required
def toggle_company_active(request, company_id):

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    company = get_object_or_404(Company, id=company_id)

    company.is_active = not company.is_active
    company.save(update_fields=["is_active"])

    return JsonResponse({
        "success": True,
        "company_id": company.id,
        "is_active": company.is_active
    })