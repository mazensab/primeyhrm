# ===============================================================
# 🔔 Company Manager — SAFE Signals (NO BILLING)
# Ultra Stable V29.2 — Biotime Auto Sync + Default System Company
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