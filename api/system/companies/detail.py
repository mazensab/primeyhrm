from __future__ import annotations

import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing_center.models import CompanySubscription
from billing_center.models import Invoice, Payment
from company_manager.models import Company

logger = logging.getLogger(__name__)


# ================================================================
# 🖼️ Primey Email Logo
# نفس فكرة reset password / system users
# ================================================================
PRIMEY_EMAIL_LOGO_URL = getattr(
    settings,
    "PRIMEY_EMAIL_LOGO_URL",
    "https://drive.google.com/uc?export=view&id=1x2Q9wJm8QmQm7mYjQmW7aJmR8bPlogoblak",
)

DEFAULT_FROM_EMAIL = getattr(
    settings,
    "DEFAULT_FROM_EMAIL",
    getattr(settings, "EMAIL_HOST_USER", "no-reply@primeyhr.com"),
)


# ================================================================
# 🧩 Helpers
# ================================================================
def _json_payload(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


def _normalize_text(value):
    if value is None:
        return None

    value = str(value).strip()
    return value if value else ""


def _safe_value(value):
    return value if value not in (None, "") else "-"


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
) -> str:
    """
    قالب HTML لإيميل تحديث بيانات الشركة
    بنفس هوية الإيميلات المعتمدة في النظام.
    """

    logo_url = escape(PRIMEY_EMAIL_LOGO_URL)

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

          <!-- Header -->
          <tr>
            <td align="center" style="background:#000000;padding:28px 24px;">
              <img src="{logo_url}" alt="Primey"
                   style="max-height:56px;width:auto;display:block;margin:0 auto 12px auto;" />
              <div style="color:#ffffff;font-size:22px;font-weight:700;line-height:1.6;">
                Primey HR Cloud
              </div>
              <div style="color:#d1d5db;font-size:14px;line-height:1.8;">
                تم تحديث بيانات الشركة بنجاح
              </div>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px 28px 20px 28px;">
              <div style="font-size:16px;color:#111827;line-height:2;">
                أهلاً <strong>{owner_name}</strong>،
              </div>

              <div style="margin-top:10px;font-size:15px;color:#374151;line-height:2;">
                تم تحديث بيانات الشركة داخل نظام <strong>Primey HR Cloud</strong> بنجاح.
              </div>

              <div style="margin-top:22px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  البيانات الحالية للشركة
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr>
                    <td style="padding:6px 0;font-weight:700;width:170px;">اسم الشركة:</td>
                    <td style="padding:6px 0;">{company_name}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">البريد الإلكتروني:</td>
                    <td style="padding:6px 0;">{company_email}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">رقم الجوال:</td>
                    <td style="padding:6px 0;">{company_phone}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">السجل التجاري:</td>
                    <td style="padding:6px 0;">{commercial_number}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">الرقم الضريبي:</td>
                    <td style="padding:6px 0;">{vat_number}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">رقم المبنى:</td>
                    <td style="padding:6px 0;">{building_number}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">الشارع:</td>
                    <td style="padding:6px 0;">{street}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">الحي:</td>
                    <td style="padding:6px 0;">{district}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">المدينة:</td>
                    <td style="padding:6px 0;">{city}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">الرمز البريدي:</td>
                    <td style="padding:6px 0;">{postal_code}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">العنوان المختصر:</td>
                    <td style="padding:6px 0;">{short_address}</td>
                  </tr>
                </table>
              </div>

              <div style="margin-top:22px;font-size:14px;color:#6b7280;line-height:2;">
                هذه الرسالة للتأكيد فقط بأنه تم حفظ التعديلات بنجاح على بيانات الشركة.
              </div>
            </td>
          </tr>

          <!-- Footer -->
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


def _send_company_updated_email(*, company: Company) -> None:
    """
    إرسال إيميل عند تحديث بيانات الشركة.
    """

    owner = getattr(company, "owner", None)
    recipient = getattr(owner, "email", None) if owner else None

    if not recipient:
        logger.warning(
            "Company update email skipped: owner email missing. company_id=%s",
            getattr(company, "id", None),
        )
        return

    owner_name = (
        owner.get_full_name().strip()
        if hasattr(owner, "get_full_name") and owner.get_full_name()
        else getattr(owner, "username", "User")
    )

    subject = f"تم تحديث بيانات الشركة - {company.name}"

    text_body = (
        f"مرحباً {owner_name},\n\n"
        f"تم تحديث بيانات الشركة بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_value(company.name)}\n"
        f"البريد الإلكتروني: {_safe_value(company.email)}\n"
        f"رقم الجوال: {_safe_value(company.phone)}\n"
        f"السجل التجاري: {_safe_value(company.commercial_number)}\n"
        f"الرقم الضريبي: {_safe_value(company.vat_number)}\n"
        f"رقم المبنى: {_safe_value(company.building_number)}\n"
        f"الشارع: {_safe_value(company.street)}\n"
        f"الحي: {_safe_value(company.district)}\n"
        f"المدينة: {_safe_value(company.city)}\n"
        f"الرمز البريدي: {_safe_value(company.postal_code)}\n"
        f"العنوان المختصر: {_safe_value(company.short_address)}\n\n"
        f"مع تحيات Primey HR Cloud"
    )

    html_body = _build_company_updated_email_html(
        owner_name=owner_name,
        company_name=company.name,
        company_email=company.email,
        company_phone=company.phone,
        commercial_number=company.commercial_number,
        vat_number=company.vat_number,
        building_number=company.building_number,
        street=company.street,
        district=company.district,
        city=company.city,
        postal_code=company.postal_code,
        short_address=company.short_address,
    )

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)

        logger.info(
            "Company update email sent successfully. company_id=%s",
            company.id,
        )
    except Exception:
        logger.exception(
            "Failed to send company update email. company_id=%s",
            getattr(company, "id", None),
        )


