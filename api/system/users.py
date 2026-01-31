from django.http import JsonResponse
from django.utils.timezone import now
from datetime import timedelta

from company_manager.models import CompanyUser


# ================================================================
# 👥 Users Overview API (Super Admin Level)
# ================================================================
def users_overview(request):
    """
    ملخص المستخدمين على مستوى النظام:
    - إجمالي المستخدمين
    - المستخدمون الجدد خلال 30 يوم
    - آخر 5 مستخدمين
    - ملاك الشركات
    """

    try:
        today = now().date()

        total_users = CompanyUser.objects.count()

        new_users_30_days = CompanyUser.objects.filter(
            created_at__gte=today - timedelta(days=30)
        ).count()

        latest_users = list(
            CompanyUser.objects
            .select_related("user", "company")
            .order_by("-created_at")
            .values(
                "id",
                "user__username",
                "user__email",
                "company__name",
                "role",
                "created_at",
            )[:5]
        )

        owners_list = list(
            CompanyUser.objects
            .select_related("user", "company")
            .filter(role__icontains="owner")
            .order_by("-created_at")
            .values(
                "id",
                "user__username",
                "user__email",
                "company__name",
                "created_at",
            )
        )

        return JsonResponse(
            {
                "status": "success",
                "users": {
                    "total": total_users,
                    "new_30_days": new_users_30_days,
                    "latest": latest_users,
                    "owners": owners_list,
                },
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "message": str(e),
            },
            status=500,
        )


# ================================================================
# 📋 Users List API (SYSTEM + COMPANY SCOPE ✅)
# ================================================================
def users_list(request, company_id=None):
    """
    قائمة مستخدمي النظام:
    - بدون company_id → كل المستخدمين (System)
    - مع company_id → مستخدمو شركة محددة
    """

    try:
        qs = (
            CompanyUser.objects
            .select_related("user", "company")
            .order_by("-created_at")
        )

        # 🔒 Company scope (اختياري)
        if company_id is not None:
            qs = qs.filter(company_id=company_id)

        users = list(
            qs.values(
                "id",
                "user__username",
                "user__email",
                "company__id",
                "company__name",
                "role",
                "is_active",
                "created_at",
            )
        )

        return JsonResponse(
            {
                "status": "success",
                "count": len(users),
                "results": users,
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "message": str(e),
            },
            status=500,
        )
