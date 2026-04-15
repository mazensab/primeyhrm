# ============================================================
# 📂 notification_center/services_onboarding.py
# 🧠 Onboarding Notification Services — Mham Cloud V1.4
# ------------------------------------------------------------
# ✅ طبقة رسمية موحدة لإشعارات التسجيل الخارجي / onboarding
# ✅ مبنية فوق Notification Center 2.0
# ✅ تدعم:
#    - onboarding_draft_created
#    - onboarding_draft_confirmed
#    - onboarding_payment_confirmed
#    - payment_confirmed_company_activated
# ✅ ترسل In-App + Email + WhatsApp حسب توفر المستلم
# ✅ تدعم public flow و internal flow
# ✅ متوافقة مع create_draft / confirm_draft / confirm_payment
# ✅ بدون أي إرسال مباشر داخل ملفات API
# ✅ الرسائل الآن أغنى بالبيانات التشغيلية
# ✅ تدعم إرفاق فاتورة PDF عند تأكيد الدفع إذا وُجدت
# ✅ تمنع تمرير bytes داخل NotificationEvent.context
# ✅ FIX: richer target fallback from context for admin / owner / company
# ✅ FIX: processed target count reflects actual dispatch attempts
# ------------------------------------------------------------

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.utils.html import escape

from notification_center.services import create_notification

try:
    from whatsapp_center.utils import normalize_phone_number
except Exception:
    normalize_phone_number = None


logger = logging.getLogger(__name__)


# ============================================================
# 🧩 Helpers
# ============================================================

def _clean_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    value = str(value).strip()
    return value or default


def _normalize_email(value: Any) -> str:
    return _clean_text(value).lower()


def _normalize_phone(value: Any) -> str:
    phone = _clean_text(value)
    if not phone:
        return ""

    if callable(normalize_phone_number):
        try:
            normalized = normalize_phone_number(phone)
            return _clean_text(normalized)
        except Exception:
            logger.exception("Failed to normalize phone number in services_onboarding")
            return phone

    return phone


def _frontend_base_url() -> str:
    return (
        _clean_text(getattr(settings, "FRONTEND_BASE_URL", ""))
        or _clean_text(getattr(settings, "FRONTEND_URL", ""))
        or _clean_text(getattr(settings, "NEXT_PUBLIC_APP_URL", ""))
        or "https://mhamcloud.sa"
    ).rstrip("/")


def _register_url(*, draft_id=None, plan_name: str = "", plan_id=None) -> str:
    base = f"{_frontend_base_url()}/register"

    params = []
    if plan_id:
        params.append(f"plan_id={plan_id}")
    if plan_name:
        params.append(f"plan_name={plan_name}")
    if draft_id:
        params.append(f"draft_id={draft_id}")

    if not params:
        return base

    return f"{base}?{'&'.join(params)}"


def _login_url() -> str:
    return f"{_frontend_base_url()}/login"


def _format_money(value: Any, default: str = "-") -> str:
    raw = _clean_text(value, "")
    if not raw:
        return default

    try:
        number = float(raw)
        return f"{number:,.2f} ريال"
    except Exception:
        return raw


def _company_display_name(company=None, draft=None, context: dict | None = None) -> str:
    if company is not None:
        value = _clean_text(getattr(company, "name", ""))
        if value:
            return value

    if draft is not None:
        value = _clean_text(getattr(draft, "company_name", ""))
        if value:
            return value

    ctx = context or {}
    return _clean_text(ctx.get("company_name")) or "الشركة"


def _plan_display_name(plan=None, subscription=None, draft=None, context: dict | None = None) -> str:
    if plan is not None:
        value = _clean_text(getattr(plan, "name", ""))
        if value:
            return value

    if subscription is not None:
        value = _clean_text(getattr(getattr(subscription, "plan", None), "name", ""))
        if value:
            return value

    if draft is not None:
        value = _clean_text(getattr(getattr(draft, "plan", None), "name", ""))
        if value:
            return value

    ctx = context or {}
    return _clean_text(ctx.get("plan_name"), "-")


def _resolve_language_code(user=None, default: str = "ar") -> str:
    if not user:
        return default

    preferred_language = _clean_text(getattr(user, "preferred_language", ""))
    if preferred_language in {"ar", "en"}:
        return preferred_language

    for profile_attr in ["profile", "userprofile"]:
        profile = getattr(user, profile_attr, None)
        if not profile:
            continue

        profile_language = _clean_text(getattr(profile, "preferred_language", ""))
        if profile_language in {"ar", "en"}:
            return profile_language

    return default


