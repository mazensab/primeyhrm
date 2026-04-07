# ===============================================================
# 🔔 Company Manager — SAFE Signals (NO BILLING)
# Ultra Stable V29.3 — Biotime Auto Sync + Default System Company
# + Leave Types / Leave Policies Seed ✅
# ===============================================================
print("🔥 company_manager.signals LOADED")

import logging

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import (
    Company,
    CompanyBranch,
    CompanyOffice,
    CompanyDepartment,
    JobTitle,
)
from .role_templates import apply_role_templates

from biotime_center.models import BiotimeSetting
from biotime_center.biotime_api_client import BiotimeAPIClient
from biotime_center.sync_service import (
    create_or_sync_branch,
    create_or_sync_department,
    create_or_sync_jobtitle,
)

logger = logging.getLogger(__name__)


# ===============================================================
# 🔧 FEATURE FLAG (Global Kill Switch)
# ===============================================================
ENABLE_COMPANY_SIGNALS = True


# ===============================================================
# 🧩 Leave Seed Helper (SAFE / IDEMPOTENT)
# ===============================================================
def seed_company_leave_master_data(company):
    """
    إنشاء بيانات الإجازات الأساسية للشركة بشكل آمن وبدون تكرار.

    ما يتم إنشاؤه:
    1) LeaveType الأساسية
    2) CompanyAnnualLeavePolicy
    3) LeavePolicy الافتراضية لكل نوع

    ملاحظات:
    - الاستيراد داخلي لتجنب أي circular import
    - لا يكسر النظام إذا لم تكن جداول leave_center جاهزة
    - يعمل بشكل idempotent
    """
    try:
        LeaveType = apps.get_model("leave_center", "LeaveType")
        LeavePolicy = apps.get_model("leave_center", "LeavePolicy")
        CompanyAnnualLeavePolicy = apps.get_model("leave_center", "CompanyAnnualLeavePolicy")
    except Exception:
        logger.exception("❌ Failed loading leave_center models for seed")
        return

    # -----------------------------------------------------------
    # 1️⃣ Company Annual Leave Policy
    # -----------------------------------------------------------
    try:
        CompanyAnnualLeavePolicy.objects.get_or_create(
            company=company,
            defaults={
                "annual_days": 21,
                "carry_forward_enabled": True,
                "carry_forward_limit": 15,
                "reset_month": 1,
                "is_active": True,
            },
        )
    except Exception:
        logger.exception(
            "❌ Failed seeding CompanyAnnualLeavePolicy | company_id=%s",
            getattr(company, "id", None),
        )

    # -----------------------------------------------------------
    # 2️⃣ Leave Types الأساسية
    # -----------------------------------------------------------
    default_leave_types = [
        {
            "name": "إجازة سنوية",
            "category": "annual",
            "annual_balance": 21,
            "requires_manager_only": False,
            "requires_hr_only": False,
            "requires_attachment": False,
            "max_days": 30,
            "color": "#0A4D3C",
        },
        {
            "name": "إجازة مرضية",
            "category": "sick",
            "annual_balance": 30,
            "requires_manager_only": False,
            "requires_hr_only": False,
            "requires_attachment": True,
            "max_days": 30,
            "color": "#3B82F6",
        },
        {
            "name": "إجازة أمومة",
            "category": "maternity",
            "annual_balance": 10,
            "requires_manager_only": False,
            "requires_hr_only": True,
            "requires_attachment": True,
            "max_days": 70,
            "color": "#EC4899",
        },
        {
            "name": "إجازة زواج",
            "category": "marriage",
            "annual_balance": 5,
            "requires_manager_only": False,
            "requires_hr_only": False,
            "requires_attachment": False,
            "max_days": 5,
            "color": "#8B5CF6",
        },
        {
            "name": "إجازة وفاة",
            "category": "death",
            "annual_balance": 3,
            "requires_manager_only": False,
            "requires_hr_only": False,
            "requires_attachment": False,
            "max_days": 5,
            "color": "#F97316",
        },
        {
            "name": "إجازة حج",
            "category": "hajj",
            "annual_balance": 10,
            "requires_manager_only": False,
            "requires_hr_only": True,
            "requires_attachment": False,
            "max_days": 10,
            "color": "#059669",
        },
        {
            "name": "إجازة دراسية",
            "category": "study",
            "annual_balance": 15,
            "requires_manager_only": False,
            "requires_hr_only": True,
            "requires_attachment": True,
            "max_days": 30,
            "color": "#14B8A6",
        },
        {
            "name": "إجازة بدون راتب",
            "category": "unpaid",
            "annual_balance": 999,
            "requires_manager_only": False,
            "requires_hr_only": True,
            "requires_attachment": False,
            "max_days": 60,
            "color": "#6B7280",
        },
    ]

    created_types_by_category = {}

    for item in default_leave_types:
        try:
            leave_type, _ = LeaveType.objects.get_or_create(
                company=company,
                category=item["category"],
                defaults={
                    "name": item["name"],
                    "annual_balance": item["annual_balance"],
                    "requires_manager_only": item["requires_manager_only"],
                    "requires_hr_only": item["requires_hr_only"],
                    "requires_attachment": item["requires_attachment"],
                    "max_days": item["max_days"],
                    "color": item["color"],
                },
            )

            # ---------------------------------------------------
            # ✅ Soft backfill لو النوع موجود لكنه ناقص بعض الحقول
            # ---------------------------------------------------
            update_fields = []

            if not getattr(leave_type, "name", None):
                leave_type.name = item["name"]
                update_fields.append("name")

            if getattr(leave_type, "annual_balance", None) in [None, 0]:
                leave_type.annual_balance = item["annual_balance"]
                update_fields.append("annual_balance")

            if getattr(leave_type, "color", None) in [None, "", "#0ea5e9"]:
                leave_type.color = item["color"]
                update_fields.append("color")

            if getattr(leave_type, "max_days", None) in [None, 0]:
                leave_type.max_days = item["max_days"]
                update_fields.append("max_days")

            if update_fields:
                leave_type.save(update_fields=update_fields)

            created_types_by_category[item["category"]] = leave_type

        except Exception:
            logger.exception(
                "❌ Failed seeding LeaveType | company_id=%s | category=%s",
                getattr(company, "id", None),
                item["category"],
            )

    # -----------------------------------------------------------
    # 3️⃣ LeavePolicy الافتراضية
    # -----------------------------------------------------------
    default_policies = {
        "annual": {
            "default_days": 21,
            "carry_forward_enabled": True,
            "carry_forward_limit": 15,
            "reset_month": 1,
            "paid_leave": True,
            "requires_manager_approval": True,
            "requires_hr_approval": False,
            "max_consecutive_days": 30,
            "gender_restriction": None,
            "is_active": True,
        },
        "sick": {
            "default_days": 30,
            "carry_forward_enabled": False,
            "carry_forward_limit": None,
            "reset_month": 1,
            "paid_leave": True,
            "requires_manager_approval": True,
            "requires_hr_approval": False,
            "max_consecutive_days": 30,
            "gender_restriction": None,
            "is_active": True,
        },
        "maternity": {
            "default_days": 10,
            "carry_forward_enabled": False,
            "carry_forward_limit": None,
            "reset_month": 1,
            "paid_leave": True,
            "requires_manager_approval": False,
            "requires_hr_approval": True,
            "max_consecutive_days": 70,
            "gender_restriction": "female",
            "is_active": True,
        },
        "marriage": {
            "default_days": 5,
            "carry_forward_enabled": False,
            "carry_forward_limit": None,
            "reset_month": 1,
            "paid_leave": True,
            "requires_manager_approval": True,
            "requires_hr_approval": False,
            "max_consecutive_days": 5,
            "gender_restriction": None,
            "is_active": True,
        },
        "death": {
            "default_days": 3,
            "carry_forward_enabled": False,
            "carry_forward_limit": None,
            "reset_month": 1,
            "paid_leave": True,
            "requires_manager_approval": True,
            "requires_hr_approval": False,
            "max_consecutive_days": 5,
            "gender_restriction": None,
            "is_active": True,
        },
        "hajj": {
            "default_days": 10,
            "carry_forward_enabled": False,
            "carry_forward_limit": None,
            "reset_month": 1,
            "paid_leave": True,
            "requires_manager_approval": True,
            "requires_hr_approval": True,
            "max_consecutive_days": 10,
            "gender_restriction": None,
            "is_active": True,
        },
        "study": {
            "default_days": 15,
            "carry_forward_enabled": False,
            "carry_forward_limit": None,
            "reset_month": 1,
            "paid_leave": True,
            "requires_manager_approval": True,
            "requires_hr_approval": True,
            "max_consecutive_days": 30,
            "gender_restriction": None,
            "is_active": True,
        },
        "unpaid": {
            "default_days": 999,
            "carry_forward_enabled": False,
            "carry_forward_limit": None,
            "reset_month": 1,
            "paid_leave": False,
            "requires_manager_approval": True,
            "requires_hr_approval": True,
            "max_consecutive_days": 60,
            "gender_restriction": None,
            "is_active": True,
        },
    }

    for category, policy_defaults in default_policies.items():
        leave_type = created_types_by_category.get(category)
        if not leave_type:
            continue

        try:
            LeavePolicy.objects.get_or_create(
                company=company,
                leave_type=leave_type,
                defaults=policy_defaults,
            )
        except Exception:
            logger.exception(
                "❌ Failed seeding LeavePolicy | company_id=%s | category=%s",
                getattr(company, "id", None),
                category,
            )

    logger.info(
        "✅ Leave master data seeded successfully | company_id=%s",
        getattr(company, "id", None),
    )


