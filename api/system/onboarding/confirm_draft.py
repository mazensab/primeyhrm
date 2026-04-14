# ============================================================
# 📂 api/system/onboarding/confirm_draft.py
# Mham Cloud
# Confirm Draft — Notification Center Clean
# ============================================================

from __future__ import annotations

import importlib
import json
import logging

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from billing_center.models import CompanyOnboardingTransaction

logger = logging.getLogger(__name__)


# ============================================================
# 🧩 Shared Helpers
# ============================================================

def _safe_text(value, default="-"):
    if value is None:
        return default
    value = str(value).strip()
    return value or default


def _normalize_email(value: str) -> str:
    if not value:
        return ""
    return str(value).strip().lower()


def _get_draft_recipient(draft) -> str | None:
    """
    محاولة استخراج بريد المستلم من حقول الـ draft المتوقعة
    بدون كسر أي بنية حالية.
    """
    possible_fields = [
        "admin_email",
        "email",
        "owner_email",
        "company_email",
    ]

    for field_name in possible_fields:
        value = getattr(draft, field_name, None)
        if value:
            value = str(value).strip()
            if value:
                return value

    return None


def _get_owner_name(draft) -> str:
    """
    محاولة استخراج اسم مناسب من الـ draft.
    """
    possible_fields = [
        "admin_full_name",
        "admin_name",
        "full_name",
        "owner_name",
        "admin_username",
        "username",
        "company_name",
    ]

    for field_name in possible_fields:
        value = getattr(draft, field_name, None)
        if value:
            value = str(value).strip()
            if value:
                return value

    return "User"


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


# ============================================================
# Notification Helpers
# ============================================================

def _load_onboarding_notification_module():
    """
    تحميل مرن لطبقة onboarding الرسمية إن كانت موجودة،
    مع fallback إلى company services لو كان المشروع ما زال في مرحلة انتقالية.
    """
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


def _build_confirm_draft_recipients(draft) -> list[str]:
    recipients: list[str] = []

    candidates = [
        getattr(draft, "admin_email", None),
        getattr(draft, "email", None),
        getattr(getattr(draft, "owner", None), "email", None),
        getattr(draft, "owner_email", None),
        getattr(draft, "company_email", None),
    ]

    for value in candidates:
        email = _normalize_email(value)
        if email and email not in recipients:
            recipients.append(email)

    return recipients


def _collect_confirm_draft_targets(draft) -> list[dict]:
    """
    تجميع مستهدفي الإشعار بشكل آمن وبدون تكرار.
    """
    seen_phones: set[str] = set()
    seen_emails: set[str] = set()
    targets: list[dict] = []

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

    # 1) الشركة / الطلب
    _append_target(
        phone=_safe_text(getattr(draft, "phone", None), ""),
        email=_get_draft_recipient(draft),
        name=_get_owner_name(draft),
        role="company",
    )

    # 2) المالك الداخلي إن وجد
    owner = getattr(draft, "owner", None)
    if owner:
        _append_target(
            phone=_get_best_phone_for_entity(owner),
            email=getattr(owner, "email", None),
            name=getattr(owner, "first_name", None) or getattr(owner, "username", None) or "Owner",
            role="owner",
        )

    return targets


def _build_confirm_draft_context(draft) -> dict:
    return {
        "draft_id": getattr(draft, "id", None),
        "company_name": _safe_text(getattr(draft, "company_name", None)),
        "plan_name": _safe_text(getattr(getattr(draft, "plan", None), "name", None)),
        "duration": _safe_text(getattr(draft, "duration", None)),
        "total_amount": _safe_text(getattr(draft, "total_amount", None)),
        "status": _safe_text(getattr(draft, "status", None)),
        "owner_name": _get_owner_name(draft),
        "recipients": _build_confirm_draft_recipients(draft),
        "targets": _collect_confirm_draft_targets(draft),
        "owner_user_id": getattr(getattr(draft, "owner", None), "id", None),
        "owner_email": _safe_text(getattr(getattr(draft, "owner", None), "email", None), ""),
    }


