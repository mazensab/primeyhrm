# ================================================================
# 🔁 ResetBalanceEngine — V1 Ultra Pro
# Primey HR Cloud — Leave Center Reset Engine
# ================================================================

from django.utils.timezone import now
from django.db import transaction
from ..models import LeaveBalance, LeaveType, ResetHistory


class ResetBalanceEngine:
    """
    🧠 محرك إعادة ضبط أرصدة الإجازات للموظفين
    ------------------------------------------------------------
    ✔ متوافق 100% مع LeaveBalance الحالي
    ✔ يدعم manual reset + yearly reset
    ✔ يعالج الرصيد حسب نوع الإجازة (annual / sick / hajj ...)
    ✔ يسجل ResetHistory بشكل صحيح
    ✔ لا يعتمد على leave_type داخل LeaveBalance (غير موجود)
    ✔ قابل للتوسعة مستقبلاً (BalanceByType)
    """

    def __init__(self, employee, leave_type, performed_by=None):
        self.employee = employee
        self.company = employee.company
        self.leave_type = leave_type      # LeaveType object
        self.performed_by = performed_by

    # ------------------------------------------------------------------
    # 📌 قراءة الرصيد الحالي من LeaveBalance حسب نوع الإجازة
    # ------------------------------------------------------------------
    def _get_current_balance(self, balance_obj):
        category = self.leave_type.category

        mapping = {
            "annual": balance_obj.annual_balance,
            "sick": balance_obj.sick_balance,
            "maternity": balance_obj.maternity_balance,
            "marriage": balance_obj.marriage_balance,
            "death": balance_obj.death_balance,
            "hajj": balance_obj.hajj_balance,
            "study": balance_obj.study_balance,
            "unpaid": balance_obj.unpaid_balance,
        }

        return mapping.get(category, 0)

    # ------------------------------------------------------------------
    # 📌 تعيين رصيد جديد حسب leave_type.annual_balance
    # ------------------------------------------------------------------
    def _apply_new_balance(self, balance_obj):
        category = self.leave_type.category
        new_value = self.leave_type.annual_balance

        if category == "annual":
            balance_obj.annual_balance = new_value
        elif category == "sick":
            balance_obj.sick_balance = new_value
        elif category == "maternity":
            balance_obj.maternity_balance = new_value
        elif category == "marriage":
            balance_obj.marriage_balance = new_value
        elif category == "death":
            balance_obj.death_balance = new_value
        elif category == "hajj":
            balance_obj.hajj_balance = new_value
        elif category == "study":
            balance_obj.study_balance = new_value
        elif category == "unpaid":
            balance_obj.unpaid_balance = new_value

        balance_obj.save()
        return new_value

    # ------------------------------------------------------------------
    # 🚀 تنفيذ عملية إعادة الضبط
    # ------------------------------------------------------------------
    @transaction.atomic
    def reset(self):
        balance_obj = LeaveBalance.objects.filter(
            employee=self.employee,
            company=self.company
        ).first()

        if not balance_obj:
            return False, "لا يوجد رصيد مسجل لهذا الموظف."

        old_value = self._get_current_balance(balance_obj)
        new_value = self._apply_new_balance(balance_obj)

        # حفظ السجل
        ResetHistory.objects.create(
            company=self.company,
            employee=self.employee,
            old_balance=old_value,
            new_balance=new_value,
            year=now().year,
            performed_by=self.performed_by
        )

        return True, "تم إعادة ضبط رصيد الإجازة بنجاح."
