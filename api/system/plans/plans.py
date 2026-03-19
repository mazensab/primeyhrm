# ======================================================
# 📦 Plans API — Billing Center (Super Admin + System Read)
# Version: V3.0 Ultra Stable (Companies + Apps Contract FINAL)
# Primey HR Cloud
# ======================================================

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt

from billing_center.models import SubscriptionPlan, CompanySubscription


# ======================================================
# 🔐 Helpers
# ======================================================

def _ensure_super_admin(user):
    """
    تأكد أن المستخدم سوبر أدمن نظام
    """
    if not user.is_superuser:
        raise PermissionDenied("Super Admin access required")


def _get_payload(request):
    """
    استخراج البيانات من:
    - JSON body
    - أو POST form-data
    """
    if request.body:
        try:
            import json
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            pass

    if request.POST:
        return request.POST.dict()

    return {}


def _parse_apps(value):
    """
    توحيد apps:
    - list → 그대로
    - CSV string → list
    - None / invalid → []
    """
    if not value:
        return []

    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]

    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]

    return []


def _safe_float(v):
    """
    تحويل آمن للأرقام (بدون كسر لو كانت None)
    """
    if v is None or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None


# ======================================================
# 📄 GET — List Plans (SYSTEM / READ ONLY)
# URL: /api/system/plans/
# ======================================================

@require_GET
def system_plans_list(request):
    """
    استرجاع الباقات المفعلة فقط
    - Read Only
    - بدون login_required
    - ✅ includes max_companies (حسب الاتفاق)
    """

    plans = (
        SubscriptionPlan.objects
        .filter(is_active=True)
        .order_by("price_monthly")
    )

    data = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price_monthly": _safe_float(p.price_monthly),
            "price_yearly": _safe_float(p.price_yearly),
            "max_companies": p.max_companies,
            "max_employees": p.max_employees,
            "is_active": p.is_active,
            "apps": p.apps or [],
        }
        for p in plans
    ]

    return JsonResponse({"plans": data}, status=200)


# ======================================================
# 📄 GET — List Plans (Super Admin)
# URL: /api/system/plans/admin/
# ======================================================

@require_GET
@login_required
def plans_list(request):
    """
    استرجاع جميع الباقات (بما فيها غير المفعلة)
    Super Admin only
    """
    _ensure_super_admin(request.user)

    plans = SubscriptionPlan.objects.all().order_by("id")

    data = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price_monthly": _safe_float(p.price_monthly),
            "price_yearly": _safe_float(p.price_yearly),
            "max_companies": p.max_companies,
            "max_employees": p.max_employees,
            "is_active": p.is_active,
            "apps": p.apps or [],

            # ⭐ عدد الشركات التي تستخدم هذه الباقة
            "companies_count": CompanySubscription.objects.filter(
                plan=p
            ).count()
        }
        for p in plans
    ]

    return JsonResponse({"plans": data}, status=200)


# ======================================================
# ✏️ POST — Update Plan (SAFE EDIT)
# URL: /api/system/plans/<id>/update/
# ======================================================

@require_POST
@login_required
def plan_update(request, plan_id):
    """
    تحديث بيانات الباقة (حسب الاتفاق)
    ✅ مسموح:
      - price_monthly
      - price_yearly
      - max_employees
      - is_active
    ❌ ممنوع:
      - max_companies
      - apps
    """
    _ensure_super_admin(request.user)

    try:
        plan = SubscriptionPlan.objects.get(id=plan_id)
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "الباقة غير موجودة"},
            status=404,
        )

    payload = _get_payload(request)
    if not payload:
        return HttpResponseBadRequest("Invalid payload")

    # ❌ بلوك صريح لأي محاولة لتغيير fields ممنوعة
    forbidden = {"apps", "max_companies", "max_branches"}
    for key in forbidden:
        if key in payload:
            return HttpResponseBadRequest(f"Field not allowed in update: {key}")

    updated_fields = []

    # ---------- Allowed Fields ----------
    field_map = {
        "description": str,
        "price_monthly": float,
        "price_yearly": float,
        "max_employees": int,
        "is_active": lambda v: str(v).lower() in ("1", "true", "yes", "on"),
    }

    for field, caster in field_map.items():
        if field not in payload:
            continue
        try:
            value = caster(payload.get(field))
        except Exception:
            return HttpResponseBadRequest(f"Invalid value for {field}")

        setattr(plan, field, value)
        updated_fields.append(field)

    if not updated_fields:
        return HttpResponseBadRequest("No valid fields provided")

    plan.save(update_fields=updated_fields)

    return JsonResponse(
        {
            "status": "success",
            "message": "تم تحديث الباقة بنجاح",
            "plan_id": plan.id,
        },
        status=200,
    )


# ======================================================
# ➕ POST — Create Plan (FINAL CONTRACT)
# URL: /api/system/plans/create/
# ======================================================

@require_POST
@login_required
@csrf_exempt
def plan_create(request):
    """
    إنشاء باقة جديدة (حسب الاتفاق)
    ✅ required:
      - name
      - price_monthly
      - price_yearly
      - max_companies
      - max_employees
      - apps
    """
    _ensure_super_admin(request.user)

    payload = _get_payload(request)
    if not payload:
        return HttpResponseBadRequest("Invalid or empty payload")

    required_fields = [
        "name",
        "price_monthly",
        "price_yearly",
        "max_companies",
        "max_employees",
        "apps",
    ]

    for field in required_fields:
        if field not in payload:
            return HttpResponseBadRequest(f"Missing field: {field}")

    apps_list = _parse_apps(payload.get("apps"))
    if not apps_list:
        return HttpResponseBadRequest("apps must include at least one item")

    try:
        plan = SubscriptionPlan.objects.create(
            name=payload["name"],
            description=payload.get("description", ""),
            
            price_monthly=float(payload["price_monthly"]),
            price_yearly=float(payload["price_yearly"]),
            max_companies=int(payload["max_companies"]),
            max_employees=int(payload["max_employees"]),
            is_active=str(payload.get("is_active", "true")).lower()
            in ("1", "true", "yes", "on"),
            apps=apps_list,
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=400,
        )

    return JsonResponse(
        {
            "status": "success",
            "message": "تم إنشاء الباقة بنجاح",
            "plan_id": plan.id,
            "apps": plan.apps,
        },
        status=201,
    )
