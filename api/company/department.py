# ======================================================
# 🏢 Department API — Company Scope
# Primey HR Cloud
# Version: D2.6 FINAL (UPSERT + BIOTIME SYNC ✅)
# ======================================================
# ✔ Create OR Update (Upsert Safe)
# ✔ Biotime auto sync on save
# ✔ CSRF exempt for internal POST APIs
# ✔ Session Auth preserved
# ✔ No behavioral regression
# ======================================================

import json
import logging

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

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

    payload = _parse_body(request)
    name = payload.get("name")

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
