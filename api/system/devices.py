from django.http import JsonResponse
from django.utils.timezone import now, timedelta

from biotime_center.models import BiotimeDevice
from company_manager.models import Company


# ================================================================
# 🔌 Devices Overview API (Super Admin Level)
# ================================================================
def devices_overview(request):
    """
    يقدم ملخص شامل عن أجهزة Biotime على مستوى النظام:
        - إجمالي الأجهزة
        - الأجهزة المتصلة / غير المتصلة
        - الأجهزة التي بها مشاكل
        - توزيع الأجهزة على الشركات
        - آخر مزامنة لكل جهاز
    """

    now_time = now()

    # ============================
    # 1) Device Counters
    # ============================
    total_devices = BiotimeDevice.objects.count()
    connected_devices = BiotimeDevice.objects.filter(status="connected").count()
    disconnected_devices = BiotimeDevice.objects.filter(status="disconnected").count()

    # ============================
    # 2) Problematic Devices (No Sync for 24+ hours)
    # ============================
    problematic = list(
        BiotimeDevice.objects.filter(
            last_seen__lt=now_time - timedelta(hours=24)
        ).select_related("company").values(
            "device_name",
            "status",
            "company__name",
            "last_seen"
        )
    )

    # ============================
    # 3) Devices per Company
    # ============================
    company_devices = []
    for company in Company.objects.all():
        count = BiotimeDevice.objects.filter(company=company).count()
        if count > 0:
            company_devices.append({
                "company": company.name,
                "count": count,
            })

    # ============================
    # 4) Latest 10 Devices
    # ============================
    latest_devices = list(
        BiotimeDevice.objects.select_related("company")
        .order_by("-created_at")
        .values(
            "id",
            "device_name",
            "status",
            "company__name",
            "created_at",
            "last_seen"
        )[:10]
    )

    # ============================
    # Response
    # ============================
    return JsonResponse({
        "status": "success",
        "devices": {
            "total": total_devices,
            "connected": connected_devices,
            "disconnected": disconnected_devices,
            "problematic": problematic,
            "company_distribution": company_devices,
            "latest": latest_devices,
        }
    }, status=200)
