# ============================================================
# 📂 api/urls.py
# ⚙️ Version: V16.9.25 FINAL — ONBOARDING FULL FLOW WIRED 🔒
# Primey HR Cloud
# ============================================================

from django.urls import path
from django.views.decorators.csrf import csrf_exempt

# ============================================================
# 📦 Core
# ============================================================
from api import views

# ============================================================
# 🔐 AUTH
# ============================================================
from api.auth.login import login_api
from api.auth.logout import logout_api
from api.auth.whoami import apiWhoAmI
from api.auth.csrf import csrf

# ============================================================
# 🟦 SYSTEM — CORE
# ============================================================
from api.system.dashboard import system_dashboard
from api.system.impersonation import start_impersonation, stop_impersonation
from api.system.health import system_health
from api.system.devices import devices_overview

# ============================================================
# 🟦 SYSTEM — COMPANIES
# ============================================================
from api.system.companies import (
    companies_overview,
    companies_list,
    company_detail,
    company_create,
)

# ============================================================
# 🟦 SYSTEM — COMPANY STATUS ACTIONS
# ============================================================
from api.system.actions.company_status import (
    activate_company,
    suspend_company,
    reactivate_company,
)

# ============================================================
# 🟦 SYSTEM — USERS
# ============================================================
from api.system.users import users_list, users_overview

# ============================================================
# 🟦 SYSTEM — USERS ACTIONS
# ============================================================
from api.system.users_actions import (
    toggle_user_status,
    change_user_role,
    reset_user_password,
    delete_user,
    create_company_user,
)

# ============================================================
# 🧾 SYSTEM — INVOICES & BILLING
# ============================================================
from api.system.billing.system_invoices import system_invoices
from api.system.billing.invoice_detail import invoice_detail
from api.system.billing.company_invoices import company_invoices
from api.system.billing.company_subscription_invoices import (
    company_subscription_invoices,
)
from api.system.billing.company_subscription import company_subscription_detail
from api.system.billing.subscriptions import list_billing_subscriptions
from api.system.billing_v3 import billing_overview

# ============================================================
# 🟦 SYSTEM — SUBSCRIPTIONS
# ============================================================
from api.system.subscriptions.preview import subscription_preview

# ============================================================
# 🟦 SYSTEM — PAYMENTS
# ============================================================
from api.system.payments_list import list_payments
from api.system.payments_detail import payment_detail
from api.system.payments_views import latest_payments
from api.system.payments.confirm_cash_payment import confirm_cash_payment

# ============================================================
# 🟦 SYSTEM — PLANS & DISCOUNTS
# ============================================================
from api.system.plans import plans_list, plan_create, plan_update
from api.system.discounts import (
    system_discounts,
    update_discount,
    toggle_discount_status,
)

# ============================================================
# 🟦 SYSTEM — SETTINGS
# ============================================================
from api.system.settings import (
    system_settings_api,
    update_system_setting_api,
)

# ============================================================
# 🟦 SYSTEM — MONITORING
# ============================================================
from api.system.monitoring.logs import monitoring_logs, monitoring_log_detail
from api.system.monitoring.metrics import monitoring_metrics

# ============================================================
# 🟦 SYSTEM — ATTENDANCE
# ============================================================
from api.system.attendance import (
    system_attendance_overview,
    pause_attendance_scheduler,
    resume_attendance_scheduler,
)

# ============================================================
# 🟦 SYSTEM — LEAVES
# ============================================================
from api.system.leaves import (
    system_leaves_overview,
    system_leave_types,
    reset_leave_balances,
)

# ============================================================
# 🔔 SYSTEM — NOTIFICATIONS
# ============================================================
from api.system.notifications import (
    notifications_list,
    mark_notification_read,
    mark_all_notifications_read,
)

# ============================================================
# 🟦 SYSTEM — ONBOARDING
# ============================================================
from api.system.onboarding.create_draft import create_onboarding_draft
from api.system.onboarding.confirm_payment import confirm_onboarding_payment

# ============================================================
# 🏢 COMPANY — EMPLOYEES / CORE
# ============================================================
from api.company.employee import (
    employees_list,
    employee_detail,
    employee_create,
    employee_update,
    employee_profile_update,
    employee_toggle_status,
    employee_history,
    employee_link_biotime,
    employee_assign_work_schedule,   # ✅ Phase F.3
)

from api.company.employee_user import link_employee_user
from api.company.users_unlinked import company_users_unlinked
from api.company.roles import roles_list, role_preview
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

