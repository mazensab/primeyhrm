# ====================================================================
# 💳 Confirm Cash Payment — FINAL ULTRA STABLE
# Mham Cloud | Super Admin Only
# ====================================================================
# ✔ Confirm manual CASH payment
# ✔ Invoice -> PAID
# ✔ Subscription -> ACTIVE
# ✔ Company -> ACTIVE (AUTO RULE after first successful payment)
# ✔ Upgrade Flow Supported
# ✔ Idempotent & Transaction-safe
# ✔ Notification Center Only (No direct email / no direct WhatsApp)
# ✔ Invoice PDF Context Supported
# ====================================================================

from __future__ import annotations

import importlib
import json
import logging
from decimal import Decimal
from io import BytesIO

from django.db import transaction
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing_center.models import (
    CompanySubscription,
    Invoice,
    Payment,
    SubscriptionPlan,
)

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


def _build_invoice_recipients(invoice) -> list[str]:
    """
    تحديد المستلمين بدون تكرار:
    - company.email
    - company.owner.email
    - أول admin داخل الشركة
    """
    recipients: list[str] = []

    company = getattr(invoice, "company", None)
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
            "Failed while building invoice recipients. invoice_id=%s",
            getattr(invoice, "id", None),
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


def _collect_invoice_notification_targets(invoice) -> list[dict]:
    """
    تجميع مستهدفي الإشعار بشكل آمن وبدون تكرار.
    """
    targets: list[dict] = []
    seen_phones: set[str] = set()
    seen_emails: set[str] = set()

    company = getattr(invoice, "company", None)
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
            "Failed while collecting invoice notification targets. invoice_id=%s",
            getattr(invoice, "id", None),
        )

    return targets


def _generate_invoice_pdf_bytes(*, invoice, payment, subscription) -> bytes | None:
    """
    إنشاء PDF بسيط للفـاتورة.
    إذا تعذر إنشاء الـ PDF لا نفشل عملية الدفع.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        _, height = A4

        y = height - 50

        company = getattr(invoice, "company", None)

        pdf.setTitle(f"Invoice {invoice.invoice_number}")

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(40, y, "Mham Cloud")
        y -= 28

        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(40, y, "Invoice Payment Confirmation")
        y -= 28

        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, y, f"Invoice Number: {_safe_text(invoice.invoice_number)}")
        y -= 18
        pdf.drawString(40, y, f"Company: {_safe_text(getattr(company, 'name', None))}")
        y -= 18
        pdf.drawString(40, y, f"Issue Date: {_date_str(getattr(invoice, 'issue_date', None))}")
        y -= 18
        pdf.drawString(40, y, f"Status: {_safe_text(getattr(invoice, 'status', None))}")
        y -= 18
        pdf.drawString(40, y, f"Payment Method: {_safe_text(getattr(payment, 'method', None))}")
        y -= 18
        pdf.drawString(40, y, f"Paid At: {_date_str(getattr(payment, 'paid_at', None))}")
        y -= 28

        subtotal_value = (
            getattr(invoice, "subtotal_amount", None)
            if hasattr(invoice, "subtotal_amount")
            else getattr(invoice, "subtotal", None)
        )
        vat_value = getattr(invoice, "vat", None)
        total_value = getattr(invoice, "total_amount", None)

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, "Totals")
        y -= 22

        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, y, f"Subtotal: {_money_str(subtotal_value)} SAR")
        y -= 18
        pdf.drawString(40, y, f"VAT: {_money_str(vat_value)} SAR")
        y -= 18
        pdf.drawString(40, y, f"Total: {_money_str(total_value)} SAR")
        y -= 28

        if subscription:
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(40, y, "Subscription")
            y -= 22

            pdf.setFont("Helvetica", 10)
            pdf.drawString(40, y, f"Plan: {_safe_text(getattr(getattr(subscription, 'plan', None), 'name', None))}")
            y -= 18
            pdf.drawString(40, y, f"Status: {_safe_text(getattr(subscription, 'status', None))}")
            y -= 18
            pdf.drawString(40, y, f"Start Date: {_date_str(getattr(subscription, 'start_date', None))}")
            y -= 18
            pdf.drawString(40, y, f"End Date: {_date_str(getattr(subscription, 'end_date', None))}")
            y -= 24

        pdf.setFont("Helvetica-Oblique", 9)
        pdf.drawString(40, y, "Generated automatically by Mham Cloud.")

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        return buffer.getvalue()

    except Exception:
        logger.exception(
            "Failed to generate invoice PDF. invoice_id=%s",
            getattr(invoice, "id", None),
        )
        return None


# ============================================================
# Notification Helpers
# ============================================================

def _load_billing_notification_module():
    """
    تحميل مرن لطبقة billing الرسمية.
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


