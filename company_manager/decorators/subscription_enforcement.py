# =============================================================================
# 🔐 Subscription Enforcement Engine
# Mham Cloud — Policy Layer
# -----------------------------------------------------------------------------
# هذا الملف يحتوي على المنطق العام لفرض قيود الباقات (Plans → Limits)
# - لا يحتوي على أي منطق HTTP
# - لا يحتوي على Redirects أو UI
# - يُستخدم كـ Decorator فقط
# -----------------------------------------------------------------------------
# أي تعديل هنا يجب أن يكون مدروسًا لأنه يؤثر على النظام كاملًا
# =============================================================================

from functools import wraps
from django.utils.timezone import now

from billing_center.models import CompanySubscription


# =============================================================================
# ❗ Business Exceptions (Internal Only)
# =============================================================================

class SubscriptionInactiveError(Exception):
    """يُرفع عند عدم وجود اشتراك نشط"""
    pass


class PlanLimitReachedError(Exception):
    """يُرفع عند تجاوز حد الباقة"""
    pass


class PlanMisconfigurationError(Exception):
    """يُرفع عند وجود limit_type غير معروف أو إعداد خاطئ"""
    pass


# =============================================================================
# 🧠 Resolver Base
# =============================================================================

class BaseLimitResolver:
    """
    Resolver أساسي
    كل Resolver فرعي يجب أن يعيد عددًا صحيحًا فقط
    """
    @staticmethod
    def count(company) -> int:
        raise NotImplementedError


# =============================================================================
# 🧩 Concrete Resolvers
# =============================================================================

class EmployeesResolver(BaseLimitResolver):
    @staticmethod
    def count(company) -> int:
        from employee_center.models import Employee
        return Employee.objects.filter(
            company=company,
            status="active",
        ).count()


class BranchesResolver(BaseLimitResolver):
    @staticmethod
    def count(company) -> int:
        from company_manager.models import Branch
        return Branch.objects.filter(
            company=company,
            is_active=True,
        ).count()


class UsersResolver(BaseLimitResolver):
    @staticmethod
    def count(company) -> int:
        from company_manager.models import CompanyUser
        return CompanyUser.objects.filter(
            company=company,
            is_active=True,
        ).count()


# =============================================================================
# 🗺️ Resolver Registry (Single Source of Truth)
# =============================================================================

RESOLVERS = {
    "employees": EmployeesResolver,
    "branches": BranchesResolver,
    "users": UsersResolver,
}


# =============================================================================
# 🔍 Helpers
# =============================================================================

def _get_active_subscription(company) -> CompanySubscription:
    """
    يعيد الاشتراك النشط الحالي للشركة
    """
    subscription = CompanySubscription.objects.select_related("plan").filter(
        company=company,
        status="ACTIVE",
        start_date__lte=now().date(),
    ).first()

    if not subscription:
        raise SubscriptionInactiveError("No active subscription found")

    return subscription


def _get_plan_limit(plan, limit_type: str):
    """
    يرجع:
    - None → Unlimited
    - int  → Limit
    """
    field_name = f"max_{limit_type}"

    if not hasattr(plan, field_name):
        raise PlanMisconfigurationError(
            f"Unknown plan limit field: {field_name}"
        )

    value = getattr(plan, field_name)

    # None أو 0 = غير محدود
    if value in (None, 0):
        return None

    return int(value)


def _get_resolver(limit_type: str) -> BaseLimitResolver:
    resolver_cls = RESOLVERS.get(limit_type)
    if not resolver_cls:
        raise PlanMisconfigurationError(
            f"No resolver registered for limit type: {limit_type}"
        )
    return resolver_cls


# =============================================================================
# 🛡️ Decorator Factory
# =============================================================================

def enforce_plan_limit(limit_type: str):
    """
    Decorator عام لفرض قيود الباقات

    مثال:
        @enforce_plan_limit("employees")
        @enforce_plan_limit("branches")
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            company = getattr(request, "company", None)
            if not company:
                raise PlanMisconfigurationError(
                    "request.company is missing (ensure CompanyMiddleware is applied)"
                )

            # 1) الاشتراك النشط
            subscription = _get_active_subscription(company)
            plan = subscription.plan

            # 2) حد الباقة
            plan_limit = _get_plan_limit(plan, limit_type)

            # Unlimited → مرّر
            if plan_limit is None:
                return view_func(request, *args, **kwargs)

            # 3) العد الحالي
            resolver = _get_resolver(limit_type)
            current_count = resolver.count(company)

            # 4) المقارنة
            if current_count >= plan_limit:
                raise PlanLimitReachedError(
                    f"Plan limit reached for '{limit_type}' "
                    f"({current_count}/{plan_limit})"
                )

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
