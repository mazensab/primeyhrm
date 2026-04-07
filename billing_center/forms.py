# 📂 الملف: billing_center/forms.py
# 🧭 نماذج الإدخال الخاصة بنظام التسجيل في Mham Cloud

from django import forms
from .models import Company, AccountProfile, SubscriptionPlan


# 🧾 نموذج تسجيل الشركة والمستخدم
class CompanyRegistrationForm(forms.Form):
    # 🏢 بيانات الشركة
    company_name = forms.CharField(label="اسم الشركة", max_length=150)
    cr_number = forms.CharField(label="رقم السجل التجاري", max_length=50)
    email = forms.EmailField(label="البريد الإلكتروني للشركة")
    phone = forms.CharField(label="رقم التواصل", max_length=20)
    address = forms.CharField(label="العنوان", max_length=255, required=False)

    # 👤 بيانات المستخدم (المدير)
    username = forms.CharField(label="اسم المستخدم", max_length=150)
    password = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="تأكيد كلمة المرور", widget=forms.PasswordInput)
    user_email = forms.EmailField(label="البريد الإلكتروني للمدير")

    # 💳 اختيار الباقة
    plan = forms.ModelChoiceField(
        label="اختر الباقة",
        queryset=SubscriptionPlan.objects.filter(is_active=True),
        empty_label="اختر باقتك",
    )

    def clean(self):
        """🔒 التحقق من صحة البيانات"""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password != confirm:
            raise forms.ValidationError("كلمتا المرور غير متطابقتان ❌")

        return cleaned_data