# ===============================================================
# 🧠 Master Seed Helper (SAFE / IDEMPOTENT)
# ===============================================================
def seed_company_master_data(company):
    """
    إنشاء البيانات الأساسية للشركة
    - آمن
    - لا يكرر
    - بدون أي Billing Logic
    """

    # -------------------------------
    # Departments
    # -------------------------------
    default_departments = [
        "الإدارة العامة",
        "الموارد البشرية",
        "المالية",
        "تقنية المعلومات",
        "المبيعات",
    ]

    for name in default_departments:
        CompanyDepartment.objects.get_or_create(
            company=company,
            name=name,
        )

    # -------------------------------
    # Job Titles
    # -------------------------------
    default_titles = [
        "مدير عام",
        "مدير موارد بشرية",
        "محاسب",
        "موظف",
        "مشرف",
    ]

    for name in default_titles:
        JobTitle.objects.get_or_create(
            company=company,
            name=name,
        )

    # -------------------------------
    # Leave Types + Policies
    # -------------------------------
    seed_company_leave_master_data(company)


# ===============================================================
# 🏢 Default System Company — SAFE POST MIGRATE
# ===============================================================
@receiver(post_migrate)
def ensure_default_system_company(sender, **kwargs):
    """
    إنشاء الشركة الافتراضية لسوبر أدمن النظام بطريقة آمنة
    - لا يعمل أثناء AppConfig.ready()
    - يعمل بعد اكتمال المايجريشن فقط
    - آمن ولا يكرر
    """

    try:
        # شغّل فقط عندما يكون التطبيق الحالي هو company_manager
        if sender.name != "company_manager":
            return

        User = get_user_model()

        # نتأكد أن موديل Company جاهز من registry
        CompanyModel = apps.get_model("company_manager", "Company")

        super_admin = User.objects.filter(is_superuser=True).order_by("id").first()
        if not super_admin:
            logger.info("ℹ️ No superuser found yet; skip default system company creation.")
            return

        existing_company = CompanyModel.objects.filter(owner=super_admin).first()
        if existing_company:
            logger.info(
                "ℹ️ Default system company already exists for superuser id=%s | company_id=%s",
                super_admin.id,
                existing_company.id,
            )
            return

        # إذا لم توجد أي شركة لهذا السوبر أدمن، ننشئها
        with transaction.atomic():
            company = CompanyModel.objects.create(
                owner=super_admin,
                name="Default System Company",
                commercial_number="0000000000",
                is_active=True,
            )

        logger.info(
            "✅ Default system company created successfully | superuser_id=%s | company_id=%s",
            super_admin.id,
            company.id,
        )

    except Exception:
        logger.exception("❌ Failed to ensure default system company after migrations")


