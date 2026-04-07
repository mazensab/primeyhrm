# ============================================================
# 📂 api/system/subscriptions/change_plan.py
# Mham Cloud
# Change Subscription Plan API — Notification Center Clean
# ============================================================

from __future__ import annotations

import importlib
import json
import logging
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from billing_center.models import (
    CompanySubscription,
    Invoice,
    SubscriptionPlan,
)

logger = logging.getLogger(__name__)


# ============================================================
# Helpers
# ============================================================

def _json_payload(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


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


def _generate_upgrade_invoice_number() -> str:
    """
    توليد رقم فاتورة فريد لطلبات ترقية الباقة
    """
    while True:
        candidate = (
            f"INV-UPG-"
            f"{timezone.now().strftime('%Y%m%d%H%M%S')}-"
            f"{uuid4().hex[:6].upper()}"
        )
        if not Invoice.objects.filter(invoice_number=candidate).exists():
            return candidate


def _collect_subscription_recipients(subscription) -> list[str]:
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
            "Failed while collecting subscription email recipients. subscription_id=%s",
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
    مفيد لاختلاف تسمية حقول الجوال بين النماذج.
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


def _collect_subscription_notification_targets(subscription) -> list[dict]:
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
            "Failed while collecting subscription notification targets. subscription_id=%s",
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


def _build_upgrade_context(*, subscription, current_plan, new_plan, invoice, difference, actor) -> dict:
    company = getattr(subscription, "company", None)
    owner = getattr(company, "owner", None) if company else None

    return {
        "subscription_id": getattr(subscription, "id", None),
        "company_id": getattr(company, "id", None) if company else None,
        "company_name": _safe_text(getattr(company, "name", None)),
        "company_email": _safe_text(getattr(company, "email", None)),
        "owner_user_id": getattr(owner, "id", None) if owner else None,
        "owner_email": _safe_text(getattr(owner, "email", None)) if owner else "",
        "current_plan_id": getattr(current_plan, "id", None),
        "current_plan_name": _safe_text(getattr(current_plan, "name", None)),
        "current_plan_price_yearly": _money_str(getattr(current_plan, "price_yearly", None)),
        "new_plan_id": getattr(new_plan, "id", None),
        "new_plan_name": _safe_text(getattr(new_plan, "name", None)),
        "new_plan_price_yearly": _money_str(getattr(new_plan, "price_yearly", None)),
        "difference_amount": _money_str(difference),
        "invoice_id": getattr(invoice, "id", None),
        "invoice_number": _safe_text(getattr(invoice, "invoice_number", None)),
        "invoice_status": _safe_text(getattr(invoice, "status", None)),
        "billing_reason": _safe_text(getattr(invoice, "billing_reason", None)),
        "subscription_start_date": _date_str(getattr(subscription, "start_date", None)),
        "subscription_end_date": _date_str(getattr(subscription, "end_date", None)),
        "recipients": _collect_subscription_recipients(subscription),
        "targets": _collect_subscription_notification_targets(subscription),
        "actor_user_id": getattr(actor, "id", None) if actor else None,
        "actor_username": _safe_text(getattr(actor, "username", None), "") if actor else "",
    }


def _build_downgrade_context(*, subscription, current_plan, new_plan, actor) -> dict:
    company = getattr(subscription, "company", None)
    owner = getattr(company, "owner", None) if company else None

    return {
        "subscription_id": getattr(subscription, "id", None),
        "company_id": getattr(company, "id", None) if company else None,
        "company_name": _safe_text(getattr(company, "name", None)),
        "company_email": _safe_text(getattr(company, "email", None)),
        "owner_user_id": getattr(owner, "id", None) if owner else None,
        "owner_email": _safe_text(getattr(owner, "email", None)) if owner else "",
        "current_plan_id": getattr(current_plan, "id", None),
        "current_plan_name": _safe_text(getattr(current_plan, "name", None)),
        "current_plan_price_yearly": _money_str(getattr(current_plan, "price_yearly", None)),
        "new_plan_id": getattr(new_plan, "id", None),
        "new_plan_name": _safe_text(getattr(new_plan, "name", None)),
        "new_plan_price_yearly": _money_str(getattr(new_plan, "price_yearly", None)),
        "subscription_start_date": _date_str(getattr(subscription, "start_date", None)),
        "subscription_end_date": _date_str(getattr(subscription, "end_date", None)),
        "recipients": _collect_subscription_recipients(subscription),
        "targets": _collect_subscription_notification_targets(subscription),
        "actor_user_id": getattr(actor, "id", None) if actor else None,
        "actor_username": _safe_text(getattr(actor, "username", None), "") if actor else "",
    }


def _dispatch_upgrade_notification(*, subscription, current_plan, new_plan, invoice, difference, actor) -> None:
    services_module = _load_subscription_notification_module()

    if not services_module:
        logger.warning(
            "Subscription notification service module not found for upgrade. subscription_id=%s invoice_id=%s",
            getattr(subscription, "id", None),
            getattr(invoice, "id", None),
        )
        return

    candidate_function_names = [
        "notify_subscription_plan_upgrade_created",
        "notify_plan_upgrade_created",
        "send_subscription_upgrade_notification",
        "send_plan_upgrade_notification",
    ]

    notify_func = None
    for func_name in candidate_function_names:
        notify_func = getattr(services_module, func_name, None)
        if callable(notify_func):
            break

    if not callable(notify_func):
        logger.warning(
            "Upgrade notification function not found. checked=%s",
            ", ".join(candidate_function_names),
        )
        return

    context = _build_upgrade_context(
        subscription=subscription,
        current_plan=current_plan,
        new_plan=new_plan,
        invoice=invoice,
        difference=difference,
        actor=actor,
    )

    try:
        notify_func(
            actor=actor,
            subscription=subscription,
            company=getattr(subscription, "company", None),
            current_plan=current_plan,
            new_plan=new_plan,
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
            current_plan=current_plan,
            new_plan=new_plan,
            invoice=invoice,
            context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(
            subscription=subscription,
            current_plan=current_plan,
            new_plan=new_plan,
            invoice=invoice,
        )
        return
    except Exception:
        logger.exception(
            "Failed while dispatching upgrade notification. subscription_id=%s invoice_id=%s",
            getattr(subscription, "id", None),
            getattr(invoice, "id", None),
        )
        return


def _dispatch_downgrade_notification(*, subscription, current_plan, new_plan, actor) -> None:
    services_module = _load_subscription_notification_module()

    if not services_module:
        logger.warning(
            "Subscription notification service module not found for downgrade. subscription_id=%s",
            getattr(subscription, "id", None),
        )
        return

    candidate_function_names = [
        "notify_subscription_plan_downgrade_requested",
        "notify_plan_downgrade_requested",
        "send_subscription_downgrade_notification",
        "send_plan_downgrade_notification",
    ]

    notify_func = None
    for func_name in candidate_function_names:
        notify_func = getattr(services_module, func_name, None)
        if callable(notify_func):
            break

    if not callable(notify_func):
        logger.warning(
            "Downgrade notification function not found. checked=%s",
            ", ".join(candidate_function_names),
        )
        return

    context = _build_downgrade_context(
        subscription=subscription,
        current_plan=current_plan,
        new_plan=new_plan,
        actor=actor,
    )

    try:
        notify_func(
            actor=actor,
            subscription=subscription,
            company=getattr(subscription, "company", None),
            current_plan=current_plan,
            new_plan=new_plan,
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
            current_plan=current_plan,
            new_plan=new_plan,
            context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(
            subscription=subscription,
            current_plan=current_plan,
            new_plan=new_plan,
        )
        return
    except Exception:
        logger.exception(
            "Failed while dispatching downgrade notification. subscription_id=%s",
            getattr(subscription, "id", None),
        )
        return


# ============================================================
# API
# POST /api/system/subscriptions/<id>/change-plan/
# ============================================================

@require_POST
@login_required
@transaction.atomic
def change_subscription_plan(request, subscription_id):

    payload = _json_payload(request)

    if not payload:
        return JsonResponse({
            "error": "Invalid payload"
        }, status=400)

    plan_id = payload.get("plan_id")

    if not plan_id:
        return JsonResponse({
            "error": "plan_id required"
        }, status=400)

    try:
        subscription = (
            CompanySubscription.objects
            .select_for_update()
            .select_related("company__owner", "plan")
            .get(id=subscription_id)
        )
    except CompanySubscription.DoesNotExist:
        return JsonResponse({
            "error": "Subscription not found"
        }, status=404)

    try:
        new_plan = SubscriptionPlan.objects.get(id=plan_id)
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({
            "error": "Plan not found"
        }, status=404)

    current_plan = subscription.plan

    # --------------------------------------------------------
    # Same Plan
    # --------------------------------------------------------

    if current_plan.id == new_plan.id:
        return JsonResponse({
            "message": "Already on this plan"
        })

    current_price = current_plan.price_yearly or 0
    new_price = new_plan.price_yearly or 0

    # --------------------------------------------------------
    # Upgrade
    # --------------------------------------------------------

    if new_price > current_price:

        difference = Decimal(new_price) - Decimal(current_price)

        invoice = Invoice.objects.create(
            company=subscription.company,
            subscription=subscription,
            invoice_number=_generate_upgrade_invoice_number(),
            subtotal_amount=difference,
            total_after_discount=difference,
            total_amount=difference,
            billing_reason="UPGRADE",
            status="PENDING",
            subscription_snapshot={
                "type": "UPGRADE",
                "subscription_id": subscription.id,
                "current_plan": {
                    "id": current_plan.id,
                    "name": current_plan.name,
                    "price_yearly": str(current_plan.price_yearly or 0),
                },
                "target_plan": {
                    "id": new_plan.id,
                    "name": new_plan.name,
                    "price_yearly": str(new_plan.price_yearly or 0),
                },
                "difference": str(difference),
            },
        )

        transaction.on_commit(
            lambda: _dispatch_upgrade_notification(
                subscription=subscription,
                current_plan=current_plan,
                new_plan=new_plan,
                invoice=invoice,
                difference=difference,
                actor=request.user,
            )
        )

        return JsonResponse({
            "action": "upgrade",
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "amount_due": str(difference)
        })

    # --------------------------------------------------------
    # Downgrade
    # --------------------------------------------------------

    transaction.on_commit(
        lambda: _dispatch_downgrade_notification(
            subscription=subscription,
            current_plan=current_plan,
            new_plan=new_plan,
            actor=request.user,
        )
    )

    return JsonResponse({
        "action": "downgrade_not_supported_yet",
        "message": "Downgrade scheduling requires a dedicated storage layer first."
    })