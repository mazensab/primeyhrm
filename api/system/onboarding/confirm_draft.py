# ============================================================
# 📂 api/system/onboarding/confirm_draft.py
# Primey HR Cloud
# Confirm Draft + WhatsApp Notification
# ============================================================

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.http import JsonResponse
from django.utils.html import escape
from django.views.decorators.http import require_POST

from billing_center.models import CompanyOnboardingTransaction
from whatsapp_center.models import ScopeType, TriggerSource
from whatsapp_center.services import send_event_whatsapp_message

logger = logging.getLogger(__name__)


# ============================================================
# 🖼️ Primey Email Logo
# نفس أسلوب reset password / system users
# ============================================================

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


# ============================================================
# ✉️ Shared Helpers
# ============================================================

def _safe_text(value, default="-"):
    if value is None:
        return default
    value = str(value).strip()
    return value or default


def _get_draft_recipient(draft) -> str | None:
    """
    محاولة استخراج بريد المستلم من حقول الـ draft المتوقعة
    بدون كسر أي بنية حالية.
    """
    possible_fields = [
        "admin_email",
        "email",
        "owner_email",
        "company_email",
    ]

    for field_name in possible_fields:
        value = getattr(draft, field_name, None)
        if value:
            value = str(value).strip()
            if value:
                return value

    return None


def _get_owner_name(draft) -> str:
    """
    محاولة استخراج اسم مناسب من الـ draft.
    """
    possible_fields = [
        "admin_full_name",
        "admin_name",
        "full_name",
        "owner_name",
        "admin_username",
        "username",
        "company_name",
    ]

    for field_name in possible_fields:
        value = getattr(draft, field_name, None)
        if value:
            value = str(value).strip()
            if value:
                return value

    return "User"


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


def _get_user_related_profile_candidates(user) -> list:
    """
    محاولة الوصول إلى بروفايل المستخدم الشائع بدون فرض اسم محدد.
    """
    if not user:
        return []

    candidates = []

    for attr_name in ["profile", "userprofile"]:
        try:
            related_obj = getattr(user, attr_name, None)
        except Exception:
            related_obj = None

        if related_obj:
            candidates.append(related_obj)

    return candidates


def _get_best_phone_for_entity(instance) -> str:
    """
    جلب أفضل رقم جوال من الكيان مباشرة أو من profile/userprofile إن وجد.
    """
    phone_attr_candidates = [
        "phone",
        "mobile",
        "mobile_number",
        "whatsapp_number",
        "phone_number",
    ]

    direct_phone = _get_first_existing_attr(instance, phone_attr_candidates, "")
    if direct_phone:
        return direct_phone

    for profile_obj in _get_user_related_profile_candidates(instance):
        profile_phone = _get_first_existing_attr(profile_obj, phone_attr_candidates, "")
        if profile_phone:
            return profile_phone

    return ""


# ============================================================
# ✉️ Email Helpers
# ============================================================

def _build_confirm_draft_email_html(
    *,
    owner_name: str,
    company_name: str,
    plan_name: str,
    duration: str,
    total_amount: str,
    status: str,
) -> str:
    logo_url = escape(PRIMEY_EMAIL_LOGO_URL)

    owner_name = escape(_safe_text(owner_name))
    company_name = escape(_safe_text(company_name))
    plan_name = escape(_safe_text(plan_name))
    duration = escape(_safe_text(duration))
    total_amount = escape(_safe_text(total_amount))
    status = escape(_safe_text(status))

    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>تم تأكيد طلب الشركة</title>
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
                تم تأكيد الطلب بنجاح
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
                تم تأكيد طلب إنشاء الشركة داخل نظام <strong>Primey HR Cloud</strong> بنجاح.
              </div>

              <div style="margin-top:22px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:18px;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:14px;">
                  بيانات الطلب
                </div>

                <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#374151;line-height:2;">
                  <tr>
                    <td style="padding:6px 0;font-weight:700;width:170px;">اسم الشركة:</td>
                    <td style="padding:6px 0;">{company_name}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">الباقة:</td>
                    <td style="padding:6px 0;">{plan_name}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">المدة:</td>
                    <td style="padding:6px 0;">{duration}</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">الإجمالي:</td>
                    <td style="padding:6px 0;">{total_amount} SAR</td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-weight:700;">الحالة:</td>
                    <td style="padding:6px 0;">{status}</td>
                  </tr>
                </table>
              </div>

              <div style="margin-top:22px;font-size:14px;color:#6b7280;line-height:2;">
                هذه الرسالة تؤكد نجاح تأكيد الطلب. وعند تنفيذ الدفع من المسار المالي الصحيح سيتم إرسال رسالة تأكيد الدفع والفاتورة في مكانها الصحيح.
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


