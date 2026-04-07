# 📂 الملف: notification_center/services_company.py
# 🧠 Company Notification Engine — Mham Cloud V2.0
# ------------------------------------------------------------
# ✅ إشعارات تحديث بيانات الشركة
# ✅ إشعارات مستخدمي الشركات
# ✅ نقل الإرسال خارج طبقة API
# ✅ توحيد البريد عبر Notification Center
# ✅ يدعم Email HTML + In-App + WhatsApp من المسار الرسمي
# ✅ بدون EmailMultiAlternatives مباشر داخل الـ APIs
# ------------------------------------------------------------

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.html import escape

from notification_center.services import create_notification

User = get_user_model()
logger = logging.getLogger(__name__)


# ============================================================
# Helpers
# ============================================================
def _clean(value) -> str:
    return str(value).strip() if value is not None else ""


def _safe_value(value):
    return value if value not in (None, "") else "-"


def _company_payload_value(company, field_name: str):
    return getattr(company, field_name, "") or ""


def _company_logo_url(company) -> str | None:
    try:
        profile = getattr(company, "profile", None)
    except Exception:
        profile = None

    if profile:
        profile_settings = getattr(profile, "settings", None) or {}
        logo_url = profile_settings.get("logo_url")
        if logo_url:
            return logo_url

    try:
        company_logo = getattr(company, "logo", None)
        if company_logo:
            file_name = getattr(company_logo, "name", None)
            if isinstance(file_name, str) and file_name.startswith(("http://", "https://")):
                return file_name
            return company_logo.url
    except Exception:
        pass

    if profile:
        try:
            profile_logo = getattr(profile, "logo", None)
            if profile_logo:
                file_name = getattr(profile_logo, "name", None)
                if isinstance(file_name, str) and file_name.startswith(("http://", "https://")):
                    return file_name
                return profile_logo.url
        except Exception:
            pass

    return None


def _primey_email_logo_url() -> str:
    return getattr(
        settings,
        "PRIMEY_EMAIL_LOGO_URL",
        "https://drive.google.com/uc?export=view&id=1a0Y1SK3n-Hn9QDZa7Ge24r3--B8zXbTd",
    )


def _get_frontend_base_url() -> str:
    return (
        getattr(settings, "FRONTEND_BASE_URL", None)
        or getattr(settings, "FRONTEND_URL", None)
        or getattr(settings, "NEXT_PUBLIC_APP_URL", None)
        or "https://mhamcloud.sa"
    ).rstrip("/")


def _get_login_url() -> str:
    return f"{_get_frontend_base_url()}/login"


def _get_company_dashboard_url() -> str:
    return f"{_get_frontend_base_url()}/company"


def _safe_getattr(obj, attr_name: str, default=None):
    try:
        return getattr(obj, attr_name, default)
    except Exception:
        return default


def _first_non_empty(*values) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _get_user_profile(user):
    if not user:
        return None

    for attr_name in ["profile", "userprofile"]:
        profile = getattr(user, attr_name, None)
        if profile:
            return profile

    return None


def _get_user_phone(user) -> str:
    if not user:
        return ""

    user_phone = _first_non_empty(
        getattr(user, "phone", ""),
        getattr(user, "phone_number", ""),
        getattr(user, "mobile", ""),
        getattr(user, "mobile_number", ""),
        getattr(user, "whatsapp_number", ""),
    )
    if user_phone:
        return user_phone

    profile = _get_user_profile(user)
    if profile:
        profile_phone = _first_non_empty(
            getattr(profile, "phone", ""),
            getattr(profile, "phone_number", ""),
            getattr(profile, "mobile", ""),
            getattr(profile, "mobile_number", ""),
            getattr(profile, "whatsapp_number", ""),
        )
        if profile_phone:
            return profile_phone

    try:
        employee = getattr(user, "hr_employee", None)
        if employee and getattr(employee, "mobile_number", None):
            return str(employee.mobile_number).strip()
    except Exception:
        pass

    return ""


