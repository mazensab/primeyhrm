# ===============================================================
# 📂 الملف: employee_center/urls.py
# 🧭 Employee Center — V25.1 Ultra Pro (FINAL CLEAN)
# ===============================================================

from django.urls import path
from . import views
from . import views_sync

app_name = "employee_center"

urlpatterns = [

    # ===========================================================
    # 🔵 (1) Dashboard
    # ===========================================================
    path(
        "<int:company_id>/dashboard/",
        views.employees_dashboard,
        name="employees_dashboard",
    ),

    # ===========================================================
    # 🔵 (2) Employees
    # ===========================================================
    path(
        "<int:company_id>/employees/",
        views.employees_list,
        name="employees_list",
    ),

    path(
        "<int:company_id>/employees/add/",
        views.employee_add,
        name="employee_add",
    ),

    path(
        "<int:company_id>/employees/<int:employee_id>/",
        views.employee_detail,
        name="employee_detail",
    ),

    path(
        "<int:company_id>/employees/<int:employee_id>/edit/",
        views.employee_edit,
        name="employee_edit",
    ),

    # ===========================================================
    # 🔵 (3) Contracts
    # ===========================================================
    path(
        "<int:company_id>/contracts/",
        views.contracts_list,
        name="contracts_list",
    ),

    path(
        "<int:company_id>/employees/<int:employee_id>/contract/add/",
        views.contract_add,
        name="contract_add",
    ),

    path(
        "<int:company_id>/contracts/<int:contract_id>/",
        views.contract_detail,
        name="contract_detail",
    ),

    # ===========================================================
    # 🔵 (4) Documents
    # ===========================================================
    path(
        "<int:company_id>/employees/<int:employee_id>/documents/",
        views.documents_list,
        name="documents_list",
    ),

    path(
        "<int:company_id>/employees/<int:employee_id>/documents/add/",
        views.document_add,
        name="document_add",
    ),

    path(
        "<int:company_id>/documents/<int:document_id>/delete/",
        views.document_delete,
        name="document_delete",
    ),

    # ===========================================================
    # 🔵 (5) Termination & Resignation
    # ===========================================================
    path(
        "<int:company_id>/employees/<int:employee_id>/termination/",
        views.terminate_employee,
        name="terminate_employee",
    ),

    path(
        "<int:company_id>/employees/<int:employee_id>/resignation/",
        views.employee_resignation,
        name="employee_resignation",
    ),

    # ===========================================================
    # 🔵 (6) Sync Operations
    # ===========================================================
    path(
        "<int:company_id>/sync/employees/",
        views_sync.sync_employees,
        name="sync_employees",
    ),

    path(
        "<int:company_id>/sync/departments/",
        views_sync.sync_departments,
        name="sync_departments",
    ),

    path(
        "<int:company_id>/sync/jobtitles/",
        views_sync.sync_jobtitles,
        name="sync_jobtitles",
    ),

    # ===========================================================
    # 🔵 (7) Sync Logs
    # ===========================================================
    path(
        "<int:company_id>/sync/logs/",
        views_sync.sync_logs_page,
        name="sync_logs_page",
    ),

    path(
        "<int:company_id>/api/sync/logs/",
        views_sync.sync_logs_api,
        name="sync_logs_api",
    ),

    path(
        "<int:company_id>/sync/logs/search/",
        views_sync.sync_logs_search,
        name="sync_logs_search",
    ),

    # ===========================================================
    # 🔵 (8) PDFs
    # ===========================================================
    path(
        "<int:company_id>/employees/<int:employee_id>/card/pdf/",
        views.employee_card_pdf,
        name="employee_card_pdf",
    ),

    path(
        "<int:company_id>/contracts/<int:contract_id>/print/",
        views.contract_print_view,
        name="contract_print",
    ),
]
