# =====================================================================
# 💳 PaymentTransaction V2 Ultra Clean
# Primey HR Cloud — Unified Payment Tracking Layer
# =====================================================================

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from company_manager.models import Company

User = get_user_model()


# =====================================================================
# 🧩 1) Payment Gateway Metadata
# (تخزين بيانات العملية من مزود الدفع — stc pay / mada / tap / tamara)
# =====================================================================
class PaymentGatewayData(models.Model):
    provider = models.CharField(max_length=100, verbose_name="مزود الخدمة")
    raw_request = models.JSONField(null=True, blank=True, verbose_name="البيانات الأصلية للطلب")
    raw_response = models.JSONField(null=True, blank=True, verbose_name="البيانات الأصلية للاستجابة")
    reference_id = models.CharField(max_length=255, null=True, blank=True, verbose_name="معرّف العملية لدى المزود")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider} — {self.reference_id}"


# =====================================================================
# 💳 2) PaymentTransaction — السجل الرسمي لكل عملية دفع
# لا علاقة له بالفواتير مباشرة، مناسب لتقارير ZATCA وعمليات التدقيق
# =====================================================================
class PaymentTransaction(models.Model):

    STATUS_CHOICES = [
        ("success", "ناجحة"),
        ("failed", "فاشلة"),
        ("pending", "بانتظار"),
        ("refunded", "مسترجعة"),
    ]

    PAYMENT_METHODS = [
        ("card", "بطاقة"),
        ("bank", "حوالة بنكية"),
        ("stc", "STC Pay"),
        ("apple", "Apple Pay"),
        ("cash", "كاش"),
    ]

    # ---------------------------------------------------------------
    # 🔗 الشركة
    # ---------------------------------------------------------------
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="payment_transactions",
        verbose_name="الشركة"
    )

    # ---------------------------------------------------------------
    # 💵 بيانات الدفع الأساسية
    # ---------------------------------------------------------------
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    transaction_id = models.CharField(max_length=255, null=True, blank=True, verbose_name="معرّف العملية")
    description = models.CharField(max_length=255, null=True, blank=True, verbose_name="الوصف")

    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ المعالجة")

    # ---------------------------------------------------------------
    # 🧩 بيانات مزود الدفع (اختياري)
    # ---------------------------------------------------------------
    gateway = models.ForeignKey(
        PaymentGatewayData,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="بيانات مزود الدفع"
    )

    # ---------------------------------------------------------------
    # 👤 من نفّذ العملية (اختياري)
    # ---------------------------------------------------------------
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="أنشئ بواسطة"
    )

    # ---------------------------------------------------------------
    # 🔍 خواص مساعدة
    # ---------------------------------------------------------------
    @property
    def is_success(self):
        return self.status == "success"

    @property
    def is_refunded(self):
        return self.status == "refunded"

    def mark_processed(self):
        self.processed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"TXN {self.id} — {self.amount} ({self.status})"


# =====================================================================
# 📝 3) PaymentTransactionLog — سجل عمليات الدفع
# (للمراجعة والتدقيق)
# =====================================================================
class PaymentTransactionLog(models.Model):

    ACTIONS = [
        ("create", "إنشاء عملية"),
        ("update_status", "تحديث الحالة"),
        ("refund", "استرجاع"),
        ("gateway_callback", "استقبال رد من مزود الدفع"),
    ]

    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="عملية الدفع"
    )

    action = models.CharField(max_length=50, choices=ACTIONS)
    message = models.TextField(verbose_name="تفاصيل")

    created_at = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="المنفذ"
    )

    def __str__(self):
        return f"Log({self.transaction.id}) — {self.action}"
