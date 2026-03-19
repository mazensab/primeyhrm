# ============================================================
# 🚀 System/Public Onboarding — Create Draft Transaction
# Primey HR Cloud | V2.4 PUBLIC SAFE + WHATSAPP + ADMIN PHONE
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
# ✔ Draft Creation Email
# ✔ Draft Creation WhatsApp
# ✔ CASH Blocked For Public Flow
# ✔ Clear Guard For Non-Nullable owner Field
# ✔ SYSTEM Scope for Public Onboarding WhatsApp
# ✔ Admin Phone Supported
# ✔ Payment Methods Cleaned (BANK_TRANSFER / CREDIT_CARD / TAMARA)
# ============================================================

from __future__ import annotations

import json
import logging
import re
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing_center.models import (
    SubscriptionPlan,
    Discount,
    CompanyOnboardingTransaction,
    AccountSubscription,
)
from whatsapp_center.models import ScopeType, TriggerSource
from whatsapp_center.services import send_event_whatsapp_message
from whatsapp_center.utils import normalize_phone_number

logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================
# 🖼️ Primey Email Branding
# ============================================================

PRIMEY_EMAIL_LOGO_URL = getattr(
    settings,
    "PRIMEY_EMAIL_LOGO_URL",
    getattr(
        settings,
        "EMAIL_LOGO_URL",
        "https://drive.google.com/uc?export=view&id=1x2Q9wJm8QmQm7mYjQmW7aJmR8bPlogoblak",
    ),
)

DEFAULT_FROM_EMAIL = getattr(
    settings,
    "DEFAULT_FROM_EMAIL",
    getattr(settings, "EMAIL_HOST_USER", "no-reply@primeyhr.com"),
)


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


def _build_draft_created_whatsapp_message(*, user, draft) -> str:
    owner_name = _safe_text(
        getattr(draft, "admin_name", None) or (getattr(user, "username", None) if user else None),
        "User",
    )
    admin_phone = _get_draft_admin_phone(draft)

    return (
        f"مرحباً {owner_name}،\n\n"
        f"تم إنشاء الطلب المبدئي بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_text(draft.company_name)}\n"
        f"السجل التجاري: {_safe_text(draft.commercial_number)}\n"
        f"الرقم الضريبي: {_safe_text(draft.tax_number)}\n"
        f"جوال الشركة: {_safe_text(draft.phone)}\n"
        f"البريد الإلكتروني للشركة: {_safe_text(draft.email)}\n"
        f"المدينة: {_safe_text(draft.city)}\n"
        f"اسم المسؤول: {_safe_text(draft.admin_name)}\n"
        f"اسم المستخدم: {_safe_text(draft.admin_username)}\n"
        f"البريد الإلكتروني للمسؤول: {_safe_text(draft.admin_email)}\n"
        f"جوال المسؤول: {_safe_text(admin_phone)}\n"
        f"الباقة: {_safe_text(getattr(draft.plan, 'name', None))}\n"
        f"المدة: {_safe_text(draft.duration)}\n"
        f"طريقة الدفع: {_safe_text(draft.payment_method)}\n"
        f"السعر الأساسي: {_money_str(draft.base_price)} SAR\n"
        f"الخصم: {_money_str(draft.discount_amount)} SAR\n"
        f"الضريبة: {_money_str(draft.vat_amount)} SAR\n"
        f"الإجمالي: {_money_str(draft.total_amount)} SAR\n"
        f"الحالة: {_safe_text(draft.status)}\n\n"
        f"تم حفظ طلبكم المبدئي بنجاح، ويمكن متابعة الخطوات التالية حسب مسار التسجيل المعتمد."
    )


