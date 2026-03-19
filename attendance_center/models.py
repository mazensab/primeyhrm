# ================================================================
# 📂 Attendance Center — Models V20 Ultra Pro
# Full WorkdaySummary Integration + WorkdayEngine V4
# Hybrid Trigger + Reverse Integration + Leave Sync
# ================================================================

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date

# روابط أساسية
from employee_center.models import Employee
from biotime_center.models import BiotimeLog, BiotimeDevice
from company_manager.models import Company   # ✅ تصحيح مرجعية الشركة
# 🆕 Phase H — Holiday Resolver


# ============================================================
# 🗓️ WEEKDAY NORMALIZATION ENGINE (Arabic + English Safe)
# ============================================================

# الشكل القياسي الداخلي (متوافق مع WorkdayEngine)
WEEKDAY_CODES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
WEEKDAY_SET = set(WEEKDAY_CODES)

# جميع المرادفات المقبولة → الكود القياسي
WEEKDAY_ALIASES = {
    # Arabic
    "السبت": "sat",
    "سبت": "sat",
    "الأحد": "sun",
    "احد": "sun",
    "الأحد": "sun",
    "الاثنين": "mon",
    "اثنين": "mon",
    "الإثنين": "mon",
    "الثلاثاء": "tue",
    "ثلاثاء": "tue",
    "الأربعاء": "wed",
    "اربعاء": "wed",
    "الخميس": "thu",
    "خميس": "thu",
    "الجمعة": "fri",
    "جمعة": "fri",

    # English shortcuts
    "mon": "mon",
    "tue": "tue",
    "wed": "wed",
    "thu": "thu",
    "fri": "fri",
    "sat": "sat",
    "sun": "sun",

    # English full
    "monday": "mon",
    "tuesday": "tue",
    "wednesday": "wed",
    "thursday": "thu",
    "friday": "fri",
    "saturday": "sat",
    "sunday": "sun",
}

# الكود القياسي → الاسم العربي للعرض
WEEKDAY_AR_NAMES = {
    "sat": "السبت",
    "sun": "الأحد",
    "mon": "الاثنين",
    "tue": "الثلاثاء",
    "wed": "الأربعاء",
    "thu": "الخميس",
    "fri": "الجمعة",
}


def normalize_weekend_days(raw_value: str) -> str:
    """
    🔒 توحيد weekend_days من عربي أو إنجليزي إلى صيغة قياسية:
        "fri,sat"

    مدخلات صحيحة:
        "الجمعة,السبت"
        "Fri , SAT"
        "Saturday"
        "sat"

    مخرجات:
        "fri,sat"
    """

    if not raw_value:
        return ""

    if not isinstance(raw_value, str):
        raise ValidationError("weekend_days must be a string.")

    parts = [
        p.strip().lower()
        for p in raw_value.split(",")
        if p and p.strip()
    ]

    if not parts:
        return ""

    normalized = []
    invalid = []

    for p in parts:
        key = p.replace(" ", "")
        code = WEEKDAY_ALIASES.get(key)
        if not code:
            invalid.append(p)
        else:
            normalized.append(code)

    if invalid:
        raise ValidationError(
            f"قيم أيام غير صالحة: {invalid}. "
            f"القيم المدعومة: {list(WEEKDAY_AR_NAMES.values())}"
        )

    # إزالة التكرار وترتيب ثابت
    unique = sorted(set(normalized), key=lambda x: WEEKDAY_CODES.index(x))
    return ",".join(unique)


