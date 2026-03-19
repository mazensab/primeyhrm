# ============================================================
# 📂 whatsapp_center/utils.py
# Primey HR Cloud - WhatsApp Utilities
# ============================================================

from __future__ import annotations

import re
from typing import Optional


# ============================================================
# 🌍 Defaults
# ============================================================

DEFAULT_COUNTRY_CODE = "966"


# ============================================================
# 🔧 Text Helper
# ============================================================

def safe_text(value: Optional[str]) -> str:
    """
    إرجاع نص آمن دائمًا.
    """
    return (value or "").strip()


# ============================================================
# 📱 Phone Helpers
# ============================================================

def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def normalize_phone_number(phone: str, default_country_code: str = DEFAULT_COUNTRY_CODE) -> str:
    """
    تنظيف وتوحيد رقم الجوال بصيغة دولية.

    يدعم بشكل جيد:
    - +9665XXXXXXXX
    - 009665XXXXXXXX
    - 9665XXXXXXXX
    - 05XXXXXXXX
    - 5XXXXXXXX

    المخرجات النهائية دائمًا بصيغة:
    +<country_code><number>

    ملاحظات:
    - الافتراضي هنا موجه للسعودية (966)
    - لا يحاول تخمينات معقدة جدًا خارج الأنماط الشائعة
    """
    raw = safe_text(phone)
    if not raw:
        return ""

    country_code = _digits_only(default_country_code) or DEFAULT_COUNTRY_CODE

    # --------------------------------------------------------
    # 1) إزالة المسافات والرموز مع الإبقاء على +
    # --------------------------------------------------------
    cleaned = re.sub(r"[^\d+]", "", raw)

    if not cleaned:
        return ""

    # --------------------------------------------------------
    # 2) تحويل 00XXXXXXXX إلى +XXXXXXXX
    # --------------------------------------------------------
    if cleaned.startswith("00"):
        cleaned = f"+{cleaned[2:]}"

    # --------------------------------------------------------
    # 3) لو يبدأ بـ + نتحقق فقط من الرقم الداخلي
    # --------------------------------------------------------
    if cleaned.startswith("+"):
        digits = _digits_only(cleaned)

        if not digits:
            return ""

        normalized = f"+{digits}"
        if re.match(r"^\+[1-9]\d{7,14}$", normalized):
            return normalized
        return ""

    # من هنا نتعامل مع أرقام بدون +
    digits = _digits_only(cleaned)

    if not digits:
        return ""

    # --------------------------------------------------------
    # 4) دعم الأرقام السعودية المحلية الشائعة
    # --------------------------------------------------------
    # مثال: 05xxxxxxxx -> +9665xxxxxxxx
    if country_code == "966":
        if digits.startswith("05") and len(digits) == 10:
            normalized = f"+966{digits[1:]}"
            if re.match(r"^\+[1-9]\d{7,14}$", normalized):
                return normalized

        # مثال: 5xxxxxxxx -> +9665xxxxxxxx
        if digits.startswith("5") and len(digits) == 9:
            normalized = f"+966{digits}"
            if re.match(r"^\+[1-9]\d{7,14}$", normalized):
                return normalized

        # مثال: 9665xxxxxxxx -> +9665xxxxxxxx
        if digits.startswith("966") and len(digits) >= 11:
            normalized = f"+{digits}"
            if re.match(r"^\+[1-9]\d{7,14}$", normalized):
                return normalized

    # --------------------------------------------------------
    # 5) لو الرقم يبدو دوليًا لكنه بدون +
    # --------------------------------------------------------
    # مثال: 14155552671 -> +14155552671
    if len(digits) >= 8 and not digits.startswith("0"):
        normalized = f"+{digits}"
        if re.match(r"^\+[1-9]\d{7,14}$", normalized):
            return normalized

    # --------------------------------------------------------
    # 6) fallback للأرقام المحلية الأخرى:
    # إزالة الصفر الأول ثم إضافة كود الدولة
    # --------------------------------------------------------
    local_digits = digits.lstrip("0")
    if local_digits:
        normalized = f"+{country_code}{local_digits}"
        if re.match(r"^\+[1-9]\d{7,14}$", normalized):
            return normalized

    return ""


def is_valid_phone_number(phone: str, default_country_code: str = DEFAULT_COUNTRY_CODE) -> bool:
    """
    تحقق من صيغة الرقم بعد التطبيع.
    """
    if not phone:
        return False

    normalized = normalize_phone_number(phone, default_country_code=default_country_code)
    return bool(re.match(r"^\+[1-9]\d{7,14}$", normalized))