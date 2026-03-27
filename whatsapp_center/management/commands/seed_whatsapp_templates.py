# ============================================================
# 📂 whatsapp_center/management/commands/seed_whatsapp_templates.py
# 🛠 Primey HR Cloud - Seed WhatsApp Templates Command
# ------------------------------------------------------------
# ✅ Seed System WhatsApp Templates
# ✅ Seed Company WhatsApp Templates
# ✅ Safe / Idempotent
# ✅ Supports single company or all companies
# ============================================================

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from company_manager.models import Company
from whatsapp_center.services import (
    ensure_company_default_whatsapp_templates,
    ensure_system_default_whatsapp_templates,
)


class Command(BaseCommand):
    help = "Seed default WhatsApp templates for system and/or companies."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--scope",
            type=str,
            choices=["system", "company", "all"],
            default="all",
            help="Choose which templates to seed: system, company, or all.",
        )
        parser.add_argument(
            "--company-id",
            type=int,
            default=None,
            help="Seed company templates for a specific company ID only.",
        )
        parser.add_argument(
            "--all-companies",
            action="store_true",
            help="Seed company templates for all companies.",
        )

    def handle(self, *args, **options) -> None:
        scope = options["scope"]
        company_id = options.get("company_id")
        all_companies = options.get("all_companies", False)

        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("🚀 Primey HR Cloud | Seed WhatsApp Templates"))
        self.stdout.write("=" * 68)

        if scope in {"system", "all"}:
            self._seed_system_templates()

        if scope in {"company", "all"}:
            self._seed_company_templates(
                company_id=company_id,
                all_companies=all_companies,
            )

        self.stdout.write("=" * 68)
        self.stdout.write(self.style.SUCCESS("✅ Done"))
        self.stdout.write("")

    # ========================================================
    # 🖥 System
    # ========================================================

    def _seed_system_templates(self) -> None:
        self.stdout.write(self.style.WARNING("📌 Seeding SYSTEM WhatsApp templates..."))

        result = ensure_system_default_whatsapp_templates()

        self.stdout.write(
            self.style.SUCCESS(
                f"   SYSTEM | created={result['created']} "
                f"| existing={result['existing']} "
                f"| total={result['total_system_templates']}"
            )
        )

    # ========================================================
    # 🏢 Company
    # ========================================================

    def _seed_company_templates(
        self,
        *,
        company_id: int | None,
        all_companies: bool,
    ) -> None:
        companies = self._resolve_companies(
            company_id=company_id,
            all_companies=all_companies,
        )

        if not companies:
            self.stdout.write(
                self.style.WARNING("⚠️ No companies selected for company template seeding.")
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"📌 Seeding COMPANY WhatsApp templates for {len(companies)} company(s)..."
            )
        )

        total_created = 0
        total_existing = 0

        for company in companies:
            with transaction.atomic():
                result = ensure_company_default_whatsapp_templates(company=company)

            total_created += int(result.get("created", 0) or 0)
            total_existing += int(result.get("existing", 0) or 0)

            self.stdout.write(
                self.style.SUCCESS(
                    f"   COMPANY #{company.id} | {self._company_label(company)} "
                    f"| created={result['created']} "
                    f"| existing={result['existing']} "
                    f"| total={result['total_company_templates']}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"   COMPANY SUMMARY | created={total_created} | existing={total_existing}"
            )
        )

    # ========================================================
    # 🔍 Helpers
    # ========================================================

    def _resolve_companies(
        self,
        *,
        company_id: int | None,
        all_companies: bool,
    ) -> list[Company]:
        if company_id:
            company = Company.objects.filter(pk=company_id).first()
            if not company:
                raise CommandError(f"Company with ID {company_id} was not found.")
            return [company]

        if all_companies:
            return list(Company.objects.all().order_by("id"))

        return []

    def _company_label(self, company: Company) -> str:
        for attr_name in ("name", "company_name", "legal_name", "title"):
            value = getattr(company, attr_name, "")
            if value:
                return str(value).strip()
        return f"Company {company.id}"