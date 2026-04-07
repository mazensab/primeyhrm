# ================================================================
# 📊 Payroll Reporting — Advanced Layer (C3.9 Hardened)
# 🔒 Company Scoped + Accounting Safe
# ✅ Pro-Rata Compatible + Partial Payment Aware
# ================================================================

from decimal import Decimal
from django.db.models import Sum

from payroll_center.models import PayrollRun, PayrollRecord, JournalEntry, JournalLine


# ================================================================
# 🔧 Helpers
# ================================================================

def _to_decimal(value, default: str = "0.00") -> Decimal:
    try:
        if value is None or value == "":
            return Decimal(default)
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _quantize_money(value: Decimal) -> Decimal:
    return _to_decimal(value, "0.00").quantize(Decimal("0.01"))


def _safe_remaining_amount(net_salary, paid_amount) -> Decimal:
    net_salary = _quantize_money(_to_decimal(net_salary, "0.00"))
    paid_amount = _quantize_money(_to_decimal(paid_amount, "0.00"))

    remaining = net_salary - paid_amount
    if remaining < Decimal("0.00"):
        return Decimal("0.00")
    return remaining.quantize(Decimal("0.01"))


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
    partial_records = records.filter(status="PARTIAL").count()
    unpaid_records = records.filter(status__in=["PENDING", "UNPAID"]).count()

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

    total_base = _quantize_money(aggregates["total_base"] or Decimal("0.00"))
    total_allowance = _quantize_money(aggregates["total_allowance"] or Decimal("0.00"))
    total_bonus = _quantize_money(aggregates["total_bonus"] or Decimal("0.00"))
    total_overtime = _quantize_money(aggregates["total_overtime"] or Decimal("0.00"))

    total_gross = _quantize_money(
        total_base + total_allowance + total_bonus + total_overtime
    )
    total_deductions = _quantize_money(
        aggregates["total_deductions"] or Decimal("0.00")
    )
    total_net = _quantize_money(aggregates["total_net"] or Decimal("0.00"))
    total_paid = _quantize_money(aggregates["total_paid"] or Decimal("0.00"))
    total_remaining = _safe_remaining_amount(total_net, total_paid)

    pending_records = partial_records + unpaid_records

    # ------------------------------------------------------------
    # 📊 Percentages (Decimal Safe)
    # ------------------------------------------------------------

    paid_percent = Decimal("0.00")
    if total_net > 0:
        paid_percent = ((total_paid / total_net) * Decimal("100")).quantize(
            Decimal("0.01")
        )

    progress_percent = Decimal("0.00")
    if total_records > 0:
        progress_percent = (
            (Decimal(paid_records) / Decimal(total_records)) * Decimal("100")
        ).quantize(Decimal("0.01"))

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

    settlement_total_amount = _quantize_money(
        settlement_entries.aggregate(total=Sum("total_debit"))["total"]
        or Decimal("0.00")
    )

    accounting_consistency = True

    if settlement_total_amount > total_net:
        accounting_consistency = False

    if payroll_journal and _quantize_money(payroll_journal.total_debit) != total_net:
        accounting_consistency = False

    if settlement_total_amount != total_paid:
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
            "partial": partial_records,
            "unpaid": unpaid_records,
            "pending": pending_records,
        },

        "amounts": {
            "total_base": total_base,
            "total_allowance": total_allowance,
            "total_bonus": total_bonus,
            "total_overtime": total_overtime,
            "total_gross": total_gross,
            "total_deductions": total_deductions,
            "total_net": total_net,
            "total_paid": total_paid,
            "paid_net": total_paid,
            "total_remaining": total_remaining,
            "pending_net": total_remaining,
        },

        "paid_percent": paid_percent,
        "progress_percent": progress_percent,

        "journals": {
            "payroll_entry_exists": payroll_journal_exists,
            "settlement_total_amount": settlement_total_amount,
        },

        "accounting_consistency": accounting_consistency,
    }


# ================================================================
# 🔥 Integrity Validator (Partial-Aware — C3.9 Compatible)
# 🔐 Company Scoped + Multi-Payment Safe
# ================================================================

