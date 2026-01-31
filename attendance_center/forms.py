# ============================================================
# 📘 نماذج سياسات الحضور — Attendance Policy Forms V1.5 Ultra Pro
# ============================================================

from django import forms
from .models import AttendancePolicy, EmployeeAttendancePolicy


# ============================================================
# 📘 نموذج سياسة الحضور العامة — AttendancePolicyForm
# ============================================================
class AttendancePolicyForm(forms.ModelForm):
    """
    🧭 النموذج الرسمي لإنشاء وتعديل سياسة حضور على مستوى الشركة.
    مناسب لواجهة Glass UI ومعايير Saudi Labour Law 2025.
    """

    work_start = forms.TimeField(
        label="⏰ بداية الدوام",
        widget=forms.TimeInput(attrs={
            "class": "form-control",
            "type": "time"
        })
    )

    work_end = forms.TimeField(
        label="⏱ نهاية الدوام",
        widget=forms.TimeInput(attrs={
            "class": "form-control",
            "type": "time"
        })
    )

    grace_minutes = forms.IntegerField(
        label="⌛ دقائق السماح",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": 0,
            "placeholder": "مثال: 15"
        })
    )

    overtime_enabled = forms.BooleanField(
        label="🔋 هل يسمح بالعمل الإضافي؟",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    overtime_rate = forms.DecimalField(
        label="📈 معامل احتساب ساعات العمل الإضافية",
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.01"
        })
    )

    auto_absent_if_no_checkin = forms.BooleanField(
        label="🚫 اعتباره غائب في حال عدم وجود بصمة",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    weekend_days = forms.CharField(
        label="📆 أيام نهاية الأسبوع (مثال: fri,sat)",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "fri,sat"
        })
    )

    weekly_hours_limit = forms.IntegerField(
        label="📘 الحد الأسبوعي لساعات العمل",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": 1,
            "placeholder": "48"
        })
    )

    class Meta:
        model = AttendancePolicy
        fields = [
            "work_start", "work_end",
            "grace_minutes",
            "overtime_enabled", "overtime_rate",
            "auto_absent_if_no_checkin",
            "weekend_days",
            "weekly_hours_limit"
        ]


# ============================================================
# 🎯 نموذج سياسة حضور خاصة بالموظف — EmployeeAttendancePolicyForm
# ============================================================
class EmployeeAttendancePolicyForm(forms.ModelForm):
    """
    🎯 Override Form
    يسمح بإعطاء الموظف سياسة حضور خاصة مختلفة عن سياسة الشركة.
    """

    custom_work_start = forms.TimeField(
        required=False,
        label="⏰ بداية الدوام (خاص)",
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"})
    )

    custom_work_end = forms.TimeField(
        required=False,
        label="⏱ نهاية الدوام (خاص)",
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"})
    )

    custom_grace_minutes = forms.IntegerField(
        required=False,
        label="⌛ دقائق السماح (خاص)",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 0})
    )

    custom_overtime_enabled = forms.BooleanField(
        required=False,
        label="🔋 السماح بالعمل الإضافي (خاص)",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    custom_overtime_rate = forms.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=2,
        label="📈 معامل العمل الإضافي (خاص)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )

    class Meta:
        model = EmployeeAttendancePolicy
        fields = [
            "company_policy",
            "custom_work_start", "custom_work_end",
            "custom_grace_minutes",
            "custom_overtime_enabled", "custom_overtime_rate"
        ]
        widgets = {
            "company_policy": forms.Select(attrs={"class": "form-select"})
        }
        labels = {
            "company_policy": "🏢 السياسة الرئيسية (Company Policy)",
        }
