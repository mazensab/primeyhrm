# 📂 الملف: notification_center/services.py
# 🧠 Mham Cloud — Smart Notification Services V7.4
# ------------------------------------------------------------
# ✅ الحفاظ على التوافق مع create_notification الحالي
# ✅ إنشاء NotificationEvent تلقائيًا
# ✅ إنشاء NotificationDelivery لكل قناة
# ✅ دعم In-App + Email + WhatsApp
# ✅ دعم بريد HTML مخصص + subject مخصص + recipients متعددة
# ✅ دعم مرفقات البريد (PDF / ملفات)
# ✅ إنشاء HTML احترافي افتراضي تلقائيًا عند عدم تمرير قالب خاص
# ✅ Fail-Safe كامل
# ✅ متوافق مع WebSocket + Channels
# ✅ جاهز للتوسعة لاحقًا نحو SMS / Push
# ✅ توحيد استخراج رقم واتساب من recipient / target_object / context
# ------------------------------------------------------------

from __future__ import annotations

import logging
from typing import Any, Iterable, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.html import escape

from .models import (
    Notification,
    NotificationChannel,
    NotificationDelivery,
    NotificationDeliveryStatus,
    NotificationEvent,
    NotificationEventStatus,
)

logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================
# 🧩 Helpers
# ============================================================
def _clean_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _safe_getattr(obj: Any, attr_name: str, default=None):
    try:
        return getattr(obj, attr_name, default)
    except Exception:
        return default


def _email_notifications_enabled() -> bool:
    return bool(getattr(settings, "EMAIL_NOTIFICATIONS_ENABLED", True))


def _whatsapp_notifications_enabled() -> bool:
    return bool(getattr(settings, "WHATSAPP_NOTIFICATIONS_ENABLED", True))


def _default_from_email() -> str:
    return getattr(
        settings,
        "DEFAULT_FROM_EMAIL",
        "Mham Cloud <no-reply@localhost>",
    )


def _default_app_name() -> str:
    return _clean_text(
        getattr(settings, "NOTIFICATION_APP_NAME", "")
        or getattr(settings, "EMAIL_APP_NAME", "")
        or getattr(settings, "PROJECT_BRAND_NAME", "")
        or "Mham Cloud"
    )


def _frontend_base_url() -> str:
    return (
        _clean_text(getattr(settings, "FRONTEND_BASE_URL", ""))
        or _clean_text(getattr(settings, "FRONTEND_URL", ""))
        or _clean_text(getattr(settings, "NEXT_PUBLIC_APP_URL", ""))
        or "https://mhamcloud.com"
    ).rstrip("/")


def _default_support_email() -> str:
    return (
        _clean_text(getattr(settings, "SUPPORT_EMAIL", ""))
        or _clean_text(getattr(settings, "DEFAULT_SUPPORT_EMAIL", ""))
        or "info@mhamcloud.sa"
    )


def _default_logo_url() -> str:
    return (
        _clean_text(getattr(settings, "PRIMEY_EMAIL_LOGO_URL", ""))
        or _clean_text(getattr(settings, "EMAIL_LOGO_URL", ""))
        or "https://drive.google.com/uc?export=view&id=1a0Y1SK3n-Hn9QDZa7Ge24r3--B8zXbTd"
    )


def _audit_bcc_list() -> list[str]:
    raw = getattr(settings, "EMAIL_AUDIT_BCC", [])
    if not raw:
        return []

    if isinstance(raw, str):
        return [email.strip() for email in raw.split(",") if email.strip()]

    if isinstance(raw, (list, tuple, set)):
        return [str(email).strip() for email in raw if str(email).strip()]

    return []


def _normalize_email_list(value: Any) -> list[str]:
    """
    تحويل أي مدخلات بريد إلى قائمة نظيفة بدون تكرار.
    """
    emails: list[str] = []

    if not value:
        return emails

    if isinstance(value, str):
        candidates = [item.strip() for item in value.split(",")]
    elif isinstance(value, (list, tuple, set)):
        candidates = [str(item).strip() for item in value]
    else:
        candidates = [str(value).strip()]

    seen: set[str] = set()
    for email in candidates:
        if not email:
            continue

        email_key = email.lower()
        if email_key in seen:
            continue

        seen.add(email_key)
        emails.append(email)

    return emails


def _normalize_email_attachments(value: Any) -> list[dict]:
    """
    يدعم:
    - [{"filename": "...", "content": b"...", "mimetype": "application/pdf"}]
    - [("file.pdf", b"..."), ("file.pdf", b"...", "application/pdf")]
    """
    normalized: list[dict] = []

    if not value:
        return normalized

    raw_items = value if isinstance(value, (list, tuple)) else [value]

    for item in raw_items:
        try:
            if isinstance(item, dict):
                filename = _clean_text(item.get("filename"))
                content = item.get("content")
                mimetype = _clean_text(item.get("mimetype")) or None

                if filename and content is not None:
                    normalized.append(
                        {
                            "filename": filename,
                            "content": content,
                            "mimetype": mimetype,
                        }
                    )
                continue

            if isinstance(item, tuple):
                if len(item) == 2:
                    filename, content = item
                    mimetype = None
                elif len(item) >= 3:
                    filename, content, mimetype = item[0], item[1], item[2]
                else:
                    continue

                filename = _clean_text(filename)
                mimetype = _clean_text(mimetype) or None

                if filename and content is not None:
                    normalized.append(
                        {
                            "filename": filename,
                            "content": content,
                            "mimetype": mimetype,
                        }
                    )
        except Exception as attachment_error:
            logger.warning(f"⚠️ تم تجاهل مرفق بريد غير صالح: {attachment_error}")

    return normalized


def _safe_username(user: User | None) -> str:
    if not user:
        return "unknown-user"

    return (
        getattr(user, "username", None)
        or getattr(user, "email", None)
        or f"user:{getattr(user, 'id', 'unknown')}"
    )


