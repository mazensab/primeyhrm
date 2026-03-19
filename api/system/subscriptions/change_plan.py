# ============================================================
# 📂 api/system/subscriptions/change_plan.py
# Primey HR Cloud
# Change Subscription Plan API
# ============================================================

from __future__ import annotations

import json
import logging
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.http import require_POST

from billing_center.models import (
    CompanySubscription,
    SubscriptionPlan,
    Invoice,
)
from whatsapp_center.models import ScopeType, TriggerSource
from whatsapp_center.services import send_event_whatsapp_message

logger = logging.getLogger(__name__)


# ============================================================
# 🖼️ Primey Email Branding
# ============================================================

PRIMEY_EMAIL_LOGO_URL = getattr(
    settings,
    "PRIMEY_EMAIL_LOGO_URL",
    getattr(
        settings,
        "EMAIL_LOGO_URL",
        "https://drive.google.com/uc?export=view&id=1x2Q9wJm8QmQm7mYjQmW7aJmR8bPlogoblak",
    ),
)

DEFAULT_FROM_EMAIL = getattr(
    settings,
    "DEFAULT_FROM_EMAIL",
    getattr(settings, "EMAIL_HOST_USER", "no-reply@primeyhr.com"),
)


# ============================================================
# Helpers
# ============================================================

