# company_manager/apps.py
from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError, ProgrammingError


class CompanyManagerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "company_manager"

    def ready(self):
        """
        🔥 Auto-create default company for System Owner (Super Admin)
        يعمل فقط بعد المايجريشن — ويتفادى أخطاء غياب الجداول
        """

        try:
            User = get_user_model()
            from .models import Company

            # ابحث عن أول سوبر أدمن
            super_admin = User.objects.filter(is_superuser=True).first()

            # إذا فيه سوبر أدمن وما عنده أي شركة → أنشئ شركة تلقائية
            if super_admin and not Company.objects.exists():
                Company.objects.create(
                    owner=super_admin,
                    name="Default System Company",
                    commercial_number="0000000000",
                )

        except (OperationalError, ProgrammingError):
            # هذا يعني أن الجداول لم تُنشأ بعد — تجاهل
            pass

        # =====================================================
        # ✅ تحميل Signals (مهم جدًا لتفعيل الربط التلقائي)
        # =====================================================
        try:
            import company_manager.signals  # noqa: F401
        except Exception as exc:
            # لا نكسر التشغيل — فقط تسجيل الخطأ
            import logging
            logging.getLogger(__name__).exception(
                "❌ Failed loading company_manager.signals: %s", exc
            )
