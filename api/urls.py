# ============================================================
# 📂 api/urls.py
# ⚙️ Version: V16.9.26 FINAL — CLEAN & STABLE 🔒
# Primey HR Cloud
# ============================================================

from django.urls import path
from django.views.decorators.csrf import csrf_exempt

# ============================================================
# 📦 Core
# ============================================================
from api import views
from api.views import csrf

# ============================================================
# 🔐 AUTH
# ============================================================
from api.auth.login import login_api
from api.auth.logout import logout_api
from api.auth.whoami import apiWhoAmI

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
from api.system.users_actions import (
    toggle_user_status,
    change_user_role,
    reset_user_password,
    delete_user,
    create_company_user,
)

# ============================================================
# 🧾 SYSTEM — BILLING / INVOICES
# ============================================================
from api.system.billing_v3 import billing_overview
from api.system.billing.system_invoices import system_invoices
from api.system.billing.invoice_detail import invoice_detail
from api.system.billing.company_invoices import company_invoices
from api.system.billing.company_subscription_invoices import (
    company_subscription_invoices,
)
from api.system.billing.company_subscription import company_subscription_detail
from api.system.billing.subscriptions import list_billing_subscriptions

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
# 🏢 COMPANY — EMPLOYEES
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
    employee_assign_work_schedule,
    employee_update_job_info,
)

from api.company.employee_user import link_employee_user
from api.company.users_unlinked import company_users_unlinked

# ============================================================
# 🏢 COMPANY — ROLES / DEPARTMENTS / JOB TITLES
# ============================================================
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
    company_attendance_policy,
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
# 🧬 COMPANY — BIOTIME (ACTIVE ONLY ✅)
# ============================================================
from api.company.biotime.devices import (
    company_biotime_devices,
    company_biotime_device_detail,
    company_biotime_sync_devices,
    company_biotime_sync_single_device,
    company_biotime_test_single_device,
)

app_name = "api"

# ============================================================
# 🌐 URLPATTERNS — FINAL & LOCKED 🔒
# ============================================================
urlpatterns = [

    # --------------------------------------------------------
    # 🩺 HEALTH
    # --------------------------------------------------------
    path("health/", views.health_check),

    # --------------------------------------------------------
    # 🔐 AUTH
    # --------------------------------------------------------
    path("auth/csrf/", csrf),
    path("auth/login/", login_api),
    path("auth/logout/", logout_api),
    path("auth/whoami/", apiWhoAmI),
    path("auth/whoami", apiWhoAmI),
    path("whoami/", apiWhoAmI),
    path("whoami", apiWhoAmI),

    # --------------------------------------------------------
    # 🏢 COMPANY — EMPLOYEE JOB INFO
    # --------------------------------------------------------
    path(
        "employees/<int:employee_id>/update-job-info/",
        employee_update_job_info,
    ),

    # (بقية المسارات كما هي بدون أي تغيير)
]