def _send_confirm_draft_email(*, draft) -> None:
    recipient = _get_draft_recipient(draft)

    if not recipient:
        logger.warning(
            "Confirm draft email skipped: no recipient found for draft_id=%s",
            getattr(draft, "id", None),
        )
        return

    owner_name = _get_owner_name(draft)
    company_name = getattr(draft, "company_name", None)
    plan_name = getattr(getattr(draft, "plan", None), "name", None)
    duration = getattr(draft, "duration", None)
    total_amount = getattr(draft, "total_amount", None)
    status = getattr(draft, "status", None)

    subject = f"تم تأكيد الطلب - {_safe_text(company_name)}"

    text_body = (
        f"مرحباً {_safe_text(owner_name)},\n\n"
        f"تم تأكيد طلب إنشاء الشركة بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_text(company_name)}\n"
        f"الباقة: {_safe_text(plan_name)}\n"
        f"المدة: {_safe_text(duration)}\n"
        f"الإجمالي: {_safe_text(total_amount)} SAR\n"
        f"الحالة: {_safe_text(status)}\n\n"
        f"مع تحيات Primey HR Cloud"
    )

    html_body = _build_confirm_draft_email_html(
        owner_name=owner_name,
        company_name=company_name,
        plan_name=plan_name,
        duration=duration,
        total_amount=total_amount,
        status=status,
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
            "Confirm draft email sent successfully. draft_id=%s recipient=%s",
            getattr(draft, "id", None),
            recipient,
        )

    except Exception:
        logger.exception(
            "Failed to send confirm draft email. draft_id=%s",
            getattr(draft, "id", None),
        )


# ============================================================
# 📲 WhatsApp Helpers
# ============================================================

def _build_confirm_draft_whatsapp_message(*, draft) -> str:
    owner_name = _get_owner_name(draft)
    company_name = getattr(draft, "company_name", None)
    plan_name = getattr(getattr(draft, "plan", None), "name", None)
    duration = getattr(draft, "duration", None)
    total_amount = getattr(draft, "total_amount", None)
    status = getattr(draft, "status", None)

    return (
        f"مرحباً {_safe_text(owner_name)}،\n\n"
        f"تم تأكيد طلب إنشاء الشركة بنجاح داخل Primey HR Cloud.\n\n"
        f"اسم الشركة: {_safe_text(company_name)}\n"
        f"الباقة: {_safe_text(plan_name)}\n"
        f"المدة: {_safe_text(duration)}\n"
        f"الإجمالي: {_safe_text(total_amount)} SAR\n"
        f"الحالة: {_safe_text(status)}\n\n"
        f"تم اعتماد الطلب بنجاح، وستصلك رسالة أخرى بعد الدفع والتفعيل النهائي."
    )


