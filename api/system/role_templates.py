# ============================================================
# 🟦 ROLE_TEMPLATES — النسخة الرسمية
# ============================================================

ROLE_TEMPLATES = {
    "Owner": {
        "readable_name": "المالك",
        "permissions": {
            "company_view": True,
            "company_edit": True,
            "users_manage": True,
            "billing_view": True,
            "billing_edit": True,
            "devices_manage": True,
        },
        "editable": False,
        "deletable": False,
    },

    "Manager": {
        "readable_name": "المدير",
        "permissions": {
            "company_view": True,
            "company_edit": True,
            "users_manage": True,
            "billing_view": True,
        },
        "editable": True,
        "deletable": False,
    },

    "Employee": {
        "readable_name": "موظف",
        "permissions": {
            "company_view": True,
        },
        "editable": True,
        "deletable": True,
    },
}
