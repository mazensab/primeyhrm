# ============================================================
# 🚀 System Onboarding — Confirm Payment & Activate Company
# Primey HR Cloud | V2.2 ULTRA SAFE (USERNAME HARDENED 🔐)
# ============================================================
# ✔ Create Only (No Merge Ever)
# ✔ Idempotent Draft Locking
# ✔ Strict Username Source = draft.admin_username
# ✔ Collision Protection (Race-Safe)
# ✔ Password Scrub After Success
# ✔ Atomic & Safe
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.views.decorators.csrf import csrf_exempt
import json
import uuid

from company_manager.models import Company, CompanyUser
from billing_center.models import (
    CompanyOnboardingTransaction,
    CompanySubscription,
    Invoice,
    Payment,
)


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
    """
    توحيد صيغة اسم المستخدم
    """
    if not value:
        return ""
    return value.strip().lower()


def _normalize_email(value: str) -> str:
    """
    توحيد صيغة البريد الإلكتروني
    """
    if not value:
        return ""
    return value.strip().lower()


# ============================================================
# ✅ API — Confirm Onboarding Payment
# URL: /api/system/onboarding/confirm-payment/
# ============================================================

@login_required
@require_POST
@csrf_exempt
def confirm_onboarding_payment(request):
    payload = _json_payload(request)

    if not payload:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    draft_id = payload.get("draft_id")
    if not draft_id:
        return JsonResponse({"error": "draft_id مطلوب"}, status=400)

    User = get_user_model()

    with transaction.atomic():

        # ====================================================
        # 1️⃣ Draft (LOCKED + IDEMPOTENT)
        # ====================================================
        try:
            draft = (
                CompanyOnboardingTransaction.objects
                .select_for_update()
                .get(id=draft_id)
            )
        except CompanyOnboardingTransaction.DoesNotExist:
            return JsonResponse({"error": "المسودة غير موجودة"}, status=404)

        if draft.status == "PAID":
            return JsonResponse(
                {"error": "تم تأكيد هذه العملية سابقًا"},
                status=409,
            )

        # ====================================================
        # 2️⃣ Company — CREATE ONLY (NO MERGE EVER)
        # ====================================================

        # 🔒 حماية من تكرار السجل التجاري إن وُجد
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

        # ✅ إنشاء شركة جديدة دائمًا
        company = Company.objects.create(
            owner=draft.owner,
            commercial_number=draft.commercial_number,
            name=draft.company_name,
            city=draft.city,
            vat_number=draft.tax_number,
            phone=draft.phone,
            email=draft.email,
            building_number=draft.national_address.get("building_no"),
            street=draft.national_address.get("street"),
            district=draft.national_address.get("district"),
            postal_code=draft.national_address.get("postal_code"),
            short_address=draft.national_address.get("short_address"),
            is_active=True,
        )

        # ====================================================
        # 3️⃣ Company Admin — USERNAME SOURCE OF TRUTH ✅
        # ====================================================

        admin_username = _normalize_username(draft.admin_username)
        admin_email = _normalize_email(draft.admin_email)

        if not admin_username:
            return JsonResponse(
                {"error": "اسم المستخدم غير موجود في المسودة"},
                status=400,
            )

        # 🔒 منع تعارض أسماء المستخدمين (Race Safe)
        try:
            admin_user = User.objects.create_user(
                username=admin_username,
                email=admin_email,
                password=draft.admin_password,
                first_name=draft.admin_name,
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

        CompanyUser.objects.create(
            user=admin_user,
            company=company,
            role="admin",
            is_active=True,
        )

        # ====================================================
        # 4️⃣ Subscription (ONE PER COMPANY)
        # ====================================================
        subscription = CompanySubscription.objects.create(
            company=company,
            plan=draft.plan,
            start_date=draft.start_date,
            end_date=draft.end_date,
            status="ACTIVE",
            apps_snapshot=draft.plan.apps,
        )

        # ====================================================
        # 5️⃣ Invoice (PAID)
        # ====================================================
        invoice = Invoice.objects.create(
            company=company,
            subscription=subscription,
            invoice_number=_generate_invoice_number(),
            issue_date=draft.start_date,
            total_amount=draft.total_amount,
            status="PAID",
            is_approved=True,
            approved_at=timezone.now(),
            subscription_snapshot={
                "plan": draft.plan.name,
                "duration": draft.duration,
            },
        )

        # ====================================================
        # 6️⃣ Payment
        # ====================================================
        Payment.objects.create(
            invoice=invoice,
            amount=draft.total_amount,
            method="CASH",
            created_by=draft.owner,
        )

        # ====================================================
        # 7️⃣ Finalize Draft (SCRUB PASSWORD 🔐)
        # ====================================================
        draft.status = "PAID"
        draft.admin_password = ""   # 🔒 إزالة كلمة المرور بعد الاستخدام
        draft.save(update_fields=["status", "admin_password"])

    # ========================================================
    # ✅ Response
    # ========================================================
    return JsonResponse(
        {
            "company_id": company.id,
            "company_name": company.name,
            "admin_username": admin_user.username,
            "subscription": {
                "plan": subscription.plan.name,
                "status": subscription.status,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
            },
            "invoice_id": invoice.id,
        },
        status=200,
    )
