# ============================================================
# 📂 الملف: biotime_center/models.py
# ⚙️ نماذج Biotime Cloud — الإصدار V12.0 (MT-5 HARD LOCK 🔒)
# 🚀 Phase MT-5 — Company NOT NULL Enforcement
# 🧱 Enterprise Isolation Mode — FINAL
# ============================================================

from django.db import models
from django.utils import timezone


# ------------------------------------------------------------
# ⚙️ Biotime Setting
# ------------------------------------------------------------
class BiotimeSetting(models.Model):

    server_url = models.URLField(max_length=255)

    company = models.ForeignKey(
        "company_manager.Company",
        on_delete=models.CASCADE,
        related_name="biotime_settings",
        db_index=True,
    )

    biotime_company = models.CharField(max_length=150, db_index=True)

    email = models.CharField(max_length=150)
    password = models.CharField(max_length=255)

    jwt_token = models.TextField(blank=True, null=True)
    token_expiry = models.DateTimeField(blank=True, null=True)

    last_login_status = models.CharField(max_length=20, blank=True, null=True)
    last_login_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("company", "biotime_company"),)

    def __str__(self):
        return f"Biotime Setting ({self.company} → {self.biotime_company})"


# ------------------------------------------------------------
# 💻 Biotime Device — MT-5 HARD LOCK
# ------------------------------------------------------------
class BiotimeDevice(models.Model):

    device_id = models.IntegerField(unique=True)

    # 🔒 HARD ISOLATION (NOT NULL)
    company = models.ForeignKey(
        "company_manager.Company",
        on_delete=models.CASCADE,
        related_name="biotime_devices",
        db_index=True,
    )

    sn = models.CharField(max_length=150)
    alias = models.CharField(max_length=150)
    terminal_name = models.CharField(max_length=150, blank=True, null=True)

    ip_address = models.GenericIPAddressField(blank=True, null=True)
    firmware_version = models.CharField(max_length=100, blank=True, null=True)
    push_ver = models.CharField(max_length=100, blank=True, null=True)

    state = models.IntegerField(default=0)
    terminal_tz = models.IntegerField(blank=True, null=True)

    area_id = models.IntegerField(blank=True, null=True)
    area_code = models.CharField(max_length=100, blank=True, null=True)
    area_name = models.CharField(max_length=150, blank=True, null=True)

    biotime_company_code = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=150, blank=True, null=True)

    last_activity = models.CharField(max_length=255, blank=True, null=True)
    user_count = models.IntegerField(blank=True, null=True)
    fp_count = models.IntegerField(blank=True, null=True)
    face_count = models.IntegerField(blank=True, null=True)
    palm_count = models.IntegerField(blank=True, null=True)
    transaction_count = models.IntegerField(blank=True, null=True)

    push_time = models.CharField(max_length=100, blank=True, null=True)
    transfer_time = models.CharField(max_length=100, blank=True, null=True)
    transfer_interval = models.IntegerField(blank=True, null=True)

    raw_json = models.JSONField(blank=True, null=True)

    last_sync = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["company", "device_id"]),
        ]

    def __str__(self):
        return f"{self.alias} ({self.sn})"


