# ============================================================
# 📂 whatsapp_center/apps.py
# Primey HR Cloud - WhatsApp Center App Config
# ============================================================
# ✅ تشغيل تلقائي لـ WhatsApp Session Gateway
# ✅ آمن مع Django runserver + StatReloader
# ✅ لا يعيد التشغيل إذا كان الجت واي شغال
# ✅ يدعم Windows بشكل صحيح
# ✅ لا يعتمد على DB داخل ready()
# ✅ يفضّل تشغيل node server.js مباشرة على ويندوز
# ============================================================

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.apps import AppConfig
from django.conf import settings


class WhatsappCenterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "whatsapp_center"
    verbose_name = "WhatsApp Center"

    # --------------------------------------------------------
    # 🚀 App Ready
    # --------------------------------------------------------
    def ready(self):
        """
        تشغيل الجت واي تلقائيًا عند إقلاع Django
        بدون تكرار مع autoreloader.
        """
        if not self._should_autostart_gateway():
            return

        worker = threading.Thread(
            target=self._autostart_gateway_worker,
            name="primey-whatsapp-gateway-autostart",
            daemon=True,
        )
        worker.start()

    # --------------------------------------------------------
    # ✅ Guards
    # --------------------------------------------------------
    def _should_autostart_gateway(self) -> bool:
        """
        منع التشغيل في أوامر لا تحتاج الجت واي،
        ومنع التكرار مع Django reloader.
        """
        if not getattr(settings, "WHATSAPP_GATEWAY_AUTOSTART", True):
            return False

        if os.getenv("DISABLE_WHATSAPP_GATEWAY_AUTOSTART", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }:
            return False

        blocked_commands = {
            "makemigrations",
            "migrate",
            "collectstatic",
            "test",
            "shell",
            "shell_plus",
            "dbshell",
            "createsuperuser",
            "changepassword",
            "dumpdata",
            "loaddata",
        }

        argv = {arg.strip().lower() for arg in sys.argv if arg.strip()}
        if argv.intersection(blocked_commands):
            return False

        # مهم جدًا:
        # مع runserver يوجد process أولي + process فعلي
        # نسمح فقط للـ process الفعلي بالتشغيل
        if "runserver" in argv:
            return os.getenv("RUN_MAIN") == "true"

        # في أي تشغيل آخر:
        # اسمح بالمحاولة مع health check لمنع التكرار.
        return True

    # --------------------------------------------------------
    # 🌐 Health Check
    # --------------------------------------------------------
    def _get_gateway_base_url(self) -> str:
        return str(
            getattr(
                settings,
                "WHATSAPP_SESSION_GATEWAY_URL",
                "http://127.0.0.1:3100",
            )
        ).rstrip("/")

    def _get_health_url(self) -> str:
        return f"{self._get_gateway_base_url()}/health"

    def _is_gateway_running(self) -> bool:
        """
        فحص هل الجت واي شغال فعليًا عبر /health
        """
        timeout = int(
            getattr(settings, "WHATSAPP_GATEWAY_AUTOSTART_HEALTH_TIMEOUT", 2)
        )

        request = Request(
            self._get_health_url(),
            headers={"Accept": "application/json"},
            method="GET",
        )

        try:
            with urlopen(request, timeout=timeout) as response:
                return int(getattr(response, "status", 0)) == 200
        except (URLError, socket.timeout, OSError, ValueError):
            return False
        except Exception:
            return False

    # --------------------------------------------------------
    # 📁 Paths / Command Helpers
    # --------------------------------------------------------
    def _get_gateway_dir(self) -> Path:
        configured = getattr(settings, "WHATSAPP_GATEWAY_DIR", "")
        if configured:
            return Path(configured).expanduser().resolve()

        return (Path(settings.BASE_DIR) / "whatsapp_center" / "session_gateway").resolve()

    def _get_gateway_log_file(self) -> Path:
        configured = getattr(settings, "WHATSAPP_GATEWAY_LOG_FILE", "")
        if configured:
            return Path(configured).expanduser().resolve()

        return (Path(settings.BASE_DIR) / "logs" / "whatsapp_gateway.log").resolve()

    def _resolve_gateway_command(self, gateway_dir: Path) -> list[str]:
        """
        اختيار أمر تشغيل الجت واي بشكل أنظف:
        - على ويندوز: نفضّل node server.js مباشرة
        - fallback إلى npm run start إذا لزم
        """
        server_js = gateway_dir / "server.js"

        node_candidates = ["node.exe", "node"] if os.name == "nt" else ["node"]
        for candidate in node_candidates:
            node_path = shutil.which(candidate)
            if node_path and server_js.exists():
                return [node_path, str(server_js)]

        npm_candidates = ["npm.cmd", "npm.exe", "npm"] if os.name == "nt" else ["npm"]
        for candidate in npm_candidates:
            npm_path = shutil.which(candidate)
            if npm_path:
                return [npm_path, "run", "start"]

        if server_js.exists():
            return ["node", str(server_js)]

        return ["npm", "run", "start"]

    # --------------------------------------------------------
    # 🧾 Logging
    # --------------------------------------------------------
    def _write_boot_log(self, message: str) -> None:
        log_file = self._get_gateway_log_file()
        log_file.parent.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] {message}\n")

    # --------------------------------------------------------
    # ▶️ Process Launch
    # --------------------------------------------------------
    def _start_gateway_process(self) -> bool:
        gateway_dir = self._get_gateway_dir()
        log_file = self._get_gateway_log_file()

        package_json = gateway_dir / "package.json"
        server_js = gateway_dir / "server.js"

        if not gateway_dir.exists():
            self._write_boot_log(
                f"[ERROR] Gateway directory not found: {gateway_dir}"
            )
            return False

        if not package_json.exists() or not server_js.exists():
            self._write_boot_log(
                f"[ERROR] Missing package.json or server.js inside: {gateway_dir}"
            )
            return False

        launch_command = self._resolve_gateway_command(gateway_dir)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        stdout_handle = log_file.open("a", encoding="utf-8")
        stderr_handle = log_file.open("a", encoding="utf-8")

        popen_kwargs = {
            "cwd": str(gateway_dir),
            "stdout": stdout_handle,
            "stderr": stderr_handle,
            "stdin": subprocess.DEVNULL,
            "env": os.environ.copy(),
        }

        if os.name == "nt":
            creationflags = (
                getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                | getattr(subprocess, "DETACHED_PROCESS", 0)
                | getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            popen_kwargs["creationflags"] = creationflags
            popen_kwargs["startupinfo"] = startupinfo
        else:
            if hasattr(os, "setsid"):
                popen_kwargs["preexec_fn"] = os.setsid

        try:
            subprocess.Popen(
                launch_command,
                **popen_kwargs,
            )
            self._write_boot_log(
                f"[INFO] WhatsApp gateway launch requested using command: {' '.join(launch_command)}"
            )
            return True
        except Exception as exc:
            self._write_boot_log(
                f"[ERROR] Failed to launch WhatsApp gateway: {exc}"
            )
            return False

    # --------------------------------------------------------
    # 🔁 Worker
    # --------------------------------------------------------
    def _autostart_gateway_worker(self) -> None:
        """
        1) يفحص هل الجت واي شغال
        2) لو لا، يشغله
        3) ينتظر حتى يصير /health شغال
        """
        try:
            if self._is_gateway_running():
                self._write_boot_log(
                    "[INFO] WhatsApp gateway already running; skip autostart."
                )
                return

            started = self._start_gateway_process()
            if not started:
                return

            boot_timeout = int(
                getattr(settings, "WHATSAPP_GATEWAY_AUTOSTART_BOOT_TIMEOUT", 25)
            )
            started_at = time.time()

            while (time.time() - started_at) < boot_timeout:
                if self._is_gateway_running():
                    self._write_boot_log(
                        "[INFO] WhatsApp gateway started successfully."
                    )
                    return
                time.sleep(1.0)

            self._write_boot_log(
                "[ERROR] WhatsApp gateway launch was requested but health check did not become ready in time."
            )

        except Exception as exc:
            self._write_boot_log(
                f"[ERROR] Unexpected autostart worker failure: {exc}"
            )