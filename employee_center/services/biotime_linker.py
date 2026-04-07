# ===============================================================
# 📂 Path: employee_center/services/biotime_linker.py
# 🔗 Biotime ↔ Employee Smart Linker — Phase C2 (Real Execution)
# 🧪 Shell-First | Safe | Auditable | Zero Migration
# 👨‍💻 Developed by Mazen — Mham Cloud 2026
# ===============================================================

from django.utils import timezone
from django.db import transaction
import logging
from collections import defaultdict
import re

from biotime_center.models import BiotimeEmployee
from employee_center.models import Employee, SyncLog
from company_manager.models import Company

logger = logging.getLogger(__name__)


# ===============================================================
# 🧠 Helpers
# ===============================================================

VALID_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{2,64}$")


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _has_biometric_data(bio: BiotimeEmployee) -> bool:
    try:
        return bool(
            (bio.enrolled_fingers or 0) > 0 or
            bool(bio.card_number) or
            bool(bio.photo_url)
        )
    except Exception:
        return False


def _is_valid_biotime_code(code: str) -> bool:
    try:
        if not code:
            return False
        if " " in code:
            return False
        return bool(VALID_CODE_PATTERN.match(code))
    except Exception:
        return False


def _calculate_match_score(employee: Employee, bio: BiotimeEmployee) -> int:
    """
    🧠 Smart heuristic scoring (0–100)
    """
    score = 0

    # ---------------------------------------------------
    # 🧩 الاسم (Defensive Access)
    # ---------------------------------------------------
    bio_name = getattr(bio, "full_name", "") or ""
    if _normalize(employee.full_name) in _normalize(bio_name):
        score += 40

    # ---------------------------------------------------
    # 🧩 القسم
    # ---------------------------------------------------
    try:
        if employee.department and bio.department:
            if _normalize(employee.department.name) == _normalize(bio.department):
                score += 20
    except Exception:
        pass

    # ---------------------------------------------------
    # 🧩 بيانات حيوية
    # ---------------------------------------------------
    if _has_biometric_data(bio):
        score += 20

    # ---------------------------------------------------
    # 🧩 حالة التفعيل
    # ---------------------------------------------------
    if bio.is_active:
        score += 10

    # ---------------------------------------------------
    # 🧩 أمان إضافي
    # ---------------------------------------------------
    score += 10

    return min(score, 100)


# ===============================================================
# 🧠 Core Service — Smart Validator + Dry Run + Real Execution
# ===============================================================

