# ============================================================
# 🛡 RolePermissionMiddleware — Hybrid RBAC V3.1 + Impersonation Gate
# 💎 Version: V15.5 — Employee Center Full Integration
# ============================================================
from django.shortcuts import redirect
from django.urls import resolve
from django.contrib import messages
from company_manager.models import CompanyUser, CompanyRole, UserRoleAssignment


class RolePermissionMiddleware:
    """
    🛡 RBAC Hybrid V3.1 — حماية شاملة للنظام + Employee Center
    - حماية impersonation (فتح شركة غير الشركة النشطة)
    - حماية روابط System Owner أثناء impersonation
    - استخراج company_id من URL مباشرة (أقوى حماية)
    - توسعة كاملة لـ employee_center modules
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # ============================================================
        # 🔥 RBAC Route Mapping — يشمل Employee Center الآن
        # ============================================================
        self.route_permissions = {
            # ===== Roles =====
            "role_list": ("roles", "view"),
            "role_add": ("roles", "create"),
            "role_edit": ("roles", "edit"),
            "role_delete": ("roles", "delete"),
            "role_permissions": ("roles", "edit"),

            # ===== Company =====
            "company_list": ("company", "view"),
            "company_detail": ("company", "view"),
            "company_settings": ("settings", "edit"),

            # ===== Employee Center =====
            "employees_dashboard": ("employee_center", "view"),
            "employees_list": ("employee_center", "view"),
            "employee_add": ("employee_center", "create"),
            "employee_edit": ("employee_center", "edit"),
            "employee_delete": ("employee_center", "delete"),

            # Sync endpoints
            "sync_employees": ("employee_center", "sync"),
            "sync_departments": ("employee_center", "sync"),
            "sync_jobtitles": ("employee_center", "sync"),

            # Contracts
            "contracts_list": ("employee_center", "manage_contracts"),
            "contract_add": ("employee_center", "manage_contracts"),
            "contract_edit": ("employee_center", "manage_contracts"),
            "contract_delete": ("employee_center", "manage_contracts"),

            # Documents
            "employee_documents": ("employee_center", "manage_documents"),
        }

        # روابط نظامية محظورة أثناء impersonation
        self.system_only_routes = {
            "company_list",
            "company_add",
            "company_edit",
            "company_delete",
            "system_dashboard",
            "billing_dashboard",
        }


    # ------------------------------------------------------------
    # 🔍 استخراج module/action من URL — Auto Detect
    # ------------------------------------------------------------
    def extract_from_url(self, path):
        segments = [seg for seg in path.split("/") if seg]

        module = None
        action = None

        # /employee/<id>/dashboard → module = employee
        if len(segments) >= 1:
            module = segments[0]

        # تحديد الأكشن حسب الكلمات
        if "add" in segments:
            action = "create"
        elif "edit" in segments:
            action = "edit"
        elif "delete" in segments:
            action = "delete"
        elif "sync" in segments:
            action = "sync"
        else:
            action = "view"

        return module, action


    # ------------------------------------------------------------
    # 🔥 دمج صلاحيات المستخدم من خلال جميع الأدوار (OR logic)
    # ------------------------------------------------------------
    def merge_permissions(self, roles):
        merged = {}
        for role in roles:
            for module, actions in role.permissions.items():
                if module not in merged:
                    merged[module] = {}
                for action, value in actions.items():
                    merged[module][action] = merged[module].get(action, False) or value
        return merged


    # ------------------------------------------------------------
    # 🔥 الميدلوير الرئيسي
    # ------------------------------------------------------------
    def __call__(self, request):
        path = request.path

        # تخطي static / media / admin
        if path.startswith("/admin") or path.startswith("/static") or path.startswith("/media"):
            return self.get_response(request)

        # المستخدم غير مسجل دخول
        if not request.user.is_authenticated:
            return self.get_response(request)

        # استخراج معلومات URL
        resolver = resolve(request.path)
        url_name = resolver.url_name
        url_kwargs = resolver.kwargs
        url_company_id = url_kwargs.get("company_id")

        impersonate_id = request.session.get("impersonate_company_id")

        # ------------------------------------------------------------
        # 🧲 حماية impersonation — لا يسمح بفتح شركة أخرى
        # ------------------------------------------------------------
        if impersonate_id:
            if url_company_id and str(url_company_id) != str(impersonate_id):
                messages.error(request, "⚠️ لا يمكنك فتح شركة أخرى أثناء impersonation.")
                return redirect("company_manager:company_detail", company_id=impersonate_id)

            if url_name in self.system_only_routes:
                messages.error(request, "⚠️ لا يمكن الوصول لصفحات مالك النظام أثناء impersonation.")
                return redirect("company_manager:company_detail", company_id=impersonate_id)

        # ------------------------------------------------------------
        # 🏢 الشركة النشطة — Active Company
        # ------------------------------------------------------------
        company_id = request.session.get("active_company_id")
        if not company_id:
            return self.get_response(request)

        # ------------------------------------------------------------
        # 🧩 جلب CompanyUser
        # ------------------------------------------------------------
        try:
            company_user = CompanyUser.objects.get(user=request.user, company_id=company_id)
        except CompanyUser.DoesNotExist:
            return self.get_response(request)

        # ------------------------------------------------------------
        # 🧩 جلب الأدوار من UserRoleAssignment
        # ------------------------------------------------------------
        assignments = UserRoleAssignment.objects.filter(company=company_id, user=request.user)
        roles = [assign.role for assign in assignments]

        if not roles:
            return self.get_response(request)

        permissions = self.merge_permissions(roles)

        # ------------------------------------------------------------
        # 🔍 تحديد module/action عبر mapping أو URL auto detect
        # ------------------------------------------------------------
        if url_name in self.route_permissions:
            module, action = self.route_permissions[url_name]
        else:
            module, action = self.extract_from_url(path)

        if not module or module not in permissions:
            return self.get_response(request)

        if not permissions[module].get(action, False):
            messages.error(request, "⛔ ليس لديك صلاحية للوصول إلى هذه الصفحة.")
            return redirect("employee_center:employees_dashboard", company_id=company_id)

        return self.get_response(request)



# ============================================================
# 🎯 PermissionContextMiddleware (V15.5)
# ============================================================
from django.utils.deprecation import MiddlewareMixin

class PermissionContextMiddleware(MiddlewareMixin):
    """
    يضيف الصلاحيات المدمجة إلى الـ context
    ليتم استخدامها داخل الواجهة مباشرة.
    """

    def process_template_response(self, request, response):
        if not request.user.is_authenticated:
            response.context_data = response.context_data or {}
            response.context_data["permissions"] = {}
            return response

        company_id = request.session.get("active_company_id")
        if not company_id:
            response.context_data = response.context_data or {}
            response.context_data["permissions"] = {}
            return response

        try:
            CompanyUser.objects.get(user=request.user, company_id=company_id)
        except CompanyUser.DoesNotExist:
            response.context_data = response.context_data or {}
            response.context_data["permissions"] = {}
            return response

        assignments = UserRoleAssignment.objects.filter(company=company_id, user=request.user)
        roles = [a.role for a in assignments]

        merged_permissions = {}
        for role in roles:
            for module, actions in role.permissions.items():
                if module not in merged_permissions:
                    merged_permissions[module] = {}
                for act, val in actions.items():
                    merged_permissions[module][act] = (
                        merged_permissions[module].get(act, False) or val
                    )

        response.context_data = response.context_data or {}
        response.context_data["permissions"] = merged_permissions
        return response
