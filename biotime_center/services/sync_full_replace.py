# ============================================================
# 🔄 Full Replace Sync Layer
# ============================================================
# ✔ Company Scoped (MT-6 Strict)
# ✔ Uses Existing Patch Functions
# ✔ Idempotent Safe
# ✔ Production Ready
# ✔ No Breaking Changes
# ✔ Developed for Mham Cloud 2026
# ============================================================

import logging

from biotime_center.models import BiotimeEmployee
from biotime_center.services.sync_snapshot import build_employee_snapshot
from biotime_center.sync_service import (
    patch_employee_name,
    patch_employee_department,
    patch_employee_position,
    patch_employee_areas_replace,
)

logger = logging.getLogger(__name__)


def sync_employee_full_replace(employee):
    """
    🔁 Full Replace Sync
    Primey = Source of Truth
    """

    if not employee:
        return False

    company = getattr(employee, "company", None)

    if not company:
        logger.error("❌ Full Replace Failed | Company missing")
        return False

    try:
        # =====================================================
        # 🔎 Resolve BiotimeEmployee (Correct FK = linked_employee)
        # =====================================================
        biotime_emp = BiotimeEmployee.objects.filter(
            company=company,
            linked_employee=employee,
        ).first()

        if not biotime_emp:
            logger.warning(
                "⚠️ Full Replace Skipped | BiotimeEmployee not found | employee=%s",
                employee.id,
            )
            return False

        biotime_employee_code = biotime_emp.employee_id

        # =====================================================
        # 📸 Build Snapshot
        # =====================================================
        snapshot = build_employee_snapshot(employee)

        logger.warning(
            "[FULL SYNC] Employee %s → %s",
            employee.id,
            snapshot,
        )

        # =====================================================
        # 🟦 1) Name
        # =====================================================
        patch_employee_name(
            company=company,
            employee_id=biotime_employee_code,
            full_name=snapshot.get("name"),
        )

        # =====================================================
        # 🟦 2) Department
        # =====================================================
        if employee.department and employee.department.biotime_code:
            patch_employee_department(
                company=company,
                employee_id=biotime_employee_code,
                dept_code=employee.department.biotime_code,
            )

        # =====================================================
        # 🟦 3) Position
        # =====================================================
        if employee.job_title and employee.job_title.biotime_code:
            patch_employee_position(
                company=company,
                employee_id=biotime_employee_code,
                position_code=employee.job_title.biotime_code,
            )

        # =====================================================
        # 🟦 4) Areas (Authoritative Replace)
        # =====================================================
        area_codes = []

        if hasattr(employee, "branches"):
            for branch in employee.branches.all():
                if branch.biotime_code:
                    area_codes.append(branch.biotime_code)

        if area_codes:
            patch_employee_areas_replace(
                employee_id=biotime_employee_code,
                area_codes=area_codes,
            )

        return True

    except Exception:
        logger.exception("❌ Full Replace Sync Exception")
        return False
