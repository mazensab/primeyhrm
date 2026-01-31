# ===============================================================
# 📂 system_settings/context_processors.py
# 🧩 Sidebar Modules Availability
# ===============================================================

from system_settings.services import is_module_enabled


def system_modules_context(request):
    """
    يمرر حالة الوحدات System-wide إلى القوالب
    """

    return {
        "SYSTEM_MODULES": {
            "employee": is_module_enabled("employee"),
            "attendance": is_module_enabled("attendance"),
            "leave": is_module_enabled("leave"),
            "payroll": is_module_enabled("payroll"),
            "performance": is_module_enabled("performance"),
        }
    }