def _get_full_name(user) -> str:
    if not user:
        return "User"

    try:
        full_name = (user.get_full_name() or "").strip()
    except Exception:
        full_name = ""

    return (
        full_name
        or _clean(getattr(user, "full_name", ""))
        or _clean(getattr(user, "username", ""))
        or _clean(getattr(user, "email", ""))
        or "User"
    )


def _get_company_user_role(company_user) -> str:
    return _clean(getattr(company_user, "role", "")) or "EMPLOYEE"


def _build_company_user_common_context(company_user, extra_context: dict | None = None) -> dict:
    user = getattr(company_user, "user", None)
    company = getattr(company_user, "company", None)

    context = {
        "company_id": getattr(company, "id", None) if company else None,
        "company_name": _safe_value(getattr(company, "name", None) if company else None),
        "company_user_id": getattr(company_user, "id", None),
        "target_user_id": getattr(user, "id", None) if user else None,
        "recipient_name": _get_full_name(user),
        "full_name": _get_full_name(user),
        "username": _safe_value(getattr(user, "username", None) if user else None),
        "email": _safe_value(getattr(user, "email", None) if user else None),
        "phone": _safe_value(_get_user_phone(user)),
        "role": _get_company_user_role(company_user),
        "login_url": _get_login_url(),
        "company_dashboard_url": _get_company_dashboard_url(),
    }

    if isinstance(extra_context, dict):
        context.update(extra_context)

    return context


def _dispatch_company_user_notification(
    *,
    company_user,
    actor=None,
    title: str,
    message: str,
    event_code: str,
    context: dict | None = None,
    severity: str = "info",
    template_key: str | None = None,
    send_email: bool = True,
    send_whatsapp: bool = True,
    create_in_app: bool = True,
    link: str | None = None,
):
    if not company_user:
        return None

    user = getattr(company_user, "user", None)
    company = getattr(company_user, "company", None)

    if not user and not company:
        return None

    final_context = _build_company_user_common_context(
        company_user,
        extra_context=context,
    )

    note = create_notification(
        recipient=user,
        title=title,
        message=message,
        notification_type="company_user",
        severity=severity,
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        link=link or _get_company_dashboard_url(),
        company=company,
        event_code=event_code,
        event_group="company_user",
        actor=actor,
        target_user=user,
        source=f"notification_center.services_company.{event_code}",
        context=final_context,
        target_object=user,
        template_key=template_key or event_code,
        whatsapp_phone=_get_user_phone(user),
        whatsapp_recipient_name=_get_full_name(user),
        whatsapp_recipient_role=_get_company_user_role(company_user).lower(),
        create_in_app=bool(create_in_app and user),
    )

    return {
        "notification_created": bool(note),
        "email_sent": bool(note) if send_email else False,
        "email_error": None,
        "whatsapp_sent": bool(note) if send_whatsapp else False,
        "whatsapp_error": None,
    }


