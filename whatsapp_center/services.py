# ============================================================
# 📂 whatsapp_center/services.py
# Primey HR Cloud - WhatsApp Services
# ============================================================

from __future__ import annotations
import logging
from dataclasses import asdict
from typing import Any

from django.db import transaction
from django.utils import timezone

from .client import WhatsAppClient, WhatsAppSessionResult
from .models import (
    DeliveryStatus,
    MessageType,
    ScopeType,
    TemplateApprovalStatus,
    TemplateProviderSyncStatus,
    TriggerSource,
    WhatsAppMessageAttempt,
    WhatsAppMessageLog,
    WhatsAppTemplate,
)
from .selectors import (
    get_active_company_whatsapp_config,
    get_active_system_whatsapp_config,
    get_whatsapp_template,
)
from .template_builder import build_message_from_template
from .utils import normalize_phone_number, safe_text


# ============================================================
# 🔧 Internal Helpers
# ============================================================

def _build_client_from_config(config) -> WhatsAppClient:
    return WhatsAppClient(
        provider=getattr(config, "provider", "") or "",
        access_token=getattr(config, "access_token", "") or "",
        phone_number_id=getattr(config, "phone_number_id", "") or "",
        api_version=getattr(config, "api_version", "v22.0"),
        session_name=getattr(config, "session_name", "") or "primey-system-session",
    )


def _get_scope_config(scope_type: str, company=None):
    if scope_type == ScopeType.COMPANY:
        return get_active_company_whatsapp_config(company)
    return get_active_system_whatsapp_config()


def _build_fallback_body(*, event_code: str, context: dict) -> str:
    """
    نص احتياطي عند عدم وجود قالب.
    """
    explicit_message = safe_text(context.get("message"))
    if explicit_message:
        return explicit_message

    recipient_name = safe_text(context.get("recipient_name")) or "User"
    company_name = safe_text(context.get("company_name"))
    employee_name = safe_text(context.get("employee_name"))
    days_left = context.get("days_left")

    if event_code == "system_test_message":
        return explicit_message or "This is a system WhatsApp test message from Primey HR Cloud."

    if event_code == "onboarding_draft_created":
        return (
            f"تم إنشاء الطلب المبدئي بنجاح داخل Primey HR Cloud.\n"
            f"اسم الشركة: {company_name or safe_text(context.get('company_name'))}\n"
            f"اسم المسؤول: {safe_text(context.get('admin_name'))}\n"
            f"اسم المستخدم: {safe_text(context.get('admin_username'))}\n"
            f"الباقة: {safe_text(context.get('plan_name'))}\n"
            f"المدة: {safe_text(context.get('duration'))}\n"
            f"الإجمالي: {safe_text(context.get('total_amount'))}\n"
            f"الحالة: {safe_text(context.get('status'))}"
        )

    if event_code == "onboarding_draft_confirmed":
        return (
            f"تم تأكيد الطلب بنجاح داخل Primey HR Cloud.\n"
            f"اسم الشركة: {company_name or safe_text(context.get('company_name'))}\n"
            f"الباقة: {safe_text(context.get('plan_name'))}\n"
            f"المدة: {safe_text(context.get('duration'))}\n"
            f"الإجمالي: {safe_text(context.get('total_amount'))}\n"
            f"الحالة: {safe_text(context.get('status'))}"
        )

    if event_code == "company_created":
        if company_name:
            return f"Welcome to Primey HR Cloud. Your company '{company_name}' has been created successfully."
        return "Welcome to Primey HR Cloud. Your company has been created successfully."

    if event_code == "payment_details_sent":
        return (
            f"Payment details have been sent for {company_name or 'your company'}.\n"
            f"Invoice Number: {safe_text(context.get('invoice_number'))}\n"
            f"Amount: {safe_text(context.get('amount'))}\n"
            f"Link: {safe_text(context.get('payment_url'))}"
        )

    if event_code == "subscription_plan_upgrade_created":
        return (
            f"Upgrade request created for {company_name or 'your company'}.\n"
            f"Current Plan: {safe_text(context.get('current_plan_name'))}\n"
            f"New Plan: {safe_text(context.get('new_plan_name'))}\n"
            f"Invoice Number: {safe_text(context.get('invoice_number'))}\n"
            f"Amount: {safe_text(context.get('amount'))}"
        )

    if event_code == "subscription_plan_downgrade_requested":
        return (
            f"Downgrade request received for {company_name or 'your company'}.\n"
            f"Current Plan: {safe_text(context.get('current_plan_name'))}\n"
            f"Requested Plan: {safe_text(context.get('new_plan_name'))}"
        )

    if event_code == "subscription_renewal_invoice_created":
        return (
            f"Renewal invoice created for {company_name or 'your company'}.\n"
            f"Plan: {safe_text(context.get('plan_name'))}\n"
            f"Duration: {safe_text(context.get('duration'))}\n"
            f"Invoice Number: {safe_text(context.get('invoice_number'))}\n"
            f"Amount: {safe_text(context.get('amount'))}"
        )

    if event_code == "payment_confirmed_company_activated":
        return (
            f"Payment confirmed and company activated for {company_name or 'your company'}.\n"
            f"Invoice Number: {safe_text(context.get('invoice_number'))}\n"
            f"Plan: {safe_text(context.get('plan_name'))}\n"
            f"Amount: {safe_text(context.get('amount'))}\n"
            f"Payment Method: {safe_text(context.get('payment_method'))}"
        )

    if event_code == "cash_payment_confirmed":
        return (
            f"Cash payment confirmed for {company_name or 'your company'}.\n"
            f"Invoice Number: {safe_text(context.get('invoice_number'))}\n"
            f"Plan: {safe_text(context.get('plan_name'))}\n"
            f"Amount: {safe_text(context.get('amount'))}"
        )

    if event_code == "subscription_expiring_7_days":
        if company_name and days_left:
            return f"Reminder: subscription for {company_name} expires in {days_left} days."
        return "Reminder: your subscription is expiring soon."

    if event_code == "employee_absent":
        if employee_name:
            return f"Attendance alert: employee {employee_name} is marked absent."
        return "Attendance alert: an employee is marked absent."

    return f"Primey HR Cloud notification for {recipient_name}."


