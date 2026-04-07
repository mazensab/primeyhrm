# ============================================================================
# 🟦 Billing & Subscription API — V4.5 Clean Notifications
# Mham Cloud — Super Admin & Company Level
# ============================================================================
# ✔ Single Source of Truth (Payment)
# ✔ Compatible with Models V9
# ✔ SAFE ADDITIONS ONLY
# ✔ Subscription Flow: PENDING → CONFIRM → ACTIVE
# ✔ Notification Center Integrated
# ============================================================================

from __future__ import annotations

import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now, timedelta
from django.db.models import Sum
from django.db import transaction

from company_manager.models import Company, CompanyUser
from billing_center.models import (
    CompanySubscription,
    SubscriptionPlan,
    Invoice,
    Payment,
)
from notification_center.services import notify_many, create_notification


# ============================================================================
# 🔹 Helpers
# ============================================================================

def serialize_invoice(invoice):
    if not invoice:
        return None

    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "amount": float(invoice.total_amount),
        "status": invoice.status,
        "issue_date": invoice.issue_date,
        "created_at": invoice.created_at,
    }


def serialize_subscription(subscription):
    if not subscription:
        return None

    days_remaining = (
        (subscription.end_date - now().date()).days
        if subscription.end_date else None
    )

    latest_invoice = (
        Invoice.objects
        .filter(subscription=subscription)
        .order_by("-created_at")
        .first()
    )

    return {
        "id": subscription.id,
        "company_id": subscription.company.id if subscription.company else None,
        "status": subscription.status,
        "start_date": subscription.start_date,
        "end_date": subscription.end_date,
        "days_remaining": max(days_remaining, 0) if days_remaining is not None else None,
        "plan": {
            "id": subscription.plan.id if subscription.plan else None,
            "name": subscription.plan.name if subscription.plan else None,
            "price_monthly": float(subscription.plan.price_monthly) if subscription.plan else None,
            "price_yearly": float(subscription.plan.price_yearly) if subscription.plan else None,
            "max_companies": subscription.plan.max_companies if subscription.plan else None,
        },
        "latest_invoice": serialize_invoice(latest_invoice),
    }


def _safe_company_users(company):
    return (
        CompanyUser.objects
        .filter(company=company, is_active=True, user__isnull=False)
        .select_related("user")
    )


def _safe_company_recipients(company):
    recipients = []
    seen_user_ids = set()

    for company_user in _safe_company_users(company):
        user = getattr(company_user, "user", None)
        user_id = getattr(user, "id", None)
        if not user or not user_id or user_id in seen_user_ids:
            continue

        seen_user_ids.add(user_id)
        recipients.append(user)

    owner = getattr(company, "owner", None)
    owner_id = getattr(owner, "id", None)
    if owner and owner_id and owner_id not in seen_user_ids:
        recipients.append(owner)

    return recipients


def _notify_company_subscription_renewed(
    *,
    company,
    subscription,
    invoice,
    actor=None,
    months: int = 0,
    years: int = 0,
):
    recipients = _safe_company_recipients(company)
    if not recipients:
        return []

    duration_label = f"{months} شهر" if months > 0 else f"{years} سنة"

    return notify_many(
        recipients=receptors if False else recipients,
        title="تم تجديد الاشتراك بنجاح",
        message=(
            f"تم تجديد اشتراك الشركة ({company.name}) بنجاح لمدة {duration_label}."
        ),
        notification_type="billing",
        severity="success",
        send_email=True,
        send_whatsapp=False,
        link=None,
        company=company,
        event_code="subscription_renewed",
        event_group="billing",
        actor=actor,
        language_code="ar",
        source="billing_v3.company_subscription_renew",
        context={
            "company_id": company.id,
            "company_name": company.name,
            "subscription_id": subscription.id if subscription else None,
            "invoice_id": invoice.id if invoice else None,
            "invoice_number": invoice.invoice_number if invoice else "",
            "months": months,
            "years": years,
            "new_end_date": str(subscription.end_date) if subscription and subscription.end_date else "",
        },
        target_object=subscription,
        template_key="subscription_renewed",
    )


