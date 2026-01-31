# ============================================================
# 🏢 Company Status Actions — FINAL
# Primey HR Cloud | System
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction

from company_manager.models import Company
from billing_center.models import CompanySubscription


# ------------------------------------------------------------
# 🔐 Helpers
# ------------------------------------------------------------
def _get_company_or_404(company_id):
    try:
        return Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return None


def _has_active_subscription(company):
    return CompanySubscription.objects.filter(
        company=company,
        status="ACTIVE",
    ).exists()


# ============================================================
# ▶️ Activate Company
# ============================================================
@login_required
@require_POST
@transaction.atomic
def activate_company(request):
    company_id = request.POST.get("company_id")

    company = _get_company_or_404(company_id)
    if not company:
        return JsonResponse({"error": "Company not found"}, status=404)

    if company.is_active:
        return JsonResponse(
            {"error": "Company already active"},
            status=400,
        )

    if not _has_active_subscription(company):
        return JsonResponse(
            {
                "error": "NO_ACTIVE_SUBSCRIPTION",
                "message": "لا يوجد اشتراك نشط",
            },
            status=400,
        )

    company.is_active = True
    company.save(update_fields=["is_active"])

    return JsonResponse(
        {
            "success": True,
            "company_id": company.id,
            "status": "ACTIVE",
        }
    )


# ============================================================
# ⏸ Suspend Company
# ============================================================
@login_required
@require_POST
@transaction.atomic
def suspend_company(request):
    company_id = request.POST.get("company_id")

    company = _get_company_or_404(company_id)
    if not company:
        return JsonResponse({"error": "Company not found"}, status=404)

    if not company.is_active:
        return JsonResponse(
            {"error": "Company already suspended"},
            status=400,
        )

    company.is_active = False
    company.save(update_fields=["is_active"])

    return JsonResponse(
        {
            "success": True,
            "company_id": company.id,
            "status": "SUSPENDED",
        }
    )


# ============================================================
# 🔁 Reactivate Company
# ============================================================
@login_required
@require_POST
@transaction.atomic
def reactivate_company(request):
    company_id = request.POST.get("company_id")

    company = _get_company_or_404(company_id)
    if not company:
        return JsonResponse({"error": "Company not found"}, status=404)

    if company.is_active:
        return JsonResponse(
            {"error": "Company already active"},
            status=400,
        )

    if not _has_active_subscription(company):
        return JsonResponse(
            {
                "error": "NO_ACTIVE_SUBSCRIPTION",
                "message": "لا يوجد اشتراك نشط",
            },
            status=400,
        )

    company.is_active = True
    company.save(update_fields=["is_active"])

    return JsonResponse(
        {
            "success": True,
            "company_id": company.id,
            "status": "ACTIVE",
        }
    )