def _json_payload(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


def _safe_text(value, default="-"):
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def _money_str(value) -> str:
    try:
        return f"{Decimal(value):.2f}"
    except Exception:
        return "0.00"


def _date_str(value) -> str:
    if not value:
        return "-"
    try:
        return value.strftime("%Y-%m-%d")
    except Exception:
        return str(value)


def _generate_upgrade_invoice_number() -> str:
    """
    توليد رقم فاتورة فريد لطلبات ترقية الباقة
    """
    while True:
        candidate = (
            f"INV-UPG-"
            f"{timezone.now().strftime('%Y%m%d%H%M%S')}-"
            f"{uuid4().hex[:6].upper()}"
        )
        if not Invoice.objects.filter(invoice_number=candidate).exists():
            return candidate


def _collect_subscription_recipients(subscription) -> list[str]:
    recipients: list[str] = []

    company = getattr(subscription, "company", None)
    owner = getattr(company, "owner", None) if company else None

    candidates = [
        getattr(company, "email", None),
        getattr(owner, "email", None),
    ]

    try:
        admin_link = (
            company.company_users
            .select_related("user")
            .filter(is_active=True, role__in=["admin", "owner"])
            .order_by("id")
            .first()
        ) if company else None

        if admin_link and admin_link.user and admin_link.user.email:
            candidates.append(admin_link.user.email)
    except Exception:
        logger.exception(
            "Failed while collecting subscription email recipients. subscription_id=%s",
            getattr(subscription, "id", None),
        )

    for value in candidates:
        email = _safe_text(value, "").lower()
        if email and email not in recipients:
            recipients.append(email)

    return recipients


def _get_first_existing_attr(instance, attr_names: list[str], default=""):
    """
    قراءة أول حقل موجود وغير فارغ من قائمة أسماء محتملة.
    مفيد لاختلاف تسمية حقول الجوال بين النماذج.
    """
    if not instance:
        return default

    for attr_name in attr_names:
        try:
            value = getattr(instance, attr_name, None)
        except Exception:
            value = None

        value = _safe_text(value, "")
        if value:
            return value

    return default


def _collect_subscription_whatsapp_targets(subscription) -> list[dict]:
    """
    تجميع مستهدفي الواتساب بشكل آمن وبدون تكرار.

    الأولوية:
    - جوال الشركة
    - جوال المالك
    - جوال أول admin/owner داخل الشركة
    """
    targets: list[dict] = []
    seen_phones: set[str] = set()

    company = getattr(subscription, "company", None)
    owner = getattr(company, "owner", None) if company else None

    def _append_target(phone, name="", role=""):
        phone = _safe_text(phone, "")
        if not phone:
            return
        if phone in seen_phones:
            return

        seen_phones.add(phone)
        targets.append({
            "phone": phone,
            "name": _safe_text(name, "User"),
            "role": _safe_text(role, ""),
        })

    company_phone = _get_first_existing_attr(
        company,
        ["phone", "mobile", "mobile_number", "whatsapp_number"],
        "",
    )
    _append_target(
        company_phone,
        name=getattr(company, "name", None),
        role="company",
    )

    owner_phone = _get_first_existing_attr(
        owner,
        ["phone", "mobile", "mobile_number", "whatsapp_number"],
        "",
    )
    owner_name = _safe_text(
        getattr(owner, "first_name", None) or getattr(owner, "username", None),
        "Owner",
    )
    _append_target(
        owner_phone,
        name=owner_name,
        role="owner",
    )

    try:
        admin_link = (
            company.company_users
            .select_related("user")
            .filter(is_active=True, role__in=["admin", "owner"])
            .order_by("id")
            .first()
        ) if company else None

        admin_user = getattr(admin_link, "user", None) if admin_link else None
        admin_phone = _get_first_existing_attr(
            admin_user,
            ["phone", "mobile", "mobile_number", "whatsapp_number"],
            "",
        )
        admin_name = _safe_text(
            getattr(admin_user, "first_name", None) or getattr(admin_user, "username", None),
            "Admin",
        )
        _append_target(
            admin_phone,
            name=admin_name,
            role=getattr(admin_link, "role", "admin") if admin_link else "admin",
        )
    except Exception:
        logger.exception(
            "Failed while collecting subscription WhatsApp targets. subscription_id=%s",
            getattr(subscription, "id", None),
        )

    return targets


def _build_upgrade_whatsapp_message(*, subscription, current_plan, new_plan, invoice, difference) -> str:
    company = getattr(subscription, "company", None)

    return (
        f"تم إنشاء طلب ترقية الباقة بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_text(getattr(company, 'name', None))}\n"
        f"الباقة الحالية: {_safe_text(getattr(current_plan, 'name', None))}\n"
        f"الباقة الجديدة: {_safe_text(getattr(new_plan, 'name', None))}\n"
        f"المبلغ المستحق: {_money_str(difference)} SAR\n"
        f"رقم الفاتورة: {_safe_text(getattr(invoice, 'invoice_number', None))}\n"
        f"الحالة: PENDING\n"
        f"تاريخ البداية: {_date_str(getattr(subscription, 'start_date', None))}\n"
        f"تاريخ النهاية: {_date_str(getattr(subscription, 'end_date', None))}\n\n"
        f"سيتم استكمال الترقية بعد سداد فاتورة فرق السعر."
    )


def _build_downgrade_whatsapp_message(*, subscription, current_plan, new_plan) -> str:
    company = getattr(subscription, "company", None)

    return (
        f"تم استلام طلب تخفيض الباقة داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_text(getattr(company, 'name', None))}\n"
        f"الباقة الحالية: {_safe_text(getattr(current_plan, 'name', None))}\n"
        f"الباقة المطلوبة: {_safe_text(getattr(new_plan, 'name', None))}\n"
        f"تاريخ البداية الحالي: {_date_str(getattr(subscription, 'start_date', None))}\n"
        f"تاريخ انتهاء الاشتراك الحالي: {_date_str(getattr(subscription, 'end_date', None))}\n\n"
        f"هذا المسار يحتاج طبقة حفظ رسمية قبل تطبيقه عند موعد التجديد القادم."
    )


def _send_upgrade_whatsapp(*, subscription, current_plan, new_plan, invoice, difference) -> None:
    """
    إرسال إشعار واتساب عند إنشاء فاتورة ترقية الباقة.
    لا يؤثر فشل الواتساب على التدفق الأساسي.
    """
    company = getattr(subscription, "company", None)
    targets = _collect_subscription_whatsapp_targets(subscription)

    if not targets:
        logger.warning(
            "Upgrade WhatsApp skipped: no phone targets found. subscription_id=%s",
            getattr(subscription, "id", None),
        )
        return

    message_text = _build_upgrade_whatsapp_message(
        subscription=subscription,
        current_plan=current_plan,
        new_plan=new_plan,
        invoice=invoice,
        difference=difference,
    )

    for target in targets:
        try:
            send_event_whatsapp_message(
                scope_type=ScopeType.COMPANY,
                company=company,
                event_code="subscription_plan_upgrade_created",
                recipient_phone=target["phone"],
                recipient_name=target["name"],
                recipient_role=target["role"],
                trigger_source=TriggerSource.SYSTEM,
                language_code="ar",
                related_model="Invoice",
                related_object_id=str(getattr(invoice, "id", "")),
                context={
                    "message": message_text,
                    "company_name": _safe_text(getattr(company, "name", None)),
                    "recipient_name": target["name"],
                    "current_plan_name": _safe_text(getattr(current_plan, "name", None)),
                    "new_plan_name": _safe_text(getattr(new_plan, "name", None)),
                    "invoice_number": _safe_text(getattr(invoice, "invoice_number", None)),
                    "amount": f"{_money_str(difference)} SAR",
                    "status": "PENDING",
                },
            )
        except Exception:
            logger.exception(
                "Failed to send upgrade WhatsApp. subscription_id=%s invoice_id=%s phone=%s",
                getattr(subscription, "id", None),
                getattr(invoice, "id", None),
                target.get("phone"),
            )


def _send_downgrade_whatsapp(*, subscription, current_plan, new_plan) -> None:
    """
    إرسال إشعار واتساب عند طلب تخفيض الباقة.
    """
    company = getattr(subscription, "company", None)
    targets = _collect_subscription_whatsapp_targets(subscription)

    if not targets:
        logger.warning(
            "Downgrade WhatsApp skipped: no phone targets found. subscription_id=%s",
            getattr(subscription, "id", None),
        )
        return

    message_text = _build_downgrade_whatsapp_message(
        subscription=subscription,
        current_plan=current_plan,
        new_plan=new_plan,
    )

    for target in targets:
        try:
            send_event_whatsapp_message(
                scope_type=ScopeType.COMPANY,
                company=company,
                event_code="subscription_plan_downgrade_requested",
                recipient_phone=target["phone"],
                recipient_name=target["name"],
                recipient_role=target["role"],
                trigger_source=TriggerSource.SYSTEM,
                language_code="ar",
                related_model="CompanySubscription",
                related_object_id=str(getattr(subscription, "id", "")),
                context={
                    "message": message_text,
                    "company_name": _safe_text(getattr(company, "name", None)),
                    "recipient_name": target["name"],
                    "current_plan_name": _safe_text(getattr(current_plan, "name", None)),
                    "new_plan_name": _safe_text(getattr(new_plan, "name", None)),
                },
            )
        except Exception:
            logger.exception(
                "Failed to send downgrade WhatsApp. subscription_id=%s phone=%s",
                getattr(subscription, "id", None),
                target.get("phone"),
            )


def _build_upgrade_email_html(*, subscription, current_plan, new_plan, invoice, difference) -> str:
    company = getattr(subscription, "company", None)

    logo_url = escape(PRIMEY_EMAIL_LOGO_URL)
    company_name = escape(_safe_text(getattr(company, "name", None)))
    company_email = escape(_safe_text(getattr(company, "email", None)))
    current_plan_name = escape(_safe_text(getattr(current_plan, "name", None)))
    new_plan_name = escape(_safe_text(getattr(new_plan, "name", None)))
    invoice_id = escape(_safe_text(getattr(invoice, "id", None)))
    invoice_number = escape(_safe_text(getattr(invoice, "invoice_number", None)))
    invoice_total = escape(_money_str(difference))
    start_date = escape(_date_str(getattr(subscription, "start_date", None)))
    end_date = escape(_date_str(getattr(subscription, "end_date", None)))

    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>طلب ترقية الباقة</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f7fb;font-family:Tahoma,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f7fb;margin:0;padding:24px 0;">
    <tr>
      <td align="center">
        <table width="680" cellpadding="0" cellspacing="0"
               style="max-width:680px;width:100%;background:#ffffff;border-radius:18px;overflow:hidden;border:1px solid #e5e7eb;">

          <tr>
            <td align="center" style="background:#000000;padding:28px 24px;">
              <img src="{logo_url}" alt="Primey"
                   style="max-height:56px;width:auto;display:block;margin:0 auto 12px auto;" />
              <div style="color:#ffffff;font-size:22px;font-weight:700;line-height:1.6;">
                Primey HR Cloud
              </div>
              <div style="color:#d1d5db;font-size:14px;line-height:1.8;">
                تم إنشاء طلب ترقية الباقة
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:32px 28px 20px 28px;">
              <div style="font-size:15px;color:#374151;line-height:2;">
                تم إنشاء طلب ترقية باقة الشركة بنجاح، وتم إصدار فاتورة بالمبلغ المستحق للترقية.
              </div>

              <div style="margin-top:22px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الشركة والاشتراك
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">اسم الشركة:</td><td style="padding:6px 0;">{company_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">البريد الإلكتروني:</td><td style="padding:6px 0;">{company_email}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الباقة الحالية:</td><td style="padding:6px 0;">{current_plan_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الباقة الجديدة:</td><td style="padding:6px 0;">{new_plan_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">تاريخ البداية:</td><td style="padding:6px 0;">{start_date}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">تاريخ النهاية:</td><td style="padding:6px 0;">{end_date}</td></tr>
                </table>
              </div>

              <div style="margin-top:18px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الفاتورة
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">رقم الفاتورة الداخلي:</td><td style="padding:6px 0;">{invoice_id}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">رقم الفاتورة:</td><td style="padding:6px 0;">{invoice_number}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">المبلغ المستحق:</td><td style="padding:6px 0;">{invoice_total} SAR</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الحالة:</td><td style="padding:6px 0;">PENDING</td></tr>
                </table>
              </div>

              <div style="margin-top:22px;font-size:14px;color:#6b7280;line-height:2;">
                سيتم استكمال الترقية بعد سداد الفاتورة الناتجة عن فرق السعر.
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:20px 28px 30px 28px;">
              <div style="border-top:1px solid #e5e7eb;padding-top:18px;font-size:12px;color:#9ca3af;line-height:1.9;text-align:center;">
                هذه رسالة آلية من Primey HR Cloud — يرجى عدم الرد عليها مباشرة.
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


def _build_downgrade_email_html(*, subscription, current_plan, new_plan) -> str:
    company = getattr(subscription, "company", None)

    logo_url = escape(PRIMEY_EMAIL_LOGO_URL)
    company_name = escape(_safe_text(getattr(company, "name", None)))
    company_email = escape(_safe_text(getattr(company, "email", None)))
    current_plan_name = escape(_safe_text(getattr(current_plan, "name", None)))
    new_plan_name = escape(_safe_text(getattr(new_plan, "name", None)))
    start_date = escape(_date_str(getattr(subscription, "start_date", None)))
    end_date = escape(_date_str(getattr(subscription, "end_date", None)))

    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>جدولة تخفيض الباقة</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f7fb;font-family:Tahoma,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f7fb;margin:0;padding:24px 0;">
    <tr>
      <td align="center">
        <table width="680" cellpadding="0" cellspacing="0"
               style="max-width:680px;width:100%;background:#ffffff;border-radius:18px;overflow:hidden;border:1px solid #e5e7eb;">

          <tr>
            <td align="center" style="background:#000000;padding:28px 24px;">
              <img src="{logo_url}" alt="Primey"
                   style="max-height:56px;width:auto;display:block;margin:0 auto 12px auto;" />
              <div style="color:#ffffff;font-size:22px;font-weight:700;line-height:1.6;">
                Primey HR Cloud
              </div>
              <div style="color:#d1d5db;font-size:14px;line-height:1.8;">
                تم جدولة تغيير الباقة
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:32px 28px 20px 28px;">
              <div style="font-size:15px;color:#374151;line-height:2;">
                تم استلام طلب تخفيض الباقة، لكن هذا المسار يحتاج طبقة تخزين رسمية قبل التفعيل عند موعد التجديد القادم.
              </div>

              <div style="margin-top:22px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الشركة والاشتراك
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">اسم الشركة:</td><td style="padding:6px 0;">{company_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">البريد الإلكتروني:</td><td style="padding:6px 0;">{company_email}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الباقة الحالية:</td><td style="padding:6px 0;">{current_plan_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الباقة المطلوبة:</td><td style="padding:6px 0;">{new_plan_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">تاريخ البداية الحالي:</td><td style="padding:6px 0;">{start_date}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">تاريخ انتهاء الاشتراك الحالي:</td><td style="padding:6px 0;">{end_date}</td></tr>
                </table>
              </div>

              <div style="margin-top:22px;font-size:14px;color:#6b7280;line-height:2;">
                يلزم لاحقًا ربط هذا التدفق بطبقة حفظ رسمية لجدولة التخفيض.
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:20px 28px 30px 28px;">
              <div style="border-top:1px solid #e5e7eb;padding-top:18px;font-size:12px;color:#9ca3af;line-height:1.9;text-align:center;">
                هذه رسالة آلية من Primey HR Cloud — يرجى عدم الرد عليها مباشرة.
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


def _send_upgrade_email(*, subscription, current_plan, new_plan, invoice, difference) -> None:
    recipients = _collect_subscription_recipients(subscription)

    if not recipients:
        logger.warning(
            "Upgrade email skipped: no recipients found. subscription_id=%s",
            getattr(subscription, "id", None),
        )
        return

    company = getattr(subscription, "company", None)

    subject = f"طلب ترقية الباقة - {_safe_text(getattr(company, 'name', None), 'Company')}"

    text_body = (
        f"تم إنشاء طلب ترقية الباقة بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_text(getattr(company, 'name', None))}\n"
        f"الباقة الحالية: {_safe_text(getattr(current_plan, 'name', None))}\n"
        f"الباقة الجديدة: {_safe_text(getattr(new_plan, 'name', None))}\n"
        f"المبلغ المستحق: {_money_str(difference)} SAR\n"
        f"رقم الفاتورة الداخلي: {_safe_text(getattr(invoice, 'id', None))}\n"
        f"رقم الفاتورة: {_safe_text(getattr(invoice, 'invoice_number', None))}\n"
        f"الحالة: PENDING\n\n"
        f"مع تحيات Primey HR Cloud"
    )

    html_body = _build_upgrade_email_html(
        subscription=subscription,
        current_plan=current_plan,
        new_plan=new_plan,
        invoice=invoice,
        difference=difference,
    )

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)

        logger.info(
            "Upgrade email sent successfully. subscription_id=%s recipients=%s",
            getattr(subscription, "id", None),
            recipients,
        )

    except Exception:
        logger.exception(
            "Failed to send upgrade email. subscription_id=%s",
            getattr(subscription, "id", None),
        )


def _send_downgrade_email(*, subscription, current_plan, new_plan) -> None:
    recipients = _collect_subscription_recipients(subscription)

    if not recipients:
        logger.warning(
            "Downgrade email skipped: no recipients found. subscription_id=%s",
            getattr(subscription, "id", None),
        )
        return

    company = getattr(subscription, "company", None)

    subject = f"طلب تخفيض الباقة - {_safe_text(getattr(company, 'name', None), 'Company')}"

    text_body = (
        f"تم استلام طلب تخفيض الباقة داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_text(getattr(company, 'name', None))}\n"
        f"الباقة الحالية: {_safe_text(getattr(current_plan, 'name', None))}\n"
        f"الباقة المطلوبة: {_safe_text(getattr(new_plan, 'name', None))}\n\n"
        f"هذا التدفق يحتاج طبقة حفظ رسمية قبل تطبيقه عند موعد التجديد.\n\n"
        f"مع تحيات Primey HR Cloud"
    )

    html_body = _build_downgrade_email_html(
        subscription=subscription,
        current_plan=current_plan,
        new_plan=new_plan,
    )

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)

        logger.info(
            "Downgrade email sent successfully. subscription_id=%s recipients=%s",
            getattr(subscription, "id", None),
            recipients,
        )

    except Exception:
        logger.exception(
            "Failed to send downgrade email. subscription_id=%s",
            getattr(subscription, "id", None),
        )


# ============================================================
# API
# POST /api/system/subscriptions/<id>/change-plan/
# ============================================================

@require_POST
@login_required
@transaction.atomic
def change_subscription_plan(request, subscription_id):

    payload = _json_payload(request)

    if not payload:
        return JsonResponse({
            "error": "Invalid payload"
        }, status=400)

    plan_id = payload.get("plan_id")

    if not plan_id:
        return JsonResponse({
            "error": "plan_id required"
        }, status=400)

    try:
        subscription = (
            CompanySubscription.objects
            .select_for_update()
            .select_related("company__owner", "plan")
            .get(id=subscription_id)
        )
    except CompanySubscription.DoesNotExist:
        return JsonResponse({
            "error": "Subscription not found"
        }, status=404)

    try:
        new_plan = SubscriptionPlan.objects.get(id=plan_id)
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({
            "error": "Plan not found"
        }, status=404)

    current_plan = subscription.plan

    # --------------------------------------------------------
    # Same Plan
    # --------------------------------------------------------

    if current_plan.id == new_plan.id:
        return JsonResponse({
            "message": "Already on this plan"
        })

    current_price = current_plan.price_yearly or 0
    new_price = new_plan.price_yearly or 0

    # --------------------------------------------------------
    # Upgrade
    # --------------------------------------------------------

    if new_price > current_price:

        difference = Decimal(new_price) - Decimal(current_price)

        invoice = Invoice.objects.create(
            company=subscription.company,
            subscription=subscription,
            invoice_number=_generate_upgrade_invoice_number(),
            subtotal_amount=difference,
            total_after_discount=difference,
            total_amount=difference,
            billing_reason="UPGRADE",
            status="PENDING",
            subscription_snapshot={
                "type": "UPGRADE",
                "subscription_id": subscription.id,
                "current_plan": {
                    "id": current_plan.id,
                    "name": current_plan.name,
                    "price_yearly": str(current_plan.price_yearly or 0),
                },
                "target_plan": {
                    "id": new_plan.id,
                    "name": new_plan.name,
                    "price_yearly": str(new_plan.price_yearly or 0),
                },
                "difference": str(difference),
            },
        )

        transaction.on_commit(
            lambda: _send_upgrade_email(
                subscription=subscription,
                current_plan=current_plan,
                new_plan=new_plan,
                invoice=invoice,
                difference=difference,
            )
        )

        transaction.on_commit(
            lambda: _send_upgrade_whatsapp(
                subscription=subscription,
                current_plan=current_plan,
                new_plan=new_plan,
                invoice=invoice,
                difference=difference,
            )
        )

        return JsonResponse({
            "action": "upgrade",
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "amount_due": str(difference)
        })

    # --------------------------------------------------------
    # Downgrade
    # --------------------------------------------------------

    transaction.on_commit(
        lambda: _send_downgrade_email(
            subscription=subscription,
            current_plan=current_plan,
            new_plan=new_plan,
        )
    )

    transaction.on_commit(
        lambda: _send_downgrade_whatsapp(
            subscription=subscription,
            current_plan=current_plan,
            new_plan=new_plan,
        )
    )

    return JsonResponse({
        "action": "downgrade_not_supported_yet",
        "message": "Downgrade scheduling requires a dedicated storage layer first."
    })