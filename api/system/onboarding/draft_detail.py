# ============================================================
# 📂 api/system/onboarding/draft_detail.py
# Primey HR Cloud
# Get Draft Details for Payment Page
# V2.0 PUBLIC SAFE
# ============================================================

from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from billing_center.models import CompanyOnboardingTransaction


VAT_RATE = Decimal("0.15")


# ============================================================
# 🧾 Draft Detail API
# ============================================================

@require_GET
def draft_detail(request, draft_id):
    """
    Return draft information for the payment / review page
    Supports both:
    - Internal flow
    - Public onboarding flow
    """

    try:
        draft = (
            CompanyOnboardingTransaction.objects
            .select_related("plan")
            .get(id=draft_id)
        )

        plan = draft.plan

        # ------------------------------------------------
        # Use Stored Draft Pricing (Source of Truth)
        # ------------------------------------------------
        base_price = draft.base_price or Decimal("0.00")
        discount_amount = draft.discount_amount or Decimal("0.00")
        vat = draft.vat_amount or Decimal("0.00")
        total = draft.total_amount or Decimal("0.00")

        # ------------------------------------------------
        # Response
        # ------------------------------------------------
        return JsonResponse({
            "draft_id": draft.id,
            "status": draft.status,

            "company_name": draft.company_name,

            "plan": {
                "id": plan.id if plan else None,
                "name": plan.name if plan else None,
            },

            "duration": draft.duration,

            "pricing": {
                "base_price": float(base_price),
                "discount_amount": float(discount_amount),
                "vat": float(vat),
                "total": float(total),
            },

            "dates": {
                "start_date": draft.start_date.isoformat() if draft.start_date else None,
                "end_date": draft.end_date.isoformat() if draft.end_date else None,
            },

            "admin": {
                "username": draft.admin_username,
                "name": draft.admin_name,
                "email": draft.admin_email,
            },

            "company": {
                "commercial_number": draft.commercial_number,
                "tax_number": draft.tax_number,
                "phone": draft.phone,
                "email": draft.email,
                "city": draft.city,
                "national_address": draft.national_address or {},
            },

            # ------------------------------------------------
            # Extra flags for public onboarding flow
            # ------------------------------------------------
            "payment_method": getattr(draft, "payment_method", None),
            "is_public_flow": getattr(draft, "owner_id", None) is None,
        })

    except CompanyOnboardingTransaction.DoesNotExist:
        return JsonResponse(
            {"error": "Draft not found"},
            status=404
        )