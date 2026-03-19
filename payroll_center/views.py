# ============================================================
# 📂 payroll_center/views.py — V12.7 ULTRA STABLE (FINAL)
# Primey HR Cloud | Payroll Module
# ============================================================

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Avg
from django.views.decorators.http import require_POST

# ============================================================
# 🔗 Models
# ============================================================
from .models import (
    PayrollRecord,
    PayrollRecordHistory,
    PayrollRun,
)

from employee_center.models import Employee, Contract
from attendance_center.models import AttendanceRecord

# ============================================================
# 📊 Services (Single Source of Truth)
# ============================================================
from .services import (
    calculate_payroll_run,
    mark_payroll_run_paid,
    reset_payroll_run,
)

# ============================================================
# 🖨️ Printing Engine
# ============================================================

# ============================================================
# 🧾 0️⃣ Payroll List
# ============================================================
@login_required
def payroll_list(request):
    qs = (
        PayrollRecord.objects
        .select_related("employee", "contract")
        .order_by("-created_at")
    )

    return render(
        request,
        "payroll_center/payroll_list.html",
        {
            "page_title": "قائمة الرواتب",
            "payrolls": qs,
            "total": qs.aggregate(
                Sum("net_salary")
            )["net_salary__sum"] or 0,
            "avg": qs.aggregate(
                Avg("net_salary")
            )["net_salary__avg"] or 0,
            "count": qs.count(),
        }
    )


# ============================================================
# 📊 1️⃣ Payroll Dashboard
# ============================================================
@login_required
def payroll_dashboard(request):
    summary = payroll_summary_v8()

    departments = (
        PayrollRecord.objects
        .values("employee__department__name")
        .annotate(total=Sum("net_salary"))
        .order_by("-total")
    )

    status_chart = (
        PayrollRecord.objects
        .values("status")
        .annotate(total=Sum("net_salary"))
    )

    latest = PayrollRecord.objects.order_by("-created_at")[:10]

    return render(
        request,
        "payroll_center/payroll_dashboard.html",
        {
            "page_title": "لوحة الرواتب",
            "summary": summary,
            "departments": departments,
            "status_chart": status_chart,
            "latest": latest,
        }
    )


# ============================================================
# ⚖️ 2️⃣ Compliance Check (READ ONLY)
# ============================================================
@login_required
def payroll_compliance_check(request):
    results = []

    for p in PayrollRecord.objects.select_related(
        "employee", "contract"
    ):
        base = (
            p.base_salary
            or (p.contract.basic_salary if p.contract else 0)
        )

        results.append({
            "employee": p.employee.full_name,
            "base_salary": base,
            "status": "ok" if base >= 4000 else "critical",
        })

    return JsonResponse({"results": results})


# ============================================================
# 🧾 3️⃣ Payroll Detail
# ============================================================
@login_required
def payroll_detail(request, pk):
    payroll = get_object_or_404(PayrollRecord, pk=pk)

    return render(
        request,
        "payroll_center/payroll_detail.html",
        {
            "payroll": payroll,
            "logs": payroll.history_logs.all(),
        }
    )


# ============================================================
# 📊 4️⃣ Attendance ↔ Payroll Analysis
# ============================================================
@login_required
def payroll_attendance_analysis(request):
    items = []

    for p in PayrollRecord.objects.select_related("employee"):
        attendance = AttendanceRecord.objects.filter(
            employee=p.employee,
            date__year=p.month.year,
            date__month=p.month.month,
        )

        items.append({
            "employee": p.employee.full_name,
            "month": p.month.strftime("%Y-%m"),
            "late": attendance.filter(is_late=True).count(),
            "absent": attendance.filter(is_absent=True).count(),
            "overtime": attendance.aggregate(
                Sum("overtime_minutes")
            )["overtime_minutes__sum"] or 0,
            "net_salary": p.net_salary,
        })

    return JsonResponse({"items": items})


# ============================================================
# 🖨️ Printing — Unified
# ============================================================
@login_required
def payroll_payslip_pdf(request, pk):
    return _render_payslip(pk, "standard")


@login_required
def payroll_payslip_v2(request, pk):
    return _render_payslip(pk, "glass")


@login_required
def payroll_payslip_v5_signature(request, pk):
    return _render_payslip(pk, "signature")


@login_required
def payroll_payslip_thermal(request, pk):
    return _render_payslip(pk, "thermal")


@login_required
def payroll_quick_print(request, pk):
    response = _render_payslip(pk, "standard")
    response["Content-Disposition"] = "inline"
    return response


@login_required
def payroll_payslip_download(request, pk):
    response = _render_payslip(pk, "standard")
    response["Content-Disposition"] = "attachment"
    return response


def _render_payslip(pk, mode):
    payroll = get_object_or_404(PayrollRecord, pk=pk)

    engine = PayrollSlipPrintEngine(
        payroll=payroll,
        company=payroll.employee.company,
        mode=mode,
    )

    pdf = engine.render_pdf()
    return HttpResponse(pdf, content_type="application/pdf")