# ------------------------------------------------------------
# 👥 Biotime Employee — MT-5 HARD LOCK
# ------------------------------------------------------------
class BiotimeEmployee(models.Model):

    employee_id = models.CharField(max_length=100, db_index=True)

    # 🔒 HARD ISOLATION (NOT NULL)
    company = models.ForeignKey(
        "company_manager.Company",
        on_delete=models.CASCADE,
        related_name="biotime_employees",
        db_index=True,
    )
        # 🔗 Link to Primey Employee (MT-6 Safe)
    linked_employee = models.OneToOneField(
        "employee_center.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="biotime_record",
        db_index=True,
    )


    full_name = models.CharField(max_length=150)

    department = models.CharField(max_length=150, blank=True, null=True)
    position = models.CharField(max_length=150, blank=True, null=True)

    card_number = models.CharField(max_length=100, blank=True, null=True)
    enrolled_fingers = models.PositiveIntegerField(default=0)
    photo_url = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "employee_id"],
                name="unique_biotime_employee_per_company"
            )
        ]
        indexes = [
            models.Index(fields=["company", "employee_id"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"


# ------------------------------------------------------------
# 🕒 Biotime Log — MT-5 HARD LOCK
# ------------------------------------------------------------
class BiotimeLog(models.Model):

    log_id = models.IntegerField(unique=True)

    # 🔒 HARD ISOLATION (NOT NULL)
    company = models.ForeignKey(
        "company_manager.Company",
        on_delete=models.CASCADE,
        related_name="biotime_logs",
        db_index=True,
    )

    employee_code = models.CharField(max_length=100)
    punch_time = models.DateTimeField()
    punch_state = models.CharField(max_length=10)
    verify_type = models.IntegerField(default=0)
    work_code = models.CharField(max_length=10, blank=True, null=True)

    device_sn = models.CharField(max_length=150)
    terminal_alias = models.CharField(max_length=150, blank=True, null=True)
    area_alias = models.CharField(max_length=150, blank=True, null=True)

    raw_json = models.JSONField(blank=True, null=True)

    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["company", "log_id"]),
            models.Index(fields=["company", "employee_code"]),
        ]

    def __str__(self):
        return f"{self.employee_code} - {self.punch_time}"

class BiotimeSyncLog(models.Model):

    company = models.ForeignKey(
        "company_manager.Company",
        on_delete=models.CASCADE,
        related_name="biotime_sync_logs",
        db_index=True,
    )

    timestamp = models.DateTimeField(default=timezone.now)

    devices_synced = models.PositiveIntegerField(default=0)
    employees_synced = models.PositiveIntegerField(default=0)
    logs_synced = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=[
            ("SUCCESS", "نجاح"),
            ("FAILED", "فشل"),
            ("PARTIAL", "جزئي"),
        ],
        default="SUCCESS"
    )

    message = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Sync {self.status} — {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

# ============================================================
# 🔄 Biotime Sync State — Employee Scoped (MT SAFE)
# ============================================================

from django.db import models


class BiotimeSyncState(models.Model):
    """
    🎯 مسؤول عن تتبع حالة مزامنة كل موظف مع BioTime
    - Multi-Tenant Safe
    - Snapshot Based
    - Retry Controlled
    """

    company = models.ForeignKey(
        "company_manager.Company",
        on_delete=models.CASCADE,
        related_name="biotime_sync_states",
    )

    employee = models.OneToOneField(
        "employee_center.Employee",
        on_delete=models.CASCADE,
        related_name="biotime_sync_state",
    )

    # آخر Snapshot تمت مزامنته بنجاح
    last_synced_snapshot = models.JSONField(
        default=dict,
        blank=True,
    )

    # الحقول التي تحتاج مزامنة
    dirty_fields = models.JSONField(
        default=list,
        blank=True,
    )

    is_dirty = models.BooleanField(default=False)

    retry_count = models.PositiveIntegerField(default=0)

    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)

    last_error = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("company", "employee")
        indexes = [
            models.Index(fields=["company", "is_dirty"]),
        ]

    def mark_dirty(self, fields: list):
        self.is_dirty = True
        self.dirty_fields = fields
        self.save(update_fields=["is_dirty", "dirty_fields", "updated_at"])

    def mark_success(self, snapshot: dict):
        self.is_dirty = False
        self.retry_count = 0
        self.last_error = None
        self.last_synced_snapshot = snapshot
        self.last_success_at = timezone.now()
        self.dirty_fields = []
        self.save()

    def mark_failure(self, error: str):
        self.retry_count += 1
        self.last_error = str(error)
        self.last_attempt_at = timezone.now()

        # 🛑 Stop retrying after 5 attempts
        if self.retry_count >= 5:
            self.is_dirty = False

        self.save()
