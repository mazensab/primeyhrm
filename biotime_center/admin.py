# ================================================================
# 📂 الملف: biotime_center/admin.py
# ✔ متوافق 100% مع IClock Models V9.0
# ✔ Developed by Mazen — Mham Cloud 2026
# ================================================================

from django.contrib import admin
from .models import (
    BiotimeSetting,
    BiotimeDevice,
    BiotimeEmployee,
    BiotimeLog,
)

# ------------------------------------------------------------
# ⚙️ إعدادات الاتصال
# ------------------------------------------------------------
@admin.register(BiotimeSetting)
class BiotimeSettingAdmin(admin.ModelAdmin):
    list_display = ("company", "email", "server_url", "last_login_status", "last_login_at")
    search_fields = ("company", "email", "server_url")


# ------------------------------------------------------------
# 💻 أجهزة IClock (Terminals)
# ------------------------------------------------------------
@admin.register(BiotimeDevice)
class BiotimeDeviceAdmin(admin.ModelAdmin):

    list_display = (
        "device_id",
        "sn",
        "alias",
        "ip_address",
        "state",
        "user_count",
        "face_count",
        "palm_count",
        "last_sync",
    )

    list_filter = ("state",)
    search_fields = ("sn", "alias", "ip_address")
    ordering = ("device_id",)


# ------------------------------------------------------------
# 👥 الموظفون
# ------------------------------------------------------------
@admin.register(BiotimeEmployee)
class BiotimeEmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "full_name", "department", "position", "is_active")
    search_fields = ("employee_id", "full_name")


# ------------------------------------------------------------
# 🕒 سجلات Transactions (IClock)
# ------------------------------------------------------------
@admin.register(BiotimeLog)
class BiotimeLogAdmin(admin.ModelAdmin):

    list_display = (
        "log_id",
        "employee_code",
        "punch_time",
        "punch_state",
        "device_sn",
        "terminal_alias",
    )

    list_filter = ("punch_state",)
    search_fields = ("employee_code", "device_sn", "terminal_alias")
    ordering = ("-punch_time",)
