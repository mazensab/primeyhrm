# ====================================================================
# 🎭 Default Company Roles Blueprint
# ====================================================================

DEFAULT_COMPANY_ROLES = [
    {
        "name": "🛡️ مدير عام (كامل الصلاحيات)",
        "description": "صلاحيات كاملة لإدارة الشركة والنظام",
        "permissions": {"*": True},
        "is_system_role": True,
    },
    {
        "name": "👥 مدير الموارد البشرية",
        "description": "إدارة الموظفين والعقود والإجازات",
        "permissions": {
            "employees": True,
            "contracts": True,
            "leaves": True,
            "attendance": True,
        },
        "is_system_role": False,
    },
    {
        "name": "💰 محاسب الرواتب",
        "description": "إدارة الرواتب والاستحقاقات",
        "permissions": {
            "payroll": True,
            "reports": True,
        },
        "is_system_role": False,
    },
    {
        "name": "👤 موظف عادي",
        "description": "وصول محدود للبيانات الشخصية",
        "permissions": {
            "profile": True,
        },
        "is_system_role": False,
    },
]