# ============================================================
# 🕒 (NEW) Work Schedule — Phase 1 Data Layer Only
# ============================================================
class WorkSchedule(models.Model):
    """
    🧱 قالب دوام مرن قابل لإعادة الاستخدام
    Phase 1: بيانات فقط — بدون أي منطق تشغيلي
    """

    SCHEDULE_TYPES = [
        ("FULL_TIME", "دوام كامل"),
        ("FLEXIBLE", "دوام مرن (فترتين)"),
        ("HOURLY", "دوام بالساعات"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="work_schedules",
        verbose_name="الشركة",
    )

    name = models.CharField(
        max_length=150,
        verbose_name="اسم جدول الدوام",
        help_text="مثال: دوام إداري، دوام ليلي، دوام مرن",
    )

    schedule_type = models.CharField(
        max_length=20,
        choices=SCHEDULE_TYPES,
        default="FULL_TIME",
        verbose_name="نوع الدوام",
    )

    # ============================================================
    # 🕘 الفترات الزمنية
    # ============================================================
    period1_start = models.TimeField(null=True, blank=True, verbose_name="بداية الفترة الأولى")
    period1_end   = models.TimeField(null=True, blank=True, verbose_name="نهاية الفترة الأولى")
    period2_start = models.TimeField(null=True, blank=True, verbose_name="بداية الفترة الثانية")
    period2_end   = models.TimeField(null=True, blank=True, verbose_name="نهاية الفترة الثانية")

    allow_night_overlap = models.BooleanField(
        default=True,
        verbose_name="السماح بالتداخل الليلي",
        help_text="يسمح بأن تمتد الفترة لليوم التالي تلقائيًا",
    )

    # ============================================================
    # ⏱️ دوام بالساعات
    # ============================================================
    target_daily_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="عدد ساعات الدوام اليومية",
        help_text="يستخدم فقط في حالة الدوام بالساعات",
    )

    # ============================================================
    # 🟢 سماحات الوقت
    # ============================================================
    early_arrival_minutes = models.PositiveIntegerField(default=0, verbose_name="السماح بالدخول المبكر (دقائق)")
    early_exit_minutes    = models.PositiveIntegerField(default=0, verbose_name="السماح بالخروج المبكر (دقائق)")

    grace_minutes = models.PositiveIntegerField(
    default=0,
    verbose_name="سماحية التأخير (دقائق)",
    help_text="عدد الدقائق المسموح بها بعد بداية الدوام بدون احتساب تأخير",
    )

    # ============================================================
    # 📅 أيام الإجازة الأسبوعية
    # ============================================================
    weekend_days = models.CharField(
        max_length=50,
        default="",
        blank=True,
        verbose_name="أيام الإجازة الأسبوعية",
        help_text="مثال: fri أو sat أو fri,sat",
    )

    is_active = models.BooleanField(default=True, verbose_name="نشط")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    class Meta:
        ordering = ["name"]
        verbose_name = "جدول دوام"
        verbose_name_plural = "جداول الدوام"

    # ============================================================
    # 🔒 Validation Hook
    # ============================================================
    def clean(self):
        try:
            self.weekend_days = normalize_weekend_days(self.weekend_days)
        except ValidationError as exc:
            raise exc

    # ============================================================
    # 🔒 Save Hook (Safety Net)
    # ============================================================
    def save(self, *args, **kwargs):
        self.weekend_days = normalize_weekend_days(self.weekend_days)
        super().save(*args, **kwargs)

    # ============================================================
    # 🧠 Helpers
    # ============================================================
    def get_weekend_days_list(self):
        """['fri', 'sat']"""
        if not self.weekend_days:
            return []
        return self.weekend_days.split(",")

    def get_weekend_days_ar_list(self):
        """['الجمعة', 'السبت']"""
        return [
            WEEKDAY_AR_NAMES.get(code, code)
            for code in self.get_weekend_days_list()
        ]

    def get_weekend_days_ar_display(self):
        """'الجمعة، السبت'"""
        return "، ".join(self.get_weekend_days_ar_list())

    def is_weekend(self, target_date: date) -> bool:
        if not target_date:
            return False

        mapping = {
            "mon": 0,
            "tue": 1,
            "wed": 2,
            "thu": 3,
            "fri": 4,
            "sat": 5,
            "sun": 6,
        }

        weekday_index = target_date.weekday()
        weekend_indexes = [
            mapping.get(code)
            for code in self.get_weekend_days_list()
            if code in mapping
        ]
        return weekday_index in weekend_indexes

    # ============================================================
    # 🛡️ SAFE __str__
    # ============================================================
    def __str__(self):
        try:
            company_name = str(self.company)
        except Exception:
            company_name = "HARD DEFAULT"

        return f"{self.name} — {company_name}"


