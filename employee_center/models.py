# ===============================================================
# 📂 employee_center/models.py
# 🧭 Employee Center — Models (FIXED + COMPLETED | OPTION A LOCKED)
# ===============================================================

from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid

from company_manager.models import (
    Company,
    CompanyDepartment,
    JobTitle,
    CompanyBranch,     # ✅ NEW — لدعم Multi-Branch
)


# ===============================================================
# 👤 (1) Employee — الموظف الأساسي
# ===============================================================
class Employee(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="employees",
        verbose_name="الشركة"
    )

    # حساب المستخدم (إجباري — معمارية Option A)
    # Employee لا يمكن أن يوجد بدون User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hr_employee",
        verbose_name="حساب المستخدم"
    )

    # ============================================================
    # 🕒 Default Work Schedule (Employee Level)
    # أعلى أولوية في التسلسل: Employee → Department → Company
    # ============================================================
    default_work_schedule = models.ForeignKey(
        "attendance_center.WorkSchedule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees_as_default",
        verbose_name="جدول الدوام الخاص بالموظف",
        help_text="في حال تحديده يتم اعتماده مباشرة، وإلا يتم الرجوع لجدول القسم ثم الشركة",
    )

    # ============================================================
    # 🔗 ربط الموظف مع Biotime (الكود فقط)
    # ============================================================
    biotime_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="كود الموظف في Biotime",
        help_text="Employee code in Biotime / biometric devices"
    )

    # ============================================================
    # 🔗 الربط الفعلي مع سجل Biotime (Phase C3)
    # ============================================================

    full_name = models.CharField(max_length=255, verbose_name="الاسم الكامل")
    arabic_name = models.CharField(max_length=255, null=True, blank=True)

    national_id = models.CharField(max_length=20, verbose_name="رقم الهوية/الإقامة")
    passport_number = models.CharField(max_length=20, null=True, blank=True)
        # ============================================================
    # 📌 بيانات الهوية والإقامة
    # ============================================================
    national_id_issue_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاريخ إصدار الهوية"
    )

    national_id_expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاريخ انتهاء الهوية"
    )

    passport_issue_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاريخ إصدار الجواز"
    )

    passport_expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاريخ انتهاء الجواز"
    )

    employee_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="رقم الموظف الداخلي"
    )

    gosi_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="رقم التأمينات الاجتماعية"
    )

    # ============================================================
    # 🖼 صورة الموظف (Google Drive URL)
    # ============================================================
    photo_url = models.URLField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="رابط صورة الموظف",
        help_text="Google Drive public image URL"
    )

    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)

    mobile_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="رقم الجوال"

    )

    gender = models.CharField(
        max_length=10,
        choices=[("male", "ذكر"), ("female", "أنثى")],
        default="male",
    )

    EMPLOYMENT_STATUS = [
        ("active", "نشط"),
        ("probation", "فترة تجريبية"),
        ("on_leave", "في إجازة"),
        ("resigned", "مستقيل"),
        ("terminated", "تم إنهاء الخدمة"),
    ]
    status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS,
        default="active",
    )

    # ============================================================
    # 🏢 القسم (يبقى كما هو — لا تغيير)
    # ============================================================
    department = models.ForeignKey(
        CompanyDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="department_employees",
    )

    # ============================================================
    # 🏢 الفروع — Multi-Branch (NEW ✅)
    # ============================================================
    branches = models.ManyToManyField(
        CompanyBranch,
        related_name="employees",
        blank=True,
        verbose_name="الفروع المرتبط بها الموظف",
        help_text="يمكن ربط الموظف بأكثر من فرع (Multi-Branch Support)",
    )

    # ============================================================
    # 🧩 المسمى الوظيفي
    # ============================================================
    job_title = models.ForeignKey(
        JobTitle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jobtitle_employees",
    )

    employment_type = models.CharField(
        max_length=20,
        choices=[
            ("full_time", "دوام كامل"),
            ("part_time", "دوام جزئي"),
            ("contract", "عقد مؤقت"),
            ("seasonal", "موسمي"),
        ],
        default="full_time",
    )

    join_date = models.DateField(default=timezone.now)
    work_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاريخ المباشرة",
        help_text="يبدأ احتساب الحضور من هذا التاريخ"

    )

    probation_end_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "موظف"
        verbose_name_plural = "الموظفون"

    def __str__(self):
        return self.full_name


# ===============================================================
# 🧩 (2) EmploymentInfo
# ===============================================================
class EmploymentInfo(models.Model):
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
         related_name="employment_info"
    )

    job_grade = models.CharField(max_length=50, null=True, blank=True)
    job_level = models.CharField(max_length=50, null=True, blank=True)
    job_category = models.CharField(max_length=100, null=True, blank=True)

    direct_manager = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manager_of",
    )

    work_location = models.CharField(max_length=200, null=True, blank=True)
    branch_name = models.CharField(max_length=200, null=True, blank=True)

    shift_type = models.CharField(
        max_length=50,
        choices=[
            ("fixed", "دوام ثابت"),
            ("shift", "شفتات"),
            ("remote", "عمل عن بعد"),
            ("hybrid", "مختلط"),
        ],
        default="fixed",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# ===============================================================
# 💰 (3) FinancialInfo
# ===============================================================
class FinancialInfo(models.Model):
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="financial_info"
    )

    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    housing_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    food_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_gosi_enabled = models.BooleanField(default=True)
    is_tax_enabled = models.BooleanField(default=False)

    bank_name = models.CharField(max_length=100, null=True, blank=True)
    iban = models.CharField(max_length=30, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# ===============================================================
# 📄 (4) Contract
# ===============================================================
class Contract(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="contracts"
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="contracts"
    )

    contract_number = models.CharField(max_length=100)

    CONTRACT_TYPES = [
        ("fixed", "محدد المدة"),
        ("unlimited", "غير محدد"),
        ("temporary", "مؤقت"),
        ("seasonal", "موسمي"),
        ("part_time", "دوام جزئي"),
    ]
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    probation_period_months = models.PositiveIntegerField(default=3)

    salary = models.DecimalField(max_digits=10, decimal_places=2)
    housing = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)
    is_renewable = models.BooleanField(default=True)

    verify_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.employee.full_name} — {self.contract_number}"