# ============================================================
# Company Settings Email Builders
# ============================================================
def _build_company_updated_email_html(
    *,
    owner_name: str,
    company_name: str,
    company_email: str,
    company_phone: str,
    commercial_number: str,
    vat_number: str,
    building_number: str,
    street: str,
    district: str,
    city: str,
    postal_code: str,
    short_address: str,
    changed_fields: list[dict],
    logo_url: str | None,
) -> str:
    logo_header_url = escape(_primey_email_logo_url())
    owner_name = escape(owner_name or "User")
    company_name = escape(_safe_value(company_name))
    company_email = escape(_safe_value(company_email))
    company_phone = escape(_safe_value(company_phone))
    commercial_number = escape(_safe_value(commercial_number))
    vat_number = escape(_safe_value(vat_number))
    building_number = escape(_safe_value(building_number))
    street = escape(_safe_value(street))
    district = escape(_safe_value(district))
    city = escape(_safe_value(city))
    postal_code = escape(_safe_value(postal_code))
    short_address = escape(_safe_value(short_address))
    safe_logo_url = escape(logo_url or "")

    changes_rows = ""
    for item in changed_fields:
        field_name = escape(item.get("field", ""))
        old_value = escape(_safe_value(item.get("old", "")))
        new_value = escape(_safe_value(item.get("new", "")))
        changes_rows += f"""
        <tr>
          <td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">{field_name}</td>
          <td style="padding:10px 12px;border:1px solid #e5e7eb;">{old_value}</td>
          <td style="padding:10px 12px;border:1px solid #e5e7eb;">{new_value}</td>
        </tr>
        """

    logo_block = ""
    if safe_logo_url:
        logo_block = f"""
        <div style="margin-top:20px;text-align:center;">
          <div style="font-size:14px;color:#374151;margin-bottom:10px;">الشعار الحالي</div>
          <img src="{safe_logo_url}" alt="Company Logo"
               style="max-height:90px;max-width:220px;width:auto;border:1px solid #e5e7eb;border-radius:12px;padding:10px;background:#ffffff;" />
        </div>
        """

    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>تم تحديث بيانات الشركة</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f7fb;font-family:Tahoma,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f7fb;margin:0;padding:24px 0;">
    <tr>
      <td align="center">
        <table width="680" cellpadding="0" cellspacing="0"
               style="max-width:680px;width:100%;background:#ffffff;border-radius:18px;overflow:hidden;border:1px solid #e5e7eb;">

          <tr>
            <td align="center" style="background:#000000;padding:28px 24px;">
              <img src="{logo_header_url}" alt="Primey"
                   style="max-height:56px;width:auto;display:block;margin:0 auto 12px auto;" />
              <div style="color:#ffffff;font-size:22px;font-weight:700;line-height:1.6;">
                Mham Cloud
              </div>
              <div style="color:#d1d5db;font-size:14px;line-height:1.8;">
                تم تحديث بيانات الشركة بنجاح
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:32px 28px 20px 28px;">
              <div style="font-size:16px;color:#111827;line-height:2;">
                أهلاً <strong>{owner_name}</strong>،
              </div>

              <div style="margin-top:10px;font-size:15px;color:#374151;line-height:2;">
                تم إجراء تعديل على بيانات الشركة داخل النظام، وهذه الرسالة للتأكيد فقط.
              </div>

              <div style="margin-top:22px;font-size:15px;font-weight:700;color:#111827;">
                بيانات الشركة الحالية
              </div>

              <table width="100%" cellpadding="0" cellspacing="0"
                     style="margin-top:12px;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;">
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">اسم الشركة</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{company_name}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">البريد الإلكتروني</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{company_email}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">الهاتف</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{company_phone}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">السجل التجاري</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{commercial_number}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">الرقم الضريبي</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{vat_number}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">رقم المبنى</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{building_number}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">الشارع</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{street}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">الحي</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{district}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">المدينة</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{city}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">الرمز البريدي</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{postal_code}</td></tr>
                <tr><td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f8fafc;">العنوان المختصر</td><td style="padding:10px 12px;border:1px solid #e5e7eb;">{short_address}</td></tr>
              </table>

              <div style="margin-top:24px;font-size:15px;font-weight:700;color:#111827;">
                الحقول التي تغيرت
              </div>

              <table width="100%" cellpadding="0" cellspacing="0"
                     style="margin-top:12px;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;">
                <tr>
                  <td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f1f5f9;">الحقل</td>
                  <td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f1f5f9;">القيمة السابقة</td>
                  <td style="padding:10px 12px;border:1px solid #e5e7eb;font-weight:700;background:#f1f5f9;">القيمة الجديدة</td>
                </tr>
                {changes_rows or '<tr><td colspan="3" style="padding:12px;border:1px solid #e5e7eb;">لا توجد تغييرات معروضة</td></tr>'}
              </table>

              {logo_block}

              <div style="margin-top:22px;font-size:13px;color:#b45309;line-height:2;">
                إذا لم تكن أنت من قام بهذا التغيير، يرجى مراجعة مسؤول النظام فورًا.
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:20px 28px 30px 28px;">
              <div style="border-top:1px solid #e5e7eb;padding-top:18px;font-size:12px;color:#9ca3af;line-height:1.9;text-align:center;">
                هذه رسالة آلية من Mham Cloud — يرجى عدم الرد عليها مباشرة.
              </div>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
