# ===============================================================
# 📂 الملف: auth_center/models.py
# 🧭 Primey HR Cloud — Auth Center Models
# 🚀 الإصدار الرسمي V12.0 (Glass White — Circular-Free Edition)
# ===============================================================

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

# 🔐 جلب نموذج المستخدم الأساسي ()
User = get_user_model()


# ===============================================================
# 👔 نموذج ملف الموظف (EmployeeProfile)
# ===============================================================
class EmployeeProfile(models.Model):
    """
    👔 ملف الموظف داخل النظام:
    - يرتبط بمستخدم رئيسي ()
    - يتبع لشركة واحدة فقط
    - يحتوي على البيانات الإدارية الأساسية
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employee_profile",
        verbose_name="المستخدم"
    )

    # ⚠️ ملاحظة مهمة:
    # نستخدم "company_manager.Company" كـ string لحل مشكلة الـ Circular Import
    company = models.ForeignKey(
        "company_manager.Company",
        on_delete=models.CASCADE,
        related_name="hrm_employees",
        verbose_name="الشركة"
    )

    position = models.CharField(
        max_length=100,
        verbose_name="المسمى الوظيفي"
    )

    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="القسم"
    )

    hire_date = models.DateField(
        default=timezone.now,
        verbose_name="تاريخ التعيين"
    )

    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="الراتب الشهري"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإضافة"
    )

    def __str__(self):
        return f"{self.user.username} ({self.company.name})"

    class Meta:
        verbose_name = "ملف موظف"
        verbose_name_plural = "ملفات الموظفين"
        ordering = ["-created_at"]
