# =====================================================================
# 🟦 Create Company — V10.3 FINAL (FIRST COMPANY ONLY)
# Primey HR Cloud
# =====================================================================
# ✔ Creates FIRST Company only (Signup / Go-Live)
# ✔ Creates Admin + Roles + Subscription + Invoice
# ✔ Subscription = PENDING_PAYMENT
# ✔ NO activation
# ✔ HARD BLOCK if any real company already exists
# =====================================================================

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now, timedelta
from django.db import transaction
import json

from django.contrib.auth import get_user_model

from company_manager.models import (
    Company,
    CompanyProfile,
    CompanyUser,
    CompanyRole,
)

from billing_center.models import (
    SubscriptionPlan,
    CompanySubscription,
    Invoice,
)

from billing_center.services.pricing_engine import (
    calculate_subscription_pricing,
)

User = get_user_model()


def _model_field_names(model_cls) -> set:
    try:
        return {f.name for f in model_cls._meta.get_fields()}
    except Exception:
        return set()


@csrf_exempt
@transaction.atomic
def create_company_full(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # ---------------------------------------------------------
    # 🔒 HARD GUARD — FIRST COMPANY ONLY
    # ---------------------------------------------------------
    existing_companies = (
        Company.objects
        .exclude(name="Default System Company")
        .exists()
    )

    if existing_companies:
        return JsonResponse(
            {
                "error": "COMPANY_LIMIT_REACHED",
                "message": (
                    "لا يمكن إنشاء أكثر من شركة واحدة عبر التسجيل. "
                    "لإضافة شركات أخرى، استخدم إدارة الشركات من داخل النظام."
                ),
            },
            status=403,
        )

    # ---------------------------------------------------------
    # Parse JSON
    # ---------------------------------------------------------
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # ---------------------------------------------------------
    # Required Fields
    # ---------------------------------------------------------
    required = [
        "name",
        "city",
        "commercial_number",
        "phone",
        "email",
        "admin_email",
        "admin_password",
        "plan_id",
        "duration",
    ]

    for field in required:
        if not data.get(field):
            return JsonResponse(
                {"error": f"Missing required field: {field}"},
                status=400,
            )

    # ---------------------------------------------------------
    # Basic Fields
    # ---------------------------------------------------------
    name = data["name"]
    city = data["city"]
    commercial_number = data["commercial_number"]
    phone = data["phone"]
    email = data["email"]

    admin_email = data["admin_email"]
    admin_password = data["admin_password"]

    plan_id = int(data["plan_id"])
    duration = data["duration"]

    discount_code = (data.get("discount_code") or "").strip() or None

    # ---------------------------------------------------------
    # 1) Validate Plan
    # ---------------------------------------------------------
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({"error": "الباقة غير موجودة"}, status=400)

    # ---------------------------------------------------------
    # 2) Pricing Engine
    # ---------------------------------------------------------
    pricing = calculate_subscription_pricing(
        plan=plan,
        duration=duration,
        discount_code=discount_code,
    )

    if pricing["errors"]:
        return JsonResponse(
            {
                "error": "PRICING_ERROR",
                "details": pricing["errors"],
            },
            status=400,
        )

    end_date = (
        now().date() + timedelta(days=30)
        if duration == "monthly"
        else now().date() + timedelta(days=365)
    )

    # ---------------------------------------------------------
    # 3) Create Company (INACTIVE)
    # ---------------------------------------------------------
    company = Company.objects.create(
        name=name,
        city=city,
        commercial_number=commercial_number,
        phone=phone,
        email=email,
        is_active=False,
    )

    # ---------------------------------------------------------
    # 4) Company Profile
    # ---------------------------------------------------------
    CompanyProfile.objects.create(company=company)

    # ---------------------------------------------------------
    # 5) Admin User
    # ---------------------------------------------------------
    admin_username = admin_email.split("@")[0]

    admin_user = User.objects.create_user(
        username=admin_username,
        email=admin_email,
        password=admin_password,
        is_staff=True,
    )

    company_user = CompanyUser.objects.create(
        user=admin_user,
        company=company,
        role="ADMIN",
        is_active=True,
    )

    # ---------------------------------------------------------
    # 6) Ensure ADMIN Role
    # ---------------------------------------------------------
    admin_role, _ = CompanyRole.objects.get_or_create(
        company=company,
        name="ADMIN",
        defaults={
            "description": "System Administrator",
            "permissions": {"*": True},
            "is_system_role": True,
        },
    )

    company_user.roles.add(admin_role)

    # ---------------------------------------------------------
    # 7) Subscription (PENDING PAYMENT)
    # ---------------------------------------------------------
    sub_fields = _model_field_names(CompanySubscription)

    subscription_kwargs = dict(
        company=company,
        plan=plan,
        start_date=now().date(),
        end_date=end_date,
        status="PENDING_PAYMENT",
    )

    if "price_before_discount" in sub_fields:
        subscription_kwargs["price_before_discount"] = pricing["base_price"]

    if "price_after_discount" in sub_fields:
        subscription_kwargs["price_after_discount"] = pricing["final_price"]

    if "discount_code" in sub_fields:
        subscription_kwargs["discount_code"] = (
            pricing["discount"]["code"]
            if pricing["discount"]
            else None
        )

    if "discount_amount" in sub_fields:
        subscription_kwargs["discount_amount"] = (
            pricing["discount"]["amount"]
            if pricing["discount"]
            else 0
        )

    subscription = CompanySubscription.objects.create(
        **subscription_kwargs
    )

    # ---------------------------------------------------------
    # 8) Invoice (PENDING)
    # ---------------------------------------------------------
    inv_fields = _model_field_names(Invoice)

    invoice_kwargs = dict(
        company=company,
        subscription=subscription,
        invoice_number=f"INV-{company.id}-{int(now().timestamp())}",
        issue_date=now().date(),
        due_date=end_date,
        total_amount=pricing["final_price"],
        status="PENDING",
    )

    if "subtotal" in inv_fields:
        invoice_kwargs["subtotal"] = pricing["base_price"]

    if "discount_code" in inv_fields:
        invoice_kwargs["discount_code"] = (
            pricing["discount"]["code"]
            if pricing["discount"]
            else None
        )

    if "discount_amount" in inv_fields:
        invoice_kwargs["discount_amount"] = (
            pricing["discount"]["amount"]
            if pricing["discount"]
            else 0
        )

    invoice = Invoice.objects.create(**invoice_kwargs)

    # ---------------------------------------------------------
    # ✅ Final Response
    # ---------------------------------------------------------
    return JsonResponse(
        {
            "success": True,
            "company_id": company.id,
            "subscription_id": subscription.id,
            "invoice_id": invoice.id,
            "subscription_status": "PENDING_PAYMENT",
            "company_active": False,
            "message": "تم إنشاء الشركة الأولى بنجاح — بانتظار الدفع",
        }
    )