def _safe_get_user_phone(user) -> str:
    if not user:
        return ""

    for field_name in [
        "phone",
        "mobile",
        "mobile_number",
        "whatsapp_number",
        "phone_number",
    ]:
        value = _normalize_phone(getattr(user, field_name, ""))
        if value:
            return value

    for profile_attr in ["profile", "userprofile"]:
        profile = getattr(user, profile_attr, None)
        if not profile:
            continue

        for field_name in [
            "phone",
            "mobile",
            "mobile_number",
            "whatsapp_number",
            "phone_number",
        ]:
            value = _normalize_phone(getattr(profile, field_name, ""))
            if value:
                return value

    return ""


def _safe_user_display_name(user, default: str = "User") -> str:
    if not user:
        return default

    try:
        full_name = _clean_text(user.get_full_name())
        if full_name:
            return full_name
    except Exception:
        pass

    return (
        _clean_text(getattr(user, "first_name", ""))
        or _clean_text(getattr(user, "username", ""))
        or _clean_text(getattr(user, "email", ""))
        or default
    )


def _merge_context(*parts: dict | None) -> dict:
    payload: dict = {}
    for part in parts:
        if isinstance(part, dict):
            payload.update(part)
    return payload


def _json_safe_context(context: dict | None = None) -> dict:
    """
    تنظيف الـ context من القيم غير القابلة للتخزين JSON
    خصوصًا bytes الخاصة بمرفقات PDF.
    """
    ctx = dict(context or {})
    ctx.pop("invoice_pdf_bytes", None)
    return ctx


def _context_first(ctx: dict | None, keys: list[str], default: str = "") -> str:
    context = ctx or {}
    for key in keys:
        value = _clean_text(context.get(key), "")
        if value:
            return value
    return default


def _collect_targets_from_context(context: dict | None = None) -> list[dict]:
    """
    استخراج المستهدفين من:
    1) targets الجاهزة إن وُجدت
    2) fallback fields المفردة للأدمن / المالك / الشركة
    """
    ctx = context or {}
    cleaned_targets: list[dict] = []
    seen_keys: set[str] = set()

    def _append_target(*, phone="", email="", name="", role="user", user=None):
        normalized_phone = _normalize_phone(phone)
        normalized_email = _normalize_email(email)
        safe_name = _clean_text(name, "User")
        safe_role = _clean_text(role, "user")

        key = normalized_phone or normalized_email or f"user:{getattr(user, 'id', None)}"
        if not key or key in seen_keys:
            return

        seen_keys.add(key)
        cleaned_targets.append(
            {
                "phone": normalized_phone,
                "email": normalized_email,
                "name": safe_name,
                "role": safe_role,
                "user": user,
            }
        )

    # --------------------------------------------------------
    # 1) targets الجاهزة
    # --------------------------------------------------------
    raw_targets = ctx.get("targets")
    if isinstance(raw_targets, list):
        for item in raw_targets:
            if not isinstance(item, dict):
                continue

            _append_target(
                phone=item.get("phone"),
                email=item.get("email"),
                name=item.get("name"),
                role=item.get("role", "user"),
                user=item.get("user"),
            )

    # --------------------------------------------------------
    # 2) fallback للأدمن
    # --------------------------------------------------------
    _append_target(
        phone=_context_first(ctx, ["admin_phone", "admin_draft_phone"]),
        email=_context_first(ctx, ["admin_email"]),
        name=_context_first(ctx, ["admin_name", "admin_username"], "Admin"),
        role="admin",
    )

    # --------------------------------------------------------
    # 3) fallback لمالك الشركة
    # --------------------------------------------------------
    _append_target(
        phone=_context_first(ctx, ["company_owner_phone"]),
        email=_context_first(ctx, ["company_owner_email", "owner_email"]),
        name=_context_first(ctx, ["company_owner_name", "owner_name"], "Owner"),
        role="owner",
    )

    # --------------------------------------------------------
    # 4) fallback للشركة نفسها
    # --------------------------------------------------------
    _append_target(
        phone=_context_first(ctx, ["company_phone", "company_draft_phone"]),
        email=_context_first(ctx, ["company_email"]),
        name=_context_first(ctx, ["company_name"], "Company"),
        role="company",
    )

    return cleaned_targets


