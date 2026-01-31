from django.contrib import admin
from .models import PayrollRecord, PayrollRecordHistory


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ("employee", "month", "net_salary", "status", "created_at")
    list_filter = ("status", "month", "created_at")
    search_fields = ("employee__first_name", "employee__last_name")
    ordering = ("-month",)


@admin.register(PayrollRecordHistory)
class PayrollRecordHistoryAdmin(admin.ModelAdmin):
    list_display = ("payroll", "action", "user", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("payroll__employee__first_name", "payroll__employee__last_name")
    ordering = ("-created_at",)