def _set_attr_if_exists(instance, field_name: str, value) -> bool:
    if hasattr(instance, field_name):
        setattr(instance, field_name, value)
        return True
    return False


def _sync_config_session_fields_from_result(config, result: WhatsAppSessionResult) -> None:
    """
    مزامنة نتيجة الجلسة داخل موديل الإعدادات الحالي
    بدون افتراض وجود جميع الحقول في كل نسخة.
    """
    update_fields: list[str] = []

    mapping = {
        "session_status": result.session_status or "disconnected",
        "session_connected_phone": result.connected_phone or "",
        "session_device_label": result.device_label or "",
        "session_qr_code": result.qr_code or "",
        "session_pairing_code": result.pairing_code or "",
        "last_error_message": result.error_message or "",
    }

    for field_name, field_value in mapping.items():
        if _set_attr_if_exists(config, field_name, field_value):
            update_fields.append(field_name)

    if result.connected and result.last_connected_at:
        if _set_attr_if_exists(config, "session_last_connected_at", timezone.now()):
            update_fields.append("session_last_connected_at")

    if _set_attr_if_exists(config, "last_health_check_at", timezone.now()):
        update_fields.append("last_health_check_at")

    if update_fields:
        seen = set()
        unique_fields = []
        for field in update_fields:
            if field not in seen:
                seen.add(field)
                unique_fields.append(field)

        config.save(update_fields=unique_fields)


def _session_result_to_payload(result: WhatsAppSessionResult) -> dict[str, Any]:
    return asdict(result)


# ============================================================
# 👥 Recipient Resolvers + Domain Notification Helpers
# ============================================================

logger = logging.getLogger(__name__)


def _safe_getattr(obj, attr_name: str, default=None):
    try:
        return getattr(obj, attr_name, default)
    except Exception:
        return default


