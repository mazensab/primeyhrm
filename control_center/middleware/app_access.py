# ============================================================
# 🔐 App Access Control Middleware — V2 Ultra Safe
# Primey HR Cloud
# ============================================================

from django.http import JsonResponse

from billing_center.models import CompanySubscription
from company_manager.models import CompanyUser


# ============================================================
# 🧠 App Route Map (Single Source of Truth)
# ============================================================
APP_ROUTE_PREFIXES = {
    "employee": "/employee/",
    "attendance": "/attendance/",
    "payroll": "/payroll/",
    "leave": "/leave/",
    "performance": "/performance/",
}


# ============================================================
# 🔐 Middleware
# ============================================================
class AppAccessMiddleware:
    """
    🔒 Enforces app/module access based on subscription.apps_snapshot
    - Super Admin: bypass
    - System/API/Public routes: bypass
    - No subscription: block only on real app routes
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # ----------------------------------------------------
        # 1) Bypass system & public routes
        # ----------------------------------------------------
        if path.startswith((
            "/admin/",
            "/api/",
            "/system/",
            "/auth/",
            "/static/",
            "/media/",
            "/ws/",
            "/_next/",
            "/favicon.ico",
        )):
            return self.get_response(request)

        # ----------------------------------------------------
        # 2) Detect app route early
        # ----------------------------------------------------
        requested_app = self._resolve_app_from_path(path)

        # Not an app route → allow
        if not requested_app:
            return self.get_response(request)

        # ----------------------------------------------------
        # 3) Not authenticated
        # ----------------------------------------------------
        if not request.user.is_authenticated:
            return self.get_response(request)

        # ----------------------------------------------------
        # 4) Super Admin bypass
        # ----------------------------------------------------
        if request.user.is_superuser:
            return self.get_response(request)

        # ----------------------------------------------------
        # 5) Resolve company user
        # ----------------------------------------------------
        try:
            company_user = (
                CompanyUser.objects
                .select_related("company")
                .get(user=request.user)
            )
        except CompanyUser.DoesNotExist:
            return JsonResponse(
                {"detail": "Company context not found"},
                status=403,
            )

        company = company_user.company

        # ----------------------------------------------------
        # 6) Resolve active subscription safely
        # ----------------------------------------------------
        subscription = (
            CompanySubscription.objects
            .filter(company=company, status="ACTIVE")
            .order_by("-id")
            .first()
        )

        if not subscription:
            subscription = (
                CompanySubscription.objects
                .filter(company=company, is_active=True)
                .order_by("-id")
                .first()
            )

        if not subscription:
            subscription = (
                CompanySubscription.objects
                .filter(company=company)
                .order_by("-id")
                .first()
            )

        if not subscription:
            return JsonResponse(
                {"detail": "No active subscription"},
                status=403,
            )

        # ----------------------------------------------------
        # 7) App access enforcement
        # ----------------------------------------------------
        allowed_apps = subscription.apps_snapshot or []

        allowed_apps = [
            str(app).strip().lower()
            for app in allowed_apps
            if str(app).strip()
        ]

        if requested_app not in allowed_apps:
            return JsonResponse(
                {
                    "detail": "APP_NOT_ALLOWED",
                    "app": requested_app,
                },
                status=403,
            )

        return self.get_response(request)

    # --------------------------------------------------------
    # 🔎 Detect app from URL
    # --------------------------------------------------------
    def _resolve_app_from_path(self, path: str):
        for app_key, prefix in APP_ROUTE_PREFIXES.items():
            if path.startswith(prefix):
                return app_key
        return None