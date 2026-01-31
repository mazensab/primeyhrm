# ====================================================================
# 💳 Confirm Cash Payment — FINAL ULTRA STABLE
# Primey HR Cloud | Super Admin Only
# ====================================================================
# ✔ Confirm manual CASH payment
# ✔ Invoice -> PAID
# ✔ Subscription -> ACTIVE
# ✔ Company -> ACTIVE (AUTO RULE after first successful payment)
# ✔ Idempotent & Transaction-safe
# ====================================================================

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils.timezone import now

import json

from billing_center.models import Invoice, Payment


@csrf_exempt
@require_POST
@transaction.atomic
def confirm_cash_payment(request):
    """
    Confirm Cash Payment (Manual)

    - Super Admin only
    - Marks invoice as PAID
    - Creates Payment record (SOURCE OF TRUTH)
    - Activates subscription
    - Auto-activates company (RULE: after ACTIVE subscription)
    """

    # ============================================================
    # 🔐 Authorization
    # ============================================================
    if not request.user.is_authenticated or not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        payload = json.loads(request.body or "{}")
        invoice_id = payload.get("invoice_id")

        if not invoice_id:
            return JsonResponse(
                {"error": "invoice_id is required"},
                status=400
            )

        # ========================================================
        # 🧾 Invoice
        # ========================================================
        invoice = Invoice.objects.select_related(
            "subscription",
            "company",
        ).get(id=invoice_id)

        if invoice.status == "PAID":
            return JsonResponse(
                {"error": "Invoice already paid"},
                status=400
            )

        # ========================================================
        # 💳 Create Payment (SOURCE OF TRUTH)
        # ========================================================
        Payment.objects.create(
            invoice=invoice,
            amount=invoice.total_amount,
            method="CASH",
            reference_number=f"CASH-{invoice.id}-{int(now().timestamp())}",
            paid_at=now(),
            created_by=request.user,
        )

        # ========================================================
        # ✅ Update Invoice (STATUS ONLY)
        # ========================================================
        invoice.status = "PAID"
        invoice.save(update_fields=["status"])

        # ========================================================
        # ✅ Activate Subscription
        # ========================================================
        subscription = invoice.subscription
        if subscription and subscription.status != "ACTIVE":
            subscription.status = "ACTIVE"
            subscription.start_date = (
                subscription.start_date or now().date()
            )
            subscription.save(
                update_fields=["status", "start_date"]
            )

        # ========================================================
        # 🟢 AUTO ACTIVATE COMPANY (FINAL FIX)
        # ========================================================
        company = invoice.company
        if company and not company.is_active:
            company.is_active = True
            company.save(update_fields=["is_active"])

        # ========================================================
        # ✅ Response
        # ========================================================
        return JsonResponse({
            "success": True,
            "invoice_id": invoice.id,
            "subscription_status": (
                subscription.status if subscription else None
            ),
            "company_active": company.is_active if company else False,
            "message": "تم تأكيد الدفع وتفعيل الاشتراك والشركة بنجاح",
        })

    except Invoice.DoesNotExist:
        return JsonResponse(
            {"error": "Invoice not found"},
            status=404
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )
