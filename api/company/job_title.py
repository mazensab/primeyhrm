# ======================================================
# 🧩 Job Title API — Company Scope
# Primey HR Cloud
# Version: JT1.5 FINAL (UPSERT PATCH ✅)
# ======================================================
# ✔ Update = Update OR Create (Upsert)
# ✔ CSRF exempt for internal POST APIs
# ✔ Session Auth preserved
# ✔ No Biotime sync here (by design)
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
# 📄 List Job Titles
# ======================================================

@require_GET
@login_required
def job_titles_list(request):
    company, error = _require_company(request)
    if error:
        return error

    qs = JobTitle.objects.filter(company=company).order_by("id")

    data = [
        {
            "id": jt.id,
            "name": jt.name,
            "is_active": jt.is_active,
        }
        for jt in qs
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

    return JsonResponse({
        "status": "success",
        "id": jt.id,
        "created": True,
    })


# ======================================================
# ✏️ Update OR Create Job Title (UPSERT)
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
    # 🆕 Create if not exists
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
    # ✏️ Update existing
    # --------------------------------------------------
    if name is not None:
        jt.name = name

    if isinstance(is_active, bool):
        jt.is_active = is_active

    jt.save()

    return JsonResponse({
        "status": "success",
        "id": jt.id,
        "created": False,
    })