def _send_draft_created_whatsapp(*, user, draft) -> None:
    """
    إرسال واتساب بعد إنشاء الطلب المبدئي.
    هذا التدفق Public/System Onboarding لذلك نعتمد SYSTEM scope.
    """
    seen_phones: set[str] = set()
    targets: list[dict] = []

    def _append_target(phone: str, name: str, role: str):
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone or normalized_phone in seen_phones:
            return

        seen_phones.add(normalized_phone)
        targets.append(
            {
                "phone": normalized_phone,
                "name": _safe_text(name, "User"),
                "role": _safe_text(role, ""),
            }
        )

    _append_target(
        _get_draft_admin_phone(draft),
        getattr(draft, "admin_name", None) or getattr(draft, "admin_username", None) or "Admin",
        "admin",
    )

    _append_target(
        _safe_text(getattr(draft, "phone", None), ""),
        getattr(draft, "company_name", None) or getattr(draft, "admin_name", None) or "Company",
        "company",
    )

    if user:
        owner_phone = _get_best_phone_for_entity(user)
        _append_target(
            owner_phone,
            getattr(user, "first_name", None) or getattr(user, "username", None) or "Owner",
            "owner",
        )

    if not targets:
        logger.warning(
            "Draft creation WhatsApp skipped: no phone targets found. draft_id=%s user_id=%s",
            getattr(draft, "id", None),
            getattr(user, "id", None) if user else None,
        )
        return

    message_text = _build_draft_created_whatsapp_message(user=user, draft=draft)

    for target in targets:
        try:
            send_event_whatsapp_message(
                scope_type=ScopeType.SYSTEM,
                company=None,
                event_code="onboarding_draft_created",
                recipient_phone=target["phone"],
                recipient_name=target["name"],
                recipient_role=target["role"],
                trigger_source=TriggerSource.SYSTEM,
                language_code="ar",
                related_model="CompanyOnboardingTransaction",
                related_object_id=str(getattr(draft, "id", "")),
                context={
                    "message": message_text,
                    "company_name": _safe_text(draft.company_name),
                    "commercial_number": _safe_text(draft.commercial_number),
                    "tax_number": _safe_text(draft.tax_number),
                    "city": _safe_text(draft.city),
                    "phone": _safe_text(draft.phone),
                    "email": _safe_text(draft.email),
                    "admin_name": _safe_text(draft.admin_name),
                    "admin_username": _safe_text(draft.admin_username),
                    "admin_email": _safe_text(draft.admin_email),
                    "admin_phone": _safe_text(_get_draft_admin_phone(draft)),
                    "plan_name": _safe_text(getattr(draft.plan, "name", None)),
                    "duration": _safe_text(draft.duration),
                    "payment_method": _safe_text(draft.payment_method),
                    "base_price": f"{_money_str(draft.base_price)} SAR",
                    "discount_amount": f"{_money_str(draft.discount_amount)} SAR",
                    "vat_amount": f"{_money_str(draft.vat_amount)} SAR",
                    "total_amount": f"{_money_str(draft.total_amount)} SAR",
                    "status": _safe_text(draft.status),
                    "recipient_name": target["name"],
                },
            )

            logger.info(
                "Draft creation WhatsApp dispatched successfully. draft_id=%s phone=%s role=%s",
                getattr(draft, "id", None),
                target.get("phone"),
                target.get("role"),
            )

        except Exception:
            logger.exception(
                "Failed to send draft creation WhatsApp. draft_id=%s phone=%s role=%s",
                getattr(draft, "id", None),
                target.get("phone"),
                target.get("role"),
            )


