# ================================================================
# 📂 الملف: employee_center/forms.py
# 🧭 Mham Cloud — Employee Center V24 Ultra Pro
# ================================================================

from django import forms
from .models import (
    Employee,
    EmploymentInfo,
    FinancialInfo,
    Contract,
    EmployeeDocument,
    TerminationRecord,
    ResignationRecord,
    EoSBRecord,
)

# ================================================================
# 🧾 1) Employee Form — نموذج الموظف
# ================================================================
class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "full_name",
            "arabic_name",
            "national_id",
            "passport_number",
            "date_of_birth",
            "nationality",
            "gender",
            "status",
            "department",
            "job_title",
            "employment_type",
            "join_date",
            "probation_end_date",
            "end_date",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "join_date": forms.DateInput(attrs={"type": "date"}),
            "probation_end_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


# ================================================================
# 🧾 2) Employment Info Form — معلومات العمل
# ================================================================
class EmploymentInfoForm(forms.ModelForm):
    class Meta:
        model = EmploymentInfo
        fields = [
            "job_grade",
            "job_level",
            "job_category",
            "direct_manager",
            "work_location",
            "branch_name",
            "shift_type",
        ]


# ================================================================
# 🧾 3) Financial Info Form — معلومات الرواتب
# ================================================================
class FinancialInfoForm(forms.ModelForm):
    class Meta:
        model = FinancialInfo
        fields = [
            "basic_salary",
            "housing_allowance",
            "transport_allowance",
            "food_allowance",
            "other_allowances",
            "is_gosi_enabled",
            "is_tax_enabled",
            "bank_name",
            "iban",
        ]


# ================================================================
# 🧾 4) Contract Form — العقود
# ================================================================
class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            "contract_type",
            "start_date",
            "end_date",
            "probation_period_months",
            "salary",
            "housing",
            "transport",
            "other_allowances",
            "is_active",
            "is_renewable",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


# ================================================================
# 🧾 5) Employee Document Form — مستندات الموظفين
# ================================================================
class EmployeeDocumentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        fields = [
            "document_type",
            "file",
            "expiry_date",
            "notes",
        ]
        widgets = {
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }


# ================================================================
# 🧾 6) Termination Form — إنهاء الخدمة
# ================================================================
class TerminationRecordForm(forms.ModelForm):
    class Meta:
        model = TerminationRecord
        fields = [
            "reason",
            "termination_date",
            "notes",
        ]
        widgets = {
            "termination_date": forms.DateInput(attrs={"type": "date"}),
        }


# ================================================================
# 🧾 7) Resignation Form — الاستقالة
# ================================================================
class ResignationRecordForm(forms.ModelForm):
    class Meta:
        model = ResignationRecord
        fields = [
            "last_working_day",
            "reason",
        ]
        widgets = {
            "last_working_day": forms.DateInput(attrs={"type": "date"}),
        }


# ================================================================
# 🧾 8) EoSB Record Form — مكافأة نهاية الخدمة (V24 Ultra Clean)
# ================================================================
class EosbRecordForm(forms.ModelForm):
    class Meta:
        model = EoSBRecord
        fields = [
            "years_of_service",
            "basic_salary",
            "active_salary",
            "total_amount",
            "calculation_method",
            "notes",
        ]
        widgets = {
            "years_of_service": forms.NumberInput(attrs={"step": "0.01"}),
            "basic_salary": forms.NumberInput(attrs={"step": "0.01"}),
            "active_salary": forms.NumberInput(attrs={"step": "0.01"}),
            "total_amount": forms.NumberInput(attrs={"step": "0.01"}),
        }
