# ============================================================
# 🔒 Primey HR Cloud — System Enforcement Middleware
# Version: V1.2 Ultra Stable — Safe Boot + Compatibility Layer
# ============================================================

from django.http import JsonResponse, HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

# ============================================================
# ⚠️ SAFE IMPORTS
# ============================================================
# الخدمات قد تكون غير مكتملة داخل settings_center.services
# لذلك نستخدم try/except لمنع كسر إقلاع النظام
# ============================================================

try:
    from settings_center.services import (
        get_system_setting,
        is_platform_active,
        is_maintenance_mode,
        is_readonly_mode,
        is_module_enabled,
        is_billing_enabled,
    )
    SERVICES_READY = True
except Exception:
    SERVICES_READY = False


class SystemEnforcementMiddleware(MiddlewareMixin):
    """
    🔐 حارس النظام المركزي
    - يُنفذ قبل أي View
    - يحمي UI + API
    - Safe-Mode إذا services غير جاهزة
    """

    def process_request(self, request):

        # --------------------------------------------------
        # 0) Ignore static & media
        # --------------------------------------------------
        path = request.path

        if path.startswith("/static/") or path.startswith("/media/"):
            return None

        # --------------------------------------------------
        # 🟡 SAFE MODE
        # --------------------------------------------------
        # إذا services غير جاهزة، نسمح بمرور الطلب
        # بدون أي Enforcement
        # --------------------------------------------------
        if not SERVICES_READY:
            return None

        # --------------------------------------------------
        # 1) Load System Settings (Fail-Safe)
        # --------------------------------------------------
        try:
            system = get_system_setting()
        except Exception:
            return None  # لا نكسر النظام

        if not system:
            return None

        # --------------------------------------------------
        # 2) Platform Kill Switch
        # --------------------------------------------------
        try:
            if not is_platform_active():
                return self._blocked(
                    request,
                    "🚫 النظام متوقف مؤقتًا من قبل الإدارة.",
                    status=503,
                )
        except Exception:
            return None

        # --------------------------------------------------
        # 3) Maintenance Mode
        # --------------------------------------------------
        try:
            if is_maintenance_mode():
                # نسمح فقط للسوبر أدمن
                if not request.user.is_authenticated or not request.user.is_superuser:
                    return self._blocked(
                        request,
                        "🛠️ النظام في وضع الصيانة حاليًا.",
                        status=503,
                    )
        except Exception:
            return None

        # --------------------------------------------------
        # 4) Readonly Mode
        # --------------------------------------------------
        try:
            if is_readonly_mode():
                if request.method not in ("GET", "HEAD", "OPTIONS"):
                    return self._blocked(
                        request,
                        "🔒 النظام في وضع القراءة فقط.",
                        status=423,
                    )
        except Exception:
            return None

        # --------------------------------------------------
        # 5) Module Kill Switch (حسب المسار)
        # --------------------------------------------------
        module_map = {
            "/companies/": "companies",
            "/billing/": "billing",
            "/users/": "users",
            "/devices/": "devices",
            "/health/": "health",
            "/settings/": "settings",
            "/api/system/companies/": "companies",
            "/api/system/billing/": "billing",
            "/api/system/users/": "users",
            "/api/system/devices/": "devices",
            "/api/system/health/": "health",
            "/api/system/settings/": "settings",
        }

        for prefix, module_key in module_map.items():
            if path.startswith(prefix):
                try:
                    if not is_module_enabled(module_key):
                        return self._blocked(
                            request,
                            f"🚫 وحدة {module_key} معطلة حاليًا.",
                            status=403,
                        )

                    # Billing خاص
                    if module_key == "billing" and not is_billing_enabled():
                        return self._blocked(
                            request,
                            "💳 نظام الفوترة معطل حاليًا.",
                            status=403,
                        )
                except Exception:
                    return None

        return None

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def _blocked(self, request, message, status=403):
        """
        🔁 يعيد JSON للـ API
        🔁 يعيد Forbidden للـ UI
        """
        if request.path.startswith("/api/"):
            return JsonResponse(
                {
                    "status": "blocked",
                    "message": message,
                },
                status=status,
            )

        return HttpResponseForbidden(message)


# ============================================================
# ✅ Compatibility Middlewares
# ============================================================
# بعض الإعدادات القديمة قد تشير إلى هذه الأسماء داخل settings.py
# لذلك نعرّفها كـ Aliases حتى لا ينكسر الإقلاع
# ============================================================

class ReadOnlyModeMiddleware(SystemEnforcementMiddleware):
    """
    Backward compatible alias.
    """
    pass


class MaintenanceModeMiddleware(SystemEnforcementMiddleware):
    """
    Backward compatible alias.
    """
    pass


class PlatformKillSwitchMiddleware(SystemEnforcementMiddleware):
    """
    Backward compatible alias.
    """
    pass
