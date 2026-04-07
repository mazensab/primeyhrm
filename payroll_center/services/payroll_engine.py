# ================================================================
# 🏦 Payroll Engine — Enterprise Core (Model Compatible Version)
# 🟢 LEGAL PATCH: Leave ↔ Payroll Bridge (Saudi-Compliant)
# 🟢 PRO-RATA PATCH: Employment Start Date Aware Payroll Calculation
# 🟢 ATTENDANCE PATCH: Arabic/English Status Aware + Late/OT/Absence Aware
# 🟢 MATERIALIZATION PATCH: Persist Missing Attendance Rows Before Payroll
# 🟢 GROSS ABSENCE PATCH: Absence Deduction From Full Gross Salary
# 🟢 ENTITLEMENT START PATCH: Ignore days before actual employee activation/existence
# 🟢 FULL-PERIOD UNPAID PATCH: Zero out payroll when full eligible period is non-payable
# 🟢 RECALC SAFETY PATCH: Reset paid state before saving recalculated records
# 🟢 NON-NEGATIVE NET PATCH: Cap deductions to gross earnings before save()
# ================================================================

from decimal import Decimal, ROUND_HALF_UP
import logging
from calendar import monthrange
from datetime import timedelta

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
from attendance_center.models import (
    AttendanceRecord,
    CompanyHoliday,
)
from notification_center.services import create_notification
from attendance_center.services.services import WorkScheduleResolver
from attendance_center.services.workday_engine import WorkdayEngine

logger = logging.getLogger(__name__)


# ================================================================
# 🔢 Decimal Helpers
# ================================================================
MONEY_QUANT = Decimal("0.01")
DAYS_DIVISOR = Decimal("30")
HOURS_PER_DAY = Decimal("8")


def _to_decimal(value, default: str = "0.00") -> Decimal:
    try:
        if value is None or value == "":
            return Decimal(default)
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _money(value) -> Decimal:
    return _to_decimal(value).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def _decimal_day_count(value) -> Decimal:
    return _to_decimal(value, "0").quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _calculate_daily_rate(monthly_amount: Decimal) -> Decimal:
    monthly_amount = _money(monthly_amount)
    if monthly_amount <= 0:
        return Decimal("0.00")
    return (monthly_amount / DAYS_DIVISOR).quantize(
        MONEY_QUANT,
        rounding=ROUND_HALF_UP,
    )


def _calculate_prorated_amount(
    monthly_amount: Decimal,
    payable_days: Decimal,
) -> Decimal:
    monthly_amount = _money(monthly_amount)
    payable_days = _decimal_day_count(payable_days)

    if monthly_amount <= 0 or payable_days <= 0:
        return Decimal("0.00")

    daily_rate = _calculate_daily_rate(monthly_amount)
    return (daily_rate * payable_days).quantize(
        MONEY_QUANT,
        rounding=ROUND_HALF_UP,
    )


