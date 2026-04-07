# 📂 الملف: notification_center/services_hr.py
# 🧠 HR Notification Engine — Mham Cloud V3.3
# 🚀 إشعارات الموارد البشرية الرسمية
# ------------------------------------------------------------
# ✅ موظفين
# ✅ عقود
# ✅ إجازات
# ✅ حضور
# ✅ رواتب
# ✅ حالة الموظف
# ✅ نهاية خدمة
# ✅ متوافق مع NotificationEvent + NotificationDelivery
# ✅ يدعم In-App + Email + WhatsApp من الطبقة الخدمية
# ✅ يدعم actor + extra_context
# ✅ تم تنظيفه ليتوافق مع employee.py و leaves.py
# ✅ يدعم استخراج المدير المباشر/المشرف بشكل مرن لإشعارات الحضور
# ------------------------------------------------------------

from __future__ import annotations

from typing import Iterable

from django.contrib.auth import get_user_model

from notification_center.services import create_notification
from employee_center.models import Employee, Contract
from leave_center.models import LeaveRequest

User = get_user_model()


# =============================================================
# 🧩 Helpers
# =============================================================
def _clean(value) -> str:
    return str(value).strip() if value is not None else ""


def _safe_getattr(obj, attr_name: str, default=None):
    try:
        return getattr(obj, attr_name, default)
    except Exception:
        return default


def _merge_context(base: dict | None = None, extra: dict | None = None) -> dict:
    payload = dict(base or {})
    if isinstance(extra, dict):
        payload.update(extra)
    return payload


def _employee_name(employee: Employee) -> str:
    return (
        _clean(_safe_getattr(employee, "full_name", ""))
        or _clean(_safe_getattr(employee, "name", ""))
        or f"Employee #{_safe_getattr(employee, 'id', '')}"
    )


def _employee_company(employee: Employee):
    return _safe_getattr(employee, "company", None)


def _employee_user(employee: Employee):
    return _safe_getattr(employee, "user", None)


def _employee_manager_users(employee: Employee) -> list:
    """
    محاولة مرنة لاستخراج المدير المباشر/المشرف من أكثر من اسم محتمل
    بدون كسر أي بنية حالية.
    """
    manager_candidates = [
        _safe_getattr(employee, "direct_manager", None),
        _safe_getattr(employee, "manager", None),
        _safe_getattr(employee, "line_manager", None),
        _safe_getattr(employee, "reporting_manager", None),
        _safe_getattr(employee, "supervisor", None),
        _safe_getattr(employee, "manager_user", None),
        _safe_getattr(employee, "direct_manager_user", None),
        _safe_getattr(employee, "supervisor_user", None),
    ]

    resolved_users = []
    seen_ids = set()

    for candidate in manager_candidates:
        if not candidate:
            continue

        # لو كان المرشح نفسه User
        candidate_id = _safe_getattr(candidate, "id", None)
        candidate_username = _safe_getattr(candidate, "username", None)

        if candidate_id and candidate_username:
            if candidate_id not in seen_ids:
                resolved_users.append(candidate)
                seen_ids.add(candidate_id)
            continue

        # لو كان المرشح Employee ونحتاج user المرتبط به
        candidate_user = _safe_getattr(candidate, "user", None)
        candidate_user_id = _safe_getattr(candidate_user, "id", None)
        if candidate_user and candidate_user_id and candidate_user_id not in seen_ids:
            resolved_users.append(candidate_user)
            seen_ids.add(candidate_user_id)

    return resolved_users


def _attendance_manager_recipients(employee: Employee, company=None) -> list:
    """
    نجمع:
    - المدير المباشر إن وجد
    - المدراء الإداريين الحاليين كما هو السلوك القديم
    """
    recipients = []
    seen_ids = set()

    for user in _employee_manager_users(employee):
        user_id = _safe_getattr(user, "id", None)
        if user_id and user_id not in seen_ids:
            recipients.append(user)
            seen_ids.add(user_id)

    for user in _get_staff_users_for_company(company):
        user_id = _safe_getattr(user, "id", None)
        if user_id and user_id not in seen_ids:
            recipients.append(user)
            seen_ids.add(user_id)

    return recipients


