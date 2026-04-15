# ============================================================
# 🚀 System/Public Onboarding — Confirm Payment & Activate Company
# Mham Cloud | V3.8 PRODUCT-AWARE
# ============================================================
# ✔ Public Flow Supported
# ✔ No CASH
# ✔ Payment Must Be Confirmed By Gateway First
# ✔ BANK_TRANSFER requires authenticated internal authorized user
# ✔ Create Only (No Merge Ever)
# ✔ Idempotent Draft Locking
# ✔ Strict Username Source = draft.admin_username
# ✔ Collision Protection (Race-Safe)
# ✔ Password Scrub After Success
# ✔ Atomic & Safe
# ✔ Notification Center Only (No direct email / no direct WhatsApp)
# ✔ Explicit Gateway Validation Per Payment Method
# ✔ Safer Invoice Amount Calculation
# ✔ Payment Methods Cleaned (BANK_TRANSFER / CREDIT_CARD / TAMARA)
# ✔ PRODUCT-AWARE Subscription Creation
# ✔ Payment record now keeps gateway reference when available
# ✔ Better idempotent response for already-paid draft
# ✔ FIX: prefer draft.admin_phone for admin onboarding notifications
# ✔ FIX: richer targets/context for onboarding payment confirmation
# ============================================================

from __future__ import annotations

import importlib
import json
import logging
import uuid
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing_center.models import (
    CompanyOnboardingTransaction,
    CompanySubscription,
    Invoice,
    Payment,
)
from company_manager.models import Company, CompanyUser

logger = logging.getLogger(__name__)


# ============================================================
# 🧩 Helpers
# ============================================================

