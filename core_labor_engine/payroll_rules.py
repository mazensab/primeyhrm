# ============================================================
# 📄 الملف: payroll_rules.py
# 💵 معالجة الرواتب والمكافآت والإضافي وفق نظام العمل السعودي
# ============================================================

from .constants_saudi_labour import OVERTIME_RATE
from .attendance_rules import calculate_absence_deduction, calculate_delay_deduction

def calculate_overtime_payment(base_salary, overtime_hours, hourly_rate):
    """حساب أجر الساعات الإضافية."""
    return overtime_hours * hourly_rate * OVERTIME_RATE

def calculate_total_salary(base_salary, overtime_hours=0, hourly_rate=0, absence_days=0, delay_hours=0):
    """حساب الراتب الصافي."""
    overtime = calculate_overtime_payment(base_salary, overtime_hours, hourly_rate)
    absence = calculate_absence_deduction(base_salary, absence_days)
    delay = calculate_delay_deduction(base_salary, delay_hours)
    total = base_salary + overtime - (absence + delay)
    return round(total, 2)
