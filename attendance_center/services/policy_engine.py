# ================================================================
# 🧠 Attendance Policy Engine — Phase F.1
# Primey HR Cloud — Attendance Center
# ------------------------------------------------
# الهدف:
#   - إنشاء AttendancePolicy افتراضية لكل شركة لا تملك سياسة.
#   - Idempotent (لا يكرر الإنشاء).
#   - آمن للإنتاج.
#   - قابل للتشغيل من Shell / Scheduler لاحقًا.
# ------------------------------------------------
# ⚠️ لا يتم لمس أي AttendanceRecord أو منطق حساب.
# ================================================================

from datetime import time
from django.db import transaction
import logging

from company_manager.models import Company
from attendance_center.models import AttendancePolicy

logger = logging.getLogger(__name__)


# ================================================================
# 🏗️ Default Policy Template
# ================================================================

DEFAULT_POLICY_TEMPLATE = {
    # 🕘 أوقات الدوام الافتراضية
    "work_start": time(9, 0),    # 09:00 AM
    "work_end": time(17, 0),     # 05:00 PM

    # 🛑 نهاية الأسبوع (السعودية)
    "weekend_days": "fri,sat",

    # ⏱ السماحية بالدقائق
    "grace_minutes": 10,
}


# ================================================================
# 🧠 PolicyEngine
# ================================================================

class AttendancePolicyEngine:
    """
    🧠 محرك إدارة سياسات الحضور

    المسؤوليات:
    - التأكد أن كل شركة لديها AttendancePolicy واحدة على الأقل.
    - إنشاء Policy افتراضية عند عدم وجودها.
    - عدم كسر أو تعديل أي Policy موجودة.
    """

    # ------------------------------------------------------------
    # 🏗️ إنشاء Policy افتراضية لشركة واحدة
    # ------------------------------------------------------------
    @classmethod
    def ensure_company_default_policy(cls, company: Company) -> AttendancePolicy:
        """
        ✅ تضمن وجود AttendancePolicy للشركة.
        - إذا كانت موجودة → تعاد كما هي.
        - إذا غير موجودة → يتم إنشاؤها افتراضيًا.
        """

        existing = AttendancePolicy.objects.filter(company=company).first()
        if existing:
            return existing

        with transaction.atomic():
            policy = AttendancePolicy.objects.create(
                company=company,

                # 🕘 Required fields
                work_start=DEFAULT_POLICY_TEMPLATE["work_start"],
                work_end=DEFAULT_POLICY_TEMPLATE["work_end"],

                # ⚙️ Behavior
                weekend_days=DEFAULT_POLICY_TEMPLATE["weekend_days"],
                grace_minutes=DEFAULT_POLICY_TEMPLATE["grace_minutes"],
            )

        logger.info(
            f"✅ Default AttendancePolicy created "
            f"(company_id={company.id}, policy_id={policy.id})"
        )

        return policy

    # ------------------------------------------------------------
    # 🌍 إنشاء Policy افتراضية لجميع الشركات
    # ------------------------------------------------------------
    @classmethod
    def ensure_all_companies_have_policy(cls) -> dict:
        """
        🔄 تمر على جميع الشركات وتضمن وجود Policy لكل شركة.

        Returns:
            {
                "checked": int,
                "created": int,
                "existing": int
            }
        """

        companies = Company.objects.all()
        checked = 0
        created = 0
        existing = 0

        for company in companies:
            checked += 1
            policy = AttendancePolicy.objects.filter(company=company).first()

            if policy:
                existing += 1
                continue

            cls.ensure_company_default_policy(company)
            created += 1

        summary = {
            "checked": checked,
            "created": created,
            "existing": existing,
        }

        logger.info(
            "📊 AttendancePolicy bootstrap completed | "
            f"checked={checked}, created={created}, existing={existing}"
        )

        return summary


# ================================================================
# ⚙️ Helper — Shell Friendly
# ================================================================

def bootstrap_default_attendance_policies():
    """
    🧪 دالة مساعدة للتشغيل من Django Shell:

    >>> from attendance_center.services.policy_engine import bootstrap_default_attendance_policies
    >>> bootstrap_default_attendance_policies()
    """

    return AttendancePolicyEngine.ensure_all_companies_have_policy()
