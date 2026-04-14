# ============================================================
# 🚀 System/Public Onboarding — Create Draft Transaction
# Mham Cloud | V2.6 NOTIFICATION-CENTER CLEAN
# ============================================================
# ✔ Public Draft Creation Supported
# ✔ Internal Logged-In Flow Still Supported
# ✔ No Company Creation
# ✔ No Invoice
# ✔ No Subscription Activation
# ✔ STRICT Admin Validation (Username + Email + Password + Phone)
# ✔ Username Uniqueness Guard
# ✔ Company Snapshot Extended
# ✔ SAFE & ATOMIC
# ✔ Notification Center Only (No direct email / no direct WhatsApp)
# ✔ CASH Blocked For Public Flow
# ✔ Clear Guard For Non-Nullable owner Field
# ✔ Admin Phone Supported
# ✔ Payment Methods Cleaned (BANK_TRANSFER / CREDIT_CARD / TAMARA)
# ✔ Better normalization for external payment aliases
# ✔ Cleaner response payload
# ============================================================

from __future__ import annotations

import importlib
import json
import logging
import re
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing_center.models import (
    AccountSubscription,
    CompanyOnboardingTransaction,
    Discount,
    SubscriptionPlan,
)
from whatsapp_center.utils import normalize_phone_number

logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================
# 🧩 Helpers
# ============================================================