def _dispatch_confirm_draft_notification(*, draft) -> None:
    """
    تمرير إشعار تأكيد الطلب إلى الطبقة الرسمية فقط.
    لا يوجد بريد مباشر ولا واتساب مباشر داخل هذا الملف بعد الآن.
    """
    services_module = _load_onboarding_notification_module()

    if not services_module:
        logger.warning(
            "Onboarding notification service module not found. draft_id=%s",
            getattr(draft, "id", None),
        )
        return

    candidate_function_names = [
        "notify_onboarding_draft_confirmed",
        "notify_draft_confirmed",
        "send_onboarding_draft_confirmed_notification",
        "send_draft_confirmed_notification",
    ]

    notify_func = None
    for func_name in candidate_function_names:
        notify_func = getattr(services_module, func_name, None)
        if callable(notify_func):
            break

    if not callable(notify_func):
        logger.warning(
            "Onboarding draft confirmed notification function not found. checked=%s",
            ", ".join(candidate_function_names),
        )
        return

    context = _build_confirm_draft_context(draft)

    try:
        notify_func(
            draft=draft,
            extra_context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(
            draft=draft,
            context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(draft=draft)
        return
    except Exception:
        logger.exception(
            "Failed while dispatching onboarding draft confirmed notification. draft_id=%s",
            getattr(draft, "id", None),
        )
        return


def _build_draft_response(*, draft, message: str, state: str) -> dict:
    return {
        "message": message,
        "state": state,
        "draft": {
            "id": draft.id,
            "company_name": draft.company_name,
            "plan": draft.plan.name if draft.plan else None,
            "duration": draft.duration,
            "total_amount": float(draft.total_amount or 0),
            "status": draft.status,
        },
    }


# ============================================================
# API — Confirm Draft
# URL: /api/system/onboarding/confirm-draft/
# ============================================================

@require_POST
def confirm_draft(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        draft_id = data.get("draft_id")

        if not draft_id:
            return JsonResponse(
                {"error": "draft_id required"},
                status=400
            )

        with transaction.atomic():
            draft = (
                CompanyOnboardingTransaction.objects
                .select_for_update()
                .select_related("plan", "owner")
                .get(id=draft_id)
            )

            # ------------------------------------------------
            # ✅ Idempotent حالات سبق تنفيذها
            # ------------------------------------------------
            if draft.status == "CONFIRMED":
                return JsonResponse(
                    _build_draft_response(
                        draft=draft,
                        message="Draft already confirmed",
                        state="already_confirmed",
                    ),
                    status=200,
                )

            if draft.status == "PENDING_PAYMENT":
                return JsonResponse(
                    _build_draft_response(
                        draft=draft,
                        message="Draft already confirmed and waiting for payment",
                        state="pending_payment",
                    ),
                    status=200,
                )

            if draft.status == "PAID":
                return JsonResponse(
                    _build_draft_response(
                        draft=draft,
                        message="Draft already paid",
                        state="already_paid",
                    ),
                    status=200,
                )

            # ------------------------------------------------
            # ❌ حالات غير مسموحة
            # ------------------------------------------------
            if draft.status != "DRAFT":
                return JsonResponse(
                    {
                        "error": "Draft status does not allow confirmation",
                        "draft_status": draft.status,
                    },
                    status=409
                )

            draft.status = "CONFIRMED"
            draft.save(update_fields=["status"])

            # ------------------------------------------------
            # Notification Center الرسمي فقط بعد نجاح الـ commit
            # ------------------------------------------------
            transaction.on_commit(
                lambda: _dispatch_confirm_draft_notification(draft=draft)
            )

    except CompanyOnboardingTransaction.DoesNotExist:
        return JsonResponse(
            {"error": "Draft not found"},
            status=404
        )
    except Exception:
        return JsonResponse(
            {"error": "Invalid request payload"},
            status=400
        )

    return JsonResponse(
        _build_draft_response(
            draft=draft,
            message="Draft confirmed successfully",
            state="confirmed",
        ),
        status=200,
    )