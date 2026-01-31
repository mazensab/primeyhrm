from django.db import models
from django.conf import settings
from django.utils import timezone

# ================================================================
# 🏢 1) Company Model — بيانات الشركة الأساسية
# ================================================================

class Company(models.Model):

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_companies",
        verbose_name="مالك الشركة",
    )

    name = models.CharField(max_length=255, verbose_name="اسم الشركة")

    commercial_number = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="رقم السجل التجاري"
    )

    vat_number = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="الرقم الضريبي"
    )

    phone = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="رقم الهاتف"
    )

    email = models.EmailField(
        blank=True, null=True, verbose_name="البريد الإلكتروني"
    )

    # 🏢 العنوان الوطني
    building_number = models.CharField(max_length=20, blank=True, null=True)
    street = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    short_address = models.CharField(max_length=255, blank=True, null=True)

    logo = models.ImageField(
        upload_to="company_logos/", blank=True, null=True
    )

    is_active = models.BooleanField(default=True)

    # ============================================================
    # 🕒 (NEW) Default Work Schedule (Company Level)
    # ============================================================
    default_work_schedule = models.ForeignKey(
        "attendance_center.WorkSchedule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="companies_as_default",
        verbose_name="جدول الدوام الافتراضي",
        help_text="يُستخدم كجدول الدوام الافتراضي للشركة في حال عدم وجود تخصيص أدق",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "شركة"
        verbose_name_plural = "الشركات"

    def __str__(self):
        return self.name


# ================================================================
# 🏬 2) CompanyBranch — الفروع
# ================================================================
class CompanyBranch(models.Model):

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="branches"
    )

    # ============================================================
    # 🔗 Biotime Mapping (SAFE)
    # ============================================================
    biotime_code = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Biotime Code",
        help_text="المعرّف الخارجي للفرع داخل نظام Biotime",
    )

    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "فرع"
        verbose_name_plural = "الفروع"

    def __str__(self):
        return f"{self.name} — {self.company.name}"


# ================================================================
# 🏢 3) CompanyOffice — المكاتب
# ================================================================
class CompanyOffice(models.Model):

    branch = models.ForeignKey(
        CompanyBranch, on_delete=models.CASCADE, related_name="offices"
    )

    name = models.CharField(max_length=255)
    floor = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "مكتب"
        verbose_name_plural = "المكاتب"

    def __str__(self):
        return f"{self.name} — {self.branch.name}"


# ================================================================
# 🔐 4) CompanyRole — الأدوار
# ================================================================
class CompanyRole(models.Model):

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="roles"
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    permissions = models.JSONField(default=dict)

    is_system_role = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "دور"
        verbose_name_plural = "الأدوار"

    def __str__(self):
        return f"{self.name} — {self.company.name}"


# ================================================================
# 👥 5) CompanyUser — ربط المستخدمين بالشركة
# ================================================================
class CompanyUser(models.Model):

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="company_users"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company_memberships",
    )

    role = models.CharField(max_length=255, blank=True, null=True)

    roles = models.ManyToManyField(
        CompanyRole, related_name="company_users", blank=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "مستخدم شركة"
        verbose_name_plural = "مستخدمو الشركات"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "company"],
                name="unique_company_user",
            )
        ]

    def __str__(self):
        return f"{self.user} — {self.company.name}"


# ================================================================
# 📄 6) CompanyDocument — الوثائق
# ================================================================
class CompanyDocument(models.Model):

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="documents"
    )

    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=255)
    document_number = models.CharField(max_length=255, blank=True, null=True)

    file = models.FileField(upload_to="company_documents/")

    issue_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)

    status = models.CharField(max_length=50, default="ACTIVE")

    extracted_text = models.TextField(blank=True, null=True)
    ai_metadata = models.JSONField(default=dict, blank=True, null=True)

    version = models.PositiveIntegerField(default=1)
    previous_versions = models.JSONField(default=list, blank=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "وثيقة"
        verbose_name_plural = "وثائق الشركة"

    def __str__(self):
        return f"{self.title} — {self.company.name}"


# ================================================================
# 🏢 7) CompanyDepartment
# ================================================================
class CompanyDepartment(models.Model):

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="departments"
    )

    # ============================================================
    # 🕒 Default Work Schedule (Department Level)
    # ============================================================
    default_work_schedule = models.ForeignKey(
        "attendance_center.WorkSchedule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="departments_as_default",
        verbose_name="جدول الدوام الافتراضي للقسم",
        help_text="يُستخدم كجدول دوام افتراضي لموظفي هذا القسم عند عدم وجود تخصيص للموظف",
    )

    # ============================================================
    # 🔗 Biotime Mapping (SAFE)
    # ============================================================
    biotime_code = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Biotime Code",
        help_text="المعرّف الخارجي للقسم داخل نظام Biotime",
    )

    biotime_area_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Biotime Area ID",
        help_text="المعرّف المقابل للقسم داخل Biotime (Area)",
    )

    biotime_department_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Biotime Department ID",
        help_text="المعرّف المقابل للقسم داخل Biotime (Department)",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "قسم"
        verbose_name_plural = "الأقسام"

    def __str__(self):
        return f"{self.name} — {self.company.name}"


# ================================================================
# 🧑‍💼 8) JobTitle
# ================================================================
class JobTitle(models.Model):

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="job_titles"
    )

    # ============================================================
    # 🔗 Biotime Mapping (SAFE)
    # ============================================================
    biotime_code = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Biotime Code",
        help_text="المعرّف الخارجي للمسمى الوظيفي داخل نظام Biotime",
    )

    biotime_position_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Biotime Position ID",
        help_text="المعرّف المقابل للمسمى الوظيفي داخل Biotime (Position)",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "مسمى وظيفي"
        verbose_name_plural = "المسميات الوظيفية"

    def __str__(self):
        return f"{self.name} — {self.company.name}"


# ================================================================
# 🏢 9) CompanyProfile
# ================================================================
class CompanyProfile(models.Model):

    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name="profile"
    )

    timezone = models.CharField(max_length=50, default="Asia/Riyadh")
    language = models.CharField(max_length=10, default="ar")
    currency = models.CharField(max_length=10, default="SAR")

    logo = models.ImageField(
        upload_to="company_logos/", blank=True, null=True
    )

    theme = models.CharField(max_length=20, default="light")

    features = models.JSONField(default=list, blank=True)
    settings = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def has_feature(self, feature_code):
        return feature_code in (self.features or [])

    def __str__(self):
        return f"Profile for {self.company.name}"
