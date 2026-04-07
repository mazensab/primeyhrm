# ============================================================
# 🔄 Renew Company Subscription
# Mham Cloud — Notification Center Clean
# ============================================================

from __future__ import annotations

import importlib
import logging
from decimal import Decimal

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from billing_center.models import (
    CompanySubscription,
    Invoice,
)

VAT_RATE = Decimal("0.15")
logger = logging.getLogger(__name__)


# ============================================================
# 🧩 Helpers
# ============================================================

def _safe_text(value, default="-"):
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def _normalize_email(value: str) -> str:
    if not value:
        return ""
    return str(value).strip().lower()


def _money_str(value) -> str:
    try:
        return f"{Decimal(value):.2f}"
    except Exception:
        return "0.00"


def _date_str(value) -> str:
    if not value:
        return "-"
    try:
        return value.strftime("%Y-%m-%d")
    except Exception:
        return str(value)


def _collect_recipients(subscription) -> list[str]:
    recipients: list[str] = []

    company = getattr(subscription, "company", None)
    owner = getattr(company, "owner", None) if company else None

    candidates = [
        getattr(company, "email", None),
        getattr(owner, "email", None),
    ]

    try:
        admin_link = (
            company.company_users
            .select_related("user")
            .filter(is_active=True, role__in=["admin", "owner"])
            .order_by("id")
            .first()
        ) if company else None

        if admin_link and admin_link.user and admin_link.user.email:
            candidates.append(admin_link.user.email)
    except Exception:
        logger.exception(
            "Failed while collecting renewal email recipients. subscription_id=%s",
            getattr(subscription, "id", None),
        )

    for value in candidates:
        email = _normalize_email(value)
        if email and email not in recipients:
            recipients.append(email)

    return recipients


def _get_first_existing_attr(instance, attr_names: list[str], default=""):
    """
    قراءة أول حقل موجود وغير فارغ من قائمة أسماء محتملة.
    """
    if not instance:
        return default

    for attr_name in attr_names:
        try:
            value = getattr(instance, attr_name, None)
        except Exception:
            value = None

        value = _safe_text(value, "")
        if value:
            return value

    return default


def _get_user_related_profile_candidates(user) -> list:
    """
    محاولة الوصول إلى بروفايل المستخدم الشائع بدون فرض اسم محدد.
    """
    if not user:
        return []

    candidates = []

    for attr_name in ["profile", "userprofile"]:
        try:
            related_obj = getattr(user, attr_name, None)
        except Exception:
            related_obj = None

        if related_obj:
            candidates.append(related_obj)

    return candidates


def _get_best_phone_for_entity(instance) -> str:
    """
    جلب أفضل رقم جوال من الكيان مباشرة أو من profile/userprofile إن وجد.
    """
    phone_attr_candidates = [
        "phone",
        "mobile",
        "mobile_number",
        "whatsapp_number",
        "phone_number",
    ]

    direct_phone = _get_first_existing_attr(instance, phone_attr_candidates, "")
    if direct_phone:
        return direct_phone

    for profile_obj in _get_user_related_profile_candidates(instance):
        profile_phone = _get_first_existing_attr(profile_obj, phone_attr_candidates, "")
        if profile_phone:
            return profile_phone

    return ""


def _collect_notification_targets(subscription) -> list[dict]:
    """
    تجميع مستهدفي الإشعار بشكل آمن وبدون تكرار.
    """
    targets: list[dict] = []
    seen_phones: set[str] = set()
    seen_emails: set[str] = set()

    company = getattr(subscription, "company", None)
    owner = getattr(company, "owner", None) if company else None

    def _append_target(*, phone="", email="", name="", role=""):
        safe_phone = _safe_text(phone, "")
        safe_email = _normalize_email(email)
        safe_name = _safe_text(name, "User")
        safe_role = _safe_text(role, "")

        key = safe_phone or safe_email
        if not key:
            return

        if safe_phone and safe_phone in seen_phones:
            return

        if safe_email and safe_email in seen_emails:
            return

        if safe_phone:
            seen_phones.add(safe_phone)

        if safe_email:
            seen_emails.add(safe_email)

        targets.append({
            "phone": safe_phone,
            "email": safe_email,
            "name": safe_name,
            "role": safe_role,
        })

    _append_target(
        phone=_get_best_phone_for_entity(company),
        email=getattr(company, "email", None),
        name=getattr(company, "name", None),
        role="company",
    )

    _append_target(
        phone=_get_best_phone_for_entity(owner),
        email=getattr(owner, "email", None),
        name=getattr(owner, "first_name", None) or getattr(owner, "username", None),
        role="owner",
    )

    try:
        admin_link = (
            company.company_users
            .select_related("user")
            .filter(is_active=True, role__in=["admin", "owner"])
            .order_by("id")
            .first()
        ) if company else None

        admin_user = getattr(admin_link, "user", None) if admin_link else None
        _append_target(
            phone=_get_best_phone_for_entity(admin_user),
            email=getattr(admin_user, "email", None),
            name=getattr(admin_user, "first_name", None) or getattr(admin_user, "username", None),
            role=getattr(admin_link, "role", "admin") if admin_link else "admin",
        )
    except Exception:
        logger.exception(
            "Failed while collecting renewal notification targets. subscription_id=%s",
            getattr(subscription, "id", None),
        )

    return targets


# ============================================================
# Notification Helpers
# ============================================================

def _load_subscription_notification_module():
    """
    تحميل مرن لطبقة الاشتراكات/الفوترة الرسمية.
    """
    candidate_modules = [
        "notification_center.services_billing",
        "notification_center.services_company",
    ]

    for module_path in candidate_modules:
        try:
            return importlib.import_module(module_path)
        except Exception:
            continue

    return None


