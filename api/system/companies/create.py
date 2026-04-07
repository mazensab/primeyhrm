# ====================================================================
# 🏢 Company Create API
# Mham Cloud — System Companies
# ====================================================================

from __future__ import annotations

import json
import logging

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from billing_center.models import (
    CompanySubscription,
    AccountSubscription,
)

from company_manager.models import (
    Company,
    CompanyUser,
    CompanyRole,
)

from notification_center import services_company as company_notification_services

from .roles_blueprint import DEFAULT_COMPANY_ROLES

logger = logging.getLogger(__name__)


# ====================================================================
# 🧩 Helpers
# ====================================================================

def _safe_value(value):
    return value if value not in (None, "") else "-"


def _build_company_created_context(*, user, company) -> dict:
    """
    تجهيز context رسمي موحد لحدث إنشاء الشركة.
    """
    owner_name = (
        user.get_full_name().strip()
        if hasattr(user, "get_full_name") and user.get_full_name()
        else getattr(user, "username", "User")
    )

    return {
        "company_id": company.id,
        "company_name": _safe_value(company.name),
        "company_email": _safe_value(company.email),
        "company_phone": _safe_value(company.phone),
        "owner_id": getattr(user, "id", None),
        "owner_name": _safe_value(owner_name),
        "owner_email": _safe_value(getattr(user, "email", None)),
    }


def _dispatch_company_created_notification(*, user, company) -> None:
    """
    تمرير إشعار إنشاء الشركة إلى الطبقة الرسمية فقط.
    هذا الملف لم يعد يحتوي أي إرسال مباشر للبريد.
    """

    candidate_function_names = [
        "notify_company_created",
        "notify_new_company_created",
        "send_company_created_notification",
        "send_company_creation_notification",
    ]

    notify_func = None
    for func_name in candidate_function_names:
        notify_func = getattr(company_notification_services, func_name, None)
        if callable(notify_func):
            break

    if not callable(notify_func):
        logger.warning(
            "Company create notification service not found in notification_center.services_company. "
            "company_id=%s checked=%s",
            getattr(company, "id", None),
            ", ".join(candidate_function_names),
        )
        return

    context = _build_company_created_context(user=user, company=company)

    try:
        # --------------------------------------------------------
        # المحاولة الأساسية: الواجهة الأحدث المتوقعة
        # --------------------------------------------------------
        notify_func(
            company=company,
            actor=user,
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
            actor=user,
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
            "Failed while dispatching company created notification. company_id=%s user_id=%s",
            getattr(company, "id", None),
            getattr(user, "id", None),
        )
        return


# ====================================================================
# 🏢 Create Company (Paid Subscription Required)
# ====================================================================

@login_required
@require_POST
def company_create(request):

    user = request.user

    # ============================================================
    # 📥 Payload (JSON + FORM SAFE)
    # ============================================================
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = request.POST

    name = payload.get("name")
    email = payload.get("email")
    phone = payload.get("phone")

    if not name:
        return JsonResponse(
            {"error": "اسم الشركة مطلوب"},
            status=400,
        )

    # ============================================================
    # 🔒 Active Account Subscription
    # ============================================================
    sub = (
        AccountSubscription.objects
        .filter(owner=user, status="ACTIVE")
        .select_related("plan")
        .first()
    )

    if not sub or not sub.plan:
        return JsonResponse(
            {"error": "لا يوجد اشتراك مدفوع نشط"},
            status=403,
        )

    # ============================================================
    # 🧮 Company Limit
    # ============================================================
    used_companies = (
        CompanyUser.objects
        .filter(user=user, is_active=True)
        .values("company")
        .distinct()
        .count()
    )

    if used_companies >= sub.plan.max_companies:
        return JsonResponse(
            {"error": "تم الوصول للحد الأقصى المسموح من الشركات"},
            status=403,
        )

    # ============================================================
    # 🏢 Atomic Creation
    # ============================================================
    with transaction.atomic():

        # --------------------------------------------------------
        # 1️⃣ Create Company
        # --------------------------------------------------------
        company = Company.objects.create(
            name=name,
            email=email,
            phone=phone,
            is_active=True,
            owner=user,
        )

        # --------------------------------------------------------
        # 2️⃣ Link Owner
        # --------------------------------------------------------
        CompanyUser.objects.create(
            user=user,
            company=company,
            role="owner",
            is_active=True,
        )

        # --------------------------------------------------------
        # 3️⃣ Subscription Stub
        # --------------------------------------------------------
        CompanySubscription.objects.get_or_create(
            company=company,
            defaults={
                "status": "PENDING"
            }
        )

        # --------------------------------------------------------
        # 4️⃣ Default Company Roles
        # --------------------------------------------------------
        for role_data in DEFAULT_COMPANY_ROLES:
            CompanyRole.objects.create(
                company=company,
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
                is_system_role=role_data["is_system_role"],
            )

        # --------------------------------------------------------
        # 5️⃣ Notification Center الرسمي فقط
        # --------------------------------------------------------
        transaction.on_commit(
            lambda: _dispatch_company_created_notification(
                user=user,
                company=company,
            )
        )

    # ============================================================
    # ✅ Success Response
    # ============================================================
    return JsonResponse(
        {
            "id": company.id,
            "name": company.name,
            "owner": {
                "id": user.id,
                "email": user.email,
            },
        },
        status=201,
    )