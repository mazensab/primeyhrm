from __future__ import annotations

from typing import Any

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from payroll_center.models import PayrollRecord
from company_manager.models import CompanyUser
from employee_center.models import Employee
from api.company.employee import _resolve_company


# ============================================================
# 🔧 Helpers
# ============================================================

def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int_or_float(value: Any) -> Any:
    number = _to_float(value, 0.0)
    if abs(number - int(number)) < 0.000001:
        return int(number)
    return round(number, 2)


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _clean_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _build_line_item(
    *,
    code: str,
    label: str,
    amount: Any,
    days: Any = None,
    quantity: Any = None,
    unit: str | None = None,
    notes: str | None = None,
    category: str | None = None,
) -> dict:
    return {
        "code": code,
        "label": label,
        "amount": round(_to_float(amount), 2),
        "days": None if days in [None, ""] else _to_int_or_float(days),
        "quantity": None if quantity in [None, ""] else _to_int_or_float(quantity),
        "unit": unit or None,
        "notes": _clean_text(notes) or None,
        "category": category or None,
    }


def _append_if_positive(target: list, item: dict):
    if _to_float(item.get("amount"), 0.0) > 0:
        target.append(item)


def _normalize_list_items(items: list, fallback_category: str) -> list:
    normalized = []

    for item in items:
        if not isinstance(item, dict):
            continue

        normalized_item = _build_line_item(
            code=_clean_text(item.get("code"), "item"),
            label=_clean_text(item.get("label") or item.get("name"), "Item"),
            amount=item.get("amount") or item.get("value") or 0,
            days=item.get("days"),
            quantity=item.get("quantity"),
            unit=_clean_text(item.get("unit")) or None,
            notes=_clean_text(item.get("notes")) or None,
            category=_clean_text(item.get("category"), fallback_category),
        )

        if _to_float(normalized_item["amount"], 0.0) > 0:
            normalized.append(normalized_item)

    return normalized


def _get_nested_value(container: dict, *keys, default=None):
    current = container
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _iso_date_or_none(value: Any) -> str | None:
    if not value:
        return None

    try:
        return value.isoformat()
    except Exception:
        pass

    text = _clean_text(value)
    return text or None


def _collect_breakdown_facts(breakdown: dict) -> list[dict]:
    facts: list[dict] = []

    mapping = [
        ("employment_start_date", "Employment Start Date"),
        ("payroll_period_start", "Payroll Period Start"),
        ("payroll_period_end", "Payroll Period End"),
        ("effective_start_date", "Effective Start Date"),
        ("effective_end_date", "Effective End Date"),
        ("eligible_days", "Eligible Days"),
        ("payable_days_before_deduction", "Payable Days Before Deduction"),
        ("payable_days_after_deduction", "Payable Days After Deduction"),
        ("leave_paid_days", "Paid Leave Days"),
        ("leave_partial_unpaid_days", "Unpaid Leave Days"),
        ("unpaid_absence_days", "Unpaid Absence Days"),
        ("inferred_absence_days", "Inferred Absence Days"),
        ("late_minutes", "Late Minutes"),
        ("overtime_minutes", "Overtime Minutes"),
        ("attendance_activity_found", "Attendance Activity Found"),
    ]

    for key, label in mapping:
        value = breakdown.get(key)
        if value in [None, ""]:
            continue

        if isinstance(value, bool):
            rendered_value = "Yes" if value else "No"
        else:
            rendered_value = _to_int_or_float(value) if isinstance(value, (int, float)) else value

        facts.append({
            "key": key,
            "label": label,
            "value": rendered_value,
        })

    return facts


# ============================================================
# 🧾 Structured Print Payload Builder
# ============================================================