def _build_target_from_user(user, *, default_role: str = "user") -> dict | None:
    if not user:
        return None

    email = _normalize_email(getattr(user, "email", ""))
    phone = _safe_get_user_phone(user)
    name = _safe_user_display_name(user, default="User")

    if not email and not phone:
        return None

    return {
        "phone": phone,
        "email": email,
        "name": name,
        "role": default_role,
        "user": user,
    }


def _dedupe_targets(targets: list[dict]) -> list[dict]:
    result: list[dict] = []
    seen_keys: set[str] = set()

    for item in targets:
        if not isinstance(item, dict):
            continue

        phone = _normalize_phone(item.get("phone"))
        email = _normalize_email(item.get("email"))
        name = _clean_text(item.get("name"), "User")
        role = _clean_text(item.get("role"), "user")
        user = item.get("user")

        key = phone or email or f"user:{getattr(user, 'id', None)}"
        if not key or key in seen_keys:
            continue

        seen_keys.add(key)
        result.append(
            {
                "phone": phone,
                "email": email,
                "name": name,
                "role": role,
                "user": user,
            }
        )

    return result


def _extract_invoice_email_attachments(context: dict | None = None) -> list[dict]:
    ctx = context or {}

    pdf_bytes = ctx.get("invoice_pdf_bytes")
    pdf_filename = _clean_text(ctx.get("invoice_pdf_filename"), "invoice.pdf")

    if not pdf_bytes:
        return []

    return [
        {
            "filename": pdf_filename,
            "content": pdf_bytes,
            "mimetype": "application/pdf",
        }
    ]


def _html_page(title: str, intro: str, sections_html: str, cta_text: str = "", cta_link: str = "") -> str:
    safe_title = escape(title)
    safe_intro = escape(intro)

    cta_block = ""
    if _clean_text(cta_text) and _clean_text(cta_link):
        cta_block = f"""
        <div style="margin-top:24px;text-align:center;">
          <a href="{escape(cta_link)}"
             style="display:inline-block;background:#111827;color:#ffffff;text-decoration:none;
                    padding:12px 22px;border-radius:12px;font-weight:700;font-size:14px;">
            {escape(cta_text)}
          </a>
        </div>
        """

    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{safe_title}</title>
</head>
<body style="margin:0;padding:0;background:#f5f7fb;font-family:Tahoma,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f7fb;padding:28px 0;">
    <tr>
      <td align="center">
        <table width="680" cellpadding="0" cellspacing="0"
               style="max-width:680px;width:100%;background:#ffffff;border:1px solid #e5e7eb;
                      border-radius:22px;overflow:hidden;">
          <tr>
            <td style="background:linear-gradient(135deg,#0f172a 0%,#111827 100%);padding:30px 28px;text-align:center;">
              <div style="color:#ffffff;font-size:24px;font-weight:800;line-height:1.6;">
                Mham Cloud
              </div>
              <div style="color:#cbd5e1;font-size:14px;line-height:1.9;margin-top:6px;">
                نظام احترافي لإدارة الشركات والموارد البشرية والاشتراكات
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:30px 28px;">
              <div style="font-size:24px;font-weight:800;color:#111827;line-height:1.6;margin-bottom:12px;">
                {safe_title}
              </div>

              <div style="font-size:15px;color:#475569;line-height:2;margin-bottom:20px;">
                {safe_intro}
              </div>

              {sections_html}

              {cta_block}

              <div style="margin-top:28px;padding-top:18px;border-top:1px solid #e5e7eb;
                          font-size:12px;color:#94a3b8;line-height:1.9;text-align:center;">
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


def _html_info_card(title: str, rows: list[tuple[str, str]]) -> str:
    rendered_rows = []
    for label, value in rows:
        rendered_rows.append(
            f"""
            <tr>
              <td style="padding:10px 12px;border:1px solid #e5e7eb;background:#f8fafc;
                         font-weight:700;color:#111827;width:34%;">
                {escape(label)}
              </td>
              <td style="padding:10px 12px;border:1px solid #e5e7eb;color:#334155;">
                {escape(value or "-")}
              </td>
            </tr>
            """.strip()
        )

    return f"""
    <div style="margin-top:18px;">
      <div style="font-size:16px;font-weight:800;color:#111827;margin-bottom:10px;">
        {escape(title)}
      </div>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse;border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;">
        {''.join(rendered_rows)}
      </table>
    </div>
    """.strip()