def _safe_company(company):
    return company if company is not None else None


def _safe_model_label(obj: Any) -> str:
    if obj is None:
        return ""

    meta = getattr(obj, "_meta", None)
    if meta:
        app_label = getattr(meta, "app_label", "")
        object_name = getattr(meta, "object_name", "")
        if app_label and object_name:
            return f"{app_label}.{object_name}"

    return obj.__class__.__name__


def _safe_object_id(obj: Any) -> str:
    if obj is None:
        return ""

    obj_id = getattr(obj, "pk", None)
    if obj_id is None:
        obj_id = getattr(obj, "id", None)

    return str(obj_id) if obj_id is not None else ""


def _json_safe_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    return {}


def _serialize_notification_for_ws(note: Notification) -> dict:
    return {
        "id": note.id,
        "title": note.title,
        "message": note.message,
        "notification_type": note.notification_type,
        "severity": note.severity,
        "link": note.link or "",
        "created_at": timezone.localtime(note.created_at).strftime("%Y-%m-%d %H:%M"),
    }


def _resolve_event_group(
    *,
    event_group: str | None = None,
    notification_type: str | None = None,
) -> str:
    if _clean_text(event_group):
        return _clean_text(event_group)

    if _clean_text(notification_type):
        return _clean_text(notification_type)

    return "system"


def _resolve_event_code(
    *,
    event_code: str | None = None,
    notification_type: str | None = None,
) -> str:
    if _clean_text(event_code):
        return _clean_text(event_code)

    if _clean_text(notification_type):
        return _clean_text(notification_type)

    return "system_notification"


def _resolve_user_phone(user: User | None) -> str:
    """
    استخراج رقم الجوال من user أو profile/userprofile بشكل مرن.
    """
    if not user:
        return ""

    direct_fields = [
        "mobile",
        "phone",
        "phone_number",
        "whatsapp_number",
        "mobile_number",
    ]

    for field_name in direct_fields:
        value = _clean_text(getattr(user, field_name, ""))
        if value:
            return value

    for profile_attr in ["profile", "userprofile"]:
        profile = getattr(user, profile_attr, None)
        if not profile:
            continue

        for field_name in direct_fields:
            value = _clean_text(getattr(profile, field_name, ""))
            if value:
                return value

    return ""


def _resolve_user_display_name(user: User | None) -> str:
    if not user:
        return ""

    get_full_name_fn = getattr(user, "get_full_name", None)
    if callable(get_full_name_fn):
        full_name = _clean_text(get_full_name_fn())
        if full_name:
            return full_name

    return (
        _clean_text(getattr(user, "full_name", ""))
        or _clean_text(getattr(user, "username", ""))
        or _clean_text(getattr(user, "email", ""))
    )


def _resolve_user_language_code(user: User | None, default: str = "ar") -> str:
    if not user:
        return default

    value = _clean_text(getattr(user, "preferred_language", ""))
    if value in {"ar", "en"}:
        return value

    for profile_attr in ["profile", "userprofile"]:
        profile = getattr(user, profile_attr, None)
        if not profile:
            continue

        profile_language = _clean_text(getattr(profile, "preferred_language", ""))
        if profile_language in {"ar", "en"}:
            return profile_language

    return default


def _resolve_employee_phone(employee: Any) -> str:
    """
    استخراج رقم الموظف بشكل مرن.
    """
    if not employee:
        return ""

    direct_fields = [
        "mobile_number",
        "mobile",
        "phone",
        "phone_number",
        "whatsapp_number",
        "personal_phone",
        "work_phone",
    ]

    for field_name in direct_fields:
        value = _clean_text(_safe_getattr(employee, field_name, ""))
        if value:
            return value

    related_user = _safe_getattr(employee, "user", None)
    if related_user:
        user_phone = _resolve_user_phone(related_user)
        if user_phone:
            return user_phone

    return ""


def _resolve_context_phone(context: dict | None = None) -> str:
    """
    محاولة استخراج الرقم من context.
    """
    ctx = _json_safe_dict(context)

    phone_candidates = [
        "recipient_phone",
        "phone",
        "phone_number",
        "mobile",
        "mobile_number",
        "whatsapp_number",
        "employee_phone",
        "employee_mobile_number",
        "user_phone",
        "manager_phone",
        "direct_manager_phone",
    ]

    for field_name in phone_candidates:
        value = _clean_text(ctx.get(field_name))
        if value:
            return value

    return ""


def _resolve_target_object_phone(target_object: Any | None = None) -> str:
    """
    استخراج رقم الجوال من target_object أو الكائنات المرتبطة به.
    يدعم:
    - User مباشرة
    - Employee مباشرة
    - كائن يحوي employee
    - كائن يحوي user
    """
    if target_object is None:
        return ""

    if _safe_getattr(target_object, "is_authenticated", None) is not None:
        phone = _resolve_user_phone(target_object)
        if phone:
            return phone

    employee_like_markers = [
        _safe_getattr(target_object, "employee_number", None),
        _safe_getattr(target_object, "mobile_number", None),
        _safe_getattr(target_object, "work_start_date", None),
    ]
    if any(marker is not None for marker in employee_like_markers):
        phone = _resolve_employee_phone(target_object)
        if phone:
            return phone

    related_employee = _safe_getattr(target_object, "employee", None)
    if related_employee:
        phone = _resolve_employee_phone(related_employee)
        if phone:
            return phone

    related_user = _safe_getattr(target_object, "user", None)
    if related_user:
        phone = _resolve_user_phone(related_user)
        if phone:
            return phone

    return ""


