# =====================================================================
# 📦 Billing Center — Models V10.1 Ultra Stable (PUBLIC FLOW PATCHED 🔒)
# Primey HR Cloud — Subscription + Invoicing + Unified Payments
# =====================================================================

from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

from company_manager.models import Company


# =====================================================================
# 💳 1) SubscriptionPlan
# =====================================================================
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)

    max_employees = models.PositiveIntegerField(default=10)
    max_branches = models.PositiveIntegerField(default=1)
    max_companies = models.PositiveIntegerField(default=1)

    apps = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# =====================================================================
# 💸 2) Discount
# =====================================================================
class Discount(models.Model):

    DISCOUNT_TYPES = [
        ("percentage", "نسبة مئوية"),
        ("fixed", "قيمة ثابتة"),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    start_date = models.DateField()
    end_date = models.DateField()

    is_active = models.BooleanField(default=True)

    applies_to_all_plans = models.BooleanField(default=False)
    allowed_plans = models.ManyToManyField(
        SubscriptionPlan,
        blank=True,
        related_name="allowed_discounts",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


# =====================================================================
# 🧾 3) CompanySubscription
# =====================================================================
class CompanySubscription(models.Model):

    STATUS_CHOICES = [
        ("ACTIVE", "نشط"),
        ("EXPIRED", "منتهي"),
        ("SUSPENDED", "موقوف"),
        ("PENDING", "قيد التفعيل"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
    )

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    auto_renew = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    apps_snapshot = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------------------------------------------------
    # Database Safety Constraint
    # يمنع وجود أكثر من اشتراك ACTIVE لنفس الشركة
    # ------------------------------------------------
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company"],
                condition=models.Q(status="ACTIVE"),
                name="unique_active_subscription_per_company",
            )
        ]

    def is_active(self):
        return self.status == "ACTIVE"

    def __str__(self):
        return self.company.name


# =====================================================================
# 🧾 4) Invoice
# =====================================================================
class Invoice(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "قيد الانتظار"),
        ("PAID", "مدفوعة"),
        ("FAILED", "فشل"),
        ("CANCELLED", "ملغاة"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="invoices",
    )

    subscription = models.ForeignKey(
        CompanySubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(blank=True, null=True)

    # -----------------------------------------------------------------
    # Legacy / Existing billing fields
    # -----------------------------------------------------------------
    subtotal_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    discount_code = models.CharField(max_length=50, null=True, blank=True)
    discount_type = models.CharField(
        max_length=20,
        choices=[("percentage", "نسبة"), ("fixed", "ثابت")],
        null=True,
        blank=True,
    )
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    total_after_discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # -----------------------------------------------------------------
    # New fields required by onboarding/payment flow
    # confirm_payment.py currently writes subtotal + vat مباشرة
    # -----------------------------------------------------------------
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    vat = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    subscription_snapshot = models.JSONField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    # ------------------------------------------------
    # Billing Reason (سبب الفاتورة)
    # ------------------------------------------------
    BILLING_REASONS = [
        ("NEW_SUBSCRIPTION", "اشتراك جديد"),
        ("RENEWAL", "تجديد الاشتراك"),
        ("UPGRADE", "ترقية الباقة"),
        ("DOWNGRADE", "تخفيض الباقة"),
        ("ADDON", "إضافة خدمة"),
    ]

    billing_reason = models.CharField(
        max_length=30,
        choices=BILLING_REASONS,
        default="NEW_SUBSCRIPTION",
    )

    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)

    pdf_file = models.FileField(upload_to="invoices/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def approve(self):
        if not self.is_approved:
            self.is_approved = True
            self.approved_at = timezone.now()
            self.save(update_fields=["is_approved", "approved_at"])

    def __str__(self):
        return f"Invoice #{self.invoice_number}"


# =====================================================================
# 💰 5) Payment
# =====================================================================
class Payment(models.Model):

    PAYMENT_METHODS = [
        ("BANK_TRANSFER", "حوالة"),
        ("CREDIT_CARD", "بطاقة"),
        ("APPLE_PAY", "Apple Pay"),
        ("STC_PAY", "STC Pay"),
        ("TAMARA", "Tamara"),
        ("CASH", "كاش"),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments",
        db_index=True,
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, choices=PAYMENT_METHODS)

    reference_number = models.CharField(max_length=255, blank=True, null=True)
    paid_at = models.DateTimeField(default=timezone.now)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.amount} — {self.method}"


# =====================================================================
# 💳 6) PaymentTransaction
# =====================================================================
class PaymentTransaction(models.Model):

    STATUS_CHOICES = [
        ("pending", "بانتظار"),
        ("success", "ناجحة"),
        ("failed", "فاشلة"),
        ("cancelled", "ملغاة"),
    ]

    PAYMENT_METHODS = [
        ("card", "بطاقة"),
        ("bank", "حوالة"),
        ("stc", "STC Pay"),
        ("apple", "Apple Pay"),
        ("tamara", "Tamara"),
        ("cash", "كاش"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_transactions",
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_transactions",
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def mark_success(self):
        self.status = "success"
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at"])

    def mark_failed(self):
        self.status = "failed"
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at"])

    def __str__(self):
        return f"TXN #{self.id} — {self.amount}"


# =====================================================================
# 🧾 7) CompanyOnboardingTransaction — Draft Only
# =====================================================================
class CompanyOnboardingTransaction(models.Model):

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("CONFIRMED", "Confirmed"),
        ("PENDING_PAYMENT", "بانتظار الدفع"),
        ("PAID", "مدفوعة"),
        ("CANCELLED", "ملغاة"),
    ]

    # -----------------------------------------------------------------
    # مهم جدًا:
    # owner أصبح اختياريًا لدعم Public Registration Flow
    # لأن التسجيل الخارجي قد يتم بدون مستخدم Logged-In
    # -----------------------------------------------------------------
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboarding_transactions",
    )

    # -------------------------------
    # 🏢 Company Snapshot
    # -------------------------------
    company_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True)
    commercial_number = models.CharField(max_length=50, blank=True)
    tax_number = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    national_address = models.JSONField(default=dict, blank=True)

    # -------------------------------
    # 👤 Admin Snapshot (PATCHED ✅)
    # -------------------------------
    admin_username = models.CharField(
        max_length=150,
        db_index=True,
        help_text="Username الحقيقي للمسؤول",
    )

    admin_name = models.CharField(max_length=255)
    admin_email = models.EmailField()
    admin_password = models.CharField(max_length=255)

    # -------------------------------
    # 📦 Plan Snapshot
    # -------------------------------
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
    )

    duration = models.CharField(
        max_length=10,
        choices=[("monthly", "شهري"), ("yearly", "سنوي")],
    )

    start_date = models.DateField()
    end_date = models.DateField()

    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    PAYMENT_METHOD_CHOICES = [
        ("BANK_TRANSFER", "حوالة"),
        ("CREDIT_CARD", "بطاقة"),
        ("APPLE_PAY", "Apple Pay"),
        ("STC_PAY", "STC Pay"),
        ("TAMARA", "Tamara"),
    ]

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        null=True,
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Onboarding #{self.id} — {self.company_name}"


# =====================================================================
# 👤 8) AccountSubscription
# =====================================================================
class AccountSubscription(models.Model):

    STATUS_CHOICES = [
        ("ACTIVE", "نشط"),
        ("EXPIRED", "منتهي"),
        ("SUSPENDED", "موقوف"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_subscriptions",
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
    )

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_active(self):
        return self.status == "ACTIVE"

    def __str__(self):
        return f"{self.owner} — {self.plan.name}"