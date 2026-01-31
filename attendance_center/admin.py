# 📂 الملف: attendance_center/admin.py
# 🧭 لوحة إدارة الحضور والانصراف (Admin Panel)
# 🚀 الإصدار V3.36 — عرض ذكي متكامل مع Biotime وخصائص التحليل

from django.contrib import admin
from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """
    ⚙️ إدارة سجلات الحضور والانصراف في لوحة الإدارة
    - عرض الأعمدة الذكية
    - تمكين البحث والتصفية
    - تكامل مع Biotime Sync
    """

    # 🧱 الأعمدة التي تظهر في لوحة الإدارة
    list_display = (
        "employee_display",
        "date",
        "status_display",
        "check_in",
        "check_out",
        "duration_display",
        "synced_from_biotime",
    )

    # 🔍 حقول البحث
    search_fields = (
        "employee__first_name",
        "employee__last_name",
        "employee__code",
        "date",
    )

    # 🔽 خيارات التصفية الجانبية
    list_filter = (
        "status",
        "synced_from_biotime",
        "date",
    )

    # 🕓 الترتيب الافتراضي
    ordering = ("-date",)

    # 🧩 تحسين واجهة التفاصيل
    fieldsets = (
        ("🧾 بيانات أساسية", {
            "fields": ("employee", "date", "status")
        }),
        ("⏱️ الوقت", {
            "fields": ("check_in", "check_out", "synced_from_biotime")
        }),
    )

    # ============================================================
    # 🧠 دوال مساعدة لعرض القيم في الواجهة
    # ============================================================

    def employee_display(self, obj):
        """👤 اسم الموظف"""
        return obj.employee.full_name() if callable(obj.employee.full_name) else str(obj.employee)
    employee_display.short_description = "الموظف"

    def status_display(self, obj):
        """📍 عرض الحالة بشكل أنيق"""
        icons = {
            "present": "🟢 حاضر",
            "absent": "🔴 غائب",
            "late": "🟡 متأخر",
            "leave": "🔵 إجازة",
        }
        return icons.get(obj.status, obj.get_status_display())
    status_display.short_description = "الحالة"

    def duration_display(self, obj):
        """⏱️ عرض مدة العمل بالساعات"""
        return f"{obj.duration} ساعة" if obj.duration else "-"
    duration_display.short_description = "المدة (ساعات)"
