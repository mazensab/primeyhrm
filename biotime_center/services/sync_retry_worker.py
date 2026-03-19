# ============================================================
# 🔄 Sync Retry Worker — Full Snapshot Replace (FINAL CLEAN)
# ============================================================

from django.db import transaction
from biotime_center.models import BiotimeSyncState
from biotime_center.services.sync_snapshot import build_employee_snapshot


def run_sync_retry():

    processed = []

    with transaction.atomic():

        dirty_states = BiotimeSyncState.objects.select_for_update().filter(
            is_dirty=True,
            retry_count__lt=5
        )

        for state in dirty_states:

            try:
                employee = state.employee
                from biotime_center.services.sync_full_replace import sync_employee_full_replace

                new_snapshot = sync_employee_full_replace(employee)

                state.mark_success(new_snapshot)
                processed.append(employee.id)

            except Exception as e:
                state.mark_failure(str(e))

    return processed
