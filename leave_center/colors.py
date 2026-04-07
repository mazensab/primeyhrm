# ======================================================================
# 🎨 Mham Cloud V14 — Enterprise Color Stack
# ----------------------------------------------------------------------
# ملف مركزي لتحديد الألوان الرسمية لأنواع الإجازات (Leave Types)
# هذا الملف يُستخدم في:
#   - Leave Calendar (FullCalendar)
#   - Dashboard KPIs
#   - Leave List Table
#   - Leave Detail Timeline
#   - API Endpoints
#
# الهدف:
#   - توحيد الألوان عبر كل النظام
#   - سهولة الإدارة والتطوير المستقبلي
# ======================================================================


# ----------------------------------------------------------------------
# 🔵 خريطة الألوان (حسب التصنيف Category في LeaveType)
# ----------------------------------------------------------------------
CATEGORY_COLORS = {
    "annual": {
        "label": "إجازة سنوية",
        "bg": "#0A4D3C",
        "text": "#FFFFFF",
        "light": "rgba(10, 77, 60, 0.22)",
        "border": "rgba(10, 77, 60, 0.45)",
    },
    "sick": {
        "label": "إجازة مرضية",
        "bg": "#3B82F6",
        "text": "#FFFFFF",
        "light": "rgba(59, 130, 246, 0.22)",
        "border": "rgba(59, 130, 246, 0.45)",
    },
    "unpaid": {
        "label": "إجازة بدون راتب",
        "bg": "#6B7280",
        "text": "#FFFFFF",
        "light": "rgba(107, 114, 128, 0.22)",
        "border": "rgba(107, 114, 128, 0.45)",
    },
    "maternity": {
        "label": "إجازة أمومة",
        "bg": "#EC4899",
        "text": "#FFFFFF",
        "light": "rgba(236, 72, 153, 0.22)",
        "border": "rgba(236, 72, 153, 0.45)",
    },
    "marriage": {
        "label": "إجازة زواج",
        "bg": "#8B5CF6",
        "text": "#FFFFFF",
        "light": "rgba(139, 92, 246, 0.22)",
        "border": "rgba(139, 92, 246, 0.45)",
    },
    "death": {
        "label": "إجازة وفاة",
        "bg": "#F97316",
        "text": "#FFFFFF",
        "light": "rgba(249, 115, 22, 0.22)",
        "border": "rgba(249, 115, 22, 0.45)",
    },
    "hajj": {
        "label": "إجازة حج",
        "bg": "#059669",
        "text": "#FFFFFF",
        "light": "rgba(5, 150, 105, 0.22)",
        "border": "rgba(5, 150, 105, 0.45)",
    },
    "study": {
        "label": "إجازة دراسية",
        "bg": "#14B8A6",
        "text": "#FFFFFF",
        "light": "rgba(20, 184, 166, 0.22)",
        "border": "rgba(20, 184, 166, 0.45)",
    },
}
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# 🟦 دالة مساعده — جلب ألوان النوع
# ----------------------------------------------------------------------
def get_leave_colors(category: str):
    """
    تُرجع ألوان النوع بناءً على Category.
    إذا لم يكن التصنيف معروف → يرجع لون رمادي افتراضي.
    """

    return CATEGORY_COLORS.get(category, {
        "label": "غير مصنف",
        "bg": "#9CA3AF",
        "text": "#FFFFFF",
        "light": "rgba(156, 163, 175, 0.22)",
        "border": "rgba(156, 163, 175, 0.45)",
    })
# ======================================================================
# 🎨 Mham Cloud V14 — Enterprise Color Stack
# ----------------------------------------------------------------------
# ملف مركزي لتحديد الألوان الرسمية لأنواع الإجازات (Leave Types)
# ======================================================================


