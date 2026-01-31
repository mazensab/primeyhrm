from django.db import models
from django.contrib.auth import get_user_model
from company_manager.models import Company

# ================================================================
# 📝 System Log Model — Audit Trail V1 (Primey HR Cloud)
# ================================================================
# هذا الموديل مسؤول عن تسجيل جميع الأحداث الحساسة داخل النظام
# مثل: (تسجيل الدخول – تعديل بيانات – حذف – مزامنة – أخطاء – صلاحيات)
# ويُعدّ الأساس لبناء Audit Trail احترافي مشابه لـ ERPNext & Odoo.
# ================================================================

User = get_user_model()


class SystemLog(models.Model):
    # ------------------------------------------------------------
    # 🟦 معلومات أساسية عن السجل
    # ------------------------------------------------------------
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="system_logs",
        verbose_name="الشركة"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
        verbose_name="المستخدم المنفّذ"
    )

    module = models.CharField(
        max_length=100,
        verbose_name="الوحدة",
        help_text="مثال: employee_center, payroll_center, biotime_center"
    )

    action = models.CharField(
        max_length=100,
        verbose_name="الإجراء",
        help_text="مثال: create, update, delete, sync, login"
    )

    # ------------------------------------------------------------
    # 🟧 مستوى الخطورة
    # ------------------------------------------------------------
    SEVERITY_CHOICES = [
        ("info", "معلومة"),
        ("warning", "تحذير"),
        ("error", "خطأ"),
        ("critical", "حرج"),
    ]

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default="info",
        verbose_name="مستوى الخطورة"
    )

    # ------------------------------------------------------------
    # 🟨 تفاصيل السجل
    # ------------------------------------------------------------
    message = models.TextField(
        verbose_name="الرسالة",
        help_text="وصف الحدث الذي حصل داخل النظام"
    )

    extra_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="بيانات إضافية",
        help_text="تخزين أي تفاصيل إضافية (مثل قبل/بعد التعديل)"
    )

    # ------------------------------------------------------------
    # 🟩 الوقت
    # ------------------------------------------------------------
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="وقت الإنشاء"
    )

    # ------------------------------------------------------------
    # 🟥 إعدادات إضافية
    # ------------------------------------------------------------
    class Meta:
        verbose_name = "سجل نظام"
        verbose_name_plural = "سجلات النظام"
        ordering = ["-created_at"]  # ترتيب تنازلي

    def __str__(self):
        return f"[{self.created_at}] {self.module} → {self.action}"
