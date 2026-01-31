# ================================================================
# 📂 api/company/branches.py
# 🏢 Company Branch API
# Primey HR Cloud
# Version: V1.2 — MODEL ALIGNED + UI SAFE + BIOTIME READY 🔒
# ================================================================

import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import transaction

from company_manager.models import CompanyBranch, CompanyUser

logger = logging.getLogger(__name__)

# ================================================================
# 🔐 Helpers
# ================================================================

def api_success(**payload):
    return JsonResponse({"status": "success", **payload}, status=200)


def api_error(message, status=400, **extra):
    return JsonResponse(
        {"status": "error", "message": message, **extra},
        status=status,
    )


def resolve_company_user(request):
    """
    Resolve active company context safely.
    """
    return (
        CompanyUser.objects
        .select_related("company")
        .filter(
            user=request.user,
            is_active=True,
            company__isnull=False,
        )
        .order_by("-id")
        .first()
    )


# ================================================================
# 📄 API — List Branches
# ================================================================
@login_required
@require_GET
def branches_list(request):
    """
    إرجاع جميع فروع الشركة الحالية.
    """

    company_user = resolve_company_user(request)
    if not company_user:
        return api_error("Company context not found.", status=403)

    try:
        qs = (
            CompanyBranch.objects
            .filter(company=company_user.company)
            .order_by("name")
        )

        branches = []

        for b in qs:
            branches.append({
                "id": b.id,
                "name": b.name,
                "is_active": b.is_active,
                "biotime_code": b.biotime_code,
            })

        return api_success(
            count=len(branches),
            branches=branches,
        )

    except Exception:
        logger.exception("Branches List API Error")

        return api_error(
            "⚠️ تعذر تحميل الفروع.",
            status=500,
        )


# ================================================================
# ➕ API — Create Branch
# ================================================================
@csrf_exempt
@login_required
@require_POST
def branch_create(request):
    """
    إنشاء فرع جديد داخل الشركة.
    متوافق مع Dialog (name فقط مطلوب).
    """

    company_user = resolve_company_user(request)
    if not company_user:
        return api_error("Company context not found.", status=403)

    try:
        payload = json.loads(request.body.decode() or "{}")

        name = (payload.get("name") or "").strip()

        # -----------------------------
        # ✅ Validation
        # -----------------------------
        if not name:
            return api_error("اسم الفرع مطلوب.", status=400)

        # منع تكرار الاسم داخل نفس الشركة
        if CompanyBranch.objects.filter(
            company=company_user.company,
            name=name,
        ).exists():
            return api_error(
                "اسم الفرع مستخدم مسبقًا.",
                status=409,
            )

        # -----------------------------
        # 💾 Create
        # -----------------------------
        with transaction.atomic():
            branch = CompanyBranch.objects.create(
                company=company_user.company,
                name=name,
                is_active=True,
            )

        return api_success(
            id=branch.id,
            name=branch.name,
            is_active=branch.is_active,
            biotime_code=branch.biotime_code,
            message="✔ تم إنشاء الفرع بنجاح.",
        )

    except Exception:
        logger.exception("Branch Create API Error")

        return api_error(
            "❌ حدث خطأ أثناء إنشاء الفرع.",
            status=500,
        )


# ================================================================
# ✏️ API — Update Branch
# ================================================================
@csrf_exempt
@login_required
@require_POST
def branch_update(request, branch_id: int):
    """
    تحديث بيانات الفرع.
    """

    company_user = resolve_company_user(request)
    if not company_user:
        return api_error("Company context not found.", status=403)

    try:
        branch = get_object_or_404(
            CompanyBranch,
            id=branch_id,
            company=company_user.company,
        )

        payload = json.loads(request.body.decode() or "{}")

        name = (payload.get("name") or "").strip()
        is_active = payload.get("is_active")

        # -----------------------------
        # ✅ Validation
        # -----------------------------
        if name and name != branch.name:
            exists = CompanyBranch.objects.filter(
                company=company_user.company,
                name=name,
            ).exclude(id=branch.id).exists()

            if exists:
                return api_error(
                    "اسم الفرع مستخدم مسبقًا.",
                    status=409,
                )

            branch.name = name

        if isinstance(is_active, bool):
            branch.is_active = is_active

        branch.save()

        return api_success(
            id=branch.id,
            name=branch.name,
            is_active=branch.is_active,
            biotime_code=branch.biotime_code,
            message="✔ تم تحديث الفرع بنجاح.",
        )

    except Exception:
        logger.exception("Branch Update API Error")

        return api_error(
            "❌ حدث خطأ أثناء تحديث الفرع.",
            status=500,
        )