def _employee_link(employee: Employee) -> str:
    company = _employee_company(employee)
    company_id = _safe_getattr(company, "id", "")
    employee_id = _safe_getattr(employee, "id", "")
    return f"/employee-center/{company_id}/employee/{employee_id}/"


def _contract_link(contract: Contract) -> str:
    employee = _safe_getattr(contract, "employee", None)
    company = _safe_getattr(employee, "company", None)
    company_id = _safe_getattr(company, "id", "")
    contract_id = _safe_getattr(contract, "id", "")
    return f"/employee-center/{company_id}/contract/{contract_id}/"


def _leave_link(leave: LeaveRequest) -> str:
    employee = _safe_getattr(leave, "employee", None)
    company = _safe_getattr(employee, "company", None)
    company_id = _safe_getattr(company, "id", "")
    leave_id = _safe_getattr(leave, "id", "")
    return f"/leave-center/{company_id}/requests/{leave_id}/"


def _attendance_link(attendance_record) -> str:
    employee = _safe_getattr(attendance_record, "employee", None)
    company = _safe_getattr(employee, "company", None)
    company_id = _safe_getattr(company, "id", "")
    record_id = _safe_getattr(attendance_record, "id", "")
    return f"/attendance-center/{company_id}/records/{record_id}/"


def _payroll_record_link(payroll_record) -> str:
    employee = _safe_getattr(payroll_record, "employee", None)
    company = _safe_getattr(employee, "company", None)
    company_id = _safe_getattr(company, "id", "")
    record_id = _safe_getattr(payroll_record, "id", "")
    return f"/payroll-center/{company_id}/records/{record_id}/"


def _payroll_run_link(payroll_run) -> str:
    company = _safe_getattr(payroll_run, "company", None)
    company_id = _safe_getattr(company, "id", "")
    run_id = _safe_getattr(payroll_run, "id", "")
    return f"/payroll-center/{company_id}/runs/{run_id}/"


def _get_staff_users_for_company(company=None):
    """
    جلب المستخدمين الإداريين بشكل مرن.
    حاليًا يبقي السلوك السابق كما هو: is_staff=True
    ويمكن لاحقًا تخصيصه على مستوى الشركة عند الحاجة.
    """
    return User.objects.filter(is_staff=True)


def _notify_user(
    *,
    recipient,
    title: str,
    message: str,
    notification_type: str,
    severity: str = "info",
    link: str | None = None,
    send_email: bool = False,
    send_whatsapp: bool = False,
    company=None,
    event_code: str | None = None,
    event_group: str = "hr",
    source: str = "services_hr",
    context: dict | None = None,
    target_object=None,
    actor=None,
):
    if not recipient or not _safe_getattr(recipient, "id", None):
        return None

    return create_notification(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        severity=severity,
        link=link,
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        company=company,
        event_code=event_code or notification_type,
        event_group=event_group,
        source=source,
        context=context or {},
        target_object=target_object,
        target_user=recipient,
        actor=actor,
    )


def _notify_users(
    *,
    recipients: Iterable,
    title: str,
    message: str,
    notification_type: str,
    severity: str = "info",
    link: str | None = None,
    send_email: bool = False,
    send_whatsapp: bool = False,
    company=None,
    event_code: str | None = None,
    event_group: str = "hr",
    source: str = "services_hr",
    context: dict | None = None,
    target_object=None,
    actor=None,
):
    seen_user_ids: set[int] = set()

    for recipient in recipients:
        if not recipient:
            continue

        user_id = _safe_getattr(recipient, "id", None)
        if not user_id or user_id in seen_user_ids:
            continue

        seen_user_ids.add(user_id)

        _notify_user(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            severity=severity,
            link=link,
            send_email=send_email,
            send_whatsapp=send_whatsapp,
            company=company,
            event_code=event_code,
            event_group=event_group,
            source=source,
            context=context,
            target_object=target_object,
            actor=actor,
        )


