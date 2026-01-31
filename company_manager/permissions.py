# ============================================================
# 📘 Company Manager — RBAC Permission Decorator
# 🧭 Version: V4 Ultra Clean (CompanyRole M2M Support)
# ============================================================

from functools import wraps
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from .models import CompanyUser, Company


# ============================================================
# 📘 Company Manager — RBAC Permission Decorator
# 🧭 Version: V5 — Wildcard Support (*)
# ============================================================

def company_permission_required(permission_code):
    def decorator(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("auth_center:login")

            company_id = kwargs.get("company_id")
            if not company_id:
                return HttpResponseForbidden("Invalid Company Access")

            company = Company.objects.filter(id=company_id).first()
            if not company:
                return HttpResponseForbidden("Company Not Found")

            company_user = CompanyUser.objects.filter(
                company=company,
                user=request.user
            ).first()

            if not company_user:
                return HttpResponseForbidden("No Company User Found")

            roles = company_user.roles.all()

            if not roles.exists():
                return HttpResponseForbidden("No Role Assigned")

            module_code, action_code = permission_code.split(".")

            # ---------------------------------------------------
            # 🔥 Wildcard Handling "*" = Full Access
            # ---------------------------------------------------
            for role in roles:
                permissions = role.permissions or {}

                # 1) Full wildcard access
                if permissions.get("*", False):
                    return function(request, *args, **kwargs)

                # 2) Module-level wildcard
                module_perms = permissions.get(module_code, {})
                if module_perms == "*":
                    return function(request, *args, **kwargs)

                # 3) Action-level permission
                if module_perms.get(action_code, False):
                    return function(request, *args, **kwargs)

            return HttpResponseForbidden("Permission Denied")

        return wrapper
    return decorator