# ============================================================
# ⚙️ 1) Attendance Setting
# ============================================================
class AttendanceSetting(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='attendance_settings'
    )

    biotime_server_url = models.URLField(max_length=255)
    api_key = models.CharField(max_length=255)

    auto_sync_enabled = models.BooleanField(default=False)
    last_sync = models.DateTimeField(null=True, blank=True)

    failure_count = models.PositiveIntegerField(default=0)
    last_failure_message = models.CharField(max_length=255, null=True, blank=True)
    sync_health_status = models.CharField(
        max_length=20,
        default="OK",
        choices=[
            ("OK", "سليم"),
            ("FAILURE", "فشل"),
            ("AUTO_DISABLED", "تم الإيقاف تلقائيًا"),
        ],
    )
    auto_disabled_at = models.DateTimeField(null=True, blank=True)

    work_start = models.TimeField(default=timezone.datetime.strptime("09:00", "%H:%M").time())
    work_end   = models.TimeField(default=timezone.datetime.strptime("17:00", "%H:%M").time())
    grace_minutes = models.PositiveIntegerField(default=15)

    def __str__(self):
        return f"إعدادات حضور {self.company}"


# ============================================================
# 📘 2) Attendance Policy (Company)
# ============================================================
class AttendancePolicy(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='attendance_policies'
    )

    work_start = models.TimeField()
    work_end   = models.TimeField()
    grace_minutes = models.PositiveIntegerField(default=15)
    absence_threshold_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name="مهلة قبل احتساب الغياب (دقائق)",
        help_text="بعد هذه المدة من بداية الدوام يتحول lifecycle_pending إلى غياب"
    )


    overtime_enabled = models.BooleanField(default=True)
    overtime_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.50)

    auto_absent_if_no_checkin = models.BooleanField(default=True)

    weekend_days = models.CharField(max_length=50, default="fri,sat")
    weekly_hours_limit = models.PositiveIntegerField(default=48)

    def __str__(self):
        return f"سياسة حضور — {self.company}"