def _daterange(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def _to_date_only(value):
    """
    يحول datetime/date/string-like إلى date عند الإمكان.
    """
    if not value:
        return None

    try:
        return value.date()
    except Exception:
        pass

    return value


# ================================================================
# 🧭 Employment / Entitlement Date Resolvers
# ================================================================
def _resolve_employment_start_date(record):
    """
    نحاول قراءة تاريخ بداية العمل من أكثر من مصدر محتمل
    بدون كسر التوافق مع الموديلات الحالية.
    """

    candidate_sources = [
        getattr(record, "contract", None),
        getattr(record, "employee", None),
        getattr(getattr(record, "employee", None), "employment_info", None),
    ]

    candidate_fields = [
        "start_date",
        "joining_date",
        "join_date",
        "date_of_joining",
        "employment_start_date",
        "work_start_date",
        "hire_date",
    ]

    for source in candidate_sources:
        if not source:
            continue

        for field_name in candidate_fields:
            value = getattr(source, field_name, None)
            value = _to_date_only(value)
            if value:
                return value

    return None


def _resolve_employee_employment_start_date(employee):
    """
    نسخة مخصصة للموظف مباشرة لاستخدامها أثناء توليد سجلات الحضور
    قبل الدخول في حساب الرواتب.
    """

    candidate_sources = [
        getattr(employee, "active_contract", None),
        employee,
        getattr(employee, "employment_info", None),
    ]

    candidate_fields = [
        "start_date",
        "joining_date",
        "join_date",
        "date_of_joining",
        "employment_start_date",
        "work_start_date",
        "hire_date",
    ]

    for source in candidate_sources:
        if not source:
            continue

        for field_name in candidate_fields:
            value = getattr(source, field_name, None)
            value = _to_date_only(value)
            if value:
                return value

    return None


def _resolve_actual_entity_existence_date(record):
    """
    هذا الحارس يمنع احتساب أيام قبل الوجود/الالتحاق الفعلي للموظف داخل النظام.
    نأخذ أحدث تاريخ صالح من مصادر الإنشاء/الانضمام الفعلي.
    """

    employee = getattr(record, "employee", None)
    employment_info = getattr(employee, "employment_info", None) if employee else None
    contract = getattr(record, "contract", None)

    candidate_values = []

    sources_and_fields = [
        (employee, ["date_joined", "created_at"]),
        (employment_info, ["created_at"]),
        (contract, ["created_at"]),
    ]

    for source, fields in sources_and_fields:
        if not source:
            continue

        for field_name in fields:
            value = getattr(source, field_name, None)
            value = _to_date_only(value)
            if value:
                candidate_values.append(value)

    if not candidate_values:
        return None

    return max(candidate_values)


def _resolve_record_entitlement_start_date(record):
    """
    تاريخ بداية الاستحقاق النهائي:
    - إذا وجد تاريخ بداية عمل
    - وإذا وجد تاريخ وجود/التحاق فعلي أحدث
    نأخذ الأحدث بينهما.
    """

    employment_start_date = _resolve_employment_start_date(record)
    actual_existence_date = _resolve_actual_entity_existence_date(record)

    candidates = [d for d in [employment_start_date, actual_existence_date] if d]
    if not candidates:
        return None

    return max(candidates)


def _resolve_employee_entitlement_start_date(employee):
    """
    نسخة خاصة بالموظف أثناء توليد الحضور المفقود.
    """

    employment_start_date = _resolve_employee_employment_start_date(employee)

    candidate_values = []
    for field_name in ["date_joined", "created_at"]:
        value = getattr(employee, field_name, None)
        value = _to_date_only(value)
        if value:
            candidate_values.append(value)

    employment_info = getattr(employee, "employment_info", None)
    if employment_info:
        info_created_at = _to_date_only(getattr(employment_info, "created_at", None))
        if info_created_at:
            candidate_values.append(info_created_at)

    actual_existence_date = max(candidate_values) if candidate_values else None

    candidates = [d for d in [employment_start_date, actual_existence_date] if d]
    if not candidates:
        return None

    return max(candidates)


# ================================================================
# 🧱 Materialize Missing Attendance Records For Payroll Window
# ================================================================
def _materialize_missing_attendance_for_payroll_window(
    *,
    employee,
    company,
    start_date,
    end_date,
):
    """
    إنشاء سجلات حضور مفقودة داخل فترة الرواتب فقط حتى تصبح
    قاعدة البيانات متوافقة مع الواقع ومع محرك الرواتب.
    """

    entitlement_start_date = _resolve_employee_entitlement_start_date(employee)

    effective_start = (
        max(start_date, entitlement_start_date)
        if entitlement_start_date else start_date
    )

    employee_end_date = _to_date_only(getattr(employee, "end_date", None))
    effective_end = (
        min(end_date, employee_end_date)
        if employee_end_date else end_date
    )

    if effective_start > effective_end:
        return {
            "created": 0,
            "absent_created": 0,
            "weekend_created": 0,
            "holiday_created": 0,
            "leave_created": 0,
            "skipped_existing": 0,
        }

    existing_dates = set(
        AttendanceRecord.objects.filter(
            employee=employee,
            date__range=(effective_start, effective_end),
        ).values_list("date", flat=True)
    )

    leave_dates = set()
    try:
        from leave_center.models import LeaveRequest

        approved_leaves = LeaveRequest.objects.filter(
            employee=employee,
            status="approved",
            start_date__lte=effective_end,
            end_date__gte=effective_start,
        ).only("start_date", "end_date")

        for leave in approved_leaves:
            current = max(leave.start_date, effective_start)
            leave_end = min(leave.end_date, effective_end)

            while current <= leave_end:
                leave_dates.add(current)
                current += timedelta(days=1)

    except Exception:
        logger.warning(
            "LeaveRequest model unavailable while materializing attendance | employee=%s",
            employee.id,
        )

    expanded_holiday_dates = set()

    holidays = CompanyHoliday.objects.filter(
        company=company,
        is_active=True,
        start_date__lte=effective_end,
        end_date__gte=effective_start,
    ).only("start_date", "end_date")

    for holiday in holidays:
        current = max(holiday.start_date, effective_start)
        holiday_last = min(holiday.end_date, effective_end)

        while current <= holiday_last:
            expanded_holiday_dates.add(current)
            current += timedelta(days=1)

    schedule = WorkScheduleResolver.resolve(employee)

    created = 0
    absent_created = 0
    weekend_created = 0
    holiday_created = 0
    leave_created = 0
    skipped_existing = 0

    for current_date in _daterange(effective_start, effective_end):
        if current_date in existing_dates:
            skipped_existing += 1
            continue

        if getattr(employee, "status", None) and str(employee.status).upper() == "TERMINATED":
            continue

        status_value = "absent"
        reason_code = "auto_payroll_absent"

        if current_date in leave_dates:
            status_value = "leave"
            reason_code = "approved_leave"

        elif current_date in expanded_holiday_dates:
            status_value = "holiday"
            reason_code = "company_holiday"

        elif schedule and schedule.is_weekend(current_date):
            status_value = "weekend"
            reason_code = "weekly_off"

        record, was_created = AttendanceRecord.objects.get_or_create(
            employee=employee,
            date=current_date,
            defaults={
                "status": status_value,
                "reason_code": reason_code,
                "is_leave": status_value == "leave",
                "late_minutes": 0,
                "early_minutes": 0,
                "overtime_minutes": 0,
                "actual_hours": 0,
                "official_hours": 0,
            },
        )

        if not was_created:
            skipped_existing += 1
            continue

        if status_value != "leave":
            try:
                WorkdayEngine.apply(record, force=True)
            except Exception:
                logger.exception(
                    "❌ Failed applying WorkdayEngine after payroll materialization | employee=%s | date=%s",
                    employee.id,
                    current_date,
                )

        created += 1

        if status_value == "absent":
            absent_created += 1
        elif status_value == "weekend":
            weekend_created += 1
        elif status_value == "holiday":
            holiday_created += 1
        elif status_value == "leave":
            leave_created += 1

    return {
        "created": created,
        "absent_created": absent_created,
        "weekend_created": weekend_created,
        "holiday_created": holiday_created,
        "leave_created": leave_created,
        "skipped_existing": skipped_existing,
    }


# ================================================================
# 🕘 Attendance Status Helpers
# ================================================================
ABSENT_STATUSES = {
    "absent",
    "غياب",
    "غائب",
    "غايب",
    "a",
}

PRESENT_STATUSES = {
    "present",
    "حاضر",
    "دوام",
    "موجود",
    "p",
}

LATE_STATUSES = {
    "late",
    "متأخر",
    "تأخير",
    "l",
}

OVERTIME_STATUSES = {
    "overtime",
    "إضافي",
    "اضافي",
    "عمل إضافي",
    "عمل اضافي",
    "ot",
}

LEAVE_STATUSES = {
    "leave",
    "on_leave",
    "إجازة",
    "اجازة",
}

HOLIDAY_STATUSES = {
    "holiday",
    "official_holiday",
    "إجازة رسمية",
    "اجازة رسمية",
}

OFFDAY_STATUSES = {
    "off",
    "offday",
    "weekend",
    "rest",
    "راحة",
    "إجازة أسبوعية",
    "اجازة اسبوعية",
}


def _normalize_attendance_status(value) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""

    if raw in ABSENT_STATUSES:
        return "ABSENT"

    if raw in PRESENT_STATUSES:
        return "PRESENT"

    if raw in LATE_STATUSES:
        return "LATE"

    if raw in OVERTIME_STATUSES:
        return "OVERTIME"

    if raw in LEAVE_STATUSES:
        return "LEAVE"

    if raw in HOLIDAY_STATUSES:
        return "HOLIDAY"

    if raw in OFFDAY_STATUSES:
        return "OFFDAY"

    return raw.upper()


def _is_present_like_attendance(att) -> bool:
    normalized = _normalize_attendance_status(getattr(att, "status", ""))

    if normalized in {"PRESENT", "LATE", "OVERTIME"}:
        return True

    check_in = getattr(att, "check_in", None)
    check_out = getattr(att, "check_out", None)
    late_minutes = int(getattr(att, "late_minutes", 0) or 0)
    overtime_minutes = int(getattr(att, "overtime_minutes", 0) or 0)

    return bool(check_in or check_out or late_minutes > 0 or overtime_minutes > 0)


# ================================================================
# 💰 Salary Source Resolver
# ================================================================
def _resolve_monthly_base_salary(record) -> Decimal:
    if record.contract and getattr(record.contract, "basic_salary", None):
        return _money(record.contract.basic_salary)

    financial_info = getattr(record.employee, "financial_info", None)
    if financial_info and getattr(financial_info, "basic_salary", None):
        return _money(financial_info.basic_salary)

    return Decimal("0.00")


def _resolve_monthly_allowance(record) -> Decimal:
    """
    نحافظ على قيمة allowance الموجودة في السجل إن كانت موجودة،
    وإلا نحاول تركيبها من البيانات المالية.
    """
    record_allowance = _money(getattr(record, "allowance", None))
    if record_allowance > 0:
        return record_allowance

    financial_info = getattr(record.employee, "financial_info", None)
    if not financial_info:
        return Decimal("0.00")

    housing = _money(getattr(financial_info, "housing_allowance", None))
    transport = _money(getattr(financial_info, "transport_allowance", None))
    food = _money(getattr(financial_info, "food_allowance", None))
    other = _money(getattr(financial_info, "other_allowances", None))

    return _money(housing + transport + food + other)


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
    return total.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


# ================================================================
# 🧮 Calculate Payroll Run (With Legal Leave Filtering Layer)
# 🟢 Now Pro-Rated From Actual Entitlement Start Date
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
        base_salary = _resolve_monthly_base_salary(record)
        if base_salary <= 0:
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

    absence_engine = AbsenceDeductionEngine(policy="FIXED_30")

    LeaveRequest = None
    try:
        from leave_center.models import LeaveRequest as _LeaveRequest
        LeaveRequest = _LeaveRequest
    except Exception:
        logger.warning("LeaveRequest model not found — Legal filtering skipped")

    for record in records:
        employee = record.employee

        # ========================================================
        # 🧱 Ensure missing attendance is materialized before payroll
        # ========================================================
        try:
            _materialize_missing_attendance_for_payroll_window(
                employee=employee,
                company=run.company,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception:
            logger.exception(
                "❌ Failed materializing missing attendance before payroll calculation | employee=%s | run=%s",
                employee.id,
                run.id,
            )

        # ========================================================
        # 1) Resolve monthly reference amounts
        # ========================================================
        monthly_base_salary = _resolve_monthly_base_salary(record)
        monthly_allowance = _resolve_monthly_allowance(record)

        # ========================================================
        # 2) Resolve effective payroll window based on actual entitlement
        # ========================================================
        employment_start_date = _resolve_employment_start_date(record)
        actual_existence_date = _resolve_actual_entity_existence_date(record)
        entitlement_start_date = _resolve_record_entitlement_start_date(record)

        effective_start_date = (
            max(start_date, entitlement_start_date)
            if entitlement_start_date else start_date
        )
        effective_end_date = end_date

        # لو الموظف بدأ بعد نهاية الشهر => لا يوجد استحقاق
        if effective_start_date > effective_end_date:
            record.base_salary = Decimal("0.00")
            record.allowance = Decimal("0.00")
            record.overtime = Decimal("0.00")
            record.bonus = Decimal("0.00")
            record.deductions = Decimal("0.00")
            record.net_salary = Decimal("0.00")

            # ✅ تصفير أي بيانات دفع قديمة قبل الحفظ
            record.paid_amount = Decimal("0.00")
            record.payment_method = None
            record.paid_at = None
            record.status = "PENDING"

            record.breakdown = {
                "salary_source": "CONTRACT"
                if record.contract and getattr(record.contract, "basic_salary", None)
                else "FINANCIAL_INFO",
                "employment_start_date": (
                    employment_start_date.isoformat() if employment_start_date else None
                ),
                "actual_existence_date": (
                    actual_existence_date.isoformat() if actual_existence_date else None
                ),
                "entitlement_start_date": (
                    entitlement_start_date.isoformat() if entitlement_start_date else None
                ),
                "payroll_period_start": start_date.isoformat(),
                "payroll_period_end": end_date.isoformat(),
                "effective_start_date": effective_start_date.isoformat(),
                "effective_end_date": effective_end_date.isoformat(),
                "eligible_days": 0,
                "payable_days_before_deduction": 0,
                "payable_days_after_deduction": 0,
                "leave_paid_days": 0,
                "leave_partial_unpaid_days": 0,
                "unpaid_absence_days": 0,
                "inferred_absence_days": 0,
                "absent_days_legal": 0,
                "attendance_activity_found": False,
                "present_like_days_count": 0,
                "explicit_absent_days_count": 0,
                "leave_status_days_count": 0,
                "offday_days_count": 0,
                "covered_non_present_days": 0,
                "full_period_unpaid_mode": False,
                "full_period_unpaid_reason": None,
                "full_period_unpaid_offday_days": 0,
                "late_days_count": 0,
                "overtime_days_count": 0,
                "monthly_reference_base_salary": float(monthly_base_salary),
                "monthly_reference_allowance": float(monthly_allowance),
                "base_salary_prorated": 0.0,
                "allowance_prorated": 0.0,
                "absence_deduction": 0.0,
                "absence_deduction_base_component": 0.0,
                "absence_deduction_allowance_component": 0.0,
                "absence_deduction_bonus_component": 0.0,
                "absence_deduction_overtime_component": 0.0,
                "absence_deduction_gross_basis": 0.0,
                "raw_total_deductions_before_cap": 0.0,
                "deductions_capped_to_gross": False,
                "gross_earnings_before_deductions": 0.0,
                "late_minutes": 0,
                "late_deduction": 0.0,
                "overtime_minutes": 0,
                "overtime_amount": 0.0,
                "manual_additions": 0.0,
                "manual_deductions": 0.0,
                "final_net_salary": 0.0,
                "note": "No payroll entitlement during this month because actual entitlement starts after payroll period.",
            }
            record.save(
                update_fields=[
                    "base_salary",
                    "allowance",
                    "overtime",
                    "bonus",
                    "deductions",
                    "net_salary",
                    "paid_amount",
                    "payment_method",
                    "paid_at",
                    "status",
                    "breakdown",
                ]
            )
            continue

        eligible_days = Decimal(
            (effective_end_date - effective_start_date).days + 1
        )

        # ========================================================
        # 3) Attendance within effective window only
        # ========================================================
        attendance_qs = AttendanceRecord.objects.filter(
            employee=employee,
            date__range=(effective_start_date, effective_end_date),
        )

        attendance_rows = list(
            attendance_qs.only(
                "date",
                "status",
                "late_minutes",
                "overtime_minutes",
                "check_in",
                "check_out",
            )
        )

        present_like_dates = set()
        explicit_absent_dates = set()
        leave_status_dates = set()
        offday_dates = set()

        total_late_minutes = 0
        total_overtime_minutes = 0
        late_days_count = 0
        overtime_days_count = 0

        for att in attendance_rows:
            normalized_status = _normalize_attendance_status(
                getattr(att, "status", "")
            )
            att_date = att.date

            late_minutes = int(getattr(att, "late_minutes", 0) or 0)
            overtime_minutes = int(getattr(att, "overtime_minutes", 0) or 0)

            total_late_minutes += late_minutes
            total_overtime_minutes += overtime_minutes

            if late_minutes > 0:
                late_days_count += 1

            if overtime_minutes > 0:
                overtime_days_count += 1

            if normalized_status == "ABSENT":
                explicit_absent_dates.add(att_date)
                continue

            if normalized_status == "LEAVE":
                leave_status_dates.add(att_date)
                continue

            if normalized_status in {"OFFDAY", "HOLIDAY"}:
                offday_dates.add(att_date)
                continue

            if _is_present_like_attendance(att):
                present_like_dates.add(att_date)

        has_attendance_activity = bool(
            attendance_rows
            or total_late_minutes > 0
            or total_overtime_minutes > 0
            or explicit_absent_dates
            or present_like_dates
        )

        # ========================================================
        # 4) Approved leaves map inside effective window
        # ========================================================
        leave_map = {}

        if LeaveRequest:
            approved_leaves = LeaveRequest.objects.filter(
                employee=employee,
                status="approved",
                start_date__lte=effective_end_date,
                end_date__gte=effective_start_date,
            ).only(
                "start_date",
                "end_date",
                "pay_percentage",
            )

            for leave in approved_leaves:
                current = max(leave.start_date, effective_start_date)
                leave_end = min(leave.end_date, effective_end_date)

                while current <= leave_end:
                    leave_map[current] = leave
                    current += timedelta(days=1)

        # ========================================================
        # 5) Determine unpaid absence inside eligible period
        # ========================================================
        unpaid_absence_days = Decimal("0.00")
        inferred_absence_days = Decimal("0.00")
        leave_paid_days = Decimal("0.00")
        leave_partial_unpaid_days = Decimal("0.00")
        covered_non_present_days = Decimal("0.00")
        full_period_unpaid_mode = False
        full_period_unpaid_reason = None
        full_period_unpaid_offday_days = Decimal("0.00")

        for current_date in _daterange(effective_start_date, effective_end_date):
            related_leave = leave_map.get(current_date)

            if related_leave:
                covered_non_present_days += Decimal("1.00")

                pay_percentage = _to_decimal(
                    getattr(related_leave, "pay_percentage", 0),
                    "0",
                )
                pay_percentage = max(
                    Decimal("0"),
                    min(Decimal("100"), pay_percentage),
                )
                unpaid_fraction = (Decimal("100") - pay_percentage) / Decimal("100")
                paid_fraction = pay_percentage / Decimal("100")

                if paid_fraction > 0:
                    leave_paid_days += paid_fraction.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP,
                    )

                if unpaid_fraction > 0:
                    unpaid_absence_days += unpaid_fraction.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP,
                    )
                    leave_partial_unpaid_days += unpaid_fraction.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP,
                    )
                continue

            if current_date in leave_status_dates:
                covered_non_present_days += Decimal("1.00")
                continue

            if current_date in offday_dates:
                covered_non_present_days += Decimal("1.00")
                continue

            if current_date in explicit_absent_dates:
                covered_non_present_days += Decimal("1.00")
                unpaid_absence_days += Decimal("1.00")
                continue

            if current_date in present_like_dates:
                continue

            # ✅ استنتاج الغياب فقط إذا وجدت حركة حضور فعلية داخل الفترة
            if has_attendance_activity:
                covered_non_present_days += Decimal("1.00")
                unpaid_absence_days += Decimal("1.00")
                inferred_absence_days += Decimal("1.00")

        # --------------------------------------------------------
        # 🟢 Full-period unpaid mode
        # --------------------------------------------------------
        if (
            eligible_days > Decimal("0.00")
            and covered_non_present_days >= eligible_days
            and len(present_like_dates) == 0
            and leave_paid_days <= Decimal("0.00")
            and total_late_minutes == 0
            and total_overtime_minutes == 0
        ):
            full_period_unpaid_mode = True
            full_period_unpaid_reason = "full_eligible_period_has_no_payable_attendance"
            full_period_unpaid_offday_days = Decimal(str(len(offday_dates)))
            unpaid_absence_days = eligible_days
            inferred_absence_days = max(
                inferred_absence_days,
                Decimal("0.00"),
            )

        if unpaid_absence_days > eligible_days:
            unpaid_absence_days = eligible_days

        payable_days_before_deduction = eligible_days
        payable_days_after_deduction = eligible_days - unpaid_absence_days
        if payable_days_after_deduction < Decimal("0.00"):
            payable_days_after_deduction = Decimal("0.00")

        # ========================================================
        # 6) Pro-rate base salary and allowances
        # ========================================================
        prorated_base_salary = _calculate_prorated_amount(
            monthly_base_salary,
            eligible_days,
        )
        prorated_allowance = _calculate_prorated_amount(
            monthly_allowance,
            eligible_days,
        )

        record.base_salary = prorated_base_salary
        record.allowance = prorated_allowance

        # ========================================================
        # 7) Hourly rate based on monthly reference salary
        # ========================================================
        hourly_rate = (
            monthly_base_salary / (DAYS_DIVISOR * HOURS_PER_DAY)
        ).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

        # ========================================================
        # 8) Manual adjustments first
        # ========================================================
        adjustments = PayrollAdjustment.objects.filter(
            run=run,
            employee=employee,
        )

        manual_additions = (
            adjustments.filter(type="ADDITION")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        manual_additions = _money(manual_additions)

        manual_deductions = (
            adjustments.filter(type="DEDUCTION")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        manual_deductions = _money(manual_deductions)

        # ========================================================
        # 9) Overtime / Late / Gross Absence Deduction
        # ========================================================
        overtime_amount = (
            Decimal(total_overtime_minutes) * (hourly_rate / Decimal("60"))
        ).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

        late_deduction = (
            Decimal(total_late_minutes) * (hourly_rate / Decimal("60"))
        ).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

        record.overtime = overtime_amount
        record.bonus = manual_additions

        monthly_gross_reference = _money(
            monthly_base_salary
            + monthly_allowance
            + manual_additions
            + overtime_amount
        )

        gross_daily_rate = absence_engine._calculate_daily_rate(
            monthly_gross_reference
        )

        absence_deduction = (
            gross_daily_rate * unpaid_absence_days
        ).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

        absence_base_component = (
            absence_engine._calculate_daily_rate(monthly_base_salary)
            * unpaid_absence_days
        ).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

        absence_allowance_component = (
            absence_engine._calculate_daily_rate(monthly_allowance)
            * unpaid_absence_days
        ).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

        absence_bonus_component = (
            absence_engine._calculate_daily_rate(manual_additions)
            * unpaid_absence_days
        ).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

        absence_overtime_component = (
            absence_engine._calculate_daily_rate(overtime_amount)
            * unpaid_absence_days
        ).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

        # ========================================================
        # 10) Final values
        # ✅ Cap deductions to gross earnings so model.save()
        # does not recompute a negative net salary in DRAFT/CALCULATED
        # ========================================================
        raw_total_deductions = _money(
            absence_deduction + late_deduction + manual_deductions
        )

        gross_earnings_before_deductions = _money(
            record.base_salary
            + record.allowance
            + record.bonus
            + record.overtime
        )

        deductions_capped_to_gross = raw_total_deductions > gross_earnings_before_deductions

        record.deductions = _money(
            min(raw_total_deductions, gross_earnings_before_deductions)
        )

        salary = calculate_salary(
            base_salary=prorated_base_salary,
            allowances=prorated_allowance,
            bonuses=record.bonus + record.overtime,
            deductions=record.deductions,
        )

        if salary < Decimal("0.00"):
            salary = Decimal("0.00")

        record.net_salary = salary

        # ✅ لأن هذا احتساب جديد، نصفر أي أثر دفع قديم
        record.paid_amount = Decimal("0.00")
        record.payment_method = None
        record.paid_at = None
        record.status = "PENDING"

        record.breakdown = {
            "salary_source": "CONTRACT"
            if record.contract and getattr(record.contract, "basic_salary", None)
            else "FINANCIAL_INFO",
            "employment_start_date": (
                employment_start_date.isoformat() if employment_start_date else None
            ),
            "actual_existence_date": (
                actual_existence_date.isoformat() if actual_existence_date else None
            ),
            "entitlement_start_date": (
                entitlement_start_date.isoformat() if entitlement_start_date else None
            ),
            "payroll_period_start": start_date.isoformat(),
            "payroll_period_end": end_date.isoformat(),
            "effective_start_date": effective_start_date.isoformat(),
            "effective_end_date": effective_end_date.isoformat(),
            "days_in_month_policy": 30,
            "eligible_days": float(eligible_days),
            "payable_days_before_deduction": float(payable_days_before_deduction),
            "payable_days_after_deduction": float(payable_days_after_deduction),
            "leave_paid_days": float(leave_paid_days),
            "leave_partial_unpaid_days": float(leave_partial_unpaid_days),
            "unpaid_absence_days": float(unpaid_absence_days),
            "inferred_absence_days": float(inferred_absence_days),
            "absent_days_legal": float(unpaid_absence_days),
            "attendance_activity_found": has_attendance_activity,
            "present_like_days_count": len(present_like_dates),
            "explicit_absent_days_count": len(explicit_absent_dates),
            "leave_status_days_count": len(leave_status_dates),
            "offday_days_count": len(offday_dates),
            "covered_non_present_days": float(covered_non_present_days),
            "full_period_unpaid_mode": full_period_unpaid_mode,
            "full_period_unpaid_reason": full_period_unpaid_reason,
            "full_period_unpaid_offday_days": float(full_period_unpaid_offday_days),
            "late_days_count": int(late_days_count),
            "overtime_days_count": int(overtime_days_count),
            "monthly_reference_base_salary": float(monthly_base_salary),
            "monthly_reference_allowance": float(monthly_allowance),
            "monthly_reference_gross_salary": float(monthly_gross_reference),
            "base_salary_prorated": float(prorated_base_salary),
            "allowance_prorated": float(prorated_allowance),
            "daily_rate_base_salary": float(absence_engine._calculate_daily_rate(monthly_base_salary)),
            "daily_rate_gross_salary": float(gross_daily_rate),
            "absence_deduction": float(absence_deduction),
            "absence_deduction_gross_basis": float(monthly_gross_reference),
            "absence_deduction_base_component": float(absence_base_component),
            "absence_deduction_allowance_component": float(absence_allowance_component),
            "absence_deduction_bonus_component": float(absence_bonus_component),
            "absence_deduction_overtime_component": float(absence_overtime_component),
            "raw_total_deductions_before_cap": float(raw_total_deductions),
            "deductions_capped_to_gross": deductions_capped_to_gross,
            "gross_earnings_before_deductions": float(gross_earnings_before_deductions),
            "late_minutes": int(total_late_minutes),
            "late_deduction": float(late_deduction),
            "overtime_minutes": int(total_overtime_minutes),
            "overtime_amount": float(overtime_amount),
            "manual_additions": float(manual_additions),
            "manual_deductions": float(manual_deductions),
            "final_net_salary": float(salary),
        }

        record.save(
            update_fields=[
                "base_salary",
                "allowance",
                "overtime",
                "bonus",
                "deductions",
                "net_salary",
                "paid_amount",
                "payment_method",
                "paid_at",
                "status",
                "breakdown",
            ]
        )

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
        record.paid_amount = Decimal("0.00")
        record.payment_method = None
        record.paid_at = None
        record.save(
            update_fields=[
                "net_salary",
                "breakdown",
                "status",
                "paid_amount",
                "payment_method",
                "paid_at",
            ]
        )

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

    record = (
        PayrollRecord.objects
        .select_for_update()
        .select_related("run", "employee")
        .get(pk=record.pk)
    )

    run = record.run
    company = run.company

    if run.status != PayrollRun.Status.APPROVED:
        raise ValueError("PayrollRun must be APPROVED before payments")

    if payment_method not in ["CASH", "BANK"]:
        raise ValueError("Invalid payment method")

    if record.status == "PAID":
        raise ValueError("PayrollRecord already fully paid")

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

    JournalLine.objects.create(
        entry=entry,
        account_code="2100",
        account_name="Payroll Payable",
        debit=amount,
        credit=Decimal("0.00"),
    )

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

    new_paid_amount = (paid_amount + amount).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

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

    if not run.records.exclude(status="PAID").exists():
        run.status = PayrollRun.Status.PAID
        run.save(update_fields=["status"])

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