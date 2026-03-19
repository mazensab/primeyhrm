# ============================================================
# 🏢 System Companies URLs
# ============================================================

from django.urls import path

from .overview import companies_overview
from .list import companies_list
from .detail import (
    system_company_detail,
    system_company_activity,
    system_company_update,
)
from .create import company_create
from .toggle import toggle_company_active
from .users import (
    system_company_users,
    system_company_user_update,
    system_company_user_change_role,
    system_company_user_toggle_status,
    system_company_user_reset_password,
    system_company_user_enter,
    system_company_exit_session,
)
from .subscription import system_company_subscription
from api.system.invoices.company_invoices import system_company_invoices

urlpatterns = [

    # --------------------------------------------------------
    # 📊 Companies Overview
    # --------------------------------------------------------
    path(
        "overview/",
        companies_overview,
    ),

    # --------------------------------------------------------
    # 📋 Companies List
    # --------------------------------------------------------
    path(
        "list/",
        companies_list,
    ),

    # --------------------------------------------------------
    # ➕ Create Company
    # --------------------------------------------------------
    path(
        "create/",
        company_create,
    ),

    # --------------------------------------------------------
    # 🔎 Company Detail
    # --------------------------------------------------------
    path(
        "<int:company_id>/",
        system_company_detail,
    ),

    # --------------------------------------------------------
    # ✏️ Update Company Information
    # --------------------------------------------------------
    path(
        "<int:company_id>/update/",
        system_company_update,
        name="system_company_update",
    ),

    # --------------------------------------------------------
    # 🔁 Toggle Active
    # --------------------------------------------------------
    path(
        "<int:company_id>/toggle-active/",
        toggle_company_active,
    ),

    # --------------------------------------------------------
    # 👥 Company Users
    # --------------------------------------------------------
    path(
        "<int:company_id>/users/",
        system_company_users,
        name="system_company_users",
    ),
    path(
        "<int:company_id>/users/<int:company_user_id>/update/",
        system_company_user_update,
        name="system_company_user_update",
    ),
    path(
        "<int:company_id>/users/<int:company_user_id>/change-role/",
        system_company_user_change_role,
        name="system_company_user_change_role",
    ),
    path(
        "<int:company_id>/users/<int:company_user_id>/toggle-status/",
        system_company_user_toggle_status,
        name="system_company_user_toggle_status",
    ),
    path(
        "<int:company_id>/users/<int:company_user_id>/reset-password/",
        system_company_user_reset_password,
        name="system_company_user_reset_password",
    ),
    path(
        "<int:company_id>/users/<int:company_user_id>/enter/",
        system_company_user_enter,
        name="system_company_user_enter",
    ),

    # --------------------------------------------------------
    # 🔐 Exit Company Session
    # --------------------------------------------------------
    path(
        "exit-session/",
        system_company_exit_session,
        name="system_company_exit_session",
    ),

    path(
        "<int:company_id>/subscription/",
        system_company_subscription,
        name="system_company_subscription",
    ),

    path(
        "<int:company_id>/invoices/",
        system_company_invoices,
        name="system_company_invoices",
    ),
    path(
        "<int:company_id>/activity/",
        system_company_activity,
    ),

]