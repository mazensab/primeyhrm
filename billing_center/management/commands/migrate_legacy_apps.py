# ======================================================
# 🔄 Migrate Legacy Plans & Subscriptions Apps
# Mham Cloud
# ======================================================

from django.core.management.base import BaseCommand
from billing_center.models import SubscriptionPlan, CompanySubscription


DEFAULT_APPS = [
    "employee",
    "attendance",
    "leave",
    "payroll",
    "performance",
]


class Command(BaseCommand):
    help = "Migrate legacy plans and active subscriptions with empty apps/apps_snapshot"

    def handle(self, *args, **options):
        self.stdout.write("🔍 Scanning legacy subscription plans...")

        plans_updated = 0
        subs_updated = 0

        # --------------------------------------------------
        # 1️⃣ Update legacy plans (apps == [])
        # --------------------------------------------------
        legacy_plans = SubscriptionPlan.objects.filter(apps=[])

        for plan in legacy_plans:
            plan.apps = DEFAULT_APPS
            plan.save(update_fields=["apps"])
            plans_updated += 1
            self.stdout.write(
                f"✔ Plan #{plan.id} ({plan.name}) → apps set"
            )

        # --------------------------------------------------
        # 2️⃣ Update active subscriptions (apps_snapshot == [])
        # --------------------------------------------------
        self.stdout.write("\n🔍 Scanning active subscriptions...")

        active_subs = CompanySubscription.objects.filter(
            status="ACTIVE",
            apps_snapshot=[],
        ).select_related("plan")

        for sub in active_subs:
            if not sub.plan or not sub.plan.apps:
                continue

            sub.apps_snapshot = sub.plan.apps
            sub.save(update_fields=["apps_snapshot"])
            subs_updated += 1

            self.stdout.write(
                f"✔ Subscription #{sub.id} (Company {sub.company_id}) → snapshot set"
            )

        # --------------------------------------------------
        # Summary
        # --------------------------------------------------
        self.stdout.write("\n" + "-" * 50)
        self.stdout.write(f"✅ Plans updated: {plans_updated}")
        self.stdout.write(f"✅ Subscriptions updated: {subs_updated}")
        self.stdout.write("-" * 50)