def _notify_company_subscription_changed(
    *,
    company,
    subscription,
    old_plan_name: str,
    new_plan_name: str,
    actor=None,
):
    recipients = _safe_company_recipients(company)
    if not recipients:
        return []

    return notify_many(
        recipients=recipients,
        title="تم تغيير خطة الاشتراك",
        message=(
            f"تم تغيير خطة اشتراك الشركة ({company.name}) من "
            f"({old_plan_name or '-'}) إلى ({new_plan_name or '-'}) بنجاح."
        ),
        notification_type="billing",
        severity="info",
        send_email=True,
        send_whatsapp=False,
        link=None,
        company=company,
        event_code="subscription_plan_changed",
        event_group="billing",
        actor=actor,
        language_code="ar",
        source="billing_v3.company_subscription_change",
        context={
            "company_id": company.id,
            "company_name": company.name,
            "subscription_id": subscription.id if subscription else None,
            "old_plan_name": old_plan_name or "",
            "new_plan_name": new_plan_name or "",
        },
        target_object=subscription,
        template_key="subscription_plan_changed",
    )


def _notify_company_subscription_confirmed(
    *,
    company,
    subscription,
    invoice,
    payment,
    actor=None,
    billing_cycle: str = "monthly",
):
    recipients = _safe_company_recipients(company)
    if not recipients:
        return []

    return notify_many(
        recipients=recipients,
        title="تم تفعيل الاشتراك بنجاح",
        message=(
            f"تم تأكيد الدفع وتفعيل اشتراك الشركة ({company.name}) بنجاح."
        ),
        notification_type="billing",
        severity="success",
        send_email=True,
        send_whatsapp=True,
        link=None,
        company=company,
        event_code="subscription_confirmed",
        event_group="billing",
        actor=actor,
        language_code="ar",
        source="billing_v3.confirm_subscription",
        context={
            "company_id": company.id,
            "company_name": company.name,
            "subscription_id": subscription.id if subscription else None,
            "invoice_id": invoice.id if invoice else None,
            "invoice_number": invoice.invoice_number if invoice else "",
            "payment_id": payment.id if payment else None,
            "reference_number": getattr(payment, "reference_number", "") if payment else "",
            "billing_cycle": billing_cycle,
            "start_date": str(subscription.start_date) if subscription and subscription.start_date else "",
            "end_date": str(subscription.end_date) if subscription and subscription.end_date else "",
        },
        target_object=subscription,
        template_key="subscription_confirmed",
    )


def _notify_super_admin_billing_event(
    *,
    title: str,
    message: str,
    event_code: str,
    company=None,
    actor=None,
    context: dict | None = None,
    target_object=None,
):
    if not actor or not getattr(actor, "is_authenticated", False):
        return None

    return create_notification(
        recipient=actor,
        title=title,
        message=message,
        notification_type="billing_admin",
        severity="info",
        send_email=False,
        send_whatsapp=False,
        link=None,
        company=company,
        event_code=event_code,
        event_group="billing",
        actor=actor,
        target_user=actor,
        language_code="ar",
        source=f"billing_v3.{event_code}",
        context=context or {},
        target_object=target_object,
        template_key=event_code,
    )


# ============================================================================
# 1️⃣ Subscription — Company Detail
# ============================================================================

def company_subscription_detail(request, company_id):
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)

    subscription = (
        CompanySubscription.objects
        .filter(company=company)
        .select_related("plan")
        .first()
    )

    return JsonResponse({
        "status": "success",
        "company": {"id": company.id, "name": company.name},
        "subscription": serialize_subscription(subscription),
    })


# ============================================================================
# 2️⃣ Subscription — Renew (ACTIVE only)
# ============================================================================

