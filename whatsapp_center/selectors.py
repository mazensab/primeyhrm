# ============================================================
# 📂 whatsapp_center/selectors.py
# Primey HR Cloud - WhatsApp Selectors
# ============================================================

from __future__ import annotations

from typing import Optional

from .models import (
    CompanyWhatsAppConfig,
    ScopeType,
    SystemWhatsAppConfig,
    WhatsAppTemplate,
)


# ============================================================
# 🔧 Internal Helpers
# ============================================================

def _normalize_language_code(language_code: str) -> str:
    value = (language_code or "").strip().lower()
    return value if value in {"ar", "en"} else "ar"


def _build_language_candidates(language_code: str) -> list[str]:
    """
    ترتيب مرن للغات:
    - اللغة المطلوبة أولًا
    - ثم العربية
    - ثم الإنجليزية
    - بدون تكرار
    """
    normalized = _normalize_language_code(language_code)
    candidates: list[str] = []

    for item in [normalized, "ar", "en"]:
        if item not in candidates:
            candidates.append(item)

    return candidates


def _get_company_template_candidate(
    *,
    company,
    event_code: str,
    language_code: str,
):
    return (
        WhatsAppTemplate.objects
        .filter(
            scope_type=ScopeType.COMPANY,
            company=company,
            event_code=event_code,
            language_code=language_code,
            is_active=True,
        )
        .order_by("-is_default", "-version", "-id")
        .first()
    )


def _get_system_template_candidate(
    *,
    event_code: str,
    language_code: str,
):
    return (
        WhatsAppTemplate.objects
        .filter(
            scope_type=ScopeType.SYSTEM,
            company__isnull=True,
            event_code=event_code,
            language_code=language_code,
            is_active=True,
        )
        .order_by("-is_default", "-version", "-id")
        .first()
    )


# ============================================================
# ⚙️ Config Selectors
# ============================================================

def get_active_system_whatsapp_config() -> Optional[SystemWhatsAppConfig]:
    return (
        SystemWhatsAppConfig.objects
        .filter(is_enabled=True, is_active=True)
        .order_by("-id")
        .first()
    )


def get_active_company_whatsapp_config(company) -> Optional[CompanyWhatsAppConfig]:
    if not company:
        return None

    return (
        CompanyWhatsAppConfig.objects
        .filter(company=company, is_enabled=True, is_active=True)
        .select_related("company")
        .order_by("-id")
        .first()
    )


# ============================================================
# 📨 Template Selector
# ============================================================

def get_whatsapp_template(
    *,
    scope_type: str,
    event_code: str,
    language_code: str = "ar",
    company=None,
):
    """
    جلب أفضل قالب متاح بترتيب مرن وآمن:

    1) إذا كان Company Scope ومعنا company:
       - نحاول قالب الشركة باللغة المطلوبة
       - ثم العربية
       - ثم الإنجليزية

    2) بعدها دائمًا نحاول System Scope كـ fallback:
       - باللغة المطلوبة
       - ثم العربية
       - ثم الإنجليزية
    """
    language_candidates = _build_language_candidates(language_code)

    # --------------------------------------------------------
    # 1) Company Scope Templates
    # --------------------------------------------------------
    if scope_type == ScopeType.COMPANY and company:
        for lang in language_candidates:
            company_template = _get_company_template_candidate(
                company=company,
                event_code=event_code,
                language_code=lang,
            )
            if company_template:
                return company_template

    # --------------------------------------------------------
    # 2) System Scope Fallback
    # --------------------------------------------------------
    for lang in language_candidates:
        system_template = _get_system_template_candidate(
            event_code=event_code,
            language_code=lang,
        )
        if system_template:
            return system_template

    return None