def _send_confirm_draft_whatsapp(*, draft) -> None:
    """
    إرسال واتساب بعد تأكيد الطلب.
    هذا التدفق يتبع الـ system/public onboarding لذلك نعتمد SYSTEM scope.
    """
    seen_phones: set[str] = set()
    targets: list[dict] = []

    def _append_target(phone: str, name: str, role: str):
        phone = _safe_text(phone, "")
        if not phone or phone in seen_phones:
            return

        seen_phones.add(phone)
        targets.append(
            {
                "phone": phone,
                "name": _safe_text(name, "User"),
                "role": _safe_text(role, ""),
            }
        )

    # 1) رقم الشركة / الطلب
    _append_target(
        _safe_text(getattr(draft, "phone", None), ""),
        _get_owner_name(draft),
        "company",
    )

    # 2) رقم المالك الداخلي إن وجد
    owner = getattr(draft, "owner", None)
    if owner:
        owner_phone = _get_best_phone_for_entity(owner)
        _append_target(
            owner_phone,
            getattr(owner, "first_name", None) or getattr(owner, "username", None) or "Owner",
            "owner",
        )

    if not targets:
        logger.warning(
            "Confirm draft WhatsApp skipped: no phone targets found. draft_id=%s owner_id=%s",
            getattr(draft, "id", None),
            getattr(owner, "id", None) if owner else None,
        )
        return

    message_text = _build_confirm_draft_whatsapp_message(draft=draft)

    for target in targets:
        try:
            send_event_whatsapp_message(
                scope_type=ScopeType.SYSTEM,
                company=None,
                event_code="onboarding_draft_confirmed",
                recipient_phone=target["phone"],
                recipient_name=target["name"],
                recipient_role=target["role"],
                trigger_source=TriggerSource.SYSTEM,
                language_code="ar",
                related_model="CompanyOnboardingTransaction",
                related_object_id=str(getattr(draft, "id", "")),
                context={
                    "message": message_text,
                    "company_name": _safe_text(getattr(draft, "company_name", None)),
                    "recipient_name": target["name"],
                    "plan_name": _safe_text(getattr(getattr(draft, "plan", None), "name", None)),
                    "duration": _safe_text(getattr(draft, "duration", None)),
                    "total_amount": f"{_safe_text(getattr(draft, 'total_amount', None))} SAR",
                    "status": _safe_text(getattr(draft, "status", None)),
                },
            )

            logger.info(
                "Confirm draft WhatsApp dispatched successfully. draft_id=%s phone=%s role=%s",
                getattr(draft, "id", None),
                target.get("phone"),
                target.get("role"),
            )

        except Exception:
            logger.exception(
                "Failed to send confirm draft WhatsApp. draft_id=%s phone=%s role=%s",
                getattr(draft, "id", None),
                target.get("phone"),
                target.get("role"),
            )


# ============================================================
# API — Confirm Draft
# URL: /api/system/onboarding/confirm-draft/
# ============================================================

@require_POST
def confirm_draft(request):

    try:
        data = json.loads(request.body)
        draft_id = data.get("draft_id")

        if not draft_id:
            return JsonResponse(
                {"error": "draft_id required"},
                status=400
            )

        draft = CompanyOnboardingTransaction.objects.select_related(
            "plan",
            "owner",
        ).get(id=draft_id)

    except CompanyOnboardingTransaction.DoesNotExist:
        return JsonResponse(
            {"error": "Draft not found"},
            status=404
        )
    except Exception:
        return JsonResponse(
            {"error": "Invalid request payload"},
            status=400
        )

    # ========================================================
    # Confirm Draft Only
    # ========================================================

    with transaction.atomic():

        # منع إعادة التأكيد
        if draft.status != "DRAFT":
            return JsonResponse(
                {"error": "Draft already confirmed"},
                status=409
            )

        draft.status = "CONFIRMED"
        draft.save(update_fields=["status"])

        # ----------------------------------------------------
        # إرسال الإيميل بعد نجاح الـ commit
        # ----------------------------------------------------
        transaction.on_commit(
            lambda: _send_confirm_draft_email(draft=draft)
        )

        # ----------------------------------------------------
        # إرسال الواتساب بعد نجاح الـ commit
        # ----------------------------------------------------
        transaction.on_commit(
            lambda: _send_confirm_draft_whatsapp(draft=draft)
        )

    # ========================================================
    # Response
    # ========================================================

    return JsonResponse({

        "message": "Draft confirmed successfully",

        "draft": {
            "id": draft.id,
            "company_name": draft.company_name,
            "plan": draft.plan.name,
            "duration": draft.duration,
            "total_amount": float(draft.total_amount),
            "status": draft.status
        }

    })