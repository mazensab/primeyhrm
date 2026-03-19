# ============================================================
# 🔄 Renew Company Subscription
# Primey HR Cloud
# ============================================================

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.http import require_POST

from billing_center.models import (
    CompanySubscription,
    Invoice,
)
from whatsapp_center.models import ScopeType, TriggerSource
from whatsapp_center.services import send_event_whatsapp_message

VAT_RATE = Decimal("0.15")
logger = logging.getLogger(__name__)


# ============================================================
# 🖼️ Primey Email Branding
# نفس أسلوب reset password / system users
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
# 🧩 Helpers
# ============================================================

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


def _collect_recipients(subscription) -> list[str]:
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
            "Failed while collecting renewal email recipients. subscription_id=%s",
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


def _collect_whatsapp_targets(subscription) -> list[dict]:
    """
    تجميع مستهدفي الواتساب بشكل آمن وبدون تكرار.

    الأولوية:
    - جوال الشركة
    - جوال المالك
    - جوال أول admin / owner داخل الشركة
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
            "Failed while collecting renewal WhatsApp targets. subscription_id=%s",
            getattr(subscription, "id", None),
        )

    return targets


def _build_renewal_whatsapp_message(*, subscription, invoice, duration, subtotal, vat_amount, total) -> str:
    company = getattr(subscription, "company", None)
    plan = getattr(subscription, "plan", None)

    return (
        f"تم إنشاء فاتورة تجديد الاشتراك بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_text(getattr(company, 'name', None))}\n"
        f"الباقة: {_safe_text(getattr(plan, 'name', None))}\n"
        f"مدة التجديد: {_safe_text(duration)}\n"
        f"رقم الفاتورة: {_safe_text(getattr(invoice, 'invoice_number', None))}\n"
        f"تاريخ الإصدار: {_date_str(getattr(invoice, 'issue_date', None))}\n"
        f"السعر الأساسي: {_money_str(subtotal)} SAR\n"
        f"الضريبة: {_money_str(vat_amount)} SAR\n"
        f"الإجمالي: {_money_str(total)} SAR\n"
        f"الحالة: PENDING\n"
        f"نهاية الاشتراك الحالي: {_date_str(getattr(subscription, 'end_date', None))}\n\n"
        f"يمكنكم الآن متابعة السداد لإكمال التجديد."
    )


def _send_renewal_invoice_whatsapp(*, subscription, invoice, duration, subtotal, vat_amount, total) -> None:
    """
    إرسال إشعار واتساب عند إنشاء فاتورة التجديد.
    """
    company = getattr(subscription, "company", None)
    targets = _collect_whatsapp_targets(subscription)

    if not targets:
        logger.warning(
            "Renewal WhatsApp skipped: no phone targets found. subscription_id=%s invoice_id=%s",
            getattr(subscription, "id", None),
            getattr(invoice, "id", None),
        )
        return

    message_text = _build_renewal_whatsapp_message(
        subscription=subscription,
        invoice=invoice,
        duration=duration,
        subtotal=subtotal,
        vat_amount=vat_amount,
        total=total,
    )

    for target in targets:
        try:
            send_event_whatsapp_message(
                scope_type=ScopeType.COMPANY,
                company=company,
                event_code="subscription_renewal_invoice_created",
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
                    "plan_name": _safe_text(getattr(subscription.plan, "name", None)),
                    "duration": _safe_text(duration),
                    "invoice_number": _safe_text(getattr(invoice, "invoice_number", None)),
                    "amount": f"{_money_str(total)} SAR",
                    "status": "PENDING",
                },
            )
        except Exception:
            logger.exception(
                "Failed to send renewal WhatsApp. subscription_id=%s invoice_id=%s phone=%s",
                getattr(subscription, "id", None),
                getattr(invoice, "id", None),
                target.get("phone"),
            )


def _build_renewal_email_html(*, subscription, invoice, duration, subtotal, vat_amount, total) -> str:
    company = getattr(subscription, "company", None)
    plan = getattr(subscription, "plan", None)

    logo_url = escape(PRIMEY_EMAIL_LOGO_URL)
    company_name = escape(_safe_text(getattr(company, "name", None)))
    company_email = escape(_safe_text(getattr(company, "email", None)))
    company_phone = escape(_safe_text(getattr(company, "phone", None)))
    plan_name = escape(_safe_text(getattr(plan, "name", None)))
    duration_text = escape(_safe_text(duration))
    invoice_number = escape(_safe_text(getattr(invoice, "invoice_number", None)))
    issue_date = escape(_date_str(getattr(invoice, "issue_date", None)))
    current_end_date = escape(_date_str(getattr(subscription, "end_date", None)))
    subtotal_text = escape(_money_str(subtotal))
    vat_text = escape(_money_str(vat_amount))
    total_text = escape(_money_str(total))

    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>فاتورة تجديد الاشتراك</title>
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
                تم إنشاء فاتورة تجديد الاشتراك
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:32px 28px 20px 28px;">
              <div style="font-size:15px;color:#374151;line-height:2;">
                تم إنشاء فاتورة تجديد الاشتراك بنجاح. يمكنك الآن متابعة السداد لإكمال التجديد.
              </div>

              <div style="margin-top:22px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الشركة
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">اسم الشركة:</td><td style="padding:6px 0;">{company_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">البريد الإلكتروني:</td><td style="padding:6px 0;">{company_email}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الجوال:</td><td style="padding:6px 0;">{company_phone}</td></tr>
                </table>
              </div>

              <div style="margin-top:18px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الاشتراك
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">الباقة:</td><td style="padding:6px 0;">{plan_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">مدة التجديد:</td><td style="padding:6px 0;">{duration_text}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">نهاية الاشتراك الحالي:</td><td style="padding:6px 0;">{current_end_date}</td></tr>
                </table>
              </div>

              <div style="margin-top:18px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الفاتورة
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">رقم الفاتورة:</td><td style="padding:6px 0;">{invoice_number}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">تاريخ الإصدار:</td><td style="padding:6px 0;">{issue_date}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">السعر الأساسي:</td><td style="padding:6px 0;">{subtotal_text} SAR</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الضريبة:</td><td style="padding:6px 0;">{vat_text} SAR</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الإجمالي:</td><td style="padding:6px 0;">{total_text} SAR</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الحالة:</td><td style="padding:6px 0;">PENDING</td></tr>
                </table>
              </div>

              <div style="margin-top:22px;font-size:14px;color:#6b7280;line-height:2;">
                هذه الرسالة للتأكيد فقط بأنه تم إصدار فاتورة التجديد بنجاح داخل النظام.
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


def _send_renewal_invoice_email(*, subscription, invoice, duration, subtotal, vat_amount, total) -> None:
    recipients = _collect_recipients(subscription)

    if not recipients:
        logger.warning(
            "Renewal invoice email skipped: no recipients found. subscription_id=%s invoice_id=%s",
            getattr(subscription, "id", None),
            getattr(invoice, "id", None),
        )
        return

    company = getattr(subscription, "company", None)
    plan = getattr(subscription, "plan", None)

    subject = f"فاتورة تجديد الاشتراك - {_safe_text(getattr(company, 'name', None), 'Company')}"

    text_body = (
        f"تم إنشاء فاتورة تجديد الاشتراك بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_text(getattr(company, 'name', None))}\n"
        f"الباقة: {_safe_text(getattr(plan, 'name', None))}\n"
        f"مدة التجديد: {_safe_text(duration)}\n"
        f"رقم الفاتورة: {_safe_text(getattr(invoice, 'invoice_number', None))}\n"
        f"تاريخ الإصدار: {_date_str(getattr(invoice, 'issue_date', None))}\n"
        f"السعر الأساسي: {_money_str(subtotal)} SAR\n"
        f"الضريبة: {_money_str(vat_amount)} SAR\n"
        f"الإجمالي: {_money_str(total)} SAR\n"
        f"الحالة: PENDING\n\n"
        f"مع تحيات Primey HR Cloud"
    )

    html_body = _build_renewal_email_html(
        subscription=subscription,
        invoice=invoice,
        duration=duration,
        subtotal=subtotal,
        vat_amount=vat_amount,
        total=total,
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
            "Renewal invoice email sent successfully. subscription_id=%s invoice_id=%s recipients=%s",
            getattr(subscription, "id", None),
            getattr(invoice, "id", None),
            recipients,
        )

    except Exception:
        logger.exception(
            "Failed to send renewal invoice email. subscription_id=%s invoice_id=%s",
            getattr(subscription, "id", None),
            getattr(invoice, "id", None),
        )


@require_POST
def renew_subscription(request, subscription_id):

    # ------------------------------------------------
    # Action Type (future support)
    # ------------------------------------------------
    action = request.POST.get("action", "RENEWAL")
    duration = request.POST.get("duration", "monthly")

    with transaction.atomic():
        subscription = get_object_or_404(
            CompanySubscription.objects.select_related("company__owner", "plan"),
            id=subscription_id
        )

        company = subscription.company
        plan = subscription.plan

        # ------------------------------------------------
        # Safety Guard
        # ------------------------------------------------
        active = CompanySubscription.objects.filter(
            company=company,
            status="ACTIVE"
        ).exclude(id=subscription.id).exists()

        if active:
            return JsonResponse({
                "error": "Company already has active subscription"
            }, status=400)

        # ------------------------------------------------
        # Prevent duplicate renewal invoice
        # ------------------------------------------------
        existing_invoice = Invoice.objects.filter(
            subscription=subscription,
            billing_reason="RENEWAL",
            status="PENDING"
        ).first()

        if existing_invoice:
            return JsonResponse({
                "error": "Renewal invoice already exists",
                "invoice_id": existing_invoice.id
            }, status=400)

        # ------------------------------------------------
        # Calculate Price
        # ------------------------------------------------
        if duration == "yearly":
            price = plan.price_yearly
        else:
            price = plan.price_monthly

        vat_amount = price * VAT_RATE
        total = price + vat_amount

        # ------------------------------------------------
        # Create Invoice
        # ------------------------------------------------
        invoice = Invoice.objects.create(
            company=company,
            subscription=subscription,
            invoice_number=f"INV-R-{int(timezone.now().timestamp())}",
            issue_date=timezone.now().date(),
            subtotal_amount=price,
            total_amount=total,
            billing_reason=action,
            status="PENDING",
        )

        # ------------------------------------------------
        # ✉️ Send Email After Successful Commit
        # ------------------------------------------------
        transaction.on_commit(
            lambda: _send_renewal_invoice_email(
                subscription=subscription,
                invoice=invoice,
                duration=duration,
                subtotal=price,
                vat_amount=vat_amount,
                total=total,
            )
        )

        # ------------------------------------------------
        # 📲 Send WhatsApp After Successful Commit
        # ------------------------------------------------
        transaction.on_commit(
            lambda: _send_renewal_invoice_whatsapp(
                subscription=subscription,
                invoice=invoice,
                duration=duration,
                subtotal=price,
                vat_amount=vat_amount,
                total=total,
            )
        )

    return JsonResponse({
        "success": True,
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number
    })