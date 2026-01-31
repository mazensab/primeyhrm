# ===============================================================
# 📂 الملف: payroll_center/services.py — V8.5 ULTRA PRO (FINAL)
# 🧠 Primey HR Cloud — Payroll Engine + PayrollSummary V8
# ===============================================================
# ✔ Pure Salary Calculation
# ✔ Payroll Run Lifecycle (DRAFT → CALCULATED → APPROVED → PAID)
# ✔ Safe Reset
# ✔ Notifications
# ✔ PayrollSummary V8 (Golden Core)
# ✔ Accounting Journal Entry (Double Entry)
# ===============================================================

from decimal import Decimal
import logging

from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Avg, Count, Max, Min

from notification_center.services import create_notification
from employee_center.models import Employee
from .models import (
    PayrollRun,
    PayrollRecord,
    JournalEntry,
    JournalLine,
)

logger = logging.getLogger(__name__)

# ===============================================================
# 🧩 1️⃣ Salary Calculation (PURE FUNCTION)
# ===============================================================
def calculate_salary(
    *,
    base_salary: Decimal,
    allowances: Decimal = Decimal("0"),
    bonuses: Decimal = Decimal("0"),
    deductions: Decimal = Decimal("0"),
) -> Decimal:
    """
    Calculate net salary with NO side effects.
    """
    total = (base_salary + allowances + bonuses) - deductions
    return total.quantize(Decimal("0.01"))


# ===============================================================
# 🧮 2️⃣ Payroll Run — Calculate
# DRAFT → CALCULATED
# ===============================================================
@transaction.atomic
def calculate_payroll_run(run: PayrollRun) -> PayrollRun:
    if run.status != PayrollRun.Status.DRAFT:
        raise ValueError("PayrollRun must be in DRAFT state")

    records = PayrollRecord.objects.select_related(
        "employee"
    ).filter(run=run)

    if not records.exists():
        raise ValueError("No payroll records found for this run")

    total_net = Decimal("0.00")

    for record in records:
        salary = calculate_salary(
            base_salary=Decimal(record.base_salary),
            allowances=Decimal(record.allowances),
            bonuses=Decimal(record.bonus),
            deductions=Decimal(record.deductions),
        )

        record.net_salary = salary
        record.status = PayrollRecord.Status.CALCULATED
        record.save(update_fields=["net_salary", "status"])

        total_net += salary

    run.total_net = total_net
    run.status = PayrollRun.Status.CALCULATED
    run.calculated_at = timezone.now()
    run.save(update_fields=["total_net", "status", "calculated_at"])

    logger.info(
        f"🧮 PayrollRun #{run.id} CALCULATED — Total: {total_net}"
    )

    return run


# ===============================================================
# 💸 3️⃣ Mark Payroll Run as PAID
# APPROVED → PAID
# ===============================================================
@transaction.atomic
def mark_payroll_run_paid(run: PayrollRun) -> PayrollRun:
    if run.status != PayrollRun.Status.APPROVED:
        raise ValueError("PayrollRun must be APPROVED before paying")

    records = PayrollRecord.objects.select_related(
        "employee", "employee__user"
    ).filter(run=run)

    paid_at = timezone.now()

    for record in records:
        record.status = PayrollRecord.Status.PAID
        record.paid_at = paid_at
        record.save(update_fields=["status", "paid_at"])

        if record.employee.user:
            create_notification(
                recipient=record.employee.user,
                title="✅ تم صرف راتبك الشهري",
                message=(
                    f"تم صرف راتب شهر {run.month}/{run.year} "
                    f"بقيمة {record.net_salary:,.2f} ريال."
                ),
                notification_type="payroll",
                severity="success",
            )

    run.status = PayrollRun.Status.PAID
    run.paid_at = paid_at
    run.save(update_fields=["status", "paid_at"])

    logger.info(f"💸 PayrollRun #{run.id} marked as PAID")

    return run


