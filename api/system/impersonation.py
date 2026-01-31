# ============================================================
# 🕵️ Impersonation API — V2 Ultra Stable (Super Admin Only)
# Primey HR Cloud
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from company_manager.models import Company


# ============================================================
# 🔐 Helpers
# ============================================================

def forbidden():
    return JsonResponse(
        {"success": False, "error": "Forbidden"},
        status=403
    )


# ============================================================
# ▶️ Start Impersonation
# ============================================================
@login_required
@require_POST
def start_impersonation(request):
    """
    Super Admin يبدأ impersonation لشركة محددة
    - يعتمد على Django Session
    - آمن
    - متوافق مع WhoAmI + Proxy
    """

    if not request.user.is_superuser:
        return forbidden()

    company_id = request.POST.get("company_id")

    if not company_id:
        return JsonResponse(
            {"success": False, "error": "company_id is required"},
            status=400
        )

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Company not found"},
            status=404
        )

    # حفظ حالة impersonation في الجلسة
    request.session["impersonate_company_id"] = str(company.id)

    return JsonResponse({
        "success": True,
        "impersonating": True,
        "company": {
            "id": str(company.id),
            "name": company.name,
        }
    })


# ============================================================
# ⏹️ Stop Impersonation
# ============================================================
@login_required
@require_POST
def stop_impersonation(request):
    """
    إيقاف impersonation والعودة لوضع Super Admin
    """

    if not request.user.is_superuser:
        return forbidden()

    request.session.pop("impersonate_company_id", None)

    return JsonResponse({
        "success": True,
        "impersonating": False,
    })
