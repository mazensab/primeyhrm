# ============================================================
# 🚀 System Onboarding — Create Draft Transaction
# Primey HR Cloud | V1.5 ULTRA SAFE (USERNAME ENFORCED 🔒)
# ============================================================
# ✔ Paid Only (Non-SuperAdmin)
# ✔ SuperAdmin Always Allowed
# ✔ Uses CompanyOnboardingTransaction
# ✔ No Company Creation
# ✔ No Invoice
# ✔ No Subscription Activation
# ✔ STRICT Admin Validation (Username + Email + Password)
# ✔ Username Uniqueness Guard
# ✔ SAFE & ATOMIC
# ============================================================

from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import json
import re

from billing_center.models import (
    SubscriptionPlan,
    Discount,
    CompanyOnboardingTransaction,
    AccountSubscription,
)


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
    """
    تنظيف النصوص قبل الحفظ
    """
    if not value:
        return ""
    return value.strip()


def _normalize_username(value: str) -> str:
    """
    توحيد شكل اسم المستخدم
    """
    return _normalize_text(value).lower()


def _normalize_email(value: str) -> str:
    """
    توحيد شكل البريد الإلكتروني
    """
    return _normalize_text(value).lower()


def _validate_username(username: str):
    """
    🔐 Validation صارم لاسم المستخدم
    """
    username = _normalize_username(username)

    if not username:
        return "اسم المستخدم مطلوب"

    if len(username) < 3:
        return "اسم المستخدم يجب ألا يقل عن 3 أحرف"

    # يسمح فقط بالحروف والأرقام والنقطة والشرطة السفلية والشرطة
    if not re.match(r"^[a-z0-9_.-]+$", username):
        return "اسم المستخدم يحتوي على رموز غير مسموحة"

    return None


def _validate_admin_payload(username, name, email, password):
    """
    🔐 Validation صارم لبيانات الأدمن
    """

    username = _normalize_username(username)
    name     = _normalize_text(name)
    email    = _normalize_email(email)
    password = _normalize_text(password)

    # -------------------------------
    # Username
    # -------------------------------
    username_error = _validate_username(username)
    if username_error:
        return username_error

    # -------------------------------
    # Presence
    # -------------------------------
    if not name:
        return "اسم المسؤول مطلوب"

    if not email:
        return "البريد الإلكتروني للمسؤول مطلوب"

    if not password:
        return "كلمة المرور مطلوبة"

    # -------------------------------
    # Email format
    # -------------------------------
    try:
        validate_email(email)
    except ValidationError:
        return "صيغة البريد الإلكتروني غير صحيحة"

    # -------------------------------
    # Password strength
    # -------------------------------
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


# ============================================================
# 🌐 API — Create Draft
# URL: /api/system/onboarding/create-draft/
# ============================================================

@login_required
@require_POST
@csrf_exempt
def create_onboarding_draft(request):
    user = request.user
    payload = _json_payload(request)

    if not payload:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    # --------------------------------------------------------
    # 🔒 Paid Account Only (Non-SuperAdmin)
    # --------------------------------------------------------
    if not user.is_superuser:
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
    # 📥 Input
    # --------------------------------------------------------
    company_name   = _normalize_text(payload.get("company_name"))
    plan_id        = payload.get("plan_id")
    duration       = payload.get("duration")
    discount_code  = _normalize_text(payload.get("discount_code"))

    # ✅ Admin Snapshot
    admin_username = payload.get("admin_username")
    admin_name     = payload.get("admin_name")
    admin_email    = payload.get("admin_email")
    admin_password = payload.get("admin_password")

    if not all([company_name, plan_id, duration]):
        return JsonResponse({"error": "بيانات غير مكتملة"}, status=400)

    # --------------------------------------------------------
    # 🔐 Validate Admin Data
    # --------------------------------------------------------
    admin_error = _validate_admin_payload(
        admin_username,
        admin_name,
        admin_email,
        admin_password,
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
    admin_name     = _normalize_text(admin_name)
    admin_email    = _normalize_email(admin_email)
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
    # 🧾 Create Draft (ATOMIC + SAFE)
    # --------------------------------------------------------
    with transaction.atomic():
        draft = CompanyOnboardingTransaction.objects.create(
            owner=user,

            # Company snapshot
            company_name=company_name,

            # ✅ Admin snapshot
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

            status="DRAFT",
        )

    # --------------------------------------------------------
    # ✅ Response
    # --------------------------------------------------------
    return JsonResponse(
        {
            "draft_id": draft.id,
            "company_name": draft.company_name,
            "admin": {
                "username": draft.admin_username,
                "name": draft.admin_name,
                "email": draft.admin_email,
            },
            "plan": {
                "id": plan.id,
                "name": plan.name,
            },
            "duration": draft.duration,
            "pricing": {
                "base_price": float(draft.base_price),
                "discount_amount": float(draft.discount_amount),
                "vat_amount": float(draft.vat_amount),
                "total": float(draft.total_amount),
            },
            "status": draft.status,
            "created_at": draft.created_at,
        },
        status=201,
    )
