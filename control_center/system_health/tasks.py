# ================================================================
# 📂 control_center/system_health/tasks.py
# 🔁 Background Task — Health Snapshot Auto Refresh
# V11 Ultra Pro
# ---------------------------------------------------------------
# ✔ يقوم بتحديث Snapshot في الخلفية كل 10 ثواني
# ✔ يخفف الحمل على السيرفر عند قراءة الواجهة
# ================================================================

from .system_health import get_system_health


def refresh_system_health():
    """
    🔁 يتم استدعاؤه بواسطة APScheduler كل 10 ثوانٍ
    """
    snapshot = get_system_health()
    return snapshot
