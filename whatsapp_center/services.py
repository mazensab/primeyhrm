# ============================================================
# 📂 whatsapp_center/services.py
# Mham Cloud - WhatsApp Services
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
    """
    جلب WhatsApp config حسب الـ scope مع fallback آمن:

    1) إذا كان scope = COMPANY:
       - نحاول أولاً Company Config
       - إذا لم يوجد Company Config نعمل fallback إلى System Config

    2) إذا كان scope = SYSTEM:
       - نستخدم System Config مباشرة

    الهدف:
    - أحداث Auth / Notification Center التي تمرّر company في السياق
      لا تنكسر إذا لم يوجد للشركة config واتساب خاص بها.
    - الحفاظ على سلوك الشركة الطبيعي إذا كان عندها config فعلي.
    """
    if scope_type == ScopeType.COMPANY:
        company_config = None

        try:
            if company is not None:
                company_config = get_active_company_whatsapp_config(company)
        except Exception:
            logger.exception(
                "Failed while resolving company WhatsApp config | company_id=%s",
                getattr(company, "id", None) if company else None,
            )
            company_config = None

        if company_config:
            return company_config

        # ----------------------------------------------------
        # Fallback مهم:
        # إذا لم يوجد config للشركة نرجع إلى system config
        # حتى لا تفشل أحداث Notification Center / Auth
        # برسالة No active WhatsApp config found
        # ----------------------------------------------------
        system_config = None
        try:
            system_config = get_active_system_whatsapp_config()
        except Exception:
            logger.exception("Failed while resolving fallback system WhatsApp config")
            system_config = None

        if system_config:
            logger.info(
                "WhatsApp config fallback applied | requested_scope=COMPANY | company_id=%s | fallback_scope=SYSTEM | system_config_id=%s",
                getattr(company, "id", None) if company else None,
                getattr(system_config, "id", None),
            )
            return system_config

        return None

    # --------------------------------------------------------
    # SYSTEM scope
    # --------------------------------------------------------
    try:
        return get_active_system_whatsapp_config()
    except Exception:
        logger.exception("Failed while resolving system WhatsApp config")
        return None

def _build_fallback_body(*, event_code: str, context: dict) -> str:
    """
    نص احتياطي عند عدم وجود قالب.
    """
    explicit_message = safe_text(context.get("message"))
    if explicit_message:
        return explicit_message

    recipient_name = (
        safe_text(context.get("recipient_name"))
        or safe_text(context.get("employee_name_ar"))
        or safe_text(context.get("employee_arabic_name"))
        or safe_text(context.get("employee_name"))
        or "User"
    )
    company_name = safe_text(context.get("company_name"))
    employee_name = (
        safe_text(context.get("employee_name_ar"))
        or safe_text(context.get("employee_arabic_name"))
        or safe_text(context.get("employee_name"))
        or recipient_name
    )
    days_left = context.get("days_left")

    if event_code == "system_test_message":
        return explicit_message or "This is a system WhatsApp test message from Mham Cloud."

    if event_code == "onboarding_draft_created":
        return (
            f"تم إنشاء الطلب المبدئي بنجاح داخل Mham Cloud.\n"
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
            f"تم تأكيد الطلب بنجاح داخل Mham Cloud.\n"
            f"اسم الشركة: {company_name or safe_text(context.get('company_name'))}\n"
            f"الباقة: {safe_text(context.get('plan_name'))}\n"
            f"المدة: {safe_text(context.get('duration'))}\n"
            f"الإجمالي: {safe_text(context.get('total_amount'))}\n"
            f"الحالة: {safe_text(context.get('status'))}"
        )

    if event_code == "company_created":
        if company_name:
            return f"Welcome to Mham Cloud. Your company '{company_name}' has been created successfully."
        return "Welcome to Mham Cloud. Your company has been created successfully."

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

    if event_code == "attendance_present":
        return (
            f"تنبيه حضور:\n"
            f"تم تسجيل حضور الموظف {employee_name or recipient_name} بتاريخ {safe_text(context.get('attendance_date'))}.\n"
            f"وقت الدخول: {safe_text(context.get('check_in'))}\n"
            f"وقت الخروج: {safe_text(context.get('check_out'))}"
        )

    if event_code == "attendance_check_in":
        return (
            f"تنبيه حركة حضور:\n"
            f"قام الموظف {employee_name or recipient_name} بتسجيل الدخول بتاريخ {safe_text(context.get('attendance_date'))}.\n"
            f"وقت الدخول: {safe_text(context.get('check_in'))}"
        )

    if event_code == "attendance_check_out":
        return (
            f"تنبيه حركة حضور:\n"
            f"قام الموظف {employee_name or recipient_name} بتسجيل الخروج بتاريخ {safe_text(context.get('attendance_date'))}.\n"
            f"وقت الخروج: {safe_text(context.get('check_out'))}"
        )

    if event_code == "leave_request_submitted":
        return (
            f"تم تقديم طلب إجازة جديد.\n"
            f"الموظف: {employee_name or recipient_name}\n"
            f"نوع الإجازة: {safe_text(context.get('leave_type'))}\n"
            f"من: {safe_text(context.get('start_date'))}\n"
            f"إلى: {safe_text(context.get('end_date'))}\n"
            f"الحالة: {safe_text(context.get('status'))}"
        )

    if event_code == "payroll_paid":
        return (
            f"تم صرف الراتب بنجاح.\n"
            f"الموظف: {employee_name or recipient_name}\n"
            f"الدورة: {safe_text(context.get('payroll_period'))}\n"
            f"صافي الراتب: {safe_text(context.get('net_salary'))}\n"
            f"المبلغ المصروف: {safe_text(context.get('paid_amount'))}\n"
            f"طريقة الدفع: {safe_text(context.get('payment_method'))}\n"
            f"الحالة: {safe_text(context.get('payment_status'))}"
        )

    if event_code == "employee_activated":
        return (
            f"تم تفعيل الموظف بنجاح.\n"
            f"اسم الموظف: {employee_name or recipient_name}\n"
            f"الحالة الحالية: {safe_text(context.get('status'))}"
        )

    if event_code == "employee_deactivated":
        return (
            f"تم تعطيل الموظف.\n"
            f"اسم الموظف: {employee_name or recipient_name}\n"
            f"الحالة الحالية: {safe_text(context.get('status'))}"
        )

    return f"Mham Cloud notification for {recipient_name}."


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


def _is_session_not_connected_failure(log: WhatsAppMessageLog) -> bool:
    """
    التحقق هل فشل الرسالة كان بسبب أن الجلسة غير متصلة.
    """
    failure_reason = safe_text(getattr(log, "failure_reason", ""))
    response_json = getattr(log, "response_json", {}) or {}
    payload_json = getattr(log, "payload_json", {}) or {}

    candidates = [
        failure_reason,
        safe_text(getattr(log, "provider_status", "")),
        safe_text(response_json.get("message")),
        safe_text(response_json.get("error")),
        safe_text(payload_json.get("message")),
    ]

    normalized_text = " | ".join([item.lower() for item in candidates if item]).strip()

    session_markers = [
        "whatsapp session is not connected",
        "session is not connected",
        "not connected",
        "gateway_failed",
    ]

    return any(marker in normalized_text for marker in session_markers)


