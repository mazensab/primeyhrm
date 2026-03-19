# ============================================================
# 📂 whatsapp_center/event_router.py
# Primey HR Cloud - WhatsApp Event Router
# ============================================================

from .models import ScopeType, TriggerSource
from .services import send_event_whatsapp_message


def notify_company_created(*, company, company_phone: str, company_name: str):
    return send_event_whatsapp_message(
        scope_type=ScopeType.SYSTEM,
        trigger_source=TriggerSource.COMPANY,
        event_code="company_created",
        recipient_phone=company_phone,
        recipient_name=company_name,
        company=None,
        context={
            "company_name": company_name,
        },
        related_model="Company",
        related_object_id=getattr(company, "id", ""),
    )


def notify_subscription_expiring_7_days(*, company, recipient_phone: str, recipient_name: str = ""):
    return send_event_whatsapp_message(
        scope_type=ScopeType.SYSTEM,
        trigger_source=TriggerSource.BILLING,
        event_code="subscription_expiring_7_days",
        recipient_phone=recipient_phone,
        recipient_name=recipient_name,
        context={
            "company_name": getattr(company, "name", ""),
            "days_left": 7,
        },
        related_model="Company",
        related_object_id=getattr(company, "id", ""),
    )


def notify_employee_absent(*, company, employee, recipient_phone: str, recipient_name: str = ""):
    return send_event_whatsapp_message(
        scope_type=ScopeType.COMPANY,
        trigger_source=TriggerSource.ATTENDANCE,
        event_code="employee_absent",
        recipient_phone=recipient_phone,
        recipient_name=recipient_name,
        company=company,
        context={
            "employee_name": getattr(employee, "full_name", "") or getattr(employee, "employee_code", ""),
            "company_name": getattr(company, "name", ""),
        },
        related_model="Employee",
        related_object_id=getattr(employee, "id", ""),
    )