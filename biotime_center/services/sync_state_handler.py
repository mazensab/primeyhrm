# ============================================================
# 🔄 Sync State Handler — Snapshot Diff (STEP 2)
# ============================================================

from biotime_center.models import BiotimeSyncState
from biotime_center.services.sync_snapshot import build_employee_snapshot


def handle_employee_sync_event(employee):
    """
    - يبني snapshot جديد
    - يقارنه مع آخر snapshot متزامن
    - يحدد الحقول المتغيرة فقط
    - يعلم السجل Dirty عند وجود اختلاف
    """

    if not employee or not getattr(employee, "company", None):
        return

    state, _ = BiotimeSyncState.objects.get_or_create(
        company=employee.company,
        employee=employee,
    )

    new_snapshot = build_employee_snapshot(employee)
    old_snapshot = state.last_synced_snapshot or {}

    dirty_fields = []

    for key, new_value in new_snapshot.items():
        old_value = old_snapshot.get(key)
        if new_value != old_value:
            dirty_fields.append(key)

    if dirty_fields:
        state.mark_dirty(dirty_fields)