CATEGORY_COLORS = {
    "annual": {
        "label": "إجازة سنوية",
        "bg": "#0A4D3C",
        "text": "#FFFFFF",
        "light": "rgba(10, 77, 60, 0.22)",
        "border": "rgba(10, 77, 60, 0.45)",
    },
    "sick": {
        "label": "إجازة مرضية",
        "bg": "#3B82F6",
        "text": "#FFFFFF",
        "light": "rgba(59, 130, 246, 0.22)",
        "border": "rgba(59, 130, 246, 0.45)",
    },
    "unpaid": {
        "label": "إجازة بدون راتب",
        "bg": "#6B7280",
        "text": "#FFFFFF",
        "light": "rgba(107, 114, 128, 0.22)",
        "border": "rgba(107, 114, 128, 0.45)",
    },
    "maternity": {
        "label": "إجازة أمومة",
        "bg": "#EC4899",
        "text": "#FFFFFF",
        "light": "rgba(236, 72, 153, 0.22)",
        "border": "rgba(236, 72, 153, 0.45)",
    },
    "marriage": {
        "label": "إجازة زواج",
        "bg": "#8B5CF6",
        "text": "#FFFFFF",
        "light": "rgba(139, 92, 246, 0.22)",
        "border": "rgba(139, 92, 246, 0.45)",
    },
    "death": {
        "label": "إجازة وفاة",
        "bg": "#F97316",
        "text": "#FFFFFF",
        "light": "rgba(249, 115, 22, 0.22)",
        "border": "rgba(249, 115, 22, 0.45)",
    },
    "hajj": {
        "label": "إجازة حج",
        "bg": "#059669",
        "text": "#FFFFFF",
        "light": "rgba(5, 150, 105, 0.22)",
        "border": "rgba(5, 150, 105, 0.45)",
    },
    "study": {
        "label": "إجازة دراسية",
        "bg": "#14B8A6",
        "text": "#FFFFFF",
        "light": "rgba(20, 184, 166, 0.22)",
        "border": "rgba(20, 184, 166, 0.45)",
    },
}


def get_leave_colors(category: str):
    """
    تُرجع ألوان النوع بناءً على Category.
    إذا لم يكن التصنيف معروف → يرجع لون رمادي افتراضي.
    """
    return CATEGORY_COLORS.get(category, {
        "label": "غير مصنف",
        "bg": "#9CA3AF",
        "text": "#FFFFFF",
        "light": "rgba(156, 163, 175, 0.22)",
        "border": "rgba(156, 163, 175, 0.45)",
    })



# ======================================================================
# ⭐ LeaveTypeColorEngine — V2 Ultra Pro
# ----------------------------------------------------------------------
# محرك ألوان ذكي للتعامل مع الألوان داخل Views و API و Dashboard
# ======================================================================

class LeaveTypeColorEngine:
    """
    🧠 محرك ألوان رسمي لنظام Mham Cloud
    - يعيد Theme شامل (أيقونة + خلفية + حدود + نص)
    - جاهز للـ Calendar + Dashboard + API
    """

    @staticmethod
    def get_theme(category: str) -> dict:
        """
        🎨 يعيد Theme كامل للنوع:
        {
            "label": "...",
            "bg": "...",
            "text": "...",
            "light": "...",
            "border": "..."
        }
        """
        return get_leave_colors(category)

    @staticmethod
    def for_calendar(category: str) -> dict:
        """
        📅 تحويل الألوان إلى صيغة FullCalendar:
        {
            "backgroundColor": "...",
            "textColor": "...",
            "borderColor": "..."
        }
        """
        c = get_leave_colors(category)
        return {
            "backgroundColor": c["bg"],
            "textColor": c["text"],
            "borderColor": c["border"],
        }

    @staticmethod
    def for_kpis(category: str) -> dict:
        """
        📊 ألوان KPIs:
        خلفية خفيفة + نص داكن
        """
        c = get_leave_colors(category)
        return {
            "background": c["light"],
            "color": c["bg"],
            "border": c["border"],
        }

    @staticmethod
    def for_badge(category: str) -> dict:
        """
        🏷️ شارة صغيرة (Badge)
        """
        c = get_leave_colors(category)
        return {
            "bg": c["bg"],
            "text": c["text"],
            "border": c["border"],
        }

# ----------------------------------------------------------------------
# 🟨 للاستخدام في التقويم:
#    مثال:
#    color = get_leave_colors(request.leave_type.category)
#    event["backgroundColor"] = color["bg"]
#    event["textColor"] = color["text"]
#    event["borderColor"] = color["border"]
# ----------------------------------------------------------------------
