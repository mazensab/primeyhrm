# =====================================================================
# 🏢 Company Manager URLs — V8 Ultra Stable
# =====================================================================

from django.urls import path

# Views (standard)
from .views import view_company as company_views
from . import views

# 🔵 الربط الصحيح للـ API الخارجية
from api.system.actions.create_company_full import create_company_full

app_name = "company_manager"

urlpatterns = [

    # ============================================================
    # 🏢 إدارة الشركات
    # ============================================================
    path("", company_views.company_list, name="company_list"),
    path("add/", company_views.company_add, name="company_add"),
    path("<int:company_id>/", company_views.company_detail, name="company_detail"),
    path("<int:company_id>/edit/", company_views.company_edit, name="company_edit"),
    path("<int:company_id>/delete/", company_views.company_delete, name="company_delete"),
    path("<int:company_id>/toggle/", company_views.toggle_company_status, name="toggle_company_status"),

    # ============================================================
    # ⚡ API: إنشاء شركة كاملة
    # ============================================================
    path("actions/create-company-full/", create_company_full, name="create_company_full"),

    # ============================================================
    # 🏢 الفروع
    # ============================================================
    path("branches/", views.branch_list, name="branch_list"),
    path("branches/add/", views.branch_add, name="branch_add"),
    path("branches/<int:branch_id>/edit/", views.branch_edit, name="branch_edit"),
    path("branches/<int:branch_id>/delete/", views.branch_delete, name="branch_delete"),

    # ============================================================
    # 🧩 المكاتب
    # ============================================================
    path("offices/", views.offices_list, name="office_list"),
    path("offices/add/", views.office_add, name="office_add"),
    path("offices/<int:office_id>/edit/", views.office_edit, name="office_edit"),
    path("offices/<int:office_id>/delete/", views.office_delete, name="office_delete"),

    # ============================================================
    # 👥 المستخدمون
    # ============================================================
    path("users/<int:company_id>/", views.users_list, name="users_list"),
    path("users/<int:company_id>/add/", views.user_add, name="user_add"),
    path("users/<int:company_id>/<int:user_id>/toggle/", views.user_toggle, name="user_toggle"),

    # ============================================================
    # 🔐 الأدوار
    # ============================================================
    path("roles/", views.role_list, name="role_list"),
    path("roles/add/", views.role_add, name="role_add"),
    path("roles/<int:role_id>/edit/", views.role_edit, name="role_edit"),
    path("roles/<int:role_id>/delete/", views.role_delete, name="role_delete"),

    # ============================================================
    # 📄 الوثائق
    # ============================================================
    path("documents/<int:company_id>/", views.documents_list, name="documents_list"),
    path("documents/<int:company_id>/add/", views.document_add, name="document_add"),
    path("documents/<int:company_id>/<int:document_id>/edit/", views.document_edit, name="document_edit"),
    path("documents/<int:company_id>/<int:document_id>/delete/", views.document_delete, name="document_delete"),

    # ============================================================
    # 🖨 طباعة
    # ============================================================
    path("print/", company_views.company_print_view, name="company_print"),
    path("print/pdf/", company_views.company_pdf_view, name="company_print_pdf"),
    path("export/excel/", company_views.company_export_excel, name="company_export_excel"),

    # ============================================================
    # 👤 Impersonation
    # ============================================================
    path("impersonate/<int:company_id>/", company_views.impersonate_company, name="impersonate_company"),
]