def _stringify(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _resolve_employee_phone(employee) -> str:
    """
    استخراج جوال الموظف بشكل مرن حسب الحقول المتوفرة في الموديل.
    """
    candidates = [
        "mobile",
        "phone",
        "phone_number",
        "whatsapp_number",
        "personal_phone",
        "work_phone",
    ]
    for field_name in candidates:
        value = _stringify(_safe_getattr(employee, field_name, ""))
        if value:
            return value
    return ""


def _resolve_employee_language(company=None, employee=None) -> str:
    """
    تحديد لغة الإرسال الافتراضية.
    """
    language = _stringify(_safe_getattr(employee, "preferred_language", ""))
    if language in ["ar", "en"]:
        return language

    if company and hasattr(company, "whatsapp_config") and company.whatsapp_config:
        cfg_lang = _stringify(_safe_getattr(company.whatsapp_config, "default_language_code", ""))
        if cfg_lang:
            return cfg_lang

    return "ar"


def _resolve_employee_recipient(employee, company=None) -> dict[str, str]:
    return {
        "phone": _resolve_employee_phone(employee),
        "name": _stringify(_safe_getattr(employee, "full_name", "")) or _stringify(employee),
        "role": "employee",
        "language_code": _resolve_employee_language(company=company, employee=employee),
    }


def _resolve_user_phone(user) -> str:
    """
    استخراج جوال اليوزر بشكل مرن من user أو profile أو userprofile.
    """
    candidates = [
        "mobile",
        "phone",
        "phone_number",
        "whatsapp_number",
        "mobile_number",
    ]

    for field_name in candidates:
        value = _stringify(_safe_getattr(user, field_name, ""))
        if value:
            return value

    for profile_attr in ["profile", "userprofile"]:
        profile = _safe_getattr(user, profile_attr, None)
        if profile:
            for field_name in candidates:
                value = _stringify(_safe_getattr(profile, field_name, ""))
                if value:
                    return value

    return ""


def _resolve_related_user_for_employee(employee, company=None):
    """
    محاولة ربط الموظف بيوزر.
    """
    user = _safe_getattr(employee, "user", None)
    if user:
        return user

    return None


def _resolve_leave_type_name(leave_request) -> str:
    leave_type = _safe_getattr(leave_request, "leave_type", None)
    if not leave_type:
        return ""
    return _stringify(_safe_getattr(leave_type, "name", ""))


def _is_permission_leave(leave_request) -> bool:
    """
    اعتبار الاستئذان نوع إجازة حسب الاسم / الكود / المفتاح.
    """
    leave_type = _safe_getattr(leave_request, "leave_type", None)
    if not leave_type:
        return False

    candidates = [
        _stringify(_safe_getattr(leave_type, "name", "")),
        _stringify(_safe_getattr(leave_type, "code", "")),
        _stringify(_safe_getattr(leave_type, "slug", "")),
        _stringify(_safe_getattr(leave_type, "key", "")),
    ]

    normalized = " ".join(candidates).strip().lower()

    keywords = [
        "permission",
        "excuse",
        "hourly",
        "partial_day",
        "short_leave",
        "اذن",
        "إذن",
        "استئذان",
        "ساعات",
        "جزئي",
    ]

    return any(word.lower() in normalized for word in keywords)


def _build_leave_context(leave_request, extra_context: dict | None = None) -> dict[str, Any]:
    employee = _safe_getattr(leave_request, "employee", None)
    leave_type_name = _resolve_leave_type_name(leave_request)

    context = {
        "recipient_name": _stringify(_safe_getattr(employee, "full_name", "")),
        "employee_name": _stringify(_safe_getattr(employee, "full_name", "")),
        "leave_type": leave_type_name,
        "start_date": _safe_getattr(leave_request, "start_date", ""),
        "end_date": _safe_getattr(leave_request, "end_date", ""),
        "reason": _stringify(_safe_getattr(leave_request, "reason", "")),
        "status": _stringify(_safe_getattr(leave_request, "status", "")),
        "request_id": _safe_getattr(leave_request, "id", ""),
        "is_permission": _is_permission_leave(leave_request),
    }

    if extra_context:
        context.update(extra_context)

    return context


def _build_attendance_context(record, extra_context: dict | None = None) -> dict[str, Any]:
    employee = _safe_getattr(record, "employee", None)

    context = {
        "recipient_name": _stringify(_safe_getattr(employee, "full_name", "")),
        "employee_name": _stringify(_safe_getattr(employee, "full_name", "")),
        "attendance_date": _safe_getattr(record, "date", ""),
        "late_minutes": _safe_getattr(record, "late_minutes", 0) or 0,
        "status": _stringify(_safe_getattr(record, "status", "")),
        "check_in": _safe_getattr(record, "check_in", ""),
        "check_out": _safe_getattr(record, "check_out", ""),
        "attendance_id": _safe_getattr(record, "id", ""),
    }

    if extra_context:
        context.update(extra_context)

    return context


def _send_event_to_recipient_if_possible(
    *,
    scope_type: str,
    event_code: str,
    recipient_phone: str,
    recipient_name: str = "",
    recipient_role: str = "",
    trigger_source: str = TriggerSource.SYSTEM,
    company=None,
    language_code: str = "ar",
    context: dict | None = None,
    related_model: str = "",
    related_object_id: str = "",
):
    normalized_phone = normalize_phone_number(recipient_phone)
    if not normalized_phone:
        logger.info(
            "WhatsApp skipped: no valid phone | event=%s | role=%s | object=%s:%s",
            event_code,
            recipient_role,
            related_model,
            related_object_id,
        )
        return None

    try:
        return send_event_whatsapp_message(
            scope_type=scope_type,
            event_code=event_code,
            recipient_phone=normalized_phone,
            recipient_name=recipient_name,
            recipient_role=recipient_role,
            trigger_source=trigger_source,
            company=company,
            language_code=language_code,
            context=context or {},
            related_model=related_model,
            related_object_id=str(related_object_id or ""),
        )
    except Exception:
        logger.exception(
            "WhatsApp send failed | event=%s | phone=%s | object=%s:%s",
            event_code,
            normalized_phone,
            related_model,
            related_object_id,
        )
        return None


def send_leave_status_whatsapp_notifications(
    *,
    leave_request,
    company=None,
    action: str,
    send_to_employee: bool = True,
    send_to_user: bool = True,
    extra_context: dict | None = None,
) -> dict[str, Any]:
    """
    إرسال إشعار حالة الإجازة / الاستئذان.
    action:
    - approved
    - rejected
    """
    employee = _safe_getattr(leave_request, "employee", None)
    if not employee:
        return {
            "success": False,
            "message": "employee_not_found",
            "sent_count": 0,
        }

    is_permission = _is_permission_leave(leave_request)

    if action == "approved":
        event_code = "permission_request_approved" if is_permission else "leave_request_approved"
    elif action == "rejected":
        event_code = "permission_request_rejected" if is_permission else "leave_request_rejected"
    else:
        return {
            "success": False,
            "message": "invalid_action",
            "sent_count": 0,
        }

    context = _build_leave_context(leave_request, extra_context=extra_context)
    sent_count = 0

    if send_to_employee:
        employee_recipient = _resolve_employee_recipient(employee, company=company)
        result = _send_event_to_recipient_if_possible(
            scope_type=ScopeType.COMPANY,
            event_code=event_code,
            recipient_phone=employee_recipient["phone"],
            recipient_name=employee_recipient["name"],
            recipient_role=employee_recipient["role"],
            trigger_source=TriggerSource.LEAVE,
            company=company,
            language_code=employee_recipient["language_code"],
            context=context,
            related_model="leave_request",
            related_object_id=_safe_getattr(leave_request, "id", ""),
        )
        if result:
            sent_count += 1

    if send_to_user:
        related_user = _resolve_related_user_for_employee(employee, company=company)
        if related_user:
            user_phone = _resolve_user_phone(related_user)
            user_language = _stringify(_safe_getattr(related_user, "preferred_language", "")) or "ar"
            user_name = ""
            get_full_name_fn = _safe_getattr(related_user, "get_full_name", None)
            if callable(get_full_name_fn):
                user_name = _stringify(get_full_name_fn())
            if not user_name:
                user_name = _stringify(related_user)

            result = _send_event_to_recipient_if_possible(
                scope_type=ScopeType.COMPANY,
                event_code=event_code,
                recipient_phone=user_phone,
                recipient_name=user_name,
                recipient_role="user",
                trigger_source=TriggerSource.LEAVE,
                company=company,
                language_code=user_language if user_language in ["ar", "en"] else "ar",
                context=context,
                related_model="leave_request",
                related_object_id=_safe_getattr(leave_request, "id", ""),
            )
            if result:
                sent_count += 1

    return {
        "success": True,
        "event_code": event_code,
        "sent_count": sent_count,
        "is_permission": is_permission,
    }


def send_attendance_status_whatsapp_notifications(
    *,
    attendance_record,
    company=None,
    send_to_employee: bool = True,
    send_to_user: bool = True,
) -> dict[str, Any]:
    """
    إرسال إشعار تأخير / غياب.
    """
    employee = _safe_getattr(attendance_record, "employee", None)
    if not employee:
        return {
            "success": False,
            "message": "employee_not_found",
            "sent_count": 0,
        }

    status_value = _stringify(_safe_getattr(attendance_record, "status", "")).lower()
    late_minutes = int(_safe_getattr(attendance_record, "late_minutes", 0) or 0)

    if status_value == "absent":
        event_code = "attendance_absent_alert"
    elif status_value == "late" or late_minutes > 0:
        event_code = "attendance_late_alert"
    else:
        return {
            "success": False,
            "message": "status_not_supported",
            "sent_count": 0,
        }

    context = _build_attendance_context(attendance_record)
    sent_count = 0

    if send_to_employee:
        employee_recipient = _resolve_employee_recipient(employee, company=company)
        result = _send_event_to_recipient_if_possible(
            scope_type=ScopeType.COMPANY,
            event_code=event_code,
            recipient_phone=employee_recipient["phone"],
            recipient_name=employee_recipient["name"],
            recipient_role=employee_recipient["role"],
            trigger_source=TriggerSource.ATTENDANCE,
            company=company,
            language_code=employee_recipient["language_code"],
            context=context,
            related_model="attendance_record",
            related_object_id=_safe_getattr(attendance_record, "id", ""),
        )
        if result:
            sent_count += 1

    if send_to_user:
        related_user = _resolve_related_user_for_employee(employee, company=company)
        if related_user:
            user_phone = _resolve_user_phone(related_user)
            user_language = _stringify(_safe_getattr(related_user, "preferred_language", "")) or "ar"
            user_name = ""
            get_full_name_fn = _safe_getattr(related_user, "get_full_name", None)
            if callable(get_full_name_fn):
                user_name = _stringify(get_full_name_fn())
            if not user_name:
                user_name = _stringify(related_user)

            result = _send_event_to_recipient_if_possible(
                scope_type=ScopeType.COMPANY,
                event_code=event_code,
                recipient_phone=user_phone,
                recipient_name=user_name,
                recipient_role="user",
                trigger_source=TriggerSource.ATTENDANCE,
                company=company,
                language_code=user_language if user_language in ["ar", "en"] else "ar",
                context=context,
                related_model="attendance_record",
                related_object_id=_safe_getattr(attendance_record, "id", ""),
            )
            if result:
                sent_count += 1

    return {
        "success": True,
        "event_code": event_code,
        "sent_count": sent_count,
        "status": status_value,
    }


# ============================================================
# 🏢 Company Default Template Bootstrap
# ============================================================

def _company_template_seed_rows() -> list[dict[str, str]]:
    """
    القوالب الافتراضية الخاصة بالشركة.
    ملاحظة:
    - كلها Company Scope
    - كلها version=1
    - عربي + إنجليزي
    - بدون تكرار
    """

    return [
        {
            "event_code": "company_created",
            "language_code": "ar",
            "template_name": "إنشاء شركة جديدة",
            "template_key": "company_created",
            "header_text": "",
            "body_text": (
                "مرحبًا {{company_name}}، تم إنشاء شركتكم بنجاح في Primey HR Cloud.\n"
                "تفاصيل الاشتراك:\n"
                "- الباقة: {{plan_name}}\n"
                "- تاريخ البداية: {{start_date}}\n"
                "- تاريخ النهاية: {{end_date}}\n"
                "يمكنكم تسجيل الدخول من خلال الرابط التالي:\n"
                "{{login_url}}\n"
                "يسعدنا خدمتكم ونتطلع لتجربة موفقة."
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "company_created",
            "language_code": "en",
            "template_name": "Company Created Welcome",
            "template_key": "company_created",
            "header_text": "",
            "body_text": (
                "Hello {{company_name}}, your company has been created successfully in Primey HR Cloud.\n"
                "Subscription details:\n"
                "- Plan: {{plan_name}}\n"
                "- Start Date: {{start_date}}\n"
                "- End Date: {{end_date}}\n"
                "You can log in using the following link:\n"
                "{{login_url}}\n"
                "We are pleased to serve you and wish you a great experience."
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "payment_details_sent",
            "language_code": "ar",
            "template_name": "إرسال بيانات الدفع",
            "template_key": "payment_details_sent",
            "header_text": "",
            "body_text": (
                "مرحبًا {{company_name}}، تم إرسال بيانات الدفع الخاصة باشتراككم.\n"
                "رقم الفاتورة: {{invoice_number}}\n"
                "المبلغ: {{amount}}\n"
                "الرابط: {{payment_url}}\n"
                "يرجى إتمام السداد لإكمال التفعيل."
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "payment_details_sent",
            "language_code": "en",
            "template_name": "Payment Details Sent",
            "template_key": "payment_details_sent",
            "header_text": "",
            "body_text": (
                "Hello {{company_name}}, your payment details have been sent.\n"
                "Invoice Number: {{invoice_number}}\n"
                "Amount: {{amount}}\n"
                "Payment Link: {{payment_url}}\n"
                "Please complete the payment to finish activation."
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "subscription_plan_upgrade_created",
            "language_code": "ar",
            "template_name": "إنشاء فاتورة ترقية الباقة",
            "template_key": "subscription_plan_upgrade_created",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم إنشاء طلب ترقية الباقة بنجاح.\n"
                "اسم الشركة: {{company_name}}\n"
                "الباقة الحالية: {{current_plan_name}}\n"
                "الباقة الجديدة: {{new_plan_name}}\n"
                "رقم الفاتورة: {{invoice_number}}\n"
                "المبلغ المستحق: {{amount}}\n"
                "الحالة: {{status}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "subscription_plan_upgrade_created",
            "language_code": "en",
            "template_name": "Subscription Upgrade Invoice Created",
            "template_key": "subscription_plan_upgrade_created",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, a subscription upgrade request has been created successfully.\n"
                "Company: {{company_name}}\n"
                "Current Plan: {{current_plan_name}}\n"
                "New Plan: {{new_plan_name}}\n"
                "Invoice Number: {{invoice_number}}\n"
                "Amount Due: {{amount}}\n"
                "Status: {{status}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "subscription_plan_downgrade_requested",
            "language_code": "ar",
            "template_name": "طلب تخفيض الباقة",
            "template_key": "subscription_plan_downgrade_requested",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم استلام طلب تخفيض الباقة.\n"
                "اسم الشركة: {{company_name}}\n"
                "الباقة الحالية: {{current_plan_name}}\n"
                "الباقة المطلوبة: {{new_plan_name}}\n"
                "سيتم تنفيذ الطلب بعد استكمال طبقة الجدولة الرسمية."
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "subscription_plan_downgrade_requested",
            "language_code": "en",
            "template_name": "Subscription Downgrade Requested",
            "template_key": "subscription_plan_downgrade_requested",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, a subscription downgrade request has been received.\n"
                "Company: {{company_name}}\n"
                "Current Plan: {{current_plan_name}}\n"
                "Requested Plan: {{new_plan_name}}\n"
                "This request will be applied after the official scheduling layer is completed."
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "subscription_renewal_invoice_created",
            "language_code": "ar",
            "template_name": "إنشاء فاتورة تجديد الاشتراك",
            "template_key": "subscription_renewal_invoice_created",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم إنشاء فاتورة تجديد الاشتراك بنجاح.\n"
                "اسم الشركة: {{company_name}}\n"
                "الباقة: {{plan_name}}\n"
                "مدة التجديد: {{duration}}\n"
                "رقم الفاتورة: {{invoice_number}}\n"
                "المبلغ: {{amount}}\n"
                "الحالة: {{status}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "subscription_renewal_invoice_created",
            "language_code": "en",
            "template_name": "Subscription Renewal Invoice Created",
            "template_key": "subscription_renewal_invoice_created",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, a subscription renewal invoice has been created successfully.\n"
                "Company: {{company_name}}\n"
                "Plan: {{plan_name}}\n"
                "Duration: {{duration}}\n"
                "Invoice Number: {{invoice_number}}\n"
                "Amount: {{amount}}\n"
                "Status: {{status}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "payment_confirmed_company_activated",
            "language_code": "ar",
            "template_name": "تأكيد الدفع وتفعيل الشركة",
            "template_key": "payment_confirmed_company_activated",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم تأكيد الدفع وتفعيل الشركة بنجاح.\n"
                "اسم الشركة: {{company_name}}\n"
                "اسم الأدمن: {{admin_name}}\n"
                "اسم المستخدم: {{username}}\n"
                "الباقة: {{plan_name}}\n"
                "رقم الفاتورة: {{invoice_number}}\n"
                "طريقة الدفع: {{payment_method}}\n"
                "الإجمالي: {{amount}}\n"
                "الحالة: {{status}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "payment_confirmed_company_activated",
            "language_code": "en",
            "template_name": "Payment Confirmed Company Activated",
            "template_key": "payment_confirmed_company_activated",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, payment has been confirmed and the company has been activated successfully.\n"
                "Company: {{company_name}}\n"
                "Admin Name: {{admin_name}}\n"
                "Username: {{username}}\n"
                "Plan: {{plan_name}}\n"
                "Invoice Number: {{invoice_number}}\n"
                "Payment Method: {{payment_method}}\n"
                "Total: {{amount}}\n"
                "Status: {{status}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "cash_payment_confirmed",
            "language_code": "ar",
            "template_name": "تأكيد الدفع النقدي",
            "template_key": "cash_payment_confirmed",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم تأكيد الدفع النقدي بنجاح.\n"
                "اسم الشركة: {{company_name}}\n"
                "رقم الفاتورة: {{invoice_number}}\n"
                "الباقة: {{plan_name}}\n"
                "طريقة الدفع: {{payment_method}}\n"
                "Subtotal: {{subtotal}}\n"
                "VAT: {{vat}}\n"
                "الإجمالي: {{amount}}\n"
                "الحالة: {{status}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "cash_payment_confirmed",
            "language_code": "en",
            "template_name": "Cash Payment Confirmed",
            "template_key": "cash_payment_confirmed",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, cash payment has been confirmed successfully.\n"
                "Company: {{company_name}}\n"
                "Invoice Number: {{invoice_number}}\n"
                "Plan: {{plan_name}}\n"
                "Payment Method: {{payment_method}}\n"
                "Subtotal: {{subtotal}}\n"
                "VAT: {{vat}}\n"
                "Total: {{amount}}\n"
                "Status: {{status}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "welcome_message",
            "language_code": "ar",
            "template_name": "رسالة ترحيبية",
            "template_key": "welcome_message",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، أهلاً بك في {{company_name}}.\n"
                "تم تجهيز حسابك على Primey HR Cloud.\n"
                "اسم المستخدم: {{username}}\n"
                "رابط الدخول: {{login_url}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "welcome_message",
            "language_code": "en",
            "template_name": "Welcome Message",
            "template_key": "welcome_message",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, welcome to {{company_name}}.\n"
                "Your account on Primey HR Cloud is ready.\n"
                "Username: {{username}}\n"
                "Login URL: {{login_url}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "password_changed",
            "language_code": "ar",
            "template_name": "تغيير كلمة المرور",
            "template_key": "password_changed",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم تغيير كلمة المرور الخاصة بحسابك بنجاح.\n"
                "إذا لم تقم بهذا الإجراء، يرجى التواصل مع إدارة النظام فورًا."
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "password_changed",
            "language_code": "en",
            "template_name": "Password Changed",
            "template_key": "password_changed",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, your account password has been changed successfully.\n"
                "If you did not perform this action, please contact the system administrator immediately."
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "employee_added",
            "language_code": "ar",
            "template_name": "إضافة موظف",
            "template_key": "employee_added",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم إضافة الموظف {{employee_name}} بنجاح.\n"
                "الرقم الوظيفي: {{employee_code}}\n"
                "المسمى الوظيفي: {{job_title}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "employee_added",
            "language_code": "en",
            "template_name": "Employee Added",
            "template_key": "employee_added",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, employee {{employee_name}} has been added successfully.\n"
                "Employee Code: {{employee_code}}\n"
                "Job Title: {{job_title}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "contract_created",
            "language_code": "ar",
            "template_name": "إنشاء عقد",
            "template_key": "contract_created",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم إنشاء عقد الموظف {{employee_name}}.\n"
                "رقم العقد: {{contract_number}}\n"
                "تاريخ البداية: {{start_date}}\n"
                "تاريخ النهاية: {{end_date}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "contract_created",
            "language_code": "en",
            "template_name": "Contract Created",
            "template_key": "contract_created",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, a contract has been created for {{employee_name}}.\n"
                "Contract Number: {{contract_number}}\n"
                "Start Date: {{start_date}}\n"
                "End Date: {{end_date}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "payroll_ready",
            "language_code": "ar",
            "template_name": "الرواتب جاهزة",
            "template_key": "payroll_ready",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، أصبحت مسيرات الرواتب جاهزة للمراجعة.\n"
                "الدورة: {{payroll_period}}\n"
                "تاريخ الصرف: {{pay_date}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "payroll_ready",
            "language_code": "en",
            "template_name": "Payroll Ready",
            "template_key": "payroll_ready",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, payroll is now ready for review.\n"
                "Period: {{payroll_period}}\n"
                "Pay Date: {{pay_date}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "leave_request_submitted",
            "language_code": "ar",
            "template_name": "تقديم طلب إجازة",
            "template_key": "leave_request_submitted",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم تقديم طلب إجازة جديد.\n"
                "الموظف: {{employee_name}}\n"
                "نوع الإجازة: {{leave_type}}\n"
                "من {{start_date}} إلى {{end_date}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "leave_request_submitted",
            "language_code": "en",
            "template_name": "Leave Request Submitted",
            "template_key": "leave_request_submitted",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, a new leave request has been submitted.\n"
                "Employee: {{employee_name}}\n"
                "Leave Type: {{leave_type}}\n"
                "From {{start_date}} to {{end_date}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "leave_request_approved",
            "language_code": "ar",
            "template_name": "اعتماد طلب إجازة",
            "template_key": "leave_request_approved",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تمت الموافقة على طلب الإجازة.\n"
                "نوع الإجازة: {{leave_type}}\n"
                "من {{start_date}} إلى {{end_date}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "leave_request_approved",
            "language_code": "en",
            "template_name": "Leave Request Approved",
            "template_key": "leave_request_approved",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, your leave request has been approved.\n"
                "Leave Type: {{leave_type}}\n"
                "From {{start_date}} to {{end_date}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "leave_request_rejected",
            "language_code": "ar",
            "template_name": "رفض طلب إجازة",
            "template_key": "leave_request_rejected",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم رفض طلب الإجازة.\n"
                "نوع الإجازة: {{leave_type}}\n"
                "سبب الرفض: {{reason}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "leave_request_rejected",
            "language_code": "en",
            "template_name": "Leave Request Rejected",
            "template_key": "leave_request_rejected",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, your leave request has been rejected.\n"
                "Leave Type: {{leave_type}}\n"
                "Reason: {{reason}}"
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "attendance_absent_alert",
            "language_code": "ar",
            "template_name": "تنبيه غياب",
            "template_key": "attendance_absent_alert",
            "header_text": "",
            "body_text": (
                "تنبيه حضور:\n"
                "تم تسجيل الموظف {{employee_name}} كغائب بتاريخ {{attendance_date}}."
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "attendance_absent_alert",
            "language_code": "en",
            "template_name": "Attendance Absent Alert",
            "template_key": "attendance_absent_alert",
            "header_text": "",
            "body_text": (
                "Attendance Alert:\n"
                "Employee {{employee_name}} has been marked absent on {{attendance_date}}."
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "attendance_late_alert",
            "language_code": "ar",
            "template_name": "تنبيه تأخير",
            "template_key": "attendance_late_alert",
            "header_text": "",
            "body_text": (
                "تنبيه حضور:\n"
                "تم تسجيل تأخر الموظف {{employee_name}} بتاريخ {{attendance_date}} لمدة {{late_minutes}} دقيقة."
            ),
            "footer_text": "Primey HR Cloud",
        },
        {
            "event_code": "attendance_late_alert",
            "language_code": "en",
            "template_name": "Attendance Late Alert",
            "template_key": "attendance_late_alert",
            "header_text": "",
            "body_text": (
                "Attendance Alert:\n"
                "Employee {{employee_name}} was marked late on {{attendance_date}} by {{late_minutes}} minutes."
            ),
            "footer_text": "Primey HR Cloud",
        },
    ]


@transaction.atomic
def ensure_company_default_whatsapp_templates(company, user=None) -> dict[str, Any]:
    """
    إنشاء القوالب الافتراضية الخاصة بالشركة عند عدم وجودها.
    - آمن ضد التكرار
    - لا يخلط مع قوالب النظام
    - ينشئ النسخ العربية والإنجليزية
    """
    if not company:
        return {
            "created": 0,
            "existing": 0,
            "total_company_templates": 0,
        }

    existing_company_count = WhatsAppTemplate.objects.filter(
        scope_type=ScopeType.COMPANY,
        company=company,
    ).count()

    if existing_company_count > 0:
        return {
            "created": 0,
            "existing": existing_company_count,
            "total_company_templates": existing_company_count,
        }

    created_count = 0

    for seed in _company_template_seed_rows():
        item, created = WhatsAppTemplate.objects.get_or_create(
            scope_type=ScopeType.COMPANY,
            company=company,
            event_code=seed["event_code"],
            language_code=seed["language_code"],
            version=1,
            defaults={
                "template_key": seed["template_key"],
                "template_name": seed["template_name"],
                "message_type": MessageType.TEXT,
                "header_text": seed.get("header_text", ""),
                "body_text": seed["body_text"],
                "footer_text": seed.get("footer_text", ""),
                "button_text": "",
                "button_url": "",
                "meta_template_name": "",
                "meta_template_namespace": "",
                "approval_status": TemplateApprovalStatus.DRAFT,
                "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
                "is_default": True,
                "is_active": True,
            },
        )

        if created:
            if user and getattr(user, "is_authenticated", False):
                if hasattr(item, "created_by"):
                    item.created_by = user
                if hasattr(item, "updated_by"):
                    item.updated_by = user
                item.save(update_fields=["created_by", "updated_by"])
            created_count += 1

    total_company_templates = WhatsAppTemplate.objects.filter(
        scope_type=ScopeType.COMPANY,
        company=company,
    ).count()

    return {
        "created": created_count,
        "existing": total_company_templates - created_count,
        "total_company_templates": total_company_templates,
    }


# ============================================================
# 🔌 Session Management Services
# ============================================================

@transaction.atomic
def get_whatsapp_session_status(
    *,
    scope_type: str,
    company=None,
) -> dict[str, Any]:
    """
    جلب حالة الجلسة الحالية من الـ gateway ثم مزامنتها داخل config.
    """
    config = _get_scope_config(scope_type=scope_type, company=company)

    if not config:
        return {
            "success": False,
            "message": "No active WhatsApp config found",
            "session_status": "failed",
            "connected": False,
        }

    client = _build_client_from_config(config)
    result = client.get_session_status()

    _sync_config_session_fields_from_result(config, result)

    payload = _session_result_to_payload(result)
    payload["session_name"] = getattr(config, "session_name", "") or "primey-system-session"
    payload["provider"] = getattr(config, "provider", "") or ""
    return payload


@transaction.atomic
def create_whatsapp_qr_session(
    *,
    scope_type: str,
    company=None,
) -> dict[str, Any]:
    """
    إنشاء QR جديد للجلسة.
    """
    config = _get_scope_config(scope_type=scope_type, company=company)

    if not config:
        return {
            "success": False,
            "message": "No active WhatsApp config found",
            "session_status": "failed",
            "connected": False,
        }

    client = _build_client_from_config(config)
    result = client.create_qr_session()

    _sync_config_session_fields_from_result(config, result)

    payload = _session_result_to_payload(result)
    payload["session_name"] = getattr(config, "session_name", "") or "primey-system-session"
    payload["provider"] = getattr(config, "provider", "") or ""
    return payload


@transaction.atomic
def create_whatsapp_pairing_code_session(
    *,
    scope_type: str,
    phone_number: str,
    company=None,
) -> dict[str, Any]:
    """
    إنشاء Pairing Code برقم الجوال.
    """
    config = _get_scope_config(scope_type=scope_type, company=company)

    if not config:
        return {
            "success": False,
            "message": "No active WhatsApp config found",
            "session_status": "failed",
            "connected": False,
        }

    normalized_phone = normalize_phone_number(phone_number)

    if not normalized_phone:
        return {
            "success": False,
            "message": "phone_number is required",
            "session_status": "failed",
            "connected": False,
        }

    client = _build_client_from_config(config)
    result = client.create_pairing_code_session(phone_number=normalized_phone)

    _sync_config_session_fields_from_result(config, result)

    payload = _session_result_to_payload(result)
    payload["session_name"] = getattr(config, "session_name", "") or "primey-system-session"
    payload["provider"] = getattr(config, "provider", "") or ""
    return payload


@transaction.atomic
def disconnect_whatsapp_session(
    *,
    scope_type: str,
    company=None,
) -> dict[str, Any]:
    """
    فصل الجلسة الحالية.
    """
    config = _get_scope_config(scope_type=scope_type, company=company)

    if not config:
        return {
            "success": False,
            "message": "No active WhatsApp config found",
            "session_status": "failed",
            "connected": False,
        }

    client = _build_client_from_config(config)
    result = client.disconnect_session()

    _sync_config_session_fields_from_result(config, result)

    payload = _session_result_to_payload(result)
    payload["session_name"] = getattr(config, "session_name", "") or "primey-system-session"
    payload["provider"] = getattr(config, "provider", "") or ""
    return payload


# ============================================================
# 📨 Message Sending Service
# ============================================================

@transaction.atomic
def send_event_whatsapp_message(
    *,
    scope_type: str,
    event_code: str,
    recipient_phone: str,
    recipient_name: str = "",
    recipient_role: str = "",
    trigger_source: str = TriggerSource.SYSTEM,
    company=None,
    language_code: str = "ar",
    context: dict | None = None,
    related_model: str = "",
    related_object_id: str = "",
    attachment_url: str = "",
    attachment_name: str = "",
    mime_type: str = "",
):
    """
    خدمة عامة لإرسال رسالة واتساب مبنية على event/template.
    """
    context = context or {}
    normalized_phone = normalize_phone_number(recipient_phone)

    if not normalized_phone:
        log = WhatsAppMessageLog.objects.create(
            scope_type=scope_type,
            company=company if scope_type == ScopeType.COMPANY else None,
            trigger_source=trigger_source,
            event_code=event_code,
            recipient_name=safe_text(recipient_name),
            recipient_phone=safe_text(recipient_phone) or "+0000000000",
            recipient_role=safe_text(recipient_role),
            message_type=MessageType.TEXT,
            language_code=language_code,
            message_body="",
            delivery_status=DeliveryStatus.FAILED,
            failure_reason="Invalid or missing recipient phone number",
            related_model=related_model,
            related_object_id=str(related_object_id or ""),
            payload_json=context,
        )
        return log

    config = _get_scope_config(scope_type=scope_type, company=company)

    if not config:
        log = WhatsAppMessageLog.objects.create(
            scope_type=scope_type,
            company=company if scope_type == ScopeType.COMPANY else None,
            trigger_source=trigger_source,
            event_code=event_code,
            recipient_name=safe_text(recipient_name),
            recipient_phone=normalized_phone,
            recipient_role=safe_text(recipient_role),
            message_type=MessageType.TEXT,
            language_code=language_code,
            message_body="",
            delivery_status=DeliveryStatus.FAILED,
            failure_reason="No active WhatsApp config found",
            related_model=related_model,
            related_object_id=str(related_object_id or ""),
            payload_json=context,
        )
        return log

    template = get_whatsapp_template(
        scope_type=scope_type,
        company=company,
        event_code=event_code,
        language_code=language_code,
    )

    built = build_message_from_template(template, context) if template else None
    message_type = MessageType.DOCUMENT if attachment_url else MessageType.TEXT
    if template:
        message_type = template.message_type or message_type

    if built and built.body_text:
        message_body = built.body_text
    else:
        message_body = _build_fallback_body(event_code=event_code, context=context)

    log = WhatsAppMessageLog.objects.create(
        scope_type=scope_type,
        company=company if scope_type == ScopeType.COMPANY else None,
        trigger_source=trigger_source,
        event_code=event_code,
        recipient_name=safe_text(recipient_name),
        recipient_phone=normalized_phone,
        recipient_role=safe_text(recipient_role),
        message_type=message_type,
        template=template,
        template_name_snapshot=(template.template_name if template else ""),
        language_code=language_code,
        header_text=(built.header_text if built else ""),
        message_body=message_body,
        footer_text=(built.footer_text if built else ""),
        attachment_url=attachment_url or "",
        attachment_name=attachment_name or "",
        mime_type=mime_type or "",
        delivery_status=DeliveryStatus.QUEUED,
        related_model=related_model,
        related_object_id=str(related_object_id or ""),
        payload_json=context,
    )

    client = _build_client_from_config(config)

    attempt = WhatsAppMessageAttempt.objects.create(
        message_log=log,
        attempt_number=1,
        request_payload={
            "recipient_phone": normalized_phone,
            "event_code": event_code,
            "scope_type": scope_type,
            "attachment_url": attachment_url,
            "provider": getattr(config, "provider", ""),
            "session_name": getattr(config, "session_name", ""),
        },
    )

    if attachment_url:
        result = client.send_document_message(
            to_phone=normalized_phone,
            document_url=attachment_url,
            caption=log.message_body,
            filename=attachment_name,
        )
    else:
        result = client.send_text_message(
            to_phone=normalized_phone,
            body=log.message_body,
        )

    attempt.response_payload = result.response_data or {}
    attempt.status_code = result.status_code
    attempt.provider_status = result.provider_status
    attempt.is_success = result.success
    attempt.error_message = result.error_message
    attempt.finished_at = timezone.now()
    attempt.save(
        update_fields=[
            "response_payload",
            "status_code",
            "provider_status",
            "is_success",
            "error_message",
            "finished_at",
        ]
    )

    response_data = result.response_data or {}
    if isinstance(response_data, dict) and any(
        key in response_data
        for key in [
            "session_status",
            "connected",
            "connected_phone",
            "device_label",
            "qr_code",
            "pairing_code",
            "last_connected_at",
            "message",
        ]
    ):
        session_result = WhatsAppSessionResult(
            success=bool(response_data.get("success", result.success)),
            status_code=int(response_data.get("status_code", result.status_code or 200)),
            session_status=str(response_data.get("session_status") or "disconnected"),
            connected=bool(response_data.get("connected", False)),
            connected_phone=str(response_data.get("connected_phone") or ""),
            device_label=str(response_data.get("device_label") or ""),
            qr_code=str(response_data.get("qr_code") or ""),
            pairing_code=str(response_data.get("pairing_code") or ""),
            last_connected_at=str(response_data.get("last_connected_at") or ""),
            response_data=response_data,
            error_message=str(response_data.get("message") or result.error_message or ""),
        )
        _sync_config_session_fields_from_result(config, session_result)

    if result.success:
        log.delivery_status = DeliveryStatus.SENT
        log.provider_status = result.provider_status
        log.external_message_id = result.external_message_id
        log.response_json = result.response_data or {}
        log.sent_at = timezone.now()
        log.save(
            update_fields=[
                "delivery_status",
                "provider_status",
                "external_message_id",
                "response_json",
                "sent_at",
                "updated_at",
            ]
        )
    else:
        log.delivery_status = DeliveryStatus.FAILED
        log.provider_status = result.provider_status
        log.failure_reason = result.error_message
        log.response_json = result.response_data or {}
        log.failed_at = timezone.now()
        log.save(
            update_fields=[
                "delivery_status",
                "provider_status",
                "failure_reason",
                "response_json",
                "failed_at",
                "updated_at",
            ]
        )

    return log