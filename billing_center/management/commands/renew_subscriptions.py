# ===============================================================
# 🔁 Renew Subscriptions Scheduler Command
# Mham Cloud | Billing Center
# ===============================================================
# ✔ Renew ACTIVE subscriptions
# ✔ Auto suspend companies with EXPIRED subscriptions
# ✔ Send pre-suspension notifications (3 / 1 days)
# ✔ Recipients: OWNER + ADMINS (CompanyUser)
# ✔ Channel: In-App only (Notification Center)
# ===============================================================

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from billing_center.models import CompanySubscription
from billing_center.services.subscription_invoice_service import (
    generate_invoice_for_subscription_event,
)

from company_manager.models import CompanyUser
from notification_center.models import Notification
from notification_center.services import create_notification


class Command(BaseCommand):
    help = "Renew subscriptions, suspend expired companies, and send notifications"

    def handle(self, *args, **options):
        today = timezone.now().date()

        # ==========================================================
        # 🔔 1️⃣ PRE-SUSPENSION NOTIFICATIONS (3 / 1 days)
        # ==========================================================
        warning_days = [3, 1]

        expiring_subscriptions = CompanySubscription.objects.select_related(
            "company"
        ).filter(
            end_date__isnull=False,
            status="ACTIVE",
        )

        for sub in expiring_subscriptions:
            days_left = (sub.end_date - today).days

            if days_left not in warning_days:
                continue

            company = sub.company
            if not company:
                continue

            # ------------------------------------------------------
            # 🛑 Idempotency — prevent duplicate notifications
            # ------------------------------------------------------
            already_sent = Notification.objects.filter(
                company=company,
                code=f"SUBSCRIPTION_EXPIRING_{days_left}",
                created_at__date=today,
            ).exists()

            if already_sent:
                continue

            # ------------------------------------------------------
            # 👥 Recipients: OWNER + ADMINS
            # ------------------------------------------------------
            recipients = CompanyUser.objects.filter(
                company=company,
                role__in=["OWNER", "ADMIN"],
                is_active=True,
            ).select_related("user")

            if not recipients.exists():
                continue

            # ------------------------------------------------------
            # 🔔 Create notifications
            # ------------------------------------------------------
            for cu in recipients:
                create_notification(
                    recipient=cu.user,
                    company=company,
                    code=f"SUBSCRIPTION_EXPIRING_{days_left}",
                    title="⚠️ تنبيه قرب انتهاء الاشتراك",
                    message=(
                        f"اشتراك شركتك سينتهي خلال {days_left} يوم/أيام. "
                        "يرجى تجديد الاشتراك لتجنب إيقاف النظام."
                    ),
                    notification_type="billing",
                    severity="warning",
                    link="/system/billing",
                )

        # ==========================================================
        # ⛔ 2️⃣ AUTO SUSPEND — EXPIRED SUBSCRIPTIONS
        # ==========================================================
        expired_subscriptions = CompanySubscription.objects.select_related(
            "company"
        ).filter(
            end_date__isnull=False,
            end_date__lt=today,
        )

        suspended_count = 0

        for sub in expired_subscriptions:
            company = sub.company
            if not company or not company.is_active:
                continue

            try:
                with transaction.atomic():
                    company.is_active = False
                    company.save(update_fields=["is_active"])
                    suspended_count += 1

                    # --------------------------------------------------
                    # 🔔 Final suspension notification (In-App)
                    # --------------------------------------------------
                    recipients = CompanyUser.objects.filter(
                        company=company,
                        role__in=["OWNER", "ADMIN"],
                        is_active=True,
                    ).select_related("user")

                    for cu in recipients:
                        create_notification(
                            recipient=cu.user,
                            company=company,
                            code="COMPANY_SUSPENDED",
                            title="⛔ تم إيقاف الشركة",
                            message=(
                                "تم إيقاف النظام تلقائيًا لانتهاء الاشتراك. "
                                "يرجى تجديد الاشتراك لإعادة التفعيل."
                            ),
                            notification_type="billing",
                            severity="error",
                            link="/system/billing",
                        )

            except Exception as e:
                self.stderr.write(
                    f"Failed to suspend company {company.id}: {e}"
                )

        # ==========================================================
        # 🔁 3️⃣ RENEW ACTIVE SUBSCRIPTIONS
        # ==========================================================
        subscriptions = CompanySubscription.objects.select_related(
            "company", "plan"
        ).filter(
            status="ACTIVE",
            end_date__isnull=False,
            end_date__lte=today,
        )

        renewed_count = 0

        for subscription in subscriptions:
            try:
                with transaction.atomic():

                    generate_invoice_for_subscription_event(
                        subscription=subscription,
                        event_type="RENEWAL",
                    )

                    subscription.start_date = today
                    subscription.end_date = (
                        today.replace(year=today.year + 1)
                        if subscription.auto_renew
                        else None
                    )

                    subscription.save(
                        update_fields=["start_date", "end_date"]
                    )

                    renewed_count += 1

            except Exception as e:
                self.stderr.write(
                    f"Failed to renew subscription {subscription.id}: {e}"
                )

        # ==========================================================
        # ✅ Summary
        # ==========================================================
        self.stdout.write(
            self.style.SUCCESS(
                f"Renewed {renewed_count} subscription(s). "
                f"Suspended {suspended_count} company(s)."
            )
        )