# ============================================================
# 🏢 Company Attendance Setting (Company Level Policy)
# Clean Source of Truth for Settings Page
# ============================================================
class CompanyAttendanceSetting(models.Model):
    """
    إعدادات سياسة الحضور العامة للشركة
    """

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name="attendance_setting_config"
    )

    # ⏱️ Grace Minutes
    grace_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name="سماحية التأخير (دقائق)"
    )

    # ⏱️ Late After
    late_after_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name="يعتبر متأخر بعد (دقائق)"
    )

    # ⛔ Absence Threshold
    absence_after_minutes = models.PositiveIntegerField(
        default=180,
        verbose_name="يعتبر غائب بعد (دقائق)"
    )

    # 🚫 Auto Absent
    auto_absent_if_no_checkin = models.BooleanField(
        default=True,
        verbose_name="احتساب غياب تلقائي بدون تسجيل حضور"
    )

    # 🕒 Overtime
    overtime_enabled = models.BooleanField(
        default=True,
        verbose_name="تفعيل العمل الإضافي"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Company Attendance Setting — {self.company}"

# ============================================================
# 🎯 3) Employee Attendance Policy (Overrides)
# ============================================================
class EmployeeAttendancePolicy(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    company_policy = models.ForeignKey(AttendancePolicy, on_delete=models.CASCADE)

    custom_work_start = models.TimeField(null=True, blank=True)
    custom_work_end   = models.TimeField(null=True, blank=True)
    custom_grace_minutes = models.PositiveIntegerField(null=True, blank=True)

    custom_overtime_enabled = models.BooleanField(null=True, blank=True)
    custom_overtime_rate    = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"سياسة {self.employee.full_name}"


# ============================================================
# 🛰️ 4) Biotime Devices
# ============================================================
class AttendanceDevice(models.Model):
    device = models.ForeignKey(BiotimeDevice, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    status    = models.CharField(max_length=20, default="connected")

    def __str__(self):
        return f"{self.device.device_name} — {self.company}"


# ============================================================
# 📘 5) Attendance Record — Smart Engine V20 Ultra Pro
# ============================================================
class AttendanceRecord(models.Model):

    STATUS_CHOICES = [
        ("present", "حاضر"),
        ("late", "متأخر"),
        ("absent", "غائب"),
        ("leave", "إجازة"),
        ("holiday", "إجازة رسمية"),
        ("weekend", "عطلة أسبوعية"),
        ("not_started", "قبل المباشرة"),
        ("unknown", "غير معروف"),
        ("terminated", "منتهي خدمة"),

    ]

    # 🟣 Overtime Type Classification
    OVERTIME_TYPE_CHOICES = [
        ("NORMAL", "Normal Overtime"),
        ("WEEKEND", "Weekend Overtime"),
        ("HOLIDAY", "Holiday Overtime"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    check_in  = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="present")

    late_minutes     = models.IntegerField(default=0)
    early_minutes    = models.IntegerField(default=0)
    overtime_minutes = models.IntegerField(default=0)
    # 🟢 NEW FIELD
    overtime_type = models.CharField(
        max_length=20,
        choices=OVERTIME_TYPE_CHOICES,
        null=True,
        blank=True,
    )

    actual_hours     = models.FloatField(default=0.0)
    official_hours   = models.FloatField(default=0.0)

    reason_code = models.CharField(max_length=50, null=True, blank=True)

    biotime_log = models.ForeignKey(BiotimeLog, on_delete=models.SET_NULL, null=True, blank=True)
    synced_from_biotime = models.BooleanField(default=False)

    is_leave = models.BooleanField(default=False)
    # ============================================================
    # 🔒 Finalization Engine — Phase F.6 (V1)
    # ============================================================
    is_finalized = models.BooleanField(
        default=False,
        verbose_name="مقفل نهائيًا"
    )

    finalized_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ الإقفال"
    )


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ============================================================
    # 🧠 WorkdayEngine Classification
    # ============================================================
    def classify_v4(self):
        try:
            from attendance_center.services.workday_engine import WorkdayEngine
            engine = WorkdayEngine(self.employee, self.employee.company)
            return engine.classify(self)
        except Exception:
            return None

    # ============================================================
    # 🔄 Reverse Integration
    # ============================================================
    def run_reverse_integration(self):
        try:
            from attendance_center.services.reverse_integration_engine import ReverseIntegrationEngine
            ReverseIntegrationEngine(self).run()
        except Exception:
            pass

    # ============================================================
    # 🧠 Clean Save — SAFE MODE (Engine Driven)
    # ============================================================
    def save(self, *args, skip_engine=False, **kwargs):
        # 🔒 Engine Recursion Guard
        if skip_engine:
            return super().save(*args, **kwargs)

        from attendance_center.services.holiday_resolver import HolidayResolver

        # ====================================================
        # 🟥 Company Holiday Guard (DB Source of Truth)
        # ====================================================
        try:
            if (
                self.employee
                and self.date
                and HolidayResolver.is_holiday(self.date, self.employee.company)
            ):
                # 🟢 فقط إذا لا يوجد حضور → اعتبره Holiday Leave
                if not self.check_in and not self.check_out:
                    self.status = "holiday"
                    self.reason_code = "company_holiday"
                    self.is_leave = False

                    self.late_minutes = 0
                    self.early_minutes = 0
                    self.overtime_minutes = 0
                    self.actual_hours = 0
                    self.official_hours = 0


                    super().save(*args, **kwargs)
                    return

        except Exception:
            pass

        # ====================================================
        # 🟨 Approved Leave Guard
        # ====================================================
        if self.is_leave:
            super().save(*args, **kwargs)
            return

        # ====================================================
        # 🟦 Reverse Integration
        # ====================================================
        if self.synced_from_biotime:
            self.run_reverse_integration()


            # 🔒 V7 Lifecycle Guard
            if self.reason_code == "lifecycle_pending":
                super().save(*args, **kwargs)
                return
            # ====================================================
            # 🟢 Auto Recalculate On Manual Edit (Non-Finalized Only)
            # ====================================================
            if not self.is_finalized:
                try:
                    from attendance_center.services.workday_engine import WorkdayEngine
                    engine = WorkdayEngine(self.employee, self.employee.company)

                    # 🔁 إعادة الحساب
                    engine.apply(self)

                    # 🔒 إعادة الإقفال بعد النجاح
                    self.is_finalized = True
                    self.finalized_at = timezone.now()

                except Exception:
                    pass


        super().save(*args, **kwargs)

    # ============================================================
    # 🔄 Smart Biotime Integration
    # ============================================================
    @classmethod
    def create_from_biotime(cls, log: BiotimeLog):
        try:
            emp = Employee.objects.filter(
                employee_code=log.employee.employee_id
            ).first()

            if not emp:
                return None

            date = log.punch_time.date()
            t = log.punch_time.time()

            record, _ = cls.objects.get_or_create(
                employee=emp,
                date=date,
                defaults={
                    "status": "present",
                    "synced_from_biotime": True,
                    "biotime_log": log
                }
            )

            if log.event_type == "check_in":
                record.check_in = t
            elif log.event_type == "check_out":
                record.check_out = t

            record.synced_from_biotime = True
            record.biotime_log = log

            record.save()
            return record

        except Exception as e:
            print(f"⚠️ خطأ أثناء إنشاء سجل الحضور من Biotime: {e}")
            return None

    # ============================================================
    # 🔒 DB Safety
    # ============================================================
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "date"],
                name="unique_attendance_per_employee_per_day",
            )
        ]
        indexes = [
            models.Index(fields=["employee", "date"]),
        ]
