# ====================================================================
# 🏢 Company Create API
# Primey HR Cloud — System Companies
# ====================================================================

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.http import JsonResponse
from django.utils.html import escape
from django.views.decorators.http import require_POST

from billing_center.models import (
    CompanySubscription,
    AccountSubscription,
)

from company_manager.models import (
    Company,
    CompanyUser,
    CompanyRole,
)

from .roles_blueprint import DEFAULT_COMPANY_ROLES

logger = logging.getLogger(__name__)


# ====================================================================
# 🖼️ Primey Email Logo
# نفس فكرة reset password / system users
# ====================================================================

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


# ====================================================================
# ✉️ Helpers
# ====================================================================

def _build_company_created_email_html(
    *,
    company_name: str,
    owner_name: str,
    owner_email: str,
    company_email: str,
    company_phone: str,
) -> str:
    """
    بناء قالب HTML لإيميل إنشاء الشركة
    بنفس نمط رسائل النظام المعتمدة.
    """

    company_name = escape(company_name or "-")
    owner_name = escape(owner_name or "User")
    owner_email = escape(owner_email or "-")
    company_email = escape(company_email or "-")
    company_phone = escape(company_phone or "-")
    logo_url = escape(PRIMEY_EMAIL_LOGO_URL)

    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>تم إنشاء الشركة بنجاح</title>
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
                تم إنشاء الشركة بنجاح
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
                تم إنشاء شركتك الجديدة بنجاح داخل نظام <strong>Primey HR Cloud</strong>.
              </div>

              <div style="margin-top:22px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الشركة
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr>
                    <td style="padding:6px 0;font-weight:700;width:160px;">اسم الشركة:</td>
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
                    <td style="padding:6px 0;font-weight:700;">مالك الحساب:</td>
                    <td style="padding:6px 0;">{owner_email}</td>
                  </tr>
                </table>
              </div>

              <div style="margin-top:22px;font-size:14px;color:#6b7280;line-height:2;">
                يمكنك الآن متابعة إعدادات الشركة وربط الوحدات وإدارة المستخدمين والاشتراكات من لوحة التحكم.
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


def _send_company_created_email(*, user, company) -> None:
    """
    إرسال إيميل إنشاء الشركة بعد نجاح الـ commit
    حتى لا يؤثر البريد على عملية الإنشاء الأساسية.
    """

    recipient = getattr(user, "email", None)
    if not recipient:
        logger.warning(
            "Company created email skipped: owner has no email. user_id=%s company_id=%s",
            getattr(user, "id", None),
            getattr(company, "id", None),
        )
        return

    owner_name = (
        user.get_full_name().strip()
        if hasattr(user, "get_full_name") and user.get_full_name()
        else getattr(user, "username", "User")
    )

    subject = f"تم إنشاء الشركة بنجاح - {company.name}"
    text_body = (
        f"مرحباً {owner_name},\n\n"
        f"تم إنشاء شركتك بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {company.name}\n"
        f"البريد الإلكتروني للشركة: {company.email or '-'}\n"
        f"رقم الجوال: {company.phone or '-'}\n"
        f"البريد الإلكتروني لمالك الحساب: {recipient}\n\n"
        f"مع تحيات Primey HR Cloud"
    )

    html_body = _build_company_created_email_html(
        company_name=company.name,
        owner_name=owner_name,
        owner_email=recipient,
        company_email=company.email or "-",
        company_phone=company.phone or "-",
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
            "Company created email sent successfully. company_id=%s user_id=%s",
            company.id,
            user.id,
        )

    except Exception:
        logger.exception(
            "Failed to send company created email. company_id=%s user_id=%s",
            getattr(company, "id", None),
            getattr(user, "id", None),
        )


# ====================================================================
# 🏢 Create Company (Paid Subscription Required)
# ====================================================================

@login_required
@require_POST
def company_create(request):

    user = request.user

    # ============================================================
    # 📥 Payload (JSON + FORM SAFE)
    # ============================================================
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = request.POST

    name = payload.get("name")
    email = payload.get("email")
    phone = payload.get("phone")

    if not name:
        return JsonResponse(
            {"error": "اسم الشركة مطلوب"},
            status=400,
        )

    # ============================================================
    # 🔒 Active Account Subscription
    # ============================================================
    sub = (
        AccountSubscription.objects
        .filter(owner=user, status="ACTIVE")
        .select_related("plan")
        .first()
    )

    if not sub or not sub.plan:
        return JsonResponse(
            {"error": "لا يوجد اشتراك مدفوع نشط"},
            status=403,
        )

    # ============================================================
    # 🧮 Company Limit
    # ============================================================
    used_companies = (
        CompanyUser.objects
        .filter(user=user, is_active=True)
        .values("company")
        .distinct()
        .count()
    )

    if used_companies >= sub.plan.max_companies:
        return JsonResponse(
            {"error": "تم الوصول للحد الأقصى المسموح من الشركات"},
            status=403,
        )

    # ============================================================
    # 🏢 Atomic Creation
    # ============================================================
    with transaction.atomic():

        # --------------------------------------------------------
        # 1️⃣ Create Company
        # --------------------------------------------------------
        company = Company.objects.create(
            name=name,
            email=email,
            phone=phone,
            is_active=True,
            owner=user,
        )

        # --------------------------------------------------------
        # 2️⃣ Link Owner
        # --------------------------------------------------------
        CompanyUser.objects.create(
            user=user,
            company=company,
            role="owner",
            is_active=True,
        )

        # --------------------------------------------------------
        # 3️⃣ Subscription Stub
        # --------------------------------------------------------
        CompanySubscription.objects.get_or_create(
            company=company,
            defaults={
                "status": "PENDING"
            }
        )

        # --------------------------------------------------------
        # 4️⃣ Default Company Roles
        # --------------------------------------------------------
        for role_data in DEFAULT_COMPANY_ROLES:
            CompanyRole.objects.create(
                company=company,
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
                is_system_role=role_data["is_system_role"],
            )

        # --------------------------------------------------------
        # 5️⃣ Send Email After Successful Commit
        # --------------------------------------------------------
        transaction.on_commit(
            lambda: _send_company_created_email(
                user=user,
                company=company,
            )
        )

    # ============================================================
    # ✅ Success Response
    # ============================================================
    return JsonResponse(
        {
            "id": company.id,
            "name": company.name,
            "owner": {
                "id": user.id,
                "email": user.email,
            },
        },
        status=201,
    )