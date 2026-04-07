# ============================================================
# 📂 primey_hrm/urls.py
# 🧭 Mham Cloud — Unified Smart Routing (FINAL ✅)
# ============================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect, HttpResponse
from auth_center.views import login_view


# ============================================================
# 🏠 الصفحة الرئيسية الذكية
# ============================================================
def home_redirect(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/control-center/dashboard/")
    return HttpResponseRedirect("/auth/login/")


# ============================================================
# ⚠️ صفحات الأخطاء (Glass UI)
# ============================================================
def custom_404_view(request, exception):
    return HttpResponse(
        """
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
        height:100vh;background:linear-gradient(135deg,#f9fafb,#e5e7eb);
        font-family:'Tajawal',sans-serif;text-align:center;">
            <h1 style="font-size:80px;color:#1e293b;">⚠️ 404</h1>
            <p style="font-size:20px;color:#475569;">الصفحة التي تبحث عنها غير موجودة.</p>
            <a href="/" style="margin-top:20px;padding:10px 25px;border-radius:10px;
                background:#1e293b;color:#fff;text-decoration:none;">
                العودة للرئيسية
            </a>
        </div>
        """,
        status=404,
    )


def custom_500_view(request):
    return HttpResponse(
        """
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
        height:100vh;background:linear-gradient(135deg,#f9fafb,#e5e7eb);
        font-family:'Tajawal',sans-serif;text-align:center;">
            <h1 style="font-size:80px;color:#991b1b;">❌ 500</h1>
            <p style="font-size:20px;color:#444;">حدث خطأ داخلي في الخادم.</p>
            <a href="/" style="margin-top:20px;padding:10px 25px;border-radius:10px;
                background:#111827;color:#fff;text-decoration:none;">
                العودة للرئيسية
            </a>
        </div>
        """,
        status=500,
    )


# ============================================================
# 🌐 URL Patterns (ORDER MATTERS)
# ============================================================
urlpatterns = [

    # ========================================================
    # 🆕 API LAYER — MUST BE FIRST
    # ========================================================
    path("api/", include("api.urls")),
    
    # ========================================================
    # 🔐 Admin & Auth
    # ========================================================
    path("admin/", admin.site.urls),
    path("login/", login_view, name="login_direct"),
    path("auth/", include(("auth_center.urls", "auth_center"), namespace="auth_center")),

    # ========================================================
    # 🧩 System Centers
    # ========================================================
    path("control-center/", include(("control_center.urls", "control_center"), namespace="control_center")),
    path("companies/", include(("company_manager.urls", "company_manager"), namespace="company_manager")),
    path("billing-center/", include(("billing_center.urls", "billing_center"), namespace="billing_center")),
    path("notifications/", include(("notification_center.urls", "notification_center"), namespace="notification_center")),
    path("settings/", include(("settings_center.urls", "settings_center"), namespace="settings_center")),

    # ========================================================
    # 👥 HR Core
    # ========================================================
    path("employee/", include(("employee_center.urls", "employee_center"), namespace="employee_center")),
    path("attendance/", include(("attendance_center.urls", "attendance_center"), namespace="attendance_center")),
    path("payroll/", include(("payroll_center.urls", "payroll_center"), namespace="payroll_center")),
    path("leave-center/", include(("leave_center.urls", "leave_center"), namespace="leave_center")),

    # ========================================================
    # 🔄 Integrations & Tools
    # ========================================================
    path("biotime-center/", include(("biotime_center.urls", "biotime_center"), namespace="biotime_center")),
    path("scheduler/", include(("scheduler.urls", "scheduler"), namespace="scheduler")),
    path("database-tools/", include(("database_tools.urls", "database_tools"), namespace="database_tools")),

    # ========================================================
    # 📊 Reports (Optional)
    # ========================================================
    *(
        [
            path(
                "reports/",
                include(("reports_center.urls", "reports_center"), namespace="reports_center"),
            )
        ]
        if "reports_center" in settings.INSTALLED_APPS
        else []
    ),

    # ========================================================
    # 🏠 Home Redirect — LAST
    # ========================================================
    path("", home_redirect, name="home_redirect"),
]


# ============================================================
# 🖼️ Static & Media (DEV)
# ============================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]


# ============================================================
# ⚙️ Error Handlers
# ============================================================
handler500 = "primey_hrm.urls.custom_500_view"

from django.conf import settings
from django.conf.urls.static import static

if not settings.DEBUG:
    handler404 = "primey_hrm.urls.custom_404_view"
    handler500 = "primey_hrm.urls.custom_500_view"

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
