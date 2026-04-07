# ============================================================
# 🧩 App Catalog — V1 (FINAL)
# Mham Cloud
# ============================================================

from typing import Dict, List

# ------------------------------------------------------------
# Stable App Keys (DO NOT CHANGE)
# ------------------------------------------------------------

APP_HR_CORE = "HR_CORE"
APP_ATTENDANCE = "ATTENDANCE"
APP_PAYROLL = "PAYROLL"
APP_LEAVE = "LEAVE"
APP_PERFORMANCE = "PERFORMANCE"
APP_BIOTIME = "BIOTIME"
APP_ANALYTICS = "ANALYTICS"
APP_NOTIFICATIONS = "NOTIFICATIONS"
APP_DOCUMENTS = "DOCUMENTS"


# ------------------------------------------------------------
# App Catalog (Source of Truth)
# ------------------------------------------------------------

APP_CATALOG: Dict[str, dict] = {
    APP_HR_CORE: {
        "label": "إدارة الموظفين",
        "description": "الملفات الوظيفية، العقود، الأقسام، المسميات",
        "core": True,
    },
    APP_ATTENDANCE: {
        "label": "الحضور والانصراف",
        "description": "الحضور، الانصراف، الورديات، التأخيرات",
        "core": False,
    },
    APP_PAYROLL: {
        "label": "الرواتب",
        "description": "الرواتب، الاستحقاقات، الاستقطاعات",
        "core": False,
    },
    APP_LEAVE: {
        "label": "الإجازات",
        "description": "إدارة الإجازات والموافقات",
        "core": False,
    },
    APP_PERFORMANCE: {
        "label": "تقييم الأداء",
        "description": "الأهداف، التقييم، التحليلات",
        "core": False,
    },
    APP_BIOTIME: {
        "label": "Biotime",
        "description": "تكامل أجهزة البصمة",
        "core": False,
    },
    APP_ANALYTICS: {
        "label": "التحليلات",
        "description": "تقارير وذكاء أعمال",
        "core": False,
    },
    APP_NOTIFICATIONS: {
        "label": "الإشعارات",
        "description": "تنبيهات النظام والبريد",
        "core": False,
    },
    APP_DOCUMENTS: {
        "label": "المستندات",
        "description": "إدارة ملفات ومستندات الشركة",
        "core": False,
    },
}


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def get_all_apps() -> List[str]:
    return list(APP_CATALOG.keys())


def is_valid_app(app_key: str) -> bool:
    return app_key in APP_CATALOG
