from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from company_manager.models import Company
from notification_center import services_company as company_notification_services


def _safe_value(value):
    return value if value not in (None, "") else "-"


def _build_company_toggle_context(company: Company, *, previous_status: bool, new_status: bool) -> dict:
    return {
        "company_id": company.id,
        "company_name": _safe_value(company.name),
        "previous_is_active": bool(previous_status),
        "is_active": bool(new_status),
        "status_label": "ACTIVE" if new_status else "INACTIVE",
    }


def _dispatch_company_toggle_notification(*, company: Company, actor, previous_status: bool, new_status: bool) -> None:
    """
    تمرير حدث تفعيل/تعطيل الشركة إلى الطبقة الرسمية فقط.
    """

    candidate_function_names = (
        [
            "notify_company_activated",
            "send_company_activated_notification",
        ]
        if new_status
        else [
            "notify_company_deactivated",
            "send_company_deactivated_notification",
        ]
    )

    notify_func = None
    for func_name in candidate_function_names:
        notify_func = getattr(company_notification_services, func_name, None)
        if callable(notify_func):
            break

    if not callable(notify_func):
        return

    context = _build_company_toggle_context(
        company,
        previous_status=previous_status,
        new_status=new_status,
    )

    try:
        notify_func(
            company=company,
            actor=actor,
            extra_context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(
            company=company,
            actor=actor,
            context=context,
        )
        return
    except TypeError:
        pass

    try:
        notify_func(company=company)
        return
    except Exception:
        return


@login_required
def toggle_company_active(request, company_id):

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    company = get_object_or_404(Company, id=company_id)

    previous_status = bool(company.is_active)
    company.is_active = not company.is_active
    company.save(update_fields=["is_active"])

    transaction.on_commit(
        lambda: _dispatch_company_toggle_notification(
            company=company,
            actor=request.user,
            previous_status=previous_status,
            new_status=bool(company.is_active),
        )
    )

    return JsonResponse({
        "success": True,
        "company_id": company.id,
        "is_active": company.is_active
    })