def _build_draft_created_email_html(
    *,
    company_name: str,
    plan_name: str,
    duration: str,
    payment_method: str,
    total_amount: str,
    draft_id: str,
    admin_name: str,
    admin_username: str,
    admin_email: str,
    admin_phone: str,
    register_url: str,
) -> str:
    sections = "".join([
        _html_info_card(
            "بيانات الشركة",
            [
                ("اسم الشركة", company_name),
                ("رقم المسودة", draft_id),
            ],
        ),
        _html_info_card(
            "بيانات الاشتراك",
            [
                ("الباقة", plan_name),
                ("المدة", duration),
                ("طريقة الدفع", payment_method),
                ("الإجمالي", _format_money(total_amount)),
            ],
        ),
        _html_info_card(
            "بيانات مسؤول الشركة",
            [
                ("اسم المسؤول", admin_name),
                ("اسم المستخدم", admin_username),
                ("البريد الإلكتروني", admin_email),
                ("رقم الجوال", admin_phone),
            ],
        ),
    ])

    return _html_page(
        title="تم إنشاء طلب تسجيل الشركة بنجاح",
        intro="تم استلام طلب التسجيل بنجاح. يمكنك الآن مراجعة الطلب ومتابعة خطوات التأكيد والدفع.",
        sections_html=sections,
        cta_text="متابعة الطلب",
        cta_link=register_url,
    )


def _build_draft_confirmed_email_html(
    *,
    company_name: str,
    plan_name: str,
    total_amount: str,
    draft_id: str,
    register_url: str,
) -> str:
    sections = "".join([
        _html_info_card(
            "تفاصيل الطلب",
            [
                ("اسم الشركة", company_name),
                ("رقم المسودة", draft_id),
                ("الباقة", plan_name),
                ("الإجمالي", _format_money(total_amount)),
            ],
        ),
    ])

    return _html_page(
        title="تم تأكيد طلب التسجيل",
        intro="تم تأكيد الطلب بنجاح، والخطوة التالية هي إتمام الدفع واعتماد العملية لتفعيل الشركة والاشتراك.",
        sections_html=sections,
        cta_text="استكمال التسجيل",
        cta_link=register_url,
    )


def _build_payment_confirmed_email_html(
    *,
    company_name: str,
    plan_name: str,
    invoice_number: str,
    total_amount: str,
    payment_method: str,
    gateway_status: str,
    gateway_transaction_id: str,
    admin_name: str,
    admin_username: str,
    admin_email: str,
    owner_email: str,
    login_url: str,
) -> str:
    sections = "".join([
        _html_info_card(
            "تفاصيل التفعيل",
            [
                ("اسم الشركة", company_name),
                ("الباقة", plan_name),
                ("رقم الفاتورة", invoice_number),
                ("الإجمالي", _format_money(total_amount)),
            ],
        ),
        _html_info_card(
            "بيانات الدفع",
            [
                ("طريقة الدفع", payment_method),
                ("حالة البوابة", gateway_status),
                ("مرجع العملية", gateway_transaction_id),
            ],
        ),
        _html_info_card(
            "بيانات الدخول والإدارة",
            [
                ("اسم المسؤول", admin_name),
                ("اسم المستخدم", admin_username),
                ("بريد المسؤول", admin_email),
                ("بريد المالك", owner_email),
            ],
        ),
    ])

    return _html_page(
        title="تم تأكيد الدفع وتفعيل الشركة بنجاح",
        intro="اكتملت عملية الدفع بنجاح وتم إنشاء الشركة وتفعيل الاشتراك. يمكنك الآن تسجيل الدخول والبدء باستخدام المنصة.",
        sections_html=sections,
        cta_text="تسجيل الدخول",
        cta_link=login_url,
    )