# ===============================================================
# 🏢 Company Post Create — SAFE INIT
# ===============================================================
@receiver(post_save, sender=Company)
def company_post_create_init(sender, instance, created, **kwargs):
    """
    Signal آمن لتجهيز الشركة بعد إنشائها
    """

    if not ENABLE_COMPANY_SIGNALS:
        return

    if not created:
        return

    if not instance.is_active:
        return

    # -------------------------------
    # 1️⃣ Branch (HQ)
    # -------------------------------
    branch, _ = CompanyBranch.objects.get_or_create(
        company=instance,
        name="المقر الرئيسي",
        defaults={
            "city": "غير محدد",
            "address": instance.short_address or "—",
        },
    )

    # -------------------------------
    # 2️⃣ Office
    # -------------------------------
    CompanyOffice.objects.get_or_create(
        branch=branch,
        name="مكتب رئيسي",
        defaults={
            "floor": "1",
            "description": "تم الإنشاء تلقائيًا",
        },
    )

    # -------------------------------
    # 3️⃣ Roles
    # -------------------------------
    apply_role_templates(instance)

    # -------------------------------
    # 4️⃣ Master Data
    # -------------------------------
    seed_company_master_data(instance)


# ===============================================================
# 🧩 Helper — Resolve Biotime Client (SAFE)
# (مُبقى كما هو — قد يُستخدم لاحقًا)
# ===============================================================
def _resolve_biotime_client(company):
    """
    إرجاع BiotimeAPIClient جاهز أو None
    """
    setting = BiotimeSetting.objects.filter(company=company).first()
    if not setting:
        logger.warning("⚠️ No BiotimeSetting for company=%s", company.id)
        return None

    client = BiotimeAPIClient(setting)
    auth = client.authenticate()

    if auth.get("status") != "success":
        logger.error("❌ Biotime authentication failed | company=%s", company.id)
        return None

    return client


