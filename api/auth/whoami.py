from django.http import JsonResponse
from django.contrib.auth import get_user_model

from company_manager.models import CompanyUser
from employee_center.models import Employee

User = get_user_model()


def apiWhoAmI(request):
    user = request.user

    # ============================================================
    # 🔒 Anonymous (NO 401 — avoid redirect loops)
    # ============================================================
    if not user.is_authenticated:
        return JsonResponse(
            {
                "authenticated": False,
                "user": None,
                "is_superuser": False,
                "role": None,
                "company": None,
                "company_id": None,
                "subscription": {
                    # 🟢 SAFE DEFAULTS (Frontend Guard)
                    "apps": [],
                    "apps_snapshot": [],
                    "days_remaining": None,
                },
            },
            status=200,
        )

    # ============================================================
    # 👤 Base User Payload (SAFE & EXTENSIBLE)
    # ============================================================
    user_payload = {
        "id": user.id,
        "username": user.username,
        "email": user.email or None,
        "full_name": None,  # 👈 يُملأ فقط إن كان Employee موجود
    }

    # ============================================================
    # 🏢 Company Context (Single Source of Truth)
    # ============================================================
    company = None
    company_id = None
    role = "system" if user.is_superuser else "company"

    if not user.is_superuser:
        company_user = (
            CompanyUser.objects
            .select_related("company")
            .filter(user=user, is_active=True)
            .order_by("-id")  # 🔒 deterministic
            .first()
        )

        if company_user and company_user.company:
            company = {
                "id": company_user.company.id,
                "name": company_user.company.name,
            }
            company_id = company_user.company.id
            role = company_user.role.lower() if company_user.role else "company"

            # ====================================================
            # 👥 Employee Profile (OPTIONAL — SAFE)
            # ====================================================
            employee = (
                Employee.objects
                .filter(user=user, company=company_user.company)
                .only("full_name")
                .first()
            )

            if employee and employee.full_name:
                user_payload["full_name"] = employee.full_name

    # ============================================================
    # 📦 Subscription Snapshot — COMPANY SCOPED (SOURCE OF TRUTH)
    # ============================================================
    def resolve_subscription_apps(user, company_id):
        """
        ⚠️ Placeholder آمن
        سيتم لاحقًا الربط مع Subscription.apps_snapshot الحقيقي
        """
        if user.is_superuser:
            return []

        if company_id:
            return [
                "employee",
                "attendance",
                "payroll",
                "leave",
            ]

        return []

    apps_snapshot = resolve_subscription_apps(user, company_id)

    # ============================================================
    # ⏳ Subscription Status — CURRENT COMPANY ONLY
    # ============================================================
    # Placeholder آمن — سيتم ربطه لاحقًا من Subscription
    days_remaining = 5 if not user.is_superuser else None

    # ============================================================
    # ✅ Response (Frontend Safe Contract — FINAL)
    # ============================================================
    return JsonResponse(
        {
            "authenticated": True,
            "user": user_payload,
            "is_superuser": user.is_superuser,
            "role": role,
            "company": company,
            "company_id": company_id,
            "subscription": {
                # 🔹 Single Source of Truth
                "apps": apps_snapshot,
                "apps_snapshot": apps_snapshot,

                # 🔹 Company Subscription Status
                "days_remaining": days_remaining,
            },
        },
        status=200,
    )
