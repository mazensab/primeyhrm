# ============================================================
# 📂 الملف: control_center/apps.py
# 🧭 Mham Cloud — Control Center V16.0 (Glass White Sync)
# 🚀 يتضمن: لوحة التحكم + إدارة المستخدمين والأدوار V10.1
# 💡 تكامل ذكي مع Billing, Payroll, Employee, AI & Attendance
# ============================================================

from django.apps import AppConfig


class ControlCenterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'control_center'
    verbose_name = "🧭 Primey Control Center — V16.0 (Users & Roles V10.1)"

    def ready(self):
        """تهيئة ذكية عند تشغيل النظام"""
        from django.utils.translation import gettext_lazy as _
        import logging

        logger = logging.getLogger(__name__)
        logger.info(_("🔹 تم تحميل وحدة التحكم الذكية (Control Center V16.0) بنجاح"))