def _build_draft_created_email_html(*, user, draft) -> str:
    logo_url = escape(PRIMEY_EMAIL_LOGO_URL)

    fallback_owner_name = None
    if user and getattr(user, "is_authenticated", False):
        fallback_owner_name = getattr(user, "username", None)

    owner_name = escape(
        _safe_text(
            getattr(draft, "admin_name", None) or fallback_owner_name,
            "User",
        )
    )

    company_name = escape(_safe_text(draft.company_name))
    commercial_number = escape(_safe_text(draft.commercial_number))
    tax_number = escape(_safe_text(draft.tax_number))
    phone = escape(_safe_text(draft.phone))
    email = escape(_safe_text(draft.email))
    city = escape(_safe_text(draft.city))

    national_address = draft.national_address or {}
    building_no = escape(_safe_text(national_address.get("building_no")))
    street = escape(_safe_text(national_address.get("street")))
    district = escape(_safe_text(national_address.get("district")))
    postal_code = escape(_safe_text(national_address.get("postal_code")))
    short_address = escape(_safe_text(national_address.get("short_address")))

    admin_username = escape(_safe_text(draft.admin_username))
    admin_name = escape(_safe_text(draft.admin_name))
    admin_email = escape(_safe_text(draft.admin_email))
    admin_phone = escape(_safe_text(_get_draft_admin_phone(draft)))

    plan_name = escape(_safe_text(getattr(draft.plan, "name", None)))
    duration = escape(_safe_text(draft.duration))
    payment_method = escape(_safe_text(draft.payment_method))
    base_price = escape(_money_str(draft.base_price))
    discount_amount = escape(_money_str(draft.discount_amount))
    vat_amount = escape(_money_str(draft.vat_amount))
    total_amount = escape(_money_str(draft.total_amount))
    status = escape(_safe_text(draft.status))
    start_date = escape(str(draft.start_date) if draft.start_date else "-")
    end_date = escape(str(draft.end_date) if draft.end_date else "-")

    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>تم إنشاء الطلب المبدئي</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f7fb;font-family:Tahoma,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f7fb;margin:0;padding:24px 0;">
    <tr>
      <td align="center">
        <table width="680" cellpadding="0" cellspacing="0"
               style="max-width:680px;width:100%;background:#ffffff;border-radius:18px;overflow:hidden;border:1px solid #e5e7eb;">

          <tr>
            <td align="center" style="background:#000000;padding:28px 24px;">
              <img src="{logo_url}" alt="Primey"
                   style="max-height:56px;width:auto;display:block;margin:0 auto 12px auto;" />
              <div style="color:#ffffff;font-size:22px;font-weight:700;line-height:1.6;">
                Primey HR Cloud
              </div>
              <div style="color:#d1d5db;font-size:14px;line-height:1.8;">
                تم إنشاء الطلب المبدئي بنجاح
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:32px 28px 20px 28px;">
              <div style="font-size:16px;color:#111827;line-height:2;">
                أهلاً <strong>{owner_name}</strong>،
              </div>

              <div style="margin-top:10px;font-size:15px;color:#374151;line-height:2;">
                تم إنشاء الطلب المبدئي للشركة بنجاح داخل <strong>Primey HR Cloud</strong>.
                يمكنك الآن متابعة المراجعة ثم الانتقال إلى خطوة الدفع من التدفق المعتمد.
              </div>

              <div style="margin-top:22px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الشركة
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">اسم الشركة:</td><td style="padding:6px 0;">{company_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">السجل التجاري:</td><td style="padding:6px 0;">{commercial_number}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الرقم الضريبي:</td><td style="padding:6px 0;">{tax_number}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">جوال الشركة:</td><td style="padding:6px 0;">{phone}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">البريد الإلكتروني:</td><td style="padding:6px 0;">{email}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">المدينة:</td><td style="padding:6px 0;">{city}</td></tr>
                </table>
              </div>

              <div style="margin-top:18px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  العنوان الوطني
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">رقم المبنى:</td><td style="padding:6px 0;">{building_no}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الشارع:</td><td style="padding:6px 0;">{street}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الحي:</td><td style="padding:6px 0;">{district}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الرمز البريدي:</td><td style="padding:6px 0;">{postal_code}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">العنوان المختصر:</td><td style="padding:6px 0;">{short_address}</td></tr>
                </table>
              </div>

              <div style="margin-top:18px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الأدمن
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">اسم المسؤول:</td><td style="padding:6px 0;">{admin_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">اسم المستخدم:</td><td style="padding:6px 0;">{admin_username}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">البريد الإلكتروني:</td><td style="padding:6px 0;">{admin_email}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">جوال المسؤول:</td><td style="padding:6px 0;">{admin_phone}</td></tr>
                </table>
              </div>

              <div style="margin-top:18px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الباقة والتسعير
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">الباقة:</td><td style="padding:6px 0;">{plan_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">المدة:</td><td style="padding:6px 0;">{duration}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">طريقة الدفع:</td><td style="padding:6px 0;">{payment_method}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">تاريخ البداية:</td><td style="padding:6px 0;">{start_date}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">تاريخ النهاية:</td><td style="padding:6px 0;">{end_date}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">السعر الأساسي:</td><td style="padding:6px 0;">{base_price} SAR</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الخصم:</td><td style="padding:6px 0;">{discount_amount} SAR</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الضريبة:</td><td style="padding:6px 0;">{vat_amount} SAR</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الإجمالي:</td><td style="padding:6px 0;">{total_amount} SAR</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الحالة:</td><td style="padding:6px 0;">{status}</td></tr>
                </table>
              </div>

              <div style="margin-top:22px;font-size:14px;color:#6b7280;line-height:2;">
                هذه الرسالة للتأكيد فقط بأنه تم حفظ الطلب المبدئي بنجاح داخل النظام.
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:20px 28px 30px 28px;">
              <div style="border-top:1px solid #e5e7eb;padding-top:18px;font-size:12px;color:#9ca3af;line-height:1.9;text-align:center;">
                هذه رسالة آلية من Primey HR Cloud — يرجى عدم الرد عليها مباشرة.
              </div>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