# ================================================================
# 🏢 System API — Company Details
# ================================================================
@login_required
def system_company_detail(request, company_id):

    company = get_object_or_404(Company, id=company_id)

    subscription = (
        CompanySubscription.objects
        .filter(company=company)
        .select_related("plan")
        .order_by("-id")
        .first()
    )

    data = {

        # Company
        "company": {
            "id": company.id,
            "name": company.name,
            "is_active": company.is_active,
            "created_at": company.created_at,

            # ------------------------------------------------
            # Company Information
            # ------------------------------------------------
            "commercial_number": company.commercial_number,
            "vat_number": company.vat_number,
            "phone": company.phone,
            "email": company.email,

            # ------------------------------------------------
            # National Address
            # ------------------------------------------------
            "national_address": {
                "building_number": company.building_number,
                "street": company.street,
                "district": company.district,
                "city": company.city,
                "postal_code": company.postal_code,
                "short_address": company.short_address,
            },
        },

        # Owner
        "owner": {
            "email": company.owner.email if company.owner else None
        },

        # Subscription
        "subscription": {
            "plan": subscription.plan.name if subscription and subscription.plan else None,
            "status": subscription.status if subscription else None
        },

        # Users
        "users_count": company.company_users.count(),
    }

    return JsonResponse(data)


# ================================================================
# ✏️ System API — Update Company Information
# ================================================================
@login_required
@require_POST
@csrf_exempt
def system_company_update(request, company_id):

    company = get_object_or_404(Company, id=company_id)
    payload = _json_payload(request)

    if not payload:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    national_address = payload.get("national_address") or {}

    company.name = _normalize_text(payload.get("name")) or company.name
    company.commercial_number = _normalize_text(payload.get("commercial_number"))
    company.vat_number = _normalize_text(payload.get("vat_number"))
    company.phone = _normalize_text(payload.get("phone"))
    company.email = _normalize_text(payload.get("email"))

    company.building_number = _normalize_text(
        national_address.get("building_number")
    )
    company.street = _normalize_text(
        national_address.get("street")
    )
    company.district = _normalize_text(
        national_address.get("district")
    )
    company.city = _normalize_text(
        national_address.get("city")
    )
    company.postal_code = _normalize_text(
        national_address.get("postal_code")
    )
    company.short_address = _normalize_text(
        national_address.get("short_address")
    )

    company.save(update_fields=[
        "name",
        "commercial_number",
        "vat_number",
        "phone",
        "email",
        "building_number",
        "street",
        "district",
        "city",
        "postal_code",
        "short_address",
    ])

    _send_company_updated_email(company=company)

    return JsonResponse({
        "success": True,
        "message": "تم تحديث بيانات الشركة بنجاح",
        "company": {
            "id": company.id,
            "name": company.name,
            "commercial_number": company.commercial_number,
            "vat_number": company.vat_number,
            "phone": company.phone,
            "email": company.email,
            "national_address": {
                "building_number": company.building_number,
                "street": company.street,
                "district": company.district,
                "city": company.city,
                "postal_code": company.postal_code,
                "short_address": company.short_address,
            },
        }
    })


# ================================================================
# 📊 System API — Company Activity Logs
# ================================================================
@login_required
def system_company_activity(request, company_id):

    company = get_object_or_404(Company, id=company_id)

    logs = []

    # ------------------------------------------------
    # Invoices
    # ------------------------------------------------
    invoices = (
        Invoice.objects
        .filter(company=company)
        .order_by("-id")[:20]
    )

    for inv in invoices:

        invoice_number = getattr(inv, "invoice_number", None) or getattr(inv, "number", f"Invoice #{inv.id}")
        total_amount = getattr(inv, "total_amount", None)
        currency = getattr(inv, "currency", "SAR")

        logs.append({
            "type": "invoice",
            "title": "Invoice Created",
            "message": invoice_number,
            "amount": f"{total_amount} {currency}" if total_amount else None,
            "created_at": getattr(inv, "issue_date", None)
        })

    # ------------------------------------------------
    # Payments
    # ------------------------------------------------
    payments = (
        Payment.objects
        .filter(invoice__company=company)
        .select_related("invoice")
        .order_by("-id")[:20]
    )

    for pay in payments:

        invoice_number = getattr(pay.invoice, "invoice_number", None) if pay.invoice else None
        amount = getattr(pay, "amount", None)
        currency = getattr(pay, "currency", "SAR")

        logs.append({
            "type": "payment",
            "title": "Payment Received",
            "message": invoice_number,
            "amount": f"{amount} {currency}" if amount else None,
            "created_at": getattr(pay, "paid_at", None)
        })

    # ------------------------------------------------
    # Sort Logs
    # ------------------------------------------------
    logs = sorted(
        logs,
        key=lambda x: str(x["created_at"]) if x["created_at"] else "",
        reverse=True
    )

    return JsonResponse({
        "status": "success",
        "data": {
            "results": logs[:20]
        }
    })