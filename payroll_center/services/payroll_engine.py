# ================================================================
# 🏦 Payroll Engine — Enterprise Core (Model Compatible Version)
# 🟢 LEGAL PATCH: Leave ↔ Payroll Bridge (Saudi-Compliant)
# ================================================================

from decimal import Decimal
import logging
from calendar import monthrange

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from payroll_center.models import (
    PayrollRun,
    PayrollRecord,
    PayrollAdjustment,
    JournalEntry,
    JournalLine,
    PayrollSlipSnapshot,
)

from payroll_center.services.absence_engine import AbsenceDeductionEngine
from attendance_center.models import AttendanceRecord
from notification_center.services import create_notification

logger = logging.getLogger(__name__)


# ================================================================
# 💰 Salary Calculator
# ================================================================
def calculate_salary(
    *,
    base_salary: Decimal,
    allowances: Decimal = Decimal("0"),
    bonuses: Decimal = Decimal("0"),
    deductions: Decimal = Decimal("0"),
) -> Decimal:
    total = (base_salary + allowances + bonuses) - deductions
    return total.quantize(Decimal("0.01"))


# ================================================================
# 🧮 Calculate Payroll Run (With Legal Leave Filtering Layer)
# ================================================================
@transaction.atomic
def calculate_payroll_run(run: PayrollRun) -> PayrollRun:

    if run.status != "DRAFT":
        raise ValueError("PayrollRun must be in DRAFT state")

    records = PayrollRecord.objects.select_related(
        "employee",
        "employee__financial_info",
        "contract",
    ).filter(run=run)

    if not records.exists():
        PayrollRecord.create_for_run_from_active_employees(run)
        records = PayrollRecord.objects.select_related(
            "employee",
            "employee__financial_info",
            "contract",
        ).filter(run=run)

        if not records.exists():
            raise ValueError("No active employees found for payroll run")

    validation_errors = []

    for record in records:
        contract_salary = (
            record.contract.basic_salary
            if record.contract and getattr(record.contract, "basic_salary", None)
            else None
        )

        financial_salary = (
            record.employee.financial_info.basic_salary
            if getattr(record.employee, "financial_info", None)
            and getattr(record.employee.financial_info, "basic_salary", None)
            else None
        )

        if not contract_salary and not financial_salary:
            validation_errors.append(
                f"Employee '{record.employee.full_name}' has no salary source"
            )

    if validation_errors:
        raise ValueError(
            "Payroll validation failed:\n" + "\n".join(validation_errors)
        )

    year = run.month.year
    month_number = run.month.month
    start_date = run.month.replace(day=1)
    end_date = run.month.replace(day=monthrange(year, month_number)[1])

    DAYS_IN_MONTH = Decimal("30")

    absence_engine = AbsenceDeductionEngine(policy="FIXED_30")

    LeaveRequest = None
    try:
        from leave_center.models import LeaveRequest as _LeaveRequest
        LeaveRequest = _LeaveRequest
    except Exception:
        logger.warning("LeaveRequest model not found — Legal filtering skipped")

    for record in records:

        resolved_base_salary = None

        if record.contract and getattr(record.contract, "basic_salary", None):
            resolved_base_salary = record.contract.basic_salary
        elif (
            getattr(record.employee, "financial_info", None)
            and getattr(record.employee.financial_info, "basic_salary", None)
        ):
            resolved_base_salary = record.employee.financial_info.basic_salary

        resolved_base_salary = Decimal(resolved_base_salary)
        record.base_salary = resolved_base_salary

        attendance_qs = AttendanceRecord.objects.filter(
            employee=record.employee,
            date__range=(start_date, end_date),
        )

        legal_absent_days = 0

        if LeaveRequest:

            approved_leaves = LeaveRequest.objects.filter(
                employee=record.employee,
                status="approved",
                start_date__lte=end_date,
                end_date__gte=start_date,
            ).only(
                "start_date",
                "end_date",
                "pay_percentage",
            )

            leave_map = {}

            for leave in approved_leaves:
                current = leave.start_date
                while current <= leave.end_date:
                    leave_map[current] = leave
                    current += timezone.timedelta(days=1)

            for att in attendance_qs.filter(status="absent"):

                related_leave = leave_map.get(att.date)

                if related_leave:
                    pay_percentage = related_leave.pay_percentage or 0
                    if pay_percentage == 0:
                        legal_absent_days += 1
                else:
                    legal_absent_days += 1

        else:
            legal_absent_days = attendance_qs.filter(status="absent").count()

        # 🔹 هذه كانت مفقودة 🔹
        total_late_minutes = (
            attendance_qs.aggregate(total=Sum("late_minutes"))["total"] or 0
        )

        total_overtime_minutes = (
            attendance_qs.aggregate(total=Sum("overtime_minutes"))["total"] or 0
        )
        hourly_rate = resolved_base_salary / (DAYS_IN_MONTH * Decimal("8"))

        absence_deduction = absence_engine.calculate_deduction(
            monthly_salary=resolved_base_salary,
            absent_days=legal_absent_days,
        )

        late_deduction = Decimal(total_late_minutes) * (
            hourly_rate / Decimal("60")
        )

        overtime_amount = Decimal(total_overtime_minutes) * (
            hourly_rate / Decimal("60")
        )

        adjustments = PayrollAdjustment.objects.filter(
            run=run,
            employee=record.employee,
        )

        manual_additions = (
            adjustments.filter(type="ADDITION")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        manual_deductions = (
            adjustments.filter(type="DEDUCTION")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        record.overtime = overtime_amount
        record.bonus = manual_additions
        record.deductions = (
            absence_deduction + late_deduction + manual_deductions
        )

        salary = calculate_salary(
            base_salary=resolved_base_salary,
            allowances=Decimal(record.allowance),
            bonuses=record.bonus + record.overtime,
            deductions=record.deductions,
        )

        record.net_salary = salary

        record.breakdown = {
            "salary_source": "CONTRACT"
            if record.contract
            else "FINANCIAL_INFO",
            "base_salary": float(resolved_base_salary),
            "allowance": float(record.allowance),
            "absent_days_legal": int(legal_absent_days),
            "absence_deduction": float(absence_deduction),
            "late_minutes": int(total_late_minutes),
            "late_deduction": float(late_deduction),
            "overtime_minutes": int(total_overtime_minutes),
            "overtime_amount": float(overtime_amount),
            "manual_additions": float(manual_additions),
            "manual_deductions": float(manual_deductions),
            "final_net_salary": float(salary),
        }

        record.save()

    run.status = "CALCULATED"
    run.save(update_fields=["status"])
    return run


# ================================================================
# 🏦 Approve Payroll Run (Enterprise Safe — Journal + Snapshot)
# ================================================================
@transaction.atomic
def approve_payroll_run(run: PayrollRun) -> PayrollRun:
    if run.status != PayrollRun.Status.CALCULATED:
        raise ValueError("Only CALCULATED runs can be approved")

    company = run.company

    if JournalEntry.objects.filter(
        company=company,
        source=JournalEntry.Source.PAYROLL,
        source_id=run.id,
    ).exists():
        raise ValueError("Journal entry already exists for this payroll run")

    total = (
        PayrollRecord.objects
        .filter(run=run)
        .aggregate(total=Sum("net_salary"))["total"]
        or Decimal("0.00")
    )

    entry = JournalEntry.objects.create(
        company=company,
        source=JournalEntry.Source.PAYROLL,
        source_id=run.id,
        description=f"Payroll Run {run.month.strftime('%B %Y')}",
        date=timezone.now().date(),
        total_debit=total,
        total_credit=total,
    )

    JournalLine.objects.create(
        entry=entry,
        account_code="5100",
        account_name="Payroll Expense",
        debit=total,
        credit=Decimal("0.00"),
    )

    JournalLine.objects.create(
        entry=entry,
        account_code="2100",
        account_name="Payroll Payable",
        debit=Decimal("0.00"),
        credit=total,
    )

    records = PayrollRecord.objects.select_related("employee").filter(run=run)

    for record in records:
        if hasattr(record, "snapshot"):
            continue

        PayrollSlipSnapshot.objects.create(
            payroll_record=record,
            run=run,
            company=company,
            base_salary=record.base_salary,
            allowance=record.allowance,
            bonus=record.bonus,
            overtime=record.overtime,
            deductions=record.deductions,
            net_salary=record.net_salary,
            breakdown=record.breakdown or {},
        )

    run.status = PayrollRun.Status.APPROVED
    run.save(update_fields=["status"])
    return run


# ================================================================
# 🔁 Reset Payroll Run (Enterprise Safe — Non Destructive)
# ================================================================
@transaction.atomic
def reset_payroll_run(run: PayrollRun) -> PayrollRun:
    if run.status != PayrollRun.Status.CALCULATED:
        raise ValueError("Only CALCULATED runs can be reset")

    if JournalEntry.objects.filter(
        company=run.company,
        source=JournalEntry.Source.PAYROLL,
        source_id=run.id,
    ).exists():
        raise ValueError("Cannot reset payroll run with existing journal entry")

    PayrollSlipSnapshot.objects.filter(run=run).delete()

    records = PayrollRecord.objects.filter(run=run)

    for record in records:
        record.net_salary = Decimal("0.00")
        record.breakdown = None
        record.status = "PENDING"
        record.save(update_fields=["net_salary", "breakdown", "status"])

    run.status = PayrollRun.Status.DRAFT
    run.save(update_fields=["status"])
    return run


# ================================================================
# 💸 Mark Payroll Run as Paid (Lifecycle Complete)
# ================================================================
@transaction.atomic
def mark_payroll_run_paid(run: PayrollRun) -> PayrollRun:
    if run.status != PayrollRun.Status.APPROVED:
        raise ValueError("PayrollRun must be APPROVED before paying")

    records = PayrollRecord.objects.select_related("employee").filter(run=run)

    for record in records:
        record.status = "PAID"
        record.paid_at = timezone.now()
        record.save(update_fields=["status", "paid_at"])

        if record.employee and getattr(record.employee, "user", None):
            create_notification(
                recipient=record.employee.user,
                title="تم صرف الراتب",
                message=f"تم صرف راتب شهر {run.month.strftime('%B %Y')}",
                notification_type="payroll",
                severity="success",
            )

    run.status = PayrollRun.Status.PAID
    run.save(update_fields=["status"])
    return run

# ================================================================
# 💸 Mark Payroll Record as Paid (Partial / Full — C3.8 Enterprise)
# 🔐 Multi-Tenant Safe + Journal Isolated + Concurrency Safe
# ================================================================
@transaction.atomic
def mark_payroll_record_paid(
    record: PayrollRecord,
    payment_method: str,
    amount: Decimal,
    user=None,
) -> PayrollRecord:

    from decimal import ROUND_HALF_UP

    # 🔒 Row Lock لمنع الدفع المزدوج
    record = (
        PayrollRecord.objects
        .select_for_update()
        .select_related("run", "employee")
        .get(pk=record.pk)
    )

    run = record.run
    company = run.company

    # ============================================================
    # 🔐 Guards (Enterprise)
    # ============================================================
    if run.status != PayrollRun.Status.APPROVED:
        raise ValueError("PayrollRun must be APPROVED before payments")

    if payment_method not in ["CASH", "BANK"]:
        raise ValueError("Invalid payment method")

    if record.status == "PAID":
        raise ValueError("PayrollRecord already fully paid")

    # 🔢 Normalize amount (دقة محاسبية)
    amount = Decimal(amount).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    if amount <= 0:
        raise ValueError("Payment amount must be positive")

    paid_amount = (record.paid_amount or Decimal("0.00")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    net_salary = record.net_salary.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    remaining = (net_salary - paid_amount).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    if amount > remaining:
        raise ValueError("Payment exceeds remaining balance")

    # ============================================================
    # 🏦 Journal Entry (Per Settlement — Accounting Isolation C3.4)
    # ============================================================
    entry = JournalEntry.objects.create(
        company=company,
        source=JournalEntry.Source.PAYROLL_PAYMENT,
        source_id=record.id,
        description=(
            f"Payroll Payment — "
            f"{record.employee.full_name} — "
            f"{run.month.strftime('%B %Y')}"
        ),
        date=timezone.now().date(),
        total_debit=amount,
        total_credit=amount,
    )

    # 🧾 Debit Payroll Payable
    JournalLine.objects.create(
        entry=entry,
        account_code="2100",
        account_name="Payroll Payable",
        debit=amount,
        credit=Decimal("0.00"),
    )

    # 💵 Credit Cash / Bank
    if payment_method == "CASH":
        account_code = "1000"
        account_name = "Cash"
    else:
        account_code = "1010"
        account_name = "Bank"

    JournalLine.objects.create(
        entry=entry,
        account_code=account_code,
        account_name=account_name,
        debit=Decimal("0.00"),
        credit=amount,
    )

    # ============================================================
    # 🟢 Update Payment State
    # ============================================================
    new_paid_amount = (paid_amount + amount).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )
    # 🔢 مزامنة الراتب الصافي المقرب (حل احترافي لمشكلة الدقة)
    record.net_salary = net_salary
    record.paid_amount = new_paid_amount

    if new_paid_amount >= net_salary:
        record.status = "PAID"
        record.payment_method = payment_method
        record.paid_at = timezone.now()
    else:
        record.status = "PARTIAL"

    record.save(update_fields=[
        "paid_amount",
        "status",
        "payment_method",
        "paid_at",
    ])

    # 🔄 Auto close run إذا تم سداد الجميع
    if not run.records.exclude(status="PAID").exists():
        run.status = PayrollRun.Status.PAID
        run.save(update_fields=["status"])

    # 🔔 Notification (Fail-Safe — لا تؤثر على المعاملة المالية)
    try:
        if record.employee and getattr(record.employee, "user", None):
            create_notification(
                recipient=record.employee.user,
                title="💰 تم تسجيل دفعة راتب",
                message=(
                    f"تم تسجيل دفعة بقيمة {amount} "
                    f"لراتب {run.month.strftime('%B %Y')}"
                ),
                notification_type="payroll",
                severity="info",
            )
    except Exception as e:
        logger.warning(
            f"Notification failed after payroll payment "
            f"(non-blocking): {e}"
        )

        return record