def _json_payload(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


def _generate_invoice_number():
    return f"INV-{uuid.uuid4().hex[:10].upper()}"


def _normalize_username(value: str) -> str:
    if not value:
        return ""
    return value.strip().lower()


def _normalize_email(value: str) -> str:
    if not value:
        return ""
    return value.strip().lower()


def _normalize_text(value: str) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_payment_method(value: str) -> str:
    method = _normalize_text(value).upper()
    if method == "TAP":
        return "CREDIT_CARD"
    return method


def _normalize_gateway_status(value: str) -> str:
    return _normalize_text(value).upper()


def _safe_text(value, default="-"):
    if value is None:
        return default

    value = str(value).strip()
    return value if value else default


def _money_str(value) -> str:
    try:
        return f"{Decimal(value):.2f}"
    except Exception:
        return _safe_text(value, "0.00")


def _invoice_date_str(value) -> str:
    if not value:
        return "-"
    try:
        return value.strftime("%Y-%m-%d")
    except Exception:
        return str(value)


def _build_recipients(draft) -> list[str]:
    recipients: list[str] = []

    candidates = [
        getattr(draft, "admin_email", None),
        getattr(draft, "email", None),
        getattr(getattr(draft, "owner", None), "email", None),
    ]

    for value in candidates:
        email = _normalize_email(value)
        if email and email not in recipients:
            recipients.append(email)

    return recipients


def _get_first_existing_attr(instance, attr_names: list[str], default=""):
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


def _get_draft_admin_phone(draft) -> str:
    return _get_first_existing_attr(
        draft,
        [
            "admin_phone",
            "admin_mobile",
            "admin_mobile_number",
            "admin_whatsapp_number",
            "admin_phone_number",
        ],
        "",
    )


def _get_draft_company_phone(draft) -> str:
    return _get_first_existing_attr(
        draft,
        [
            "phone",
            "mobile",
            "mobile_number",
            "whatsapp_number",
            "phone_number",
        ],
        "",
    )


def _populate_admin_user_phone_from_draft(*, admin_user, draft) -> None:
    """
    ✅ الإصلاح الأساسي:
    نأخذ رقم الأدمن من admin_phone داخل draft أولًا،
    ثم fallback فقط إلى رقم الشركة لو لم يوجد رقم أدمن.
    """
    draft_admin_phone = _safe_text(_get_draft_admin_phone(draft), "")
    fallback_company_phone = _safe_text(_get_draft_company_phone(draft), "")
    selected_phone = draft_admin_phone or fallback_company_phone

    if not selected_phone or not admin_user:
        return

    updated_fields: list[str] = []

    for attr_name in ["phone", "mobile", "mobile_number", "whatsapp_number", "phone_number"]:
        try:
            has_attr = hasattr(admin_user, attr_name)
        except Exception:
            has_attr = False

        if not has_attr:
            continue

        current_value = _safe_text(getattr(admin_user, attr_name, None), "")
        if current_value:
            continue

        try:
            setattr(admin_user, attr_name, selected_phone)
            updated_fields.append(attr_name)
        except Exception:
            logger.exception(
                "Failed setting admin phone attribute. user_id=%s attr=%s",
                getattr(admin_user, "id", None),
                attr_name,
            )

    if updated_fields:
        try:
            admin_user.save(update_fields=updated_fields)
            logger.info(
                "Admin user phone populated from draft successfully. user_id=%s updated_fields=%s source=%s",
                getattr(admin_user, "id", None),
                updated_fields,
                "draft_admin_phone" if draft_admin_phone else "draft_company_phone",
            )
        except Exception:
            logger.exception(
                "Failed saving admin user phone fields from draft. user_id=%s fields=%s",
                getattr(admin_user, "id", None),
                updated_fields,
            )


def _collect_notification_targets(*, company, admin_user, company_owner, draft=None) -> list[dict]:
    """
    تجميع المستهدفين بشكل غني وآمن:
    - الشركة
    - المالك
    - الأدمن الجديد
    - أدمن الـ draft حتى لو لم ينعكس بعد على user/profile
    - بريد/هاتف الشركة من الـ draft
    """
    targets: list[dict] = []
    seen_phones: set[str] = set()
    seen_emails: set[str] = set()

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

    # 1) الشركة من السجل الفعلي
    _append_target(
        phone=_get_best_phone_for_entity(company),
        email=getattr(company, "email", None),
        name=getattr(company, "name", None),
        role="company",
    )

    # 2) المالك
    _append_target(
        phone=_get_best_phone_for_entity(company_owner),
        email=getattr(company_owner, "email", None),
        name=getattr(company_owner, "first_name", None) or getattr(company_owner, "username", None),
        role="owner",
    )

    # 3) الأدمن الجديد من user الفعلي
    _append_target(
        phone=_get_best_phone_for_entity(admin_user),
        email=getattr(admin_user, "email", None),
        name=getattr(admin_user, "first_name", None) or getattr(admin_user, "username", None),
        role="admin",
    )

    # 4) أدمن الـ draft مباشرة لضمان عدم ضياع الإرسال
    if draft is not None:
        _append_target(
            phone=_get_draft_admin_phone(draft),
            email=getattr(draft, "admin_email", None),
            name=getattr(draft, "admin_name", None) or getattr(draft, "admin_username", None),
            role="admin",
        )

        # 5) جهة الشركة من الـ draft
        _append_target(
            phone=_get_draft_company_phone(draft),
            email=getattr(draft, "email", None),
            name=getattr(draft, "company_name", None),
            role="company",
        )

    return targets


def _split_admin_name(full_name: str) -> tuple[str, str]:
    full_name = _normalize_text(full_name)
    if not full_name:
        return "", ""

    parts = full_name.split()
    if len(parts) == 1:
        return parts[0], ""

    return parts[0], " ".join(parts[1:])


def _calculate_invoice_amounts_from_draft(draft):
    base_price = Decimal(getattr(draft, "base_price", 0) or 0)
    discount_amount = Decimal(getattr(draft, "discount_amount", 0) or 0)
    vat_amount = Decimal(getattr(draft, "vat_amount", 0) or 0)
    total_amount = Decimal(getattr(draft, "total_amount", 0) or 0)

    subtotal = base_price - discount_amount
    if subtotal < Decimal("0.00"):
        subtotal = Decimal("0.00")

    if subtotal == Decimal("0.00") and total_amount > Decimal("0.00") and vat_amount >= Decimal("0.00"):
        subtotal = total_amount - vat_amount
        if subtotal < Decimal("0.00"):
            subtotal = Decimal("0.00")

    return {
        "subtotal": subtotal,
        "vat": vat_amount,
        "total": total_amount,
    }


def _resolve_plan_product(plan):
    if not plan:
        return None
    return getattr(plan, "product", None) if getattr(plan, "product_id", None) else None


def _user_can_verify_bank_transfer(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False):
        return True

    if getattr(user, "is_staff", False):
        return True

    try:
        if user.has_perm("billing_center.can_verify_bank_transfer"):
            return True
    except Exception:
        logger.exception("Failed while checking custom permission for user=%s", getattr(user, "id", None))

    try:
        group_names = set(
            user.groups.values_list("name", flat=True)
        )
    except Exception:
        group_names = set()

    allowed_groups = {
        "System Admin",
        "Super Admin",
        "Finance",
        "Billing",
        "Finance Team",
        "Billing Team",
    }

    return bool(group_names.intersection(allowed_groups))


def _validate_gateway_confirmation(*, payment_method: str, gateway_status: str) -> tuple[bool, JsonResponse | None]:
    online_methods = {"CREDIT_CARD", "TAMARA"}
    online_success_statuses = {"SUCCESS", "PAID", "CAPTURED", "APPROVED", "AUTHORIZED"}
    online_pending_statuses = {"PENDING", "INITIATED", "WAITING", "PROCESSING"}
    bank_success_statuses = {"VERIFIED", "CONFIRMED", "PAID", "SUCCESS"}

    if payment_method in online_methods:
        if not gateway_status:
            return False, JsonResponse(
                {
                    "error": "لا يمكن تفعيل الشركة قبل تأكيد البوابة",
                    "details": "gateway_status مطلوب لطرق الدفع الإلكترونية",
                    "field": "gateway_status",
                },
                status=400,
            )

        if gateway_status in online_pending_statuses:
            return False, JsonResponse(
                {
                    "message": "عملية الدفع ما زالت قيد الانتظار",
                    "gateway_status": gateway_status,
                    "payment_method": payment_method,
                    "status": "PAYMENT_PENDING",
                },
                status=202,
            )

        if gateway_status not in online_success_statuses:
            return False, JsonResponse(
                {
                    "error": "لم يتم تأكيد الدفع من البوابة بعد",
                    "gateway_status": gateway_status,
                    "payment_method": payment_method,
                },
                status=400,
            )

        return True, None

    if payment_method == "BANK_TRANSFER":
        if not gateway_status:
            return False, JsonResponse(
                {
                    "error": "لا يمكن تفعيل الشركة قبل التحقق من التحويل البنكي",
                    "details": "يجب إرسال gateway_status صريح مثل VERIFIED أو CONFIRMED",
                    "field": "gateway_status",
                },
                status=400,
            )

        if gateway_status not in bank_success_statuses:
            return False, JsonResponse(
                {
                    "error": "التحويل البنكي لم يتم تأكيده بعد",
                    "gateway_status": gateway_status,
                    "payment_method": payment_method,
                },
                status=400,
            )

        return True, None

    return False, JsonResponse(
        {
            "error": "طريقة الدفع غير مدعومة",
            "field": "payment_method",
        },
        status=400,
    )


def _generate_invoice_pdf_bytes(*, company, subscription, invoice, admin_user, payment_method) -> bytes | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        _, height = A4

        y = height - 50

        pdf.setTitle(f"Invoice {invoice.invoice_number}")

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(40, y, "Mham Cloud")
        y -= 30

        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(40, y, "Payment Confirmation Invoice")
        y -= 30

        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, y, f"Invoice Number: {_safe_text(invoice.invoice_number)}")
        y -= 18
        pdf.drawString(40, y, f"Issue Date: {_invoice_date_str(invoice.issue_date)}")
        y -= 18
        pdf.drawString(40, y, f"Company: {_safe_text(company.name)}")
        y -= 18
        pdf.drawString(40, y, f"Admin Username: {_safe_text(admin_user.username)}")
        y -= 18
        pdf.drawString(40, y, f"Admin Email: {_safe_text(admin_user.email)}")
        y -= 18
        pdf.drawString(40, y, f"Plan: {_safe_text(getattr(subscription.plan, 'name', None))}")
        y -= 18
        pdf.drawString(40, y, f"Product: {_safe_text(getattr(getattr(subscription, 'resolved_product', None), 'code', None))}")
        y -= 18
        pdf.drawString(40, y, f"Subscription Status: {_safe_text(subscription.status)}")
        y -= 18
        pdf.drawString(40, y, f"Start Date: {_invoice_date_str(subscription.start_date)}")
        y -= 18
        pdf.drawString(40, y, f"End Date: {_invoice_date_str(subscription.end_date)}")
        y -= 30

        subtotal_value = getattr(invoice, "subtotal", None)
        vat_value = getattr(invoice, "vat", None)
        total_value = getattr(invoice, "total_amount", None)

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, "Invoice Totals")
        y -= 22

        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, y, f"Subtotal: {_money_str(subtotal_value)} SAR")
        y -= 18
        pdf.drawString(40, y, f"VAT: {_money_str(vat_value)} SAR")
        y -= 18
        pdf.drawString(40, y, f"Total: {_money_str(total_value)} SAR")
        y -= 18
        pdf.drawString(40, y, f"Status: {_safe_text(invoice.status)}")
        y -= 18
        pdf.drawString(40, y, f"Payment Method: {_safe_text(payment_method)}")
        y -= 30

        pdf.setFont("Helvetica-Oblique", 9)
        pdf.drawString(40, y, "Generated automatically by Mham Cloud.")
        y -= 16
        pdf.drawString(40, y, "This document is attached to the payment confirmation email.")

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        return buffer.getvalue()

    except Exception:
        logger.exception(
            "Failed to generate invoice PDF attachment. invoice_id=%s invoice_number=%s",
            getattr(invoice, "id", None),
            getattr(invoice, "invoice_number", None),
        )
        return None


