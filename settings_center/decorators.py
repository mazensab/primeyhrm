# ===============================================================
# 📂 system_settings/decorators.py
# 🔒 Module Kill Switch Decorators
# ===============================================================

from functools import wraps
from django.http import HttpResponseForbidden

from system_settings.services import is_module_enabled


def require_module(module_key: str):
    """
    🔒 Decorator يمنع الوصول لوحدة معطلة System-wide

    Usage:
        @require_module("attendance")
        @require_module("payroll")
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):

            if not is_module_enabled(module_key):
                return HttpResponseForbidden(
                    f"🚫 وحدة ({module_key}) معطّلة حاليًا على مستوى النظام."
                )

            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
