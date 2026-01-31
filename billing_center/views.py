# ============================================================
# 💳 Billing Center — Views V14.2 Ultra Stable
# Primey HR Cloud
# ============================================================

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ValidationError

import json

from billing_center.models import (
    Invoice,
    CompanySubscription,
    SubscriptionPlan,
)
from billing_center.services.discount_service import apply_discount_to_invoice
from billing_center.services.subscription_invoice_service import (
    generate_invoice_for_subscription_event,
)


# ------------------------------------------------------------
# 1) Dashboard — Premium Hybrid V15
# ------------------------------------------------------------
def billing_dashboard(request):

    chart_months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    chart_revenue = [1200, 1800, 900, 2100, 3500, 2800]

    invoices_count = 12
    total_revenue = sum(chart_revenue)
    avg_monthly = round(total_revenue / 6)

    subscription = {
        "plan_name": "Pro Plan",
        "renewal_date": "2025-12-01",
        "status": "active",
    }

    status_colors = {
        "paid": "success",
        "unpaid": "danger",
        "pending": "warning",
        "refunded": "secondary",
    }

    recent_invoices = [
        {"number": "INV-001", "amount": 350, "date": "2025-01-03", "status": "unpaid", "status_color": status_colors.get("unpaid")},
        {"number": "INV-002", "amount": 900, "date": "2025-01-01", "status": "paid", "status_color": status_colors.get("paid")},
        {"number": "INV-003", "amount": 199, "date": "2024-12-25", "status": "pending", "status_color": status_colors.get("pending")},
    ]

    recent_transactions = [
        {"type": "Payment", "amount": 900, "date": "2025-01-10"},
        {"type": "Refund", "amount": 200, "date": "2025-01-03"},
        {"type": "Payment", "amount": 1200, "date": "2024-12-28"},
    ]

    billing_alerts = [
        "⚠ لديك فاتورة غير مدفوعة (INV-001)",
        "ℹ سيتم التجديد تلقائيًا بتاريخ 01-12-2025",
    ]

    context = {
        "subscription": subscription,
        "invoices_count": invoices_count,
        "balance_due": 350,
        "recent_invoices": recent_invoices,
        "recent_transactions": recent_transactions,
        "billing_alerts": billing_alerts,
        "chart_months": chart_months,
        "chart_revenue": chart_revenue,
        "total_revenue": total_revenue,
        "avg_monthly": avg_monthly,
    }

    return render(request, "billing_center/billing_dashboard.html", context)


# ------------------------------------------------------------
# 2) قائمة الفواتير
# ------------------------------------------------------------
def billing_invoices(request):
    context = {
        "invoices": [
            {"id": 1, "number": "INV-001", "date": "2025-01-03", "amount": 350, "status": "unpaid", "type": "Renewal"},
            {"id": 2, "number": "INV-002", "date": "2025-01-01", "amount": 900, "status": "paid", "type": "Subscription"},
        ]
    }
    return render(request, "billing_center/billing_invoices.html", context)


# ------------------------------------------------------------
# 3) تفاصيل الفاتورة
# ------------------------------------------------------------
def billing_invoice_detail(request, invoice_id):
    invoice = {
        "id": invoice_id,
        "number": "INV-001",
        "date": "2025-01-03",
        "amount": 350,
        "discount": 0,
        "total": 350,
        "status": "unpaid",
        "type": "Renewal",
        "plan": "Pro Plan",
        "items": [
            {"name": "Renewal Fee", "description": "Monthly renewal", "price": 350}
        ]
    }
    return render(request, "billing_center/billing_invoice_detail.html", {"invoice": invoice})


# ------------------------------------------------------------
# 4) الخطط
# ------------------------------------------------------------
def billing_plans(request):
    plans = [
        {"id": 1, "name": "Basic", "price": 99, "period": "شهري", "features": ["5 موظفين", "دعم البريد"]},
        {"id": 2, "name": "Pro", "price": 199, "period": "شهري", "features": ["20 موظف", "لوحة BI", "مركز الحضور"]},
        {"id": 3, "name": "Enterprise", "price": 399, "period": "شهري", "features": ["بدون حدود", "دعم متقدم", "تكامل API"]},
    ]

    current_plan = plans[1]

    return render(request, "billing_center/billing_plans.html", {
        "plans": plans,
        "current_plan": current_plan,
    })