# ===============================================================
# 🔗 Branch → Biotime (Area)
# ===============================================================
@receiver(post_save, sender=CompanyBranch)
def sync_branch_to_biotime(sender, instance, created, **kwargs):

    if not ENABLE_COMPANY_SIGNALS:
        return

    if not created:
        return

    try:
        create_or_sync_branch(instance)

        logger.info(
            "✅ Branch synced via Service | id=%s | name=%s | code=%s",
            instance.id,
            instance.name,
            instance.biotime_code,
        )

    except Exception:
        logger.exception("🔥 Failed syncing branch to Biotime")


# ===============================================================
# 🔗 Department → Biotime (Area + Department)
# ===============================================================
@receiver(post_save, sender=CompanyDepartment)
def sync_department_to_biotime(sender, instance, created, **kwargs):

    if not ENABLE_COMPANY_SIGNALS:
        return

    if not created:
        return

    try:
        create_or_sync_department(instance)

        logger.info(
            "✅ Department synced via Service | id=%s | name=%s | code=%s",
            instance.id,
            instance.name,
            instance.biotime_code,
        )

    except Exception:
        logger.exception("🔥 Failed syncing department to Biotime")


# ===============================================================
# 🔗 JobTitle → Biotime (Position)
# ===============================================================
@receiver(post_save, sender=JobTitle)
def sync_jobtitle_to_biotime(sender, instance, created, **kwargs):

    if not ENABLE_COMPANY_SIGNALS:
        return

    if not created:
        return

    try:
        create_or_sync_jobtitle(instance)

        logger.info(
            "✅ JobTitle synced via Service | id=%s | name=%s | code=%s",
            instance.id,
            instance.name,
            instance.biotime_code,
        )

    except Exception:
        logger.exception("🔥 Failed syncing job title to Biotime")