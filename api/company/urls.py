# ============================================================
# 📂 api/company/urls.py
# 🏢 Company APIs Router
# Mham Cloud
# ============================================================

from django.urls import path

from api.company.employee import (
    switch_company,
    employees_list,
    employees_report,
    employee_detail,
    employee_create,
    employee_update,
    employee_profile_update,
    employee_toggle_status,
    employee_change_role,
    employee_history,
    employee_assign_work_schedule,
    employee_update_job_info,
    update_employee_profile,
    update_employee_financial,
    employee_search,
    employee_link_biotime,
)

from api.company.branches import (
    branches_list,
    branch_create,
    branch_update,
)

from api.company.department import (
    departments_list,
    department_create,
    department_update,
)

from api.company.job_title import (
    job_titles_list,
    job_title_create,
    job_title_update,
)

from api.company.attendance import (
    company_attendance_policy,
    attendance_dashboard,
    attendance_sync,
    attendance_unmapped_logs,
    attendance_reports_preview,
    attendance_records,
    employee_attendance_preview,
    employee_schedule_preview,
    attendance_manual_entry,
    attendance_manual_action,
    work_schedules,
    work_schedule_detail,
    work_schedule_toggle,
)

# ============================================================
# 🏖 Leave APIs
# ============================================================
from api.company.leaves import (
    company_leave_requests,
    create_leave_request,
    approve_leave,
    reject_leave,
    leave_balance,
    company_leave_types,
    company_annual_leave_policy,
)


from api.company.payroll.runs import (
    PayrollRunListAPIView,
    PayrollRunCreateAPIView,
    PayrollRunDetailAPIView,
    PayrollRunCalculateAPIView,
    PayrollRunApproveAPIView,
    PayrollRunResetAPIView,
    PayrollRunPayAPIView,
)

from api.company.payroll.records import (
    PayrollRunRecordsListAPIView,
    PayrollRecordDetailAPIView,
    PayrollRecordLedgerAPIView,
    PayrollRecordPayAPIView,
)

from api.company.payroll.salary_slip import (
    CompanyPayrollSalarySlipAPIView,
)
# ============================================================
# 🧬 Biotime APIs
# ============================================================
from api.company.biotime.biotime import (
    company_biotime_sync_employee,
    company_biotime_sync_employees,
    company_biotime_employees,
    company_biotime_test_connection,
    company_biotime_save_settings,
    company_biotime_status,
    company_biotime_sync_logs,
    company_biotime_push_employee,
    company_biotime_link_employee,
)

from api.company.biotime.devices import (
    company_biotime_devices,
    company_biotime_device_detail,
    company_biotime_sync_devices,
    company_biotime_sync_single_device,
    company_biotime_reset_connection,
    company_biotime_test_single_device,
)

from api.company.whatsapp.settings import (
    company_whatsapp_settings,
    company_whatsapp_settings_update,
)
from api.company.whatsapp.status import (
    company_whatsapp_status,
    company_whatsapp_session_create_qr,
    company_whatsapp_session_create_pairing_code,
    company_whatsapp_session_disconnect,
)
from api.company.whatsapp.logs import company_whatsapp_logs
from api.company.whatsapp.templates import (
    company_whatsapp_templates,
    company_whatsapp_template_create,
    company_whatsapp_template_update,
    company_whatsapp_template_toggle,
    company_whatsapp_template_delete,
)
from api.company.whatsapp.send_test import company_whatsapp_send_test

# ============================================================
# 📈 Performance APIs
# ============================================================
from api.company.performance import (
    performance_dashboard,
    performance_templates_list,
    performance_template_create,
    performance_reviews_list,
    performance_review_detail,
    performance_review_create,
    performance_submit_self,
    performance_submit_manager,
    performance_submit_hr,
    performance_workflow_status,
    performance_employees_lookup,
)

from api.company.settings import (
    company_settings_overview,
    company_settings_update,
)

from api.system.notifications import (
    notifications_list,
    mark_notification_read,
    mark_all_notifications_read,
)

from api.company.payments.tamara_create_checkout import tamara_create_checkout
from api.company.payments.tamara_webhook import tamara_webhook


app_name = "company_api"

