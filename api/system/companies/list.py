from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from billing_center.models import CompanySubscription
from company_manager.models import Company, CompanyUser


@login_required
def companies_list(request):

    companies = Company.objects.all().order_by("-created_at")

    result = []

    for company in companies:

        sub = (
            CompanySubscription.objects
            .filter(company=company)
            .select_related("plan")
            .order_by("-created_at")
            .first()
        )

        result.append({
            "id": company.id,
            "name": company.name,
            "is_active": company.is_active,
            "created_at": company.created_at.isoformat() if company.created_at else None,

            "owner": {
                "id": company.owner.id if company.owner else None,
                "name": f"{company.owner.first_name} {company.owner.last_name}".strip() if company.owner else None,
                "email": company.owner.email if company.owner else None,
            },

            "contact": {
                "phone": company.phone,
                "email": company.email,
            },

            "address": company.short_address or company.city or "-",

            "subscription": {
                "plan": sub.plan.name if sub and sub.plan else None,
                "status": sub.status if sub else None,
                "end_date": sub.end_date.isoformat() if sub and sub.end_date else None,
            },

            "users_count": CompanyUser.objects.filter(company=company).count(),
            "devices_count": 0,
        })

    return JsonResponse(result, safe=False)