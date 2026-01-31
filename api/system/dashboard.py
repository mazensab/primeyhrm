# ====================================================================
# 🟦 System Dashboard API — V15.7 FINAL STABLE (BACKEND FIX ONLY)
# Primey HR Cloud
# ====================================================================

from django.http import JsonResponse
from django.utils.timezone import now
from django.db.models import Sum
from datetime import datetime, timedelta

from company_manager.models import Company, CompanyUser
from employee_center.models import Employee
from billing_center.models import CompanySubscription, PaymentTransaction

# ⚠️ Biotime optional
try:
    from biotime_center.models import BiotimeDevice
except Exception:
    BiotimeDevice = None


def system_dashboard(request):
    today = now().date()

    # ============================================================
    # 🟡 Date Range (SAFE)
    # ============================================================
    try:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end_date = today
            start_date = today - timedelta(days=30)
    except Exception:
        end_date = today
        start_date = today - timedelta(days=30)

    # ============================================================
    # 🧱 SAFE RESPONSE STRUCTURE (DO NOT BREAK FRONTEND)
    # ============================================================
    metrics = {
        "companies": {"total": 0, "latest": []},
        "subscriptions": {"active": 0, "expired": 0, "pending": 0},
        "billing": {"invoices_month": 0, "revenue_month": 0},
        "users": {"total": 0, "latest": []},
        "employees_total": 0,
        "devices": {"total": 0, "problematic": []},
        "payments": {"latest": []},
        "health": {
            "api": "ok",
            "scheduler": "running",
            "redis": "ok",
            "errors_24h": 0,
        },
    }

    # ============================================================
    # 💳 PAYMENTS — FINAL FIX (STATUS IS SOURCE OF TRUTH)
    # ============================================================
    try:
        tx_qs = (
            PaymentTransaction.objects
            .select_related("company")
            .filter(status__in=["COMPLETED", "PAID"])
            .order_by("-created_at")
        )

        # Monthly KPIs
        month_tx = tx_qs.filter(
            created_at__date__range=(start_date, end_date)
        )

        metrics["billing"]["invoices_month"] = month_tx.count()
        metrics["billing"]["revenue_month"] = float(
            month_tx.aggregate(total=Sum("amount"))["total"] or 0
        )

        # 🔑 SAME KEYS EXPECTED BY DASHBOARD UI
        metrics["payments"]["latest"] = [
            {
                "id": tx.id,
                "amount": float(tx.amount or 0),
                "status": tx.status,                     # PAID / COMPLETED
                "method": tx.payment_method,             # CASH / BANK / ONLINE
                "paid_at": tx.created_at,                # ✔ EXISTS
                "invoice__company__name": (
                    tx.company.name if tx.company else "—"
                ),
            }
            for tx in tx_qs[:10]
        ]

    except Exception as e:
        print("Dashboard payments error:", e)

    # ============================================================
    # 🏢 Companies (UNCHANGED)
    # ============================================================
    try:
        qs = Company.objects.all()
        metrics["companies"]["total"] = qs.count()

        latest = []
        for c in qs.order_by("-created_at")[:5]:
            sub = (
                CompanySubscription.objects
                .filter(company=c, status="ACTIVE")
                .select_related("plan")
                .first()
            )

            latest.append({
                "id": c.id,
                "name": c.name,
                "status": "نشطة" if c.is_active else "موقوفة",
                "city": getattr(c, "city", None),
                "plan_name": sub.plan.name if sub and sub.plan else None,
                "subscription_start": sub.start_date if sub else None,
                "subscription_end": sub.end_date if sub else None,
                "created_at": c.created_at,
            })

        metrics["companies"]["latest"] = latest
    except Exception:
        pass

    # ============================================================
    # 👤 Users
    # ============================================================
    try:
        qs = CompanyUser.objects.select_related("user", "company")
        metrics["users"]["total"] = qs.count()
        metrics["users"]["latest"] = list(
            qs.order_by("-created_at").values(
                "user__username",
                "user__email",
                "company__name",
                "created_at",
            )[:5]
        )
    except Exception:
        pass

    # ============================================================
    # 👷 Employees
    # ============================================================
    try:
        metrics["employees_total"] = Employee.objects.count()
    except Exception:
        pass

    # ============================================================
    # 📄 Subscriptions KPIs
    # ============================================================
    try:
        subs = CompanySubscription.objects.all()
        metrics["subscriptions"]["active"] = subs.filter(status="ACTIVE").count()
        metrics["subscriptions"]["expired"] = subs.filter(status="EXPIRED").count()
        metrics["subscriptions"]["pending"] = subs.filter(status="PENDING_PAYMENT").count()
    except Exception:
        pass

    # ============================================================
    # 🖥️ Devices (OPTIONAL)
    # ============================================================
    if BiotimeDevice:
        try:
            qs = BiotimeDevice.objects.all()
            metrics["devices"]["total"] = qs.count()
            metrics["devices"]["problematic"] = list(
                qs.filter(last_sync__lte=now() - timedelta(hours=24)).values()[:10]
            )
        except Exception:
            pass

    # ============================================================
    # ✅ FINAL RESPONSE
    # ============================================================
    return JsonResponse(
        {
            "metrics": metrics,
            "range": {
                "start_date": str(start_date),
                "end_date": str(end_date),
            },
        },
        status=200,
    )
