# ================================================================
# 📊 Payroll Reporting — Advanced Layer (C3 Hardened)
# 🔒 Company Scoped + Accounting Safe
# ================================================================

from decimal import Decimal
from django.db.models import Sum
from payroll_center.models import PayrollRun, PayrollRecord, JournalEntry


# ================================================================
# 📊 Financial Summary (Company Scoped)
# ================================================================

def get_payroll_run_financial_summary(run: PayrollRun) -> dict:
    """
    Enterprise Financial Summary for a PayrollRun.
    Company Scoped.
    Compatible with current PayrollRecord model.
    """

    company = run.company
    records = PayrollRecord.objects.filter(run=run)

    total_records = records.count()
    paid_records = records.filter(status="PAID").count()
    pending_records = records.filter(status__in=["PENDING", "PARTIAL"]).count()

    # ------------------------------------------------------------
    # 🔥 Gross Calculation (Derived from real fields)
    # ------------------------------------------------------------

    aggregates = records.aggregate(
        total_base=Sum("base_salary"),
        total_allowance=Sum("allowance"),
        total_bonus=Sum("bonus"),
        total_overtime=Sum("overtime"),
        total_deductions=Sum("deductions"),
        total_net=Sum("net_salary"),
        total_paid=Sum("paid_amount"),
    )

    total_base = aggregates["total_base"] or Decimal("0.00")
    total_allowance = aggregates["total_allowance"] or Decimal("0.00")
    total_bonus = aggregates["total_bonus"] or Decimal("0.00")
    total_overtime = aggregates["total_overtime"] or Decimal("0.00")

    total_gross = total_base + total_allowance + total_bonus + total_overtime
    total_deductions = aggregates["total_deductions"] or Decimal("0.00")
    total_net = aggregates["total_net"] or Decimal("0.00")
    total_paid = aggregates["total_paid"] or Decimal("0.00")

    pending_net = total_net - total_paid


    # ------------------------------------------------------------
    # 📊 Percentages (Decimal Safe)
    # ------------------------------------------------------------

    paid_percent = Decimal("0.00")
    if total_net > 0:
        paid_percent = (total_paid / total_net) * Decimal("100")

    progress_percent = Decimal("0.00")
    if total_records > 0:
        progress_percent = (
            Decimal(paid_records) / Decimal(total_records)
        ) * Decimal("100")
    # ------------------------------------------------------------
    # 📒 Journal Checks
    # ------------------------------------------------------------

    payroll_journal = JournalEntry.objects.filter(
        company=company,
        source="PAYROLL",
        source_id=run.id,
    ).first()

    payroll_journal_exists = payroll_journal is not None

    settlement_entries = JournalEntry.objects.filter(
        company=company,
        source="PAYROLL_PAYMENT",
        source_id__in=records.values_list("id", flat=True),
    )

    settlement_total_amount = (
        settlement_entries.aggregate(total=Sum("total_debit"))["total"]
        or Decimal("0.00")
    )

    accounting_consistency = True

    if settlement_total_amount > total_net:
        accounting_consistency = False

    if payroll_journal and payroll_journal.total_debit != total_net:
        accounting_consistency = False

    # ------------------------------------------------------------
    # 📦 Final Payload
    # ------------------------------------------------------------

    return {
        "run_id": run.id,
        "month": run.month.strftime("%B %Y"),
        "status": run.status,

        "records": {
            "total": total_records,
            "paid": paid_records,
            "pending": pending_records,
        },

        "amounts": {
            "total_gross": total_gross,
            "total_deductions": total_deductions,
            "total_net": total_net,
            "paid_net": total_paid,
            "pending_net": pending_net,
        },

        "paid_percent": round(paid_percent, 2),
        "progress_percent": round(progress_percent, 2),

        "journals": {
            "payroll_entry_exists": payroll_journal_exists,
        },

        "accounting_consistency": accounting_consistency,
    }
# ================================================================
# 🔥 Integrity Validator (Partial-Aware — C3.8 Compatible)
# 🔐 Company Scoped + Multi-Payment Safe
# ================================================================