def _build_renewal_context(*, subscription, invoice, duration, subtotal, vat_amount, total, actor) -> dict:
    company = getattr(subscription, "company", None)
    owner = getattr(company, "owner", None) if company else None
    plan = getattr(subscription, "plan", None)

    return {
        "subscription_id": getattr(subscription, "id", None),
        "company_id": getattr(company, "id", None) if company else None,
        "company_name": _safe_text(getattr(company, "name", None)),
        "company_email": _safe_text(getattr(company, "email", None)),
        "company_phone": _safe_text(getattr(company, "phone", None)),
        "owner_user_id": getattr(owner, "id", None) if owner else None,
        "owner_email": _safe_text(getattr(owner, "email", None)) if owner else "",
        "plan_id": getattr(plan, "id", None) if plan else None,
        "plan_name": _safe_text(getattr(plan, "name", None)),
        "duration": _safe_text(duration),
        "invoice_id": getattr(invoice, "id", None),
        "invoice_number": _safe_text(getattr(invoice, "invoice_number", None)),
        "invoice_status": _safe_text(getattr(invoice, "status", None)),
        "billing_reason": _safe_text(getattr(invoice, "billing_reason", None)),
        "issue_date": _date_str(getattr(invoice, "issue_date", None)),
        "subtotal_amount": _money_str(subtotal),
        "vat_amount": _money_str(vat_amount),
        "total_amount": _money_str(total),
        "subscription_end_date": _date_str(getattr(subscription, "end_date", None)),
        "recipients": _collect_recipients(subscription),
        "targets": _collect_notification_targets(subscription),
        "actor_user_id": getattr(actor, "id", None) if actor else None,
        "actor_username": _safe_text(getattr(actor, "username", None), "") if actor else "",
    }


def _dispatch_renewal_notification(*, subscription, invoice, duration, subtotal, vat_amount, total, actor) -> None:
    services_module = _load_subscription_notification_module()

    if not services_module:
        logger.warning(
            "Subscription notification service module not found for renewal. subscription_id=%s invoice_id=%s",
            getattr(subscription, "id", None),
            getattr(invoice, "id", None),
        )
        return

    candidate_function_names = [
        "notify_subscription_renewal_invoice_created",
        "notify_renewal_invoice_created",
        "send_subscription_renewal_notification",
        "send_renewal_invoice_notification",
    ]

    notify_func = None
    for func_name in candidate_function_names:
        notify_func = getattr(services_module, func_name, None)
        if callable(notify_func):
            break

    if not callable(notify_func):
        logger.warning(
            "Renewal notification function not found. checked=%s",
            ", ".join(candidate_function_names),
        )
        return

    context = _build_renewal_context(
        subscription=subscription,
        invoice=invoice,
        duration=duration,
        subtotal=subtotal,
        vat_amount=vat_amount,
        total=total,
        actor=actor,
    )

    try:
        notify_func(
            actor=actor,
            subscription=subscription,
            company=getattr(subscription, "company", None),
            invoice=invoice,
            extra_context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(
            actor=actor,
            subscription=subscription,
            company=getattr(subscription, "company", None),
            invoice=invoice,
            context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(
            subscription=subscription,
            invoice=invoice,
        )
        return
    except Exception:
        logger.exception(
            "Failed while dispatching renewal notification. subscription_id=%s invoice_id=%s",
            getattr(subscription, "id", None),
            getattr(invoice, "id", None),
        )
        return


@require_POST
def renew_subscription(request, subscription_id):

    # ------------------------------------------------
    # Action Type (future support)
    # ------------------------------------------------
    action = request.POST.get("action", "RENEWAL")
    duration = request.POST.get("duration", "monthly")

    with transaction.atomic():
        subscription = get_object_or_404(
            CompanySubscription.objects.select_related("company__owner", "plan"),
            id=subscription_id
        )

        company = subscription.company
        plan = subscription.plan

        # ------------------------------------------------
        # Safety Guard
        # ------------------------------------------------
        active = CompanySubscription.objects.filter(
            company=company,
            status="ACTIVE"
        ).exclude(id=subscription.id).exists()

        if active:
            return JsonResponse({
                "error": "Company already has active subscription"
            }, status=400)

        # ------------------------------------------------
        # Prevent duplicate renewal invoice
        # ------------------------------------------------
        existing_invoice = Invoice.objects.filter(
            subscription=subscription,
            billing_reason="RENEWAL",
            status="PENDING"
        ).first()

        if existing_invoice:
            return JsonResponse({
                "error": "Renewal invoice already exists",
                "invoice_id": existing_invoice.id
            }, status=400)

        # ------------------------------------------------
        # Calculate Price
        # ------------------------------------------------
        if duration == "yearly":
            price = plan.price_yearly
        else:
            price = plan.price_monthly

        vat_amount = price * VAT_RATE
        total = price + vat_amount

        # ------------------------------------------------
        # Create Invoice
        # ------------------------------------------------
        invoice = Invoice.objects.create(
            company=company,
            subscription=subscription,
            invoice_number=f"INV-R-{int(timezone.now().timestamp())}",
            issue_date=timezone.now().date(),
            subtotal_amount=price,
            total_amount=total,
            billing_reason=action,
            status="PENDING",
        )

        # ------------------------------------------------
        # Notification Center الرسمي فقط بعد نجاح الـ commit
        # ------------------------------------------------
        transaction.on_commit(
            lambda: _dispatch_renewal_notification(
                subscription=subscription,
                invoice=invoice,
                duration=duration,
                subtotal=price,
                vat_amount=vat_amount,
                total=total,
                actor=getattr(request, "user", None),
            )
        )

    return JsonResponse({
        "success": True,
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number
    })