# ================================================================
# 📂 auth_center/urls.py — FINAL
# ================================================================

from django.urls import path
from . import views

app_name = "auth_center"

urlpatterns = [

    # HTML ONLY (Django Admin / Legacy)
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("change-password/", views.change_password_view, name="change_password"),

    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
]