def _dispatch_to_targets(
    *,
    targets: list[dict],
    title: str,
    message: str,
    notification_type: str,
    severity: str,
    event_code: str,
    event_group: str,
    company=None,
    actor=None,
    link: str | None = None,
    base_context: dict | None = None,
    target_object=None,
    template_key: str | None = None,
    email_subject: str | None = None,
    email_text_message: str | None = None,
    email_html_message: str | None = None,
    email_attachments: list[dict] | None = None,
    create_in_app_for_user: bool = True,
) -> list[dict]:
    """
    نعيد قائمة summaries بدل الاعتماد على note فقط،
    لأن create_notification قد يرسل email/whatsapp بنجاح
    حتى لو لم ينشئ In-App note.
    """
    processed_results: list[dict] = []

    safe_base_context = _json_safe_context(base_context)

    for target in _dedupe_targets(targets):
        user = target.get("user")
        phone = _normalize_phone(target.get("phone"))
        email = _normalize_email(target.get("email"))
        name = _clean_text(target.get("name"), "User")
        role = _clean_text(target.get("role"), "user")

        send_email = bool(email)
        send_whatsapp = bool(phone)
        create_in_app = bool(create_in_app_for_user and user)

        if not user and not send_email and not send_whatsapp:
            continue

        context = _merge_context(
            safe_base_context,
            {
                "recipient_name": name,
                "recipient_email": email,
                "recipient_phone": phone,
                "recipient_role": role,
            },
        )

        note = create_notification(
            recipient=user,
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
            target_user=user if user else None,
            language_code=_resolve_language_code(user),
            source=f"notification_center.services_onboarding.{event_code}",
            context=context,
            target_object=target_object,
            template_key=template_key or event_code,
            whatsapp_phone=phone,
            whatsapp_recipient_name=name,
            whatsapp_recipient_role=role,
            email_recipients=[email] if email else None,
            email_subject=email_subject,
            email_text_message=email_text_message,
            email_html_message=email_html_message,
            email_attachments=email_attachments if send_email else None,
            create_in_app=create_in_app,
        )

        processed_results.append(
            {
                "user_id": getattr(user, "id", None) if user else None,
                "email": email,
                "phone": phone,
                "name": name,
                "role": role,
                "send_email": send_email,
                "send_whatsapp": send_whatsapp,
                "create_in_app": create_in_app,
                "notification_created": bool(note),
            }
        )

    return processed_results


# ============================================================
# 🧾 Draft Created
# ============================================================

def notify_onboarding_draft_created(
    *,
    actor=None,
    user=None,
    draft=None,
    plan=None,
    extra_context: dict | None = None,
    context: dict | None = None,
) -> dict:
    final_context = _json_safe_context(_merge_context(context, extra_context))

    company_name = _company_display_name(draft=draft, context=final_context)
    plan_name = _plan_display_name(plan=plan, draft=draft, context=final_context)
    draft_id = _clean_text(getattr(draft, "id", None) or final_context.get("draft_id"), "-")
    duration = _clean_text(getattr(draft, "duration", "") or final_context.get("duration"), "-")
    total_amount = _clean_text(
        getattr(draft, "total_amount", "") or final_context.get("total_amount"),
        "-",
    )
    payment_method = _clean_text(
        getattr(draft, "payment_method", "") or final_context.get("payment_method"),
        "-",
    )
    admin_name = _clean_text(getattr(draft, "admin_name", "") or final_context.get("admin_name"), "-")
    admin_username = _clean_text(getattr(draft, "admin_username", "") or final_context.get("admin_username"), "-")
    admin_email = _clean_text(getattr(draft, "admin_email", "") or final_context.get("admin_email"), "-")
    admin_phone = _clean_text(
        final_context.get("admin_phone") or final_context.get("admin_draft_phone"),
        "-",
    )

    title = "تم إنشاء طلب تسجيل الشركة بنجاح"
    message = (
        f"تم إنشاء طلب تسجيل جديد للشركة: {company_name}.\n"
        f"رقم المسودة: {draft_id}\n"
        f"الباقة: {plan_name}\n"
        f"مدة الاشتراك: {duration}\n"
        f"طريقة الدفع: {payment_method}\n"
        f"الإجمالي: {_format_money(total_amount)}\n"
        f"اسم المسؤول: {admin_name}\n"
        f"اسم المستخدم: {admin_username}\n"
        "يمكنك متابعة الطلب وإكمال خطوات الدفع من صفحة التسجيل."
    )

    link = _register_url(
        draft_id=draft_id,
        plan_name=plan_name,
        plan_id=getattr(plan, "id", None) or final_context.get("plan_id"),
    )

    html_body = _build_draft_created_email_html(
        company_name=company_name,
        plan_name=plan_name,
        duration=duration,
        payment_method=payment_method,
        total_amount=total_amount,
        draft_id=draft_id,
        admin_name=admin_name,
        admin_username=admin_username,
        admin_email=admin_email,
        admin_phone=admin_phone,
        register_url=link,
    )

    targets: list[dict] = []

    owner_target = _build_target_from_user(user, default_role="owner")
    if owner_target:
        targets.append(owner_target)

    targets.extend(_collect_targets_from_context(final_context))

    created = _dispatch_to_targets(
        targets=targets,
        title=title,
        message=message,
        notification_type="onboarding",
        severity="info",
        event_code="onboarding_draft_created",
        event_group="onboarding",
        company=None,
        actor=actor,
        link=link,
        base_context=final_context,
        target_object=draft,
        template_key="onboarding_draft_created",
        email_subject=f"Mham Cloud | تم إنشاء طلب تسجيل الشركة - {company_name}",
        email_text_message=message,
        email_html_message=html_body,
        create_in_app_for_user=True,
    )

    return {
        "ok": True,
        "notification_count": len(created),
        "draft_id": draft_id,
        "event_code": "onboarding_draft_created",
    }