def _retry_existing_whatsapp_log(log: WhatsAppMessageLog):
    """
    إعادة إرسال نفس السجل الفاشل بدون إنشاء WhatsAppMessageLog جديد.
    ينشئ Attempt جديد فقط ويحدث نفس السجل.
    """
    if not log:
        return None

    scope_type = getattr(log, "scope_type", "")
    company = getattr(log, "company", None)

    config = _get_scope_config(scope_type=scope_type, company=company)
    if not config:
        log.delivery_status = DeliveryStatus.FAILED
        log.provider_status = "gateway_failed"
        log.failure_reason = "No active WhatsApp config found during retry"
        log.failed_at = timezone.now()
        log.save(
            update_fields=[
                "delivery_status",
                "provider_status",
                "failure_reason",
                "failed_at",
                "updated_at",
            ]
        )
        return log

    recipient_phone = normalize_phone_number(getattr(log, "recipient_phone", ""))
    if not recipient_phone:
        log.delivery_status = DeliveryStatus.FAILED
        log.provider_status = "validation_failed"
        log.failure_reason = "Invalid or missing recipient phone number during retry"
        log.failed_at = timezone.now()
        log.save(
            update_fields=[
                "delivery_status",
                "provider_status",
                "failure_reason",
                "failed_at",
                "updated_at",
            ]
        )
        return log

    client = _build_client_from_config(config)

    last_attempt_number = (
        WhatsAppMessageAttempt.objects
        .filter(message_log=log)
        .order_by("-attempt_number")
        .values_list("attempt_number", flat=True)
        .first()
        or 0
    )

    log.delivery_status = DeliveryStatus.QUEUED
    log.failure_reason = ""
    log.provider_status = ""
    log.save(
        update_fields=[
            "delivery_status",
            "failure_reason",
            "provider_status",
            "updated_at",
        ]
    )

    attempt = WhatsAppMessageAttempt.objects.create(
        message_log=log,
        attempt_number=last_attempt_number + 1,
        request_payload={
            "recipient_phone": recipient_phone,
            "event_code": getattr(log, "event_code", ""),
            "scope_type": scope_type,
            "attachment_url": getattr(log, "attachment_url", ""),
            "provider": getattr(config, "provider", ""),
            "session_name": getattr(config, "session_name", ""),
            "retry": True,
        },
    )

    attachment_url = getattr(log, "attachment_url", "") or ""
    attachment_name = getattr(log, "attachment_name", "") or ""

    if attachment_url:
        result = client.send_document_message(
            to_phone=recipient_phone,
            document_url=attachment_url,
            caption=getattr(log, "message_body", "") or "",
            filename=attachment_name,
        )
    else:
        result = client.send_text_message(
            to_phone=recipient_phone,
            body=getattr(log, "message_body", "") or "",
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
        log.failure_reason = ""
        log.sent_at = timezone.now()
        log.failed_at = None
        log.save(
            update_fields=[
                "delivery_status",
                "provider_status",
                "external_message_id",
                "response_json",
                "failure_reason",
                "sent_at",
                "failed_at",
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


@transaction.atomic
def retry_failed_whatsapp_messages_for_scope(
    *,
    scope_type: str,
    company=None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    إعادة إرسال الرسائل الفاشلة تلقائيًا عند رجوع الجلسة.
    يعيد فقط الرسائل التي فشلت بسبب انقطاع الجلسة.
    """
    logs_qs = (
        WhatsAppMessageLog.objects
        .select_related("template", "company")
        .filter(
            scope_type=scope_type,
            delivery_status=DeliveryStatus.FAILED,
        )
        .order_by("created_at")
    )

    if scope_type == ScopeType.COMPANY:
        logs_qs = logs_qs.filter(company=company)
    else:
        logs_qs = logs_qs.filter(company__isnull=True)

    retried = 0
    sent = 0
    failed_again = 0
    skipped = 0

    for log in logs_qs[:limit]:
        if not _is_session_not_connected_failure(log):
            skipped += 1
            continue

        retried += 1
        updated_log = _retry_existing_whatsapp_log(log)

        if updated_log and getattr(updated_log, "delivery_status", "") == DeliveryStatus.SENT:
            sent += 1
        else:
            failed_again += 1

    return {
        "success": True,
        "retried": retried,
        "sent": sent,
        "failed_again": failed_again,
        "skipped": skipped,
        "scope_type": scope_type,
        "company_id": getattr(company, "id", None) if company else None,
    }


def _auto_retry_failed_messages_after_reconnect(
    *,
    scope_type: str,
    company=None,
    connected: bool,
) -> dict[str, Any]:
    """
    إذا أصبحت الجلسة متصلة يتم تشغيل إعادة الإرسال التلقائي.
    """
    if not connected:
        return {
            "success": True,
            "retried": 0,
            "sent": 0,
            "failed_again": 0,
            "skipped": 0,
            "auto_retry_triggered": False,
        }

    retry_result = retry_failed_whatsapp_messages_for_scope(
        scope_type=scope_type,
        company=company,
        limit=100,
    )
    retry_result["auto_retry_triggered"] = True
    return retry_result


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
    ✅ يدعم mobile_number لأنه المستخدم فعليًا في Employee API.
    ✅ يحاول أيضًا fallback إلى اليوزر المرتبط إذا وُجد.
    """
    candidates = [
        "mobile_number",
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

    related_user = _resolve_related_user_for_employee(employee)
    if related_user:
        related_user_phone = _resolve_user_phone(related_user)
        if related_user_phone:
            return related_user_phone

    return ""


def _build_employee_created_context(employee, extra_context: dict | None = None) -> dict[str, Any]:
    user = _safe_getattr(employee, "user", None)
    department = _safe_getattr(employee, "department", None)
    job_title = _safe_getattr(employee, "job_title", None)

    context = {
        "recipient_name": _stringify(_safe_getattr(employee, "full_name", "")),
        "employee_name": _stringify(_safe_getattr(employee, "full_name", "")),
        "employee_code": _stringify(_safe_getattr(employee, "employee_number", "")),
        "job_title": _stringify(_safe_getattr(job_title, "name", "")),
        "department_name": _stringify(_safe_getattr(department, "name", "")),
        "username": _stringify(_safe_getattr(user, "username", "")),
        "email": _stringify(_safe_getattr(user, "email", "")),
        "employee_id": _safe_getattr(employee, "id", ""),
    }

    if extra_context:
        context.update(extra_context)

    return context


def send_employee_created_whatsapp_notifications(
    *,
    employee,
    company=None,
    send_to_employee: bool = True,
    send_to_user: bool = True,
    send_to_manager: bool = True,
    extra_context: dict | None = None,
) -> dict[str, Any]:
    """
    إرسال إشعار إنشاء موظف جديد.
    يستخدم event_code = employee_added
    """
    if not employee:
        return {
            "success": False,
            "message": "employee_not_found",
            "sent_count": 0,
        }

    context = _build_employee_created_context(employee, extra_context=extra_context)
    sent_count = 0
    event_code = "employee_added"

    recipients = _collect_employee_notification_recipients(
        employee=employee,
        company=company,
        send_to_employee=send_to_employee,
        send_to_user=send_to_user,
        send_to_manager=send_to_manager,
    )

    for recipient in recipients:
        result = _send_event_to_recipient_if_possible(
            scope_type=ScopeType.COMPANY,
            event_code=event_code,
            recipient_phone=recipient["phone"],
            recipient_name=recipient["name"],
            recipient_role=recipient["role"],
            trigger_source=TriggerSource.EMPLOYEE,
            company=company,
            language_code=recipient["language_code"],
            context=context,
            related_model="employee",
            related_object_id=_safe_getattr(employee, "id", ""),
        )
        if result:
            sent_count += 1

    return {
        "success": True,
        "event_code": event_code,
        "sent_count": sent_count,
    }


def _resolve_employee_language(company=None, employee=None) -> str:
    """
    تحديد لغة الإرسال الافتراضية.
    """
    language = _stringify(_safe_getattr(employee, "preferred_language", ""))
    if language in ["ar", "en"]:
        return language

    if company and hasattr(company, "whatsapp_config") and company.whatsapp_config:
        cfg_lang = _stringify(_safe_getattr(company.whatsapp_config, "default_language_code", ""))
        if cfg_lang in ["ar", "en"]:
            return cfg_lang

    return "ar"


def _resolve_employee_recipient(employee, company=None) -> dict[str, Any]:
    return {
        "user": None,
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


def _resolve_user_display_name(user) -> str:
    user_name = ""
    get_full_name_fn = _safe_getattr(user, "get_full_name", None)
    if callable(get_full_name_fn):
        user_name = _stringify(get_full_name_fn())
    if not user_name:
        user_name = _stringify(_safe_getattr(user, "full_name", ""))
    if not user_name:
        user_name = _stringify(user)
    return user_name


def _resolve_user_language(user, company=None) -> str:
    language = _stringify(_safe_getattr(user, "preferred_language", ""))
    if language in ["ar", "en"]:
        return language

    for profile_attr in ["profile", "userprofile"]:
        profile = _safe_getattr(user, profile_attr, None)
        if profile:
            profile_lang = _stringify(_safe_getattr(profile, "preferred_language", ""))
            if profile_lang in ["ar", "en"]:
                return profile_lang

    if company and hasattr(company, "whatsapp_config") and company.whatsapp_config:
        cfg_lang = _stringify(_safe_getattr(company.whatsapp_config, "default_language_code", ""))
        if cfg_lang in ["ar", "en"]:
            return cfg_lang

    return "ar"


def _resolve_related_user_for_employee(employee, company=None):
    """
    محاولة ربط الموظف بيوزر.
    """
    direct_candidates = [
        "user",
        "auth_user",
        "account_user",
        "linked_user",
    ]

    for attr_name in direct_candidates:
        user = _safe_getattr(employee, attr_name, None)
        if user:
            return user

    return None


def _extract_user_from_candidate(candidate):
    """
    يحاول استخراج User من أي كيان محتمل:
    - User مباشرة
    - Employee -> user
    - Profile-like object -> user
    """
    if not candidate:
        return None

    if _safe_getattr(candidate, "is_authenticated", None) is not None:
        return candidate

    nested_user = _safe_getattr(candidate, "user", None)
    if nested_user:
        return nested_user

    return None


def _resolve_direct_manager_user_for_employee(employee, company=None):
    """
    محاولة مرنة لاستخراج المدير المباشر للموظف.
    لا تكسر النظام إذا لم تكن الحقول موجودة.
    """
    direct_manager_candidates = [
        "manager",
        "line_manager",
        "direct_manager",
        "reporting_manager",
        "supervisor",
        "manager_user",
        "line_manager_user",
        "direct_manager_user",
        "supervisor_user",
    ]

    for attr_name in direct_manager_candidates:
        manager_obj = _safe_getattr(employee, attr_name, None)
        manager_user = _extract_user_from_candidate(manager_obj)
        if manager_user:
            return manager_user

    # محاولة ثانية عبر القسم / الوحدة التنظيمية
    structure_candidates = [
        "department",
        "section",
        "team",
        "unit",
        "position",
        "job_title",
    ]

    structure_manager_fields = [
        "manager",
        "line_manager",
        "direct_manager",
        "supervisor",
        "head",
        "director",
        "responsible_user",
        "user",
    ]

    for structure_attr in structure_candidates:
        structure_obj = _safe_getattr(employee, structure_attr, None)
        if not structure_obj:
            continue

        for manager_field in structure_manager_fields:
            manager_candidate = _safe_getattr(structure_obj, manager_field, None)
            manager_user = _extract_user_from_candidate(manager_candidate)
            if manager_user:
                return manager_user

    return None


def _resolve_user_recipient(user, company=None, role: str = "user") -> dict[str, Any]:
    if not user:
        return {
            "user": None,
            "phone": "",
            "name": "",
            "role": role,
            "language_code": "ar",
        }

    return {
        "user": user,
        "phone": _resolve_user_phone(user),
        "name": _resolve_user_display_name(user),
        "role": role,
        "language_code": _resolve_user_language(user, company=company),
    }


def _resolve_manager_recipient(employee, company=None) -> dict[str, Any]:
    """
    تجهيز بيانات مستلم المدير المباشر.
    """
    manager_user = _resolve_direct_manager_user_for_employee(employee, company=company)
    if not manager_user:
        return {
            "user": None,
            "phone": "",
            "name": "",
            "role": "manager",
            "language_code": "ar",
        }

    return _resolve_user_recipient(manager_user, company=company, role="manager")


def _build_recipient_dedupe_key(recipient: dict[str, Any]) -> str:
    """
    منع تكرار الإرسال لنفس الشخص:
    - أولاً على user.pk إن وجد
    - ثم على رقم الجوال بعد التطبيع
    - ثم fallback على role + name
    """
    user = recipient.get("user")
    user_pk = _safe_getattr(user, "pk", None)
    if user_pk:
        return f"user:{user_pk}"

    normalized_phone = normalize_phone_number(recipient.get("phone", ""))
    if normalized_phone:
        return f"phone:{normalized_phone}"

    return f"fallback:{recipient.get('role', '')}:{recipient.get('name', '')}"


def _collect_employee_notification_recipients(
    *,
    employee,
    company=None,
    send_to_employee: bool = True,
    send_to_user: bool = True,
    send_to_manager: bool = True,
) -> list[dict[str, Any]]:
    """
    بناء قائمة المستلمين النهائية مع:
    - employee
    - linked user
    - direct manager
    + منع التكرار
    """
    recipients: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _append_if_unique(recipient: dict[str, Any] | None):
        if not recipient:
            return

        key = _build_recipient_dedupe_key(recipient)
        if key in seen:
            return

        seen.add(key)
        recipients.append(recipient)

    if send_to_employee:
        _append_if_unique(_resolve_employee_recipient(employee, company=company))

    if send_to_user:
        related_user = _resolve_related_user_for_employee(employee, company=company)
        if related_user:
            _append_if_unique(_resolve_user_recipient(related_user, company=company, role="user"))

    if send_to_manager:
        manager_recipient = _resolve_manager_recipient(employee, company=company)
        if manager_recipient.get("user") or manager_recipient.get("phone"):
            _append_if_unique(manager_recipient)

    return recipients


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


def _build_payroll_context(payroll_record, extra_context: dict | None = None) -> dict[str, Any]:
    employee = _safe_getattr(payroll_record, "employee", None)
    run = _safe_getattr(payroll_record, "run", None)

    payroll_period = ""
    try:
        month_value = _safe_getattr(run, "month", None) or _safe_getattr(payroll_record, "month", None)
        if month_value and hasattr(month_value, "strftime"):
            payroll_period = month_value.strftime("%Y-%m")
        elif month_value:
            payroll_period = _stringify(month_value)
    except Exception:
        payroll_period = _stringify(_safe_getattr(payroll_record, "month", ""))

    context = {
        "recipient_name": _stringify(_safe_getattr(employee, "full_name", "")),
        "employee_name": _stringify(_safe_getattr(employee, "full_name", "")),
        "payroll_period": payroll_period,
        "pay_date": _safe_getattr(_safe_getattr(payroll_record, "paid_at", None), "date", lambda: "")()
        if _safe_getattr(payroll_record, "paid_at", None)
        else "",
        "payment_status": _stringify(_safe_getattr(payroll_record, "status", "")),
        "payment_method": _stringify(_safe_getattr(payroll_record, "payment_method", "")),
        "paid_amount": _safe_getattr(payroll_record, "paid_amount", 0) or 0,
        "remaining_amount": _safe_getattr(payroll_record, "remaining_amount", 0) or 0,
        "net_salary": _safe_getattr(payroll_record, "net_salary", 0) or 0,
        "record_id": _safe_getattr(payroll_record, "id", ""),
    }

    if extra_context:
        context.update(extra_context)

    return context

def _build_employee_status_values(employee) -> dict[str, Any]:
    """
    توحيد قيم حالة الموظف لاستخدامها في:
    - المسار المباشر داخل whatsapp_center
    - Notification Center Bridge
    - القوالب الحالية التي تعتمد على {{status}}
    """

    user = _safe_getattr(employee, "user", None)
    is_active = bool(_safe_getattr(user, "is_active", False))

    return {
        "status": "نشط" if is_active else "معطل",
        "status_code": "ACTIVE" if is_active else "INACTIVE",
        "status_label": "نشط" if is_active else "معطل",
        "status_label_en": "Active" if is_active else "Inactive",
        "is_active": is_active,
    }


def _build_employee_status_context(employee, extra_context: dict | None = None) -> dict[str, Any]:
    status_values = _build_employee_status_values(employee)

    employee_name = (
        _stringify(_safe_getattr(employee, "full_name_ar", ""))
        or _stringify(_safe_getattr(employee, "arabic_name", ""))
        or _stringify(_safe_getattr(employee, "name_ar", ""))
        or _stringify(_safe_getattr(employee, "full_name", ""))
    )

    context = {
        "recipient_name": employee_name,
        "employee_name": employee_name,
        "employee_name_ar": employee_name,
        "employee_arabic_name": employee_name,
        "employee_code": _stringify(_safe_getattr(employee, "employee_number", "")),
        "employee_id": _safe_getattr(employee, "id", ""),
        **status_values,
    }

    if extra_context:
        context.update(extra_context)

    return context


def _inject_employee_status_context_if_missing(*, event=None, context: dict) -> dict[str, Any]:
    """
    حقن status تلقائيًا إذا كان الحدث متعلقًا بتفعيل/تعطيل الموظف
    ولم تكن القيم موجودة داخل event.context.
    """
    resolved_context = dict(context or {})

    event_code = _stringify(_safe_getattr(event, "event_code", "")).lower()
    if event_code not in {"employee_activated", "employee_deactivated"}:
        return resolved_context

    target_object = _safe_getattr(event, "target_object", None)

    employee = None

    if target_object and (
        hasattr(target_object, "employee_number")
        or hasattr(target_object, "mobile_number")
        or hasattr(target_object, "work_start_date")
    ):
        employee = target_object

    if not employee:
        employee = _safe_getattr(target_object, "employee", None)

    if employee:
        status_values = _build_employee_status_values(employee)

        for key, value in status_values.items():
            if key not in resolved_context or resolved_context.get(key) in [None, "", "{{status}}"]:
                resolved_context[key] = value

        employee_name = (
            _stringify(_safe_getattr(employee, "full_name_ar", ""))
            or _stringify(_safe_getattr(employee, "arabic_name", ""))
            or _stringify(_safe_getattr(employee, "name_ar", ""))
            or _stringify(_safe_getattr(employee, "full_name", ""))
        )

        if not resolved_context.get("employee_name") or resolved_context.get("employee_name") == "{{employee_name}}":
            resolved_context["employee_name"] = employee_name

        if not resolved_context.get("employee_name_ar"):
            resolved_context["employee_name_ar"] = employee_name

        if not resolved_context.get("employee_arabic_name"):
            resolved_context["employee_arabic_name"] = employee_name

        if not resolved_context.get("recipient_name"):
            resolved_context["recipient_name"] = employee_name

        if not resolved_context.get("employee_code"):
            resolved_context["employee_code"] = _stringify(_safe_getattr(employee, "employee_number", ""))

        return resolved_context

    if not resolved_context.get("status") or resolved_context.get("status") == "{{status}}":
        resolved_context["status"] = "نشط" if event_code == "employee_activated" else "معطل"

    if not resolved_context.get("status_code"):
        resolved_context["status_code"] = "ACTIVE" if event_code == "employee_activated" else "INACTIVE"

    if not resolved_context.get("status_label"):
        resolved_context["status_label"] = "نشط" if event_code == "employee_activated" else "معطل"

    if not resolved_context.get("status_label_en"):
        resolved_context["status_label_en"] = "Active" if event_code == "employee_activated" else "Inactive"

    return resolved_context


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
    send_to_manager: bool = True,
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

    recipients = _collect_employee_notification_recipients(
        employee=employee,
        company=company,
        send_to_employee=send_to_employee,
        send_to_user=send_to_user,
        send_to_manager=send_to_manager,
    )

    for recipient in recipients:
        result = _send_event_to_recipient_if_possible(
            scope_type=ScopeType.COMPANY,
            event_code=event_code,
            recipient_phone=recipient["phone"],
            recipient_name=recipient["name"],
            recipient_role=recipient["role"],
            trigger_source=TriggerSource.LEAVE,
            company=company,
            language_code=recipient["language_code"],
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


def send_leave_submitted_whatsapp_notifications(
    *,
    leave_request,
    company=None,
    send_to_employee: bool = True,
    send_to_user: bool = True,
    send_to_manager: bool = True,
    extra_context: dict | None = None,
) -> dict[str, Any]:
    """
    إرسال إشعار تقديم طلب إجازة / استئذان.
    """
    employee = _safe_getattr(leave_request, "employee", None)
    if not employee:
        return {
            "success": False,
            "message": "employee_not_found",
            "sent_count": 0,
        }

    context = _build_leave_context(leave_request, extra_context=extra_context)
    sent_count = 0
    event_code = "leave_request_submitted"

    recipients = _collect_employee_notification_recipients(
        employee=employee,
        company=company,
        send_to_employee=send_to_employee,
        send_to_user=send_to_user,
        send_to_manager=send_to_manager,
    )

    for recipient in recipients:
        result = _send_event_to_recipient_if_possible(
            scope_type=ScopeType.COMPANY,
            event_code=event_code,
            recipient_phone=recipient["phone"],
            recipient_name=recipient["name"],
            recipient_role=recipient["role"],
            trigger_source=TriggerSource.LEAVE,
            company=company,
            language_code=recipient["language_code"],
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
    }


def send_payroll_whatsapp_notifications(
    *,
    payroll_record,
    company=None,
    send_to_employee: bool = True,
    send_to_user: bool = True,
    send_to_manager: bool = True,
    extra_context: dict | None = None,
) -> dict[str, Any]:
    """
    إرسال إشعار صرف راتب الموظف.
    """
    employee = _safe_getattr(payroll_record, "employee", None)
    if not employee:
        return {
            "success": False,
            "message": "employee_not_found",
            "sent_count": 0,
        }

    context = _build_payroll_context(payroll_record, extra_context=extra_context)
    sent_count = 0
    event_code = "payroll_paid"

    recipients = _collect_employee_notification_recipients(
        employee=employee,
        company=company,
        send_to_employee=send_to_employee,
        send_to_user=send_to_user,
        send_to_manager=send_to_manager,
    )

    for recipient in recipients:
        result = _send_event_to_recipient_if_possible(
            scope_type=ScopeType.COMPANY,
            event_code=event_code,
            recipient_phone=recipient["phone"],
            recipient_name=recipient["name"],
            recipient_role=recipient["role"],
            trigger_source=TriggerSource.PAYROLL,
            company=company,
            language_code=recipient["language_code"],
            context=context,
            related_model="payroll_record",
            related_object_id=_safe_getattr(payroll_record, "id", ""),
        )
        if result:
            sent_count += 1

    return {
        "success": True,
        "event_code": event_code,
        "sent_count": sent_count,
    }


def send_employee_status_whatsapp_notifications(
    *,
    employee,
    company=None,
    send_to_employee: bool = True,
    send_to_user: bool = True,
    send_to_manager: bool = True,
    extra_context: dict | None = None,
) -> dict[str, Any]:
    """
    إرسال إشعار تفعيل / تعطيل الموظف.
    """
    if not employee:
        return {
            "success": False,
            "message": "employee_not_found",
            "sent_count": 0,
        }

    user = _safe_getattr(employee, "user", None)
    is_active = bool(_safe_getattr(user, "is_active", False))
    event_code = "employee_activated" if is_active else "employee_deactivated"

    context = _build_employee_status_context(employee, extra_context=extra_context)
    sent_count = 0

    recipients = _collect_employee_notification_recipients(
        employee=employee,
        company=company,
        send_to_employee=send_to_employee,
        send_to_user=send_to_user,
        send_to_manager=send_to_manager,
    )

    for recipient in recipients:
        result = _send_event_to_recipient_if_possible(
            scope_type=ScopeType.COMPANY,
            event_code=event_code,
            recipient_phone=recipient["phone"],
            recipient_name=recipient["name"],
            recipient_role=recipient["role"],
            trigger_source=TriggerSource.EMPLOYEE,
            company=company,
            language_code=recipient["language_code"],
            context=context,
            related_model="employee",
            related_object_id=_safe_getattr(employee, "id", ""),
        )
        if result:
            sent_count += 1

    return {
        "success": True,
        "event_code": event_code,
        "sent_count": sent_count,
        "is_active": is_active,
    }


def send_attendance_status_whatsapp_notifications(
    *,
    attendance_record,
    company=None,
    send_to_employee: bool = True,
    send_to_user: bool = True,
    send_to_manager: bool = True,
    action: str | None = None,
    extra_context: dict | None = None,
) -> dict[str, Any]:
    """
    إرسال إشعار الحضور:
    - absent
    - late
    - present
    - check_in
    - check_out

    ملاحظة:
    للحفاظ على التوافق الخلفي:
    - إذا لم يُرسل action فسيتم استنتاجه من status الحالي كما كان سابقًا.
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

    normalized_action = _stringify(action).lower()

    if normalized_action == "check_in":
        event_code = "attendance_check_in"
    elif normalized_action == "check_out":
        event_code = "attendance_check_out"
    elif normalized_action == "present":
        event_code = "attendance_present"
    elif status_value == "absent":
        event_code = "attendance_absent_alert"
    elif status_value == "late" or late_minutes > 0:
        event_code = "attendance_late_alert"
    elif status_value == "present":
        event_code = "attendance_present"
    else:
        return {
            "success": False,
            "message": "status_not_supported",
            "sent_count": 0,
        }

    context = _build_attendance_context(attendance_record, extra_context=extra_context)
    sent_count = 0

    recipients = _collect_employee_notification_recipients(
        employee=employee,
        company=company,
        send_to_employee=send_to_employee,
        send_to_user=send_to_user,
        send_to_manager=send_to_manager,
    )

    for recipient in recipients:
        result = _send_event_to_recipient_if_possible(
            scope_type=ScopeType.COMPANY,
            event_code=event_code,
            recipient_phone=recipient["phone"],
            recipient_name=recipient["name"],
            recipient_role=recipient["role"],
            trigger_source=TriggerSource.ATTENDANCE,
            company=company,
            language_code=recipient["language_code"],
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
        "action": normalized_action or status_value,
    }


# ============================================================
# 🧩 Default Template Seed Helpers
# ============================================================

def _build_seed_defaults(seed: dict[str, Any]) -> dict[str, Any]:
    """
    توحيد defaults الخاصة بإنشاء القوالب الافتراضية.
    """
    return {
        "template_key": seed["template_key"],
        "template_name": seed["template_name"],
        "message_type": seed.get("message_type", MessageType.TEXT),
        "header_text": seed.get("header_text", ""),
        "body_text": seed["body_text"],
        "footer_text": seed.get("footer_text", ""),
        "button_text": seed.get("button_text", ""),
        "button_url": seed.get("button_url", ""),
        "meta_template_name": seed.get("meta_template_name", ""),
        "meta_template_namespace": seed.get("meta_template_namespace", ""),
        "approval_status": seed.get("approval_status", TemplateApprovalStatus.DRAFT),
        "provider_status": seed.get("provider_status", TemplateProviderSyncStatus.NOT_SYNCED),
        "rejection_reason": seed.get("rejection_reason", ""),
        "is_default": seed.get("is_default", True),
        "is_active": seed.get("is_active", True),
    }


def _system_template_seed_rows() -> list[dict[str, Any]]:
    """
    القوالب الافتراضية الخاصة بالنظام.
    مطابقة للقوالب المعتمدة حاليًا في اللوكل.
    """

    return [
        {
            "event_code": "company_created",
            "template_key": "system_company_created_ar",
            "template_name": "إنشاء شركة جديدة",
            "language_code": "ar",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "مرحبًا {{company_name}}،\n"
                "تم إنشاء شركتكم بنجاح في Mham Cloud.\n\n"
                "تفاصيل الاشتراك:\n"
                "- الباقة: {{plan_name}}\n"
                "- تاريخ البداية: {{start_date}}\n"
                "- تاريخ النهاية: {{end_date}}\n\n"
                "يمكنكم تسجيل الدخول من خلال الرابط التالي:\n"
                "{{login_url}}\n\n"
                "نسعد بخدمتكم ونتطلع لتجربة موفقة."
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": True,
            "is_active": True,
        },
        {
            "event_code": "company_created",
            "template_key": "system_company_created_en",
            "template_name": "Company Created Welcome",
            "language_code": "en",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "Hello {{company_name}},\n"
                "Your company has been created successfully in Mham Cloud.\n\n"
                "Subscription details:\n"
                "- Plan: {{plan_name}}\n"
                "- Start Date: {{start_date}}\n"
                "- End Date: {{end_date}}\n\n"
                "You can log in using the following link:\n"
                "{{login_url}}\n\n"
                "We are pleased to serve you and wish you a great experience."
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": False,
            "is_active": True,
        },
        {
            "event_code": "invoice_payment_details",
            "template_key": "system_invoice_payment_details_ar",
            "template_name": "إرسال بيانات الدفع",
            "language_code": "ar",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "مرحبًاا {{company_name}}،\n"
                "تم إصدار فاتورة جديدة لكم، وفيما يلي بيانات الدفع:\n\n"
                "- رقم الفاتورة: {{invoice_number}}\n"
                "- المبلغ: {{amount}}\n"
                "- طريقة الدفع: {{payment_method}}\n"
                "- حالة الدفع: {{payment_status}}\n\n"
                "يمكنكم متابعة الفاتورة أو إتمام السداد عبر الرابط التالي:\n"
                "{{invoice_url}}"
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": True,
            "is_active": True,
        },
        {
            "event_code": "invoice_payment_details",
            "template_key": "system_invoice_payment_details_en",
            "template_name": "Payment Details Sent",
            "language_code": "en",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "Hello {{company_name}},\n"
                "A new invoice has been issued for you. Please find the payment details below:\n\n"
                "- Invoice Number: {{invoice_number}}\n"
                "- Amount: {{amount}}\n"
                "- Payment Method: {{payment_method}}\n"
                "- Payment Status: {{payment_status}}\n\n"
                "You can review the invoice or complete payment using the following link:\n"
                "{{invoice_url}}"
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": False,
            "is_active": True,
        },
        {
            "event_code": "invoice_pdf_sent",
            "template_key": "system_invoice_pdf_sent_ar",
            "template_name": "إرسال الفاتورة PDF",
            "language_code": "ar",
            "message_type": MessageType.DOCUMENT,
            "header_text": "",
            "body_text": (
                "مرحبًا {{companyy_name}}،\n"
                "تم إرسال نسخة الفاتورة الخاصة بكم بنجاح.\n\n"
                "تفاصيل الفاتورة:\n"
                "- رقم الفاتورة: {{invoice_number}}\n"
                "- المبلغ: {{amount}}\n"
                "- تاريخ الإصدار: {{invoice_date}}\n\n"
                "تم إرفاق ملف الفاتورة PDF أو يمكنكم الوصول إليه عبر الرابط التالي:\n"
                "{{invoice_url}}"
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": True,
            "is_active": True,
        },
        {
            "event_code": "invoice_pdf_sent",
            "template_key": "system_invoice_pdf_sent_en",
            "template_name": "Invoice PDF Sent",
            "language_code": "en",
            "message_type": MessageType.DOCUMENT,
            "header_text": "",
            "body_text": (
                "Hello {{company_name}},\n"
                "Your invoice copy has been sent successfully.\n\n"
                "Invoice details:\n"
                "- Invoice Number: {{invoice_number}}\n"
                "- Amount: {{amount}}\n"
                "- Invoice Date: {{invoice_date}}\n\n"
                "The invoice PDF has been attached, or you may access it using the following link:\n"
                "{{invoice_url}}"
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": False,
            "is_active": True,
        },
        {
            "event_code": "subscription_expiring_7_days",
            "template_key": "system_subscription_expiring_7_days_ar",
            "template_name": "تنبيه قرب انتهاء الاشتراك",
            "language_code": "ar",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "مرحبًا {{company_name}}،\n"
                "نود إشعاركم بأن اشتراككم الحالي على وشك الانتهاء خلال 7 أيام.\n\n"
                "تفاصيل الاشترراك:\n"
                "- الباقة الحالية: {{plan_name}}\n"
                "- تاريخ الانتهاء: {{end_date}}\n\n"
                "يرجى التجديد قبل تاريخ الانتهاء لتجنب توقف الخدمة.\n\n"
                "رابط التجديد:\n"
                "{{renewal_url}}"
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": True,
            "is_active": True,
        },
        {
            "event_code": "subscription_expiring_7_days",
            "template_key": "system_subscription_expiring_7_days_en",
            "template_name": "Subscription Expiring in 7 Days",
            "language_code": "en",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "Hello {{company_name}},\n"
                "We would like to inform you that your current subscription will expire in 7 days.\n\n"
                "Subscription details:\n"
                "- Current Plan: {{plan_name}}\n"
                "- Expiry Date: {{end_date}}\n\n"
                "Please renew before the expiry date to avoid service interruption.\n\n"
                "Renewal URL:\n"
                "{{renewal_url}}"
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": False,
            "is_active": True,
        },
        {
            "event_code": "subscription_plan_changed",
            "template_key": "system_subscription_plan_changed_ar",
            "template_name": "تغيير الباقة",
            "language_code": "ar",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "مرحبًا {{{company_name}}،\n"
                "تم تحديث باقتكم بنجاح في Mham Cloud.\n\n"
                "تفاصيل التغيير:\n"
                "- الباقة السابقة: {{old_plan_name}}\n"
                "- الباقة الجديدة: {{new_plan_name}}\n"
                "- تاريخ التفعيل: {{effective_date}}\n\n"
                "يمكنكم مراجعة تفاصيل الاشتراك من خلال الرابط التالي:\n"
                "{{subscription_url}}"
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": True,
            "is_active": True,
        },
        {
            "event_code": "subscription_plan_changed",
            "template_key": "system_subscription_plan_changed_en",
            "template_name": "Subscription Plan Changed",
            "language_code": "en",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "Hello {{company_name}},\n"
                "Your subscription plan has been updated successfully in Mham Cloud.\n\n"
                "Change details:\n"
                "- Previous Plan: {{old_plan_name}}\n"
                "- New Plan: {{new_plan_name}}\n"
                "- Effective Date: {{effective_date}}\n\n"
                "You can review your subscription details using the following link:\n"
                "{{subscription_url}}"
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": False,
            "is_active": True,
        },
        {
            "event_code": "subscription_stopped",
            "template_key": "system_subscription_stopped_ar",
            "template_name": "إيقاف الاشتراك",
            "language_code": "ar",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "مرحبًا {{companyy_name}}،\n"
                "نود إشعاركم بأنه تم إيقاف اشتراككم الحالي في Mham Cloud.\n\n"
                "تفاصيل الحالة:\n"
                "- الباقة: {{plan_name}}\n"
                "- تاريخ الإيقاف: {{stopped_at}}\n"
                "- السبب: {{stop_reason}}\n\n"
                "لإعادة التفعيل أو مراجعة التفاصيل، يرجى استخدام الرابط التالي:\n"
                "{{reactivation_url}}"
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": True,
            "is_active": True,
        },
        {
            "event_code": "subscription_stopped",
            "template_key": "system_subscription_stopped_en",
            "template_name": "Subscription Stopped Notification",
            "language_code": "en",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "Hello {{company_name}},\n"
                "We would like to inform you that your current subscription in Mham Cloud has been stopped.\n\n"
                "Status details:\n"
                "- Plan: {{plan_name}}\n"
                "- Stopped At: {{stopped_at}}\n"
                "- Reason: {{stop_reason}}\n\n"
                "To reactivate or review the details, please use the following link:\n"
                "{{reactivation_url}}"
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": False,
            "is_active": True,
        },
        {
            "event_code": "system_user_created",
            "template_key": "system_user_created_ar",
            "template_name": "إنشاء مستخدم جديد",
            "language_code": "ar",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "مرحبًا {{full_name}}،\n"
                "nتم إنشاء حسابك بنجاح في Mham Cloud.\n\n"
                "بيانات الدخول:\n"
                "- اسم المستخدم: {{username}}\n"
                "- البريد الإلكتروني: {{email}}\n"
                "- كلمة المرور المؤقتة: {{temporary_password}}\n\n"
                "رابط الدخول:\n"
                "{{login_url}}\n\n"
                "ننصح بتغيير كلمة المرور فور تسجيل الدخول حفاظًا على أمان حسابك."
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": True,
            "is_active": True,
        },
        {
            "event_code": "system_user_created",
            "template_key": "system_user_created_en",
            "template_name": "User Created Welcome",
            "language_code": "en",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "Hello {{full_name}},\n"
                "Your account has been created successfully in Mham Cloud.\n\n"
                "Login details:\n"
                "- Username: {{username}}\n"
                "- Email: {{email}}\n"
                "- Temporary Password: {{temporary_password}}\n\n"
                "Login URL:\n"
                "{{login_url}}\n\n"
                "For your account security, we recommend changing your password immediately after logging in."
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": False,
            "is_active": True,
        },
        {
            "event_code": "system_user_password_changed",
            "template_key": "system_user_password_changed_ar",
            "template_name": "تغيير كلمة المرور",
            "language_code": "ar",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "مرحبًا {{full_name}}،\n"
                "تم تغيير كلمة المرور الخاصة بحسابك بنجاح.\n\n"
                "تفاصيل العملية:\n"
                "- وقت التغيير: {{changed_at}}\n\n"
                "إإذا لم تقم بهذا الإجراء، يرجى التواصل فورًا مع الدعم الفني أو مسؤول النظام.\n\n"
                "رابط الدخول:\n"
                "{{login_url}}"
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": True,
            "is_active": True,
        },
        {
            "event_code": "system_user_password_changed",
            "template_key": "system_user_password_changed_en",
            "template_name": "Password Changed Notification",
            "language_code": "en",
            "message_type": MessageType.TEXT,
            "header_text": "",
            "body_text": (
                "Hello {{full_name}},\n"
                "Your account password has been changed successfully.\n\n"
                "Change details:\n"
                "- Changed At: {{changed_at}}\n\n"
                "If you did not perform this action, please contact technical support or your system administrator immediately.\n\n"
                "Login URL:\n"
                "{{login_url}}"
            ),
            "footer_text": "",
            "button_text": "",
            "button_url": "",
            "meta_template_name": "",
            "meta_template_namespace": "",
            "approval_status": TemplateApprovalStatus.APPROVED,
            "provider_status": TemplateProviderSyncStatus.NOT_SYNCED,
            "rejection_reason": "",
            "is_default": False,
            "is_active": True,
        },
    ]


def _company_template_seed_rows() -> list[dict[str, Any]]:
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
                "مرحبًا {{company_name}}، تم إنشاء شركتكم بنجاح في Mham Cloud.\n"
                "تفاصيل الاشتراك:\n"
                "- الباقة: {{plan_name}}\n"
                "- تاريخ البداية: {{start_date}}\n"
                "- تاريخ النهاية: {{end_date}}\n"
                "يمكنكم تسجيل الدخول من خلال الرابط التالي:\n"
                "{{login_url}}\n"
                "يسعدنا خدمتكم ونتطلع لتجربة موفقة."
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "company_created",
            "language_code": "en",
            "template_name": "Company Created Welcome",
            "template_key": "company_created",
            "header_text": "",
            "body_text": (
                "Hello {{company_name}}, your company has been created successfully in Mham Cloud.\n"
                "Subscription details:\n"
                "- Plan: {{plan_name}}\n"
                "- Start Date: {{start_date}}\n"
                "- End Date: {{end_date}}\n"
                "You can log in using the following link:\n"
                "{{login_url}}\n"
                "We are pleased to serve you and wish you a great experience."
            ),
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "welcome_message",
            "language_code": "ar",
            "template_name": "رسالة ترحيبية",
            "template_key": "welcome_message",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، أهلاً بك في {{company_name}}.\n"
                "تم تجهيز حسابك على Mham Cloud.\n"
                "اسم المستخدم: {{username}}\n"
                "رابط الدخول: {{login_url}}"
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "welcome_message",
            "language_code": "en",
            "template_name": "Welcome Message",
            "template_key": "welcome_message",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, welcome to {{company_name}}.\n"
                "Your account on Mham Cloud is ready.\n"
                "Username: {{username}}\n"
                "Login URL: {{login_url}}"
            ),
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
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
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "attendance_present",
            "language_code": "ar",
            "template_name": "تسجيل حضور",
            "template_key": "attendance_present",
            "header_text": "",
            "body_text": (
                "تنبيه حضور:\n"
                "تم تسجيل حضور الموظف {{employee_name}} بتاريخ {{attendance_date}}.\n"
                "وقت الدخول: {{check_in}}\n"
                "وقت الخروج: {{check_out}}"
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "attendance_present",
            "language_code": "en",
            "template_name": "Attendance Present",
            "template_key": "attendance_present",
            "header_text": "",
            "body_text": (
                "Attendance Update:\n"
                "Employee {{employee_name}} was marked present on {{attendance_date}}.\n"
                "Check In: {{check_in}}\n"
                "Check Out: {{check_out}}"
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "attendance_check_in",
            "language_code": "ar",
            "template_name": "تسجيل دخول",
            "template_key": "attendance_check_in",
            "header_text": "",
            "body_text": (
                "تنبيه حركة حضور:\n"
                "قام الموظف {{employee_name}} بتسجيل الدخول بتاريخ {{attendance_date}}.\n"
                "وقت الدخول: {{check_in}}"
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "attendance_check_in",
            "language_code": "en",
            "template_name": "Attendance Check In",
            "template_key": "attendance_check_in",
            "header_text": "",
            "body_text": (
                "Attendance Movement:\n"
                "Employee {{employee_name}} checked in on {{attendance_date}}.\n"
                "Check In: {{check_in}}"
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "attendance_check_out",
            "language_code": "ar",
            "template_name": "تسجيل خروج",
            "template_key": "attendance_check_out",
            "header_text": "",
            "body_text": (
                "تنبيه حركة حضور:\n"
                "قام الموظف {{employee_name}} بتسجيل الخروج بتاريخ {{attendance_date}}.\n"
                "وقت الخروج: {{check_out}}"
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "attendance_check_out",
            "language_code": "en",
            "template_name": "Attendance Check Out",
            "template_key": "attendance_check_out",
            "header_text": "",
            "body_text": (
                "Attendance Movement:\n"
                "Employee {{employee_name}} checked out on {{attendance_date}}.\n"
                "Check Out: {{check_out}}"
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "payroll_paid",
            "language_code": "ar",
            "template_name": "صرف راتب",
            "template_key": "payroll_paid",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم صرف راتبك بنجاح.\n"
                "الدورة: {{payroll_period}}\n"
                "صافي الراتب: {{net_salary}}\n"
                "المبلغ المصروف: {{paid_amount}}\n"
                "طريقة الدفع: {{payment_method}}\n"
                "الحالة: {{payment_status}}"
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "payroll_paid",
            "language_code": "en",
            "template_name": "Payroll Paid",
            "template_key": "payroll_paid",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, your salary has been paid successfully.\n"
                "Period: {{payroll_period}}\n"
                "Net Salary: {{net_salary}}\n"
                "Paid Amount: {{paid_amount}}\n"
                "Payment Method: {{payment_method}}\n"
                "Status: {{payment_status}}"
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "employee_activated",
            "language_code": "ar",
            "template_name": "تفعيل موظف",
            "template_key": "employee_activated",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم تفعيل حالة الموظف {{employee_name}} بنجاح.\n"
                "الحالة الحالية: {{status}}"
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "employee_activated",
            "language_code": "en",
            "template_name": "Employee Activated",
            "template_key": "employee_activated",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, employee {{employee_name}} has been activated successfully.\n"
                "Current Status: {{status}}"
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "employee_deactivated",
            "language_code": "ar",
            "template_name": "تعطيل موظف",
            "template_key": "employee_deactivated",
            "header_text": "",
            "body_text": (
                "مرحبًا {{recipient_name}}، تم تعطيل حالة الموظف {{employee_name}}.\n"
                "الحالة الحالية: {{status}}"
            ),
            "footer_text": "Mham Cloud",
        },
        {
            "event_code": "employee_deactivated",
            "language_code": "en",
            "template_name": "Employee Deactivated",
            "template_key": "employee_deactivated",
            "header_text": "",
            "body_text": (
                "Hello {{recipient_name}}, employee {{employee_name}} has been deactivated.\n"
                "Current Status: {{status}}"
            ),
            "footer_text": "Mham Cloud",
        },
    ]


def _create_or_get_seed_template(
    *,
    scope_type: str,
    company=None,
    seed: dict[str, Any],
    user=None,
):
    item, created = WhatsAppTemplate.objects.get_or_create(
        scope_type=scope_type,
        company=company,
        event_code=seed["event_code"],
        language_code=seed["language_code"],
        version=1,
        defaults=_build_seed_defaults(seed),
    )

    if created and user and getattr(user, "is_authenticated", False):
        update_fields: list[str] = []

        if hasattr(item, "created_by"):
            item.created_by = user
            update_fields.append("created_by")

        if hasattr(item, "updated_by"):
            item.updated_by = user
            update_fields.append("updated_by")

        if update_fields:
            item.save(update_fields=update_fields)

    return item, created


# ============================================================
# 🖥 System Default Template Bootstrap
# ============================================================

@transaction.atomic
def ensure_system_default_whatsapp_templates(user=None) -> dict[str, Any]:
    """
    إنشاء القوالب الافتراضية الخاصة بالنظام عند عدم وجودها.
    - آمن ضد التكرار
    - لا يخلط مع قوالب الشركة
    - ينشئ النسخ العربية والإنجليزية
    """
    existing_system_count = WhatsAppTemplate.objects.filter(
        scope_type=ScopeType.SYSTEM,
        company__isnull=True,
    ).count()

    if existing_system_count > 0:
        return {
            "created": 0,
            "existing": existing_system_count,
            "total_system_templates": existing_system_count,
        }

    created_count = 0

    for seed in _system_template_seed_rows():
        _, created = _create_or_get_seed_template(
            scope_type=ScopeType.SYSTEM,
            company=None,
            seed=seed,
            user=user,
        )
        if created:
            created_count += 1

    total_system_templates = WhatsAppTemplate.objects.filter(
        scope_type=ScopeType.SYSTEM,
        company__isnull=True,
    ).count()

    return {
        "created": created_count,
        "existing": total_system_templates - created_count,
        "total_system_templates": total_system_templates,
    }


# ============================================================
# 🏢 Company Default Template Bootstrap
# ============================================================

@transaction.atomic
def ensure_company_default_whatsapp_templates(company, user=None) -> dict[str, Any]:
    """
    إنشاء القوالب الافتراضية الخاصة بالشركة.
    - آمن ضد التكرار
    - لا يخلط مع قوالب النظام
    - ينشئ النسخ العربية والإنجليزية
    - ✅ يضيف القوالب الناقصة فقط للشركات القديمة دون المساس بالقوالب الموجودة
    """
    if not company:
        return {
            "created": 0,
            "existing": 0,
            "total_company_templates": 0,
        }

    created_count = 0
    existing_count = 0

    for seed in _company_template_seed_rows():
        _, created = _create_or_get_seed_template(
            scope_type=ScopeType.COMPANY,
            company=company,
            seed=seed,
            user=user,
        )
        if created:
            created_count += 1
        else:
            existing_count += 1

    total_company_templates = WhatsAppTemplate.objects.filter(
        scope_type=ScopeType.COMPANY,
        company=company,
    ).count()

    return {
        "created": created_count,
        "existing": existing_count,
        "total_company_templates": total_company_templates,
    }


@transaction.atomic
def get_whatsapp_session_status(
    *,
    scope_type: str,
    company=None,
) -> dict[str, Any]:
    """
    جلب حالة الجلسة الحالية من الـ gateway ثم مزامنتها داخل config.
    وإذا كانت الجلسة متصلة يتم إعادة إرسال الرسائل الفاشلة تلقائيًا
    التي فشلت بسبب انقطاع الجلسة.
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

    retry_result = _auto_retry_failed_messages_after_reconnect(
        scope_type=scope_type,
        company=company,
        connected=bool(result.connected),
    )
    payload["retry_result"] = retry_result

    return payload


@transaction.atomic
def create_whatsapp_qr_session(
    *,
    scope_type: str,
    company=None,
) -> dict[str, Any]:
    """
    إنشاء QR جديد للجلسة.
    وإذا رجعت الجلسة متصلة يتم إعادة إرسال الرسائل الفاشلة تلقائيًا.
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

    retry_result = _auto_retry_failed_messages_after_reconnect(
        scope_type=scope_type,
        company=company,
        connected=bool(result.connected),
    )
    payload["retry_result"] = retry_result

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
    وإذا رجعت الجلسة متصلة يتم إعادة إرسال الرسائل الفاشلة تلقائيًا.
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

    retry_result = _auto_retry_failed_messages_after_reconnect(
        scope_type=scope_type,
        company=company,
        connected=bool(result.connected),
    )
    payload["retry_result"] = retry_result

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


# ============================================================
# 🔗 Notification Center Bridge — WhatsApp Channel
# ============================================================

def _infer_scope_type_from_company(company=None) -> str:
    return ScopeType.COMPANY if company is not None else ScopeType.SYSTEM


def _map_event_group_to_trigger_source(event_group: str | None) -> str:
    normalized = safe_text(event_group).lower()

    if normalized == "billing":
        return TriggerSource.BILLING
    if normalized in {"attendance", "biotime"}:
        return TriggerSource.ATTENDANCE
    if normalized == "leave":
        return TriggerSource.LEAVE
    if normalized == "payroll":
        return TriggerSource.PAYROLL
    if normalized in {"employee", "hr"}:
        return TriggerSource.EMPLOYEE
    if normalized == "company":
        return TriggerSource.COMPANY
    if normalized == "broadcast":
        return TriggerSource.BROADCAST

    return TriggerSource.SYSTEM


def _build_notification_center_context(
    *,
    event=None,
    delivery=None,
    recipient_name: str = "",
    base_context: dict | None = None,
) -> dict[str, Any]:
    context: dict[str, Any] = {}

    if isinstance(base_context, dict):
        context.update(base_context)

    if event:
        event_context = getattr(event, "context", {}) or {}
        if isinstance(event_context, dict):
            context.update(event_context)

        if not context.get("message"):
            context["message"] = safe_text(getattr(event, "message", ""))

        if not context.get("recipient_name"):
            context["recipient_name"] = recipient_name or safe_text(
                getattr(getattr(event, "target_user", None), "get_full_name", lambda: "")()
            ) or safe_text(getattr(getattr(event, "target_user", None), "username", ""))

        company = getattr(event, "company", None)
        if company and not context.get("company_name"):
            context["company_name"] = safe_text(getattr(company, "name", ""))

        if not context.get("event_code"):
            context["event_code"] = safe_text(getattr(event, "event_code", ""))

        if not context.get("title"):
            context["title"] = safe_text(getattr(event, "title", ""))

        if not context.get("link"):
            context["link"] = safe_text(getattr(event, "link", ""))

    if delivery:
        if not context.get("delivery_id"):
            context["delivery_id"] = getattr(delivery, "id", None)

        if not context.get("subject"):
            context["subject"] = safe_text(getattr(delivery, "subject", ""))

        if not context.get("message"):
            context["message"] = safe_text(getattr(delivery, "rendered_message", ""))

    if recipient_name and not context.get("recipient_name"):
        context["recipient_name"] = recipient_name

    context = _inject_employee_status_context_if_missing(
        event=event,
        context=context,
    )

    if not context.get("employee_name") or context.get("employee_name") == "{{employee_name}}":
        context["employee_name"] = (
            safe_text(context.get("employee_name_ar"))
            or safe_text(context.get("employee_arabic_name"))
            or safe_text(context.get("recipient_name"))
            or safe_text(context.get("employee_name"))
        )

    if not context.get("employee_name_ar"):
        context["employee_name_ar"] = safe_text(context.get("employee_name"))

    if not context.get("employee_arabic_name"):
        context["employee_arabic_name"] = safe_text(context.get("employee_name"))

    return context


@transaction.atomic
def send_notification_center_whatsapp_delivery(
    *,
    delivery,
    recipient_phone: str,
    recipient_name: str = "",
    recipient_role: str = "user",
    company=None,
    language_code: str = "ar",
    context: dict | None = None,
    attachment_url: str = "",
    attachment_name: str = "",
    mime_type: str = "",
):
    """
    جسر رسمي بين Notification Center و WhatsApp Center.

    المتوقع:
    - delivery = NotificationDelivery من notification_center
    - event = delivery.event
    - تحديث delivery بناءً على نتيجة الإرسال
    - إنشاء WhatsAppMessageLog كـ audit فعلي داخل whatsapp_center
    """
    if not delivery:
        return None

    event = getattr(delivery, "event", None)
    resolved_company = company or getattr(delivery, "company", None) or getattr(event, "company", None)
    resolved_language = safe_text(language_code) or safe_text(getattr(delivery, "language_code", "")) or "ar"
    resolved_event_code = safe_text(getattr(event, "event_code", "")) or "system_notification"
    resolved_event_group = safe_text(getattr(event, "event_group", "")) or "system"
    resolved_scope_type = _infer_scope_type_from_company(resolved_company)
    resolved_trigger_source = _map_event_group_to_trigger_source(resolved_event_group)

    final_context = _build_notification_center_context(
        event=event,
        delivery=delivery,
        recipient_name=recipient_name,
        base_context=context,
    )

    normalized_phone = normalize_phone_number(recipient_phone)
    if not normalized_phone:
        try:
            delivery.mark_attempt()
            delivery.mark_failed(
                error_message="Invalid or missing WhatsApp recipient phone",
                provider_response={
                    "channel": "whatsapp",
                    "reason": "INVALID_PHONE",
                },
            )
        except Exception:
            logger.exception(
                "Failed to update NotificationDelivery as failed بسبب رقم واتساب غير صالح | delivery_id=%s",
                getattr(delivery, "id", None),
            )
        return None

    try:
        delivery.mark_attempt()
    except Exception:
        logger.exception(
            "Failed to mark attempt on NotificationDelivery | delivery_id=%s",
            getattr(delivery, "id", None),
        )

    log = send_event_whatsapp_message(
        scope_type=resolved_scope_type,
        event_code=resolved_event_code,
        recipient_phone=normalized_phone,
        recipient_name=recipient_name or safe_text(final_context.get("recipient_name")),
        recipient_role=recipient_role,
        trigger_source=resolved_trigger_source,
        company=resolved_company,
        language_code=resolved_language,
        context=final_context,
        related_model=safe_text(getattr(event, "target_model", "")) or "notification_event",
        related_object_id=safe_text(getattr(event, "target_object_id", "")) or safe_text(getattr(event, "id", "")),
        attachment_url=attachment_url,
        attachment_name=attachment_name,
        mime_type=mime_type,
    )

    if not log:
        try:
            delivery.mark_failed(
                error_message="WhatsApp log was not created",
                provider_response={
                    "channel": "whatsapp",
                    "reason": "LOG_NOT_CREATED",
                },
            )
        except Exception:
            logger.exception(
                "Failed to update NotificationDelivery after WhatsApp log missing | delivery_id=%s",
                getattr(delivery, "id", None),
            )
        return None

    provider_response = {
        "channel": "whatsapp",
        "scope_type": resolved_scope_type,
        "event_code": resolved_event_code,
        "trigger_source": resolved_trigger_source,
        "log_id": getattr(log, "id", None),
        "provider_status": safe_text(getattr(log, "provider_status", "")),
        "delivery_status": safe_text(getattr(log, "delivery_status", "")),
        "external_message_id": safe_text(getattr(log, "external_message_id", "")),
        "response_json": getattr(log, "response_json", {}) or {},
        "failure_reason": safe_text(getattr(log, "failure_reason", "")),
    }

    if getattr(log, "delivery_status", "") == DeliveryStatus.SENT:
        try:
            delivery.mark_sent(
                provider_message_id=safe_text(getattr(log, "external_message_id", "")) or str(getattr(log, "id", "")),
                provider_response=provider_response,
            )
        except Exception:
            logger.exception(
                "Failed to mark NotificationDelivery as sent | delivery_id=%s | log_id=%s",
                getattr(delivery, "id", None),
                getattr(log, "id", None),
            )
    else:
        try:
            delivery.mark_failed(
                error_message=safe_text(getattr(log, "failure_reason", "")) or "WHATSAPP_SEND_FAILED",
                provider_response=provider_response,
            )
        except Exception:
            logger.exception(
                "Failed to mark NotificationDelivery as failed | delivery_id=%s | log_id=%s",
                getattr(delivery, "id", None),
                getattr(log, "id", None),
            )

    return log