""".strip()


def _send_draft_created_email(*, user, draft) -> None:
    recipients = _build_draft_recipients(user=user, draft=draft)

    if not recipients:
        logger.warning(
            "Draft creation email skipped: no recipients found. draft_id=%s",
            getattr(draft, "id", None),
        )
        return

    owner_name = _safe_text(
        draft.admin_name or (getattr(user, "username", None) if user else None),
        "User",
    )

    subject = f"تم إنشاء الطلب المبدئي - {draft.company_name}"

    text_body = (
        f"مرحباً {owner_name},\n\n"
        f"تم إنشاء الطلب المبدئي بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_text(draft.company_name)}\n"
        f"السجل التجاري: {_safe_text(draft.commercial_number)}\n"
        f"الرقم الضريبي: {_safe_text(draft.tax_number)}\n"
        f"جوال الشركة: {_safe_text(draft.phone)}\n"
        f"البريد الإلكتروني: {_safe_text(draft.email)}\n"
        f"المدينة: {_safe_text(draft.city)}\n"
        f"اسم المسؤول: {_safe_text(draft.admin_name)}\n"
        f"اسم المستخدم: {_safe_text(draft.admin_username)}\n"
        f"البريد الإلكتروني للمسؤول: {_safe_text(draft.admin_email)}\n"
        f"جوال المسؤول: {_safe_text(_get_draft_admin_phone(draft))}\n"
        f"الباقة: {_safe_text(getattr(draft.plan, 'name', None))}\n"
        f"المدة: {_safe_text(draft.duration)}\n"
        f"طريقة الدفع: {_safe_text(draft.payment_method)}\n"
        f"السعر الأساسي: {_money_str(draft.base_price)} SAR\n"
        f"الخصم: {_money_str(draft.discount_amount)} SAR\n"
        f"الضريبة: {_money_str(draft.vat_amount)} SAR\n"
        f"الإجمالي: {_money_str(draft.total_amount)} SAR\n"
        f"الحالة: {_safe_text(draft.status)}\n\n"
        f"مع تحيات Primey HR Cloud"
    )

    html_body = _build_draft_created_email_html(user=user, draft=draft)

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)

        logger.info(
            "Draft creation email sent successfully. draft_id=%s recipients=%s",
            getattr(draft, "id", None),
            recipients,
        )

    except Exception:
        logger.exception(
            "Failed to send draft creation email. draft_id=%s",
            getattr(draft, "id", None),
        )


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
    payment_method = _normalize_text(payload.get("payment_method")).upper()

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
            lambda: _send_draft_created_email(
                user=user,
                draft=draft,
            )
        )

        transaction.on_commit(
            lambda: _send_draft_created_whatsapp(
                user=user,
                draft=draft,
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