def _build_cash_payment_context(*, invoice, payment, subscription, actor) -> dict:
    company = getattr(invoice, "company", None)
    owner = getattr(company, "owner", None) if company else None

    subtotal_value = (
        getattr(invoice, "subtotal_amount", None)
        if hasattr(invoice, "subtotal_amount")
        else getattr(invoice, "subtotal", None)
    )
    vat_value = getattr(invoice, "vat", None)
    total_value = getattr(invoice, "total_amount", None)

    pdf_bytes = _generate_invoice_pdf_bytes(
        invoice=invoice,
        payment=payment,
        subscription=subscription,
    )

    return {
        "invoice_id": getattr(invoice, "id", None),
        "invoice_number": _safe_text(getattr(invoice, "invoice_number", None)),
        "invoice_status": _safe_text(getattr(invoice, "status", None)),
        "billing_reason": _safe_text(getattr(invoice, "billing_reason", None)),
        "company_id": getattr(company, "id", None) if company else None,
        "company_name": _safe_text(getattr(company, "name", None)),
        "company_email": _safe_text(getattr(company, "email", None)),
        "company_phone": _safe_text(getattr(company, "phone", None)),
        "company_active": bool(getattr(company, "is_active", False)) if company else False,
        "owner_user_id": getattr(owner, "id", None) if owner else None,
        "owner_email": _safe_text(getattr(owner, "email", None)) if owner else "",
        "payment_id": getattr(payment, "id", None),
        "payment_method": _safe_text(getattr(payment, "method", None)),
        "payment_reference": _safe_text(getattr(payment, "reference_number", None)),
        "paid_at": _date_str(getattr(payment, "paid_at", None)),
        "subtotal_amount": _money_str(subtotal_value),
        "vat_amount": _money_str(vat_value),
        "total_amount": _money_str(total_value),
        "plan_name": _safe_text(getattr(getattr(subscription, "plan", None), "name", None)) if subscription else "-",
        "subscription_id": getattr(subscription, "id", None) if subscription else None,
        "subscription_status": _safe_text(getattr(subscription, "status", None)) if subscription else "-",
        "subscription_start_date": _date_str(getattr(subscription, "start_date", None)) if subscription else "-",
        "subscription_end_date": _date_str(getattr(subscription, "end_date", None)) if subscription else "-",
        "recipients": _build_invoice_recipients(invoice),
        "targets": _collect_invoice_notification_targets(invoice),
        "invoice_pdf_bytes": pdf_bytes,
        "invoice_pdf_filename": f"{_safe_text(getattr(invoice, 'invoice_number', None), 'invoice')}.pdf",
        "actor_user_id": getattr(actor, "id", None) if actor else None,
        "actor_username": _safe_text(getattr(actor, "username", None), "") if actor else "",
    }


