# ======================================================================
# 📌 Primey HR Cloud — Company Manager
# 🧩 File: forms.py — Ultra Pro V4 (Synced with Models)
# ======================================================================

from django import forms
from company_manager.models import Company


class CompanyForm(forms.ModelForm):
    """
    🌟 Ultra Pro V4 — Synced With Company Model
    ✔ متزامن رسميًا مع models.py
    ✔ يدعم العنوان الوطني الوطني بالكامل
    ✔ جاهز للربط مع Templates V4
    """

    class Meta:
        model = Company
        fields = [
            # القسم الأول — بيانات أساسية
            "name",
            "email",
            "phone",

            # القسم الثاني — الهوية والسجل التجاري
            "commercial_number",
            "vat_number",
            "logo",

            # القسم الثالث — العنوان الوطني السعودي
            "building_number",
            "street",
            "district",
            "city",
            "postal_code",
            "short_address",
        ]

        widgets = {
            # ===============================
            # 📌 القسم الأول — بيانات الشركة
            # ===============================
            "name": forms.TextInput(attrs={
                "class": "primey-input",
                "placeholder": "اسم الشركة"
            }),

            "email": forms.EmailInput(attrs={
                "class": "primey-input",
                "placeholder": "البريد الإلكتروني"
            }),

            "phone": forms.TextInput(attrs={
                "class": "primey-input",
                "placeholder": "05xxxxxxxx"
            }),

            # ===============================
            # 📌 القسم الثاني — الهوية والسجل
            # ===============================
            "commercial_number": forms.TextInput(attrs={
                "class": "primey-input",
                "placeholder": "رقم السجل التجاري"
            }),

            "vat_number": forms.TextInput(attrs={
                "class": "primey-input",
                "placeholder": "الرقم الضريبي"
            }),

            "logo": forms.ClearableFileInput(attrs={
                "class": "primey-input",
            }),

            # ===============================
            # 📌 القسم الثالث — العنوان الوطني
            # ===============================
            "building_number": forms.TextInput(attrs={
                "class": "primey-input",
                "placeholder": "رقم المبنى"
            }),

            "street": forms.TextInput(attrs={
                "class": "primey-input",
                "placeholder": "اسم الشارع"
            }),

            "district": forms.TextInput(attrs={
                "class": "primey-input",
                "placeholder": "الحي"
            }),

            "city": forms.TextInput(attrs={
                "class": "primey-input",
                "placeholder": "المدينة"
            }),

            "postal_code": forms.TextInput(attrs={
                "class": "primey-input",
                "placeholder": "الرمز البريدي (5 أرقام)"
            }),

            "short_address": forms.TextInput(attrs={
                "class": "primey-input",
                "placeholder": "عنوان مختصر"
            }),
        }

    # ==================================================================
    # ✔️ Validations — Ultra Pro V4
    # ==================================================================
    def clean_postal_code(self):
        value = self.cleaned_data.get("postal_code")
        if value and (not value.isdigit() or len(value) != 5):
            raise forms.ValidationError("❌ الرمز البريدي يجب أن يكون 5 أرقام.")
        return value

    def clean_building_number(self):
        value = self.cleaned_data.get("building_number")
        if value and not value.isdigit():
            raise forms.ValidationError("❌ رقم المبنى يجب أن يكون أرقام فقط.")
        return value
