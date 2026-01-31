from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from company_manager.models import Company
from employee_center.models import Employee

User = get_user_model()

# ================================================================
# 📌 1) PerformanceTemplate — قالب التقييم الأساسي
# ================================================================
class PerformanceTemplate(models.Model):
    PERIOD_CHOICES = [
        ("YEARLY", "تقييم سنوي"),
        ("QUARTERLY", "تقييم ربع سنوي"),
        ("MONTHLY", "تقييم شهري"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="performance_templates",
        verbose_name="الشركة"
    )

    name = models.CharField(
        max_length=255,
        verbose_name="اسم القالب"
    )

    period = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        default="YEARLY",
        verbose_name="نوع التقييم"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="الوصف"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخر تحديث"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "قالب تقييم"
        verbose_name_plural = "قوالب التقييم"

    def __str__(self):
        return f"{self.name} — {self.company.name}"


# ================================================================
# 📌 2) PerformanceCategory — فئات التقييم (الانضباط / السلوك ...)
# ================================================================
class PerformanceCategory(models.Model):
    template = models.ForeignKey(
        PerformanceTemplate,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name="القالب"
    )

    name = models.CharField(
        max_length=255,
        verbose_name="اسم الفئة"
    )

    weight = models.PositiveIntegerField(
        default=20,
        verbose_name="الوزن (%)"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "فئة تقييم"
        verbose_name_plural = "فئات التقييم"

    def __str__(self):
        return f"{self.name} ({self.weight}%)"


# ================================================================
# 📌 3) PerformanceItem — أسئلة التقييم داخل كل فئة
# ================================================================
class PerformanceItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ("SCORE", "نقاط"),
        ("TEXT", "نصي"),
    ]

    category = models.ForeignKey(
        PerformanceCategory,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="الفئة"
    )

    question = models.CharField(
        max_length=500,
        verbose_name="السؤال"
    )

    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        default="SCORE",
        verbose_name="نوع السؤال"
    )

    max_score = models.PositiveIntegerField(
        default=5,
        verbose_name="أقصى درجة"
    )

    weight = models.PositiveIntegerField(
        default=10,
        verbose_name="الوزن داخل الفئة"
    )

    class Meta:
        ordering = ["category", "weight"]
        verbose_name = "عنصر تقييم"
        verbose_name_plural = "عناصر التقييم"

    def __str__(self):
        return self.question


# ================================================================
# 📌 4) PerformanceReview — تقييم الموظف (Self + Manager + HR)
# ================================================================
class PerformanceReview(models.Model):
    STATUS_CHOICES = [
        ("SELF_PENDING", "بانتظار تقييم الموظف"),
        ("MANAGER_PENDING", "بانتظار تقييم المدير"),
        ("HR_PENDING", "بانتظار تقييم الموارد البشرية"),
        ("COMPLETED", "مكتمل"),
    ]

    DECISION_CHOICES = [
        ("NORMAL", "استمرار"),
        ("PROMOTION", "ترقية"),
        ("BONUS", "مكافأة"),
        ("WARNING", "إنذار"),
        ("IMPROVEMENT_PLAN", "خطة تطوير"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="performance_reviews",
        verbose_name="الموظف"
    )

    template = models.ForeignKey(
        PerformanceTemplate,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="قالب التقييم"
    )

    period_label = models.CharField(
        max_length=255,
        verbose_name="دورة التقييم (مثال: 2025 Q1)"
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="SELF_PENDING",
        verbose_name="حالة سير العمل"
    )

    self_score = models.FloatField(
        blank=True,
        null=True,
        verbose_name="درجة تقييم الموظف لنفسه"
    )

    manager_score = models.FloatField(
        blank=True,
        null=True,
        verbose_name="درجة تقييم المدير"
    )

    hr_score = models.FloatField(
        blank=True,
        null=True,
        verbose_name="درجة تقييم الموارد البشرية"
    )

    final_score = models.FloatField(
        blank=True,
        null=True,
        verbose_name="النتيجة النهائية"
    )

    final_decision = models.CharField(
        max_length=50,
        choices=DECISION_CHOICES,
        default="NORMAL",
        verbose_name="القرار النهائي"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخر تحديث"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "تقييم أداء"
        verbose_name_plural = "تقييمات الأداء"

    def __str__(self):
        return f"تقييم {self.employee} — {self.period_label}"


# ================================================================
# 📌 5) PerformanceAnswer — إجابات التقييم لكل عنصر
# ================================================================
class PerformanceAnswer(models.Model):
    review = models.ForeignKey(
        PerformanceReview,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="التقييم"
    )

    item = models.ForeignKey(
        PerformanceItem,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="العنصر"
    )

    self_answer = models.TextField(
        blank=True,
        null=True,
        verbose_name="إجابة الموظف"
    )

    manager_answer = models.TextField(
        blank=True,
        null=True,
        verbose_name="إجابة المدير"
    )

    hr_answer = models.TextField(
        blank=True,
        null=True,
        verbose_name="إجابة الموارد البشرية"
    )

    self_score = models.FloatField(
        blank=True,
        null=True,
        verbose_name="درجة الموظف"
    )

    manager_score = models.FloatField(
        blank=True,
        null=True,
        verbose_name="درجة المدير"
    )

    hr_score = models.FloatField(
        blank=True,
        null=True,
        verbose_name="درجة HR"
    )

    class Meta:
        verbose_name = "إجابة تقييم"
        verbose_name_plural = "إجابات التقييم"

    def __str__(self):
        return f"إجابة — {self.review.employee}"


# ================================================================
# 📌 6) PerformanceWorkflowStatus — تتبع Workflow
# ================================================================
class PerformanceWorkflowStatus(models.Model):
    review = models.OneToOneField(
        PerformanceReview,
        on_delete=models.CASCADE,
        related_name="workflow",
        verbose_name="التقييم"
    )

    self_completed = models.BooleanField(default=False)
    manager_completed = models.BooleanField(default=False)
    hr_completed = models.BooleanField(default=False)

    last_update = models.DateTimeField(
        auto_now=True,
        verbose_name="آخر تحديث"
    )

    class Meta:
        verbose_name = "سير العمل"
        verbose_name_plural = "سير العمل للتقييم"

    def __str__(self):
        return f"Workflow — {self.review}"
