# ============================================================
# 📦 Subscription Limits Service — Product-Aware
# Mham Cloud | Primey HR Cloud
# ============================================================
# ✔ Product-aware subscription resolution
# ✔ Unified usage calculation
# ✔ Unified limit access
# ✔ Employee / Branch enforcement helpers
# ✔ Safe fallbacks
# ✔ Read-only helpers (no DB writes)
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from billing_center.models import CompanySubscription
from company_manager.models import CompanyBranch
from employee_center.models import Employee


# ============================================================
# 🧩 Constants
# ============================================================

PRODUCT_HR = "HR"

LIMIT_EMPLOYEES = "max_employees"
LIMIT_BRANCHES = "max_branches"


# ============================================================
# 🧱 Data Objects
# ============================================================

@dataclass(slots=True)
class LimitCheckResult:
    allowed: bool
    code: str
    message: str
    product_code: str | None
    limit_key: str
    current_usage: int
    max_allowed: int | None
    remaining: int | None
    subscription_id: int | None
    company_id: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "code": self.code,
            "message": self.message,
            "product_code": self.product_code,
            "limit_key": self.limit_key,
            "current_usage": self.current_usage,
            "max_allowed": self.max_allowed,
            "remaining": self.remaining,
            "subscription_id": self.subscription_id,
            "company_id": self.company_id,
        }


# ============================================================
# 🧩 Product Mapping
# ------------------------------------------------------------
# المرحلة الحالية:
# الموظفين والفروع ضمن منتج HR
# ويمكن لاحقًا توسيعها لمنتجات أخرى
# ============================================================

def get_product_code_for_employees() -> str:
    return PRODUCT_HR


def get_product_code_for_branches() -> str:
    return PRODUCT_HR


# ============================================================
# 🔎 Subscription Resolution
# ============================================================

def get_active_product_subscription(company, product_code: str) -> CompanySubscription | None:
    """
    جلب الاشتراك النشط الخاص بمنتج معين للشركة.
    """

    if not company or not getattr(company, "id", None):
        return None

    if not product_code:
        return None

    return (
        CompanySubscription.objects
        .select_related("product", "plan")
        .filter(
            company=company,
            product__code=product_code,
            status="ACTIVE",
        )
        .order_by("-end_date", "-created_at", "-id")
        .first()
    )


# ============================================================
# 📏 Limit Readers
# ============================================================

def _normalize_limit_value(value) -> int | None:
    """
    تحويل الحد إلى int أو None.
    None تعني: غير محدد / لا يوجد ضبط.
    0 تبقى 0 وتعني المنع الكامل.
    """

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_subscription_limit(subscription: CompanySubscription | None, limit_key: str) -> int | None:
    """
    يقرأ limit من plan مباشرة.
    """

    if not subscription or not subscription.plan:
        return None

    raw_value = getattr(subscription.plan, limit_key, None)
    return _normalize_limit_value(raw_value)


# ============================================================
# 📊 Usage Calculators
# ============================================================

def get_employees_usage(company) -> int:
    if not company or not getattr(company, "id", None):
        return 0

    return (
        Employee.objects
        .filter(company=company)
        .count()
    )


def get_branches_usage(company) -> int:
    if not company or not getattr(company, "id", None):
        return 0

    return (
        CompanyBranch.objects
        .filter(company=company)
        .count()
    )


def get_usage_value(company, limit_key: str) -> int:
    if limit_key == LIMIT_EMPLOYEES:
        return get_employees_usage(company)

    if limit_key == LIMIT_BRANCHES:
        return get_branches_usage(company)

    return 0


# ============================================================
# 🧠 Core Check Engine
# ============================================================

def check_company_limit(
    *,
    company,
    product_code: str,
    limit_key: str,
) -> LimitCheckResult:
    """
    فحص موحد لأي limit على مستوى الشركة + المنتج.
    """

    company_id = getattr(company, "id", None) if company else None
    subscription = get_active_product_subscription(company, product_code)
    current_usage = get_usage_value(company, limit_key)

    if not company_id:
        return LimitCheckResult(
            allowed=False,
            code="NO_COMPANY",
            message="Company context missing.",
            product_code=product_code,
            limit_key=limit_key,
            current_usage=current_usage,
            max_allowed=None,
            remaining=None,
            subscription_id=None,
            company_id=None,
        )

    if not subscription:
        return LimitCheckResult(
            allowed=False,
            code="NO_PRODUCT_SUBSCRIPTION",
            message="No active subscription found for the required product.",
            product_code=product_code,
            limit_key=limit_key,
            current_usage=current_usage,
            max_allowed=None,
            remaining=None,
            subscription_id=None,
            company_id=company_id,
        )

    max_allowed = get_subscription_limit(subscription, limit_key)

    # --------------------------------------------------------
    # إذا لا يوجد limit مضبوط نعتبره غير مقيّد حاليًا
    # --------------------------------------------------------
    if max_allowed is None:
        return LimitCheckResult(
            allowed=True,
            code="LIMIT_NOT_DEFINED",
            message="No explicit limit configured for this item.",
            product_code=product_code,
            limit_key=limit_key,
            current_usage=current_usage,
            max_allowed=None,
            remaining=None,
            subscription_id=subscription.id,
            company_id=company_id,
        )

    remaining = max_allowed - current_usage

    if current_usage >= max_allowed:
        return LimitCheckResult(
            allowed=False,
            code="LIMIT_EXCEEDED",
            message="Subscription limit exceeded.",
            product_code=product_code,
            limit_key=limit_key,
            current_usage=current_usage,
            max_allowed=max_allowed,
            remaining=max(remaining, 0),
            subscription_id=subscription.id,
            company_id=company_id,
        )

    return LimitCheckResult(
        allowed=True,
        code="OK",
        message="Within allowed subscription limit.",
        product_code=product_code,
        limit_key=limit_key,
        current_usage=current_usage,
        max_allowed=max_allowed,
        remaining=remaining,
        subscription_id=subscription.id,
        company_id=company_id,
    )


# ============================================================
# 👥 Employee Limit Helpers
# ============================================================

def check_employee_creation_limit(company) -> LimitCheckResult:
    return check_company_limit(
        company=company,
        product_code=get_product_code_for_employees(),
        limit_key=LIMIT_EMPLOYEES,
    )


def can_create_employee(company) -> bool:
    return check_employee_creation_limit(company).allowed


# ============================================================
# 🏢 Branch Limit Helpers
# ============================================================

def check_branch_creation_limit(company) -> LimitCheckResult:
    return check_company_limit(
        company=company,
        product_code=get_product_code_for_branches(),
        limit_key=LIMIT_BRANCHES,
    )


def can_create_branch(company) -> bool:
    return check_branch_creation_limit(company).allowed


# ============================================================
# 📊 Subscription Usage Snapshot
# ============================================================

def build_subscription_usage_snapshot(subscription: CompanySubscription | None) -> dict[str, Any]:
    """
    Snapshot موحد للاستخدام والحدود لواجهة التفاصيل.
    """

    if not subscription:
        return {
            "employees": 0,
            "max_employees": None,
            "branches": 0,
            "max_branches": None,
            "devices": 0,
            "max_devices": None,
        }

    company = subscription.company

    employees_usage = get_employees_usage(company)
    branches_usage = get_branches_usage(company)

    return {
        "employees": employees_usage,
        "max_employees": get_subscription_limit(subscription, LIMIT_EMPLOYEES),
        "branches": branches_usage,
        "max_branches": get_subscription_limit(subscription, LIMIT_BRANCHES),
        "devices": 0,
        "max_devices": None,
    }