def validate_payroll_run_integrity(run: PayrollRun) -> dict:
    company = run.company
    errors = []

    records = PayrollRecord.objects.filter(run=run)

    total_net = _quantize_money(
        records.aggregate(total=Sum("net_salary"))["total"]
        or Decimal("0.00")
    )

    total_paid = _quantize_money(
        records.aggregate(total=Sum("paid_amount"))["total"]
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
        if _quantize_money(payroll_entry.total_debit) != total_net:
            errors.append("Payroll journal total mismatch")

    # ------------------------------------------------------------
    # Settlement Journals Validation (Partial Aware)
    # ------------------------------------------------------------

    settlement_entries = JournalEntry.objects.filter(
        company=company,
        source="PAYROLL_PAYMENT",
        source_id__in=records.values_list("id", flat=True),
    )

    settlement_total = _quantize_money(
        settlement_entries.aggregate(total=Sum("total_debit"))["total"]
        or Decimal("0.00")
    )

    if settlement_total > total_net:
        errors.append("Settlement total exceeds payroll total")

    if settlement_total > Decimal("0.00") and not payroll_entry:
        errors.append("Settlement exists without payroll journal")

    if settlement_total != total_paid:
        errors.append("Run-level paid amount mismatch with settlement journals")

    # ------------------------------------------------------------
    # Per-Record Validation
    # ------------------------------------------------------------

    for record in records:
        record_net_salary = _quantize_money(record.net_salary or Decimal("0.00"))
        record_paid_amount = _quantize_money(record.paid_amount or Decimal("0.00"))
        record_remaining_amount = _safe_remaining_amount(
            record_net_salary,
            record_paid_amount,
        )

        record_settlement_total = _quantize_money(
            JournalEntry.objects.filter(
                company=company,
                source="PAYROLL_PAYMENT",
                source_id=record.id,
            ).aggregate(total=Sum("total_debit"))["total"]
            or Decimal("0.00")
        )

        if record_settlement_total != record_paid_amount:
            errors.append(
                f"Settlement mismatch for record {record.id}"
            )

        if record_settlement_total > record_net_salary:
            errors.append(
                f"Overpayment detected for record {record.id}"
            )

        if record.status == "PAID" and record_remaining_amount > Decimal("0.00"):
            errors.append(
                f"Record {record.id} marked PAID but still has remaining balance"
            )

        if record.status == "PARTIAL" and record_remaining_amount <= Decimal("0.00"):
            errors.append(
                f"Record {record.id} marked PARTIAL but fully settled"
            )

        if record.status in ["PENDING", "UNPAID"] and record_paid_amount > Decimal("0.00"):
            errors.append(
                f"Record {record.id} marked unpaid but has paid amount"
            )

    return {
        "run_id": run.id,
        "is_valid": len(errors) == 0,
        "errors": errors,
    }


# ================================================================
# 🧾 Employee Payroll Ledger (Enterprise Safe — Ultra Pro Patch)
# 🔒 Read-Only | Company Scoped | Accounting Accurate | C3.9 Native
# ================================================================

def get_employee_payroll_ledger(record) -> dict:
    """
    Enterprise Ledger for a PayrollRecord.
    - Company Scoped
    - Journal Driven (Not UI Driven)
    - Partial Payment Aware
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
    settlement_total = _quantize_money(
        entries.aggregate(total=Sum("total_debit"))["total"]
        or Decimal("0.00")
    )

    if settlement_total == Decimal("0.00"):
        settlement_total = _quantize_money(record.paid_amount or Decimal("0.00"))

    net_salary = _quantize_money(record.net_salary or Decimal("0.00"))
    remaining_amount = _safe_remaining_amount(net_salary, settlement_total)

    # ------------------------------------------------------------
    # 🧮 Build Detailed Ledger Entries (Accounting Trace)
    # ------------------------------------------------------------
    ledger_entries = []

    for e in entries:
        payment_method = "UNKNOWN"
        credit_account = None
        debit_lines = []
        credit_lines = []

        for line in e.lines.all():
            line_payload = {
                "account_code": line.account_code,
                "account_name": line.account_name,
                "debit": _quantize_money(line.debit or Decimal("0.00")),
                "credit": _quantize_money(line.credit or Decimal("0.00")),
            }

            if line.debit and line.debit > 0:
                debit_lines.append(line_payload)

            if line.credit and line.credit > 0:
                credit_lines.append(line_payload)
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
            "amount": _quantize_money(e.total_debit),
            "payment_method": payment_method,
            "credit_account": credit_account,
            "debit_lines": debit_lines,
            "credit_lines": credit_lines,
        })

    # ------------------------------------------------------------
    # 🔒 Accounting Consistency Check (Enterprise Audit Layer)
    # ------------------------------------------------------------
    accounting_consistent = True

    if settlement_total != _quantize_money(record.paid_amount or Decimal("0.00")):
        accounting_consistent = False

    if settlement_total > net_salary:
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
            "net_salary": net_salary,
            "paid_amount": settlement_total,
            "remaining_amount": remaining_amount,
            "record_status": record.status,
        },

        "entries": ledger_entries,

        "meta": {
            "entries_count": len(ledger_entries),
            "accounting_consistent": accounting_consistent,
            "source": "JournalEntry.PAYROLL_PAYMENT",
            "engine_version": "C3.9 Pro-Rata + Partial Settlement Engine",
        },
    }