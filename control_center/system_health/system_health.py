# ================================================================
# 📂 control_center/system_health/system_health.py
# 🧠 System Health Engine — V11 Ultra Pro
# ---------------------------------------------------------------
# ✔ يفحص حالة النظام الحقيقية
# ✔ يدعم مستويات الصحة (OK / WARN / DOWN / DEGRADED)
# ✔ فحص الخادم + قاعدة البيانات + Biotime
# ✔ يعيد Snapshot جاهز للاستهلاك عبر API
# ================================================================

import psutil
import time
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from biotime_center.models import BiotimeSyncLog


def check_server_health():
    """فحص موارد الخادم"""
    cpu = psutil.cpu_percent(interval=0.4)
    ram = psutil.virtual_memory().percent

    status = "OK"
    if cpu > 85 or ram > 85:
        status = "DEGRADED"
    if cpu > 95 or ram > 95:
        status = "DOWN"

    return {
        "cpu": cpu,
        "ram": ram,
        "status": status
    }


def check_db_health():
    """فحص الاتصال بقاعدة البيانات"""
    start = time.time()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
        latency = round((time.time() - start) * 1000, 2)

        status = "OK"
        if latency > 200:
            status = "WARN"
        if latency > 500:
            status = "DOWN"

        return {
            "latency": latency,
            "status": status
        }

    except Exception:
        return {
            "latency": None,
            "status": "DOWN"
        }


def check_biotime_health():
    last_log = BiotimeSyncLog.objects.order_by("-timestamp").first()

    if not last_log:
        return {"status": "DOWN", "last_sync": None}

    last_sync = last_log.timestamp
    diff = (timezone.now() - last_sync).total_seconds()

    if last_log.status == "FAILED":
        status = "DOWN"
    elif diff < 120:
        status = "OK"
    elif diff < 300:
        status = "WARN"
    else:
        status = "DEGRADED"

    return {
        "status": status,
        "last_sync": last_sync.strftime("%Y-%m-%d %H:%M"),
        "devices": last_log.devices_synced,
        "employees": last_log.employees_synced,
        "logs": last_log.logs_synced,
    }


def get_system_health():
    """📌 Snapshot نهائي — يتم استدعاؤه من الـ API"""
    cache_key = "system_health_snapshot"
    cached = cache.get(cache_key)

    # Snapshot Cache لمدة 10 ثواني
    if cached:
        return cached

    server = check_server_health()
    db = check_db_health()
    biotime = check_biotime_health()

    final_status = "OK"
    all_status = [server["status"], db["status"], biotime["status"]]

    if "DOWN" in all_status:
        final_status = "DOWN"
    elif "DEGRADED" in all_status:
        final_status = "DEGRADED"
    elif "WARN" in all_status:
        final_status = "WARN"

    snapshot = {
        "server": server,
        "db": db,
        "biotime": biotime,
        "overall": final_status,
        "timestamp": timezone.now().strftime("%H:%M:%S"),
    }

    cache.set(cache_key, snapshot, 10)
    return snapshot
