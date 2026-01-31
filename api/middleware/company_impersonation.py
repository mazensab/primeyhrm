from company_manager.models import CompanyUser

class CompanyImpersonationMiddleware:
    """
    ============================================================
    🧠 Company Impersonation Resolver
    ============================================================
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        company_id = request.session.get("impersonated_company_id")

        if company_id and request.user.is_authenticated:
            try:
                company_user = CompanyUser.objects.select_related(
                    "user", "company"
                ).get(
                    user=request.user,
                    company_id=company_id,
                    is_active=True,
                )

                # ✅ THE KEY LINE
                request.company_user = company_user

            except CompanyUser.DoesNotExist:
                request.company_user = None

        return self.get_response(request)
