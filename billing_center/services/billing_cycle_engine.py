# ============================================================
# 🔁 Billing Cycle Engine — S3-A
# Mham Cloud | Ultra Stable V2
# ============================================================
# ✔ Decision Engine Only
# ✔ No DB Writes
# ✔ No Invoice Creation
# ✔ No State Changes
# ✔ Safe & Idempotent
# ✔ Richer normalized output
# ============================================================

from __future__ import annotations

from datetime import date
from typing import Dict, List

from django.conf import settings
from django.utils.timezone import now

from billing_center.models import CompanySubscription


# ============================================================
# Decisions Enum (String-based for flexibility)
# ============================================================
DECISION_NO_ACTION = "NO_ACTION"
DECISION_READY_FOR_RENEW = "READY_FOR_RENEW"
DECISION_EXPIRED_CANDIDATE = "EXPIRED_CANDIDATE"
DECISION_SKIPPED_MANUAL = "SKIPPED_MANUAL"


class BillingCycleEngine:
    """
    ============================================================
    Billing Cycle Engine (S3-A)
    ------------------------------------------------------------
    Evaluates subscriptions and decides:
    - Needs renewal
    - Near expiry
    - Expired candidate
    ------------------------------------------------------------
    ❌ Does NOT:
      - Create invoices
      - Update subscription status
      - Trigger payments
    ============================================================
    """

    def __init__(self, reference_date: date | None = None):
        self.today = reference_date or now().date()
        self.renew_window_days = int(
            getattr(
                settings,
                "BILLING_RENEW_WINDOW_DAYS",
                5,
            )
            or 5
        )

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------
    def evaluate(self) -> List[Dict]:
        """
        Evaluate all relevant subscriptions and return decisions.
        """
        results: List[Dict] = []

        subscriptions = CompanySubscription.objects.select_related(
            "company",
            "plan",
        ).filter(
            status="ACTIVE"
        )

        for subscription in subscriptions:
            decision_data = self._evaluate_subscription(subscription)
            if decision_data:
                results.append(decision_data)

        return results

    # --------------------------------------------------------
    # Core Logic
    # --------------------------------------------------------
    def _evaluate_subscription(
        self,
        subscription: CompanySubscription,
    ) -> Dict | None:
        """
        Evaluate a single subscription and return decision dict.
        """

        # 1️⃣ No end date → manual lifecycle
        if not subscription.end_date:
            return self._build_result(
                subscription,
                decision=DECISION_SKIPPED_MANUAL,
                days_remaining=None,
            )

        # 2️⃣ Auto-renew disabled
        if not subscription.auto_renew:
            return self._build_result(
                subscription,
                decision=DECISION_NO_ACTION,
                days_remaining=self._days_remaining(subscription.end_date),
            )

        # 3️⃣ Auto-renew enabled
        days_remaining = self._days_remaining(subscription.end_date)

        # Expired
        if days_remaining < 0:
            return self._build_result(
                subscription,
                decision=DECISION_EXPIRED_CANDIDATE,
                days_remaining=days_remaining,
            )

        # Near expiry → ready for renew
        if days_remaining <= self.renew_window_days:
            return self._build_result(
                subscription,
                decision=DECISION_READY_FOR_RENEW,
                days_remaining=days_remaining,
            )

        # Default → no action
        return self._build_result(
            subscription,
            decision=DECISION_NO_ACTION,
            days_remaining=days_remaining,
        )

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------
    def _days_remaining(self, end_date: date) -> int:
        return (end_date - self.today).days

    def _build_result(
        self,
        subscription: CompanySubscription,
        decision: str,
        days_remaining: int | None,
    ) -> Dict:
        """
        Build normalized decision output.
        """
        company = subscription.company
        plan = getattr(subscription, "plan", None)

        return {
            "subscription_id": subscription.id,
            "company_id": subscription.company_id,
            "company_name": getattr(company, "name", ""),
            "plan_id": getattr(plan, "id", None) if plan else None,
            "plan_name": getattr(plan, "name", "") if plan else "",
            "status": subscription.status,
            "auto_renew": subscription.auto_renew,
            "start_date": subscription.start_date,
            "end_date": subscription.end_date,
            "days_remaining": days_remaining,
            "renew_window_days": self.renew_window_days,
            "reference_date": self.today,
            "decision": decision,
        }