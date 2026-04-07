# ==================================================================
# 🎛️ Role Templates — Ultra Stable for Mham Cloud
# ==================================================================

from django.db import transaction
from .models import CompanyRole

# --------------------------------------------------------------
# 🧩 Modules Definitions (الصلاحيات لكل وحدة)
# --------------------------------------------------------------
ROLE_TEMPLATES = {
    "MODULES": {
        "COMPANY_MANAGER": {
            "view": True,
            "edit": True,
            "delete": True,
        },
        "EMPLOYEE_CENTER": {
            "view": True,
            "create": True,
            "edit": True,
            "delete": True,
        },
        "ATTENDANCE_CENTER": {
            "view": True,
            "sync": True,
            "edit": True,
        },
        "PAYROLL_CENTER": {
            "view": True,
            "generate": True,
            "edit": True,
        },
        "LEAVE_CENTER": {
            "view": True,
            "request": True,
            "approve": True,
        },
    },

    # ----------------------------------------------------------
    # 🧩 Templates Ready for Quick Assignment — ERPNext style
    # ----------------------------------------------------------
    "ADMIN": {
        "all_permissions": True,
        "modules": ["*"],
    },

    "HR_MANAGER": {
        "modules": [
            "EMPLOYEE_CENTER",
            "ATTENDANCE_CENTER",
            "LEAVE_CENTER",
        ],
        "all_permissions": False,
    },

    "ACCOUNTANT": {
        "modules": [
            "PAYROLL_CENTER",
        ],
        "all_permissions": False,
    },

    "EMPLOYEE": {
        "modules": [
            "EMPLOYEE_CENTER",
            "LEAVE_CENTER",
        ],
        "all_permissions": False,
    },
}


# --------------------------------------------------------------
# 🧩 قائمة جاهزة للاختيار في الفورم
# --------------------------------------------------------------
DEFAULT_ROLE_TEMPLATES = [
    ("ADMIN", "🛡️ مدير عام (كامل الصلاحيات)"),
    ("HR_MANAGER", "👥 مدير الموارد البشرية"),
    ("ACCOUNTANT", "💰 محاسب الرواتب"),
    ("EMPLOYEE", "👤 موظف عادي"),
]


# ==================================================================
# 🛡️ apply_role_templates — إنشاء الأدوار الافتراضية للشركة
# ==================================================================
def apply_role_templates(company):
    """
    🧠 إنشاء الأدوار الافتراضية للشركة الجديدة باستخدام ROLE_TEMPLATES
    يتم استدعاؤها تلقائيًا عبر signal عند إنشاء شركة جديدة.
    """

    from .role_templates import ROLE_TEMPLATES, DEFAULT_ROLE_TEMPLATES  # لضمان الاستيراد المتأخر

    with transaction.atomic():

        # loop على القوالب الافتراضية
        for role_code, role_label in DEFAULT_ROLE_TEMPLATES:

            template = ROLE_TEMPLATES.get(role_code, {})

            # استخراج معلومات الصلاحيات
            is_admin = template.get("all_permissions", False)
            modules = template.get("modules", [])

            # تجهيز صلاحيات JSON
            permissions = {}

            if is_admin:
                # صلاحيات كاملة لجميع الوحدات
                for module_name, actions in ROLE_TEMPLATES["MODULES"].items():
                    permissions[module_name] = actions
            else:
                # صلاحيات محددة بناءً على modules
                for module_name in modules:
                    actions = ROLE_TEMPLATES["MODULES"].get(module_name, {})
                    permissions[module_name] = actions

            # إنشاء الدور الفعلي داخل الشركة
            CompanyRole.objects.create(
                company=company,
                name=role_label,
                permissions=permissions,
                is_system_role=True
            )
