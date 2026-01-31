# ================================================================
# 🕒 Holiday Backfill APScheduler Job
# Phase H.7 — SAFE / IDEMPOTENT / NIGHTLY
# ================================================================

from company_manager.models import Company
from attendance_center.services.holiday_backfill_engine import HolidayBackfillEngine


def run_holiday_backfill_job():
    """
    🔁 Nightly Holiday Backfill Job
    - Safe to re-run
    - Company scoped
    - Idempotent
    """

    stats = {
        "companies": 0,
        "total_updated": 0,
        "total_skipped": 0,
    }

    for company in Company.objects.filter(is_active=True):
        result = HolidayBackfillEngine.run(
            company=company,
            dry_run=False
        )

        stats["companies"] += 1
        stats["total_updated"] += result.get("updated", 0)
        stats["total_skipped"] += result.get("skipped", 0)

    return stats