def _build_structured_print_payload(record: PayrollRecord, source_obj: Any) -> dict:
    breakdown = _as_dict(getattr(source_obj, "breakdown", None))

    earnings_items: list[dict] = []
    deduction_items: list[dict] = []
    facts: list[dict] = []

    # ========================================================
    # ✅ Reference / prorated salary metadata
    # ========================================================
    monthly_reference_base_salary = (
        breakdown.get("monthly_reference_base_salary")
        or breakdown.get("base_salary_reference")
        or breakdown.get("base_salary_monthly_reference")
        or 0
    )
    monthly_reference_allowance = (
        breakdown.get("monthly_reference_allowance")
        or breakdown.get("allowance_reference")
        or breakdown.get("allowance_monthly_reference")
        or 0
    )

    base_salary_prorated = (
        breakdown.get("base_salary_prorated")
        or getattr(source_obj, "base_salary", 0)
        or 0
    )
    allowance_prorated = (
        breakdown.get("allowance_prorated")
        or getattr(source_obj, "allowance", 0)
        or 0
    )

    eligible_days = breakdown.get("eligible_days")
    payable_days_after_deduction = breakdown.get("payable_days_after_deduction")
    unpaid_absence_days = (
        breakdown.get("unpaid_absence_days")
        or breakdown.get("absent_days_legal")
        or breakdown.get("absence_days")
    )

    # ========================================================
    # ✅ Earnings
    # ========================================================
    _append_if_positive(
        earnings_items,
        _build_line_item(
            code="base_salary_prorated",
            label="Base Salary",
            amount=base_salary_prorated,
            days=eligible_days,
            notes=(
                f"Reference Monthly Salary: {round(_to_float(monthly_reference_base_salary), 2)}"
                if _to_float(monthly_reference_base_salary) > 0
                else "Prorated base salary"
            ),
            category="earning",
        ),
    )

    _append_if_positive(
        earnings_items,
        _build_line_item(
            code="allowance_prorated",
            label="Allowance",
            amount=allowance_prorated,
            days=eligible_days,
            notes=(
                f"Reference Monthly Allowance: {round(_to_float(monthly_reference_allowance), 2)}"
                if _to_float(monthly_reference_allowance) > 0
                else "Prorated allowance"
            ),
            category="earning",
        ),
    )

    _append_if_positive(
        earnings_items,
        _build_line_item(
            code="bonus",
            label="Bonus",
            amount=getattr(source_obj, "bonus", 0),
            category="earning",
        ),
    )

    _append_if_positive(
        earnings_items,
        _build_line_item(
            code="overtime",
            label="Overtime",
            amount=getattr(source_obj, "overtime", 0),
            quantity=(
                breakdown.get("overtime_hours")
                or _get_nested_value(breakdown, "overtime", "hours")
                or breakdown.get("overtime_minutes")
            ),
            unit=(
                "hours"
                if breakdown.get("overtime_hours") or _get_nested_value(breakdown, "overtime", "hours")
                else ("minutes" if breakdown.get("overtime_minutes") else None)
            ),
            notes=(
                f"Hourly Rate: {round(_to_float(breakdown.get('hourly_rate')), 2)}"
                if _to_float(breakdown.get("hourly_rate")) > 0
                else None
            ),
            category="earning",
        ),
    )

    # ========================================================
    # ✅ Optional explicit earning lists from breakdown
    # ========================================================
    explicit_earnings = []
    explicit_earnings.extend(_as_list(breakdown.get("earning_items")))
    explicit_earnings.extend(_as_list(breakdown.get("earnings")))
    explicit_earnings.extend(_as_list(breakdown.get("allowance_items")))
    explicit_earnings.extend(_as_list(breakdown.get("bonus_items")))
    explicit_earnings.extend(_as_list(breakdown.get("additions")))

    existing_earning_codes = {item["code"] for item in earnings_items}
    for item in _normalize_list_items(explicit_earnings, "earning"):
        if item["code"] in existing_earning_codes:
            continue
        earnings_items.append(item)
        existing_earning_codes.add(item["code"])

    # ========================================================
    # ✅ Optional explicit deduction lists from breakdown
    # ========================================================
    explicit_deductions = []
    explicit_deductions.extend(_as_list(breakdown.get("deduction_items")))
    explicit_deductions.extend(_as_list(breakdown.get("deductions")))
    explicit_deductions.extend(_as_list(breakdown.get("deduction_breakdown")))
    explicit_deductions.extend(_as_list(breakdown.get("salary_deductions")))
    explicit_deductions.extend(_as_list(breakdown.get("attendance_deductions")))

    for item in _normalize_list_items(explicit_deductions, "deduction"):
        deduction_items.append(item)

    # ========================================================
    # ✅ Smart inferred deductions from breakdown
    # ========================================================
    attendance = _as_dict(breakdown.get("attendance"))
    penalties = _as_dict(breakdown.get("penalties"))
    loans = _as_dict(breakdown.get("loans"))
    admin = _as_dict(breakdown.get("administrative"))
    absence = _as_dict(breakdown.get("absence"))
    lateness = _as_dict(breakdown.get("lateness"))

    absent_days = (
        absence.get("days")
        or attendance.get("absent_days")
        or breakdown.get("unpaid_absence_days")
        or breakdown.get("absent_days_legal")
        or breakdown.get("absent_days")
        or breakdown.get("absence_days")
    )
    absent_amount = (
        absence.get("amount")
        or attendance.get("absence_deduction")
        or breakdown.get("absence_deduction")
        or breakdown.get("absent_deduction")
    )
    _append_if_positive(
        deduction_items,
        _build_line_item(
            code="absence_deduction",
            label="Absence Deduction",
            amount=absent_amount,
            days=absent_days,
            notes=(
                f"Payable Days After Deduction: {_to_int_or_float(payable_days_after_deduction)}"
                if payable_days_after_deduction not in [None, ""]
                else "Unpaid absence inside eligible payroll period"
            ),
            category="deduction",
        ),
    )

    late_count = (
        lateness.get("count")
        or attendance.get("late_count")
        or breakdown.get("late_count")
    )
    late_minutes = (
        lateness.get("minutes")
        or attendance.get("late_minutes")
        or breakdown.get("late_minutes")
    )
    late_amount = (
        lateness.get("amount")
        or attendance.get("late_deduction")
        or breakdown.get("late_deduction")
    )
    _append_if_positive(
        deduction_items,
        _build_line_item(
            code="late_deduction",
            label="Late Deduction",
            amount=late_amount,
            quantity=late_minutes or late_count,
            unit="minutes" if late_minutes else ("times" if late_count else None),
            notes="Late attendance",
            category="deduction",
        ),
    )

    admin_amount = (
        admin.get("amount")
        or breakdown.get("administrative_deduction")
        or breakdown.get("admin_deduction")
    )
    admin_reason = (
        admin.get("reason")
        or breakdown.get("administrative_reason")
        or "Administrative deduction"
    )
    _append_if_positive(
        deduction_items,
        _build_line_item(
            code="administrative_deduction",
            label="Administrative Deduction",
            amount=admin_amount,
            notes=admin_reason,
            category="deduction",
        ),
    )

    loan_amount = (
        loans.get("amount")
        or breakdown.get("loan_deduction")
        or breakdown.get("advance_deduction")
    )
    loan_notes = (
        loans.get("notes")
        or breakdown.get("loan_notes")
        or "Loan / advance deduction"
    )
    _append_if_positive(
        deduction_items,
        _build_line_item(
            code="loan_deduction",
            label="Loan / Advance",
            amount=loan_amount,
            notes=loan_notes,
            category="deduction",
        ),
    )

    penalty_amount = (
        penalties.get("amount")
        or breakdown.get("penalty_deduction")
        or breakdown.get("disciplinary_deduction")
    )
    penalty_reason = (
        penalties.get("reason")
        or breakdown.get("penalty_reason")
        or "Penalty deduction"
    )
    _append_if_positive(
        deduction_items,
        _build_line_item(
            code="penalty_deduction",
            label="Penalty / Disciplinary Deduction",
            amount=penalty_amount,
            notes=penalty_reason,
            category="deduction",
        ),
    )

    # ========================================================
    # ✅ Rich facts / chips for receipt
    # ========================================================
    facts.extend(_collect_breakdown_facts(breakdown))

    reference_facts = [
        ("monthly_reference_base_salary", "Reference Monthly Base Salary"),
        ("monthly_reference_allowance", "Reference Monthly Allowance"),
        ("base_salary_prorated", "Prorated Base Salary"),
        ("allowance_prorated", "Prorated Allowance"),
        ("hourly_rate", "Hourly Rate"),
        ("daily_rate_base_salary", "Daily Rate"),
    ]

    for key, label in reference_facts:
        value = breakdown.get(key)
        if value in [None, ""]:
            continue
        facts.append({
            "key": key,
            "label": label,
            "value": _to_int_or_float(value),
        })

    # ========================================================
    # ✅ Fallback generic deduction if no details matched
    # ========================================================
    total_deductions = _to_float(getattr(source_obj, "deductions", 0), 0.0)
    detailed_deductions_sum = sum(
        _to_float(item.get("amount"), 0.0) for item in deduction_items
    )

    if total_deductions > 0 and detailed_deductions_sum == 0:
        deduction_items.append(
            _build_line_item(
                code="deductions_total",
                label="Other Deductions",
                amount=total_deductions,
                category="deduction",
            )
        )
    elif total_deductions > detailed_deductions_sum + 0.01:
        deduction_items.append(
            _build_line_item(
                code="deductions_balance",
                label="Other Deductions",
                amount=round(total_deductions - detailed_deductions_sum, 2),
                category="deduction",
            )
        )

    gross_salary = sum(_to_float(item.get("amount"), 0.0) for item in earnings_items)

    return {
        "earnings_items": earnings_items,
        "deduction_items": deduction_items,
        "facts": facts,
        "summary": {
            "gross_salary": round(gross_salary, 2),
            "total_earnings": round(gross_salary, 2),
            "total_deductions": round(total_deductions, 2),
            "net_salary": round(_to_float(getattr(source_obj, "net_salary", 0), 0.0), 2),
            "paid_amount": round(_to_float(getattr(record, "paid_amount", 0), 0.0), 2),
            "remaining_amount": round(_to_float(getattr(record, "remaining_amount", 0), 0.0), 2),
        },
        "meta": {
            "employment_start_date": breakdown.get("employment_start_date"),
            "payroll_period_start": breakdown.get("payroll_period_start"),
            "payroll_period_end": breakdown.get("payroll_period_end"),
            "effective_start_date": breakdown.get("effective_start_date"),
            "effective_end_date": breakdown.get("effective_end_date"),
            "eligible_days": _to_float(breakdown.get("eligible_days"), 0.0),
            "payable_days_after_deduction": _to_float(
                breakdown.get("payable_days_after_deduction"),
                0.0,
            ),
            "unpaid_absence_days": _to_float(
                breakdown.get("unpaid_absence_days"),
                0.0,
            ),
        },
    }


