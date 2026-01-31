# ===================================================================
# 📂 الملف: performance_center/urls.py
# 🧭 نظام المسارات — Performance Center V1.0 Ultra Pro
# ===================================================================

from django.urls import path
from . import views
from .views import (
    review_pdf_view,
    employee_summary_pdf_view,
    reviews_excel_export,
)

app_name = "performance"


urlpatterns = [

    # ============================================================
    # 📌 Dashboard
    # ============================================================
    path("dashboard/", views.performance_dashboard, name="dashboard"),

    # ============================================================
    # 📌 Templates
    # ============================================================
    path("templates/", views.template_list, name="template_list"),
    path("templates/add/", views.template_add, name="template_add"),
    path("templates/<int:template_id>/edit/", views.template_edit, name="template_edit"),
    path("templates/<int:template_id>/delete/", views.template_delete, name="template_delete"),

    # ============================================================
    # 📌 Categories
    # ============================================================
    path("templates/<int:template_id>/categories/", views.category_list, name="category_list"),
    path("templates/<int:template_id>/categories/add/", views.category_add, name="category_add"),
    path("categories/<int:category_id>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:category_id>/delete/", views.category_delete, name="category_delete"),

    # ============================================================
    # 📌 Items
    # ============================================================
    path("categories/<int:category_id>/items/", views.item_list, name="item_list"),
    path("categories/<int:category_id>/items/add/", views.item_add, name="item_add"),
    path("items/<int:item_id>/edit/", views.item_edit, name="item_edit"),
    path("items/<int:item_id>/delete/", views.item_delete, name="item_delete"),

    # ============================================================
    # 📌 Reviews
    # ============================================================
    path("reviews/", views.review_list, name="review_list"),
    path("reviews/start/<int:employee_id>/<int:template_id>/", views.review_start, name="review_start"),
    path("reviews/<int:review_id>/", views.review_detail, name="review_detail"),

    # ============================================================
    # 📌 Self Review
    # ============================================================
    path("reviews/<int:review_id>/self/", views.self_review, name="self_review"),

    # ============================================================
    # 📌 Manager Review
    # ============================================================
    path("reviews/<int:review_id>/manager/", views.manager_review, name="manager_review"),

    # ============================================================
    # 📌 HR Review
    # ============================================================
    path("reviews/<int:review_id>/hr/", views.hr_review, name="hr_review"),

    # ============================================================
    # 📊 Reports (PDF + Excel)
    # ============================================================
    # 📝 PDF لتقرير تقييم واحد
    path("reports/review/<int:review_id>/pdf/", review_pdf_view, name="review_pdf"),

    # 👤 PDF لتقرير جميع تقييمات موظف
    path("reports/employee/<int:employee_id>/pdf/", employee_summary_pdf_view, name="employee_summary_pdf"),

    # 📊 Excel — جميع التقييمات
    path("reports/reviews/excel/", reviews_excel_export, name="reviews_excel"),
]
