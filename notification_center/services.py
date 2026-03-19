# 📂 الملف: notification_center/services.py
# 🧠 Primey HR Cloud — Smart Notification Services V5.0 (Email Ready Stable)
# 🔧 Patch:
# ------------------------------------------------------------
# ✅ توحيد إنشاء الإشعار الداخلي + البث المباشر + البريد
# ✅ احترام إعدادات SMTP من settings.py / .env
# ✅ Fail-Safe كامل: فشل البريد لا يكسر Billing / Payroll / Onboarding
# ✅ دعم EMAIL_NOTIFICATIONS_ENABLED
# ✅ دعم EMAIL_AUDIT_BCC
# ✅ عدم الاعتماد على حقول غير موجودة في Notification Model
# ✅ متوافق مع Redis / InMemory / Channels
# ------------------------------------------------------------

import logging
from typing import Iterable, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from .models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================
# 🧩 Helpers
# ============================================================
def _clean_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _email_notifications_enabled() -> bool:
    return bool(getattr(settings, "EMAIL_NOTIFICATIONS_ENABLED", True))


def _default_from_email() -> str:
    return getattr(
        settings,
        "DEFAULT_FROM_EMAIL",
        "Primey HR Cloud <no-reply@localhost>",
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


def _safe_username(user: User) -> str:
    return getattr(user, "username", None) or getattr(user, "email", None) or f"user:{getattr(user, 'id', 'unknown')}"


def _send_notification_email(
    *,
    recipient: User,
    title: str,
    message: str,
) -> bool:
    """
    ✉️ إرسال بريد الإشعار بشكل Fail-Safe.
    - لا يرفع Exception للخارج
    - يحترم تفعيل/تعطيل البريد على مستوى النظام
    """
    if not _email_notifications_enabled():
        logger.info("📭 البريد معطّل من الإعدادات: EMAIL_NOTIFICATIONS_ENABLED=False")
        return False

    recipient_email = _clean_text(getattr(recipient, "email", ""))
    if not recipient_email:
        logger.info(f"📭 لا يوجد بريد للمستخدم {_safe_username(recipient)}")
        return False

    try:
        send_mail(
            subject=f"[Primey HR Cloud] {_clean_text(title)}",
            message=_clean_text(message),
            from_email=_default_from_email(),
            recipient_list=[recipient_email],
            fail_silently=False,
            html_message=None,
        )
        logger.info(f"✅ تم إرسال بريد إشعار إلى: {recipient_email}")

        # ----------------------------------------------------
        # BCC Audit اختياري — يرسل نسخة مستقلة إذا كانت موجودة
        # حتى لا نعدل على send_mail الأساسية أو نكسر التوافق
        # ----------------------------------------------------
        audit_bcc = _audit_bcc_list()
        if audit_bcc:
            try:
                send_mail(
                    subject=f"[AUDIT COPY] [Primey HR Cloud] {_clean_text(title)}",
                    message=(
                        f"Recipient: {recipient_email}\n\n"
                        f"Title: {_clean_text(title)}\n\n"
                        f"Message:\n{_clean_text(message)}"
                    ),
                    from_email=_default_from_email(),
                    recipient_list=audit_bcc,
                    fail_silently=True,
                    html_message=None,
                )
            except Exception as audit_error:
                logger.warning(f"⚠️ فشل إرسال نسخة BCC audit (غير حرج): {audit_error}")

        return True

    except Exception as e:
        logger.warning(f"📭 فشل إرسال بريد إشعار (غير حرج): {e}")
        return False


# ============================================================
# 1️⃣ الدالة العامة لإنشاء إشعار فردي + بث مباشر + بريد
# ============================================================
def create_notification(
    *,
    recipient: User,
    title: str,
    message: str,
    notification_type: str = "system",
    severity: str = "info",
    send_email: bool = False,
    link: str | None = None,
) -> Notification | None:
    """
    🧠 إنشاء إشعار جديد وتفعيله فورًا على واجهة المستخدم.

    🔒 Enterprise Safe:
    - لا يعتمد على حقول غير موجودة في الموديل
    - فشل البريد لا يكسر العمليات الحساسة
    - متوافق مع WebSocket + Channels
    """
    if not recipient:
        logger.warning("🚫 محاولة إنشاء إشعار بدون مستلم.")
        return None

    title = _clean_text(title)
    message = _clean_text(message)
    link = _clean_text(link)

    if not title and not message:
        logger.warning("🚫 تم تجاهل إشعار فارغ (عنوان ورسالة فارغان).")
        return None

    try:
        note = Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            severity=severity,
            link=link,
        )

        # 📡 بث الإشعار فورًا عبر WebSocket
        _broadcast_live_notification(note)

        # ✉️ إرسال بريد (اختياري — Fail-Safe)
        if send_email:
            email_sent = _send_notification_email(
                recipient=recipient,
                title=note.title,
                message=note.message,
            )

            # حماية للتوافق مع أي نسخة مستقبلية من الموديل
            if email_sent and hasattr(note, "mark_as_sent_email"):
                try:
                    note.mark_as_sent_email()
                except Exception as mark_error:
                    logger.warning(f"⚠️ تعذر تحديث حالة البريد في الإشعار: {mark_error}")

        logger.info(
            f"✅ إشعار جديد أُنشئ للمستخدم {_safe_username(recipient)}: {note.title}"
        )
        return note

    except Exception as e:
        logger.error(f"❌ فشل إنشاء الإشعار (Non-Blocking): {e}")
        return None