def _dispatch_cash_payment_confirmation_notification(*, invoice, payment, subscription, actor) -> None:
    """
    تمرير إشعار الدفع النقدي المؤكد إلى الطبقة الرسمية فقط.
    """
    services_module = _load_billing_notification_module()

    if not services_module:
        logger.warning(
            "Billing notification service module not found. invoice_id=%s payment_id=%s",
            getattr(invoice, "id", None),
            getattr(payment, "id", None),
        )
        return

    candidate_function_names = [
        "notify_cash_payment_confirmed",
        "notify_payment_confirmed",
        "send_cash_payment_confirmation_notification",
        "send_payment_confirmation_notification",
    ]

    notify_func = None
    for func_name in candidate_function_names:
        notify_func = getattr(services_module, func_name, None)
        if callable(notify_func):
            break

    if not callable(notify_func):
        logger.warning(
            "Cash payment notification function not found. checked=%s",
            ", ".join(candidate_function_names),
        )
        return

    context = _build_cash_payment_context(
        invoice=invoice,
        payment=payment,
        subscription=subscription,
        actor=actor,
    )

    try:
        notify_func(
            actor=actor,
            invoice=invoice,
            payment=payment,
            subscription=subscription,
            company=getattr(invoice, "company", None),
            extra_context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(
            actor=actor,
            invoice=invoice,
            payment=payment,
            subscription=subscription,
            company=getattr(invoice, "company", None),
            context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(
            invoice=invoice,
            payment=payment,
            subscription=subscription,
        )
        return
    except Exception:
        logger.exception(
            "Failed while dispatching cash payment confirmation notification. invoice_id=%s payment_id=%s",
            getattr(invoice, "id", None),
            getattr(payment, "id", None),
        )
        return


@csrf_exempt
@require_POST
@transaction.atomic
def confirm_cash_payment(request):
    """
    Confirm Cash Payment (Manual)

    - Super Admin only
    - Marks invoice as PAID
    - Creates Payment record (SOURCE OF TRUTH)
    - Activates subscription
    - Auto-activates company (RULE: after ACTIVE subscription)
    - Supports UPGRADE invoices
    """

    # ============================================================
    # 🔐 Authorization
    # ============================================================
    if not request.user.is_authenticated or not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        payload = json.loads(request.body or "{}")
        invoice_id = payload.get("invoice_id")

        if not invoice_id:
            return JsonResponse(
                {"error": "invoice_id is required"},
                status=400
            )

        # ========================================================
        # 🧾 Invoice
        # ========================================================
        invoice = Invoice.objects.select_for_update().select_related(
            "subscription__plan",
            "company__owner",
        ).get(id=invoice_id)

        if invoice.status == "PAID":
            return JsonResponse(
                {"error": "Invoice already paid"},
                status=400
            )

        # ========================================================
        # 🔄 Subscription Reference
        # ========================================================
        subscription = invoice.subscription

        # ========================================================
        # 💳 Create Payment (SOURCE OF TRUTH)
        # ========================================================
        payment = Payment.objects.create(
            invoice=invoice,
            amount=invoice.total_amount,
            method="CASH",
            reference_number=f"CASH-{invoice.id}-{int(now().timestamp())}",
            paid_at=now(),
            created_by=request.user,
        )

        # ========================================================
        # ✅ Update Invoice (STATUS ONLY)
        # ========================================================
        invoice.status = "PAID"
        invoice.save(update_fields=["status"])

        # ========================================================
        # 🔄 Subscription Logic
        # ========================================================
        if subscription:

            # ----------------------------------------------------
            # UPGRADE FLOW
            # ----------------------------------------------------
            if invoice.billing_reason == "UPGRADE":
                snapshot = invoice.subscription_snapshot or {}
                target_plan_data = snapshot.get("target_plan") or {}
                target_plan_id = target_plan_data.get("id")

                if not target_plan_id:
                    return JsonResponse(
                        {"error": "Upgrade target plan not found in invoice snapshot"},
                        status=400
                    )

                try:
                    target_plan = SubscriptionPlan.objects.get(id=target_plan_id)
                except SubscriptionPlan.DoesNotExist:
                    return JsonResponse(
                        {"error": "Target upgrade plan does not exist"},
                        status=404
                    )

                subscription.plan = target_plan

                if subscription.status != "ACTIVE":
                    subscription.status = "ACTIVE"

                if not subscription.start_date:
                    subscription.start_date = now().date()

                subscription.save(update_fields=["plan", "status", "start_date"])

            # ----------------------------------------------------
            # RENEWAL FLOW
            # ----------------------------------------------------
            elif invoice.billing_reason == "RENEWAL":

                subscription.status = "EXPIRED"
                subscription.save(update_fields=["status"])

                new_subscription = CompanySubscription.objects.create(
                    company=subscription.company,
                    plan=subscription.plan,
                    start_date=now().date(),
                    end_date=subscription.end_date,
                    status="ACTIVE",
                    apps_snapshot=subscription.apps_snapshot,
                )

                subscription = new_subscription

            # ----------------------------------------------------
            # NORMAL ACTIVATION (Onboarding)
            # ----------------------------------------------------
            else:

                if subscription.status != "ACTIVE":
                    subscription.status = "ACTIVE"
                    subscription.start_date = (
                        subscription.start_date or now().date()
                    )

                    subscription.save(
                        update_fields=["status", "start_date"]
                    )

        # ========================================================
        # 🟢 AUTO ACTIVATE COMPANY
        # ========================================================
        company = invoice.company
        if company and not company.is_active:
            company.is_active = True
            company.save(update_fields=["is_active"])

        # ========================================================
        # Notification Center الرسمي فقط بعد نجاح الـ commit
        # ========================================================
        transaction.on_commit(
            lambda: _dispatch_cash_payment_confirmation_notification(
                invoice=invoice,
                payment=payment,
                subscription=subscription,
                actor=request.user,
            )
        )

        # ========================================================
        # ✅ Response
        # ========================================================
        return JsonResponse({
            "success": True,
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "billing_reason": invoice.billing_reason,
            "subscription_status": (
                subscription.status if subscription else None
            ),
            "active_plan": (
                subscription.plan.name
                if subscription and subscription.plan
                else None
            ),
            "company_active": company.is_active if company else False,
            "message": "تم تأكيد الدفع وتفعيل الاشتراك/الترقية بنجاح",
        })

    except Invoice.DoesNotExist:
        return JsonResponse(
            {"error": "Invoice not found"},
            status=404
        )

    except Exception as e:
        logger.exception("confirm_cash_payment failed")
        return JsonResponse(
            {"error": str(e)},
            status=500
        )