# ===============================================================
# 📄 (5) EmployeeDocument
# ===============================================================
class EmployeeDocument(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=100)

    file = models.FileField(upload_to="employee_documents/%Y/%m/")
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=50, default="ACTIVE")
    notes = models.TextField(null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.employee.work_start_date and self.employee.join_date:
            if self.employee.work_start_date < self.employee.join_date:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    "تاريخ المباشرة لا يمكن أن يكون قبل تاريخ التعيين."
                )
    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.title} — {self.employee.full_name}"


# ===============================================================
# ⚙️ (6) EmploymentHistory
# ===============================================================
class EmploymentHistory(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="employment_history"
    )

    action_type = models.CharField(
        max_length=50,
        choices=[
            ("hire", "تعيين"),
            ("promotion", "ترقية"),
            ("transfer", "نقل"),
            ("salary_change", "تعديل راتب"),
            ("termination", "إنهاء خدمة"),
            ("resignation", "استقالة"),
            ("eosb_auto", "مكافأة نهاية الخدمة تلقائيًا"),
            ("eosb_created", "إنشاء مكافأة نهاية الخدمة"),
        ]
    )

    description = models.TextField(null=True, blank=True)
    effective_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)


# ===============================================================
# 🚪 (7) ResignationRecord
# ===============================================================
class ResignationRecord(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="resignation_records"
    )
    resignation_date = models.DateField()
    last_working_day = models.DateField()
    reason = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-resignation_date"]
        verbose_name = "سجل استقالة"
        verbose_name_plural = "سجلات الاستقالة"

    def __str__(self):
        return f"{self.employee.full_name} — {self.resignation_date}"


# ===============================================================
# ❌ (8) TerminationRecord — إنهاء الخدمة
# ===============================================================
class TerminationRecord(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="termination_records",
        verbose_name="الموظف"
    )

    termination_date = models.DateField(verbose_name="تاريخ إنهاء الخدمة")
    reason = models.TextField(null=True, blank=True, verbose_name="سبب الإنهاء")
    notes = models.TextField(null=True, blank=True, verbose_name="ملاحظات إدارية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        ordering = ["-termination_date"]
        verbose_name = "سجل إنهاء خدمة"
        verbose_name_plural = "سجلات إنهاء الخدمة"

    def __str__(self):
        return f"{self.employee.full_name} — {self.termination_date}"


# ===============================================================
# 🧮 (9) EoSBRecord — مكافأة نهاية الخدمة
# ===============================================================
class EoSBRecord(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="eosb_records",
        verbose_name="الموظف"
    )

    termination = models.ForeignKey(
        TerminationRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eosb_records",
        verbose_name="سجل الإنهاء"
    )

    years_of_service = models.DecimalField(max_digits=6, decimal_places=2)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    active_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    calculation_method = models.CharField(
        max_length=50,
        default="auto",
        choices=[
            ("auto", "حساب تلقائي"),
            ("manual", "حساب يدوي"),
        ],
        verbose_name="طريقة الحساب"
    )

    notes = models.TextField(null=True, blank=True, verbose_name="ملاحظات")
    calculation_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-calculation_date"]
        verbose_name = "مكافأة نهاية الخدمة"
        verbose_name_plural = "مكافآت نهاية الخدمة"

    def __str__(self):
        return f"{self.employee.full_name} — {self.total_amount} SAR"


# ===============================================================
# 🔄 (10) SyncLog — سجلات المزامنة
# ===============================================================
class SyncLog(models.Model):
    SYNC_TYPES = [
        ("employees", "Employees"),
        ("departments", "Departments"),
        ("job_titles", "Job Titles"),
    ]

    STATUS_CHOICES = [
        ("success", "Success"),
        ("failed", "Failed"),
        ("partial", "Partial"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="employee_sync_logs",
        verbose_name="الشركة"
    )

    sync_type = models.CharField(
        max_length=30,
        choices=SYNC_TYPES,
        verbose_name="نوع المزامنة"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="success",
        verbose_name="الحالة"
    )

    total_records = models.PositiveIntegerField(default=0, verbose_name="إجمالي السجلات")
    success_count = models.PositiveIntegerField(default=0, verbose_name="عدد الناجح")
    failed_count = models.PositiveIntegerField(default=0, verbose_name="عدد الفاشل")

    error_message = models.TextField(null=True, blank=True, verbose_name="رسالة الخطأ")

    started_at = models.DateTimeField(default=timezone.now, verbose_name="بدأت في")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="انتهت في")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "سجل مزامنة"
        verbose_name_plural = "سجلات المزامنة"

    def __str__(self):
        return f"{self.company} — {self.sync_type} — {self.status}"
