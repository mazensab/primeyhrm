# ============================================================================
# 🇸🇦 Saudi National Address — Cached Lookups API
# Primey HR Cloud | System Layer
# Version: V1.0 Ultra Stable (READ ONLY)
# ============================================================================
# ✔ Uses cached data only
# ✔ Cities / Districts / Streets
# ✔ Fast + Safe + System scoped
# ============================================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

from settings_center.models import (
    NationalAddressCity,
    NationalAddressDistrict,
    NationalAddressStreet,
)


# ============================================================================
# 🏙️ Cities
# GET /api/system/national_address/cities/
# ============================================================================
@login_required
@require_GET
def cities_list(request):
    qs = NationalAddressCity.objects.order_by("name")

    return JsonResponse({
        "count": qs.count(),
        "items": [
            {"id": c.id, "name": c.name}
            for c in qs
        ]
    })


# ============================================================================
# 🏘️ Districts
# GET /api/system/national_address/districts/?city_id=
# ============================================================================
@login_required
@require_GET
def districts_list(request):
    city_id = request.GET.get("city_id")
    if not city_id:
        return JsonResponse({"error": "city_id مطلوب"}, status=400)

    qs = (
        NationalAddressDistrict.objects
        .filter(city_id=city_id)
        .select_related("city")
        .order_by("name")
    )

    return JsonResponse({
        "count": qs.count(),
        "items": [
            {
                "id": d.id,
                "name": d.name,
                "city_id": d.city_id,
            }
            for d in qs
        ]
    })


# ============================================================================
# 🛣️ Streets
# GET /api/system/national_address/streets/?district_id=
# ============================================================================
@login_required
@require_GET
def streets_list(request):
    district_id = request.GET.get("district_id")
    if not district_id:
        return JsonResponse({"error": "district_id مطلوب"}, status=400)

    qs = (
        NationalAddressStreet.objects
        .filter(district_id=district_id)
        .select_related("district")
        .order_by("name")
    )

    return JsonResponse({
        "count": qs.count(),
        "items": [
            {
                "id": s.id,
                "name": s.name,
                "district_id": s.district_id,
            }
            for s in qs
        ]
    })