@require_http_methods(["POST"])
def company_subscription_renew(request, company_id):
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)

    subscription = (
        CompanySubscription.objects
        .filter(company=company, status="ACTIVE")
        .select_related("plan")
        .first()
    )

    if not subscription or not subscription.plan:
        return JsonResponse({"error": "No active subscription"}, status=400)

    try:
        months = int(request.GET.get("months", 0))
        years = int(request.GET.get("years", 0))
    except Exception:
        return JsonResponse({"error": "Invalid renewal period"}, status=400)

    if months <= 0 and years <= 0:
        return JsonResponse({"error": "Invalid renewal period"}, status=400)

    if not subscription.end_date:
        return JsonResponse({"error": "Subscription end_date is missing"}, status=400)

    if months > 0:
        amount = subscription.plan.price_monthly * months
        new_end = subscription.end_date + timedelta(days=30 * months)
    else:
        amount = subscription.plan.price_yearly * years
        new_end = subscription.end_date + timedelta(days=365 * years)

    subscription.end_date = new_end
    subscription.save(update_fields=["end_date"])

    invoice = Invoice.objects.create(
        company=company,
        subscription=subscription,
        invoice_number=f"INV-{company.id}-{int(now().timestamp())}",
        total_amount=amount,
        status="PAID",
    )

    _notify_company_subscription_renewed(
        company=company,
        subscription=subscription,
        invoice=invoice,
        actor=getattr(request, "user", None),
        months=months,
        years=years,
    )

    _notify_super_admin_billing_event(
        title="تم تنفيذ تجديد اشتراك",
        message=f"تم تجديد اشتراك الشركة ({company.name}) بنجاح.",
        event_code="subscription_renewed_admin",
        company=company,
        actor=getattr(request, "user", None),
        context={
            "company_id": company.id,
            "company_name": company.name,
            "subscription_id": subscription.id,
            "invoice_id": invoice.id,
        },
        target_object=subscription,
    )

    return JsonResponse({
        "status": "success",
        "new_end_date": new_end,
    })


# ============================================================================
# 3️⃣ Subscription — Change Plan
# ============================================================================

@require_http_methods(["POST"])
def company_subscription_change(request, company_id):
    plan_id = request.GET.get("plan_id")
    if not plan_id:
        return JsonResponse({"error": "plan_id is required"}, status=400)

    try:
        company = Company.objects.get(id=company_id)
        new_plan = SubscriptionPlan.objects.get(id=plan_id)
    except (Company.DoesNotExist, SubscriptionPlan.DoesNotExist):
        return JsonResponse({"error": "Invalid company or plan"}, status=404)

    subscription = CompanySubscription.objects.filter(
        company=company,
        status="ACTIVE"
    ).select_related("plan").first()

    if not subscription:
        return JsonResponse({"error": "No active subscription"}, status=400)

    old_plan_name = subscription.plan.name if subscription.plan else ""
    subscription.plan = new_plan
    subscription.save(update_fields=["plan"])

    _notify_company_subscription_changed(
        company=company,
        subscription=subscription,
        old_plan_name=old_plan_name,
        new_plan_name=new_plan.name,
        actor=getattr(request, "user", None),
    )

    _notify_super_admin_billing_event(
        title="تم تغيير خطة اشتراك",
        message=f"تم تغيير خطة الشركة ({company.name}) إلى ({new_plan.name}).",
        event_code="subscription_plan_changed_admin",
        company=company,
        actor=getattr(request, "user", None),
        context={
            "company_id": company.id,
            "company_name": company.name,
            "subscription_id": subscription.id,
            "old_plan_name": old_plan_name,
            "new_plan_name": new_plan.name,
        },
        target_object=subscription,
    )

    return JsonResponse({
        "status": "success",
        "plan": new_plan.name,
    })


# ============================================================================
# 4️⃣ Subscription — Invoices List
# ============================================================================

def company_subscription_invoices(request, company_id):
    invoices = Invoice.objects.filter(company_id=company_id).order_by("-created_at")
    return JsonResponse({
        "status": "success",
        "invoices": [serialize_invoice(i) for i in invoices],
    })


# ============================================================================
# 5️⃣ Billing Overview — Super Admin
# ============================================================================

def billing_overview(request):
    return JsonResponse({
        "status": "success",
        "subscriptions": {
            "total": CompanySubscription.objects.count(),
            "active": CompanySubscription.objects.filter(status="ACTIVE").count(),
            "expired": CompanySubscription.objects.filter(status="EXPIRED").count(),
        },
        "payments": {
            "total_amount": Payment.objects.aggregate(total=Sum("amount"))["total"] or 0,
        },
    })