# ===============================================================
# 📊 4️⃣ Payroll Summary — LEGACY SAFE
# ===============================================================
def payroll_summary_basic() -> dict:
    """
    Backward compatible summary.
    """
    today = timezone.now().date()
    month = today.replace(day=1)

    payrolls = PayrollRecord.objects.filter(
        run__month=month.month,
        run__year=month.year,
    )

    return {
        "count": payrolls.count(),
        "paid": payrolls.filter(
            status=PayrollRecord.Status.PAID
        ).aggregate(Sum("net_salary"))["net_salary__sum"] or 0,
        "pending": payrolls.exclude(
            status=PayrollRecord.Status.PAID
        ).aggregate(Sum("net_salary"))["net_salary__sum"] or 0,
    }


# ===============================================================
# ⭐ 5️⃣ PayrollSummary V8 — GOLDEN CORE
# ===============================================================
def payroll_summary_v8(*, month=None, year=None) -> dict:
    today = timezone.now().date()
    month = month or today.month
    year = year or today.year

    runs = PayrollRun.objects.filter(
        month=month,
        year=year,
        status__in=[
            PayrollRun.Status.CALCULATED,
            PayrollRun.Status.APPROVED,
            PayrollRun.Status.PAID,
        ],
    )

    records = PayrollRecord.objects.filter(run__in=runs)

    totals = records.aggregate(
        total=Sum("net_salary"),
        paid=Sum(
            "net_salary",
            filter=records.filter(
                status=PayrollRecord.Status.PAID
            ),
        ),
        avg=Avg("net_salary"),
        max=Max("net_salary"),
        min=Min("net_salary"),
    )

    by_department = records.values(
        "employee__department__name"
    ).annotate(
        total=Sum("net_salary"),
        count=Count("id"),
    )

    by_contract = records.values(
        "employee__contract__contract_type"
    ).annotate(
        total=Sum("net_salary"),
        count=Count("id"),
    )

    return {
        "month": f"{month}/{year}",
        "runs_count": runs.count(),
        "employees_count": records.values("employee").distinct().count(),
        "total": totals["total"] or 0,
        "paid": totals["paid"] or 0,
        "pending": (totals["total"] or 0) - (totals["paid"] or 0),
        "avg": totals["avg"] or 0,
        "max": totals["max"] or 0,
        "min": totals["min"] or 0,
        "by_department": list(by_department),
        "by_contract": list(by_contract),
    }


# ===============================================================
# 🔁 6️⃣ Reset Payroll Run
# CALCULATED → DRAFT
# ===============================================================
@transaction.atomic
def reset_payroll_run(run: PayrollRun) -> PayrollRun:
    if run.status != PayrollRun.Status.CALCULATED:
        raise ValueError("Only CALCULATED runs can be reset")

    records = PayrollRecord.objects.filter(run=run)

    for record in records:
        record.net_salary = Decimal("0.00")
        record.status = PayrollRecord.Status.DRAFT
        record.save(update_fields=["net_salary", "status"])

    run.status = PayrollRun.Status.DRAFT
    run.total_net = Decimal("0.00")
    run.calculated_at = None
    run.save(update_fields=["status", "total_net", "calculated_at"])

    logger.warning(
        f"🔁 PayrollRun #{run.id} RESET to DRAFT"
    )

    return run


# ===============================================================
# 🧾 7️⃣ Accounting — Create Journal Entry
# ===============================================================
@transaction.atomic
def create_payroll_journal_entry(run: PayrollRun):
    if run.status not in [
        PayrollRun.Status.APPROVED,
        PayrollRun.Status.PAID,
    ]:
        raise ValueError("PayrollRun must be APPROVED or PAID")

    if JournalEntry.objects.filter(
        source="PAYROLL",
        source_id=run.id
    ).exists():
        logger.warning(
            f"🧾 Journal already exists for PayrollRun #{run.id}"
        )
        return None

    total = run.total_net

    entry = JournalEntry.objects.create(
        source="PAYROLL",
        source_id=run.id,
        description=f"Payroll {run.month}/{run.year}",
        total_debit=total,
        total_credit=total,
    )

    JournalLine.objects.create(
        entry=entry,
        account_code="5100",
        account_name="Payroll Expense",
        debit=total,
        credit=0,
    )

    JournalLine.objects.create(
        entry=entry,
        account_code="2100",
        account_name="Payroll Payable",
        debit=0,
        credit=total,
    )

    logger.info(
        f"🧾 JournalEntry created for PayrollRun #{run.id}"
    )

    return entry
