from django.urls import path
from . import views

app_name = "leave_center"

urlpatterns = [

    # ================================================================
    # 🔵 الصفحات الأساسية
    # ================================================================
    path("<int:company_id>/", views.leave_list, name="leave_list"),
    path("<int:company_id>/add/", views.leave_add, name="leave_add"),
    path("<int:company_id>/<int:leave_id>/detail/", views.leave_detail, name="leave_detail"),

    # ================================================================
    # 📅 Leave Calendar
    # ================================================================
    path("<int:company_id>/calendar/", views.leave_calendar, name="leave_calendar"),
    path("<int:company_id>/calendar/events/", views.calendar_events, name="calendar_events"),

    # ================================================================
    # 🟩 Workflow — Approvals (Unified)
    # ================================================================
    path("<int:company_id>/<int:leave_id>/approve/",
         views.approve_request,
         name="approve_request"),

    # ================================================================
    # 🔴 Workflow — Rejections
    # ================================================================
    path("<int:company_id>/<int:leave_id>/reject/",
         views.reject_request,
         name="reject_request"),

    # ================================================================
    # ⚫ Workflow — Cancellation
    # ================================================================
    path("<int:company_id>/<int:leave_id>/cancel/",
         views.cancel_leave,
         name="cancel_leave"),

    # ================================================================
    # ⚫ Employee self-cancel (new)
    # ================================================================
    path("<int:company_id>/<int:leave_id>/cancel/self/",
         views.cancel_request,
         name="cancel_request"),

    # ================================================================
    # 🟦 Leave Balance Page
    # ================================================================
    path("<int:company_id>/balance/",
         views.leave_balance_view,
         name="leave_balance"),

    # ================================================================
    # 🔄 Reset Leave Balance (HR/Admin)
    # ================================================================
    path("<int:company_id>/balance/<int:employee_id>/<int:leave_type_id>/reset/",
         views.reset_leave_balance,
         name="reset_leave_balance"),

    # ================================================================
    # 🟦 تطبيق الإجازة على الحضور
    # ================================================================
    path("<int:company_id>/<int:leave_id>/apply/attendance/",
         views.apply_leave_to_attendance,
         name="apply_leave_to_attendance"),

    # ================================================================
    # 🗑 Delete Leave
    # ================================================================
    path("<int:company_id>/<int:leave_id>/delete/",
         views.delete_leave,
         name="delete_leave"),
]
