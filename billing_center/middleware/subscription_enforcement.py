from __future__ import annotations

from django.http import JsonResponse
from django.utils.timezone import now

from billing_center.models import CompanySubscription
from company_manager.models import CompanyUser


class SubscriptionEnforcementMiddleware:
    """
    ============================================================
    🔐 Subscription Enforcement Middleware — HARD ENFORCEMENT
    Mham Cloud | V4.0 PRODUCT-AWARE
    ============================================================

    Responsibilities:
    - WRITE enforcement only
    - Product-aware subscription resolution
    - Works with or without AppAccessMiddleware context
    - Super Admin bypass
    - Company.is_active = False => read-only hard stop

    Notes:
    - READ requests are always allowed
    - System/Auth/Billing safe routes are bypassed
    - If AppAccessMiddleware already resolved company/product/subscription,
      we reuse that context instead of re-querying from scratch
    """

    # ============================================================
    # 🟢 PATHS NEVER ENFORCED (ABSOLUTE SAFE)
    # ============================================================
    SAFE_PATH_PREFIXES = (
        "/admin/",
        "/api/auth/",
        "/api/system/",      # System APIs
        "/api/billing/",
        "/api/dashboard/",
        "/static/",
        "/media/",
    )

    WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")

    # ============================================================
    # 🧩 Product Route Mapping
    # ------------------------------------------------------------
    # المرحلة الحالية:
    # كل موديولات الشركة التشغيلية تقع تحت منتج HR
    # ويمكن لاحقًا إضافة ACCOUNTING / SALES / CRM ...
    # ============================================================
    PRODUCT_ROUTE_PREFIXES = {
        "HR": (
            # Frontend app routes
            "/employee/",
            "/attendance/",
            "/payroll/",
            "/leave/",
            "/performance/",

            # Company API routes
            "/api/company/employees/",
            "/api/company/employee/",
            "/api/company/contracts/",
            "/api/company/departments/",
            "/api/company/job-titles/",
            "/api/company/attendance/",
            "/api/company/payroll/",
            "/api/company/leaves/",
            "/api/company/leave/",
            "/api/company/performance/",
            "/api/company/biotime/",
            "/api/company/analytics/",
            "/api/company/notifications/",
            "/api/company/documents/",
        ),
    }

    # ------------------------------------------------------------
    def __init__(self, get_response):
        self.get_response = get_response

    # ------------------------------------------------------------
    def __call__(self, request):
        path = request.path
        method = request.method

        # ========================================================
        # 🟢 ABSOLUTE BYPASS — SAFE PATHS
        # ========================================================
        for prefix in self.SAFE_PATH_PREFIXES:
            if path.startswith(prefix):
                return self.get_response(request)

        # ========================================================
        # 🟢 Anonymous users (Auth layer decides)
        # ========================================================
        if not request.user.is_authenticated:
            return self.get_response(request)

        # ========================================================
        # 🟢 Super Admin — ABSOLUTE BYPASS
        # ========================================================
        if request.user.is_superuser:
            return self.get_response(request)

        # ========================================================
        # 🟢 READ requests are ALWAYS allowed
        # ========================================================
        if method not in self.WRITE_METHODS:
            return self.get_response(request)

        # ========================================================
        # 🏢 Resolve company context
        # --------------------------------------------------------
        # Prefer upstream middleware context if already available
        # ========================================================
        company = getattr(request, "company_context", None)
        company_user = getattr(request, "company_user_context", None)

        if not company:
            company_user = self._resolve_company_user(request)
            company = getattr(company_user, "company", None) if company_user else None

        if not company:
            return self._block(
                code="NO_COMPANY",
                message="المستخدم غير مرتبط بأي شركة",
            )

        # ========================================================
        # ⛔ HARD STOP — COMPANY SUSPENDED
        # ========================================================
        if not company.is_active:
            return self._block(
                code="COMPANY_SUSPENDED",
                message="تم إيقاف الشركة — النظام في وضع القراءة فقط",
                extra={
                    "company_id": company.id,
                },
            )

        # ========================================================
        # 🧩 Resolve required product
        # --------------------------------------------------------
        # Prefer upstream middleware context if available
        # Fallback: detect from current path
        # ========================================================
        required_product_code = getattr(request, "required_product_code", None)
        if not required_product_code:
            required_product_code = self._resolve_required_product_code_from_path(path)

        # ========================================================
        # 📦 Resolve subscription
        # --------------------------------------------------------
        # Prefer upstream middleware resolved_subscription if valid
        # Otherwise resolve it here product-aware
        # ========================================================
        subscription = getattr(request, "resolved_subscription", None)

        if not self._is_subscription_context_valid(
            subscription=subscription,
            company=company,
            required_product_code=required_product_code,
        ):
            subscription = self._resolve_subscription(
                company=company,
                required_product_code=required_product_code,
            )

        if not subscription:
            return self._block(
                code="NO_PRODUCT_SUBSCRIPTION" if required_product_code else "NO_SUBSCRIPTION",
                message="لا يوجد اشتراك صالح لهذا المنتج" if required_product_code else "لا يوجد اشتراك صالح لهذه الشركة",
                extra={
                    "company_id": company.id,
                    "product": required_product_code,
                } if required_product_code else {
                    "company_id": company.id,
                },
            )

        # Keep request context updated for downstream code
        request.company_context = company
        request.company_user_context = company_user
        request.required_product_code = required_product_code
        request.resolved_subscription = subscription

        # ========================================================
        # ⛔ SUBSCRIPTION ENFORCEMENT — WRITE ONLY
        # ========================================================
        if subscription.status == "SUSPENDED":
            return self._block(
                code="SUBSCRIPTION_SUSPENDED",
                message="تم إيقاف الاشتراك مؤقتًا",
                extra={
                    "subscription_id": subscription.id,
                    "product": getattr(getattr(subscription, "resolved_product", None), "code", None),
                },
            )

        if subscription.status == "PENDING":
            return self._block(
                code="SUBSCRIPTION_NOT_ACTIVE",
                message="الاشتراك لم يُفعّل بعد",
                extra={
                    "subscription_id": subscription.id,
                    "product": getattr(getattr(subscription, "resolved_product", None), "code", None),
                },
            )

        if (
            subscription.status == "EXPIRED"
            or (
                subscription.end_date
                and subscription.end_date < now().date()
            )
        ):
            return self._block(
                code="SUBSCRIPTION_EXPIRED",
                message="انتهى الاشتراك — النظام في وضع القراءة فقط",
                extra={
                    "subscription_id": subscription.id,
                    "expired_at": subscription.end_date,
                    "product": getattr(getattr(subscription, "resolved_product", None), "code", None),
                },
            )

        # ========================================================
        # ✅ ACTIVE — allow WRITE request
        # ========================================================
        return self.get_response(request)

    # ------------------------------------------------------------
    # 🏢 Resolve CompanyUser safely
    # ------------------------------------------------------------
    def _resolve_company_user(self, request):
        active_company_id = request.session.get("active_company_id")

        qs = (
            CompanyUser.objects
            .filter(user=request.user)
            .select_related("company")
        )

        if active_company_id:
            preferred = qs.filter(company_id=active_company_id).order_by("-id").first()
            if preferred:
                return preferred

        return qs.order_by("-id").first()

    # ------------------------------------------------------------
    # 🧩 Detect product from current path
    # ------------------------------------------------------------
    def _resolve_required_product_code_from_path(self, path: str):
        for product_code, prefixes in self.PRODUCT_ROUTE_PREFIXES.items():
            for prefix in prefixes:
                if path.startswith(prefix):
                    return product_code
        return None

    # ------------------------------------------------------------
    # 📦 Resolve subscription for company + product
    # ------------------------------------------------------------
    def _resolve_subscription(self, *, company, required_product_code: str | None):
        qs = (
            CompanySubscription.objects
            .select_related("product", "plan")
            .filter(company=company)
        )

        if required_product_code:
            qs = qs.filter(product__code=required_product_code)

        # Prefer ACTIVE first
        active_sub = (
            qs.filter(status="ACTIVE")
            .order_by("-end_date", "-created_at", "-id")
            .first()
        )
        if active_sub:
            return active_sub

        # Fallback to latest subscription for same product only
        return qs.order_by("-end_date", "-created_at", "-id").first()

    # ------------------------------------------------------------
    # ✅ Validate upstream subscription context
    # ------------------------------------------------------------
    def _is_subscription_context_valid(self, *, subscription, company, required_product_code):
        if not subscription:
            return False

        if getattr(subscription, "company_id", None) != getattr(company, "id", None):
            return False

        if not required_product_code:
            return True

        resolved_product = getattr(subscription, "resolved_product", None)
        resolved_code = getattr(resolved_product, "code", None)

        return resolved_code == required_product_code

    # ------------------------------------------------------------
    def _block(self, code, message, extra=None):
        payload = {
            "blocked": True,
            "code": code,
            "message": message,
            "mode": "read_only",
        }

        if extra:
            payload.update(extra)

        return JsonResponse(payload, status=402)