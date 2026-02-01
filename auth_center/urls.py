# ================================================================
# 📂 auth_center/urls.py
# 🧭 Authentication Routing — Primey HR Cloud V15.1 ULTRA STABLE
# ================================================================

from django.urls import path
from . import views

app_name = "auth_center"

urlpatterns = [

    # ============================================================
    # 🧭 HTML ONLY (Django Admin / Legacy UI)
    # ============================================================
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("change-password/", views.change_password_view, name="change_password"),

    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),

    # ============================================================
    # 🔐 API — Session Based (Next.js / Frontend)
    # ============================================================
    path("api/login/", views.login_api, name="login_api"),
    path("api/whoami/", views.whoami_api, name="whoami_api"),
]
