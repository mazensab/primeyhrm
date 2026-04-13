# ===============================================================
# 🔁 Renew Subscriptions Scheduler Command
# Mham Cloud | Billing Center | PRODUCT-AWARE SAFE
# ===============================================================
# ✔ Sends expiring notifications per subscription/product
# ✔ Updates expired subscription status per subscription
# ✔ Does NOT suspend company globally
# ✔ Generates renewal invoices only for eligible subscriptions
# ✔ Product-aware / subscription-aware
# ✔ Safer idempotency than company-level legacy logic
# ===============================================================

from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from billing_center.models import CompanySubscription
from billing_center.services.subscription_invoice_service import (
    generate_invoice_for_subscription_event,
)
from company_manager.models import CompanyUser
from notification_center.models import Notification
from notification_center.services import create_notification


# ===============================================================
# 🧩 Helpers
# ===============================================================
def _safe_product_code(subscription: CompanySubscription) -> str:
    product = getattr(subscription, "resolved_product", None)
    return getattr(product, "code", None) or "UNKNOWN"


def _safe_product_name(subscription: CompanySubscription) -> str:
    product = getattr(subscription, "resolved_product", None)
    return getattr(product, "name", None) or "المنتج"


def _normalize_role(value) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def _get_company_recipients(company):
    """
    Recipients: OWNER + ADMINS
    Supports legacy string roles.
    """
    recipients = []

    qs = (
        CompanyUser.objects
        .filter(company=company, is_active=True)
        .select_related("user")
        .order_by("id")
    )

    for item in qs:
        role_value = _normalize_role(getattr(item, "role", None))
        if role_value not in {"OWNER", "ADMIN"}:
            continue
        if not getattr(item, "user", None):
            continue
        recipients.append(item)

    return recipients


def _renewal_notification_code(subscription: CompanySubscription, days_left: int) -> str:
    return f"SUBSCRIPTION_EXPIRING_{_safe_product_code(subscription)}_{days_left}"


def _expired_notification_code(subscription: CompanySubscription) -> str:
    return f"SUBSCRIPTION_EXPIRED_{_safe_product_code(subscription)}"


def _build_expiring_message(subscription: CompanySubscription, days_left: int) -> str:
    product_name = _safe_product_name(subscription)
    end_date = subscription.end_date.strftime("%Y-%m-%d") if subscription.end_date else "-"
    return (
        f"اشتراك منتج {product_name} سينتهي خلال {days_left} يوم/أيام "
        f"(تاريخ الانتهاء: {end_date}). يرجى التجديد لتجنب توقف هذا المنتج."
    )


def _build_expired_message(subscription: CompanySubscription) -> str:
    product_name = _safe_product_name(subscription)
    end_date = subscription.end_date.strftime("%Y-%m-%d") if subscription.end_date else "-"
    return (
        f"انتهى اشتراك منتج {product_name} بتاريخ {end_date}. "
        "يرجى التجديد لإعادة تفعيل هذا المنتج."
    )


def _build_notification_link(subscription: CompanySubscription) -> str:
    return f"/system/subscriptions/{subscription.id}"


# ===============================================================
# Command
# ===============================================================
class Command(BaseCommand):
    help = "Renew subscriptions and send product-aware renewal/expiry notifications"

    def handle(self, *args, **options):
        today = timezone.now().date()

        warning_days = [3, 1]

        warnings_sent_count = 0
        expired_count = 0
        renewed_count = 0

        # ==========================================================
        # 🔔 1️⃣ EXPIRING NOTIFICATIONS (3 / 1 days) — PRODUCT-AWARE
        # ==========================================================
        expiring_subscriptions = (
            CompanySubscription.objects
            .select_related("company", "plan", "product")
            .filter(
                status="ACTIVE",
                end_date__isnull=False,
                end_date__gte=today,
            )
            .order_by("end_date", "id")
        )

        for subscription in expiring_subscriptions:
            days_left = (subscription.end_date - today).days

            if days_left not in warning_days:
                continue

            company = subscription.company
            if not company:
                continue

            notification_code = _renewal_notification_code(subscription, days_left)

            already_sent = Notification.objects.filter(
                company=company,
                code=notification_code,
                created_at__date=today,
            ).exists()

            if already_sent:
                continue

            recipients = _get_company_recipients(company)
            if not recipients:
                continue

            for company_user in recipients:
                create_notification(
                    recipient=company_user.user,
                    company=company,
                    code=notification_code,
                    title="⚠️ تنبيه قرب انتهاء الاشتراك",
                    message=_build_expiring_message(subscription, days_left),
                    notification_type="billing",
                    severity="warning",
                    link=_build_notification_link(subscription),
                )
                warnings_sent_count += 1

        # ==========================================================
        # ⛔ 2️⃣ EXPIRE SUBSCRIPTIONS ONLY — NO COMPANY SUSPEND
        # ==========================================================
        expired_subscriptions = (
            CompanySubscription.objects
            .select_related("company", "plan", "product")
            .filter(
                end_date__isnull=False,
                end_date__lt=today,
            )
            .exclude(status="EXPIRED")
            .order_by("end_date", "id")
        )

        for subscription in expired_subscriptions:
            company = subscription.company
            if not company:
                continue

            try:
                with transaction.atomic():
                    subscription.status = "EXPIRED"
                    subscription.save(update_fields=["status"])
                    expired_count += 1

                    recipients = _get_company_recipients(company)
                    if not recipients:
                        continue

                    notification_code = _expired_notification_code(subscription)

                    already_sent = Notification.objects.filter(
                        company=company,
                        code=notification_code,
                        created_at__date=today,
                    ).exists()

                    if already_sent:
                        continue

                    for company_user in recipients:
                        create_notification(
                            recipient=company_user.user,
                            company=company,
                            code=notification_code,
                            title="⛔ انتهى الاشتراك",
                            message=_build_expired_message(subscription),
                            notification_type="billing",
                            severity="error",
                            link=_build_notification_link(subscription),
                        )

            except Exception as exc:
                self.stderr.write(
                    f"Failed to expire subscription {subscription.id}: {exc}"
                )

        # ==========================================================
        # 🔁 3️⃣ GENERATE RENEWAL INVOICES FOR ELIGIBLE SUBSCRIPTIONS
        # ----------------------------------------------------------
        # Only:
        # - ACTIVE
        # - auto_renew=True
        # - end_date reached/passed
        # - do NOT extend dates here
        #   (renewal confirmation/payment flow should handle activation)
        # ==========================================================
        renewable_subscriptions = (
            CompanySubscription.objects
            .select_related("company", "plan", "product")
            .filter(
                status="ACTIVE",
                auto_renew=True,
                end_date__isnull=False,
                end_date__lte=today,
            )
            .order_by("end_date", "id")
        )

        for subscription in renewable_subscriptions:
            try:
                with transaction.atomic():
                    invoice = generate_invoice_for_subscription_event(
                        subscription=subscription,
                        event_type="RENEWAL",
                    )

                    if invoice:
                        renewed_count += 1

            except Exception as exc:
                self.stderr.write(
                    f"Failed to generate renewal invoice for subscription {subscription.id}: {exc}"
                )

        # ==========================================================
        # ✅ Summary
        # ==========================================================
        self.stdout.write(
            self.style.SUCCESS(
                "Renew Subscriptions Summary | "
                f"warnings_sent={warnings_sent_count} | "
                f"expired={expired_count} | "
                f"renewal_invoices_created={renewed_count}"
            )
        )