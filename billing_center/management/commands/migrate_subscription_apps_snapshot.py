# ===============================================================
# 🔁 Migration Tool — Apps Snapshot for Legacy Subscriptions
# Mham Cloud | Billing Center
# ===============================================================
# ✔ One-off manual command
# ✔ Idempotent & Safe
# ✔ ACTIVE subscriptions only
# ✔ Never overwrites existing snapshots
# ===============================================================

from django.core.management.base import BaseCommand
from django.db import transaction

from billing_center.models import CompanySubscription


class Command(BaseCommand):
    help = "Migrate apps_snapshot for legacy ACTIVE subscriptions"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.NOTICE("🔍 Scanning legacy subscriptions...")
        )

        subscriptions = CompanySubscription.objects.select_related("plan").filter(
            status="ACTIVE"
        )

        updated = 0
        skipped = 0

        for sub in subscriptions:
            # --------------------------------------------------
            # 🛑 Skip if snapshot already exists
            # --------------------------------------------------
            if sub.apps_snapshot:
                skipped += 1
                continue

            # --------------------------------------------------
            # 🛑 Skip if no plan
            # --------------------------------------------------
            if not sub.plan:
                skipped += 1
                continue

            plan_apps = sub.plan.apps or []

            # Defensive
            if not isinstance(plan_apps, list):
                plan_apps = []

            # --------------------------------------------------
            # ✅ Write snapshot (ONCE)
            # --------------------------------------------------
            try:
                with transaction.atomic():
                    sub.apps_snapshot = plan_apps
                    sub.save(update_fields=["apps_snapshot"])
                    updated += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✔ Subscription #{sub.id} → snapshot set: {plan_apps}"
                        )
                    )

            except Exception as e:
                self.stderr.write(
                    f"❌ Failed to update subscription #{sub.id}: {e}"
                )

        # ------------------------------------------------------
        # Summary
        # ------------------------------------------------------
        self.stdout.write("\n" + "-" * 50)
        self.stdout.write(
            self.style.SUCCESS(f"✅ Updated: {updated}")
        )
        self.stdout.write(
            self.style.WARNING(f"⏭ Skipped: {skipped}")
        )
        self.stdout.write("-" * 50)