# ============================================================================
# 6️⃣ Subscriptions Overview — Super Admin
# ============================================================================

def subscriptions_overview(request):
    today = now().date()
    return JsonResponse({
        "status": "success",
        "expiring_7_days": CompanySubscription.objects.filter(
            end_date__lte=today + timedelta(days=7),
            status="ACTIVE",
        ).count(),
    })


# ============================================================================
# 7️⃣ Account Companies Usage
# ============================================================================

@login_required
def account_companies_usage(request):
    subscription = (
        CompanySubscription.objects
        .filter(company__companyuser__user=request.user, status="ACTIVE")
        .select_related("plan")
        .first()
    )

    if not subscription:
        return JsonResponse({"error": "No active subscription"}, status=400)

    used = (
        CompanyUser.objects
        .filter(user=request.user, is_active=True)
        .values("company")
        .distinct()
        .count()
    )

    return JsonResponse({
        "status": "success",
        "companies": {
            "used": used,
            "max": subscription.plan.max_companies,
            "remaining": max(subscription.plan.max_companies - used, 0),
        }
    })


# ============================================================================
# 8️⃣ Confirm Subscription (CASH) — HARDENED
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def confirm_subscription(request):
    """
    🔐 Super Admin ONLY
    STEP: PENDING → ACTIVE (Cash Payment)
    """

    if not request.user.is_superuser:
        return JsonResponse({"error": "Permission denied"}, status=403)

    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    company_id = payload.get("company_id")
    billing_cycle = payload.get("billing_cycle", "monthly")
    reference_number = payload.get("reference_number")

    if not company_id or not reference_number:
        return JsonResponse(
            {"error": "company_id and reference_number are required"},
            status=400,
        )

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)

    if CompanySubscription.objects.filter(company=company, status="ACTIVE").exists():
        return JsonResponse(
            {"error": "Company already has an active subscription"},
            status=400,
        )

    subscription = (
        CompanySubscription.objects
        .filter(company=company, status="PENDING")
        .select_related("plan")
        .first()
    )

    if not subscription or not subscription.plan:
        return JsonResponse({"error": "No pending subscription"}, status=400)

    plan = subscription.plan

    if not plan.is_active:
        return JsonResponse({"error": "Subscription plan is not active"}, status=400)

    if billing_cycle == "yearly":
        amount = plan.price_yearly
        end_date = now().date() + timedelta(days=365)
    else:
        amount = plan.price_monthly
        end_date = now().date() + timedelta(days=30)

    with transaction.atomic():
        invoice = Invoice.objects.create(
            company=company,
            subscription=subscription,
            invoice_number=f"INV-{company.id}-{int(now().timestamp())}",
            total_amount=amount,
            status="PAID",
        )

        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            method="BANK_TRANSFER",
            reference_number=reference_number,
            created_by=request.user,
        )

        subscription.status = "ACTIVE"
        subscription.start_date = now().date()
        subscription.end_date = end_date
        subscription.apps_snapshot = list(plan.apps or [])
        subscription.save()

    _notify_company_subscription_confirmed(
        company=company,
        subscription=subscription,
        invoice=invoice,
        payment=payment,
        actor=request.user,
        billing_cycle=billing_cycle,
    )

    _notify_super_admin_billing_event(
        title="تم تأكيد اشتراك نقدي",
        message=f"تم تأكيد وتفعيل اشتراك الشركة ({company.name}) بنجاح.",
        event_code="subscription_confirmed_admin",
        company=company,
        actor=request.user,
        context={
            "company_id": company.id,
            "company_name": company.name,
            "subscription_id": subscription.id,
            "invoice_id": invoice.id,
            "payment_id": payment.id,
            "reference_number": reference_number,
            "billing_cycle": billing_cycle,
        },
        target_object=subscription,
    )

    return JsonResponse({
        "status": "success",
        "invoice": serialize_invoice(invoice),
        "subscription": serialize_subscription(subscription),
    })