# ============================================================
# 🎌 Holiday Type
# ============================================================
class HolidayType(models.Model):
    """
    نوع الإجازة (رسمية / وطنية / دينية / خاصة ...)
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="الكود"
    )

    name = models.CharField(
        max_length=150,
        verbose_name="اسم الإجازة"
    )

    is_paid = models.BooleanField(
        default=True,
        verbose_name="إجازة مدفوعة"
    )

    color = models.CharField(
        max_length=20,
        default="blue",
        verbose_name="لون العرض"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "نوع إجازة"
        verbose_name_plural = "أنواع الإجازات"

    def __str__(self):
        return self.name
# ============================================================
# 📅 Company Holiday Calendar
# ============================================================
class CompanyHoliday(models.Model):
    """
    تقويم الإجازات الرسمي الخاص بالشركة
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="holidays",
        verbose_name="الشركة"
    )

    name = models.CharField(
        max_length=200,
        verbose_name="اسم الإجازة"
    )

    holiday_type = models.ForeignKey(
        HolidayType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="نوع الإجازة"
    )

    start_date = models.DateField(
        verbose_name="تاريخ البداية"
    )

    end_date = models.DateField(
        verbose_name="تاريخ النهاية"
    )

    is_paid = models.BooleanField(
        default=True,
        verbose_name="مدفوعة الأجر"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="نشطة"
    )

    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name="ملاحظات"
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
        verbose_name = "إجازة رسمية"
        verbose_name_plural = "الإجازات الرسمية"
        ordering = ["start_date"]
        indexes = [
            models.Index(fields=["company", "start_date", "end_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gte=models.F("start_date")),
                name="holiday_end_date_after_start_date",
            ),
        ]

    # ========================================================
    # 🔒 Validation Hook
    # ========================================================
    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError(
                "تاريخ نهاية الإجازة لا يمكن أن يكون قبل تاريخ البداية."
            )

    # ========================================================
    # 🔒 Save Hook (Safety Net)
    # ========================================================
    def save(self, *args, **kwargs):
        self.full_clean()  # يضمن تطبيق جميع القيود
        super().save(*args, **kwargs)

    # ========================================================
    # 🧠 Helpers
    # ========================================================
    def includes(self, target_date: date) -> bool:
        """
        هل هذا التاريخ يقع ضمن الإجازة؟
        """
        if not target_date:
            return False
        return self.start_date <= target_date <= self.end_date

    def duration_days(self) -> int:
        """
        عدد أيام الإجازة
        """
        return (self.end_date - self.start_date).days + 1

    # ========================================================
    # 🛡️ SAFE __str__
    # ========================================================
    def __str__(self):
        try:
            company_name = str(self.company)
        except Exception:
            company_name = "UNKNOWN COMPANY"

        return f"{self.name} — {company_name} ({self.start_date} → {self.end_date})"

    # ========================================================
    # 🧠 Helpers
    # ========================================================
    def includes(self, target_date: date) -> bool:
        return self.start_date <= target_date <= self.end_date

    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.name} ({self.start_date} → {self.end_date})"
