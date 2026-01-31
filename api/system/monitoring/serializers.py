from system_log.models import SystemLog


# ============================================================
# 📦 Monitoring Serializers — FINAL
# ============================================================

def serialize_log(log: SystemLog):
    return {
        "id": log.id,
        "module": log.module,
        "action": log.action,
        "severity": log.severity,
        "message": log.message,
        "user": log.user.get_full_name() if log.user else "—",
        "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