# ============================================================
# 🧾 Company Admin Salary Slip
# ============================================================

class CompanyPayrollSalarySlipAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        try:
            company_user = CompanyUser.objects.select_related("company").get(
                user=request.user
            )
        except CompanyUser.DoesNotExist:
            return Response(
                {"detail": "Company context not found."},
                status=status.HTTP_403_FORBIDDEN
            )

        company = company_user.company

        try:
            record = (
                PayrollRecord.objects
                .select_related(
                    "employee",
                    "employee__department",
                    "employee__job_title",
                    "employee__financial_info",
                    "run",
                    "run__company",
                    "contract",
                    "snapshot",
                )
                .prefetch_related("employee__branches")
                .get(
                    id=record_id,
                    run__company=company
                )
            )
        except PayrollRecord.DoesNotExist:
            return Response(
                {"detail": "Payroll record not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        employee = record.employee
        contract = record.contract
        financial_info = getattr(employee, "financial_info", None)

        use_snapshot = (
            record.run.status in ["APPROVED", "PAID"]
            and getattr(record, "snapshot", None) is not None
        )
        source = record.snapshot if use_snapshot else record

        print_payload = _build_structured_print_payload(record, source)
        breakdown = getattr(source, "breakdown", None) or {}

        response_data = {
            "id": record.id,
            "record_id": record.id,
            "company": {
                "id": company.id,
                "name": getattr(company, "name", None),
                "email": getattr(company, "email", None),
                "phone": getattr(company, "phone", None),
                "commercial_number": getattr(company, "commercial_number", None),
                "vat_number": getattr(company, "vat_number", None),
                "building_number": getattr(company, "building_number", None),
                "street": getattr(company, "street", None),
                "district": getattr(company, "district", None),
                "city": getattr(company, "city", None),
                "postal_code": getattr(company, "postal_code", None),
                "short_address": getattr(company, "short_address", None),
                "logo_url": (
                    getattr(company, "logo_url", None)
                    or getattr(company, "logo", None)
                    or getattr(company, "image", None)
                    or getattr(company, "photo_url", None)
                ),
            },
            "employee": {
                "id": employee.id,
                "full_name": employee.full_name,
                "employee_number": getattr(employee, "employee_number", None),
                "department": (
                    employee.department.name
                    if employee.department else None
                ),
                "job_title": (
                    employee.job_title.name
                    if employee.job_title else None
                ),
                "branches": [
                    branch.name for branch in employee.branches.all()
                ],
            },
            "contract": {
                "id": contract.id if contract else None,
                "contract_type": getattr(contract, "contract_type", None),
                "start_date": _iso_date_or_none(
                    getattr(contract, "start_date", None)
                    or getattr(contract, "joining_date", None)
                    or getattr(contract, "join_date", None)
                ),
            },
            "financial_info": {
                "basic_salary": float(getattr(financial_info, "basic_salary", 0) or 0),
                "housing_allowance": float(getattr(financial_info, "housing_allowance", 0) or 0),
                "transport_allowance": float(getattr(financial_info, "transport_allowance", 0) or 0),
                "food_allowance": float(getattr(financial_info, "food_allowance", 0) or 0),
                "other_allowances": float(getattr(financial_info, "other_allowances", 0) or 0),
                "bank_name": getattr(financial_info, "bank_name", None),
                "iban": getattr(financial_info, "iban", None),
            },
            "month": record.month.strftime("%Y-%m"),
            "run": {
                "id": record.run.id,
                "status": record.run.status,
            },
            "payment_status": record.status,
            "payment": {
                "status": record.status,
                "paid_amount": float(record.paid_amount or 0),
                "remaining_amount": float(record.remaining_amount or 0),
                "payment_method": record.payment_method,
                "paid_at": record.paid_at,
            },
            "salary": {
                "base_salary": float(getattr(source, "base_salary", 0) or 0),
                "allowance": float(getattr(source, "allowance", 0) or 0),
                "bonus": float(getattr(source, "bonus", 0) or 0),
                "overtime": float(getattr(source, "overtime", 0) or 0),
                "deductions": float(getattr(source, "deductions", 0) or 0),
                "net_salary": float(getattr(source, "net_salary", 0) or 0),
                "reference_base_salary": float(
                    breakdown.get("monthly_reference_base_salary")
                    or getattr(financial_info, "basic_salary", 0)
                    or 0
                ),
                "reference_allowance": float(
                    breakdown.get("monthly_reference_allowance")
                    or 0
                ),
                "prorated_base_salary": float(
                    breakdown.get("base_salary_prorated")
                    or getattr(source, "base_salary", 0)
                    or 0
                ),
                "prorated_allowance": float(
                    breakdown.get("allowance_prorated")
                    or getattr(source, "allowance", 0)
                    or 0
                ),
            },
            "period": {
                "employment_start_date": breakdown.get("employment_start_date"),
                "payroll_period_start": breakdown.get("payroll_period_start"),
                "payroll_period_end": breakdown.get("payroll_period_end"),
                "effective_start_date": breakdown.get("effective_start_date"),
                "effective_end_date": breakdown.get("effective_end_date"),
                "eligible_days": _to_float(breakdown.get("eligible_days"), 0.0),
                "payable_days_before_deduction": _to_float(
                    breakdown.get("payable_days_before_deduction"),
                    0.0,
                ),
                "payable_days_after_deduction": _to_float(
                    breakdown.get("payable_days_after_deduction"),
                    0.0,
                ),
                "unpaid_absence_days": _to_float(
                    breakdown.get("unpaid_absence_days"),
                    0.0,
                ),
                "inferred_absence_days": _to_float(
                    breakdown.get("inferred_absence_days"),
                    0.0,
                ),
                "leave_paid_days": _to_float(
                    breakdown.get("leave_paid_days"),
                    0.0,
                ),
                "leave_partial_unpaid_days": _to_float(
                    breakdown.get("leave_partial_unpaid_days"),
                    0.0,
                ),
            },
            "breakdown": breakdown,
            "print_payload": print_payload,
            "generated_at": record.updated_at,
        }

        return Response(response_data, status=status.HTTP_200_OK)


# ======================================================
# 🧾 Employee Self-Service Salary Slip
# ======================================================

@require_GET
@login_required
def employee_self_salary_slip(request, record_id):
    company = _resolve_company(request)
    if not company:
        return JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )

    try:
        employee = Employee.objects.get(
            user=request.user,
            company=company,
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employee profile not found"},
            status=403,
        )

    try:
        record = (
            PayrollRecord.objects
            .select_related(
                "run",
                "run__company",
                "employee__department",
                "employee__job_title",
                "employee__financial_info",
                "contract",
                "snapshot",
            )
            .prefetch_related("employee__branches")
            .get(
                id=record_id,
                employee=employee,
                run__company=company,
            )
        )
    except PayrollRecord.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Salary slip not found"},
            status=404,
        )

    emp = record.employee
    financial_info = getattr(emp, "financial_info", None)

    use_snapshot = (
        record.run.status in ["APPROVED", "PAID"]
        and getattr(record, "snapshot", None) is not None
    )
    source = record.snapshot if use_snapshot else record
    print_payload = _build_structured_print_payload(record, source)
    breakdown = getattr(source, "breakdown", None) or {}

    return JsonResponse({
        "status": "ok",
        "record_id": record.id,
        "company": {
            "name": record.run.company.name,
        },
        "month": record.month.strftime("%Y-%m"),
        "run_status": record.run.status,
        "payment_status": record.status,
        "payment": {
            "status": record.status,
            "paid_amount": float(record.paid_amount or 0),
            "remaining_amount": float(record.remaining_amount or 0),
            "payment_method": record.payment_method,
            "paid_at": record.paid_at.isoformat() if record.paid_at else None,
        },
        "employee": {
            "full_name": emp.full_name,
            "employee_number": getattr(emp, "employee_number", None),
            "department": (
                emp.department.name if emp.department else None
            ),
            "job_title": (
                emp.job_title.name if emp.job_title else None
            ),
            "branches": [
                b.name for b in emp.branches.all()
            ],
        },
        "contract": {
            "id": record.contract.id if record.contract else None,
            "contract_type": getattr(record.contract, "contract_type", None) if record.contract else None,
            "start_date": _iso_date_or_none(
                getattr(record.contract, "start_date", None)
                or getattr(record.contract, "joining_date", None)
                or getattr(record.contract, "join_date", None)
            ) if record.contract else None,
        },
        "financial_info": {
            "basic_salary": float(getattr(financial_info, "basic_salary", 0) or 0),
            "housing_allowance": float(getattr(financial_info, "housing_allowance", 0) or 0),
            "transport_allowance": float(getattr(financial_info, "transport_allowance", 0) or 0),
            "food_allowance": float(getattr(financial_info, "food_allowance", 0) or 0),
            "other_allowances": float(getattr(financial_info, "other_allowances", 0) or 0),
            "bank_name": getattr(financial_info, "bank_name", None),
            "iban": getattr(financial_info, "iban", None),
        },
        "salary": {
            "base_salary": float(getattr(source, "base_salary", 0) or 0),
            "allowance": float(getattr(source, "allowance", 0) or 0),
            "bonus": float(getattr(source, "bonus", 0) or 0),
            "overtime": float(getattr(source, "overtime", 0) or 0),
            "deductions": float(getattr(source, "deductions", 0) or 0),
            "net_salary": float(getattr(source, "net_salary", 0) or 0),
            "reference_base_salary": float(
                breakdown.get("monthly_reference_base_salary")
                or getattr(financial_info, "basic_salary", 0)
                or 0
            ),
            "reference_allowance": float(
                breakdown.get("monthly_reference_allowance")
                or 0
            ),
            "prorated_base_salary": float(
                breakdown.get("base_salary_prorated")
                or getattr(source, "base_salary", 0)
                or 0
            ),
            "prorated_allowance": float(
                breakdown.get("allowance_prorated")
                or getattr(source, "allowance", 0)
                or 0
            ),
        },
        "period": {
            "employment_start_date": breakdown.get("employment_start_date"),
            "payroll_period_start": breakdown.get("payroll_period_start"),
            "payroll_period_end": breakdown.get("payroll_period_end"),
            "effective_start_date": breakdown.get("effective_start_date"),
            "effective_end_date": breakdown.get("effective_end_date"),
            "eligible_days": _to_float(breakdown.get("eligible_days"), 0.0),
            "payable_days_before_deduction": _to_float(
                breakdown.get("payable_days_before_deduction"),
                0.0,
            ),
            "payable_days_after_deduction": _to_float(
                breakdown.get("payable_days_after_deduction"),
                0.0,
            ),
            "unpaid_absence_days": _to_float(
                breakdown.get("unpaid_absence_days"),
                0.0,
            ),
            "inferred_absence_days": _to_float(
                breakdown.get("inferred_absence_days"),
                0.0,
            ),
            "leave_paid_days": _to_float(
                breakdown.get("leave_paid_days"),
                0.0,
            ),
            "leave_partial_unpaid_days": _to_float(
                breakdown.get("leave_partial_unpaid_days"),
                0.0,
            ),
        },
        "breakdown": breakdown,
        "print_payload": print_payload,
        "generated_at": record.updated_at.isoformat() if record.updated_at else None,
    })


# ======================================================
# 📋 Employee Self-Slips List
# ======================================================

@require_GET
@login_required
def employee_self_slips_list(request):
    company = _resolve_company(request)
    if not company:
        return JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )

    try:
        employee = Employee.objects.get(
            user=request.user,
            company=company,
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employee profile not found"},
            status=403,
        )

    records = (
        PayrollRecord.objects
        .filter(employee=employee)
        .select_related("run")
        .order_by("-month")
    )

    results = [
        {
            "record_id": r.id,
            "month": r.month.strftime("%Y-%m"),
            "net_salary": float(r.net_salary),
            "payment_status": r.status,
            "run_status": r.run.status,
        }
        for r in records
    ]

    return JsonResponse({
        "status": "ok",
        "count": len(results),
        "results": results,
    })