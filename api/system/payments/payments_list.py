# ============================================================
# 💳 SYSTEM — Payments List (READ ONLY)
# Primey HR Cloud
# ============================================================
# ✔ Safe Read Only
# ✔ Status derived from payment state
# ✔ Uses invoice issued_at as fallback display date
# ✔ Supports filters (company / method / date)
# ✔ No side effects
# ============================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.utils.dateparse import parse_date

from billing_center.models import Payment


@require_GET
@login_required
def list_payments(request):
    """
    ============================================================
    🔒 SYSTEM PAYMENTS LIST
    - Read only
    - Ordered by EFFECTIVE payment date
    - Supports filters:
        ?company_id=
        ?method=
        ?date_from=
        ?date_to=
    ============================================================
    """

    qs = (
        Payment.objects
        .select_related("invoice", "invoice__company")
        .order_by("-paid_at", "-id")  # ✅ ترتيب آمن فعليًا
    )

    # ------------------------------------------------------------
    # 🔍 Filters
    # ------------------------------------------------------------

    company_id = request.GET.get("company_id")
    method = request.GET.get("method")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    if company_id:
        qs = qs.filter(invoice__company_id=company_id)

    if method:
        qs = qs.filter(method=method)

    if date_from:
        df = parse_date(date_from)
        if df:
            qs = qs.filter(invoice__issued_at__date__gte=df)

    if date_to:
        dt = parse_date(date_to)
        if dt:
            qs = qs.filter(invoice__issued_at__date__lte=dt)

    # ------------------------------------------------------------
    # 📦 Serialize
    # ------------------------------------------------------------

    data = []

    for p in qs:
        is_paid = p.paid_at is not None or p.status == "PAID"

        # ✅ التاريخ المعتمد للعرض
        display_date = (
            p.paid_at
            or (p.invoice.issued_at if p.invoice else None)
        )

        company_name = (
            p.invoice.company.name
            if p.invoice and p.invoice.company
            else None
        )

        data.append({
            "id": p.id,
            "amount": float(p.amount),
            "status": "PAID" if is_paid else "PENDING",
            "method": p.method,

            # Invoice
            "invoice_id": p.invoice_id,
            "invoice_number": (
                p.invoice.invoice_number
                if p.invoice else None
            ),

            # Company (✅ FIX)
            "company_id": (
                p.invoice.company_id
                if p.invoice else None
            ),
            "company_name": company_name,  # ✅ Frontend friendly
            "invoice__company__name": company_name,  # 🔒 Backward compatible

            # Date
            "paid_at": display_date,

            # Reference
            "reference": p.reference_number,
        })

    return JsonResponse(
        data,
        safe=False,
        json_dumps_params={"ensure_ascii": False},
    )