""".strip()


def _build_company_updated_email_text(*, company, owner_name: str, changed_fields: list[dict]) -> str:
    text_changes = []
    for item in changed_fields:
        text_changes.append(
            f"- {item.get('field', '')}: {_safe_value(item.get('old', ''))} → {_safe_value(item.get('new', ''))}"
        )

    return (
        f"مرحباً {owner_name},\n\n"
        f"تم تحديث بيانات الشركة بنجاح داخل Mham Cloud.\n\n"
        f"اسم الشركة: {_safe_value(_company_payload_value(company, 'name'))}\n"
        f"البريد الإلكتروني: {_safe_value(_company_payload_value(company, 'email'))}\n"
        f"رقم الجوال: {_safe_value(_company_payload_value(company, 'phone'))}\n"
        f"السجل التجاري: {_safe_value(_company_payload_value(company, 'commercial_number'))}\n"
        f"الرقم الضريبي: {_safe_value(_company_payload_value(company, 'vat_number'))}\n"
        f"رقم المبنى: {_safe_value(_company_payload_value(company, 'building_number'))}\n"
        f"الشارع: {_safe_value(_company_payload_value(company, 'street'))}\n"
        f"الحي: {_safe_value(_company_payload_value(company, 'district'))}\n"
        f"المدينة: {_safe_value(_company_payload_value(company, 'city'))}\n"
        f"الرمز البريدي: {_safe_value(_company_payload_value(company, 'postal_code'))}\n"
        f"العنوان المختصر: {_safe_value(_company_payload_value(company, 'short_address'))}\n\n"
        f"الحقول المتغيرة:\n"
        f"{chr(10).join(text_changes) if text_changes else '- لا توجد تغييرات معروضة'}\n\n"
        f"مع تحيات Mham Cloud"
    )


# ============================================================
# Company Settings Notification
# ============================================================
def notify_company_settings_updated(
    *,
    company,
    changed_fields: list[dict],
    actor=None,
    send_email: bool = True,
    send_in_app: bool = True,
    extra_context: dict | None = None,
):
    """
    حدث رسمي عند تحديث بيانات الشركة.
    - In-App عبر Notification Center لمالك الشركة إن وجد
    - Email عبر Notification Center للمالك + بريد الشركة
    """
    if not company or not changed_fields:
        return None

    owner = getattr(company, "owner", None)
    owner_email = getattr(owner, "email", None) if owner else None
    company_email = getattr(company, "email", None)

    recipients: list[str] = []
    if owner_email:
        recipients.append(_clean(owner_email))
    if company_email and _clean(company_email) not in recipients:
        recipients.append(_clean(company_email))

    owner_name = (
        owner.get_full_name().strip()
        if owner and hasattr(owner, "get_full_name") and owner.get_full_name()
        else getattr(owner, "username", "User") if owner else "User"
    )

    subject = f"Mham Cloud | تم تحديث بيانات الشركة - {getattr(company, 'name', '')}"
    text_body = _build_company_updated_email_text(
        company=company,
        owner_name=owner_name,
        changed_fields=changed_fields,
    )
    html_body = _build_company_updated_email_html(
        owner_name=owner_name,
        company_name=_company_payload_value(company, "name"),
        company_email=_company_payload_value(company, "email"),
        company_phone=_company_payload_value(company, "phone"),
        commercial_number=_company_payload_value(company, "commercial_number"),
        vat_number=_company_payload_value(company, "vat_number"),
        building_number=_company_payload_value(company, "building_number"),
        street=_company_payload_value(company, "street"),
        district=_company_payload_value(company, "district"),
        city=_company_payload_value(company, "city"),
        postal_code=_company_payload_value(company, "postal_code"),
        short_address=_company_payload_value(company, "short_address"),
        changed_fields=changed_fields,
        logo_url=_company_logo_url(company),
    )

    context = {
        "company_id": getattr(company, "id", None),
        "company_name": _company_payload_value(company, "name"),
        "company_email": _company_payload_value(company, "email"),
        "company_phone": _company_payload_value(company, "phone"),
        "changed_fields": changed_fields,
    }
    if isinstance(extra_context, dict):
        context.update(extra_context)

    note = None

    try:
        note = create_notification(
            recipient=owner if owner else None,
            title="🏢 تم تحديث بيانات الشركة",
            message=f"تم تحديث بيانات الشركة ({_company_payload_value(company, 'name')}) بنجاح.",
            notification_type="company_settings",
            severity="info",
            send_email=bool(send_email and recipients),
            send_whatsapp=False,
            link=None,
            company=company,
            event_code="company_settings_updated",
            event_group="company",
            source="services_company.notify_company_settings_updated",
            context=context,
            target_object=company,
            actor=actor,
            target_user=owner if owner else None,
            template_key="company_settings_updated",
            email_recipients=recipients,
            email_subject=subject,
            email_text_message=text_body,
            email_html_message=html_body,
            create_in_app=bool(send_in_app and owner),
        )

        logger.info(
            "Company settings unified notification processed | company=%s | email=%s | in_app=%s | recipients=%s",
            getattr(company, "id", None),
            bool(send_email and recipients),
            bool(send_in_app and owner),
            recipients,
        )

    except Exception:
        logger.exception(
            "Failed unified company settings notification | company=%s",
            getattr(company, "id", None),
        )

    return note


# ============================================================
# Company User Notifications
# ============================================================
def notify_company_user_updated(
    *,
    actor=None,
    company=None,
    company_user=None,
    user=None,
    target_user=None,
    extra_context: dict | None = None,
):
    resolved_user = target_user or user or getattr(company_user, "user", None)
    resolved_company = company or getattr(company_user, "company", None)

    if not company_user:
        return {
            "notification_created": False,
            "email_sent": False,
            "email_error": "company_user is required",
            "whatsapp_sent": False,
            "whatsapp_error": "company_user is required",
        }

    context = _build_company_user_common_context(
        company_user,
        extra_context=extra_context,
    )

    return _dispatch_company_user_notification(
        company_user=company_user,
        actor=actor,
        title="تم تحديث بيانات حسابك",
        message=(
            "تم تحديث بيانات حسابك داخل الشركة بنجاح. "
            "إذا لم تكن أنت من قام بهذا التعديل، يرجى التواصل مع إدارة النظام فورًا."
        ),
        event_code="company_user_updated",
        context=context,
        severity="info",
        template_key="company_user_updated",
        send_email=bool(getattr(resolved_user, "email", "")),
        send_whatsapp=bool(_get_user_phone(resolved_user)),
        create_in_app=True,
        link=_get_company_dashboard_url(),
    )


def notify_company_user_role_changed(
    *,
    actor=None,
    company=None,
    company_user=None,
    user=None,
    target_user=None,
    extra_context: dict | None = None,
):
    resolved_user = target_user or user or getattr(company_user, "user", None)

    if not company_user:
        return {
            "notification_created": False,
            "email_sent": False,
            "email_error": "company_user is required",
            "whatsapp_sent": False,
            "whatsapp_error": "company_user is required",
        }

    context = _build_company_user_common_context(
        company_user,
        extra_context=extra_context,
    )

    old_role = _clean(context.get("old_role"))
    new_role = _clean(context.get("new_role")) or _get_company_user_role(company_user)

    message = "تم تحديث الدور الوظيفي المرتبط بحسابك داخل الشركة."
    if old_role or new_role:
        message += f" الدور السابق: {_safe_value(old_role)} | الدور الجديد: {_safe_value(new_role)}."

    return _dispatch_company_user_notification(
        company_user=company_user,
        actor=actor,
        title="تم تحديث دور حسابك",
        message=message,
        event_code="company_user_role_changed",
        context=context,
        severity="info",
        template_key="company_user_role_changed",
        send_email=bool(getattr(resolved_user, "email", "")),
        send_whatsapp=bool(_get_user_phone(resolved_user)),
        create_in_app=True,
        link=_get_company_dashboard_url(),
    )


def notify_company_user_status_changed(
    *,
    actor=None,
    company=None,
    company_user=None,
    user=None,
    target_user=None,
    extra_context: dict | None = None,
):
    resolved_user = target_user or user or getattr(company_user, "user", None)

    if not company_user:
        return {
            "notification_created": False,
            "email_sent": False,
            "email_error": "company_user is required",
            "whatsapp_sent": False,
            "whatsapp_error": "company_user is required",
        }

    context = _build_company_user_common_context(
        company_user,
        extra_context=extra_context,
    )

    is_active = bool(context.get("is_active", getattr(company_user, "is_active", False)))
    status_label = _clean(context.get("status_label")) or ("ACTIVE" if is_active else "INACTIVE")

    if is_active:
        title = "تم تفعيل حسابك"
        message = (
            "تم تفعيل حسابك داخل الشركة بنجاح. "
            f"الحالة الحالية: {status_label}."
        )
        severity = "success"
        event_code = "company_user_activated"
    else:
        title = "تم تعطيل حسابك"
        message = (
            "تم تعطيل حسابك داخل الشركة. "
            f"الحالة الحالية: {status_label}."
        )
        severity = "warning"
        event_code = "company_user_deactivated"

    return _dispatch_company_user_notification(
        company_user=company_user,
        actor=actor,
        title=title,
        message=message,
        event_code=event_code,
        context=context,
        severity=severity,
        template_key=event_code,
        send_email=bool(getattr(resolved_user, "email", "")),
        send_whatsapp=bool(_get_user_phone(resolved_user)),
        create_in_app=True,
        link=_get_company_dashboard_url(),
    )


def notify_company_user_password_reset(
    *,
    actor=None,
    company=None,
    company_user=None,
    user=None,
    target_user=None,
    new_password: str = "",
    extra_context: dict | None = None,
):
    resolved_user = target_user or user or getattr(company_user, "user", None)

    if not company_user:
        return {
            "notification_created": False,
            "email_sent": False,
            "email_error": "company_user is required",
            "whatsapp_sent": False,
            "whatsapp_error": "company_user is required",
        }

    context = _build_company_user_common_context(
        company_user,
        extra_context=extra_context,
    )
    context["temporary_password"] = _clean(new_password)

    message = (
        "تمت إعادة تعيين كلمة مرور حسابك بنجاح من خلال إدارة الشركة. "
        "إذا لم تكن أنت من قام بهذا الإجراء، يرجى التواصل مع مسؤول النظام فورًا."
    )

    if _clean(new_password):
        message += f"\nكلمة المرور المؤقتة: {_clean(new_password)}"

    return _dispatch_company_user_notification(
        company_user=company_user,
        actor=actor,
        title="تمت إعادة تعيين كلمة المرور",
        message=message,
        event_code="company_user_password_reset",
        context=context,
        severity="warning",
        template_key="company_user_password_reset",
        send_email=bool(getattr(resolved_user, "email", "")),
        send_whatsapp=bool(_get_user_phone(resolved_user)),
        create_in_app=True,
        link=_get_login_url(),
    )