def _resolve_whatsapp_phone(
    *,
    explicit_phone: str | None = None,
    recipient: User | None = None,
    target_object: Any | None = None,
    context: dict | None = None,
) -> str:
    """
    توحيد استخراج رقم الواتساب داخل Notification Center.
    """
    if _clean_text(explicit_phone):
        return _clean_text(explicit_phone)

    recipient_phone = _resolve_user_phone(recipient)
    if recipient_phone:
        return recipient_phone

    object_phone = _resolve_target_object_phone(target_object)
    if object_phone:
        return object_phone

    context_phone = _resolve_context_phone(context)
    if context_phone:
        return context_phone

    return ""


# ============================================================
# ✉️ Professional Email Helpers
# ============================================================
def _absolute_link(value: str | None) -> str:
    raw = _clean_text(value)
    if not raw:
        return ""

    if raw.startswith(("http://", "https://")):
        return raw

    if raw.startswith("/"):
        return f"{_frontend_base_url()}{raw}"

    return f"{_frontend_base_url()}/{raw}"


def _recipient_display_name_from_context(
    recipient: User | None = None,
    context: dict | None = None,
) -> str:
    if recipient:
        name = _resolve_user_display_name(recipient)
        if name:
            return name

    ctx = _json_safe_dict(context)
    for key in [
        "recipient_name",
        "full_name",
        "employee_name",
        "username",
        "name",
    ]:
        value = _clean_text(ctx.get(key))
        if value:
            return value

    return "المستخدم"


def _company_display_name(company=None, context: dict | None = None) -> str:
    company_name = _clean_text(_safe_getattr(company, "name", ""))
    if company_name:
        return company_name

    ctx = _json_safe_dict(context)
    return _clean_text(ctx.get("company_name")) or _default_app_name()


def _severity_palette(severity: str) -> dict[str, str]:
    normalized = _clean_text(severity).lower()

    palettes = {
        "success": {
            "badge_bg": "#dcfce7",
            "badge_text": "#166534",
            "accent": "#16a34a",
        },
        "warning": {
            "badge_bg": "#fef3c7",
            "badge_text": "#92400e",
            "accent": "#d97706",
        },
        "error": {
            "badge_bg": "#fee2e2",
            "badge_text": "#991b1b",
            "accent": "#dc2626",
        },
        "danger": {
            "badge_bg": "#fee2e2",
            "badge_text": "#991b1b",
            "accent": "#dc2626",
        },
        "info": {
            "badge_bg": "#dbeafe",
            "badge_text": "#1d4ed8",
            "accent": "#2563eb",
        },
    }

    return palettes.get(normalized, palettes["info"])


def _render_message_html_blocks(message: str) -> str:
    clean_message = _clean_text(message)
    if not clean_message:
        return ""

    paragraphs = []
    for raw_line in clean_message.splitlines():
        line = _clean_text(raw_line)
        if not line:
            continue

        paragraphs.append(
            f"""
            <div style="margin:0 0 12px;color:#334155;font-size:15px;line-height:2;">
              {escape(line)}
            </div>
            """.strip()
        )

    return "\n".join(paragraphs)


def _build_default_notification_email_html(
    *,
    recipient: User | None,
    title: str,
    message: str,
    subject: str,
    severity: str = "info",
    link: str | None = None,
    company=None,
    context: dict | None = None,
) -> str:
    resolved_link = _absolute_link(link)
    app_name = escape(_default_app_name())
    support_email = escape(_default_support_email())
    app_url = escape(_frontend_base_url())
    logo_url = escape(_default_logo_url())
    recipient_name = escape(_recipient_display_name_from_context(recipient=recipient, context=context))
    company_name = escape(_company_display_name(company=company, context=context))
    safe_title = escape(_clean_text(title) or _clean_text(subject) or "تنبيه جديد")
    safe_subject = escape(_clean_text(subject) or _clean_text(title) or "تنبيه جديد")
    message_blocks = _render_message_html_blocks(message)
    palette = _severity_palette(severity)

    badge_label_map = {
        "success": "نجاح",
        "warning": "تنبيه",
        "error": "هام",
        "danger": "هام",
        "info": "إشعار",
    }
    badge_label = badge_label_map.get(_clean_text(severity).lower(), "إشعار")

    cta_block = ""
    if resolved_link:
        safe_link = escape(resolved_link)
        cta_block = f"""
        <tr>
          <td style="padding:0 32px 28px 32px;">
            <a
              href="{safe_link}"
              style="
                display:inline-block;
                background:{palette['accent']};
                color:#ffffff;
                text-decoration:none;
                font-size:15px;
                font-weight:700;
                padding:14px 26px;
                border-radius:12px;
              "
            >
              عرض التفاصيل
            </a>
          </td>
        </tr>
        """

    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{safe_subject}</title>
