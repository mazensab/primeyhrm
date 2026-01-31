# ============================================================
# 📄 الملف: labour_engine.py
# 🧭 محرك تطبيق نظام العمل السعودي — Saudi Labour Engine V10.1
# ------------------------------------------------------------
# ✅ يطبق القوانين والمواد (98–107) من اللائحة التنفيذية 2025
# ✅ يحسب:
#     - خصم الغياب والتأخير
#     - الأجر الإضافي (1.5×)
#     - الحد الأدنى للأجور
#     - صافي الراتب الشهري بدقة
# ============================================================

from decimal import Decimal
from django.utils import timezone
from .constants_saudi_labour import (
    WORK_HOURS_PER_DAY,
    WORK_HOURS_PER_WEEK,
    OVERTIME_RATE,
    ABSENCE_DEDUCTION_RATE,
    DELAY_HOURLY_DEDUCTION,
    MIN_WAGE_SAR,
    MAX_ALLOWANCE_PERCENT,
)

# ------------------------------------------------------------
# 🧮 حساب خصم الغياب (لكل يوم غياب)
# ------------------------------------------------------------
def calculate_absence_deduction(base_salary, absence_days: int):
    return Decimal(base_salary) * Decimal(ABSENCE_DEDUCTION_RATE) * Decimal(absence_days)

# ------------------------------------------------------------
# 🕒 حساب خصم التأخير (لكل ساعة)
# ------------------------------------------------------------
def calculate_delay_deduction(base_salary, delay_hours: float):
    return Decimal(base_salary) * Decimal(DELAY_HOURLY_DEDUCTION) * Decimal(delay_hours)

# ------------------------------------------------------------
# 💰 حساب الأجر الإضافي
# ------------------------------------------------------------
def calculate_overtime_pay(base_salary, overtime_hours: float):
    hourly_rate = Decimal(base_salary) / Decimal(WORK_HOURS_PER_DAY * 30)
    return hourly_rate * Decimal(overtime_hours) * Decimal(OVERTIME_RATE)

# ------------------------------------------------------------
# 🧾 التحقق من الحد الأدنى للأجر
# ------------------------------------------------------------
def ensure_minimum_wage(total_salary: Decimal):
    return max(total_salary, Decimal(MIN_WAGE_SAR))

# ------------------------------------------------------------
# 💵 حساب الراتب الشهري الكامل
# ------------------------------------------------------------
def calculate_monthly_salary(contract, overtime_hours=0, absence_days=0, delay_hours=0):
    """
    🔹 يعتمد على بيانات عقد الموظف.
    🔹 يطبّق القوانين السعودية للخصومات والإضافي.
    """
    base = Decimal(contract.basic_salary)
    allowances = Decimal(contract.allowances)
    deductions = Decimal(contract.deductions)
    overtime = calculate_overtime_pay(base, overtime_hours)
    abs_deduct = calculate_absence_deduction(base, absence_days)
    delay_deduct = calculate_delay_deduction(base, delay_hours)

    gross = base + allowances + overtime
    total_deductions = deductions + abs_deduct + delay_deduct
    net = ensure_minimum_wage(gross - total_deductions)

    return {
        "base_salary": base,
        "allowances": allowances,
        "deductions": total_deductions,
        "overtime": overtime,
        "net_salary": net,
        "calculated_at": timezone.now(),
    }
