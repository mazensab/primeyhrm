# ============================================================
# 📂 الملف: biotime_center/forms.py
# 🧾 نماذج إدخال بيانات إعدادات Biotime — الإصدار V7.1 بعد التصحيح
# ------------------------------------------------------------
# ✔ متوافق تمامًا مع نموذج BiotimeSetting (دون api_key)
# ✔ يدعم تسجيل الدخول (company + email + password)
# ✔ تصميم جاهز للقالب (Glass White 2026)
# Developed by Mazen — Mham Cloud 2026
# ============================================================

from django import forms
from .models import BiotimeSetting


class BiotimeSettingForm(forms.ModelForm):
    """
    🧠 النموذج الرسمي لإعدادات الاتصال بخادم Biotime Cloud V7.1
    الحقول المدعومة:
      - server_url
      - company
      - email
      - password
    """

    class Meta:
        model = BiotimeSetting
        fields = [
            "server_url",
            "company",
            "email",
            "password",
        ]

        widgets = {
            "server_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://biotime-server/api",
            }),

            "company": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "اسم الشركة المسجل في Biotime",
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "البريد الإلكتروني لنظام Biotime",
            }),

            "password": forms.PasswordInput(attrs={
                "class": "form-control",
                "placeholder": "كلمة مرور الحساب",
            }),
        }

        labels = {
            "server_url": "رابط خادم Biotime",
            "company": "اسم الشركة",
            "email": "البريد الإلكتروني",
            "password": "كلمة المرور",
        }