def _json_payload(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


def _normalize_text(value: str) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_username(value: str) -> str:
    return _normalize_text(value).lower()


def _normalize_email(value: str) -> str:
    return _normalize_text(value).lower()


def _normalize_phone(value: str) -> str:
    return _normalize_text(value)


def _normalize_payment_method(value: str) -> str:
    method = _normalize_text(value).upper()

    if method in {"", "CARD", "CARD_PAYMENT", "TAP"}:
        return "CREDIT_CARD"

    return method


def _normalize_national_address(value):
    """
    توحيد العنوان الوطني إلى JSON ثابت
    """
    if not isinstance(value, dict):
        return {}

    return {
        "building_no": _normalize_text(
            value.get("building_no") or value.get("building_number")
        ),
        "street": _normalize_text(value.get("street")),
        "district": _normalize_text(value.get("district")),
        "postal_code": _normalize_text(value.get("postal_code")),
        "short_address": _normalize_text(value.get("short_address")),
    }


def _request_user_or_none(request):
    """
    إرجاع المستخدم فقط إذا كان مسجل دخولًا فعليًا
    """
    user = getattr(request, "user", None)

    if user and getattr(user, "is_authenticated", False):
        return user

    return None


def _validate_username(username: str):
    username = _normalize_username(username)

    if not username:
        return "اسم المستخدم مطلوب"

    if len(username) < 3:
        return "اسم المستخدم يجب ألا يقل عن 3 أحرف"

    if not re.match(r"^[a-z0-9_.-]+$", username):
        return "اسم المستخدم يحتوي على رموز غير مسموحة"

    return None


def _validate_admin_payload(username, name, email, password, phone):
    username = _normalize_username(username)
    name = _normalize_text(name)
    email = _normalize_email(email)
    password = _normalize_text(password)
    phone = _normalize_phone(phone)

    username_error = _validate_username(username)
    if username_error:
        return username_error

    if not name:
        return "اسم المسؤول مطلوب"

    if not email:
        return "البريد الإلكتروني للمسؤول مطلوب"

    try:
        validate_email(email)
    except ValidationError:
        return "صيغة البريد الإلكتروني غير صحيحة"

    if not phone:
        return "رقم جوال المسؤول مطلوب"

    normalized_phone = normalize_phone_number(phone)
    if not normalized_phone:
        return "صيغة رقم جوال المسؤول غير صحيحة"

    if not password:
        return "كلمة المرور مطلوبة"

    if len(password) < 8:
        return "كلمة المرور يجب أن تكون 8 أحرف على الأقل"

    if not re.search(r"[A-Za-z]", password):
        return "كلمة المرور يجب أن تحتوي على أحرف"

    if not re.search(r"\d", password):
        return "كلمة المرور يجب أن تحتوي على أرقام"

    return None


def _calculate_pricing(plan, duration, discount_code=None):
    if duration == "monthly":
        base_price = Decimal(plan.price_monthly)
        end_date = timezone.now().date() + timedelta(days=30)
    elif duration == "yearly":
        base_price = Decimal(plan.price_yearly)
        end_date = timezone.now().date() + timedelta(days=365)
    else:
        raise ValueError("Invalid duration")

    discount_amount = Decimal("0.00")

    if discount_code:
        try:
            discount = Discount.objects.get(code=discount_code, is_active=True)
            if discount.discount_type == "percentage":
                discount_amount = base_price * Decimal(discount.value) / Decimal("100")
            elif discount.discount_type == "fixed":
                discount_amount = Decimal(discount.value)
        except Discount.DoesNotExist:
            pass

    price_after_discount = max(base_price - discount_amount, Decimal("0.00"))
    vat_amount = price_after_discount * Decimal("0.15")
    total_amount = price_after_discount + vat_amount

    return {
        "base_price": base_price,
        "discount_amount": discount_amount,
        "vat_amount": vat_amount,
        "total_amount": total_amount,
        "start_date": timezone.now().date(),
        "end_date": end_date,
    }


def _safe_text(value, default="-"):
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def _money_str(value) -> str:
    try:
        return f"{Decimal(value):.2f}"
    except Exception:
        return "0.00"


def _build_draft_recipients(*, user, draft) -> list[str]:
    recipients: list[str] = []

    candidates = [
        getattr(draft, "admin_email", None),
        getattr(draft, "email", None),
        getattr(user, "email", None) if user else None,
    ]

    for value in candidates:
        email = _normalize_email(value)
        if email and email not in recipients:
            recipients.append(email)

    return recipients


def _owner_field_accepts_null() -> bool:
    """
    فحص بنية الموديل runtime للتأكد هل owner يقبل null أم لا.
    هذا يمنع انفجار IntegrityError في التسجيل الخارجي.
    """
    try:
        owner_field = CompanyOnboardingTransaction._meta.get_field("owner")
        return bool(getattr(owner_field, "null", False))
    except Exception:
        logger.exception("Failed to inspect CompanyOnboardingTransaction.owner field")
        return False


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


def _set_draft_admin_phone_if_supported(draft, admin_phone: str) -> None:
    """
    حفظ رقم جوال الأدمن داخل المسودة إذا كان الموديل يدعم ذلك.
    """
    supported_fields = [
        "admin_phone",
        "admin_mobile",
        "admin_mobile_number",
        "admin_whatsapp_number",
        "admin_phone_number",
    ]

    for field_name in supported_fields:
        try:
            if hasattr(draft, field_name):
                setattr(draft, field_name, admin_phone)
                return
        except Exception:
            continue


def _get_draft_admin_phone(draft) -> str:
    """
    قراءة رقم جوال الأدمن من المسودة إذا كان الحقل موجودًا.
    """
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


def _collect_notification_targets(*, user, draft) -> list[dict]:
    """
    تجميع المستهدفين بشكل آمن وبدون تكرار.
    """
    targets: list[dict] = []
    seen_phones: set[str] = set()
    seen_emails: set[str] = set()

    def _append_target(*, phone="", email="", name="", role=""):
        normalized_phone = normalize_phone_number(phone) if phone else ""
        normalized_email = _normalize_email(email)
        safe_name = _safe_text(name, "User")
        safe_role = _safe_text(role, "")

        key = normalized_phone or normalized_email
        if not key:
            return

        if normalized_phone and normalized_phone in seen_phones:
            return

        if normalized_email and normalized_email in seen_emails:
            return

        if normalized_phone:
            seen_phones.add(normalized_phone)

        if normalized_email:
            seen_emails.add(normalized_email)

        targets.append({
            "phone": normalized_phone,
            "email": normalized_email,
            "name": safe_name,
            "role": safe_role,
        })

    _append_target(
        phone=_get_draft_admin_phone(draft),
        email=getattr(draft, "admin_email", None),
        name=getattr(draft, "admin_name", None) or getattr(draft, "admin_username", None) or "Admin",
        role="admin",
    )

    _append_target(
        phone=_safe_text(getattr(draft, "phone", None), ""),
        email=getattr(draft, "email", None),
        name=getattr(draft, "company_name", None) or getattr(draft, "admin_name", None) or "Company",
        role="company",
    )

    if user:
        _append_target(
            phone=_get_best_phone_for_entity(user),
            email=getattr(user, "email", None),
            name=getattr(user, "first_name", None) or getattr(user, "username", None) or "Owner",
            role="owner",
        )

    return targets


def _build_draft_created_context(*, user, draft, plan) -> dict:
    return {
        "draft_id": getattr(draft, "id", None),
        "company_name": _safe_text(draft.company_name),
        "commercial_number": _safe_text(draft.commercial_number),
        "tax_number": _safe_text(draft.tax_number),
        "phone": _safe_text(draft.phone),
        "email": _safe_text(draft.email),
        "city": _safe_text(draft.city),
        "national_address": draft.national_address or {},
        "admin_username": _safe_text(draft.admin_username),
        "admin_name": _safe_text(draft.admin_name),
        "admin_email": _safe_text(draft.admin_email),
        "admin_phone": _safe_text(_get_draft_admin_phone(draft)),
        "plan_id": getattr(plan, "id", None),
        "plan_name": _safe_text(getattr(plan, "name", None)),
        "duration": _safe_text(draft.duration),
        "payment_method": _safe_text(draft.payment_method),
        "base_price": _money_str(draft.base_price),
        "discount_amount": _money_str(draft.discount_amount),
        "vat_amount": _money_str(draft.vat_amount),
        "total_amount": _money_str(draft.total_amount),
        "status": _safe_text(draft.status),
        "start_date": str(draft.start_date) if draft.start_date else "-",
        "end_date": str(draft.end_date) if draft.end_date else "-",
        "recipients": _build_draft_recipients(user=user, draft=draft),
        "targets": _collect_notification_targets(user=user, draft=draft),
        "is_public_flow": user is None,
        "owner_user_id": getattr(user, "id", None) if user else None,
        "owner_username": _safe_text(getattr(user, "username", None), "") if user else "",
        "owner_email": _safe_text(getattr(user, "email", None), "") if user else "",
    }


def _dispatch_draft_created_notification(*, actor, user, draft, plan) -> None:
    """
    تمرير إشعار إنشاء الطلب المبدئي إلى الطبقة الرسمية فقط.
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
        "notify_onboarding_draft_created",
        "notify_draft_created",
        "send_onboarding_draft_created_notification",
        "send_draft_created_notification",
    ]

    notify_func = None
    for func_name in candidate_function_names:
        notify_func = getattr(services_module, func_name, None)
        if callable(notify_func):
            break

    if not callable(notify_func):
        logger.warning(
            "Onboarding draft created notification function not found. checked=%s",
            ", ".join(candidate_function_names),
        )
        return

    context = _build_draft_created_context(
        user=user,
        draft=draft,
        plan=plan,
    )

    try:
        notify_func(
            actor=actor,
            user=user,
            draft=draft,
            plan=plan,
            extra_context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(
            actor=actor,
            user=user,
            draft=draft,
            plan=plan,
            context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(
            draft=draft,
            plan=plan,
        )
        return
    except Exception:
        logger.exception(
            "Failed while dispatching onboarding draft created notification. draft_id=%s",
            getattr(draft, "id", None),
        )
        return


# ============================================================
# 🌐 API — Create Draft
# URL: /api/system/onboarding/create-draft/
# ============================================================

@require_POST
@csrf_exempt
def create_onboarding_draft(request):
    user = _request_user_or_none(request)
    payload = _json_payload(request)

    if not payload:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    # --------------------------------------------------------
    # 📥 Input
    # --------------------------------------------------------
    company_name = _normalize_text(payload.get("company_name"))
    plan_id = payload.get("plan_id")
    duration = _normalize_text(payload.get("duration")).lower()
    discount_code = _normalize_text(payload.get("discount_code"))
    payment_method = _normalize_payment_method(payload.get("payment_method"))

    # ✅ Company Snapshot
    commercial_number = _normalize_text(payload.get("commercial_number"))
    tax_number = _normalize_text(
        payload.get("tax_number") or payload.get("vat_number")
    )
    phone = _normalize_text(payload.get("phone"))
    email = _normalize_email(payload.get("email"))
    city = _normalize_text(payload.get("city"))
    national_address = _normalize_national_address(
        payload.get("national_address")
    )

    # ✅ Admin Snapshot
    admin_username = payload.get("admin_username")
    admin_name = payload.get("admin_name")
    admin_email = payload.get("admin_email")
    admin_phone = payload.get("admin_phone")
    admin_password = payload.get("admin_password")

    if not all([company_name, plan_id, duration]):
        return JsonResponse({"error": "بيانات غير مكتملة"}, status=400)

    # --------------------------------------------------------
    # 🔐 Payment Method Validation
    # --------------------------------------------------------
    allowed_payment_methods = {
        "BANK_TRANSFER",
        "CREDIT_CARD",
        "TAMARA",
    }

    if payment_method and payment_method not in allowed_payment_methods:
        return JsonResponse(
            {
                "error": "طريقة الدفع غير مدعومة",
                "field": "payment_method",
            },
            status=400,
        )

    if payment_method == "CASH":
        return JsonResponse(
            {
                "error": "الدفع النقدي غير متاح في التسجيل العام",
                "field": "payment_method",
            },
            status=400,
        )

    # --------------------------------------------------------
    # 🔒 Internal Paid Account Guard
    # فقط لو المستخدم مسجل دخولًا داخليًا وليس زائرًا عامًا
    # --------------------------------------------------------
    if user and not user.is_superuser:
        account_sub = (
            AccountSubscription.objects
            .filter(owner=user, status="ACTIVE")
            .select_related("plan")
            .first()
        )

        if not account_sub:
            return JsonResponse(
                {"error": "لا يوجد اشتراك مدفوع نشط لهذا المستخدم"},
                status=403,
            )

    # --------------------------------------------------------
    # 🔐 Validate Admin Data
    # --------------------------------------------------------
    admin_error = _validate_admin_payload(
        admin_username,
        admin_name,
        admin_email,
        admin_password,
        admin_phone,
    )

    if admin_error:
        return JsonResponse(
            {
                "error": "بيانات المسؤول غير صحيحة",
                "details": admin_error,
            },
            status=400,
        )

    admin_username = _normalize_username(admin_username)
    admin_name = _normalize_text(admin_name)
    admin_email = _normalize_email(admin_email)
    admin_phone = normalize_phone_number(_normalize_phone(admin_phone))
    admin_password = _normalize_text(admin_password)

    # --------------------------------------------------------
    # 🚫 Username Uniqueness Guard (Global)
    # --------------------------------------------------------
    if User.objects.filter(username=admin_username).exists():
        return JsonResponse(
            {
                "error": "اسم المستخدم مستخدم مسبقًا",
                "field": "admin_username",
            },
            status=409,
        )

    # --------------------------------------------------------
    # 📦 Plan
    # --------------------------------------------------------
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({"error": "الباقة غير موجودة"}, status=404)

    # --------------------------------------------------------
    # 💰 Pricing
    # --------------------------------------------------------
    try:
        pricing = _calculate_pricing(plan, duration, discount_code)
    except ValueError:
        return JsonResponse({"error": "مدة الاشتراك غير صحيحة"}, status=400)

    # --------------------------------------------------------
    # 🛡️ Public Flow Guard For Non-Nullable owner Field
    # --------------------------------------------------------
    if user is None and not _owner_field_accepts_null():
        logger.error(
            "Public onboarding blocked because CompanyOnboardingTransaction.owner "
            "does not accept NULL. Please make owner nullable and run migrations."
        )
        return JsonResponse(
            {
                "error": "إعداد قاعدة البيانات غير مكتمل للتسجيل الخارجي",
                "details": (
                    "الحقل owner في CompanyOnboardingTransaction لا يقبل NULL. "
                    "يجب تعديل الموديل ليصبح owner nullable ثم تشغيل migrations."
                ),
                "field": "owner",
            },
            status=500,
        )

    # --------------------------------------------------------
    # 🧾 Create Draft (ATOMIC + SAFE)
    # --------------------------------------------------------
    with transaction.atomic():
        draft = CompanyOnboardingTransaction.objects.create(
            owner=user if user else None,

            # Company snapshot
            company_name=company_name,
            commercial_number=commercial_number,
            tax_number=tax_number,
            phone=phone,
            email=email,
            city=city,
            national_address=national_address,

            # Admin snapshot
            admin_username=admin_username,
            admin_name=admin_name,
            admin_email=admin_email,
            admin_password=admin_password,

            # Plan
            plan=plan,
            duration=duration,
            start_date=pricing["start_date"],
            end_date=pricing["end_date"],

            # Amounts
            base_price=pricing["base_price"],
            discount_amount=pricing["discount_amount"],
            vat_amount=pricing["vat_amount"],
            total_amount=pricing["total_amount"],

            # Payment
            payment_method=payment_method or None,

            # Status
            status="DRAFT",
        )

        _set_draft_admin_phone_if_supported(draft, admin_phone)

        save_fields = []
        for field_name in [
            "admin_phone",
            "admin_mobile",
            "admin_mobile_number",
            "admin_whatsapp_number",
            "admin_phone_number",
        ]:
            if hasattr(draft, field_name):
                save_fields.append(field_name)

        if save_fields:
            draft.save(update_fields=save_fields)

        transaction.on_commit(
            lambda: _dispatch_draft_created_notification(
                actor=getattr(request, "user", None),
                user=user,
                draft=draft,
                plan=plan,
            )
        )

    # --------------------------------------------------------
    # ✅ Response
    # --------------------------------------------------------
    return JsonResponse(
        {
            "draft_id": draft.id,
            "company_name": draft.company_name,
            "company": {
                "commercial_number": draft.commercial_number,
                "tax_number": draft.tax_number,
                "phone": draft.phone,
                "email": draft.email,
                "city": draft.city,
                "national_address": draft.national_address or {},
            },
            "admin": {
                "username": draft.admin_username,
                "name": draft.admin_name,
                "email": draft.admin_email,
                "phone": _get_draft_admin_phone(draft),
            },
            "plan": {
                "id": plan.id,
                "name": plan.name,
            },
            "duration": draft.duration,
            "payment_method": payment_method or None,
            "pricing": {
                "base_price": float(draft.base_price),
                "discount_amount": float(draft.discount_amount),
                "vat_amount": float(draft.vat_amount),
                "total": float(draft.total_amount),
            },
            "status": draft.status,
            "created_at": draft.created_at,
            "is_public_flow": user is None,
        },
        status=201,
    )