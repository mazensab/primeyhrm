# ====================================================================
# 🟦 System Companies API — V12.4 Ultra Stable (AUTO ROLES ENABLED ✅)
# Primey HR Cloud — Super Admin Dashboard
# ====================================================================

from django.http import JsonResponse
from django.utils.timezone import now
from datetime import timedelta
from django.db import transaction
import json

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from company_manager.models import (
    Company,
    CompanyUser,
    CompanyRole,   # ✅ NEW
)

from billing_center.models import CompanySubscription, Invoice, AccountSubscription


# ====================================================================
# 🎭 Default Company Roles Blueprint (SYSTEM STANDARD)
# ====================================================================

DEFAULT_COMPANY_ROLES = [
    {
        "name": "🛡️ مدير عام (كامل الصلاحيات)",
        "description": "صلاحيات كاملة لإدارة الشركة والنظام",
        "permissions": {"*": True},
        "is_system_role": True,
    },
    {
        "name": "👥 مدير الموارد البشرية",
        "description": "إدارة الموظفين والعقود والإجازات",
        "permissions": {
            "employees": True,
            "contracts": True,
            "leaves": True,
            "attendance": True,
        },
        "is_system_role": False,
    },
    {
        "name": "💰 محاسب الرواتب",
        "description": "إدارة الرواتب والاستحقاقات",
        "permissions": {
            "payroll": True,
            "reports": True,
        },
        "is_system_role": False,
    },
    {
        "name": "👤 موظف عادي",
        "description": "وصول محدود للبيانات الشخصية",
        "permissions": {
            "profile": True,
        },
        "is_system_role": False,
    },
]


# ====================================================================
# 1) Overview — KPIs
# ====================================================================
def companies_overview(request):
    total = Company.objects.count()
    active = Company.objects.filter(is_active=True).count()
    suspended = Company.objects.filter(is_active=False).count()

    today = now().date()

    subs = CompanySubscription.objects.all()
    expiring_7 = subs.filter(end_date__lte=today + timedelta(days=7)).count()
    expiring_30 = subs.filter(end_date__lte=today + timedelta(days=30)).count()

    return JsonResponse(
        {
            "total": total,
            "active": active,
            "suspended": suspended,
            "expiring_7": expiring_7,
            "expiring_30": expiring_30,
        },
        status=200,
    )


# ====================================================================
# 2) Companies List
# ====================================================================
def companies_list(request):
    companies = Company.objects.all().order_by("-created_at")
    result = []

    for company in companies:
        sub = (
            CompanySubscription.objects
            .filter(company=company)
            .select_related("plan")
            .order_by("-created_at")
            .first()
        )

        result.append(
            {
                "id": company.id,
                "name": company.name,
                "is_active": company.is_active,
                "created_at": company.created_at.isoformat() if company.created_at else None,

                "owner": {
                    "id": company.owner.id if company.owner else None,
                    "name": f"{company.owner.first_name} {company.owner.last_name}".strip()
                    if company.owner else None,
                    "email": company.owner.email if company.owner else None,
                },

                "contact": {
                    "phone": company.phone,
                    "email": company.email,
                },

                "address": company.short_address or company.city or "-",

                "subscription": {
                    "plan": sub.plan.name if sub and sub.plan else None,
                    "status": sub.status if sub else None,
                    "end_date": sub.end_date.isoformat() if sub and sub.end_date else None,
                },

                "users_count": CompanyUser.objects.filter(company=company).count(),
                "devices_count": 0,
            }
        )

    return JsonResponse(result, safe=False, status=200)


