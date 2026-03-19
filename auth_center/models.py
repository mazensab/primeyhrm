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
# 👤 User Profile (System User)
# ===============================================================

class UserProfile(models.Model):
    """
    👤 ملف المستخدم الأساسي
    يستخدم لحفظ بيانات الحساب مثل الصورة
    ولا يرتبط بالشركة
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="المستخدم"
    )

    avatar_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="رابط الصورة"
    )

    # ===============================================================
    # 📱 بيانات الاتصال للمستخدم الداخلي
    # ===============================================================
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="رقم الجوال"
    )

    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="رقم واتساب"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


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

    # ===============================================================
    # 🖼 Avatar (Google Drive URL)
    # ===============================================================
    avatar_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="رابط الصورة"
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


# ===============================================================
# 🔐 Active User Session Registry (Ω+)
# ===============================================================
class ActiveUserSession(models.Model):
    """
    🔐 تسجيل الجلسات النشطة داخل النظام

    ✔ يدعم Multi-Login
    ✔ يدعم Session Monitor
    ✔ يدعم Force Logout
    ✔ يدعم Version Sync
    ✔ لا يؤثر على Django Session Engine
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="active_sessions",
        verbose_name="المستخدم",
    )

    session_key = models.CharField(
        max_length=40,
        unique=True,
        verbose_name="Session Key",
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Address",
    )

    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name="User Agent",
    )

    session_version = models.PositiveIntegerField(
        default=1,
        verbose_name="Session Version",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="نشطة",
    )

    last_seen = models.DateTimeField(
        auto_now=True,
        verbose_name="آخر نشاط",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء",
    )

    def __str__(self):
        return f"{self.user.username} — {self.session_key}"

    class Meta:
        verbose_name = "جلسة مستخدم نشطة"
        verbose_name_plural = "الجلسات النشطة"
        ordering = ["-last_seen"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["session_key"]),
            models.Index(fields=["is_active"]),
        ]


# ===============================================================
# 🔁 Auto Create EmployeeProfile
# ===============================================================
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    """
    إنشاء EmployeeProfile فقط إذا كان المستخدم موظف داخل شركة
    """

    if not created:
        return

    # إذا لم يكن للمستخدم شركة لا تنشئ EmployeeProfile
    if not hasattr(instance, "companyuser"):
        return

    EmployeeProfile.objects.create(
        user=instance,
        company=instance.companyuser.company,
        position="User"
    )