# ============================================================
# 🏢 COMPANY — BRANCHES
# ============================================================
from api.company.branches import (
    branches_list,
    branch_create,
    branch_update,
)

# ============================================================
# 🏢 COMPANY — ATTENDANCE
# ============================================================
from api.company.attendance import (
    attendance_dashboard,
    attendance_records,
    attendance_sync,
    attendance_unmapped_logs,
    attendance_reports_preview,
    employee_attendance_preview,

    # 📄 Company Level Policy
    company_attendance_policy,

    # ✅ Phase F.2 — WorkSchedule CRUD
    work_schedules,
    work_schedule_detail,
    work_schedule_toggle,
)

# ============================================================
# 🏢 COMPANY — LEAVES
# ============================================================
from api.company.leaves import (
    company_leave_requests,
    create_leave_request,
    approve_leave,
    reject_leave,
    leave_balance,
)
from api.company.activity_snapshot import activity_snapshot

# ============================================================
# 🧬 COMPANY — BIOTIME
# ============================================================
from api.company.biotime.devices import (
    company_biotime_devices,
    company_biotime_device_detail,
    company_biotime_sync_devices,
    company_biotime_sync_single_device,
    company_biotime_test_single_device,
)

from api.company.biotime.biotime import (
    company_biotime_sync_logs,
    company_biotime_test_connection,
    company_biotime_save_settings,
    company_biotime_sync_employees,
    company_biotime_employees,
    company_biotime_link_employees,
    company_biotime_push_employee,
    company_biotime_append_employee_area,
)

app_name = "api"