# ------------------------------------------------------------
# 5) تفاصيل الاشتراك الحالي
# ------------------------------------------------------------
def billing_subscription(request):
    subscription = {
        "plan_name": "Pro Plan",
        "start_date": "2025-01-01",
        "renewal_date": "2025-12-01",
        "status": "active",
        "price": 199,
        "period": "شهري",
        "users_count": 15,
        "features": ["20 موظف", "دعم", "تقارير متقدمة"],
        "is_expiring": False,
    }

    return render(request, "billing_center/billing_subscription.html", {
        "subscription": subscription
    })


# ------------------------------------------------------------
# 6) تعديل الاشتراك (UI فقط)
# ------------------------------------------------------------
def billing_subscription_edit(request):
    plans = [
        {"id": 1, "name": "Basic", "price": 99, "period": "شهري"},
        {"id": 2, "name": "Pro", "price": 199, "period": "شهري"},
        {"id": 3, "name": "Enterprise", "price": 399, "period": "شهري"},
    ]

    subscription = {
        "plan_id": 2,
        "period": "شهري",
        "users_count": 15,
        "discount_code": "",
        "total": 199,
    }

    return render(request, "billing_center/billing_subscription_edit.html", {
        "plans": plans,
        "subscription": subscription,
    })


# ------------------------------------------------------------
# 7) العمليات المالية
# ------------------------------------------------------------
def billing_transactions(request):
    transactions = [
        {"id": 1, "date": "2025-01-10", "type": "Payment", "amount": 900, "reference": "TX-2025-009", "status": "success"},
        {"id": 2, "date": "2025-01-03", "type": "Refund",  "amount": 200, "reference": "TX-2025-005", "status": "pending"},
        {"id": 3, "date": "2024-12-28", "type": "Payment", "amount": 1200, "reference": "TX-2024-998", "status": "failed"},
    ]
    return render(request, "billing_center/billing_transactions.html", {
        "transactions": transactions,
    })


# ------------------------------------------------------------
# 8) 🧾 Create Invoice API (Manual / Frontend)
# ------------------------------------------------------------
@csrf_exempt
def create_invoice(request):
    """
    Create Invoice
    - Optional discount_code
    - Discount applied ONCE at creation
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)

        company = request.user.company
        subscription = CompanySubscription.objects.filter(company=company).first()

        discount_code = data.get("discount_code")
        total_amount = data.get("total_amount")

        invoice = Invoice.objects.create(
            company=company,
            subscription=subscription,
            invoice_number=f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            issue_date=timezone.now().date(),
            total_amount=total_amount,
            status="PENDING",
        )

        if discount_code:
            apply_discount_to_invoice(invoice, discount_code)

        return JsonResponse({
            "success": True,
            "invoice_id": invoice.id,
            "total_amount": str(invoice.total_amount),
            "discount_amount": str(invoice.discount_amount or 0),
            "total_after_discount": str(
                invoice.total_after_discount or invoice.total_amount
            ),
        })

    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)

    except Exception:
        return JsonResponse({"error": "Failed to create invoice"}, status=500)


# ------------------------------------------------------------
# 9) 🔁 Change / Upgrade Subscription Plan (Auto Invoice)
# ------------------------------------------------------------
@csrf_exempt
def change_subscription_plan(request):
    """
    Change subscription plan
    - Generates invoice automatically (UPGRADE)
    - Optional discount_code
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)

        subscription = CompanySubscription.objects.get(
            company=request.user.company
        )

        new_plan = SubscriptionPlan.objects.get(
            id=data["plan_id"]
        )

        discount_code = data.get("discount_code")

        # 1) Update plan
        subscription.plan = new_plan
        subscription.save(update_fields=["plan"])

        # 2) Generate invoice for upgrade
        generate_invoice_for_subscription_event(
            subscription=subscription,
            event_type="UPGRADE",
            discount_code=discount_code,
        )

        return JsonResponse({"success": True})

    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)

    except Exception:
        return JsonResponse({"error": "Failed to change plan"}, status=500)
