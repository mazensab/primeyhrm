# ============================================================
# 📂 api/system/onboarding/pending_drafts.py
# Mham Cloud
# Pending Bank Transfer Onboarding Drafts
# ============================================================

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from billing_center.models import CompanyOnboardingTransaction


@require_GET
@login_required
def pending_onboarding_drafts(request):
    drafts = (
        CompanyOnboardingTransaction.objects
        .select_related("plan")
        .filter(
            payment_method="BANK_TRANSFER",
            status__in=["DRAFT", "CONFIRMED"],
        )
        .order_by("-created_at")
    )

    return JsonResponse(
        {
            "drafts": [
                {
                    "draft_id": draft.id,
                    "company_name": draft.company_name,
                    "plan_name": draft.plan.name if draft.plan else "-",
                    "duration": draft.duration,
                    "payment_method": draft.payment_method,
                    "status": draft.status,
                    "total_amount": float(draft.total_amount or 0),
                    "created_at": draft.created_at.isoformat() if draft.created_at else None,
                    "admin_name": draft.admin_name,
                    "admin_email": draft.admin_email,
                }
                for draft in drafts
            ]
        },
        status=200,
    )