def notify_draft_created(**kwargs):
    return notify_onboarding_draft_created(**kwargs)


def send_onboarding_draft_created_notification(**kwargs):
    return notify_onboarding_draft_created(**kwargs)


def send_draft_created_notification(**kwargs):
    return notify_onboarding_draft_created(**kwargs)


# ============================================================
# ✅ Draft Confirmed
# ============================================================

def notify_onboarding_draft_confirmed(
    *,
    draft=None,
    extra_context: dict | None = None,
    context: dict | None = None,
) -> dict:
    final_context = _json_safe_context(_merge_context(context, extra_context))

    company_name = _company_display_name(draft=draft, context=final_context)
    draft_id = _clean_text(getattr(draft, "id", None) or final_context.get("draft_id"), "-")
    plan_name = _plan_display_name(draft=draft, context=final_context)
    total_amount = _clean_text(
        getattr(draft, "total_amount", "") or final_context.get("total_amount"),
        "-",
    )

    title = "تم تأكيد طلب التسجيل"
    message = (
        f"تم تأكيد طلب تسجيل الشركة: {company_name} بنجاح.\n"
        f"رقم المسودة: {draft_id}\n"
        f"الباقة: {plan_name}\n"
        f"الإجمالي: {_format_money(total_amount)}\n"
        "الخطوة التالية هي إتمام الدفع واعتماد العملية ليتم إنشاء الشركة وتفعيل الاشتراك."
    )

    link = _register_url(
        draft_id=draft_id,
        plan_name=plan_name,
        plan_id=final_context.get("plan_id"),
    )

    html_body = _build_draft_confirmed_email_html(
        company_name=company_name,
        plan_name=plan_name,
        total_amount=total_amount,
        draft_id=draft_id,
        register_url=link,
    )

    targets = _collect_targets_from_context(final_context)

    created = _dispatch_to_targets(
        targets=targets,
        title=title,
        message=message,
        notification_type="onboarding",
        severity="success",
        event_code="onboarding_draft_confirmed",
        event_group="onboarding",
        company=None,
        actor=None,
        link=link,
        base_context=final_context,
        target_object=draft,
        template_key="onboarding_draft_confirmed",
        email_subject=f"Mham Cloud | تم تأكيد طلب التسجيل - {company_name}",
        email_text_message=message,
        email_html_message=html_body,
        create_in_app_for_user=True,
    )

    return {
        "ok": True,
        "notification_count": len(created),
        "draft_id": draft_id,
        "event_code": "onboarding_draft_confirmed",
    }


def notify_draft_confirmed(**kwargs):
    return notify_onboarding_draft_confirmed(**kwargs)


def send_onboarding_draft_confirmed_notification(**kwargs):
    return notify_onboarding_draft_confirmed(**kwargs)


def send_draft_confirmed_notification(**kwargs):
    return notify_onboarding_draft_confirmed(**kwargs)


# ============================================================
# 💳 Payment Confirmed + Company Activated
# ============================================================

