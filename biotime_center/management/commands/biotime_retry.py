# biotime_center/management/commands/biotime_retry.py

from django.core.management.base import BaseCommand
from biotime_center.services.sync_retry_worker import run_sync_retry


class Command(BaseCommand):
    help = "Run Biotime Sync Retry Worker"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("🚀 Running Biotime Retry Worker..."))

        processed = run_sync_retry()

        if processed:
            self.stdout.write(
                self.style.SUCCESS(f"✔ Synced Employees: {processed}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✔ No dirty records found.")
            )
