# ============================================================
# 🏷️ SYSTEM — Discounts API
# Primey HR Cloud | V1.7 Ultra Stable — FINAL
# ============================================================
# ✔ JSON + form-data
# ✔ CSRF Safe
# ✔ Super Admin Only
# ✔ Supports: discount_type | type
# ✔ Safe date parsing
# ✔ Soft Toggle
# ✔ Update by ID (PATCH)
# ✔ NO unexpected model fields
# ============================================================

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from datetime import datetime
import json

from billing_center.models import Discount


# ============================================================
# 🔐 Helpers
# ============================================================

def super_admin_required(user):
    return user.is_authenticated and user.is_superuser


def get_payload(request):
    if request.body:
        try:
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            pass

    if request.POST:
        return request.POST.dict()

    return None


def parse_date(value, field_name):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        raise ValueError(f"Invalid date format for {field_name}")


# ============================================================
# 🏷️ Discounts List + Create
# URL: /api/system/discounts/
# ============================================================

@login_required
@require_http_methods(["GET", "POST"])
def system_discounts(request):

    # 🔒 Authorization
    if not super_admin_required(request.user):
        return JsonResponse({"detail": "Permission denied"}, status=403)

    # --------------------------------------------------------
    # 📄 GET — List Discounts
    # --------------------------------------------------------
    if request.method == "GET":
        discounts = Discount.objects.all().order_by("-created_at")

        return JsonResponse(
            {
                "results": [
                    {
                        "id": d.id,
                        "code": d.code,
                        "type": d.discount_type,
                        "value": float(d.value),
                        "is_active": d.is_active,
                        "applies_to_all_plans": d.applies_to_all_plans,
                        "start_date": d.start_date,
                        "end_date": d.end_date,
                    }
                    for d in discounts
                ]
            },
            status=200,
        )

    # --------------------------------------------------------
    # ➕ POST — Create Discount
    # --------------------------------------------------------
    payload = get_payload(request)
    if not payload:
        return HttpResponseBadRequest("Invalid or empty payload")

    code = payload.get("code")
    discount_type = payload.get("discount_type") or payload.get("type")
    value = payload.get("value")

    applies_to_all_plans = str(
        payload.get("applies_to_all_plans", "true")
    ).lower() in ("1", "true", "yes", "on")

    # 🧪 Validation
    if not code:
        return JsonResponse({"detail": "Discount code is required"}, status=400)

    if discount_type not in ("percentage", "fixed"):
        return JsonResponse({"detail": "Invalid discount type"}, status=400)

    try:
        value = float(value)
        if value <= 0:
            raise ValueError
    except Exception:
        return JsonResponse({"detail": "Invalid discount value"}, status=400)

    if Discount.objects.filter(code=code).exists():
        return JsonResponse(
            {"detail": "Discount code already exists"}, status=400
        )

    try:
        start_date = parse_date(payload.get("start_date"), "start_date")
        end_date = parse_date(payload.get("end_date"), "end_date")
    except ValueError as e:
        return JsonResponse({"detail": str(e)}, status=400)

    # 💾 Create (SAFE)
    discount = Discount.objects.create(
        code=code,
        discount_type=discount_type,
        value=value,
        start_date=start_date,
        end_date=end_date,
        applies_to_all_plans=applies_to_all_plans,
        is_active=True,
    )

    return JsonResponse(
        {
            "id": discount.id,
            "code": discount.code,
            "detail": "Discount created successfully",
        },
        status=201,
    )


# ============================================================
# ✏️ Update Discount
# URL: /api/system/discounts/<int:discount_id>/
# ============================================================

@login_required
@require_http_methods(["PATCH"])
def update_discount(request, discount_id):

    # 🔒 Authorization
    if not super_admin_required(request.user):
        return JsonResponse({"detail": "Permission denied"}, status=403)

    discount = get_object_or_404(Discount, id=discount_id)
    payload = get_payload(request)

    if not payload:
        return HttpResponseBadRequest("Invalid or empty payload")

    # 🧠 Accept both discount_type | type
    discount_type = payload.get("discount_type") or payload.get("type")
    if discount_type:
        if discount_type not in ("percentage", "fixed"):
            return JsonResponse({"detail": "Invalid discount type"}, status=400)
        discount.discount_type = discount_type

    if "value" in payload:
        try:
            value = float(payload.get("value"))
            if value <= 0:
                raise ValueError
            discount.value = value
        except Exception:
            return JsonResponse({"detail": "Invalid discount value"}, status=400)

    try:
        if "start_date" in payload:
            discount.start_date = parse_date(
                payload.get("start_date"), "start_date"
            )

        if "end_date" in payload:
            discount.end_date = parse_date(
                payload.get("end_date"), "end_date"
            )
    except ValueError as e:
        return JsonResponse({"detail": str(e)}, status=400)

    if "applies_to_all_plans" in payload:
        discount.applies_to_all_plans = str(
            payload.get("applies_to_all_plans")
        ).lower() in ("1", "true", "yes", "on")

    discount.save()

    return JsonResponse(
        {
            "id": discount.id,
            "detail": "Discount updated successfully",
        },
        status=200,
    )


# ============================================================
# 🔁 Toggle Discount Status
# URL: /api/system/discounts/<int:discount_id>/toggle/
# ============================================================

@login_required
@require_http_methods(["PATCH"])
def toggle_discount_status(request, discount_id):

    # 🔒 Authorization
    if not super_admin_required(request.user):
        return JsonResponse({"detail": "Permission denied"}, status=403)

    discount = get_object_or_404(Discount, id=discount_id)

    discount.is_active = not discount.is_active
    discount.save(update_fields=["is_active"])

    return JsonResponse(
        {
            "id": discount.id,
            "is_active": discount.is_active,
            "detail": "Discount status updated",
        },
        status=200,
    )
