# ===============================================================
# 📂 api/company/employee_user.py
# 🔗 Employee ↔ User Link API — V1 Ultra Pro (FINAL)
# Primey HR Cloud
# ===============================================================
# ✔ Link existing user
# ✔ Create new user + link
# ✔ Unlink user
# ✔ Auto role assign / revoke
# ✔ Company-safe
# ✔ Atomic & Defensive
# ===============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
import json

from company_manager.models import CompanyUser
from employee_center.models import Employee

from api.company.employee_role_mapper import (
    apply_employee_role,
    remove_employee_role,
)

User = get_user_model()


# ===============================================================
# 🔐 Helpers
# ===============================================================
def _get_company_employee(request, employee_id):
    """
    جلب الموظف مع التأكد من أنه تابع لنفس الشركة
    """
    company_user = (
        CompanyUser.objects
        .select_related("company")
        .filter(
            user=request.user,
            is_active=True,
            company__isnull=False,
        )
        .order_by("-id")
        .first()
    )

    if not company_user:
        return None, JsonResponse(
            {"error": "Company context not found"},
            status=403
        )

    employee = Employee.objects.filter(
        id=employee_id,
        company=company_user.company
    ).first()

    if not employee:
        return None, JsonResponse(
            {"error": "Employee not found"},
            status=404
        )

    return employee, None


def _parse_request_data(request):
    """
    قراءة آمنة للـ JSON / POST
    """
    try:
        if request.content_type == "application/json":
            return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        pass

    return request.POST


# ===============================================================
# 🔗 POST /api/company/employees/<id>/link-user/
# ===============================================================
@login_required
@require_http_methods(["POST"])
@transaction.atomic
def link_employee_user(request, employee_id):
    """
    ربط / إنشاء / فك ربط مستخدم مع موظف
    + RBAC Auto Assign / Revoke
    """

    employee, error = _get_company_employee(request, employee_id)
    if error:
        return error

    data = _parse_request_data(request)
    mode = data.get("mode")

    # -----------------------------------------------------------
    # 🧨 Unlink user
    # -----------------------------------------------------------
    if mode == "unlink":
        if employee.user:
            remove_employee_role(employee)

            employee.user = None
            employee.save(update_fields=["user"])

        return JsonResponse({
            "success": True,
            "action": "unlinked",
        })

    # -----------------------------------------------------------
    # 🔗 Link existing user
    # -----------------------------------------------------------
    if mode == "link_existing":
        user_id = data.get("user_id")

        if not user_id:
            return JsonResponse(
                {"error": "user_id required"},
                status=400
            )

        user = User.objects.filter(id=user_id).first()
        if not user:
            return JsonResponse(
                {"error": "User not found"},
                status=404
            )

        # ❌ منع الربط المزدوج
        if Employee.objects.filter(
            user=user
        ).exclude(id=employee.id).exists():
            return JsonResponse(
                {"error": "User already linked to another employee"},
                status=400
            )

        employee.user = user
        employee.save(update_fields=["user"])

        apply_employee_role(employee)

        return JsonResponse({
            "success": True,
            "action": "linked_existing",
            "user_id": user.id,
        })

    # -----------------------------------------------------------
    # ➕ Create new user + link
    # -----------------------------------------------------------
    if mode == "create_new":
        username = data.get("username")
        email = data.get("email")

        if not username:
            return JsonResponse(
                {"error": "username required"},
                status=400
            )

        if User.objects.filter(username=username).exists():
            return JsonResponse(
                {"error": "username already exists"},
                status=400
            )

        # 🔐 إنشاء المستخدم بدون كلمة مرور (Invite لاحقًا)
        user = User.objects.create_user(
            username=username,
            email=email or None,
            password=None,
        )

        employee.user = user
        employee.save(update_fields=["user"])

        apply_employee_role(employee)

        return JsonResponse({
            "success": True,
            "action": "created_and_linked",
            "user_id": user.id,
        })

    # -----------------------------------------------------------
    # ❌ Invalid mode
    # -----------------------------------------------------------
    return JsonResponse(
        {"error": "Invalid mode"},
        status=400
    )
