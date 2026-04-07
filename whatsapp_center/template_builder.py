# ============================================================
# 📂 whatsapp_center/template_builder.py
# Mham Cloud - WhatsApp Template Builder
# ============================================================

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class BuiltWhatsAppMessage:
    header_text: str = ""
    body_text: str = ""
    footer_text: str = ""


# يدعم:
# {full_name}
# {{full_name}}
_PLACEHOLDER_PATTERN = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}|\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _safe_format(text: str, context: dict[str, Any]) -> str:
    """
    تنسيق آمن للنصوص.

    يدعم الصيغتين:
    - {key}
    - {{key}}

    وإذا كان المفتاح غير موجود يتركه كما هو بدون كسر الرسالة.
    """
    if not text:
        return ""

    if not context:
        return text

    def replace_match(match: re.Match[str]) -> str:
        key = match.group(1) or match.group(2)

        if not key:
            return match.group(0)

        if key not in context:
            return match.group(0)

        value = context.get(key)

        if value is None:
            return ""

        return str(value)

    try:
        return _PLACEHOLDER_PATTERN.sub(replace_match, text)
    except Exception:
        return text


def build_message_from_template(template, context: dict[str, Any]) -> BuiltWhatsAppMessage:
    """
    بناء الرسالة النهائية من القالب + context.
    """
    return BuiltWhatsAppMessage(
        header_text=_safe_format(getattr(template, "header_text", ""), context),
        body_text=_safe_format(getattr(template, "body_text", ""), context),
        footer_text=_safe_format(getattr(template, "footer_text", ""), context),
    )