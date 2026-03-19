# ====================================================================
# 💳 Confirm Cash Payment — FINAL ULTRA STABLE
# Primey HR Cloud | Super Admin Only
# ====================================================================
# ✔ Confirm manual CASH payment
# ✔ Invoice -> PAID
# ✔ Subscription -> ACTIVE
# ✔ Company -> ACTIVE (AUTO RULE after first successful payment)
# ✔ Upgrade Flow Supported
# ✔ Idempotent & Transaction-safe
# ✔ Payment Confirmation Email
# ✔ Invoice PDF Attachment
# ✔ WhatsApp Confirmation After Successful Commit
# ====================================================================

from __future__ import annotations

import json
import logging
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.http import JsonResponse
from django.utils.html import escape
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing_center.models import (
    Invoice,
    Payment,
    CompanySubscription,
    SubscriptionPlan,
)
from whatsapp_center.models import ScopeType, TriggerSource
from whatsapp_center.services import send_event_whatsapp_message

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


def _build_invoice_recipients(invoice) -> list[str]:
    """
    تحديد المستلمين بدون تكرار:
    - company.email
    - company.owner.email
    - أول admin داخل الشركة
    """
    recipients: list[str] = []

    company = getattr(invoice, "company", None)
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
            "Failed while building invoice recipients. invoice_id=%s",
            getattr(invoice, "id", None),
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


def _collect_invoice_whatsapp_targets(invoice) -> list[dict]:
    """
    تجميع مستهدفي الواتساب بشكل آمن وبدون تكرار.

    الأولوية:
    - جوال الشركة
    - جوال المالك
    - جوال أول admin/owner داخل الشركة
    """
    targets: list[dict] = []
    seen_phones: set[str] = set()

    company = getattr(invoice, "company", None)
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
            "Failed while collecting invoice WhatsApp targets. invoice_id=%s",
            getattr(invoice, "id", None),
        )

    return targets