def notify_onboarding_payment_confirmed(
    *,
    actor=None,
    company=None,
    draft=None,
    subscription=None,
    invoice=None,
    admin_user=None,
    target_user=None,
    payment_method: str | None = None,
    gateway_status: str | None = None,
    gateway_transaction_id: str | None = None,
    extra_context: dict | None = None,
    context: dict | None = None,
) -> dict:
    raw_context = _merge_context(context, extra_context)
    final_context = _json_safe_context(raw_context)

    company_name = _company_display_name(company=company, draft=draft, context=final_context)
    plan_name = _plan_display_name(subscription=subscription, draft=draft, context=final_context)
    invoice_number = _clean_text(
        getattr(invoice, "invoice_number", "") or final_context.get("invoice_number"),
        "-",
    )
    total_amount = _clean_text(
        getattr(invoice, "total_amount", "") or final_context.get("total_amount"),
        "-",
    )
    payment_method = _clean_text(payment_method or final_context.get("payment_method"), "-")
    gateway_status = _clean_text(gateway_status or final_context.get("gateway_status"), "-")
    gateway_transaction_id = _clean_text(
        gateway_transaction_id or final_context.get("gateway_transaction_id"),
        "-",
    )

    admin_name = _clean_text(
        _safe_user_display_name(admin_user or target_user, default="")
        or final_context.get("admin_name"),
        "-",
    )
    admin_username = _clean_text(
        getattr(admin_user or target_user, "username", "") or final_context.get("admin_username"),
        "-",
    )
    admin_email = _clean_text(
        getattr(admin_user or target_user, "email", "") or final_context.get("admin_email"),
        "-",
    )
    owner_email = _clean_text(
        getattr(getattr(company, "owner", None), "email", "") or final_context.get("company_owner_email"),
        "-",
    )

    title = "تم تأكيد الدفع وتفعيل الشركة بنجاح"
    message = (
        f"تم تأكيد الدفع بنجاح وإنشاء الشركة وتفعيل الاشتراك.\n"
        f"اسم الشركة: {company_name}\n"
        f"الباقة: {plan_name}\n"
        f"رقم الفاتورة: {invoice_number}\n"
        f"الإجمالي: {_format_money(total_amount)}\n"
        f"طريقة الدفع: {payment_method}\n"
        f"حالة البوابة: {gateway_status}\n"
        f"مرجع العملية: {gateway_transaction_id}\n"
        f"اسم المسؤول: {admin_name}\n"
        f"اسم المستخدم: {admin_username}\n"
        f"بريد المسؤول: {admin_email}\n"
        "يمكنك الآن تسجيل الدخول والبدء باستخدام المنصة."
    )

    email_subject = f"Mham Cloud | تم تأكيد الدفع وتفعيل الشركة - {company_name}"
    link = _login_url()

    html_body = _build_payment_confirmed_email_html(
        company_name=company_name,
        plan_name=plan_name,
        invoice_number=invoice_number,
        total_amount=total_amount,
        payment_method=payment_method,
        gateway_status=gateway_status,
        gateway_transaction_id=gateway_transaction_id,
        admin_name=admin_name,
        admin_username=admin_username,
        admin_email=admin_email,
        owner_email=owner_email,
        login_url=link,
    )

    email_attachments = _extract_invoice_email_attachments(raw_context)

    targets: list[dict] = []

    admin_target = _build_target_from_user(
        admin_user or target_user,
        default_role="admin",
    )
    if admin_target:
        targets.append(admin_target)

    company_owner = getattr(company, "owner", None)
    owner_target = _build_target_from_user(company_owner, default_role="owner")
    if owner_target:
        targets.append(owner_target)

    targets.extend(_collect_targets_from_context(final_context))

    created = _dispatch_to_targets(
        targets=targets,
        title=title,
        message=message,
        notification_type="onboarding_payment",
        severity="success",
        event_code="payment_confirmed_company_activated",
        event_group="onboarding",
        company=company,
        actor=actor,
        link=link,
        base_context=final_context,
        target_object=invoice or subscription or company or draft,
        template_key="payment_confirmed_company_activated",
        email_subject=email_subject,
        email_text_message=message,
        email_html_message=html_body,
        email_attachments=email_attachments,
        create_in_app_for_user=True,
    )

    return {
        "ok": True,
        "notification_count": len(created),
        "invoice_number": invoice_number,
        "company_id": getattr(company, "id", None),
        "event_code": "payment_confirmed_company_activated",
        "attachments_count": len(email_attachments),
    }


def notify_payment_confirmed_company_activated(**kwargs):
    return notify_onboarding_payment_confirmed(**kwargs)


def send_onboarding_payment_confirmation_notification(**kwargs):
    return notify_onboarding_payment_confirmed(**kwargs)


def send_payment_confirmed_company_activated_notification(**kwargs):
    return notify_onboarding_payment_confirmed(**kwargs)