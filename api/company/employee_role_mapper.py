# ===============================================================
# 📂 api/company/employee_role_mapper.py
# 🔐 Employee → RBAC Auto Mapper — V2 FINAL
# Primey HR Cloud
# ===============================================================
# ✔ Auto assign role_code on link
# ✔ Update role_code on re-link
# ✔ Safe unlink handling
# ✔ Company scoped
# ✔ NO dependency on Role model
# ===============================================================

from django.db import transaction

from company_manager.models import CompanyUser
from employee_center.models import Employee


# ===============================================================
# ⚙️ CONFIG
# ===============================================================
DEFAULT_EMPLOYEE_ROLE_CODE = "employee_default"


# ===============================================================
# 🔗 Apply Role After Link
# ===============================================================
@transaction.atomic
def apply_employee_role(employee: Employee):
    """
    تطبيق الدور الافتراضي عند ربط مستخدم بموظف

    Flow:
    Employee -> User -> CompanyUser -> role_code
    """

    if not employee.user:
        return

    company = employee.company
    user = employee.user

    company_user, created = CompanyUser.objects.get_or_create(
        company=company,
        user=user,
        defaults={
            "role_code": DEFAULT_EMPLOYEE_ROLE_CODE,
            "is_active": True,
        }
    )

    # في حال كان موجود لكن:
    # - غير مفعل
    # - أو role_code مختلف
    needs_update = False

    if not company_user.is_active:
        company_user.is_active = True
        needs_update = True

    if company_user.role_code != DEFAULT_EMPLOYEE_ROLE_CODE:
        company_user.role_code = DEFAULT_EMPLOYEE_ROLE_CODE
        needs_update = True

    if needs_update:
        company_user.save(update_fields=["role_code", "is_active"])


# ===============================================================
# 🔓 Remove Role On Unlink
# ===============================================================
@transaction.atomic
def remove_employee_role(employee: Employee):
    """
    إزالة صلاحيات الموظف عند فك الربط
    - لا نحذف المستخدم
    - لا نحذف CompanyUser
    - فقط نفك التفعيل ونزيل role_code
    """

    if not employee.user:
        return

    CompanyUser.objects.filter(
        company=employee.company,
        user=employee.user,
    ).update(
        role_code=None,
        is_active=False,
    )
