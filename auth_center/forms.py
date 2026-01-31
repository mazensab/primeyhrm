# 📂 الملف: auth_center/forms.py
# 🧭 نموذج تعديل الملف الشخصي للمستخدم
# 🚀 المرحلة 6.2 من Primey HRM Cloud V2
# ✅ يسمح بتعديل الاسم – البريد الإلكتروني – رقم الجوال

from django import forms
from billing_center.models import AccountProfile


class ProfileUpdateForm(forms.ModelForm):
    """🧾 نموذج تعديل بيانات المستخدم الأساسية"""
    
    class Meta:
        model = AccountProfile
        fields = ["first_name", "last_name", "email", "phone"]
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control text-center",
                "placeholder": "الاسم الأول",
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control text-center",
                "placeholder": "اسم العائلة",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control text-center",
                "placeholder": "البريد الإلكتروني",
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control text-center",
                "placeholder": "رقم الجوال",
            }),
        }
        labels = {
            "first_name": "الاسم الأول",
            "last_name": "اسم العائلة",
            "email": "البريد الإلكتروني",
            "phone": "رقم الجوال",
        }