</head>
<body style="margin:0;padding:0;background-color:#f6f8fb;font-family:Tahoma,Arial,'Segoe UI',sans-serif;direction:rtl;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;">
    {safe_subject}
  </div>

  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f6f8fb;margin:0;padding:24px 0;">
    <tr>
      <td align="center">
        <table
          width="680"
          cellpadding="0"
          cellspacing="0"
          style="max-width:680px;width:100%;background:#ffffff;border:1px solid #e8eef7;border-radius:20px;overflow:hidden;"
        >
          <tr>
            <td align="center" style="background:linear-gradient(135deg,#0f172a 0%,#111827 100%);padding:30px 24px 24px;">
              <img
                src="{logo_url}"
                alt="{app_name}"
                width="148"
                height="48"
                style="margin:0 auto 14px;object-fit:contain;display:block;"
              />
              <div style="margin:0;color:#cbd5e1;font-size:14px;line-height:24px;">
                نظام احترافي لإدارة الشركات والموظفين والفوترة والاشتراكات
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:28px 24px 8px;">
              <div style="margin:0 0 16px;font-size:24px;font-weight:700;color:#0f172a;line-height:1.5;">
                {safe_title}
              </div>

              <div
                style="
                  display:inline-block;
                  margin:0 0 18px;
                  padding:6px 12px;
                  border-radius:999px;
                  background:{palette['badge_bg']};
                  color:{palette['badge_text']};
                  font-size:12px;
                  font-weight:700;
                "
              >
                {badge_label}
              </div>

              <div
                style="
                  background-color:#ffffff;
                  border:1px solid #e5e7eb;
                  border-radius:16px;
                  padding:24px;
                "
              >
                <div style="margin:0 0 14px;color:#0f172a;font-size:16px;line-height:2;">
                  أهلاً <strong>{recipient_name}</strong>،
                </div>

                <div style="margin:0 0 16px;color:#475569;font-size:14px;line-height:2;">
                  هذه رسالة آلية من <strong>{app_name}</strong> لإشعارك بحدث جديد مرتبط بحسابك أو نشاطك داخل النظام.
                </div>

                {message_blocks}

                <div
                  style="
                    margin-top:18px;
                    padding:14px 16px;
                    border-radius:12px;
                    background:#f8fafc;
                    border:1px solid #e2e8f0;
                    color:#334155;
                    font-size:14px;
                    line-height:1.9;
                  "
                >
                  <div><strong>المنصة:</strong> {app_name}</div>
                  <div><strong>الجهة:</strong> {company_name}</div>
                </div>
              </div>
            </td>
          </tr>

          {cta_block}

          <tr>
            <td style="padding:8px 24px 26px;text-align:center;">
              <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0 20px;" />

              <div style="margin:0 0 8px;color:#475569;font-size:13px;line-height:22px;">
                تم إرسال هذه الرسالة من خلال نظام {app_name}.
              </div>

              <div style="margin:0 0 8px;color:#475569;font-size:13px;line-height:22px;">
                الموقع:
                <a href="{app_url}" style="color:#2563eb;text-decoration:none;"> {app_url}</a>
              </div>

              <div style="margin:0 0 8px;color:#475569;font-size:13px;line-height:22px;">
                الدعم الفني:
                <a href="mailto:{support_email}" style="color:#2563eb;text-decoration:none;"> {support_email}</a>
              </div>

              <div style="margin:8px 0 0;color:#94a3b8;font-size:12px;line-height:20px;">
                © 2026 {app_name}. جميع الحقوق محفوظة.
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


# ============================================================
# 🧩 Event / Delivery Builders
# ============================================================
def create_notification_event(
    *,
    event_code: str,
    event_group: str = "system",
    company=None,
    actor: User | None = None,
    target_user: User | None = None,
    severity: str = "info",
    title: str | None = None,
    message: str | None = None,
    link: str | None = None,
    language_code: str = "ar",
    source: str | None = None,
    context: dict | None = None,
    target_object: Any | None = None,
) -> NotificationEvent | None:
    """
    إنشاء الحدث الأصلي داخل النظام.
    """
    event_code = _clean_text(event_code)
    event_group = _clean_text(event_group) or "system"
    title = _clean_text(title)
    message = _clean_text(message)
    link = _clean_text(link)
    language_code = _clean_text(language_code) or "ar"
    source = _clean_text(source)

    if not event_code:
        logger.warning("🚫 تم تجاهل إنشاء NotificationEvent بدون event_code.")
        return None

    try:
        event = NotificationEvent.objects.create(
            company=_safe_company(company),
            actor=actor,
            target_user=target_user,
            event_code=event_code,
            event_group=event_group,
            severity=severity or "info",
            status=NotificationEventStatus.PENDING,
            language_code=language_code,
            target_model=_safe_model_label(target_object),
            target_object_id=_safe_object_id(target_object),
            title=title or None,
            message=message or None,
            link=link or None,
            context=_json_safe_dict(context),
            source=source or None,
        )
        return event

    except Exception as e:
        logger.error(f"❌ فشل إنشاء NotificationEvent: {e}")
        return None


def create_notification_delivery(
    *,
    event: NotificationEvent | None,
    channel: str,
    recipient: User | None = None,
    company=None,
    destination: str | None = None,
    subject: str | None = None,
    rendered_message: str | None = None,
    template_key: str | None = None,
    language_code: str = "ar",
    provider_name: str | None = None,
    notification: Notification | None = None,
) -> NotificationDelivery | None:
    """
    إنشاء سجل تسليم لقناة محددة.
    """
    if not event:
        return None

    try:
        return NotificationDelivery.objects.create(
            event=event,
            company=_safe_company(company) or getattr(event, "company", None),
            recipient=recipient,
            channel=channel,
            status=NotificationDeliveryStatus.PENDING,
            destination=_clean_text(destination) or None,
            subject=_clean_text(subject) or None,
            rendered_message=_clean_text(rendered_message) or None,
            template_key=_clean_text(template_key) or None,
            language_code=_clean_text(language_code) or "ar",
            provider_name=_clean_text(provider_name) or None,
            notification=notification,
        )
    except Exception as e:
        logger.warning(f"⚠️ فشل إنشاء NotificationDelivery (غير حرج): {e}")
        return None


def _finalize_event_status(event: NotificationEvent | None) -> None:
    """
    تحديث حالة الحدث بناءً على حالات الـ deliveries.
    """
    if not event:
        return

    try:
        deliveries = list(event.deliveries.all())
        if not deliveries:
            event.mark_failed()
            return

        statuses = {delivery.status for delivery in deliveries}

        if statuses == {NotificationDeliveryStatus.SENT}:
            event.mark_processed(NotificationEventStatus.PROCESSED)
            return

        if NotificationDeliveryStatus.SENT in statuses and (
            NotificationDeliveryStatus.FAILED in statuses
            or NotificationDeliveryStatus.SKIPPED in statuses
            or NotificationDeliveryStatus.RETRYING in statuses
        ):
            event.mark_processed(NotificationEventStatus.PARTIAL)
            return

        if NotificationDeliveryStatus.SENT in statuses:
            event.mark_processed(NotificationEventStatus.PROCESSED)
            return

        if statuses.issubset(
            {
                NotificationDeliveryStatus.FAILED,
                NotificationDeliveryStatus.SKIPPED,
                NotificationDeliveryStatus.CANCELLED,
            }
        ):
            event.mark_failed()
            return

        event.status = NotificationEventStatus.PENDING
        event.processed_at = None
        event.save(update_fields=["status", "processed_at"])

    except Exception as e:
        logger.warning(f"⚠️ تعذر تحديث حالة الحدث #{getattr(event, 'id', '?')}: {e}")


