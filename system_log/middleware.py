from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from company_manager.models import CompanyUser
from .models import SystemLog

# 🔥 Realtime WebSocket
from channels.layers import get_channel_layer
import asyncio

User = get_user_model()


# ================================================================
# 🛰️ System Log Sniffer Middleware — V6.1 FINAL (Auth Safe)
# ================================================================
# ✔ يمنع التسجيل بدون شركة
# ✔ آمن أثناء login / logout / apiWhoAmI()
# ✔ لا يكسر Session Auth
# ✔ WebSocket بث لحظي مستقر
# ================================================================

class SystemLogSniffer(MiddlewareMixin):

    AUTH_EXCLUDED_PATHS = (
        "/auth/login",
        "/auth/logout",
        "/api/auth/apiWhoAmI()/",
        "/api/auth/login",
        "/api/auth/logout",
        "/api/api/auth/apiWhoAmI()/",
    )

    STATIC_EXCLUDED_PATHS = (
        "/admin/",
        "/static/",
        "/media/",
    )

    # ============================================================
    # 🧭 1) Request
    # ============================================================
    def process_request(self, request):

        request._start_time = now()

        # 🔒 تجاهل auth endpoints بالكامل
        if request.path.startswith(self.AUTH_EXCLUDED_PATHS):
            return None

        # GET لا نحتاج تسجيله
        if request.method == "GET":
            return None

        # تجاهل المسارات الثابتة
        if request.path.startswith(self.STATIC_EXCLUDED_PATHS):
            return None

        request._system_log_capture = True
        return None

    # ============================================================
    # ❌ 2) Exception
    # ============================================================
    def process_exception(self, request, exception):

        if not hasattr(request, "_system_log_capture"):
            return None

        if request.path.startswith(self.AUTH_EXCLUDED_PATHS):
            return None

        user = request.user if request.user.is_authenticated else None
        company = self._get_company(user)

        # ❌ لا تسجيل بدون شركة
        if not company:
            return None

        log_item = SystemLog.objects.create(
            company=company,
            user=user,
            module=self._resolve_module(request),
            action="exception",
            severity="critical",
            message=str(exception),
            extra_data={
                "method": request.method,
                "path": request.path,
            }
        )

        self._broadcast(company, log_item)
        return None

    # ============================================================
    # 📡 3) Response
    # ============================================================
    def process_response(self, request, response):

        if not hasattr(request, "_system_log_capture"):
            return response

        if request.path.startswith(self.AUTH_EXCLUDED_PATHS):
            return response

        user = request.user if request.user.is_authenticated else None
        company = self._get_company(user)

        # ❌ لا تسجيل بدون شركة
        if not company:
            return response

        log_item = SystemLog.objects.create(
            company=company,
            user=user,
            module=self._resolve_module(request),
            action=self._resolve_action(request.method),
            severity="info",
            message=f"{request.method} → {request.path}",
            extra_data={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
            }
        )

        self._broadcast(company, log_item)
        return response

    # ============================================================
    # 🧩 Helpers
    # ============================================================

    def _get_company(self, user):
        if not user:
            return None
        cu = CompanyUser.objects.filter(user=user).select_related("company").first()
        return cu.company if cu else None

    def _broadcast(self, company, log_item):
        if not company:
            return

        try:
            layer = get_channel_layer()
            asyncio.run(layer.group_send(
                f"system_log_{company.id}",
                {
                    "type": "stream_log",
                    "id": log_item.id,
                    "module": log_item.module,
                    "action": log_item.action,
                    "severity": log_item.severity,
                    "message": log_item.message,
                    "created_at": log_item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "user": log_item.user.get_full_name() if log_item.user else "—",
                }
            ))
        except Exception as e:
            print("WebSocket Error:", e)

    def _resolve_module(self, request):
        try:
            return request.path.strip("/").split("/")[0] or "unknown"
        except Exception:
            return "unknown"

    def _resolve_action(self, method):
        return {
            "POST": "create/update",
            "PUT": "update",
            "PATCH": "patch",
            "DELETE": "delete",
        }.get(method, method.lower())
