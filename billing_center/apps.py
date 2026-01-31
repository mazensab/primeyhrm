from django.apps import AppConfig


class BillingCenterConfig(AppConfig):
    """
    ============================================================
    💳 Billing Center — AppConfig
    Primey HR Cloud
    ============================================================
    ✔ Initializes Auto Billing Scheduler (S3-D)
    ✔ Registers Billing Signals (Payment → Transaction)
    ✔ No DB Queries on import
    ✔ Safe for:
        - migrate
        - shell
        - collectstatic
        - production
    ============================================================
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "billing_center"

    def ready(self):
        """
        ------------------------------------------------------------
        🔌 App Initialization Hook
        ------------------------------------------------------------
        1) Register billing signals (SAFE, no side effects)
        2) Start auto billing scheduler (guarded)
        ------------------------------------------------------------
        """

        # ---------------------------------------------------------
        # 1️⃣ Register Signals (SAFE)
        # ---------------------------------------------------------
        try:
            import billing_center.signals  # noqa: F401
        except Exception:
            # لا نكسر تشغيل Django في أي ظرف
            pass

        # ---------------------------------------------------------
        # 2️⃣ Start Auto Billing Scheduler (GUARDED)
        # ---------------------------------------------------------
        try:
            from billing_center.schedulers.auto_billing_scheduler import start
            start()
        except Exception:
            # ❗ لا نكسر تشغيل Django في أي حالة:
            # - أثناء migrations
            # - أثناء shell
            # - أثناء collectstatic
            # - أثناء startup في بيئات معينة
            pass
