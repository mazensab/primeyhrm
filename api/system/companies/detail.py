from __future__ import annotations

import json
import logging

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing_center.models import CompanySubscription
from billing_center.models import Invoice, Payment
from company_manager.models import Company
from notification_center import services_company as company_notification_services

logger = logging.getLogger(__name__)


# ================================================================
# 🧩 Helpers
# ================================================================
def _json_payload(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


def _normalize_text(value):
    if value is None:
        return None

    value = str(value).strip()
    return value if value else ""


def _safe_value(value):
    return value if value not in (None, "") else "-"


def _serialize_company_payload(company: Company) -> dict:
    """
    توحيد إخراج بيانات الشركة داخل الاستجابة.
    """
    return {
        "id": company.id,
        "name": company.name,
        "commercial_number": company.commercial_number,
        "vat_number": company.vat_number,
        "phone": company.phone,
        "email": company.email,
        "national_address": {
            "building_number": company.building_number,
            "street": company.street,
            "district": company.district,
            "city": company.city,
            "postal_code": company.postal_code,
            "short_address": company.short_address,
        },
    }


def _build_company_update_context(company: Company) -> dict:
    """
    تجهيز context رسمي موحد لحدث تحديث بيانات الشركة.
    """
    return {
        "company_id": company.id,
        "company_name": _safe_value(company.name),
        "company_email": _safe_value(company.email),
        "company_phone": _safe_value(company.phone),
        "commercial_number": _safe_value(company.commercial_number),
        "vat_number": _safe_value(company.vat_number),
        "building_number": _safe_value(company.building_number),
        "street": _safe_value(company.street),
        "district": _safe_value(company.district),
        "city": _safe_value(company.city),
        "postal_code": _safe_value(company.postal_code),
        "short_address": _safe_value(company.short_address),
    }


def _dispatch_company_updated_notification(*, company: Company, actor=None) -> None:
    """
    تمرير إشعار تحديث بيانات الشركة إلى الطبقة الرسمية فقط.
    هذا الملف لم يعد يحتوي أي إرسال مباشر للبريد.
    """

    candidate_function_names = [
        "notify_company_updated",
        "notify_company_profile_updated",
        "notify_company_information_updated",
        "send_company_updated_notification",
    ]

    notify_func = None
    for func_name in candidate_function_names:
        notify_func = getattr(company_notification_services, func_name, None)
        if callable(notify_func):
            break

    if not callable(notify_func):
        logger.warning(
            "Company update notification service not found in notification_center.services_company. "
            "company_id=%s checked=%s",
            getattr(company, "id", None),
            ", ".join(candidate_function_names),
        )
        return

    context = _build_company_update_context(company)

    try:
        # --------------------------------------------------------
        # المحاولة الأساسية: الواجهة الأحدث المتوقعة
        # --------------------------------------------------------
        notify_func(
            company=company,
            actor=actor,
            extra_context=context,
        )
        return

    except TypeError:
        pass

    try:
        # --------------------------------------------------------
        # Fallback: بعض الإصدارات قد تستخدم context بدل extra_context
        # --------------------------------------------------------
        notify_func(
            company=company,
            actor=actor,
            context=context,
        )
        return

    except TypeError:
        pass

    try:
        # --------------------------------------------------------
        # Fallback: بعض الإصدارات قد تكتفي بالشركة فقط
        # --------------------------------------------------------
        notify_func(company=company)
        return

    except Exception:
        logger.exception(
            "Failed while dispatching company updated notification. company_id=%s",
            getattr(company, "id", None),
        )
        return


# ================================================================
# 🏢 System API — Company Details
# ================================================================
@login_required
def system_company_detail(request, company_id):

    company = get_object_or_404(Company, id=company_id)

    subscription = (
        CompanySubscription.objects
        .filter(company=company)
        .select_related("plan")
        .order_by("-id")
        .first()
    )

    data = {
        # Company
        "company": {
            "id": company.id,
            "name": company.name,
            "is_active": company.is_active,
            "created_at": company.created_at,

            # ------------------------------------------------
            # Company Information
            # ------------------------------------------------
            "commercial_number": company.commercial_number,
            "vat_number": company.vat_number,
            "phone": company.phone,
            "email": company.email,

            # ------------------------------------------------
            # National Address
            # ------------------------------------------------
            "national_address": {
                "building_number": company.building_number,
                "street": company.street,
                "district": company.district,
                "city": company.city,
                "postal_code": company.postal_code,
                "short_address": company.short_address,
            },
        },

        # Owner
        "owner": {
            "email": company.owner.email if company.owner else None
        },

        # Subscription
        "subscription": {
            "plan": subscription.plan.name if subscription and subscription.plan else None,
            "status": subscription.status if subscription else None,
        },

        # Users
        "users_count": company.company_users.count(),
    }

    return JsonResponse(data)


# ================================================================
# ✏️ System API — Update Company Information
# ================================================================
@login_required
@require_POST
@csrf_exempt
def system_company_update(request, company_id):

    company = get_object_or_404(Company, id=company_id)
    payload = _json_payload(request)

    if not payload:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    national_address = payload.get("national_address") or {}

    company.name = _normalize_text(payload.get("name")) or company.name
    company.commercial_number = _normalize_text(payload.get("commercial_number"))
    company.vat_number = _normalize_text(payload.get("vat_number"))
    company.phone = _normalize_text(payload.get("phone"))
    company.email = _normalize_text(payload.get("email"))

    company.building_number = _normalize_text(
        national_address.get("building_number")
    )
    company.street = _normalize_text(
        national_address.get("street")
    )
    company.district = _normalize_text(
        national_address.get("district")
    )
    company.city = _normalize_text(
        national_address.get("city")
    )
    company.postal_code = _normalize_text(
        national_address.get("postal_code")
    )
    company.short_address = _normalize_text(
        national_address.get("short_address")
    )

    company.save(update_fields=[
        "name",
        "commercial_number",
        "vat_number",
        "phone",
        "email",
        "building_number",
        "street",
        "district",
        "city",
        "postal_code",
        "short_address",
    ])

    # ------------------------------------------------------------
    # ✅ Notification Center الرسمي فقط
    # بعد نجاح الـ commit
    # ------------------------------------------------------------
    transaction.on_commit(
        lambda: _dispatch_company_updated_notification(
            company=company,
            actor=request.user,
        )
    )

    return JsonResponse({
        "success": True,
        "message": "تم تحديث بيانات الشركة بنجاح",
        "company": _serialize_company_payload(company),
    })


# ================================================================
# 📊 System API — Company Activity Logs
# ================================================================
@login_required
def system_company_activity(request, company_id):

    company = get_object_or_404(Company, id=company_id)

    logs = []

    # ------------------------------------------------
    # Invoices
    # ------------------------------------------------
    invoices = (
        Invoice.objects
        .filter(company=company)
        .order_by("-id")[:20]
    )

    for inv in invoices:

        invoice_number = getattr(inv, "invoice_number", None) or getattr(inv, "number", f"Invoice #{inv.id}")
        total_amount = getattr(inv, "total_amount", None)
        currency = getattr(inv, "currency", "SAR")

        logs.append({
            "type": "invoice",
            "title": "Invoice Created",
            "message": invoice_number,
            "amount": f"{total_amount} {currency}" if total_amount else None,
            "created_at": getattr(inv, "issue_date", None),
        })

    # ------------------------------------------------
    # Payments
    # ------------------------------------------------
    payments = (
        Payment.objects
        .filter(invoice__company=company)
        .select_related("invoice")
        .order_by("-id")[:20]
    )

    for pay in payments:

        invoice_number = getattr(pay.invoice, "invoice_number", None) if pay.invoice else None
        amount = getattr(pay, "amount", None)
        currency = getattr(pay, "currency", "SAR")

        logs.append({
            "type": "payment",
            "title": "Payment Received",
            "message": invoice_number,
            "amount": f"{amount} {currency}" if amount else None,
            "created_at": getattr(pay, "paid_at", None),
        })

    # ------------------------------------------------
    # Sort Logs
    # ------------------------------------------------
    logs = sorted(
        logs,
        key=lambda x: str(x["created_at"]) if x["created_at"] else "",
        reverse=True,
    )

    return JsonResponse({
        "status": "success",
        "data": {
            "results": logs[:20]
        }
    })