# ====================================================================
# 3) Company Detail
# ====================================================================
def company_detail(request, company_id):
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)

    sub = (
        CompanySubscription.objects
        .filter(company=company)
        .select_related("plan")
        .order_by("-created_at")
        .first()
    )

    subscription_info = None
    if sub:
        latest_invoice = _get_latest_invoice(sub)

        subscription_info = {
            "id": sub.id,
            "plan": sub.plan.name if sub.plan else None,
            "status": sub.status,
            "start_date": sub.start_date,
            "end_date": sub.end_date,
            "days_remaining": (
                (sub.end_date - now().date()).days
                if sub.end_date else None
            ),
            "invoice_id": latest_invoice["id"] if latest_invoice else None,
            "latest_invoice": latest_invoice,
        }

    raw_users = (
        CompanyUser.objects.filter(company=company)
        .select_related("user")
        .values(
            "user__id",
            "user__first_name",
            "user__last_name",
            "user__email",
            "is_active",
            "role",
            "created_at",
        )
    )

    users_list = [
        {
            "id": u["user__id"],
            "name": f"{u['user__first_name']} {u['user__last_name']}".strip(),
            "email": u["user__email"],
            "role": u["role"],
            "is_active": u["is_active"],
            "created_at": u["created_at"],
        }
        for u in raw_users
    ]

    active_users = len([u for u in users_list if u["is_active"]])
    suspended_users = len(users_list) - active_users

    return JsonResponse(
        {
            "company": {
                "id": company.id,
                "name": company.name,
                "logo": company.logo.url if getattr(company, "logo", None) else None,
                "is_active": company.is_active,
                "created_at": company.created_at,
            },
            "subscription": subscription_info,
            "stats": {
                "users_total": len(users_list),
                "users_active": active_users,
                "users_inactive": suspended_users,
                "devices_count": 0,
            },
            "users": {
                "total": len(users_list),
                "active": active_users,
                "inactive": suspended_users,
                "list": users_list,
            },
        },
        status=200,
    )


# ====================================================================
# Helper — Latest Invoice
# ====================================================================
def _get_latest_invoice(subscription):
    if not subscription:
        return None

    last = (
        Invoice.objects
        .filter(subscription=subscription)
        .order_by("-created_at")
        .first()
    )

    if not last:
        return None

    return {
        "id": last.id,
        "amount": float(last.total_amount),
        "status": last.status,
        "created_at": last.created_at,
    }


# Alias
system_company_detail = company_detail


# ====================================================================
# 4) Company Create — PAID ONLY (AUTO ROLES ENABLED ✅)
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

    # ============================================================
    # 🔒 ACTIVE PAID SUBSCRIPTION
    # ============================================================
    sub = (
        AccountSubscription.objects
        .filter(owner=user, status="ACTIVE")
        .select_related("plan")
        .first()
    )

    if not sub or not sub.plan:
        return JsonResponse({"error": "لا يوجد اشتراك مدفوع نشط"}, status=403)

    # ============================================================
    # 🧮 Company Limit
    # ============================================================
    used = (
        CompanyUser.objects
        .filter(user=user, is_active=True)
        .values("company")
        .distinct()
        .count()
    )

    if used >= sub.plan.max_companies:
        return JsonResponse(
            {"error": "تم الوصول للحد الأقصى المسموح من الشركات"},
            status=403
        )

    # ============================================================
    # 🏢 Required Fields
    # ============================================================
    name = payload.get("name")
    email = payload.get("email")
    phone = payload.get("phone")

    if not name:
        return JsonResponse({"error": "اسم الشركة مطلوب"}, status=400)

    # ============================================================
    # 🏢 Atomic Create (Company + Roles + Owner)
    # ============================================================
    with transaction.atomic():
        # ----------------------------
        # 🏢 Create Company
        # ----------------------------
        company = Company.objects.create(
            name=name,
            email=email,
            phone=phone,
            is_active=True,
            owner=user,
        )

        # ----------------------------
        # 👤 Link Owner
        # ----------------------------
        CompanyUser.objects.create(
            user=user,
            company=company,
            role="owner",
            is_active=True,
        )

        # ----------------------------
        # 📦 Subscription Stub
        # ----------------------------
        CompanySubscription.objects.get_or_create(
            company=company,
            defaults={"status": "PENDING"},
        )

        # ----------------------------
        # 🎭 Auto Create Default Roles
        # ----------------------------
        for role_data in DEFAULT_COMPANY_ROLES:
            CompanyRole.objects.create(
                company=company,
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
                is_system_role=role_data["is_system_role"],
            )

    return JsonResponse(
        {
            "id": company.id,
            "name": company.name,
        },
        status=201,
    )