def _load_onboarding_notification_module():
    candidate_modules = [
        "notification_center.services_onboarding",
        "notification_center.services_company",
    ]

    for module_path in candidate_modules:
        try:
            return importlib.import_module(module_path)
        except Exception:
            continue

    return None


def _build_payment_confirmation_context(
    *,
    draft,
    company,
    subscription,
    invoice,
    admin_user,
    payment_method,
    company_owner,
    gateway_status,
    gateway_transaction_id,
) -> dict:
    payment_method_label = "بطاقة ائتمانية (Tap)" if payment_method == "CREDIT_CARD" else _safe_text(payment_method)
    pdf_bytes = _generate_invoice_pdf_bytes(
        company=company,
        subscription=subscription,
        invoice=invoice,
        admin_user=admin_user,
        payment_method=payment_method,
    )

    targets = _collect_notification_targets(
        company=company,
        admin_user=admin_user,
        company_owner=company_owner,
        draft=draft,
    )

    resolved_product = getattr(subscription, "resolved_product", None)
    draft_admin_phone = _safe_text(_get_draft_admin_phone(draft), "")
    draft_company_phone = _safe_text(_get_draft_company_phone(draft), "")

    return {
        "draft_id": getattr(draft, "id", None),
        "company_id": getattr(company, "id", None),
        "company_name": _safe_text(company.name),
        "company_email": _safe_text(company.email),
        "company_phone": _safe_text(company.phone),
        "company_draft_phone": draft_company_phone,
        "commercial_number": _safe_text(company.commercial_number),
        "city": _safe_text(company.city),
        "company_owner_id": getattr(company_owner, "id", None),
        "company_owner_email": _safe_text(getattr(company_owner, "email", None)),
        "company_owner_phone": _safe_text(_get_best_phone_for_entity(company_owner), ""),
        "admin_user_id": getattr(admin_user, "id", None),
        "admin_name": _safe_text(admin_user.first_name or admin_user.username),
        "admin_username": _safe_text(admin_user.username),
        "admin_email": _safe_text(admin_user.email),
        "admin_phone": _safe_text(_get_best_phone_for_entity(admin_user), "") or draft_admin_phone,
        "admin_draft_phone": draft_admin_phone,
        "product_id": getattr(resolved_product, "id", None),
        "product_code": _safe_text(getattr(resolved_product, "code", None)),
        "product_name": _safe_text(getattr(resolved_product, "name", None)),
        "plan_name": _safe_text(getattr(subscription.plan, "name", None)),
        "subscription_id": getattr(subscription, "id", None),
        "subscription_status": _safe_text(subscription.status),
        "subscription_start_date": _invoice_date_str(subscription.start_date),
        "subscription_end_date": _invoice_date_str(subscription.end_date),
        "invoice_id": getattr(invoice, "id", None),
        "invoice_number": _safe_text(invoice.invoice_number),
        "invoice_status": _safe_text(invoice.status),
        "invoice_issue_date": _invoice_date_str(invoice.issue_date),
        "subtotal_amount": _money_str(getattr(invoice, "subtotal", None)),
        "vat_amount": _money_str(getattr(invoice, "vat", None)),
        "total_amount": _money_str(getattr(invoice, "total_amount", None)),
        "payment_method": payment_method,
        "payment_method_label": payment_method_label,
        "gateway_status": _safe_text(gateway_status, ""),
        "gateway_transaction_id": _safe_text(gateway_transaction_id, ""),
        "recipients": _build_recipients(draft),
        "targets": targets,
        "invoice_pdf_bytes": pdf_bytes,
        "invoice_pdf_filename": f"{_safe_text(invoice.invoice_number, 'invoice')}.pdf",
    }