# ============================================================
# 2️⃣ بث مباشر عبر WebSocket Channel Layer
# ============================================================
def _broadcast_live_notification(note: Notification) -> None:
    """
    📡 إرسال إشعار جديد للمجموعة المخصصة للمستخدم.
    يعمل مع Redis أو InMemory تلقائيًا.
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
                "notification": {
                    "id": note.id,
                    "title": note.title,
                    "message": note.message,
                    "notification_type": note.notification_type,
                    "severity": note.severity,
                    "link": note.link or "",
                    "created_at": timezone.localtime(note.created_at).strftime("%Y-%m-%d %H:%M"),
                },
            },
        }

        async_to_sync(channel_layer.group_send)(group_name, payload)
        logger.debug(f"📡 بث إشعار مباشر للمجموعة: {group_name}")

    except Exception as e:
        logger.warning(f"⚠️ فشل بث الإشعار الفوري: {e}")


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
) -> list[Notification]:
    """
    🔔 إرسال نفس الإشعار لمجموعة مستخدمين.
    """
    notes: list[Notification] = []
    seen_user_ids: set[int] = set()

    for user in users:
        if not user:
            continue

        user_id = getattr(user, "id", None)
        if not user_id or user_id in seen_user_ids:
            continue

        seen_user_ids.add(user_id)

        note = create_notification(
            recipient=user,
            title=title,
            message=message,
            notification_type=ntype,
            severity=severity,
            send_email=send_email,
        )
        if note:
            notes.append(note)

    return notes


# ============================================================
# 4️⃣ إعلان عام
# ============================================================
def announce_global(
    title: str,
    message: str,
    severity: str = "info",
    send_email: bool = False,
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
    )


# ============================================================
# 5️⃣ إشعار الفوترة
# ============================================================
def notify_billing_event(
    recipient: User,
    invoice_number: str,
    status: str,
    send_email: bool = False,
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
    )


# ============================================================
# 6️⃣ إشعار التقارير
# ============================================================
def notify_report_generated(
    recipient: User,
    report_title: str,
    send_email: bool = False,
) -> Notification | None:
    return create_notification(
        recipient=recipient,
        title=f"📊 تم إنشاء تقرير جديد: {report_title}",
        message=f"تم توليد التقرير ({report_title}) بنجاح وهو متاح الآن.",
        notification_type="report",
        severity="success",
        send_email=send_email,
    )


# ============================================================
# 7️⃣ إشعارات المساعد الذكي
# ============================================================
def notify_smart_assistant(
    recipient: User,
    suggestion: str,
    send_email: bool = False,
) -> Notification | None:
    return create_notification(
        recipient=recipient,
        title="🤖 تنبيه من المساعد الذكي",
        message=suggestion,
        notification_type="assistant",
        severity="info",
        send_email=send_email,
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
    link: str | None = None,
) -> list[Notification]:
    """
    🧩 Helper إضافي لاستخدامه لاحقًا في:
    - confirm_payment
    - confirm_cash_payment
    - renew_subscription
    - change_plan
    - users / reset_password
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
            link=link,
        )
        if note:
            notes.append(note)

    return notes