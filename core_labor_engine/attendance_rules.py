# ============================================================
# 📄 الملف: attendance_rules.py
# 🕒 القواعد الخاصة بالحضور والانصراف وفق اللائحة التنفيذية 2025
# ============================================================

from .constants_saudi_labour import ABSENCE_DEDUCTION_RATE, DELAY_HOURLY_DEDUCTION

def calculate_absence_deduction(base_salary, absent_days):
    """حساب خصم الغياب الكامل."""
    return base_salary * ABSENCE_DEDUCTION_RATE * absent_days

def calculate_delay_deduction(base_salary, delay_hours):
    """حساب خصم التأخير الجزئي."""
    return base_salary * DELAY_HOURLY_DEDUCTION * delay_hours

def validate_daily_hours(hours):
    """يتحقق من أن ساعات العمل اليومية لا تتجاوز الحد المسموح."""
    if hours > 8:
        return "⚠️ تجاوز الحد اليومي المسموح للساعات (8 ساعات)"
    return "✅ ضمن الحد النظامي"
