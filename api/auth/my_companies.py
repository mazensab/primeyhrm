from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from company_manager.models import CompanyUser

@login_required
def my_companies(request):

    companies = CompanyUser.objects.filter(
        user=request.user
    ).select_related("company")

    data = []

    for c in companies:
        data.append({
            "id": c.company.id,
            "name": c.company.name
        })

    return JsonResponse(data, safe=False)