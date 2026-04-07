# ======================================================
# 🧩 Job Title API — Company Scope
# Mham Cloud
# Version: JT1.7 FINAL (SAFE BIO TIME)
# ======================================================

import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from company_manager.models import JobTitle, CompanyUser


# ======================================================
# Helpers
# ======================================================

def _parse_body(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


def _resolve_company(request):
    if hasattr(request, "company") and request.company:
        return request.company

    cu = (
        CompanyUser.objects
        .select_related("company")
        .filter(user=request.user, is_active=True)
        .order_by("-id")
        .first()
    )
    return cu.company if cu else None


def _require_company(request):
    company = _resolve_company(request)
    if not company:
        return None, JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )
    return company, None


# ======================================================
# 📄 List Job Titles
# ======================================================

@require_GET
@login_required
def job_titles_list(request):
    company, error = _require_company(request)
    if error:
        return error

    data = [
        {
            "id": jt.id,
            "name": jt.name,
            "is_active": jt.is_active,
        }
        for jt in JobTitle.objects.filter(company=company).order_by("id")
    ]

    return JsonResponse({"job_titles": data})


# ======================================================
# ➕ Create Job Title
# ======================================================

@csrf_exempt
@require_POST
@login_required
def job_title_create(request):
    company, error = _require_company(request)
    if error:
        return error

    payload = _parse_body(request)
    name = (payload.get("name") or "").strip()

    if not name:
        return HttpResponseBadRequest("Job title name is required")

    jt = JobTitle.objects.create(
        company=company,
        name=name,
        is_active=True,
    )

    # 🔗 Try BioTime create (SAFE / OPTIONAL)
    try:
        from biotime_center.sync_service import create_biotime_position

        result = create_biotime_position(company=company, job_title=jt)
        if result and result.get("position_id"):
            jt.biotime_position_id = result["position_id"]
            jt.save(update_fields=["biotime_position_id"])

    except Exception as e:
        print(f"[JobTitle Create] BioTime skipped jt={jt.id}: {e}")

    return JsonResponse({
        "status": "success",
        "id": jt.id,
        "created": True,
    })


# ======================================================
# ✏️ Update OR Create Job Title (UPSERT + BioTime SAFE)
# ======================================================

@csrf_exempt
@require_POST
@login_required
def job_title_update(request, job_title_id):
    company, error = _require_company(request)
    if error:
        return error

    payload = _parse_body(request)
    name = payload.get("name")
    is_active = payload.get("is_active")

    jt = JobTitle.objects.filter(
        id=job_title_id,
        company=company,
    ).first()

    # --------------------------------------------------
    # 🆕 Create if not exists (Local DB only)
    # --------------------------------------------------
    if not jt:
        if not name:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Job title not found and name is required to create",
                },
                status=400,
            )

        jt = JobTitle.objects.create(
            company=company,
            name=name,
            is_active=True if is_active is None else bool(is_active),
        )

        return JsonResponse({
            "status": "success",
            "id": jt.id,
            "created": True,
        })

    # --------------------------------------------------
    # ✏️ Update local fields
    # --------------------------------------------------
    if name is not None:
        jt.name = name

    if isinstance(is_active, bool):
        jt.is_active = is_active

    jt.save(update_fields=["name", "is_active"])

        # --------------------------------------------------
    # 🧠 BioTime SYNC (UPDATE ONLY - SAFE)
    # --------------------------------------------------
    try:
        from biotime_center.sync_service import BiotimeAPIClient
        from biotime_center.models import BiotimeSetting

        # جلب إعداد BioTime الصحيح
        biotime_setting = (
            BiotimeSetting.objects
            .filter(company=company)
            .first()
        )

        if not biotime_setting:
            raise Exception("BioTime setting not configured for company")

        # لا يوجد ربط → لا تحديث
        if not jt.biotime_position_id:
            return JsonResponse({
                "status": "success",
                "id": jt.id,
                "created": False,
            })

        client = BiotimeAPIClient(setting=biotime_setting)

        # ⚠️ BioTime requires FULL payload + PUT
        payload = {
            "id": jt.biotime_position_id,
            "position_name": jt.name,
            "parent": None,
        }

        client._put(
            f"/personnel/positions/{jt.biotime_position_id}/",
            payload,
        )

    except Exception as e:
        # ❗ لا نكسر التحديث المحلي
        print(
            f"[JobTitle BioTime Update] skipped jt={jt.id}: {e}"
        )