# =============================================================
# 👤 1) إشعار عند إضافة موظف جديد
# =============================================================
def notify_employee_created(
    employee: Employee,
    send_email: bool = False,
    send_whatsapp: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    """
    يرسل إشعارًا عن إضافة موظف جديد.
    - للمدراء
    - وللموظف نفسه إذا كان له user
    """
    company = _employee_company(employee)
    managers = _get_staff_users_for_company(company)
    employee_user = _employee_user(employee)

    shared_context = _merge_context(
        {
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": _employee_name(employee),
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    if employee_user:
        _notify_user(
            recipient=employee_user,
            title="👤 تم إنشاء ملفك الوظيفي",
            message=f"تم إنشاء ملفك الوظيفي بنجاح باسم {_employee_name(employee)}.",
            notification_type="hr_employee",
            severity="success",
            link=_employee_link(employee),
            send_email=send_email,
            send_whatsapp=send_whatsapp,
            company=company,
            event_code="employee_created",
            event_group="hr",
            source="services_hr.notify_employee_created.employee",
            context=shared_context,
            target_object=employee,
            actor=actor,
        )

    _notify_users(
        recipients=managers,
        title="👤 موظف جديد",
        message=f"تم إضافة الموظف {_employee_name(employee)} إلى الشركة.",
        notification_type="hr_employee",
        severity="success",
        link=_employee_link(employee),
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        company=company,
        event_code="employee_created",
        event_group="hr",
        source="services_hr.notify_employee_created.managers",
        context=shared_context,
        target_object=employee,
        actor=actor,
    )


# =============================================================
# 📝 2) إشعار تحديث بيانات الموظف
# =============================================================
def notify_employee_updated(
    employee: Employee,
    send_email: bool = False,
    send_whatsapp: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    company = _employee_company(employee)
    managers = _get_staff_users_for_company(company)

    shared_context = _merge_context(
        {
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": _employee_name(employee),
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    _notify_users(
        recipients=managers,
        title="📝 تحديث بيانات موظف",
        message=f"تم تحديث بيانات الموظف {_employee_name(employee)}.",
        notification_type="hr_employee",
        severity="info",
        link=_employee_link(employee),
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        company=company,
        event_code="employee_updated",
        event_group="hr",
        source="services_hr.notify_employee_updated",
        context=shared_context,
        target_object=employee,
        actor=actor,
    )


# =============================================================
# 📄 3) إشعار عند إنشاء عقد
# =============================================================
def notify_contract_created(
    contract: Contract,
    send_email: bool = False,
    send_whatsapp: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    employee = _safe_getattr(contract, "employee", None)
    company = _employee_company(employee)
    managers = _get_staff_users_for_company(company)

    shared_context = _merge_context(
        {
            "contract_id": _safe_getattr(contract, "id", None),
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": _employee_name(employee),
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    _notify_users(
        recipients=managers,
        title="📄 عقد جديد",
        message=f"تم إنشاء عقد جديد للموظف {_employee_name(employee)}.",
        notification_type="hr_contract",
        severity="success",
        link=_contract_link(contract),
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        company=company,
        event_code="contract_created",
        event_group="hr",
        source="services_hr.notify_contract_created",
        context=shared_context,
        target_object=contract,
        actor=actor,
    )


# =============================================================
# ⚠️ 4) إشعار انتهاء عقد
# =============================================================
def notify_contract_expiring(
    contract: Contract,
    send_email: bool = False,
    send_whatsapp: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    employee = _safe_getattr(contract, "employee", None)
    company = _employee_company(employee)
    managers = _get_staff_users_for_company(company)
    end_date = _safe_getattr(contract, "end_date", "")

    shared_context = _merge_context(
        {
            "contract_id": _safe_getattr(contract, "id", None),
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": _employee_name(employee),
            "end_date": _clean(end_date),
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    _notify_users(
        recipients=managers,
        title="⚠️ عقد على وشك الانتهاء",
        message=f"عقد الموظف {_employee_name(employee)} ينتهي بتاريخ {end_date}.",
        notification_type="hr_contract",
        severity="warning",
        link=_contract_link(contract),
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        company=company,
        event_code="contract_expiring",
        event_group="hr",
        source="services_hr.notify_contract_expiring",
        context=shared_context,
        target_object=contract,
        actor=actor,
    )


# =============================================================
# 📁 5) إشعار عند رفع مستند للموظف
# =============================================================
def notify_document_uploaded(
    employee: Employee,
    document_name: str,
    send_email: bool = False,
    send_whatsapp: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    company = _employee_company(employee)
    managers = _get_staff_users_for_company(company)

    shared_context = _merge_context(
        {
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": _employee_name(employee),
            "document_name": _clean(document_name),
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    _notify_users(
        recipients=managers,
        title="📁 مستند جديد",
        message=f"تم رفع مستند ({document_name}) للموظف {_employee_name(employee)}.",
        notification_type="hr_document",
        severity="info",
        link=f"{_employee_link(employee)}documents/",
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        company=company,
        event_code="employee_document_uploaded",
        event_group="hr",
        source="services_hr.notify_document_uploaded",
        context=shared_context,
        target_object=employee,
        actor=actor,
    )


# =============================================================
# 🏖 6) إشعار طلب إجازة جديد
# =============================================================
def notify_leave_requested(
    leave: LeaveRequest,
    send_email: bool = False,
    send_whatsapp: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    employee = _safe_getattr(leave, "employee", None)
    company = _employee_company(employee)
    approvers = _get_staff_users_for_company(company)
    leave_type_name = _safe_getattr(_safe_getattr(leave, "leave_type", None), "name", "")

    shared_context = _merge_context(
        {
            "leave_id": _safe_getattr(leave, "id", None),
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": _employee_name(employee),
            "leave_type_name": _clean(leave_type_name),
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    _notify_users(
        recipients=approvers,
        title="🏖 طلب إجازة جديد",
        message=f"قام {_employee_name(employee)} بتقديم طلب إجازة ({leave_type_name}).",
        notification_type="hr_leave",
        severity="info",
        link=_leave_link(leave),
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        company=company,
        event_code="leave_requested",
        event_group="hr",
        source="services_hr.notify_leave_requested",
        context=shared_context,
        target_object=leave,
        actor=actor,
    )


# =============================================================
# ✅ 7) إشعار الموافقة على الإجازة
# =============================================================
def notify_leave_approved(
    leave: LeaveRequest,
    send_email: bool = True,
    send_whatsapp: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    employee = _safe_getattr(leave, "employee", None)
    company = _employee_company(employee)
    employee_user = _employee_user(employee)
    leave_type_name = _safe_getattr(_safe_getattr(leave, "leave_type", None), "name", "")

    if not employee_user:
        return None

    shared_context = _merge_context(
        {
            "leave_id": _safe_getattr(leave, "id", None),
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": _employee_name(employee),
            "leave_type_name": _clean(leave_type_name),
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    return _notify_user(
        recipient=employee_user,
        title="✅ تم قبول طلب الإجازة",
        message=f"تمت الموافقة على الإجازة ({leave_type_name}).",
        notification_type="hr_leave",
        severity="success",
        link=_leave_link(leave),
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        company=company,
        event_code="leave_approved",
        event_group="hr",
        source="services_hr.notify_leave_approved",
        context=shared_context,
        target_object=leave,
        actor=actor,
    )


# =============================================================
# ❌ 8) إشعار رفض الإجازة
# =============================================================
def notify_leave_rejected(
    leave: LeaveRequest,
    send_email: bool = True,
    send_whatsapp: bool = False,
    actor=None,
    rejection_reason: str | None = None,
    extra_context: dict | None = None,
):
    employee = _safe_getattr(leave, "employee", None)
    company = _employee_company(employee)
    employee_user = _employee_user(employee)
    leave_type_name = _safe_getattr(_safe_getattr(leave, "leave_type", None), "name", "")

    if not employee_user:
        return None

    clean_reason = (
        _clean(rejection_reason)
        or _clean(_safe_getattr(leave, "reason", ""))
        or ""
    )

    message = f"تم رفض الإجازة ({leave_type_name})."
    if clean_reason:
        message = f"{message}\nسبب الرفض: {clean_reason}"

    shared_context = _merge_context(
        {
            "leave_id": _safe_getattr(leave, "id", None),
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": _employee_name(employee),
            "leave_type_name": _clean(leave_type_name),
            "rejection_reason": clean_reason,
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    return _notify_user(
        recipient=employee_user,
        title="❌ تم رفض طلب الإجازة",
        message=message,
        notification_type="hr_leave",
        severity="error",
        link=_leave_link(leave),
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        company=company,
        event_code="leave_rejected",
        event_group="hr",
        source="services_hr.notify_leave_rejected",
        context=shared_context,
        target_object=leave,
        actor=actor,
    )


# =============================================================
# 🛑 9) إشعار إنهاء خدمة موظف
# =============================================================
def notify_employee_terminated(
    employee: Employee,
    send_email: bool = False,
    send_whatsapp: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    company = _employee_company(employee)
    managers = _get_staff_users_for_company(company)

    shared_context = _merge_context(
        {
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": _employee_name(employee),
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    _notify_users(
        recipients=managers,
        title="🛑 إنهاء خدمة",
        message=f"تم إنهاء خدمة الموظف {_employee_name(employee)}.",
        notification_type="hr_termination",
        severity="error",
        link=_employee_link(employee),
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        company=company,
        event_code="employee_terminated",
        event_group="hr",
        source="services_hr.notify_employee_terminated",
        context=shared_context,
        target_object=employee,
        actor=actor,
    )


# =============================================================
# 💰 10) إشعار إنشاء مكافأة نهاية الخدمة
# =============================================================
def notify_eosb_created(
    employee: Employee,
    amount: float,
    send_email: bool = False,
    send_whatsapp: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    company = _employee_company(employee)
    managers = _get_staff_users_for_company(company)

    shared_context = _merge_context(
        {
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": _employee_name(employee),
            "amount": amount,
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    _notify_users(
        recipients=managers,
        title="💰 مكافأة نهاية خدمة",
        message=f"تم احتساب مكافأة نهاية الخدمة للموظف {_employee_name(employee)} بمبلغ {amount} ريال.",
        notification_type="hr_eosb",
        severity="success",
        link=_employee_link(employee),
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        company=company,
        event_code="eosb_created",
        event_group="hr",
        source="services_hr.notify_eosb_created",
        context=shared_context,
        target_object=employee,
        actor=actor,
    )


# =============================================================
# 🕒 11) إشعارات الحضور
# =============================================================
def notify_attendance_event(
    attendance_record,
    *,
    action: str | None = None,
    send_email_to_employee: bool = True,
    send_email_to_managers: bool = False,
    send_whatsapp_to_employee: bool = False,
    send_whatsapp_to_managers: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    """
    يدعم:
    - absent
    - late
    - present
    - check_in
    - check_out
    """
    employee = _safe_getattr(attendance_record, "employee", None)
    if not employee:
        return None

    company = _employee_company(employee)
    employee_user = _employee_user(employee)
    managers = _attendance_manager_recipients(employee, company)

    employee_name = _employee_name(employee)
    attendance_date = _safe_getattr(attendance_record, "date", "")
    check_in = _safe_getattr(attendance_record, "check_in", "")
    check_out = _safe_getattr(attendance_record, "check_out", "")
    late_minutes = int(_safe_getattr(attendance_record, "late_minutes", 0) or 0)
    status_value = _clean(_safe_getattr(attendance_record, "status", "")).lower()
    normalized_action = _clean(action).lower()

    event_code = "attendance_event"

    if normalized_action == "check_in":
        title = "🟢 تسجيل دخول"
        employee_message = f"تم تسجيل دخولك بتاريخ {attendance_date}. وقت الدخول: {check_in}."
        manager_message = f"قام الموظف {employee_name} بتسجيل الدخول بتاريخ {attendance_date}. وقت الدخول: {check_in}."
        severity = "info"
        event_code = "attendance_check_in"
    elif normalized_action == "check_out":
        title = "🔵 تسجيل خروج"
        employee_message = f"تم تسجيل خروجك بتاريخ {attendance_date}. وقت الخروج: {check_out}."
        manager_message = f"قام الموظف {employee_name} بتسجيل الخروج بتاريخ {attendance_date}. وقت الخروج: {check_out}."
        severity = "info"
        event_code = "attendance_check_out"
    elif normalized_action == "present" or status_value == "present":
        title = "✅ تسجيل حضور"
        employee_message = (
            f"تم تسجيل حضورك بتاريخ {attendance_date}. "
            f"وقت الدخول: {check_in} | وقت الخروج: {check_out}."
        )
        manager_message = (
            f"تم تسجيل الموظف {employee_name} كحاضر بتاريخ {attendance_date}. "
            f"وقت الدخول: {check_in} | وقت الخروج: {check_out}."
        )
        severity = "success"
        event_code = "attendance_present"
    elif status_value == "late":
        title = "⏰ تنبيه تأخير"
        employee_message = f"تم تسجيلك كمتأخر بتاريخ {attendance_date} لمدة {late_minutes} دقيقة."
        manager_message = f"تم تسجيل الموظف {employee_name} كمتأخر بتاريخ {attendance_date} لمدة {late_minutes} دقيقة."
        severity = "warning"
        event_code = "attendance_late"
    elif status_value == "absent":
        title = "🚨 تنبيه غياب"
        employee_message = f"تم تسجيلك كغائب بتاريخ {attendance_date}."
        manager_message = f"تم تسجيل الموظف {employee_name} كغائب بتاريخ {attendance_date}."
        severity = "error"
        event_code = "attendance_absent"
    else:
        return None

    shared_context = _merge_context(
        {
            "attendance_record_id": _safe_getattr(attendance_record, "id", None),
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": employee_name,
            "attendance_date": _clean(attendance_date),
            "check_in": _clean(check_in),
            "check_out": _clean(check_out),
            "late_minutes": late_minutes,
            "status": status_value,
            "action": normalized_action,
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    if employee_user:
        _notify_user(
            recipient=employee_user,
            title=title,
            message=employee_message,
            notification_type="hr_attendance",
            severity=severity,
            link=_attendance_link(attendance_record),
            send_email=send_email_to_employee,
            send_whatsapp=send_whatsapp_to_employee,
            company=company,
            event_code=event_code,
            event_group="hr",
            source="services_hr.notify_attendance_event.employee",
            context=shared_context,
            target_object=attendance_record,
            actor=actor,
        )

    _notify_users(
        recipients=managers,
        title=title,
        message=manager_message,
        notification_type="hr_attendance",
        severity=severity,
        link=_attendance_link(attendance_record),
        send_email=send_email_to_managers,
        send_whatsapp=send_whatsapp_to_managers,
        company=company,
        event_code=event_code,
        event_group="hr",
        source="services_hr.notify_attendance_event.managers",
        context=shared_context,
        target_object=attendance_record,
        actor=actor,
    )


# =============================================================
# 💵 12) إشعار صرف راتب سجل مفرد
# =============================================================
def notify_payroll_record_paid(
    payroll_record,
    *,
    send_email_to_employee: bool = True,
    send_email_to_managers: bool = False,
    send_whatsapp_to_employee: bool = True,
    send_whatsapp_to_managers: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    employee = _safe_getattr(payroll_record, "employee", None)
    if not employee:
        return None

    company = _employee_company(employee)
    employee_user = _employee_user(employee)
    managers = _get_staff_users_for_company(company)

    employee_name = _employee_name(employee)
    paid_amount = _safe_getattr(payroll_record, "paid_amount", 0) or 0
    net_salary = _safe_getattr(payroll_record, "net_salary", 0) or 0
    payment_method = _safe_getattr(payroll_record, "payment_method", "")
    payment_status = _safe_getattr(payroll_record, "status", "")
    paid_at = _safe_getattr(payroll_record, "paid_at", "")

    run = _safe_getattr(payroll_record, "run", None)
    month_value = _safe_getattr(run, "month", None) or _safe_getattr(payroll_record, "month", "")
    payroll_period = _clean(month_value)

    title = "💰 تم صرف الراتب"
    employee_message = (
        f"تم صرف راتبك بنجاح.\n"
        f"الدورة: {payroll_period}\n"
        f"صافي الراتب: {net_salary}\n"
        f"المبلغ المصروف: {paid_amount}\n"
        f"طريقة الدفع: {payment_method}\n"
        f"الحالة: {payment_status}\n"
        f"تاريخ الصرف: {paid_at}"
    )
    manager_message = (
        f"تم صرف راتب الموظف {employee_name} بنجاح.\n"
        f"الدورة: {payroll_period}\n"
        f"صافي الراتب: {net_salary}\n"
        f"المبلغ المصروف: {paid_amount}\n"
        f"طريقة الدفع: {payment_method}\n"
        f"الحالة: {payment_status}\n"
        f"تاريخ الصرف: {paid_at}"
    )

    shared_context = _merge_context(
        {
            "payroll_record_id": _safe_getattr(payroll_record, "id", None),
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": employee_name,
            "paid_amount": paid_amount,
            "net_salary": net_salary,
            "payment_method": _clean(payment_method),
            "payment_status": _clean(payment_status),
            "paid_at": _clean(paid_at),
            "payroll_period": payroll_period,
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    if employee_user:
        _notify_user(
            recipient=employee_user,
            title=title,
            message=employee_message,
            notification_type="hr_payroll",
            severity="success",
            link=_payroll_record_link(payroll_record),
            send_email=send_email_to_employee,
            send_whatsapp=send_whatsapp_to_employee,
            company=company,
            event_code="payroll_record_paid",
            event_group="hr",
            source="services_hr.notify_payroll_record_paid.employee",
            context=shared_context,
            target_object=payroll_record,
            actor=actor,
        )

    _notify_users(
        recipients=managers,
        title=title,
        message=manager_message,
        notification_type="hr_payroll",
        severity="success",
        link=_payroll_record_link(payroll_record),
        send_email=send_email_to_managers,
        send_whatsapp=send_whatsapp_to_managers,
        company=company,
        event_code="payroll_record_paid",
        event_group="hr",
        source="services_hr.notify_payroll_record_paid.managers",
        context=shared_context,
        target_object=payroll_record,
        actor=actor,
    )


# =============================================================
# 🧾 13) إشعار صرف Payroll Run كامل
# =============================================================
def notify_payroll_run_paid(
    payroll_run,
    *,
    send_email_to_managers: bool = True,
    send_whatsapp_to_managers: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    company = _safe_getattr(payroll_run, "company", None)
    managers = _get_staff_users_for_company(company)

    month_value = _safe_getattr(payroll_run, "month", "")
    period = _clean(month_value)
    pay_date = _safe_getattr(payroll_run, "pay_date", "")
    status_value = _safe_getattr(payroll_run, "status", "")

    title = "🧾 تم صرف Payroll Run"
    message = (
        f"تم صرف مسير رواتب كامل بنجاح.\n"
        f"الدورة: {period}\n"
        f"تاريخ الصرف: {pay_date}\n"
        f"الحالة: {status_value}"
    )

    shared_context = _merge_context(
        {
            "payroll_run_id": _safe_getattr(payroll_run, "id", None),
            "payroll_period": period,
            "pay_date": _clean(pay_date),
            "status": _clean(status_value),
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    _notify_users(
        recipients=managers,
        title=title,
        message=message,
        notification_type="hr_payroll_run",
        severity="success",
        link=_payroll_run_link(payroll_run),
        send_email=send_email_to_managers,
        send_whatsapp=send_whatsapp_to_managers,
        company=company,
        event_code="payroll_run_paid",
        event_group="hr",
        source="services_hr.notify_payroll_run_paid",
        context=shared_context,
        target_object=payroll_run,
        actor=actor,
    )


# =============================================================
# 🔐 14) إشعارات حالة الموظف
# =============================================================
def notify_employee_status_changed(
    employee: Employee,
    *,
    is_active: bool,
    send_email_to_employee: bool = True,
    send_email_to_managers: bool = False,
    send_whatsapp_to_employee: bool = False,
    send_whatsapp_to_managers: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    company = _employee_company(employee)
    employee_user = _employee_user(employee)
    managers = _get_staff_users_for_company(company)
    employee_name = _employee_name(employee)

    if is_active:
        title = "🟢 تم تفعيل الموظف"
        employee_message = "تم تفعيل حالتك الوظيفية بنجاح."
        manager_message = f"تم تفعيل الموظف {employee_name} بنجاح."
        severity = "success"
        event_code = "employee_activated"
    else:
        title = "🔴 تم تعطيل الموظف"
        employee_message = "تم تعطيل حالتك الوظيفية."
        manager_message = f"تم تعطيل الموظف {employee_name}."
        severity = "warning"
        event_code = "employee_deactivated"

    shared_context = _merge_context(
        {
            "employee_id": _safe_getattr(employee, "id", None),
            "employee_name": employee_name,
            "is_active": bool(is_active),
            "company_id": _safe_getattr(company, "id", None),
        },
        extra_context,
    )

    if employee_user:
        _notify_user(
            recipient=employee_user,
            title=title,
            message=employee_message,
            notification_type="hr_employee_status",
            severity=severity,
            link=_employee_link(employee),
            send_email=send_email_to_employee,
            send_whatsapp=send_whatsapp_to_employee,
            company=company,
            event_code=event_code,
            event_group="hr",
            source="services_hr.notify_employee_status_changed.employee",
            context=shared_context,
            target_object=employee,
            actor=actor,
        )

    _notify_users(
        recipients=managers,
        title=title,
        message=manager_message,
        notification_type="hr_employee_status",
        severity=severity,
        link=_employee_link(employee),
        send_email=send_email_to_managers,
        send_whatsapp=send_whatsapp_to_managers,
        company=company,
        event_code=event_code,
        event_group="hr",
        source="services_hr.notify_employee_status_changed.managers",
        context=shared_context,
        target_object=employee,
        actor=actor,
    )


def notify_employee_activated(
    employee: Employee,
    send_email_to_employee: bool = True,
    send_email_to_managers: bool = False,
    send_whatsapp_to_employee: bool = False,
    send_whatsapp_to_managers: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    return notify_employee_status_changed(
        employee,
        is_active=True,
        send_email_to_employee=send_email_to_employee,
        send_email_to_managers=send_email_to_managers,
        send_whatsapp_to_employee=send_whatsapp_to_employee,
        send_whatsapp_to_managers=send_whatsapp_to_managers,
        actor=actor,
        extra_context=extra_context,
    )


def notify_employee_deactivated(
    employee: Employee,
    send_email_to_employee: bool = True,
    send_email_to_managers: bool = False,
    send_whatsapp_to_employee: bool = False,
    send_whatsapp_to_managers: bool = False,
    actor=None,
    extra_context: dict | None = None,
):
    return notify_employee_status_changed(
        employee,
        is_active=False,
        send_email_to_employee=send_email_to_employee,
        send_email_to_managers=send_email_to_managers,
        send_whatsapp_to_employee=send_whatsapp_to_employee,
        send_whatsapp_to_managers=send_whatsapp_to_managers,
        actor=actor,
        extra_context=extra_context,
    )