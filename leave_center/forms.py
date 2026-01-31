# =====================================================================
# 📂 الملف: leave_center/forms.py — Phase 2 Ultra Pro
# =====================================================================

from django import forms
from django.utils import timezone
from django.db.models import Q

from .models import LeaveRequest, LeaveType, LeaveBalance


class LeaveRequestForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company", None)
        self.employee = kwargs.pop("employee", None)
        super().__init__(*args, **kwargs)

        # تصفية الأنواع حسب الشركة
        if self.company:
            self.fields["leave_type"].queryset = LeaveType.objects.filter(
                company=self.company
            )

        # Glass UI
        for f in self.fields.values():
            f.widget.attrs.update({"class": "form-control rounded-4"})

    class Meta:
        model = LeaveRequest
        fields = [
            "leave_type",
            "start_date",
            "end_date",
            "reason",
            "attachment",
        ]

    # =================================================================
    # 🟣 التحقق من صحة الطلب
    # =================================================================
    def clean(self):
        cleaned = super().clean()

        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        leave_type = cleaned.get("leave_type")

        # 1) valid dates
        if start and start < timezone.now().date():
            raise forms.ValidationError("لا يمكن تقديم إجازة بتاريخ سابق.")

        if start and end and end < start:
            raise forms.ValidationError("تاريخ النهاية يجب أن يكون بعد البداية.")

        if start and end:
            cleaned["total_days"] = (end - start).days + 1

        # 2) منع التداخل
        overlapping = LeaveRequest.objects.filter(
            employee=self.employee,
            company=self.company,
            status__in=["approved", "pending_manager", "pending_hr"],
        ).filter(
            Q(start_date__lte=end) & Q(end_date__gte=start)
        )

        if overlapping.exists():
            raise forms.ValidationError("يوجد طلب آخر يتداخل مع نفس المدة.")

        # ===============================================================
        # 🟦 قواعد Phase 2 — حسب قانون العمل السعودي
        # ===============================================================
        emp = self.employee
        category = leave_type.category

        # -----------------------------
        # 🟢 1) maternity → فقط للإناث
        # -----------------------------
        if category == "maternity" and emp.gender != "female":
            raise forms.ValidationError("إجازة الأمومة مخصصة للإناث فقط.")

        # -----------------------------
        # 🟣 2) hajj → مرة كل 5 سنوات
        # -----------------------------
        if category == "hajj":
            old_hajj = LeaveRequest.objects.filter(
                employee=emp,
                leave_type__category="hajj",
                status="approved",
                start_date__gte=timezone.now().date() - timezone.timedelta(days=5 * 365)
            )
            if old_hajj.exists():
                raise forms.ValidationError("إجازة الحج تُمنح مرة كل 5 سنوات فقط.")

        # -----------------------------
        # 🟡 3) marriage → مرة واحدة فقط
        # -----------------------------
        if category == "marriage":
            old_marriage = LeaveRequest.objects.filter(
                employee=emp,
                leave_type__category="marriage",
                status="approved"
            )
            if old_marriage.exists():
                raise forms.ValidationError("إجازة الزواج تُمنح مرة واحدة فقط.")

        return cleaned

    # =================================================================
    # 🟩 التحقق من الرصيد
    # =================================================================
    def validate_balance(self):
        cleaned = self.cleaned_data
        leave_type = cleaned.get("leave_type")
        days = cleaned.get("total_days")

        if leave_type.category == "unpaid":
            return True

        balance, _ = LeaveBalance.objects.get_or_create(
            employee=self.employee,
            company=self.company
        )

        category = leave_type.category
        mapping = {
            "annual": balance.annual_balance,
            "sick": balance.sick_balance,
            "maternity": balance.maternity_balance,
            "marriage": balance.marriage_balance,
            "death": balance.death_balance,
            "hajj": balance.hajj_balance,
            "study": balance.study_balance,
        }

        available = mapping.get(category, 0)

        if days > available:
            raise forms.ValidationError(
                f"الرصيد غير كافٍ — المتاح: {available} يوم، المطلوب: {days} يوم."
            )

        return True

    # =================================================================
    # 🟢 الحفظ
    # =================================================================
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.company = self.company
        instance.employee = self.employee
        if commit:
            instance.save()
        return instance
