# =====================================================================
# 📦 Billing Center — Models V11.0 Product-Aware Foundation
# Mham Cloud — Subscription + Invoicing + Unified Payments
# =====================================================================

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from company_manager.models import Company


# =====================================================================
# 🧩 0) Product
# =====================================================================
class Product(models.Model):
    """
    المنتج الرئيسي داخل المنصة
    أمثلة:
    - HR
    - ACCOUNTING
    - SALES
    """

    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.name} ({self.code})"


# =====================================================================
# 💳 1) SubscriptionPlan
# =====================================================================
class SubscriptionPlan(models.Model):
    """
    الباقة التجارية.
    في المرحلة الانتقالية:
    - product قابل لأن يكون فارغًا مؤقتًا حتى تكتمل الـ migrations
    - apps تبقى كما هي للحفاظ على التوافق مع النظام الحالي
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="plans",
    )

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

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["product", "is_active"]),
        ]

    def __str__(self):
        if self.product_id:
            return f"{self.product.code} — {self.name}"
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

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.code


# =====================================================================
# 🧾 3) CompanySubscription
# =====================================================================
class CompanySubscription(models.Model):
    """
    اشتراك الشركة.
    في البنية الجديدة:
    - نفس الشركة يمكن أن تملك عدة اشتراكات
    - لكن اشتراك ACTIVE واحد فقط لكل company + product
    """

    STATUS_CHOICES = [
        ("ACTIVE", "نشط"),
        ("EXPIRED", "منتهي"),
        ("SUSPENDED", "موقوف"),
        ("PENDING", "قيد التفعيل"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="company_subscriptions",
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="company_subscriptions",
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

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            # ------------------------------------------------
            # Database Safety Constraint (NEW)
            # يمنع وجود أكثر من اشتراك ACTIVE لنفس الشركة
            # ولنفس المنتج في نفس الوقت
            # ------------------------------------------------
            models.UniqueConstraint(
                fields=["company", "product"],
                condition=models.Q(status="ACTIVE"),
                name="unique_active_subscription_per_company_product",
            )
        ]
        indexes = [
            models.Index(fields=["company", "product", "status"]),
            models.Index(fields=["company", "status"]),
        ]

    def save(self, *args, **kwargs):
        """
        مزامنة المنتج تلقائيًا من الخطة أثناء المرحلة الانتقالية
        لتقليل احتمالات البيانات الناقصة.
        """
        if self.plan_id and not self.product_id and getattr(self.plan, "product_id", None):
            self.product = self.plan.product
        super().save(*args, **kwargs)

    @property
    def resolved_product(self):
        """
        إرجاع المنتج بشكل آمن:
        - product المباشر أولًا
        - ثم plan.product كـ fallback
        """
        if self.product_id:
            return self.product
        if self.plan_id and getattr(self.plan, "product_id", None):
            return self.plan.product
        return None

    def is_active(self):
        return self.status == "ACTIVE"

    def __str__(self):
        company_name = getattr(self.company, "name", "-")
        product_code = getattr(self.resolved_product, "code", "NO_PRODUCT")
        return f"{company_name} — {product_code}"


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
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    discount_code = models.CharField(max_length=50, null=True, blank=True)
    discount_type = models.CharField(
        max_length=20,
        choices=[("percentage", "نسبة"), ("fixed", "ثابت")],
        null=True,
        blank=True,
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    total_after_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # -----------------------------------------------------------------
    # New fields required by onboarding/payment flow
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
    # Billing Reason
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

    class Meta:
        ordering = ["-issue_date", "-id"]
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["billing_reason"]),
        ]

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

    class Meta:
        ordering = ["-paid_at", "-id"]

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

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["invoice", "status"]),
            models.Index(fields=["transaction_id"]),
        ]

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
    # 👤 Admin Snapshot
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

    class Meta:
        ordering = ["-created_at", "-id"]

    @property
    def resolved_product(self):
        if self.plan_id and getattr(self.plan, "product_id", None):
            return self.plan.product
        return None

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

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["owner", "status"]),
        ]

    @property
    def resolved_product(self):
        if self.plan_id and getattr(self.plan, "product_id", None):
            return self.plan.product
        return None

    def is_active(self):
        return self.status == "ACTIVE"

    def __str__(self):
        return f"{self.owner} — {self.plan.name}"