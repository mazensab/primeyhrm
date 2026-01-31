# ============================================================
# 📄 الملف: compliance_check.py
# ✅ مراقبة الالتزام بنظام العمل وإصدار التنبيهات القانونية
# ============================================================

def check_compliance(employee):
    """يفحص التزام الموظف بنظام العمل السعودي."""
    results = []
    if employee.base_salary < 4000:
        results.append("⚠️ الراتب أقل من الحد الأدنى للأجور.")
    if not employee.contract_signed:
        results.append("⚠️ لم يتم توقيع عقد العمل بعد.")
    if employee.work_hours > 48:
        results.append("⚠️ تجاوز الحد الأسبوعي لساعات العمل.")
    return results or ["✅ الموظف ملتزم بنظام العمل السعودي."]
