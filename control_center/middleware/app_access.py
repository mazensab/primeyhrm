# ============================================================
# 🔐 App Access Control Middleware — V3 Product-Aware
# Mham Cloud
# ============================================================
# ✔ Product-aware subscription resolution
# ✔ Keeps public/system/api routes bypassed
# ✔ App-level access via apps_snapshot / plan.apps
# ✔ Super Admin bypass
# ✔ Supports active_company_id when available
# ✔ Prepares request context for downstream middleware
# ============================================================

from __future__ import annotations

from django.http import JsonResponse

from billing_center.models import CompanySubscription
from company_manager.models import CompanyUser


# ============================================================
# 🧠 App Route Map (Single Source of Truth)
# ------------------------------------------------------------
# مفاتيح المسارات الحالية (legacy route keys)
# ============================================================
APP_ROUTE_PREFIXES = {
    "employee": "/employee/",
    "attendance": "/attendance/",
    "payroll": "/payroll/",
    "leave": "/leave/",
    "performance": "/performance/",
}


# ============================================================
# 🧩 App → Product Mapping
# ------------------------------------------------------------
# جميع هذه التطبيقات الآن تقع تحت منتج HR
# ويمكن لاحقًا إضافة accounting / sales / crm ...
# ============================================================
APP_PRODUCT_CODES = {
    "employee": "HR",
    "attendance": "HR",
    "payroll": "HR",
    "leave": "HR",
    "performance": "HR",
}


# ============================================================
# 🧩 App Access Aliases
# ------------------------------------------------------------
# ندعم:
# - legacy apps_snapshot values: employee / attendance / ...
# - catalog-like values: hr_core / attendance / ...
# ============================================================
APP_ACCESS_ALIASES = {
    "employee": {"employee", "hr_core"},
    "attendance": {"attendance"},
    "payroll": {"payroll"},
    "leave": {"leave"},
    "performance": {"performance"},
}


# ============================================================
# 🔐 Middleware
# ============================================================
class AppAccessMiddleware:
    """
    🔒 Enforces app/module access based on product subscription
    and apps_snapshot / plan.apps

    Responsibilities:
    - Detect requested app from route
    - Resolve required product
    - Resolve company context
    - Resolve active subscription for required product
    - Enforce app visibility
    - Expose request context for downstream middleware

    Notes:
    - This middleware does NOT enforce lifecycle write blocking;
      that remains the responsibility of SubscriptionEnforcementMiddleware.
    - This middleware is mainly for app/module access control.
    """

    BYPASS_PREFIXES = (
        "/admin/",
        "/api/",
        "/system/",
        "/auth/",
        "/static/",
        "/media/",
        "/ws/",
        "/_next/",
        "/favicon.ico",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    # --------------------------------------------------------
    # Main Entry
    # --------------------------------------------------------
    def __call__(self, request):
        path = request.path

        # ----------------------------------------------------
        # 0) Initialize request context
        # ----------------------------------------------------
        request.required_app = None
        request.required_product_code = None
        request.company_context = None
        request.company_user_context = None
        request.resolved_subscription = None

        # ----------------------------------------------------
        # 1) Bypass system & public routes
        # ----------------------------------------------------
        if path.startswith(self.BYPASS_PREFIXES):
            return self.get_response(request)

        # ----------------------------------------------------
        # 2) Detect app route early
        # ----------------------------------------------------
        requested_app = self._resolve_app_from_path(path)

        # Not an app route → allow
        if not requested_app:
            return self.get_response(request)

        request.required_app = requested_app
        request.required_product_code = APP_PRODUCT_CODES.get(requested_app)

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
        # 5) Resolve company context
        # ----------------------------------------------------
        company_user = self._resolve_company_user(request)

        if not company_user or not company_user.company:
            return JsonResponse(
                {
                    "detail": "COMPANY_CONTEXT_NOT_FOUND",
                    "app": requested_app,
                    "product": request.required_product_code,
                },
                status=403,
            )

        company = company_user.company
        request.company_context = company
        request.company_user_context = company_user

        # ----------------------------------------------------
        # 6) Resolve subscription for required product
        # ----------------------------------------------------
        subscription = self._resolve_subscription_for_app(
            company=company,
            requested_app=requested_app,
            required_product_code=request.required_product_code,
        )

        if not subscription:
            return JsonResponse(
                {
                    "detail": "NO_PRODUCT_SUBSCRIPTION",
                    "app": requested_app,
                    "product": request.required_product_code,
                    "company_id": company.id,
                },
                status=403,
            )

        request.resolved_subscription = subscription

        # ----------------------------------------------------
        # 7) App access enforcement
        # ----------------------------------------------------
        if not self._is_app_allowed(
            requested_app=requested_app,
            subscription=subscription,
        ):
            resolved_product = getattr(subscription, "resolved_product", None)

            return JsonResponse(
                {
                    "detail": "APP_NOT_ALLOWED",
                    "app": requested_app,
                    "product": getattr(resolved_product, "code", None),
                    "subscription_id": subscription.id,
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

    # --------------------------------------------------------
    # 🏢 Resolve CompanyUser safely
    # --------------------------------------------------------
    def _resolve_company_user(self, request):
        active_company_id = request.session.get("active_company_id")

        base_qs = (
            CompanyUser.objects
            .select_related("company")
            .filter(user=request.user)
        )

        # لو عندنا active company في الجلسة نفضله
        if active_company_id:
            preferred = base_qs.filter(company_id=active_company_id).order_by("-id").first()
            if preferred:
                return preferred

        # fallback آمن
        return base_qs.order_by("-id").first()

    # --------------------------------------------------------
    # 📦 Resolve active subscription for requested product
    # --------------------------------------------------------
    def _resolve_subscription_for_app(self, *, company, requested_app: str, required_product_code: str | None):
        qs = (
            CompanySubscription.objects
            .select_related("product", "plan")
            .filter(company=company)
        )

        if required_product_code:
            qs = qs.filter(product__code=required_product_code)

        # نفضل ACTIVE أولًا
        active_sub = (
            qs.filter(status="ACTIVE")
            .order_by("-end_date", "-created_at", "-id")
            .first()
        )
        if active_sub:
            return active_sub

        # fallback أخير: آخر اشتراك لنفس المنتج فقط
        # نحتفظ به مرحليًا حتى لا نكسر القراءة/العرض القديمة
        return qs.order_by("-end_date", "-created_at", "-id").first()

    # --------------------------------------------------------
    # ✅ App access check
    # --------------------------------------------------------
    def _is_app_allowed(self, *, requested_app: str, subscription: CompanySubscription) -> bool:
        """
        يقرأ apps_snapshot أولًا، ثم fallback إلى plan.apps
        ويدعم legacy keys + catalog-like keys
        """
        raw_allowed_apps = []

        if subscription.apps_snapshot:
            raw_allowed_apps = subscription.apps_snapshot
        elif subscription.plan and getattr(subscription.plan, "apps", None):
            raw_allowed_apps = subscription.plan.apps

        if not isinstance(raw_allowed_apps, list):
            raw_allowed_apps = []

        normalized_allowed = {
            str(app).strip().lower()
            for app in raw_allowed_apps
            if str(app).strip()
        }

        accepted_aliases = APP_ACCESS_ALIASES.get(
            requested_app,
            {requested_app},
        )

        return any(alias in normalized_allowed for alias in accepted_aliases)