# ============================================================
# 🧾 Auto Invoice Generator — S3-B
# Mham Cloud | Ultra Stable V2
# ============================================================
# ✔ Uses BillingCycleEngine decisions
# ✔ Creates Invoice only
# ✔ Snapshot-based
# ✔ Idempotent-safe (basic)
# ✔ No Scheduler / No Payments / No Enforcement
# ✔ Notification Ready
# ============================================================

from __future__ import annotations

from decimal import Decimal
from typing import Dict, List

from django.db import transaction
from django.utils import timezone

from billing_center.models import CompanySubscription, Invoice
from billing_center.services.billing_cycle_engine import (
    BillingCycleEngine,
    DECISION_READY_FOR_RENEW,
)
from billing_center.services.billing_notifications import notify_invoice_created


class AutoInvoiceGenerator:
    """
    ============================================================
    Auto Invoice Generator (S3-B)
    ------------------------------------------------------------
    Creates renewal invoices for subscriptions marked
    as READY_FOR_RENEW by BillingCycleEngine.
    ============================================================
    """

    def __init__(self, reference_date=None):
        self.reference_date = reference_date

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------
    def run(self) -> List[Invoice]:
        """
        Run auto invoice generation process.
        Returns list of created invoices.
        """
        engine = BillingCycleEngine(reference_date=self.reference_date)
        decisions = engine.evaluate()

        created_invoices: List[Invoice] = []

        for item in decisions:
            if item["decision"] != DECISION_READY_FOR_RENEW:
                continue

            invoice = self._create_invoice_if_needed(
                subscription_id=item["subscription_id"]
            )

            if invoice:
                created_invoices.append(invoice)

        return created_invoices

    # --------------------------------------------------------
    # Core Logic
    # --------------------------------------------------------
    @transaction.atomic
    def _create_invoice_if_needed(
        self,
        subscription_id: int,
    ) -> Invoice | None:
        """
        Create invoice for subscription if not already created.
        Basic idempotency: one pending invoice per period.
        """

        subscription = CompanySubscription.objects.select_related(
            "company",
            "plan",
        ).get(id=subscription_id)

        # Safety: subscription must still be valid
        if not subscription.plan or not subscription.end_date:
            return None

        # 🛡️ Idempotency Guard:
        # If there's already a PENDING invoice for this subscription
        # and same period → skip
        existing = Invoice.objects.filter(
            subscription=subscription,
            status="PENDING",
        ).exists()

        if existing:
            return None

        # ----------------------------------------------------
        # Amounts
        # ----------------------------------------------------
        plan = subscription.plan

        # ⚠️ Currently: Monthly price only
        total_amount = Decimal(plan.price_monthly)

        # ----------------------------------------------------
        # Snapshot
        # ----------------------------------------------------
        snapshot: Dict = {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "period": {
                "start": subscription.start_date.isoformat()
                if subscription.start_date
                else None,
                "end": subscription.end_date.isoformat()
                if subscription.end_date
                else None,
            },
            "plan": {
                "id": plan.id,
                "name": plan.name,
                "price_monthly": str(plan.price_monthly),
                "price_yearly": str(plan.price_yearly),
                "limits": {
                    "max_employees": plan.max_employees,
                    "max_branches": plan.max_branches,
                },
            },
        }

        # ----------------------------------------------------
        # Create Invoice
        # ----------------------------------------------------
        invoice = Invoice.objects.create(
            company=subscription.company,
            subscription=subscription,
            invoice_number=self._generate_invoice_number(),
            issue_date=timezone.now().date(),
            due_date=subscription.end_date,
            total_amount=total_amount,
            subtotal_amount=total_amount,
            total_after_discount=total_amount,
            subscription_snapshot=snapshot,
            status="PENDING",
        )

        # ----------------------------------------------------
        # 🔔 Notification
        # ----------------------------------------------------
        try:
            notify_invoice_created(
                company=subscription.company,
                invoice_number=invoice.invoice_number,
            )
        except Exception:
            # لا نكسر إنشاء الفاتورة بسبب الإشعار
            pass

        return invoice

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------
    def _generate_invoice_number(self) -> str:
        """
        Generate invoice number.
        Can be replaced later by a sequence service.
        """
        return f"INV-{timezone.now().strftime('%Y%m%d%H%M%S%f')}"