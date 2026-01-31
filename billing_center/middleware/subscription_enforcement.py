from django.http import JsonResponse
from django.utils.timezone import now

from billing_center.models import CompanySubscription
from company_manager.models import CompanyUser


class SubscriptionEnforcementMiddleware:
    """
    ============================================================
    🔐 Subscription Enforcement Middleware — HARD ENFORCEMENT
    Primey HR Cloud | V3.1 ULTRA SAFE
    ============================================================

    ✔ لا يتدخل في Auth / Login / WhoAmI
    ✔ READ دائمًا مسموح
    ✔ WRITE enforcement فقط
    ✔ System / Billing / Payments معفاة 100%
    ✔ Super Admin معفى
    ✔ Company.is_active = False ⇒ Read-only HARD
    """

    # ============================================================
    # 🟢 PATHS NEVER ENFORCED (ABSOLUTE SAFE)
    # ============================================================
    SAFE_PATH_PREFIXES = (
        "/admin/",
        "/api/auth/",
        "/api/system/",      # 🔥 System APIs (Super Admin)
        "/api/billing/",
        "/api/dashboard/",
        "/static/",
        "/media/",
    )

    WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")

    # ------------------------------------------------------------
    def __init__(self, get_response):
        self.get_response = get_response

    # ------------------------------------------------------------
    def __call__(self, request):
        path = request.path
        method = request.method

        # ========================================================
        # 🟢 ABSOLUTE BYPASS — SAFE PATHS (FIRST LINE OF DEFENSE)
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
        # 🔗 Resolve Company via CompanyUser (WRITE ONLY)
        # ========================================================
        link = (
            CompanyUser.objects
            .filter(user=request.user)
            .select_related("company")
            .first()
        )

        if not link or not link.company:
            return self._block(
                code="NO_COMPANY",
                message="المستخدم غير مرتبط بأي شركة",
            )

        company = link.company

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
        # 📦 Latest Subscription (WRITE ONLY)
        # ========================================================
        subscription = (
            CompanySubscription.objects
            .filter(company=company)
            .order_by("-end_date", "-created_at")
            .first()
        )

        if not subscription:
            return self._block(
                code="NO_SUBSCRIPTION",
                message="لا يوجد اشتراك صالح لهذه الشركة",
            )

        # ========================================================
        # ⛔ SUBSCRIPTION ENFORCEMENT — WRITE ONLY
        # ========================================================
        if subscription.status == "SUSPENDED":
            return self._block(
                code="SUBSCRIPTION_SUSPENDED",
                message="تم إيقاف الاشتراك مؤقتًا",
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
                    "expired_at": subscription.end_date,
                },
            )

        # ========================================================
        # ✅ ACTIVE — allow WRITE request
        # ========================================================
        return self.get_response(request)

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
