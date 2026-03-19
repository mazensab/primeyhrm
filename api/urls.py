# ============================================================
# 📂 api/urls.py
# ⚙️ CLEAN ROOT ROUTER
# Primey HR Cloud
# ============================================================

from django.urls import path, include

# ============================================================
# 🔐 AUTH
# ============================================================

from api.auth.login import login_api, csrf_api
from api.auth.logout import logout_api
from api.auth.whoami import apiWhoAmI
from api.auth.profile_update import profile_update
# ------------------------------------------------------------
# 👤 PROFILE
# ------------------------------------------------------------

from api.auth.activity import user_activity
from api.auth.sessions import user_sessions
from api.system.my_companies import my_companies

# ============================================================
# 🏢 COMPANY
# ============================================================

from api.company.employee import switch_company
from api.system.onboarding.create_draft import create_onboarding_draft
from api.system.onboarding.draft_detail import draft_detail
from api.system.invoices.invoices_list import system_invoices_list

from api.system.onboarding.pending_drafts import pending_onboarding_drafts
# ============================================================
# 👥 SYSTEM — INTERNAL USERS
# ============================================================

from api.system.users.users import (
    system_users_list,
    system_user_roles,
    system_user_create,
    system_user_toggle_status,
    system_user_change_role,
    system_user_reset_password,
    system_user_delete,
)

from api.system.whatsapp.settings import (
    system_whatsapp_settings,
    system_whatsapp_settings_update,
)
from api.system.whatsapp.status import (
    system_whatsapp_status,
    system_whatsapp_session_create_qr,
    system_whatsapp_session_create_pairing_code,
    system_whatsapp_session_disconnect,
)
from api.system.whatsapp.logs import system_whatsapp_logs
from api.system.whatsapp.templates import (
    system_whatsapp_templates,
    system_whatsapp_template_create,
    system_whatsapp_template_update,
    system_whatsapp_template_toggle,
    system_whatsapp_template_delete,
)
from api.system.whatsapp.send_test import system_whatsapp_send_test
from api.system.whatsapp.broadcasts import (
    system_whatsapp_broadcasts,
    system_whatsapp_broadcast_create,
    system_whatsapp_broadcast_detail,
    system_whatsapp_broadcast_execute,
)

from api.system.whatsapp.webhook import (
    system_whatsapp_webhook_verify,
    system_whatsapp_webhook_receive,
)

# ============================================================
# 📦 SYSTEM — SUBSCRIPTIONS
# ============================================================

from api.system.subscriptions.subscriptions_list import subscriptions_list
from api.system.subscriptions.subscription_detail import system_subscription_detail
from api.system.invoices.invoice_detail import system_invoice_detail
from api.system.billing.invoice_preview import invoice_preview
from api.system.onboarding.confirm_draft import confirm_draft
from api.system.onboarding.confirm_payment import confirm_onboarding_payment
from api.system.invoices.public_invoice import public_invoice_detail
from api.system.subscriptions.renew_subscription import renew_subscription
from api.system.payments.confirm_cash_payment import confirm_cash_payment
from api.system.subscriptions.change_plan import change_subscription_plan
from api.system.subscriptions.preview_plan_change import preview_plan_change
from api.auth.avatar_upload import avatar_upload
from api.auth.change_password import change_password
from api.auth.resetguest_password import resetguest_password


# ============================================================
# 📦 SYSTEM — PLANS
# ============================================================

from api.system.plans.plans import (
    system_plans_list,
    plans_list,
    plan_create,
    plan_update,
)

# ============================================================
# ⚙️ SYSTEM SETTINGS
# ============================================================

from api.system.settings import (
    system_settings_api,
    update_system_setting_api,
    test_email_settings_api,
)

from api.system.notifications import (
    notifications_list,
    mark_notification_read,
    mark_all_notifications_read,
)

# ============================================================
# 🎟 SYSTEM — DISCOUNTS
# ============================================================

from api.system.discounts import (
    system_discounts,
    update_discount,
    toggle_discount_status,
)

# ============================================================
# 🩺 HEALTH
# ============================================================
from api.public.contact import public_contact_submit

from api import views


app_name = "api"


# ============================================================
# 🌐 URLPATTERNS
# ============================================================

