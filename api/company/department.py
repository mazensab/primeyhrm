# ======================================================
# 🏢 Department API — Company Scope
# Mham Cloud
# Version: D2.7 FINAL (UPSERT + BIOTIME SYNC + LIMIT SAFE ✅)
# ======================================================
# ✔ Create OR Update (Upsert Safe)
# ✔ Biotime auto sync on save
# ✔ CSRF exempt for internal POST APIs
# ✔ Session Auth preserved
# ✔ No behavioral regression
# ✔ Product-aware limit guard ready
# ======================================================

import json
import logging

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from billing_center.services.subscription_limits import (
    get_active_product_subscription,
)
from company_manager.models import CompanyDepartment, CompanyUser
from biotime_center.sync_service import create_or_sync_department

logger = logging.getLogger(__name__)


# ======================================================
# Helpers
# ======================================================

def _parse_body(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


def _resolve_company(request):
    """
    Resolve company safely:
    1) From middleware (request.company)
    2) Fallback from CompanyUser
    """
    if hasattr(request, "company") and request.company:
        return request.company

    company_user = (
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

    if company_user:
        return company_user.company

    return None


def _require_company(request):
    company = _resolve_company(request)
    if not company:
        return None, JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )
    return company, None


def _check_hr_product_subscription(company):
    """
    نتحقق فقط من وجود اشتراك HR نشط قبل إنشاء قسم جديد.
    لا يوجد حاليًا max_departments معتمد، لكن نمنع الإنشاء
    إذا لم يوجد اشتراك منتج HR أصلًا.
    """
    subscription = get_active_product_subscription(company, "HR")
    if subscription:
        return subscription, None

    return None, JsonResponse(
        {
            "status": "error",
            "message": "لا يوجد اشتراك HR نشط لهذه الشركة.",
            "limit": {
                "resource": "departments",
                "product_code": "HR",
                "code": "NO_PRODUCT_SUBSCRIPTION",
            },
        },
        status=402,
    )


# ======================================================
# 📄 List Departments (READ)
# ======================================================

@require_GET
@login_required
def departments_list(request):
    company, guard = _require_company(request)
    if guard:
        return guard

    qs = (
        CompanyDepartment.objects
        .filter(company=company)
        .order_by("id")
    )

    data = [
        {
            "id": d.id,
            "name": d.name,
            "is_active": d.is_active,
        }
        for d in qs
    ]

    return JsonResponse({"departments": data})


# ======================================================
# ➕ Create OR Update Department (UPSERT)
# ======================================================

@csrf_exempt
@require_POST
@login_required
def department_create(request):
    company, guard = _require_company(request)
    if guard:
        return guard

    subscription, subscription_guard = _check_hr_product_subscription(company)
    if subscription_guard:
        return subscription_guard

    payload = _parse_body(request)
    name = (payload.get("name") or "").strip()

    if not name:
        return HttpResponseBadRequest("Department name is required")

    dep, created = CompanyDepartment.objects.get_or_create(
        company=company,
        name=name,
        defaults={"is_active": True},
    )

    # 🔁 لو موجود مسبقًا نحدّثه
    if not created:
        dep.is_active = True
        dep.save(update_fields=["is_active"])

    # 🔗 Sync with Biotime (Create OR Update)
    try:
        create_or_sync_department(dep)
    except Exception:
        logger.exception("❌ Biotime department sync failed | dep_id=%s", dep.id)

    return JsonResponse({
        "status": "success",
        "id": dep.id,
        "created": created,
        "product": "HR",
        "subscription_id": subscription.id if subscription else None,
    })


# ======================================================
# ✏️ Update / Toggle Department
# ======================================================

@csrf_exempt
@require_POST
@login_required
def department_update(request, department_id):
    company, guard = _require_company(request)
    if guard:
        return guard

    payload = _parse_body(request)

    try:
        dep = CompanyDepartment.objects.get(
            id=department_id,
            company=company,
        )
    except CompanyDepartment.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Department not found"},
            status=404,
        )

    updated = False

    if "name" in payload and payload["name"]:
        dep.name = payload["name"]
        updated = True

    if "is_active" in payload:
        dep.is_active = bool(payload["is_active"])
        updated = True

    if updated:
        dep.save()

        # 🔗 Sync with Biotime after update
        try:
            create_or_sync_department(dep)
        except Exception:
            logger.exception("❌ Biotime department sync failed | dep_id=%s", dep.id)

    return JsonResponse({"status": "success"})