def validate_payroll_run_integrity(run: PayrollRun) -> dict:

    from django.db.models import Sum

    company = run.company
    errors = []

    records = PayrollRecord.objects.filter(run=run)

    total_net = (
        records.aggregate(total=Sum("net_salary"))["total"]
        or Decimal("0.00")
    )

    # ------------------------------------------------------------
    # Payroll Journal Validation
    # ------------------------------------------------------------

    payroll_entry = JournalEntry.objects.filter(
        company=company,
        source="PAYROLL",
        source_id=run.id,
    ).first()

    if run.status in ["APPROVED", "PAID"] and not payroll_entry:
        errors.append("Missing payroll journal entry")

    if payroll_entry:
        if payroll_entry.total_debit != total_net:
            errors.append("Payroll journal total mismatch")

    # ------------------------------------------------------------
    # Settlement Journals Validation (Partial Aware)
    # ------------------------------------------------------------

    settlement_entries = JournalEntry.objects.filter(
        company=company,
        source="PAYROLL_PAYMENT",
        source_id__in=records.values_list("id", flat=True),
    )

    settlement_total = (
        settlement_entries.aggregate(total=Sum("total_debit"))["total"]
        or Decimal("0.00")
    )

    if settlement_total > total_net:
        errors.append("Settlement total exceeds payroll total")

    if settlement_total > 0 and not payroll_entry:
        errors.append("Settlement exists without payroll journal")

    # ------------------------------------------------------------
    # Per-Record Validation
    # ------------------------------------------------------------

    for record in records:

        record_settlement_total = (
            JournalEntry.objects.filter(
                company=company,
                source="PAYROLL_PAYMENT",
                source_id=record.id,
            ).aggregate(total=Sum("total_debit"))["total"]
            or Decimal("0.00")
        )

        # 🔒 Check Paid Amount Sync
        if record_settlement_total != record.paid_amount:
            errors.append(
                f"Settlement mismatch for record {record.id}"
            )

        # 🔒 Overpayment Check
        if record_settlement_total > record.net_salary:
            errors.append(
                f"Overpayment detected for record {record.id}"
            )

        # 🔒 Status Consistency
        if record.status == "PAID" and record.paid_amount < record.net_salary:
            errors.append(
                f"Record {record.id} marked PAID but not fully settled"
            )

        if record.status == "PARTIAL" and record.paid_amount >= record.net_salary:
            errors.append(
                f"Record {record.id} marked PARTIAL but fully settled"
            )

    return {
        "run_id": run.id,
        "is_valid": len(errors) == 0,
        "errors": errors,
    }
# ================================================================
# 🧾 Employee Payroll Ledger (Enterprise Safe — Ultra Pro Patch)
# 🔒 Read-Only | Company Scoped | Accounting Accurate | C3.8 Native
# ================================================================

from payroll_center.models import JournalEntry, JournalLine
from django.db.models import Sum


def get_employee_payroll_ledger(record) -> dict:
    """
    Enterprise Ledger for a PayrollRecord.
    - Company Scoped
    - Journal Driven (Not UI Driven)
    - Partial Payment Aware (C3.8)
    - Accounting Trace Enabled
    """

    company = record.run.company

    # ------------------------------------------------------------
    # 🏦 Fetch Settlement Journal Entries (Accounting Source of Truth)
    # ------------------------------------------------------------
    entries = (
        JournalEntry.objects
        .filter(
            company=company,
            source="PAYROLL_PAYMENT",
            source_id=record.id,
        )
        .prefetch_related("lines")
        .order_by("date", "created_at", "id")
    )

    # ------------------------------------------------------------
    # 💰 Calculate Settlement Total (Journal-Based)
    # ------------------------------------------------------------
    settlement_total = (
        entries.aggregate(total=Sum("total_debit"))["total"]
        or Decimal("0.00")
    )

    # Fallback Safety (should always match C3.8 engine)
    if settlement_total == Decimal("0.00"):
        settlement_total = record.paid_amount or Decimal("0.00")

    # ------------------------------------------------------------
    # 🧮 Build Detailed Ledger Entries (Accounting Trace)
    # ------------------------------------------------------------
    ledger_entries = []

    for e in entries:
        payment_method = "UNKNOWN"
        credit_account = None

        # 🔍 Detect Payment Method from Journal Lines (1000 / 1010)
        for line in e.lines.all():
            if line.credit and line.credit > 0:
                credit_account = line.account_code

                if line.account_code == "1000":
                    payment_method = "CASH"
                elif line.account_code == "1010":
                    payment_method = "BANK"

        ledger_entries.append({
            "entry_id": e.id,
            "date": e.date,
            "created_at": e.created_at,
            "description": e.description,
            "amount": e.total_debit,
            "payment_method": payment_method,
            "credit_account": credit_account,
        })

    # ------------------------------------------------------------
    # 🔒 Accounting Consistency Check (Enterprise Audit Layer)
    # ------------------------------------------------------------
    accounting_consistent = True

    if settlement_total != (record.paid_amount or Decimal("0.00")):
        accounting_consistent = False

    if settlement_total > (record.net_salary or Decimal("0.00")):
        accounting_consistent = False

    # ------------------------------------------------------------
    # 📊 Final Ledger Payload (Backward Compatible)
    # ------------------------------------------------------------
    return {
        "employee": record.employee.full_name,
        "employee_id": record.employee.id,

        "run": {
            "run_id": record.run.id,
            "month": record.run.month.strftime("%B %Y"),
            "status": record.run.status,
        },

        "salary": {
            "net_salary": record.net_salary,
            "paid_amount": settlement_total,
            "remaining_amount": (record.net_salary - settlement_total),
            "record_status": record.status,
        },

        "entries": ledger_entries,

        "meta": {
            "entries_count": len(ledger_entries),
            "accounting_consistent": accounting_consistent,
            "source": "JournalEntry.PAYROLL_PAYMENT",
            "engine_version": "C3.8 Partial Settlement Engine",
        },
    }