def _generate_invoice_pdf_bytes(*, invoice, payment, subscription) -> bytes | None:
    """
    إنشاء PDF بسيط للفـاتورة.
    إذا تعذر إنشاء الـ PDF لا نفشل عملية الدفع.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = height - 50

        company = getattr(invoice, "company", None)

        pdf.setTitle(f"Invoice {invoice.invoice_number}")

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(40, y, "Primey HR Cloud")
        y -= 28

        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(40, y, "Invoice Payment Confirmation")
        y -= 28

        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, y, f"Invoice Number: {_safe_text(invoice.invoice_number)}")
        y -= 18
        pdf.drawString(40, y, f"Company: {_safe_text(getattr(company, 'name', None))}")
        y -= 18
        pdf.drawString(40, y, f"Issue Date: {_date_str(getattr(invoice, 'issue_date', None))}")
        y -= 18
        pdf.drawString(40, y, f"Status: {_safe_text(getattr(invoice, 'status', None))}")
        y -= 18
        pdf.drawString(40, y, f"Payment Method: {_safe_text(getattr(payment, 'method', None))}")
        y -= 18
        pdf.drawString(40, y, f"Paid At: {_date_str(getattr(payment, 'paid_at', None))}")
        y -= 28

        subtotal_value = (
            getattr(invoice, "subtotal_amount", None)
            if hasattr(invoice, "subtotal_amount")
            else getattr(invoice, "subtotal", None)
        )
        vat_value = getattr(invoice, "vat", None)
        total_value = getattr(invoice, "total_amount", None)

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, "Totals")
        y -= 22

        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, y, f"Subtotal: {_money_str(subtotal_value)} SAR")
        y -= 18
        pdf.drawString(40, y, f"VAT: {_money_str(vat_value)} SAR")
        y -= 18
        pdf.drawString(40, y, f"Total: {_money_str(total_value)} SAR")
        y -= 28

        if subscription:
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(40, y, "Subscription")
            y -= 22

            pdf.setFont("Helvetica", 10)
            pdf.drawString(40, y, f"Plan: {_safe_text(getattr(getattr(subscription, 'plan', None), 'name', None))}")
            y -= 18
            pdf.drawString(40, y, f"Status: {_safe_text(getattr(subscription, 'status', None))}")
            y -= 18
            pdf.drawString(40, y, f"Start Date: {_date_str(getattr(subscription, 'start_date', None))}")
            y -= 18
            pdf.drawString(40, y, f"End Date: {_date_str(getattr(subscription, 'end_date', None))}")
            y -= 24

        pdf.setFont("Helvetica-Oblique", 9)
        pdf.drawString(40, y, "Generated automatically by Primey HR Cloud.")

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        return buffer.getvalue()

    except Exception:
        logger.exception(
            "Failed to generate invoice PDF. invoice_id=%s",
            getattr(invoice, "id", None),
        )
        return None


def _build_cash_payment_whatsapp_message(*, invoice, payment, subscription) -> str:
    company = getattr(invoice, "company", None)

    subtotal_value = (
        getattr(invoice, "subtotal_amount", None)
        if hasattr(invoice, "subtotal_amount")
        else getattr(invoice, "subtotal", None)
    )
    vat_value = getattr(invoice, "vat", None)
    total_value = getattr(invoice, "total_amount", None)

    return (
        f"تم تأكيد الدفع النقدي بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_text(getattr(company, 'name', None))}\n"
        f"رقم الفاتورة: {_safe_text(getattr(invoice, 'invoice_number', None))}\n"
        f"تاريخ الإصدار: {_date_str(getattr(invoice, 'issue_date', None))}\n"
        f"تاريخ الدفع: {_date_str(getattr(payment, 'paid_at', None))}\n"
        f"طريقة الدفع: CASH\n"
        f"الباقة: {_safe_text(getattr(getattr(subscription, 'plan', None), 'name', None)) if subscription else '-'}\n"
        f"حالة الاشتراك: {_safe_text(getattr(subscription, 'status', None)) if subscription else '-'}\n"
        f"Subtotal: {_money_str(subtotal_value)} SAR\n"
        f"VAT: {_money_str(vat_value)} SAR\n"
        f"الإجمالي: {_money_str(total_value)} SAR\n\n"
        f"تم تحديث حالة الفاتورة والاشتراك بنجاح."
    )


def _send_cash_payment_confirmation_whatsapp(*, invoice, payment, subscription) -> None:
    """
    إرسال إشعار واتساب بعد نجاح الدفع النقدي.
    """
    company = getattr(invoice, "company", None)
    targets = _collect_invoice_whatsapp_targets(invoice)

    if not targets:
        logger.warning(
            "Cash payment WhatsApp skipped: no phone targets found. invoice_id=%s",
            getattr(invoice, "id", None),
        )
        return

    subtotal_value = (
        getattr(invoice, "subtotal_amount", None)
        if hasattr(invoice, "subtotal_amount")
        else getattr(invoice, "subtotal", None)
    )
    vat_value = getattr(invoice, "vat", None)
    total_value = getattr(invoice, "total_amount", None)

    message_text = _build_cash_payment_whatsapp_message(
        invoice=invoice,
        payment=payment,
        subscription=subscription,
    )

    for target in targets:
        try:
            send_event_whatsapp_message(
                scope_type=ScopeType.COMPANY,
                company=company,
                event_code="cash_payment_confirmed",
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
                    "invoice_number": _safe_text(getattr(invoice, "invoice_number", None)),
                    "payment_method": "CASH",
                    "amount": f"{_money_str(total_value)} SAR",
                    "subtotal": f"{_money_str(subtotal_value)} SAR",
                    "vat": f"{_money_str(vat_value)} SAR",
                    "status": _safe_text(getattr(subscription, "status", None)) if subscription else "-",
                    "plan_name": _safe_text(getattr(getattr(subscription, "plan", None), "name", None)) if subscription else "-",
                },
            )
        except Exception:
            logger.exception(
                "Failed to send cash payment WhatsApp. invoice_id=%s phone=%s",
                getattr(invoice, "id", None),
                target.get("phone"),
            )


def _build_cash_payment_email_html(*, invoice, payment, subscription) -> str:
    company = getattr(invoice, "company", None)
    owner = getattr(company, "owner", None) if company else None

    logo_url = escape(PRIMEY_EMAIL_LOGO_URL)

    company_name = escape(_safe_text(getattr(company, "name", None)))
    company_email = escape(_safe_text(getattr(company, "email", None)))
    company_phone = escape(_safe_text(getattr(company, "phone", None)))
    commercial_number = escape(_safe_text(getattr(company, "commercial_number", None)))
    city = escape(_safe_text(getattr(company, "city", None)))
    owner_email = escape(_safe_text(getattr(owner, "email", None)))

    plan_name = escape(_safe_text(getattr(getattr(subscription, "plan", None), "name", None))) if subscription else "-"
    subscription_status = escape(_safe_text(getattr(subscription, "status", None))) if subscription else "-"
    start_date = escape(_date_str(getattr(subscription, "start_date", None))) if subscription else "-"
    end_date = escape(_date_str(getattr(subscription, "end_date", None))) if subscription else "-"

    invoice_number = escape(_safe_text(getattr(invoice, "invoice_number", None)))
    issue_date = escape(_date_str(getattr(invoice, "issue_date", None)))
    paid_at = escape(_date_str(getattr(payment, "paid_at", None)))

    subtotal_value = (
        getattr(invoice, "subtotal_amount", None)
        if hasattr(invoice, "subtotal_amount")
        else getattr(invoice, "subtotal", None)
    )
    vat_value = getattr(invoice, "vat", None)
    total_value = getattr(invoice, "total_amount", None)

    subtotal = escape(_money_str(subtotal_value))
    vat = escape(_money_str(vat_value))
    total = escape(_money_str(total_value))

    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>تأكيد الدفع النقدي</title>
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
                تم تأكيد الدفع النقدي بنجاح
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:32px 28px 20px 28px;">
              <div style="font-size:16px;color:#111827;line-height:2;">
                تم تسجيل عملية الدفع وتحديث حالة الفاتورة والاشتراك بنجاح.
              </div>

              <div style="margin-top:22px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الشركة
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">اسم الشركة:</td><td style="padding:6px 0;">{company_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">البريد الإلكتروني:</td><td style="padding:6px 0;">{company_email}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الجوال:</td><td style="padding:6px 0;">{company_phone}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">السجل التجاري:</td><td style="padding:6px 0;">{commercial_number}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">المدينة:</td><td style="padding:6px 0;">{city}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">بريد المالك:</td><td style="padding:6px 0;">{owner_email}</td></tr>
                </table>
              </div>

              <div style="margin-top:18px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الاشتراك
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">الباقة:</td><td style="padding:6px 0;">{plan_name}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الحالة:</td><td style="padding:6px 0;">{subscription_status}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">تاريخ البداية:</td><td style="padding:6px 0;">{start_date}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">تاريخ النهاية:</td><td style="padding:6px 0;">{end_date}</td></tr>
                </table>
              </div>

              <div style="margin-top:18px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الفاتورة والدفع
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr><td style="padding:6px 0;font-weight:700;width:170px;">رقم الفاتورة:</td><td style="padding:6px 0;">{invoice_number}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">تاريخ الإصدار:</td><td style="padding:6px 0;">{issue_date}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">تاريخ الدفع:</td><td style="padding:6px 0;">{paid_at}</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">طريقة الدفع:</td><td style="padding:6px 0;">CASH</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">Subtotal:</td><td style="padding:6px 0;">{subtotal} SAR</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">VAT:</td><td style="padding:6px 0;">{vat} SAR</td></tr>
                  <tr><td style="padding:6px 0;font-weight:700;">الإجمالي:</td><td style="padding:6px 0;">{total} SAR</td></tr>
                </table>
              </div>

              <div style="margin-top:22px;font-size:14px;color:#6b7280;line-height:2;">
                تم إرفاق نسخة PDF من الفاتورة مع هذه الرسالة.
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


def _send_cash_payment_confirmation_email(*, invoice, payment, subscription) -> None:
    recipients = _build_invoice_recipients(invoice)

    if not recipients:
        logger.warning(
            "Cash payment email skipped: no recipients found. invoice_id=%s",
            getattr(invoice, "id", None),
        )
        return

    company = getattr(invoice, "company", None)

    subtotal_value = (
        getattr(invoice, "subtotal_amount", None)
        if hasattr(invoice, "subtotal_amount")
        else getattr(invoice, "subtotal", None)
    )
    vat_value = getattr(invoice, "vat", None)
    total_value = getattr(invoice, "total_amount", None)

    subject = f"تأكيد الدفع النقدي - {_safe_text(getattr(company, 'name', None), 'Company')}"

    text_body = (
        f"تم تأكيد الدفع النقدي بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_text(getattr(company, 'name', None))}\n"
        f"رقم الفاتورة: {_safe_text(getattr(invoice, 'invoice_number', None))}\n"
        f"تاريخ الإصدار: {_date_str(getattr(invoice, 'issue_date', None))}\n"
        f"تاريخ الدفع: {_date_str(getattr(payment, 'paid_at', None))}\n"
        f"طريقة الدفع: CASH\n"
        f"الباقة: {_safe_text(getattr(getattr(subscription, 'plan', None), 'name', None)) if subscription else '-'}\n"
        f"حالة الاشتراك: {_safe_text(getattr(subscription, 'status', None)) if subscription else '-'}\n"
        f"Subtotal: {_money_str(subtotal_value)} SAR\n"
        f"VAT: {_money_str(vat_value)} SAR\n"
        f"الإجمالي: {_money_str(total_value)} SAR\n\n"
        f"تم إرفاق نسخة PDF من الفاتورة مع هذه الرسالة.\n\n"
        f"مع تحيات Primey HR Cloud"
    )

    html_body = _build_cash_payment_email_html(
        invoice=invoice,
        payment=payment,
        subscription=subscription,
    )

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        message.attach_alternative(html_body, "text/html")

        pdf_bytes = _generate_invoice_pdf_bytes(
            invoice=invoice,
            payment=payment,
            subscription=subscription,
        )
        if pdf_bytes:
            filename = f"{_safe_text(getattr(invoice, 'invoice_number', None), 'invoice')}.pdf"
            message.attach(filename, pdf_bytes, "application/pdf")

        message.send(fail_silently=False)

        logger.info(
            "Cash payment confirmation email sent successfully. invoice_id=%s recipients=%s",
            getattr(invoice, "id", None),
            recipients,
        )

    except Exception:
        logger.exception(
            "Failed to send cash payment confirmation email. invoice_id=%s",
            getattr(invoice, "id", None),
        )


@csrf_exempt
@require_POST
@transaction.atomic
def confirm_cash_payment(request):
    """
    Confirm Cash Payment (Manual)

    - Super Admin only
    - Marks invoice as PAID
    - Creates Payment record (SOURCE OF TRUTH)
    - Activates subscription
    - Auto-activates company (RULE: after ACTIVE subscription)
    - Supports UPGRADE invoices
    """

    # ============================================================
    # 🔐 Authorization
    # ============================================================
    if not request.user.is_authenticated or not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        payload = json.loads(request.body or "{}")
        invoice_id = payload.get("invoice_id")

        if not invoice_id:
            return JsonResponse(
                {"error": "invoice_id is required"},
                status=400
            )

        # ========================================================
        # 🧾 Invoice
        # ========================================================
        invoice = Invoice.objects.select_for_update().select_related(
            "subscription__plan",
            "company__owner",
        ).get(id=invoice_id)

        if invoice.status == "PAID":
            return JsonResponse(
                {"error": "Invoice already paid"},
                status=400
            )

        # ========================================================
        # 🔄 Subscription Reference
        # ========================================================
        subscription = invoice.subscription

        # ========================================================
        # 💳 Create Payment (SOURCE OF TRUTH)
        # ========================================================
        payment = Payment.objects.create(
            invoice=invoice,
            amount=invoice.total_amount,
            method="CASH",
            reference_number=f"CASH-{invoice.id}-{int(now().timestamp())}",
            paid_at=now(),
            created_by=request.user,
        )

        # ========================================================
        # ✅ Update Invoice (STATUS ONLY)
        # ========================================================
        invoice.status = "PAID"
        invoice.save(update_fields=["status"])

        # ========================================================
        # 🔄 Subscription Logic
        # ========================================================
        if subscription:

            # ----------------------------------------------------
            # UPGRADE FLOW
            # ----------------------------------------------------
            if invoice.billing_reason == "UPGRADE":
                snapshot = invoice.subscription_snapshot or {}
                target_plan_data = snapshot.get("target_plan") or {}
                target_plan_id = target_plan_data.get("id")

                if not target_plan_id:
                    return JsonResponse(
                        {"error": "Upgrade target plan not found in invoice snapshot"},
                        status=400
                    )

                try:
                    target_plan = SubscriptionPlan.objects.get(id=target_plan_id)
                except SubscriptionPlan.DoesNotExist:
                    return JsonResponse(
                        {"error": "Target upgrade plan does not exist"},
                        status=404
                    )

                subscription.plan = target_plan

                if subscription.status != "ACTIVE":
                    subscription.status = "ACTIVE"

                if not subscription.start_date:
                    subscription.start_date = now().date()

                subscription.save(update_fields=["plan", "status", "start_date"])

            # ----------------------------------------------------
            # RENEWAL FLOW
            # ----------------------------------------------------
            elif invoice.billing_reason == "RENEWAL":

                subscription.status = "EXPIRED"
                subscription.save(update_fields=["status"])

                new_subscription = CompanySubscription.objects.create(
                    company=subscription.company,
                    plan=subscription.plan,
                    start_date=now().date(),
                    end_date=subscription.end_date,
                    status="ACTIVE",
                    apps_snapshot=subscription.apps_snapshot,
                )

                subscription = new_subscription

            # ----------------------------------------------------
            # NORMAL ACTIVATION (Onboarding)
            # ----------------------------------------------------
            else:

                if subscription.status != "ACTIVE":
                    subscription.status = "ACTIVE"
                    subscription.start_date = (
                        subscription.start_date or now().date()
                    )

                    subscription.save(
                        update_fields=["status", "start_date"]
                    )

        # ========================================================
        # 🟢 AUTO ACTIVATE COMPANY
        # ========================================================
        company = invoice.company
        if company and not company.is_active:
            company.is_active = True
            company.save(update_fields=["is_active"])

        # ========================================================
        # ✉️ Send Email After Successful Commit
        # ========================================================
        transaction.on_commit(
            lambda: _send_cash_payment_confirmation_email(
                invoice=invoice,
                payment=payment,
                subscription=subscription,
            )
        )

        # ========================================================
        # 📲 Send WhatsApp After Successful Commit
        # ========================================================
        transaction.on_commit(
            lambda: _send_cash_payment_confirmation_whatsapp(
                invoice=invoice,
                payment=payment,
                subscription=subscription,
            )
        )

        # ========================================================
        # ✅ Response
        # ========================================================
        return JsonResponse({
            "success": True,
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "billing_reason": invoice.billing_reason,
            "subscription_status": (
                subscription.status if subscription else None
            ),
            "active_plan": (
                subscription.plan.name
                if subscription and subscription.plan
                else None
            ),
            "company_active": company.is_active if company else False,
            "message": "تم تأكيد الدفع وتفعيل الاشتراك/الترقية بنجاح",
        })

    except Invoice.DoesNotExist:
        return JsonResponse(
            {"error": "Invoice not found"},
            status=404
        )

    except Exception as e:
        logger.exception("confirm_cash_payment failed")
        return JsonResponse(
            {"error": str(e)},
            status=500
        )