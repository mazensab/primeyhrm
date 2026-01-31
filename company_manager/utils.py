# ================================================================
# 🧩 Company Manager Utils — V4 Ultra Pro
# ================================================================

from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from company_manager.models import CompanyUser


# ================================================================
# 🏢 1) company_required — تحقق من انتماء المستخدم للشركة
# ================================================================
def company_required(view_func):
    @wraps(view_func)
    def _wrapped(request, company_id, *args, **kwargs):
        try:
            cu = CompanyUser.objects.get(user=request.user, company_id=company_id)
        except CompanyUser.DoesNotExist:
            messages.error(request, "🚫 غير مصرح لك بالوصول لهذه الشركة.")
            return redirect("control_center:dashboard")

        request.company_user = cu
        request.company = cu.company
        return view_func(request, company_id, *args, **kwargs)

    return _wrapped


# ================================================================
# 🔐 2) permission_required — التحقق من صلاحيات الدور
# ================================================================
def permission_required(module, action):
    """
    مثال:
    @permission_required("employees", "view")
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, company_id, *args, **kwargs):
            cu = getattr(request, "company_user", None)

            if not cu or not cu.role:
                messages.error(request, "🚫 لا تملك صلاحية الوصول.")
                return redirect("control_center:dashboard")

            # الصلاحيات مخزنة داخل JSONField في role.permissions
            permissions = cu.role.permissions or {}

            module_perms = permissions.get(module, {})

            if not module_perms.get(action, False):
                messages.error(request, "🚫 ليست لديك الصلاحية المطلوبة.")
                return redirect("control_center:dashboard")

            return view_func(request, company_id, *args, **kwargs)

        return _wrapped

    return decorator
