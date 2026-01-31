# ============================================================
# 📄 الملف: contract_rules.py
# ⚖️ منطق تحليل العقود وتحديد الصلاحيات وفق النظام السعودي
# ============================================================

from .constants_saudi_labour import CONTRACT_TYPES, MIN_WAGE_SAR

def validate_contract(contract):
    """يتحقق من أن العقد قانوني ومتوافق مع النظام."""
    errors = []
    if contract.salary < MIN_WAGE_SAR:
        errors.append("❌ الأجر أقل من الحد الأدنى للأجور المعتمد.")
    if contract.type not in CONTRACT_TYPES:
        errors.append("❌ نوع العقد غير معتمد في النظام السعودي.")
    return errors if errors else ["✅ العقد متوافق مع النظام."]

def contract_duration_days(contract):
    """يحسب مدة العقد بالأيام."""
    if contract.end_date and contract.start_date:
        return (contract.end_date - contract.start_date).days
    return None
