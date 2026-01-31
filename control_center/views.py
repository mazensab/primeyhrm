# ================================================================
# 📂 control_center/views.py — V14 Ultra Pro (API ONLY)
# ---------------------------------------------------------------
# ❌ NO HTML RENDERING
# ❌ NO DJANGO DASHBOARD
# ✅ Django = Admin + API ONLY
# ✅ All logic preserved (KPIs / Queries)
# ================================================================

from datetime import date, timedelta

from django.http import JsonResponse, HttpResponseGone
from django.db.models import Sum, Count
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required

# Billing + Companies
from billing_center.models import (
    Invoice,
    CompanySubscription,
    Company,
)
from company_manager.models import CompanyUser

# Biotime
from biotime_center.models import BiotimeDevice

# System Health
from .system_health.system_health import get_system_health


# ============================================================
# 🔐 Guards
# ============================================================

def is_system_owner(user):
    return user.is_authenticated and user.is_superuser


# ============================================================
# ❌ DISABLED: System Owner Dashboard (HTML REMOVED)
# ============================================================

@login_required
@user_passes_test(is_system_owner)
def dashboard_system_owner(request):
    """
    ❌ HTML Dashboard disabled permanently.
    Use Next.js frontend instead.
    """
    return HttpResponseGone(
        "System Owner dashboard has been removed. "
        "Use Next.js frontend."
    )


# ============================================================
# 🔁 API — System Health (SECURED)
# ============================================================

@login_required
@user_passes_test(is_system_owner)
def system_health_api(request):
    return JsonResponse(get_system_health(), safe=False)


# ============================================================
# ❌ DISABLED: Legacy Staff Dashboard
# ============================================================

@staff_member_required
def system_dashboard(request):
    """
    ❌ Legacy Django dashboard disabled.
    """
    return HttpResponseGone(
        "Legacy Django dashboard removed. "
        "Admin panel only."
    )