urlpatterns = [
    # ========================================================
    # 🏢 Company Context
    # ========================================================
    path(
        "switch/",
        switch_company,
        name="switch_company",
    ),

    # ========================================================
    # ⚙️ Company Settings
    # ========================================================
    path(
        "settings/",
        company_settings_overview,
        name="company_settings_overview",
    ),
    path(
        "settings/update/",
        company_settings_update,
        name="company_settings_update",
    ),

    # ========================================================
    # 💳 Company Payments
    # ========================================================
    path(
        "payments/tamara/create-checkout/",
        tamara_create_checkout,
        name="company_tamara_create_checkout",
    ),
    path(
        "payments/tamara/webhook/",
        tamara_webhook,
        name="company_tamara_webhook",
    ),

    # ========================================================
    # 👥 Employees
    # ========================================================
    path(
        "employees/",
        employees_list,
        name="employees_list",
    ),
    path(
        "employees/report/",
        employees_report,
        name="employees_report",
    ),
    path(
        "employees/create/",
        employee_create,
        name="employee_create",
    ),
    path(
        "employees/search/",
        employee_search,
        name="employee_search",
    ),

    # ========================================================
    # 🏢 Company Master Data
    # ========================================================
    path(
        "branches/list/",
        branches_list,
        name="branches_list",
    ),
    path(
        "branches/create/",
        branch_create,
        name="branch_create",
    ),
    path(
        "branches/<int:branch_id>/update/",
        branch_update,
        name="branch_update",
    ),

    path(
        "departments/list/",
        departments_list,
        name="departments_list",
    ),
    path(
        "departments/create/",
        department_create,
        name="department_create",
    ),
    path(
        "departments/<int:department_id>/update/",
        department_update,
        name="department_update",
    ),

    path(
        "job-titles/list/",
        job_titles_list,
        name="job_titles_list",
    ),
    path(
        "job-titles/create/",
        job_title_create,
        name="job_title_create",
    ),
    path(
        "job-titles/<int:job_title_id>/update/",
        job_title_update,
        name="job_title_update",
    ),

    # ========================================================
    # 🕒 Work Schedules
    # ========================================================
    path(
        "work-schedules/",
        work_schedules,
        name="work_schedules",
    ),
    path(
        "work-schedules/<int:schedule_id>/",
        work_schedule_detail,
        name="work_schedule_detail",
    ),
    path(
        "work-schedules/<int:schedule_id>/toggle/",
        work_schedule_toggle,
        name="work_schedule_toggle",
    ),

    # ========================================================
    # 📊 Attendance
    # ========================================================
    path(
        "attendance/dashboard/",
        attendance_dashboard,
        name="attendance_dashboard",
    ),
    path(
        "attendance/policy/",
        company_attendance_policy,
        name="company_attendance_policy",
    ),
    path(
        "attendance/sync/",
        attendance_sync,
        name="attendance_sync",
    ),
    path(
        "attendance/unmapped-logs/",
        attendance_unmapped_logs,
        name="attendance_unmapped_logs",
    ),
    path(
        "attendance/reports/preview/",
        attendance_reports_preview,
        name="attendance_reports_preview",
    ),
    path(
        "attendance/records/",
        attendance_records,
        name="attendance_records",
    ),
    path(
        "attendance/manual-entry/",
        attendance_manual_entry,
        name="attendance_manual_entry",
    ),
    path(
        "attendance/manual-action/",
        attendance_manual_action,
        name="attendance_manual_action",
    ),
    path(
        "attendance/employee-preview/<int:employee_id>/",
        employee_attendance_preview,
        name="employee_attendance_preview",
    ),
    path(
        "attendance/employee-schedule-preview/",
        employee_schedule_preview,
        name="employee_schedule_preview",
    ),

    # ========================================================
    # 🏖 Leave Center
    # ========================================================
    path(
        "leaves/requests/",
        company_leave_requests,
        name="leave_requests",
    ),
    path(
        "leaves/request/",
        create_leave_request,
        name="create_leave_request",
    ),
    path(
        "leaves/balance/",
        leave_balance,
        name="leave_balance",
    ),
    path(
        "leaves/types/",
        company_leave_types,
        name="company_leave_types",
    ),
    path(
        "leaves/annual-policy/",
        company_annual_leave_policy,
        name="company_annual_leave_policy",
    ),
    path(
        "leaves/<int:leave_id>/approve/",
        approve_leave,
        name="approve_leave",
    ),
    path(
        "leaves/<int:leave_id>/reject/",
        reject_leave,
        name="reject_leave",
    ),

    # ========================================================
    # 👤 Employee Detail / Update
    # ========================================================
    path(
        "employees/<int:employee_id>/",
        employee_detail,
        name="employee_detail",
    ),
    path(
        "employees/<int:employee_id>/update/",
        employee_update,
        name="employee_update",
    ),
    path(
        "employees/<int:employee_id>/profile-update/",
        employee_profile_update,
        name="employee_profile_update",
    ),
    path(
        "employees/<int:employee_id>/toggle-status/",
        employee_toggle_status,
        name="employee_toggle_status",
    ),
    path(
        "employees/<int:employee_id>/change-role/",
        employee_change_role,
        name="employee_change_role",
    ),
    path(
        "employees/<int:employee_id>/history/",
        employee_history,
        name="employee_history",
    ),

    # ========================================================
    # 🕒 Work Schedule / Job Info
    # ========================================================
    path(
        "employees/<int:employee_id>/assign-work-schedule/",
        employee_assign_work_schedule,
        name="employee_assign_work_schedule",
    ),
    path(
        "employees/<int:employee_id>/update-job-info/",
        employee_update_job_info,
        name="employee_update_job_info",
    ),

    # ========================================================
    # 🧩 Extended Update APIs
    # ========================================================
    path(
        "employees/<int:employee_id>/update-profile/",
        update_employee_profile,
        name="update_employee_profile",
    ),
    path(
        "employees/<int:employee_id>/update-financial/",
        update_employee_financial,
        name="update_employee_financial",
    ),

    # ========================================================
    # 🧬 Employee ↔ Biotime
    # ========================================================
    path(
        "employees/<int:employee_id>/link-biotime/",
        employee_link_biotime,
        name="employee_link_biotime",
    ),

    # ========================================================
    # 🧬 Biotime Settings / Status
    # ========================================================
    path(
        "biotime/status/",
        company_biotime_status,
        name="company_biotime_status",
    ),
    path(
        "biotime/save-settings/",
        company_biotime_save_settings,
        name="company_biotime_save_settings",
    ),
    path(
        "biotime/test-connection/",
        company_biotime_test_connection,
        name="company_biotime_test_connection",
    ),
    path(
        "biotime/reset-connection/",
        company_biotime_reset_connection,
        name="company_biotime_reset_connection",
    ),

    # ========================================================
    # 🧬 Biotime Employees
    # ========================================================
    path(
        "biotime/employees/",
        company_biotime_employees,
        name="company_biotime_employees",
    ),
    path(
        "biotime/sync-employees/",
        company_biotime_sync_employees,
        name="company_biotime_sync_employees",
    ),
    path(
        "biotime/link-employee/",
        company_biotime_link_employee,
        name="company_biotime_link_employee",
    ),
    path(
        "biotime/push-employee/<int:employee_id>/",
        company_biotime_push_employee,
        name="company_biotime_push_employee",
    ),
    path(
        "biotime/sync-employee/<int:employee_id>/",
        company_biotime_sync_employee,
        name="company_biotime_sync_employee",
    ),

    # ========================================================
    # 🧬 Biotime Devices
    # ========================================================
    path(
        "biotime/devices/",
        company_biotime_devices,
        name="company_biotime_devices",
    ),
    path(
        "biotime/devices/sync/",
        company_biotime_sync_devices,
        name="company_biotime_sync_devices",
    ),
    path(
        "biotime/devices/<int:device_id>/",
        company_biotime_device_detail,
        name="company_biotime_device_detail",
    ),
    path(
        "biotime/devices/<int:device_id>/sync/",
        company_biotime_sync_single_device,
        name="company_biotime_sync_single_device",
    ),
    path(
        "biotime/devices/<int:device_id>/test/",
        company_biotime_test_single_device,
        name="company_biotime_test_single_device",
    ),

    # ========================================================
    # 🧬 Biotime Logs
    # ========================================================
    path(
        "biotime/sync-logs/",
        company_biotime_sync_logs,
        name="company_biotime_sync_logs",
    ),

    # ========================================================
    # 📈 Performance Center
    # ========================================================
    path(
        "performance/dashboard/",
        performance_dashboard,
        name="performance_dashboard",
    ),
    path(
        "performance/templates/",
        performance_templates_list,
        name="performance_templates_list",
    ),
    path(
        "performance/templates/create/",
        performance_template_create,
        name="performance_template_create",
    ),
    path(
        "performance/reviews/",
        performance_reviews_list,
        name="performance_reviews_list",
    ),
    path(
        "performance/reviews/create/",
        performance_review_create,
        name="performance_review_create",
    ),
    path(
        "performance/reviews/<int:review_id>/",
        performance_review_detail,
        name="performance_review_detail",
    ),
    path(
        "performance/reviews/<int:review_id>/submit-self/",
        performance_submit_self,
        name="performance_submit_self",
    ),
    path(
        "performance/reviews/<int:review_id>/submit-manager/",
        performance_submit_manager,
        name="performance_submit_manager",
    ),
    path(
        "performance/reviews/<int:review_id>/submit-hr/",
        performance_submit_hr,
        name="performance_submit_hr",
    ),
    path(
        "performance/reviews/<int:review_id>/workflow/",
        performance_workflow_status,
        name="performance_workflow_status",
    ),
    path(
        "performance/employees/lookup/",
        performance_employees_lookup,
        name="performance_employees_lookup",
    ),

    # ========================================================
    # 🔔 Company Notifications
    # ========================================================
    path(
        "notifications/",
        notifications_list,
        name="company_notifications",
    ),
    path(
        "notifications/read/<int:notification_id>/",
        mark_notification_read,
        name="company_notification_read",
    ),
    path(
        "notifications/read-all/",
        mark_all_notifications_read,
        name="company_notifications_read_all",
    ),

    # ========================================================
    # 💬 Company WhatsApp
    # ========================================================
    path(
        "whatsapp/settings/",
        company_whatsapp_settings,
        name="company_whatsapp_settings",
    ),
    path(
        "whatsapp/settings/update/",
        company_whatsapp_settings_update,
        name="company_whatsapp_settings_update",
    ),
    path(
        "whatsapp/status/",
        company_whatsapp_status,
        name="company_whatsapp_status",
    ),
    path(
        "whatsapp/logs/",
        company_whatsapp_logs,
        name="company_whatsapp_logs",
    ),
    path(
        "whatsapp/templates/",
        company_whatsapp_templates,
        name="company_whatsapp_templates",
    ),

    # --------------------------------------------------------
    # ✅ CRUD routes for company templates
    # --------------------------------------------------------
    path(
        "whatsapp/templates/create/",
        company_whatsapp_template_create,
        name="company_whatsapp_template_create",
    ),
    path(
        "whatsapp/templates/<int:template_id>/update/",
        company_whatsapp_template_update,
        name="company_whatsapp_template_update",
    ),
    path(
        "whatsapp/templates/<int:template_id>/toggle/",
        company_whatsapp_template_toggle,
        name="company_whatsapp_template_toggle",
    ),
    path(
        "whatsapp/templates/<int:template_id>/delete/",
        company_whatsapp_template_delete,
        name="company_whatsapp_template_delete",
    ),

    path(
        "whatsapp/send-test/",
        company_whatsapp_send_test,
        name="company_whatsapp_send_test",
    ),
    path(
        "whatsapp/session/create-qr/",
        company_whatsapp_session_create_qr,
        name="company_whatsapp_session_create_qr",
    ),
    path(
        "whatsapp/session/create-pairing-code/",
        company_whatsapp_session_create_pairing_code,
        name="company_whatsapp_session_create_pairing_code",
    ),
    path(
        "whatsapp/session/disconnect/",
        company_whatsapp_session_disconnect,
        name="company_whatsapp_session_disconnect",
    ),

    # --------------------------------------------------------
    # ✅ Alias routes without trailing slash
    # --------------------------------------------------------
    path(
        "whatsapp/settings",
        company_whatsapp_settings,
        name="company_whatsapp_settings_no_slash",
    ),
    path(
        "whatsapp/settings/update",
        company_whatsapp_settings_update,
        name="company_whatsapp_settings_update_no_slash",
    ),
    path(
        "whatsapp/status",
        company_whatsapp_status,
        name="company_whatsapp_status_no_slash",
    ),
    path(
        "whatsapp/logs",
        company_whatsapp_logs,
        name="company_whatsapp_logs_no_slash",
    ),
    path(
        "whatsapp/templates",
        company_whatsapp_templates,
        name="company_whatsapp_templates_no_slash",
    ),

    # --------------------------------------------------------
    # ✅ CRUD aliases without trailing slash
    # --------------------------------------------------------
    path(
        "whatsapp/templates/create",
        company_whatsapp_template_create,
        name="company_whatsapp_template_create_no_slash",
    ),
    path(
        "whatsapp/templates/<int:template_id>/update",
        company_whatsapp_template_update,
        name="company_whatsapp_template_update_no_slash",
    ),
    path(
        "whatsapp/templates/<int:template_id>/toggle",
        company_whatsapp_template_toggle,
        name="company_whatsapp_template_toggle_no_slash",
    ),
    path(
        "whatsapp/templates/<int:template_id>/delete",
        company_whatsapp_template_delete,
        name="company_whatsapp_template_delete_no_slash",
    ),

    path(
        "whatsapp/send-test",
        company_whatsapp_send_test,
        name="company_whatsapp_send_test_no_slash",
    ),
    path(
        "whatsapp/session/create-qr",
        company_whatsapp_session_create_qr,
        name="company_whatsapp_session_create_qr_no_slash",
    ),
    path(
        "whatsapp/session/create-pairing-code",
        company_whatsapp_session_create_pairing_code,
        name="company_whatsapp_session_create_pairing_code_no_slash",
    ),
    path(
        "whatsapp/session/disconnect",
        company_whatsapp_session_disconnect,
        name="company_whatsapp_session_disconnect_no_slash",
    ),

        # ========================================================
    # 💰 Payroll
    # ========================================================
    path(
        "payroll/runs/",
        PayrollRunListAPIView.as_view(),
        name="company_payroll_runs_list",
    ),
    path(
        "payroll/runs/create/",
        PayrollRunCreateAPIView.as_view(),
        name="company_payroll_runs_create",
    ),
    path(
        "payroll/runs/<int:run_id>/",
        PayrollRunDetailAPIView.as_view(),
        name="company_payroll_run_detail",
    ),
    path(
        "payroll/runs/<int:run_id>/calculate/",
        PayrollRunCalculateAPIView.as_view(),
        name="company_payroll_run_calculate",
    ),
    path(
        "payroll/runs/<int:run_id>/approve/",
        PayrollRunApproveAPIView.as_view(),
        name="company_payroll_run_approve",
    ),
    path(
        "payroll/runs/<int:run_id>/reset/",
        PayrollRunResetAPIView.as_view(),
        name="company_payroll_run_reset",
    ),
    path(
        "payroll/runs/<int:run_id>/pay/",
        PayrollRunPayAPIView.as_view(),
        name="company_payroll_run_pay",
    ),

    path(
        "payroll/runs/<int:run_id>/records/",
        PayrollRunRecordsListAPIView.as_view(),
        name="company_payroll_run_records",
    ),
    path(
        "payroll/records/<int:record_id>/",
        PayrollRecordDetailAPIView.as_view(),
        name="company_payroll_record_detail",
    ),
    path(
        "payroll/records/<int:record_id>/ledger/",
        PayrollRecordLedgerAPIView.as_view(),
        name="company_payroll_record_ledger",
    ),
    path(
        "payroll/records/<int:record_id>/pay/",
        PayrollRecordPayAPIView.as_view(),
        name="company_payroll_record_pay",
    ),
    path(
        "payroll/slip/<int:record_id>/",
        CompanyPayrollSalarySlipAPIView.as_view(),
        name="company_payroll_salary_slip",
    ),
    
]