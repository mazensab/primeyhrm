# ============================================================
# 🔄 Subscription State Updater — S3-C
# Primey HR Cloud | Ultra Stable V1
# ============================================================
# ✔ Soft Mode (No Enforcement)
# ✔ Date-based state correction
# ✔ No Invoice / No Payment
# ✔ Safe & Idempotent
# ============================================================

from datetime import date
from typing import List, Dict

from django.db import transaction
from django.utils.timezone import now

from billing_center.models import CompanySubscription


class SubscriptionStateUpdater:
    """
    ============================================================
    Subscription State Updater (S3-C)
    ------------------------------------------------------------
    Corrects subscription status based on end_date.
    ------------------------------------------------------------
    Rules:
    - ACTIVE + end_date < today  → EXPIRED
    - Others → unchanged
    ------------------------------------------------------------
    ❌ No enforcement
    ❌ No invoice creation
    ❌ No scheduler logic
    ============================================================
    """

    def __init__(self, reference_date: date | None = None):
        self.today = reference_date or now().date()

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------
    def run(self) -> List[Dict]:
        """
        Run state update and return list of changes.
        """
        changes: List[Dict] = []

        subscriptions = CompanySubscription.objects.filter(
            status="ACTIVE",
            end_date__isnull=False,
        )

        for sub in subscriptions:
            if sub.end_date < self.today:
                change = self._expire_subscription(sub)
                if change:
                    changes.append(change)

        return changes

    # --------------------------------------------------------
    # Core Logic
    # --------------------------------------------------------
    @transaction.atomic
    def _expire_subscription(
        self, subscription: CompanySubscription
    ) -> Dict:
        """
        Expire a single subscription (idempotent).
        """

        old_status = subscription.status
        subscription.status = "EXPIRED"
        subscription.save(update_fields=["status"])

        return {
            "subscription_id": subscription.id,
            "company_id": subscription.company_id,
            "old_status": old_status,
            "new_status": "EXPIRED",
            "end_date": subscription.end_date,
        }