# ============================================================
# ✉️ Email Sender (Fail-Safe + Attachments)
# ============================================================
def _send_notification_email(
    *,
    recipient: User | None,
    title: str,
    message: str,
    recipient_emails: list[str] | None = None,
    subject_override: str | None = None,
    text_message: str | None = None,
    html_message: str | None = None,
    link: str | None = None,
    company=None,
    context: dict | None = None,
    severity: str = "info",
    attachments: list[dict] | None = None,
) -> tuple[bool, dict]:
    """
    ✉️ إرسال بريد الإشعار بشكل Fail-Safe.
    يدعم:
    - recipient الافتراضي
    - recipient_emails متعددة
    - subject مخصص
    - text/html body مخصصين
    - HTML احترافي افتراضي عند عدم تمرير قالب خاص
    - مرفقات بريد مثل PDF
    """
    if not _email_notifications_enabled():
        logger.info("📭 البريد معطّل من الإعدادات: EMAIL_NOTIFICATIONS_ENABLED=False")
        return False, {"reason": "EMAIL_NOTIFICATIONS_DISABLED"}

    resolved_recipients = _normalize_email_list(recipient_emails)
    if not resolved_recipients and recipient is not None:
        resolved_recipients = _normalize_email_list(getattr(recipient, "email", ""))

    if not resolved_recipients:
        logger.info(f"📭 لا يوجد بريد صالح للمستخدم {_safe_username(recipient)}")
        return False, {"reason": "RECIPIENT_EMAIL_MISSING"}

    resolved_subject = _clean_text(subject_override) or f"[{_default_app_name()}] {_clean_text(title)}"
    resolved_text_message = _clean_text(text_message) or _clean_text(message)

    resolved_html_message = html_message
    if not resolved_html_message:
        resolved_html_message = _build_default_notification_email_html(
            recipient=recipient,
            title=title,
            message=resolved_text_message or message,
            subject=resolved_subject,
            severity=severity,
            link=link,
            company=company,
            context=context,
        )

    resolved_attachments = _normalize_email_attachments(attachments)

    try:
        email = EmailMultiAlternatives(
            subject=resolved_subject,
            body=resolved_text_message,
            from_email=_default_from_email(),
            to=resolved_recipients,
        )

        if resolved_html_message:
            email.attach_alternative(resolved_html_message, "text/html")

        attached_filenames: list[str] = []
        for item in resolved_attachments:
            filename = item["filename"]
            content = item["content"]
            mimetype = item.get("mimetype") or None

            email.attach(filename, content, mimetype)
            attached_filenames.append(filename)

        email.send(fail_silently=False)
        logger.info(f"✅ تم إرسال بريد إشعار إلى: {resolved_recipients}")

        audit_bcc = _audit_bcc_list()
        if audit_bcc:
            try:
                send_mail(
                    subject=f"[AUDIT COPY] {resolved_subject}",
                    message=(
                        f"Recipients: {', '.join(resolved_recipients)}\n\n"
                        f"Title: {_clean_text(title)}\n\n"
                        f"Message:\n{resolved_text_message}"
                    ),
                    from_email=_default_from_email(),
                    recipient_list=audit_bcc,
                    fail_silently=True,
                    html_message=None,
                )
            except Exception as audit_error:
                logger.warning(f"⚠️ فشل إرسال نسخة BCC audit (غير حرج): {audit_error}")

        return True, {
            "provider": "django_email_multi_alternatives",
            "recipient_emails": resolved_recipients,
            "status": "sent",
            "subject": resolved_subject,
            "has_html": bool(resolved_html_message),
            "attachments_count": len(attached_filenames),
            "attachments": attached_filenames,
        }

    except Exception as e:
        logger.warning(f"📭 فشل إرسال بريد إشعار (غير حرج): {e}")
        return False, {
            "provider": "django_email_multi_alternatives",
            "recipient_emails": resolved_recipients,
            "status": "failed",
            "subject": resolved_subject,
            "error": str(e),
            "attachments_count": len(resolved_attachments),
        }


# ============================================================
# 💬 WhatsApp Sender (Fail-Safe)
# ============================================================
def _send_notification_whatsapp(
    *,
    delivery: NotificationDelivery,
    recipient: User | None,
    recipient_phone: str | None = None,
    recipient_name: str | None = None,
    recipient_role: str = "user",
    company=None,
    language_code: str = "ar",
    context: dict | None = None,
    attachment_url: str = "",
    attachment_name: str = "",
    mime_type: str = "",
) -> tuple[bool, dict]:
    """
    إرسال واتساب عبر الجسر الرسمي مع Fail-Safe كامل.
    """
    if not _whatsapp_notifications_enabled():
        logger.info("📵 الواتساب معطّل من الإعدادات: WHATSAPP_NOTIFICATIONS_ENABLED=False")
        return False, {"reason": "WHATSAPP_NOTIFICATIONS_DISABLED"}

    resolved_phone = _clean_text(recipient_phone) or _resolve_user_phone(recipient)
    if not resolved_phone:
        logger.info(f"📵 لا يوجد رقم واتساب للمستخدم {_safe_username(recipient)}")
        return False, {"reason": "RECIPIENT_PHONE_MISSING"}

    resolved_name = (
        _clean_text(recipient_name)
        or _resolve_user_display_name(recipient)
        or _safe_username(recipient)
    )

    resolved_language = _clean_text(language_code) or _resolve_user_language_code(recipient, default="ar")

    try:
        from whatsapp_center.services import send_notification_center_whatsapp_delivery

        log = send_notification_center_whatsapp_delivery(
            delivery=delivery,
            recipient_phone=resolved_phone,
            recipient_name=resolved_name,
            recipient_role=_clean_text(recipient_role) or "user",
            company=company,
            language_code=resolved_language,
            context=context or {},
            attachment_url=attachment_url,
            attachment_name=attachment_name,
            mime_type=mime_type,
        )

        if not log:
            return False, {
                "reason": "WHATSAPP_LOG_NOT_CREATED",
                "recipient_phone": resolved_phone,
            }

        delivery_status = _clean_text(getattr(log, "delivery_status", ""))
        success = delivery_status.upper() == "SENT"

        return success, {
            "provider": "whatsapp_center",
            "recipient_phone": resolved_phone,
            "recipient_name": resolved_name,
            "status": "sent" if success else "failed",
            "log_id": getattr(log, "id", None),
            "external_message_id": _clean_text(getattr(log, "external_message_id", "")),
            "delivery_status": delivery_status,
            "provider_status": _clean_text(getattr(log, "provider_status", "")),
            "failure_reason": _clean_text(getattr(log, "failure_reason", "")),
        }

    except Exception as e:
        logger.warning(f"📵 فشل إرسال واتساب (غير حرج): {e}")
        return False, {
            "provider": "whatsapp_center",
            "recipient_phone": resolved_phone,
            "status": "failed",
            "error": str(e),
        }