def _dispatch_payment_confirmation_notification(
    *,
    actor,
    draft,
    company,
    subscription,
    invoice,
    admin_user,
    payment_method,
    company_owner,
    gateway_status,
    gateway_transaction_id,
) -> None:
    services_module = _load_onboarding_notification_module()

    if not services_module:
        logger.warning(
            "Onboarding notification service module not found. draft_id=%s invoice_id=%s company_id=%s",
            getattr(draft, "id", None),
            getattr(invoice, "id", None),
            getattr(company, "id", None),
        )
        return

    candidate_function_names = [
        "notify_onboarding_payment_confirmed",
        "notify_payment_confirmed_company_activated",
        "send_onboarding_payment_confirmation_notification",
        "send_payment_confirmed_company_activated_notification",
    ]

    notify_func = None
    for func_name in candidate_function_names:
        notify_func = getattr(services_module, func_name, None)
        if callable(notify_func):
            break

    if not callable(notify_func):
        logger.warning(
            "Onboarding payment confirmation notification function not found. checked=%s",
            ", ".join(candidate_function_names),
        )
        return

    context = _build_payment_confirmation_context(
        draft=draft,
        company=company,
        subscription=subscription,
        invoice=invoice,
        admin_user=admin_user,
        payment_method=payment_method,
        company_owner=company_owner,
        gateway_status=gateway_status,
        gateway_transaction_id=gateway_transaction_id,
    )

    try:
        notify_func(
            actor=actor,
            company=company,
            draft=draft,
            subscription=subscription,
            invoice=invoice,
            admin_user=admin_user,
            target_user=admin_user,
            payment_method=payment_method,
            gateway_status=gateway_status,
            gateway_transaction_id=gateway_transaction_id,
            extra_context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(
            actor=actor,
            company=company,
            draft=draft,
            subscription=subscription,
            invoice=invoice,
            admin_user=admin_user,
            target_user=admin_user,
            payment_method=payment_method,
            gateway_status=gateway_status,
            gateway_transaction_id=gateway_transaction_id,
            context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(
            company=company,
            invoice=invoice,
            subscription=subscription,
            admin_user=admin_user,
            payment_method=payment_method,
        )
        return
    except Exception:
        logger.exception(
            "Failed while dispatching onboarding payment confirmation notification. "
            "draft_id=%s invoice_id=%s company_id=%s",
            getattr(draft, "id", None),
            getattr(invoice, "id", None),
            getattr(company, "id", None),
        )
        return


def _build_already_paid_response(*, draft):
    """
    إرجاع استجابة idempotent واضحة بدل إرجاع خطأ مجرد،
    حتى يتمكن الفرونت من إكمال تجربة المستخدم بسلاسة عند
    إعادة تحميل صفحة النجاح أو وصول webhook ثم محاولة تأكيد ثانية.
    """
    company = (
        Company.objects
        .filter(commercial_number=draft.commercial_number)
        .order_by("-id")
        .first()
    )

    if company:
        subscription = (
            CompanySubscription.objects
            .select_related("plan", "product")
            .filter(company=company)
            .order_by("-id")
            .first()
        )
        invoice = (
            Invoice.objects
            .filter(company=company)
            .order_by("-id")
            .first()
        )

        return {
            "message": "تم تأكيد هذه العملية سابقًا",
            "status": "already_confirmed",
            "company_id": company.id,
            "company_name": company.name,
            "admin_username": _normalize_username(getattr(draft, "admin_username", "")),
            "payment_method": _normalize_payment_method(getattr(draft, "payment_method", "")),
            "gateway_status": "PAID",
            "gateway_transaction_id": None,
            "subscription": {
                "product": getattr(getattr(subscription, "product", None), "code", None) if subscription else None,
                "plan": getattr(getattr(subscription, "plan", None), "name", None) if subscription else None,
                "status": getattr(subscription, "status", None) if subscription else None,
                "start_date": getattr(subscription, "start_date", None) if subscription else None,
                "end_date": getattr(subscription, "end_date", None) if subscription else None,
            },
            "invoice_id": getattr(invoice, "id", None),
        }

    return {
        "message": "تم تأكيد هذه العملية سابقًا",
        "status": "already_confirmed",
        "company_id": None,
        "company_name": None,
        "admin_username": _normalize_username(getattr(draft, "admin_username", "")),
        "payment_method": _normalize_payment_method(getattr(draft, "payment_method", "")),
        "gateway_status": "PAID",
        "gateway_transaction_id": None,
        "subscription": {
            "product": None,
            "plan": None,
            "status": None,
            "start_date": None,
            "end_date": None,
        },
        "invoice_id": None,
    }


# ============================================================
# ✅ API — Confirm Onboarding Payment
# ============================================================

@require_POST
@csrf_exempt
def confirm_onboarding_payment(request):
    payload = _json_payload(request)

    if not payload:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    draft_id = payload.get("draft_id")
    if not draft_id:
        return JsonResponse({"error": "draft_id مطلوب"}, status=400)

    payment_method = _normalize_payment_method(payload.get("payment_method"))
    gateway_status = _normalize_gateway_status(payload.get("gateway_status"))
    gateway_transaction_id = _normalize_text(payload.get("gateway_transaction_id"))

    if not payment_method:
        return JsonResponse(
            {
                "error": "payment_method مطلوب",
                "field": "payment_method",
            },
            status=400,
        )

    allowed_payment_methods = {
        "BANK_TRANSFER",
        "CREDIT_CARD",
        "TAMARA",
    }

    if payment_method not in allowed_payment_methods:
        return JsonResponse(
            {
                "error": "طريقة الدفع غير مدعومة",
                "field": "payment_method",
            },
            status=400,
        )

    gateway_ok, gateway_response = _validate_gateway_confirmation(
        payment_method=payment_method,
        gateway_status=gateway_status,
    )
    if not gateway_ok:
        return gateway_response

    if payment_method == "BANK_TRANSFER":
        if not _user_can_verify_bank_transfer(getattr(request, "user", None)):
            return JsonResponse(
                {
                    "error": "غير مصرح لك باعتماد التحويل البنكي",
                    "details": "هذه العملية متاحة فقط للمستخدمين الداخليين المخولين",
                },
                status=403,
            )

    User = get_user_model()

    with transaction.atomic():
        try:
            draft = (
                CompanyOnboardingTransaction.objects
                .select_for_update()
                .select_related("plan__product", "owner")
                .get(id=draft_id)
            )
        except CompanyOnboardingTransaction.DoesNotExist:
            return JsonResponse({"error": "المسودة غير موجودة"}, status=404)

        if draft.status == "PAID":
            return JsonResponse(
                _build_already_paid_response(draft=draft),
                status=409,
            )

        if draft.status not in {"DRAFT", "CONFIRMED", "PENDING_PAYMENT"}:
            return JsonResponse(
                {
                    "error": "حالة المسودة لا تسمح بتأكيد الدفع",
                    "draft_status": draft.status,
                },
                status=409,
            )

        if not draft.plan:
            return JsonResponse({"error": "المسودة لا تحتوي على باقة صالحة"}, status=400)

        plan_product = _resolve_plan_product(draft.plan)
        if not plan_product:
            return JsonResponse(
                {
                    "error": "الباقة الحالية غير مرتبطة بأي منتج",
                    "field": "plan.product",
                },
                status=400,
            )

        if draft.commercial_number:
            exists = Company.objects.filter(
                commercial_number=draft.commercial_number
            ).exists()

            if exists:
                return JsonResponse(
                    {
                        "error": "شركة بنفس السجل التجاري موجودة مسبقًا",
                        "commercial_number": draft.commercial_number,
                    },
                    status=409,
                )

        admin_username = _normalize_username(draft.admin_username)
        admin_email = _normalize_email(draft.admin_email)
        admin_password = _normalize_text(draft.admin_password)
        admin_full_name = _normalize_text(draft.admin_name)

        if not admin_username:
            return JsonResponse({"error": "اسم المستخدم غير موجود في المسودة"}, status=400)

        if not admin_password:
            return JsonResponse({"error": "كلمة مرور المسؤول غير موجودة في المسودة"}, status=400)

        first_name, last_name = _split_admin_name(admin_full_name)

        try:
            admin_user = User.objects.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )
        except IntegrityError:
            return JsonResponse(
                {
                    "error": "اسم المستخدم مستخدم مسبقًا",
                    "username": admin_username,
                },
                status=409,
            )

        _populate_admin_user_phone_from_draft(
            admin_user=admin_user,
            draft=draft,
        )

        national_address = draft.national_address or {}
        company_owner = draft.owner if getattr(draft, "owner_id", None) else admin_user

        company = Company.objects.create(
            owner=company_owner,
            commercial_number=draft.commercial_number,
            name=draft.company_name,
            city=draft.city,
            vat_number=draft.tax_number,
            phone=draft.phone,
            email=draft.email,
            building_number=national_address.get("building_no"),
            street=national_address.get("street"),
            district=national_address.get("district"),
            postal_code=national_address.get("postal_code"),
            short_address=national_address.get("short_address"),
            is_active=True,
        )

        CompanyUser.objects.create(
            user=admin_user,
            company=company,
            role="admin",
            is_active=True,
        )

        subscription = CompanySubscription.objects.create(
            company=company,
            product=plan_product,
            plan=draft.plan,
            start_date=draft.start_date,
            end_date=draft.end_date,
            status="ACTIVE",
            apps_snapshot=draft.plan.apps if isinstance(draft.plan.apps, list) else [],
        )

        invoice_amounts = _calculate_invoice_amounts_from_draft(draft)

        invoice = Invoice.objects.create(
            company=company,
            subscription=subscription,
            invoice_number=_generate_invoice_number(),
            issue_date=draft.start_date,
            subtotal=invoice_amounts["subtotal"],
            vat=invoice_amounts["vat"],
            total_amount=invoice_amounts["total"],
            status="PAID",
            is_approved=True,
            approved_at=timezone.now(),
            subscription_snapshot={
                "type": "NEW_SUBSCRIPTION",
                "product": {
                    "id": plan_product.id,
                    "code": plan_product.code,
                    "name": plan_product.name,
                },
                "plan": {
                    "id": draft.plan.id,
                    "name": draft.plan.name,
                },
                "duration": draft.duration,
            },
        )

        payment_kwargs = {
            "invoice": invoice,
            "amount": draft.total_amount,
            "method": payment_method,
            "created_by": company_owner,
        }

        if gateway_transaction_id:
            payment_kwargs["reference_number"] = gateway_transaction_id

        Payment.objects.create(**payment_kwargs)

        draft.status = "PAID"
        draft.payment_method = payment_method
        draft.admin_password = ""
        draft.save(update_fields=["status", "payment_method", "admin_password"])

        transaction.on_commit(
            lambda: _dispatch_payment_confirmation_notification(
                actor=getattr(request, "user", None),
                draft=draft,
                company=company,
                subscription=subscription,
                invoice=invoice,
                admin_user=admin_user,
                payment_method=payment_method,
                company_owner=company_owner,
                gateway_status=gateway_status,
                gateway_transaction_id=gateway_transaction_id,
            )
        )

    return JsonResponse(
        {
            "company_id": company.id,
            "company_name": company.name,
            "admin_username": admin_user.username,
            "payment_method": payment_method,
            "gateway_status": gateway_status,
            "gateway_transaction_id": gateway_transaction_id or None,
            "subscription": {
                "product": plan_product.code,
                "plan": subscription.plan.name,
                "status": subscription.status,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
            },
            "invoice_id": invoice.id,
        },
        status=200,
    )