# ============================================================
# 🧾 PAYROLL RUN — LIST
# ============================================================
@login_required
def payroll_run_list(request):
    company_user = (
        request.user.company_users
        .select_related("company")
        .filter(is_active=True)
        .order_by("-id")
        .first()
    )

    if not company_user:
        return JsonResponse({"runs": []})

    runs = (
        PayrollRun.objects
        .filter(company=company_user.company)
        .prefetch_related("records__employee")
        .order_by("-year", "-month")
    )

    data = []
    for run in runs:
        records = run.records.all()
        data.append({
            "id": run.id,
            "month": f"{run.month}/{run.year}",
            "status": run.status,
            "employees_count": records.count(),
            "total_net": records.aggregate(
                Sum("net_salary")
            )["net_salary__sum"] or 0,
        })

    if request.GET.get("format") == "json":
        return JsonResponse({"runs": data})

    return render(
        request,
        "payroll_center/run_list.html",
        {
            "page_title": "دورات الرواتب",
            "runs": data,
        }
    )


# ============================================================
# 🧾 PAYROLL RUN — DETAIL
# ============================================================
@login_required
def payroll_run_detail(request, pk):
    run = get_object_or_404(
        PayrollRun.objects.prefetch_related(
            "records__employee",
            "records__contract",
        ),
        pk=pk,
    )

    records_qs = run.records.all().order_by(
        "employee__full_name"
    )

    records = [
        {
            "employee_id": r.employee.id,
            "employee_name": r.employee.full_name,
            "base_salary": float(r.base_salary),
            "allowances": float(r.allowances),
            "deductions": float(r.deductions),
            "net_salary": float(r.net_salary),
            "status": r.status,
        }
        for r in records_qs
    ]

    summary = {
        "total_employees": records_qs.count(),
        "total_net": records_qs.aggregate(
            Sum("net_salary")
        )["net_salary__sum"] or 0,
    }

    if request.GET.get("format") == "json":
        return JsonResponse({
            "run": {
                "id": run.id,
                "month": run.month,
                "year": run.year,
                "status": run.status,
            },
            "summary": summary,
            "records": records,
        })

    return render(
        request,
        "payroll_center/run_detail.html",
        {
            "page_title": f"دورة رواتب {run.month}/{run.year}",
            "run": run,
            "records": records_qs,
            "summary": summary,
        }
    )


# ============================================================
# 🧮 PAYROLL RUN — CALCULATE
# ============================================================
@login_required
@require_POST
@transaction.atomic
def payroll_run_calculate(request, run_id):
    run = get_object_or_404(
        PayrollRun.objects.select_for_update(),
        pk=run_id,
    )

    try:
        calculate_payroll_run(run)

        return JsonResponse({
            "status": "calculated",
            "run_id": run.id,
            "total_net": run.total_net,
        })

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )


# ============================================================
# ✅ PAYROLL RUN — APPROVE
# ============================================================
@login_required
@require_POST
@transaction.atomic
def payroll_run_approve(request, pk):
    run = get_object_or_404(
        PayrollRun.objects.select_for_update(),
        pk=pk,
    )

    if run.status != PayrollRun.Status.CALCULATED:
        return JsonResponse(
            {"error": "Invalid state"},
            status=400,
        )

    run.status = PayrollRun.Status.APPROVED
    run.approved_at = timezone.now()
    run.approved_by = request.user
    run.save(
        update_fields=[
            "status",
            "approved_at",
            "approved_by",
        ]
    )

    return JsonResponse({"status": "approved"})


# ============================================================
# 💸 PAYROLL RUN — PAY
# ============================================================
@login_required
@require_POST
@transaction.atomic
def payroll_run_pay(request, pk):
    run = get_object_or_404(
        PayrollRun.objects.select_for_update(),
        pk=pk,
    )

    try:
        mark_payroll_run_paid(run)
        create_payroll_journal_entry(run)

        return JsonResponse({
            "status": "paid",
            "run_id": run.id,
        })

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )


# ============================================================
# 🔁 PAYROLL RUN — RESET
# ============================================================
@login_required
@require_POST
@transaction.atomic
def payroll_run_reset(request, run_id):
    run = get_object_or_404(
        PayrollRun.objects.select_for_update(),
        pk=run_id,
    )

    try:
        reset_payroll_run(run)

        return JsonResponse({
            "success": True,
            "run_id": run.id,
            "status": run.status,
        })

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )
# ============================================================
# 🧮 PAYROLL RUN — CALCULATE COMMIT (ALIAS FOR URL COMPATIBILITY)
# ============================================================

@login_required
@require_POST
@transaction.atomic
def payroll_run_calculate_commit(request, pk):
    """
    Alias endpoint
    ------------------------------------------------------------
    ✔ Keeps backward compatibility with urls.py
    ✔ Internally uses payroll_run_calculate logic
    ✔ Does NOT duplicate business logic
    ------------------------------------------------------------
    """

    run = get_object_or_404(
        PayrollRun.objects.select_for_update(),
        pk=pk,
    )

    try:
        calculate_payroll_run(run)

        return JsonResponse({
            "status": "calculated",
            "run_id": run.id,
            "total_net": run.total_net,
        })

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )
# ============================================================
# ⚙️ PAYROLL AUTO GENERATE (LEGACY / SAFE ALIAS)
# ============================================================

@login_required
@transaction.atomic
def payroll_auto_generate(request):
    """
    Legacy endpoint kept for compatibility
    --------------------------------------
    ✔ Does NOT break urls.py
    ✔ Can be deprecated later safely
    ✔ Uses current PayrollRun logic
    """

    # في النسخ الحديثة، التوليد يتم عبر PayrollRun
    # لذلك نُرجع استجابة آمنة بدون تنفيذ خاطئ

    return JsonResponse({
        "status": "disabled",
        "message": (
            "Auto generate payrolls is deprecated. "
            "Use Payroll Runs instead."
        )
    })
