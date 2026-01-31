# 📂 الملف: payroll_center/forms.py
# 🧭 Primey HR Cloud — Payroll Form V5.0 (Smart Validation + UX Ready)
# 🚀 نموذج إنشاء وتعديل الرواتب بواجهة حديثة وتحقق تلقائي
# ===============================================================

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import PayrollRecord


class PayrollForm(forms.ModelForm):
    """
    🧮 نموذج إدارة وإنشاء الرواتب
    - يدعم التحقق التلقائي من القيم
    - يمنع تكرار الرواتب لنفس الموظف في نفس الشهر
    - متوافق مع الواجهات الحديثة (Glass UI)
    """

    class Meta:
        model = PayrollRecord
        fields = ["employee", "month", "base_salary", "allowance", "deductions", "notes"]
        labels = {
            "employee": "الموظف",
            "month": "شهر الراتب",
            "base_salary": "الراتب الأساسي",
            "allowance": "البدلات",
            "deductions": "الخصومات",
            "notes": "ملاحظات إضافية",
        }
        widgets = {
            "employee": forms.Select(attrs={
                "class": "form-select shadow-sm border-0 rounded-3",
                "style": "background:rgba(255,255,255,0.85);backdrop-filter:blur(8px);"
            }),
            "month": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control shadow-sm border-0 rounded-3",
                "style": "background:rgba(255,255,255,0.85);"
            }),
            "base_salary": forms.NumberInput(attrs={
                "class": "form-control text-center shadow-sm border-0 rounded-3",
                "placeholder": "0.00"
            }),
            "allowance": forms.NumberInput(attrs={
                "class": "form-control text-center shadow-sm border-0 rounded-3",
                "placeholder": "0.00"
            }),
            "deductions": forms.NumberInput(attrs={
                "class": "form-control text-center shadow-sm border-0 rounded-3",
                "placeholder": "0.00"
            }),
            "notes": forms.Textarea(attrs={
                "rows": 3,
                "class": "form-control shadow-sm border-0 rounded-3",
                "placeholder": "أضف أي ملاحظات إضافية هنا..."
            }),
        }

    # ============================================================
    # 🧠 التحقق من صحة البيانات قبل الحفظ
    # ============================================================
    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get("employee")
        month = cleaned_data.get("month")
        base_salary = cleaned_data.get("base_salary", 0)
        allowance = cleaned_data.get("allowance", 0)
        deductions = cleaned_data.get("deductions", 0)

        # 🔹 التحقق من القيم المالية
        if base_salary < 0 or allowance < 0 or deductions < 0:
            raise ValidationError("⚠️ لا يمكن أن تكون القيم المالية سالبة.")

        # 🔹 منع تكرار سجل راتب لنفس الشهر
        if employee and month:
            exists = PayrollRecord.objects.filter(employee=employee, month__month=month.month).exists()
            if exists:
                raise ValidationError(f"❌ يوجد بالفعل سجل راتب لهذا الموظف في شهر {month.strftime('%B %Y')}.")

        # 🔹 التحقق من أن الشهر ليس في المستقبل
        if month and month > timezone.now().date():
            raise ValidationError("⚠️ لا يمكن إنشاء راتب لتاريخ مستقبلي.")

        return cleaned_data

    # ============================================================
    # 🧩 تحسين تجربة المستخدم عند الحفظ
    # ============================================================
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.net_salary = (instance.base_salary + instance.allowance) - instance.deductions
        if commit:
            instance.save()
        return instance
