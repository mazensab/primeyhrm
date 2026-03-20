# company_manager/apps.py
from django.apps import AppConfig
import logging


logger = logging.getLogger(__name__)


class CompanyManagerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "company_manager"

    def ready(self):
        """
        ✅ تحميل Signals فقط
        ممنوع تنفيذ أي استعلامات قاعدة بيانات داخل ready()
        لتفادي RuntimeWarning أثناء أوامر Django والإقلاع.
        """

        try:
            import company_manager.signals  # noqa: F401
            logger.info("🔥 company_manager.signals LOADED")
        except Exception as exc:
            logger.exception(
                "❌ Failed loading company_manager.signals: %s",
                exc,
            )