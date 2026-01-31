# ============================================================
# 📄 الملف: helpers.py
# 🧩 أدوات عامة للمحرك (تنسيق الأرقام، الوقت، والتحقق)
# ============================================================

from datetime import datetime

def format_currency(amount):
    """تنسيق المبلغ بعملة الريال السعودي."""
    return f"{amount:,.2f} ر.س"

def current_year():
    """إرجاع السنة الحالية."""
    return datetime.now().year

def percent(value):
    """تحويل القيمة إلى نسبة مئوية منسقة."""
    return f"{round(value * 100, 2)}%"