# ============================================================
# 🌐 URLPATTERNS — FINAL & LOCKED 🔒
# ============================================================
urlpatterns = [

    # ❤️ HEALTH
    path("health/", views.health_check),

    # ========================================================
    # 🔐 AUTH
    # ========================================================
    path("auth/csrf/", csrf),
    path("auth/login/", login_api),
    path("auth/logout/", logout_api),
    path("auth/whoami/", apiWhoAmI),
    path("auth/whoami", apiWhoAmI),
    path("whoami/", apiWhoAmI),
    path("whoami", apiWhoAmI),

    # ========================================================
    # 🟦 SYSTEM — CORE
    # ========================================================
    path("system/dashboard/", system_dashboard),
    path("system/health/", system_health),
    path("system/devices/overview/", devices_overview),
    path("system/impersonation/start/", start_impersonation),
    path("system/impersonation/stop/", stop_impersonation),

    # ========================================================
    # 🟦 SYSTEM — COMPANIES
    # ========================================================
    path("system/companies/overview/", companies_overview),
    path("system/companies/list/", companies_list),
    path("system/companies/create/", company_create),
    path("system/companies/<int:company_id>/", company_detail),

    # ========================================================
    # 🏢 SYSTEM — COMPANY STATUS ACTIONS
    # ========================================================
    path("system/companies/actions/activate/", activate_company),
    path("system/companies/actions/suspend/", suspend_company),
    path("system/companies/actions/reactivate/", reactivate_company),

    # ========================================================
    # 👥 SYSTEM — USERS
    # ========================================================
    path("system/users/", users_list),
    path("system/users/overview/", users_overview),
    path("system/companies/<int:company_id>/users/", users_list),

    # ========================================================
    # 👤 SYSTEM — USERS ACTIONS
    # ========================================================
    path("system/users/actions/create/", create_company_user),
    path("system/users/actions/change-role/", change_user_role),
    path("system/users/actions/reset-password/", reset_user_password),
    path("system/users/actions/toggle-status/", toggle_user_status),
    path("system/users/actions/delete/", delete_user),

    # ========================================================
    # 🧾 SYSTEM — INVOICES
    # ========================================================
    path("system/invoices/", system_invoices),
    path("system/invoices/<int:invoice_id>/", invoice_detail),
    path("system/companies/<int:company_id>/invoices/", company_invoices),
    path(
        "system/companies/<int:company_id>/subscription/invoices/",
        company_subscription_invoices,
    ),
    path(
        "system/subscriptions/<int:subscription_id>/",
        company_subscription_detail,
    ),

    # ========================================================
    # 📦 SYSTEM — BILLING
    # ========================================================
    path("system/billing/subscriptions/", list_billing_subscriptions),
    path("system/billing/", billing_overview),

    # ========================================================
    # 🧾 SYSTEM — SUBSCRIPTIONS (PREVIEW)
    # ========================================================
    path("system/subscriptions/preview/", subscription_preview),
    path("system/subscriptions/preview", subscription_preview),

    # ========================================================
    # 🟦 SYSTEM — PAYMENTS
    # ========================================================
    path("system/payments/", list_payments),
    path("system/payments/latest/", latest_payments),
    path("system/payments/<int:payment_id>/", payment_detail),
    path("system/payments/confirm-cash/", confirm_cash_payment),

    # ========================================================
    # 🟦 SYSTEM — PLANS
    # ========================================================
    path("system/plans/", plans_list),
    path("system/plans/create/", plan_create),
    path("system/plans/<int:plan_id>/update/", plan_update),

    # ========================================================
    # 🔔 SYSTEM — NOTIFICATIONS
    # ========================================================
    path("system/notifications/", notifications_list),
    path("system/notifications/mark-read/", mark_notification_read),
    path("system/notifications/mark-all-read/", mark_all_notifications_read),

    # ========================================================
    # 🟦 SYSTEM — SETTINGS
    # ========================================================
    path("system/settings/", system_settings_api),
    path("system/settings", system_settings_api),
    path("system/settings/update/", update_system_setting_api),

    # ========================================================
    # 🟦 SYSTEM — ONBOARDING
    # ========================================================
    path("system/onboarding/create-draft/", csrf_exempt(create_onboarding_draft)),
    path("system/onboarding/create-draft", csrf_exempt(create_onboarding_draft)),
    path("system/onboarding/confirm-payment/", csrf_exempt(confirm_onboarding_payment)),
    path("system/onboarding/confirm-payment", csrf_exempt(confirm_onboarding_payment)),

    # ========================================================
    # 🟦 SYSTEM — MONITORING
    # ========================================================
    path("system/monitoring/logs/", monitoring_logs),
    path("system/monitoring/logs/<int:log_id>/", monitoring_log_detail),
    path("system/monitoring/metrics/", monitoring_metrics),

    # ========================================================
    # 🟦 SYSTEM — ATTENDANCE
    # ========================================================
    path("system/attendance/", system_attendance_overview),
    path("system/attendance/pause/", pause_attendance_scheduler),
    path("system/attendance/resume/", resume_attendance_scheduler),

    # ========================================================
    # 🟦 SYSTEM — LEAVES
    # ========================================================
    path("system/leaves/", system_leaves_overview),
    path("system/leaves/types/", system_leave_types),
    path("system/leaves/reset-balances/", reset_leave_balances),

    # ========================================================
    # 🏢 COMPANY — EMPLOYEES
    # ========================================================
    path("company/employees/", employees_list),
    path("company/employees/create/", csrf_exempt(employee_create)),
    path("company/employees/create", csrf_exempt(employee_create)),
    path("company/employees/<int:employee_id>/", employee_detail),
    path("company/employees/<int:employee_id>/update/", employee_update),
    path("company/employees/<int:employee_id>/profile-update/", employee_profile_update),
    path("company/employees/<int:employee_id>/history/", employee_history),
    path("company/employees/<int:employee_id>/toggle-status/", employee_toggle_status),
    path("company/employees/<int:employee_id>/link-biotime/", csrf_exempt(employee_link_biotime)),
    path("company/employees/<int:employee_id>/link-biotime", csrf_exempt(employee_link_biotime)),
    path("company/employees/link-user/", link_employee_user),
    path("company/users/unlinked/", company_users_unlinked),

    # ✅ Phase F.3 — Assign Work Schedule To Employee
    path(
        "company/employees/<int:employee_id>/assign-work-schedule/",
        csrf_exempt(employee_assign_work_schedule),
    ),

    # ========================================================
    # 🏢 COMPANY — ROLES
    # ========================================================
    path("company/roles/", roles_list),
    path("company/roles/preview/", role_preview),

    # ========================================================
    # 🏢 COMPANY — DEPARTMENTS
    # ========================================================
    path("company/departments/", departments_list),
    path("company/departments", departments_list),
    path("company/departments/create/", department_create),
    path("company/departments/create", department_create),
    path("company/departments/<int:department_id>/update/", department_update),
    path("company/departments/<int:department_id>/update", department_update),

    # ========================================================
    # 🏢 COMPANY — JOB TITLES
    # ========================================================
    path("company/job-titles/", job_titles_list),
    path("company/job-titles", job_titles_list),
    path("company/job-titles/create/", job_title_create),
    path("company/job-titles/create", job_title_create),
    path("company/job-titles/<int:job_title_id>/update/", job_title_update),
    path("company/job-titles/<int:job_title_id>/update", job_title_update),

    # ========================================================
    # 🏢 COMPANY — BRANCHES
    # ========================================================
    path("company/branches/", branches_list),
    path("company/branches", branches_list),
    path("company/branches/create/", branch_create),
    path("company/branches/create", branch_create),
    path("company/branches/<int:branch_id>/update/", branch_update),
    path("company/branches/<int:branch_id>/update", branch_update),

    # ========================================================
    # 🏢 COMPANY — ATTENDANCE
    # ========================================================
    path(
        "company/attendance/policy/",
        company_attendance_policy,
    ),

    path("company/attendance/dashboard/", attendance_dashboard),
    path("company/attendance/records/", attendance_records),
    path("company/attendance/sync/", attendance_sync),
    path("company/attendance/unmapped-logs/", attendance_unmapped_logs),
    path("company/attendance/reports/preview/", attendance_reports_preview),
    path("company/employees/<int:employee_id>/attendance-preview/", employee_attendance_preview),

    # ✅ Phase F.2 — Work Schedules CRUD
    path("company/attendance/schedules/", work_schedules),
    path("company/attendance/schedules/<int:schedule_id>/", work_schedule_detail),
    path("company/attendance/schedules/<int:schedule_id>/toggle/", work_schedule_toggle),

    # ========================================================
    # 🏢 COMPANY — LEAVES
    # ========================================================
    path("company/leaves/", company_leave_requests),
    path("company/leaves/create/", create_leave_request),
    path("company/leaves/approve/", approve_leave),
    path("company/leaves/reject/", reject_leave),
    path("company/leaves/balance/", leave_balance),

    # ========================================================
    # 🏢 COMPANY — SNAPSHOT
    # ========================================================
    path("company/activity-snapshot/", activity_snapshot),

    # ========================================================
    # 🔌 COMPANY — BIOTIME
    # ========================================================
    path("company/biotime/devices/", company_biotime_devices),
    path("company/biotime/devices/<int:device_id>/", company_biotime_device_detail),
    path("company/biotime/devices/<int:device_id>/sync/", csrf_exempt(company_biotime_sync_single_device)),
    path("company/biotime/devices/<int:device_id>/test/", csrf_exempt(company_biotime_test_single_device)),
    path("company/biotime/sync-devices/", csrf_exempt(company_biotime_sync_devices)),
    path("company/biotime/sync-devices", csrf_exempt(company_biotime_sync_devices)),
    path("company/biotime/sync-employees/", csrf_exempt(company_biotime_sync_employees)),
    path("company/biotime/sync-employees", csrf_exempt(company_biotime_sync_employees)),
    path("company/biotime/test-connection/", csrf_exempt(company_biotime_test_connection)),
    path("company/biotime/test-connection", csrf_exempt(company_biotime_test_connection)),
    path("company/biotime/save-settings/", csrf_exempt(company_biotime_save_settings)),
    path("company/biotime/save-settings", csrf_exempt(company_biotime_save_settings)),
    path("company/biotime/sync-logs/", company_biotime_sync_logs),
    path("company/biotime/sync-logs", company_biotime_sync_logs),

    # 👥 Biotime Employees (READ ONLY)
    path("company/biotime/employees/", company_biotime_employees, name="company_biotime_employees"),
    path("company/biotime/employees", company_biotime_employees, name="company_biotime_employees_no_slash"),

    # ========================================================
    # 🔗 BIOTIME — BULK LINK EMPLOYEES
    # ========================================================
    path("company/biotime/link-employees/", csrf_exempt(company_biotime_link_employees), name="company_biotime_link_employees"),
    path("company/biotime/link-employees", csrf_exempt(company_biotime_link_employees), name="company_biotime_link_employees_no_slash"),

    # ========================================================
    # 🚀 BIOTIME — PUSH EMPLOYEE
    # ========================================================
    path(
        "company/biotime/push-employee/<int:employee_id>/",
        csrf_exempt(company_biotime_push_employee),
        name="company_biotime_push_employee",
    ),

    # ========================================================
    # ➕ BIOTIME — APPEND AREA (Phase E.1)
    # ========================================================
    path(
        "company/biotime/append-area/<int:employee_id>/",
        csrf_exempt(company_biotime_append_employee_area),
        name="company_biotime_append_employee_area",
    ),
]