# ============================================================
# 📡 WebSocket Broadcast
# ============================================================
def _broadcast_live_notification(note: Notification) -> None:
    """
    📡 إرسال إشعار جديد للمجموعة المخصصة للمستخدم.
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("⚠️ لم يتم العثور على Channel Layer.")
            return

        group_name = f"user_{note.recipient.id}"
        payload = {
            "type": "send_notification",
            "data": {
                "type": "new",
                "notification": _serialize_notification_for_ws(note),
            },
        }

        async_to_sync(channel_layer.group_send)(group_name, payload)
        logger.debug(f"📡 بث إشعار مباشر للمجموعة: {group_name}")

    except Exception as e:
        logger.warning(f"⚠️ فشل بث الإشعار الفوري: {e}")


# ============================================================
# 1️⃣ الدالة العامة لإنشاء إشعار فردي + Event + Delivery + بريد + واتساب
# ============================================================
@transaction.atomic
def create_notification(
    *,
    recipient: User | None = None,
    title: str,
    message: str,
    notification_type: str = "system",
    severity: str = "info",
    send_email: bool = False,
    send_whatsapp: bool = False,
    link: str | None = None,
    company=None,
    event: NotificationEvent | None = None,
    event_code: str | None = None,
    event_group: str | None = None,
    actor: User | None = None,
    target_user: User | None = None,
    language_code: str = "ar",
    source: str | None = None,
    context: dict | None = None,
    target_object: Any | None = None,
    template_key: str | None = None,
    whatsapp_phone: str | None = None,
    whatsapp_recipient_name: str | None = None,
    whatsapp_recipient_role: str = "user",
    whatsapp_attachment_url: str = "",
    whatsapp_attachment_name: str = "",
    whatsapp_mime_type: str = "",
    email_recipients: list[str] | tuple[str, ...] | set[str] | str | None = None,
    email_subject: str | None = None,
    email_text_message: str | None = None,
    email_html_message: str | None = None,
    email_attachments: list[dict] | list[tuple] | tuple | None = None,
    create_in_app: bool = True,
) -> Notification | None:
    """
    🧠 إنشاء إشعار جديد وتفعيله.

    الجديد في V7.4:
    - دعم بريد HTML مخصص
    - دعم subject مخصص
    - دعم recipients متعددة
    - دعم email-only notification عند الحاجة
    - دعم مرفقات البريد (email_attachments)
    - الحفاظ على التوافق الكامل مع الاستدعاءات القديمة
    - توحيد استخراج رقم الواتساب من recipient / target_object / context
    - توليد قالب بريد احترافي تلقائيًا عند عدم تمرير HTML مخصص
    """
    if not recipient and not send_email and not send_whatsapp:
        logger.warning("🚫 محاولة إنشاء إشعار بدون مستلم وبدون أي قناة إرسال.")
        return None

    title = _clean_text(title)
    message = _clean_text(message)
    link = _clean_text(link)

    if not title and not message:
        logger.warning("🚫 تم تجاهل إشعار فارغ (عنوان ورسالة فارغان).")
        return None

    resolved_company = _safe_company(company)
    resolved_target_user = target_user or recipient
    resolved_event_group = _resolve_event_group(
        event_group=event_group,
        notification_type=notification_type,
    )
    resolved_event_code = _resolve_event_code(
        event_code=event_code,
        notification_type=notification_type,
    )
    resolved_context = _json_safe_dict(context)
    resolved_email_recipients = _normalize_email_list(email_recipients)
    resolved_email_attachments = _normalize_email_attachments(email_attachments)

    note: Notification | None = None

    try:
        if event is None:
            event = create_notification_event(
                event_code=resolved_event_code,
                event_group=resolved_event_group,
                company=resolved_company,
                actor=actor,
                target_user=resolved_target_user,
                severity=severity,
                title=title,
                message=message,
                link=link,
                language_code=language_code,
                source=source or "services.create_notification",
                context=resolved_context,
                target_object=target_object,
            )

        if recipient is not None and create_in_app:
            note = Notification.objects.create(
                company=resolved_company or getattr(event, "company", None),
                recipient=recipient,
                title=title,
                message=message,
                notification_type=notification_type,
                severity=severity,
                link=link or None,
                event=event,
            )

            in_app_delivery = create_notification_delivery(
                event=event,
                channel=NotificationChannel.IN_APP,
                recipient=recipient,
                company=resolved_company or getattr(event, "company", None),
                destination=f"user:{recipient.id}",
                subject=title,
                rendered_message=message,
                template_key=template_key,
                language_code=language_code,
                provider_name="notification_center",
                notification=note,
            )

            if in_app_delivery:
                try:
                    in_app_delivery.mark_attempt()
                    in_app_delivery.mark_sent(
                        provider_message_id=str(note.id),
                        provider_response={
                            "notification_id": note.id,
                            "channel": NotificationChannel.IN_APP,
                            "status": "sent",
                        },
                    )
                except Exception as delivery_error:
                    logger.warning(f"⚠️ فشل تحديث Delivery الخاص بـ in_app: {delivery_error}")

            _broadcast_live_notification(note)

        if send_email:
            email_destination = ",".join(resolved_email_recipients) if resolved_email_recipients else _clean_text(
                getattr(recipient, "email", "") if recipient else ""
            )

            email_delivery = create_notification_delivery(
                event=event,
                channel=NotificationChannel.EMAIL,
                recipient=recipient,
                company=resolved_company or getattr(event, "company", None),
                destination=email_destination or None,
                subject=_clean_text(email_subject) or title,
                rendered_message=_clean_text(email_text_message) or message,
                template_key=template_key,
                language_code=language_code,
                provider_name="django_email_multi_alternatives",
                notification=note,
            )

            if email_delivery:
                email_delivery.mark_attempt()

            email_sent, email_response = _send_notification_email(
                recipient=recipient,
                title=note.title if note else title,
                message=note.message if note else message,
                recipient_emails=resolved_email_recipients,
                subject_override=email_subject,
                text_message=email_text_message,
                html_message=email_html_message,
                link=link,
                company=resolved_company or getattr(event, "company", None),
                context=resolved_context,
                severity=severity,
                attachments=resolved_email_attachments,
            )

            if email_delivery:
                if email_sent:
                    provider_message_id = None
                    recipient_list = email_response.get("recipient_emails", [])
                    if recipient_list:
                        provider_message_id = ",".join(recipient_list)

                    email_delivery.mark_sent(
                        provider_message_id=provider_message_id,
                        provider_response=email_response,
                    )
                else:
                    email_delivery.mark_failed(
                        error_message=_clean_text(email_response.get("reason"))
                        or _clean_text(email_response.get("error"))
                        or "EMAIL_SEND_FAILED",
                        provider_response=email_response,
                    )

            if email_sent and note and hasattr(note, "mark_as_sent_email"):
                try:
                    note.mark_as_sent_email()
                except Exception as mark_error:
                    logger.warning(f"⚠️ تعذر تحديث حالة البريد في الإشعار: {mark_error}")

        if send_whatsapp:
            whatsapp_destination = _resolve_whatsapp_phone(
                explicit_phone=whatsapp_phone,
                recipient=recipient,
                target_object=target_object,
                context=resolved_context,
            )

            whatsapp_delivery = create_notification_delivery(
                event=event,
                channel=NotificationChannel.WHATSAPP,
                recipient=recipient,
                company=resolved_company or getattr(event, "company", None),
                destination=whatsapp_destination or None,
                subject=title,
                rendered_message=message,
                template_key=template_key,
                language_code=_clean_text(language_code) or _resolve_user_language_code(recipient, default="ar"),
                provider_name="whatsapp_center",
                notification=note,
            )

            if whatsapp_delivery:
                whatsapp_sent, whatsapp_response = _send_notification_whatsapp(
                    delivery=whatsapp_delivery,
                    recipient=recipient,
                    recipient_phone=whatsapp_destination,
                    recipient_name=whatsapp_recipient_name,
                    recipient_role=whatsapp_recipient_role,
                    company=resolved_company or getattr(event, "company", None),
                    language_code=language_code,
                    context=resolved_context,
                    attachment_url=whatsapp_attachment_url,
                    attachment_name=whatsapp_attachment_name,
                    mime_type=whatsapp_mime_type,
                )

                if whatsapp_delivery.status == NotificationDeliveryStatus.PENDING:
                    if whatsapp_sent:
                        whatsapp_delivery.mark_sent(
                            provider_message_id=_clean_text(
                                whatsapp_response.get("external_message_id", "")
                            ) or None,
                            provider_response=whatsapp_response,
                        )
                    else:
                        whatsapp_delivery.mark_failed(
                            error_message=_clean_text(whatsapp_response.get("reason"))
                            or _clean_text(whatsapp_response.get("failure_reason"))
                            or _clean_text(whatsapp_response.get("error"))
                            or "WHATSAPP_SEND_FAILED",
                            provider_response=whatsapp_response,
                        )

        _finalize_event_status(event)

        logger.info(
            f"✅ إشعار جديد أُنشئ/عولج للمستخدم {_safe_username(recipient)}: {title}"
        )
        return note

    except Exception as e:
        logger.error(f"❌ فشل إنشاء الإشعار (Non-Blocking): {e}")
        try:
            _finalize_event_status(event)
        except Exception:
            pass
        return None


# ============================================================
# 2️⃣ إرسال Event موحّد لعدة قنوات (النسخة الأولى)
# ============================================================
def dispatch_notification_event(
    *,
    recipients: Iterable[User],
    title: str,
    message: str,
    notification_type: str = "system",
    severity: str = "info",
    send_email: bool = False,
    send_whatsapp: bool = False,
    link: str | None = None,
    company=None,
    event_code: str | None = None,
    event_group: str | None = None,
    actor: User | None = None,
    language_code: str = "ar",
    source: str | None = None,
    context: dict | None = None,
    target_object: Any | None = None,
    template_key: str | None = None,
) -> list[Notification]:
    """
    بوابة موحدة مبدئية لإطلاق نفس الحدث على عدة مستلمين.
    """
    notes: list[Notification] = []
    seen_user_ids: set[int] = set()

    for recipient in recipients:
        if not recipient:
            continue

        user_id = getattr(recipient, "id", None)
        if not user_id or user_id in seen_user_ids:
            continue

        seen_user_ids.add(user_id)

        note = create_notification(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            severity=severity,
            send_email=send_email,
            send_whatsapp=send_whatsapp,
            link=link,
            company=company,
            event_code=event_code,
            event_group=event_group,
            actor=actor,
            target_user=recipient,
            language_code=language_code,
            source=source or "services.dispatch_notification_event",
            context=context,
            target_object=target_object,
            template_key=template_key,
        )
        if note:
            notes.append(note)

    return notes


# ============================================================
# 3️⃣ إشعار جماعي
# ============================================================
def broadcast_notification(
    *,
    users: Iterable[User],
    title: str,
    message: str,
    ntype: str = "system",
    severity: str = "info",
    send_email: bool = False,
    send_whatsapp: bool = False,
) -> list[Notification]:
    """
    🔔 إرسال نفس الإشعار لمجموعة مستخدمين.
    """
    return dispatch_notification_event(
        recipients=users,
        title=title,
        message=message,
        notification_type=ntype,
        severity=severity,
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        event_code=ntype,
        event_group=ntype,
        source="services.broadcast_notification",
    )


# ============================================================
# 4️⃣ إعلان عام
# ============================================================
def announce_global(
    title: str,
    message: str,
    severity: str = "info",
    send_email: bool = False,
    send_whatsapp: bool = False,
) -> list[Notification]:
    """
    📢 إعلان عام لجميع المستخدمين.
    """
    users = User.objects.all()
    return broadcast_notification(
        users=users,
        title=title,
        message=message,
        ntype="announcement",
        severity=severity,
        send_email=send_email,
        send_whatsapp=send_whatsapp,
    )


# ============================================================
# 5️⃣ إشعار الفوترة
# ============================================================
def notify_billing_event(
    recipient: User,
    invoice_number: str,
    status: str,
    send_email: bool = False,
    send_whatsapp: bool = False,
) -> Notification | None:
    title = f"💳 تحديث حالة الفاتورة رقم {invoice_number}"
    message = f"تم تحديث حالة الفاتورة رقم {invoice_number} إلى: {status}"
    severity = "success" if _clean_text(status).lower() == "paid" else "info"

    return create_notification(
        recipient=recipient,
        title=title,
        message=message,
        notification_type="billing",
        severity=severity,
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        event_code="billing_invoice_status_updated",
        event_group="billing",
        source="services.notify_billing_event",
        context={
            "invoice_number": _clean_text(invoice_number),
            "status": _clean_text(status),
        },
    )


# ============================================================
# 6️⃣ إشعار التقارير
# ============================================================
def notify_report_generated(
    recipient: User,
    report_title: str,
    send_email: bool = False,
    send_whatsapp: bool = False,
) -> Notification | None:
    return create_notification(
        recipient=recipient,
        title=f"📊 تم إنشاء تقرير جديد: {report_title}",
        message=f"تم توليد التقرير ({report_title}) بنجاح وهو متاح الآن.",
        notification_type="report",
        severity="success",
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        event_code="report_generated",
        event_group="report",
        source="services.notify_report_generated",
        context={"report_title": _clean_text(report_title)},
    )


# ============================================================
# 7️⃣ إشعارات المساعد الذكي
# ============================================================
def notify_smart_assistant(
    recipient: User,
    suggestion: str,
    send_email: bool = False,
    send_whatsapp: bool = False,
) -> Notification | None:
    return create_notification(
        recipient=recipient,
        title="🤖 تنبيه من المساعد الذكي",
        message=suggestion,
        notification_type="assistant",
        severity="info",
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        event_code="assistant_suggestion",
        event_group="assistant",
        source="services.notify_smart_assistant",
        context={"suggestion": _clean_text(suggestion)},
    )


# ============================================================
# 8️⃣ إشعار آمن لعدة مستلمين
# ============================================================
def notify_many(
    *,
    recipients: Iterable[User],
    title: str,
    message: str,
    notification_type: str = "system",
    severity: str = "info",
    send_email: bool = False,
    send_whatsapp: bool = False,
    link: str | None = None,
    company=None,
    event_code: str | None = None,
    event_group: str | None = None,
    actor: User | None = None,
    language_code: str = "ar",
    source: str | None = None,
    context: dict | None = None,
    target_object: Any | None = None,
    template_key: str | None = None,
) -> list[Notification]:
    """
    🧩 Helper إضافي لاستخدامه لاحقًا.
    """
    return dispatch_notification_event(
        recipients=recipients,
        title=title,
        message=message,
        notification_type=notification_type,
        severity=severity,
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        link=link,
        company=company,
        event_code=event_code or notification_type,
        event_group=event_group or notification_type,
        actor=actor,
        language_code=language_code,
        source=source or "services.notify_many",
        context=context,
        target_object=target_object,
        template_key=template_key,
    )


# ============================================================
# 9️⃣ Backward Compatibility Helpers
# ============================================================
def notify_company(
    *,
    recipient,
    title: str,
    message: str,
    notification_type: str = "company",
    severity: str = "info",
    send_email: bool = False,
    send_whatsapp: bool = False,
    link: str | None = None,
    company=None,
    event_code: str | None = None,
    event_group: str | None = "company",
    actor=None,
    language_code: str = "ar",
    source: str | None = None,
    context: dict | None = None,
    target_object=None,
    template_key: str | None = None,
):
    """
    توافق خلفي للمسارات القديمة التي كانت تستورد notify_company
    من notification_center.services.
    """
    return create_notification(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        severity=severity,
        send_email=send_email,
        send_whatsapp=send_whatsapp,
        link=link,
        company=company,
        event_code=event_code or notification_type,
        event_group=event_group or "company",
        actor=actor,
        target_user=recipient,
        language_code=language_code,
        source=source or "services.notify_company",
        context=context,
        target_object=target_object,
        template_key=template_key,
    )