def link_biotime_employees(company: Company, execute: bool = False):
    """
    Enhancements up to Phase C2:
    - Phase B4 كامل.
    - Phase C1: Dry Run Preview.
    - Phase C2: Real Execution (Atomic + Idempotent).
    """

    started_at = timezone.now()

    total_employees = 0
    ready = 0
    not_ready = 0
    missing = 0
    failed = 0
    duplicates = 0

    invalid_codes = 0
    biotime_conflicts = 0
    weak_biometric = 0

    warnings = []
    errors = []
    conflicts = []
    orphans = []
    readiness_flags = {}

    # Phase B3
    suggestions = []

    # Phase C1
    dry_run_links = []

    # Phase C2
    executed_links = []
    skipped_links = []

    logger.info("🔵 Starting Smart Biotime Validation (Phase C2)")

    try:
        # -------------------------------------------------------
        # 🎯 Employees
        # -------------------------------------------------------
        employees = (
            Employee.objects
            .select_related("company", "department")
            .filter(company=company)
        )

        total_employees = employees.count()

        # -------------------------------------------------------
        # 🧬 Biotime Index
        # -------------------------------------------------------
        biotime_index = defaultdict(list)
        all_bios = list(BiotimeEmployee.objects.all())

        for bio in all_bios:
            try:
                key = (bio.employee_id or "").strip()
                if key:
                    biotime_index[key].append(bio)
            except Exception:
                continue

        # -------------------------------------------------------
        # 🚦 Core Scan
        # -------------------------------------------------------
        for employee in employees:

            try:
                biotime_code = (employee.biotime_code or "").strip()
                flags = []

                # --------------------------------------------
                # 🧪 Format Validation
                # --------------------------------------------
                if biotime_code and not _is_valid_biotime_code(biotime_code):
                    invalid_codes += 1
                    flags.append("invalid_code_format")

                bios = biotime_index.get(biotime_code, []) if biotime_code else []

                if biotime_code and len(bios) > 1:
                    duplicates += len(bios)
                    biotime_conflicts += 1
                    flags.append("duplicate_in_biotime")

                bio = bios[0] if bios else None

                if biotime_code and not bio:
                    missing += 1
                    flags.append("missing_in_biotime")

                if bio:
                    if not bio.is_active:
                        flags.append("inactive_in_biotime")

                    if not _has_biometric_data(bio):
                        weak_biometric += 1
                        flags.append("no_biometric_data")

                readiness_flags[employee.id] = flags

                if not flags:
                    ready += 1
                else:
                    not_ready += 1

                # ------------------------------------------------
                # 🤖 Phase B3 — Smart Suggestions
                # ------------------------------------------------
                if flags:
                    best_match = None
                    best_score = 0

                    for bio_candidate in all_bios:
                        score = _calculate_match_score(employee, bio_candidate)
                        if score > best_score:
                            best_score = score
                            best_match = bio_candidate

                    if best_match and best_score >= 60:
                        suggestions.append({
                            "employee_id": employee.id,
                            "employee_name": employee.full_name,
                            "suggested_biotime_id": best_match.id,
                            "biotime_name": getattr(best_match, "full_name", "") or "",
                            "score": best_score,
                            "reason": "heuristic_match",
                        })

            except Exception as e:
                failed += 1
                errors.append(str(e))
                logger.exception("❌ Smart Validation Error")

        # -------------------------------------------------------
        # 🧮 Final Status
        # -------------------------------------------------------
        if failed == 0 and duplicates == 0:
            status = "success"
        elif ready > 0:
            status = "partial"
        else:
            status = "failed"

    except Exception as e:
        logger.exception("🔥 Critical Failure")
        status = "failed"
        errors.append(str(e))

    finished_at = timezone.now()

    # ===========================================================
    # 🛡️ Phase B4 — Execution Guard Layer
    # ===========================================================

    blocking_counters = {
        "duplicates": duplicates,
        "invalid_codes": invalid_codes,
        "biotime_conflicts": biotime_conflicts,
        "weak_biometric": weak_biometric,
        "failed": failed,
    }

    blocking_reasons = []

    if duplicates > 0:
        blocking_reasons.append("duplicates_detected")

    if invalid_codes > 0:
        blocking_reasons.append("invalid_codes_detected")

    if biotime_conflicts > 0:
        blocking_reasons.append("biotime_conflicts_detected")

    if weak_biometric > 0:
        blocking_reasons.append("weak_biometric_data_detected")

    if failed > 0:
        blocking_reasons.append("runtime_errors_detected")

    can_execute = len(blocking_reasons) == 0

    execution_decision = {
        "can_execute": can_execute,
        "blocking_reasons": blocking_reasons,
        "blocking_counters": blocking_counters,
    }

    logger.info("🛡️ Execution Decision: %s", execution_decision)

    # ===========================================================
    # 🧪 Phase C1 — Dry Run Execution Engine
    # ===========================================================

    if can_execute:
        for employee in employees:
            flags = readiness_flags.get(employee.id, [])
            if flags:
                continue

            biotime_code = (employee.biotime_code or "").strip()
            bios = biotime_index.get(biotime_code, [])
            bio = bios[0] if bios else None

            if not bio:
                continue

            dry_run_links.append({
                "employee_id": employee.id,
                "employee_name": employee.full_name,
                "biotime_employee_id": bio.id,
                "biotime_name": getattr(bio, "full_name", "") or "",
                "biotime_code": biotime_code,
                "mode": "dry_run",
            })

    # ===========================================================
    # 🚀 Phase C2 — Real Execution Engine (Atomic)
    # ===========================================================

    if execute and can_execute and dry_run_links:

        logger.info("🚀 Starting REAL execution (Atomic Linking)")

        try:
            with transaction.atomic():

                for link in dry_run_links:
                    employee = Employee.objects.select_for_update().get(
                        id=link["employee_id"]
                    )
                    bio = BiotimeEmployee.objects.get(
                        id=link["biotime_employee_id"]
                    )

                    # -------------------------------
                    # 🛡️ Idempotency Guard
                    # -------------------------------
                    already_linked = False

                    if hasattr(employee, "biotime_employee"):
                        already_linked = bool(employee.biotime_employee_id)

                    if already_linked:
                        skipped_links.append({
                            "employee_id": employee.id,
                            "reason": "already_linked",
                        })
                        continue

                    # -------------------------------
                    # 🔗 Safe Linking (Defensive)
                    # -------------------------------
                    if hasattr(employee, "biotime_employee"):
                        employee.biotime_employee = bio
                        employee.save(update_fields=["biotime_employee"])
                        executed_links.append({
                            "employee_id": employee.id,
                            "biotime_employee_id": bio.id,
                        })

                    elif hasattr(employee, "biotime_employee_id"):
                        employee.biotime_employee_id = bio.id
                        employee.save(update_fields=["biotime_employee_id"])
                        executed_links.append({
                            "employee_id": employee.id,
                            "biotime_employee_id": bio.id,
                        })

                    else:
                        # ✅ لا نكسر التنفيذ — نسجل تخطي ذكي
                        skipped_links.append({
                            "employee_id": employee.id,
                            "biotime_employee_id": bio.id,
                            "reason": "no_biotime_relation_field",
                        })
                        continue

        except Exception as e:
            logger.exception("🔥 Execution Failed — Rolled Back")
            errors.append(str(e))
            status = "failed"

    # ===========================================================
    # 🧾 Audit Log
    # ===========================================================

    try:
        SyncLog.objects.create(
            company=company,
            sync_type=(
                "biotime_link_execute"
                if execute else
                "biotime_link_validation"
            ),
            status=status,
            total_records=total_employees,
            success_count=len(executed_links) if execute else ready,
            failed_count=failed + duplicates,
            error_message=(
                "\n".join(errors + warnings + conflicts + orphans)
                if (errors or warnings or conflicts or orphans)
                else None
            ),
            started_at=started_at,
            finished_at=timezone.now(),
        )
    except Exception:
        pass

    # ===========================================================
    # 📦 Final Result
    # ===========================================================

    result = {
        "status": status,
        "total_employees": total_employees,
        "ready": ready,
        "not_ready": not_ready,
        "missing_in_biotime": missing,
        "duplicates": duplicates,
        "invalid_codes": invalid_codes,
        "biotime_conflicts": biotime_conflicts,
        "weak_biometric": weak_biometric,
        "failed": failed,
        "warnings": warnings,
        "errors": errors,
        "conflicts": conflicts,
        "orphans": orphans,
        "readiness_flags": readiness_flags,

        # Phase B3
        "suggestions": suggestions,
        "suggestions_count": len(suggestions),

        # Phase B4
        "can_execute": can_execute,
        "blocking_reasons": blocking_reasons,
        "blocking_counters": blocking_counters,
        "execution_decision": execution_decision,

        # Phase C1
        "dry_run_links": dry_run_links,
        "dry_run_count": len(dry_run_links),
        "dry_run_preview": dry_run_links[:20],

        # Phase C2
        "executed_links": executed_links,
        "skipped_links": skipped_links,

        "started_at": started_at,
        "finished_at": timezone.now(),
    }

    logger.info("✅ Final Result: %s", {
        "execute": execute,
        "can_execute": can_execute,
        "dry_run": len(dry_run_links),
        "executed": len(executed_links),
        "skipped": len(skipped_links),
    })

    return result