urlpatterns = [

    # --------------------------------------------------------
    # 🩺 HEALTH
    # --------------------------------------------------------
    path("health/", views.health_check),

    path("company/", include("api.company.urls")),

    # --------------------------------------------------------
    # 🔐 AUTH
    # --------------------------------------------------------
    path("auth/csrf/", csrf_api),
    path("auth/login/", login_api),
    path("auth/logout/", logout_api),

    path("auth/whoami/", apiWhoAmI),
    path("whoami/", apiWhoAmI),

    path(
        "auth/change-password/",
        change_password,
        name="change_password",
    ),

    path(
        "auth/resetguest-password/",
        resetguest_password,
        name="resetguest_password",
    ),

    path(
        "auth/profile/update/",
        profile_update,
        name="profile_update",
    ),

    # --------------------------------------------------------
    # 👤 PROFILE
    # --------------------------------------------------------
    path(
        "auth/activity/",
        user_activity,
    ),

    path(
        "auth/sessions/",
        user_sessions,
    ),

    path(
        "system/my-companies/",
        my_companies,
    ),

    # --------------------------------------------------------
    # 🏢 SWITCH COMPANY
    # --------------------------------------------------------
    path("company/switch/", switch_company),

    # --------------------------------------------------------
    # 👥 SYSTEM — INTERNAL USERS
    # --------------------------------------------------------
    path(
        "system/users/",
        system_users_list,
        name="system_users_list",
    ),

    path(
        "system/users/roles/",
        system_user_roles,
        name="system_user_roles",
    ),

    path(
        "system/users/create/",
        system_user_create,
        name="system_user_create",
    ),

    path(
        "system/users/toggle-status/",
        system_user_toggle_status,
        name="system_user_toggle_status",
    ),

    path(
        "system/users/change-role/",
        system_user_change_role,
        name="system_user_change_role",
    ),

    path(
        "system/users/reset-password/",
        system_user_reset_password,
        name="system_user_reset_password",
    ),

    path(
        "system/users/delete/",
        system_user_delete,
        name="system_user_delete",
    ),

    # --------------------------------------------------------
    # 🟦 SYSTEM — COMPANIES
    # --------------------------------------------------------
    path(
        "system/companies/",
        include("api.system.companies.urls"),
    ),

    # --------------------------------------------------------
    # 🧾 SYSTEM — BILLING
    # --------------------------------------------------------
    path(
        "system/billing/",
        include("api.system.billing.urls"),
    ),

    # --------------------------------------------------------
    # 💳 SYSTEM — PAYMENTS
    # --------------------------------------------------------
    path(
        "system/payments/",
        include("api.system.payments.urls"),
    ),

    # --------------------------------------------------------
    # 📦 SYSTEM — PLANS
    # --------------------------------------------------------
    path(
        "system/plans/",
        system_plans_list,
        name="system_plans_list",
    ),

    path(
        "system/plans/admin/",
        plans_list,
        name="plans_list",
    ),

    path(
        "system/plans/create/",
        plan_create,
        name="plan_create",
    ),

    path(
        "system/plans/<int:plan_id>/update/",
        plan_update,
        name="plan_update",
    ),

    # --------------------------------------------------------
    # 📦 SYSTEM — SUBSCRIPTIONS
    # --------------------------------------------------------
    path(
        "system/subscriptions/",
        subscriptions_list,
        name="system-subscriptions",
    ),

    path(
        "system/subscriptions/<int:subscription_id>/",
        system_subscription_detail,
    ),

    path(
        "system/invoices/",
        system_invoices_list,
        name="system_invoices_list",
    ),

    path(
        "system/invoices/<str:invoice_number>/",
        system_invoice_detail,
        name="system_invoice_detail"
    ),

    # --------------------------------------------------------
    # 🎟 SYSTEM — DISCOUNTS
    # --------------------------------------------------------
    path(
        "system/discounts/",
        system_discounts,
        name="system_discounts",
    ),

    path(
        "system/discounts/<int:discount_id>/",
        update_discount,
        name="update_discount",
    ),

    path(
        "system/discounts/<int:discount_id>/toggle/",
        toggle_discount_status,
        name="toggle_discount_status",
    ),

    # --------------------------------------------------------
    # 🔔 SYSTEM — NOTIFICATIONS
    # --------------------------------------------------------
    path(
        "system/notifications/",
        notifications_list,
        name="system_notifications",
    ),

    path(
        "system/notifications/read/<int:notification_id>/",
        mark_notification_read,
        name="system_notification_read",
    ),

    path(
        "system/notifications/read-all/",
        mark_all_notifications_read,
        name="system_notifications_read_all",
    ),

    # ============================================================
    # ⚙️ SYSTEM SETTINGS
    # ============================================================
    path(
        "system/settings/",
        system_settings_api,
    ),

    path(
        "system/settings/update/",
        update_system_setting_api,
    ),

    path(
        "system/billing/preview/",
        invoice_preview
    ),

    # ============================================================
    # 🏢 SYSTEM — ONBOARDING
    # ============================================================
    path(
        "system/onboarding/create-draft/",
        create_onboarding_draft,
    ),

    path(
        "system/onboarding/confirm-draft/",
        confirm_draft,
    ),

    path(
        "system/onboarding/confirm-payment/",
        confirm_onboarding_payment,
    ),

    path(
        "public/invoice/<str:number>/",
        public_invoice_detail
    ),

    path(
        "public/contact/",
        public_contact_submit,
        name="public_contact_submit",
    ),

    path(
        "system/onboarding/draft/<int:draft_id>/",
        draft_detail
    ),

    path(
        "system/subscriptions/<int:subscription_id>/renew/",
        renew_subscription,
    ),

    path(
        "system/payments/confirm-cash/",
        confirm_cash_payment
    ),

    path(
        "system/subscriptions/<int:subscription_id>/change-plan/",
        change_subscription_plan
    ),

    path(
        "system/subscriptions/<int:subscription_id>/preview-plan-change/",
        preview_plan_change
    ),

    path(
        "auth/avatar/upload/",
        avatar_upload,
        name="avatar_upload"
    ),

    path(
        "system/settings/email/test/",
        test_email_settings_api,
    ),

    # --------------------------------------------------------
    # 💬 SYSTEM — WHATSAPP
    # --------------------------------------------------------
    path(
        "system/whatsapp/settings/",
        system_whatsapp_settings,
        name="system_whatsapp_settings",
    ),
    path(
        "system/whatsapp/settings/update/",
        system_whatsapp_settings_update,
        name="system_whatsapp_settings_update",
    ),
    path(
        "system/whatsapp/status/",
        system_whatsapp_status,
        name="system_whatsapp_status",
    ),
    path(
        "system/whatsapp/logs/",
        system_whatsapp_logs,
        name="system_whatsapp_logs",
    ),
    path(
        "system/whatsapp/templates/",
        system_whatsapp_templates,
        name="system_whatsapp_templates",
    ),
    path(
        "system/whatsapp/templates/create/",
        system_whatsapp_template_create,
        name="system_whatsapp_template_create",
    ),
    path(
        "system/whatsapp/templates/<int:template_id>/update/",
        system_whatsapp_template_update,
        name="system_whatsapp_template_update",
    ),
    path(
        "system/whatsapp/templates/<int:template_id>/toggle/",
        system_whatsapp_template_toggle,
        name="system_whatsapp_template_toggle",
    ),
    path(
        "system/whatsapp/templates/<int:template_id>/delete/",
        system_whatsapp_template_delete,
        name="system_whatsapp_template_delete",
    ),
    path(
        "system/whatsapp/send-test/",
        system_whatsapp_send_test,
        name="system_whatsapp_send_test",
    ),
    path(
        "system/whatsapp/broadcasts/",
        system_whatsapp_broadcasts,
        name="system_whatsapp_broadcasts",
    ),
    path(
        "system/whatsapp/broadcasts/create/",
        system_whatsapp_broadcast_create,
        name="system_whatsapp_broadcast_create",
    ),
    path(
        "system/whatsapp/session/create-qr/",
        system_whatsapp_session_create_qr,
        name="system_whatsapp_session_create_qr",
    ),
    path(
        "system/whatsapp/session/create-pairing-code/",
        system_whatsapp_session_create_pairing_code,
        name="system_whatsapp_session_create_pairing_code",
    ),
    path(
        "system/whatsapp/session/disconnect/",
        system_whatsapp_session_disconnect,
        name="system_whatsapp_session_disconnect",
    ),
    path(
        "system/whatsapp/webhook/",
        system_whatsapp_webhook_verify,
        name="system_whatsapp_webhook_verify",
    ),
    path(
        "system/whatsapp/webhook/receive/",
        system_whatsapp_webhook_receive,
        name="system_whatsapp_webhook_receive",
    ),

    path(
        "system/whatsapp/broadcasts/<int:broadcast_id>/",
        system_whatsapp_broadcast_detail,
        name="system_whatsapp_broadcast_detail",
    ),
    path(
        "system/whatsapp/broadcasts/<int:broadcast_id>/execute/",
        system_whatsapp_broadcast_execute,
        name="system_whatsapp_broadcast_execute",
    ),

    path(
        "system/onboarding/pending-drafts/",
        pending_onboarding_drafts,
        name="pending_onboarding_drafts",
    ),




]