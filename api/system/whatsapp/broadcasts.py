# ============================================================
# 📂 api/system/whatsapp/broadcasts.py
# 🛡 System WhatsApp Broadcast APIs
# Primey HR Cloud
# ============================================================

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from api.system.whatsapp.helpers import json_bad_request, json_ok, json_server_error
from whatsapp_center.models import (
    BroadcastAudienceType,
    BroadcastStatus,
    DeliveryStatus,
    MessageType,
    RecipientType,
    ScopeType,
    TriggerSource,
    WhatsAppBroadcast,
    WhatsAppBroadcastRecipient,
)
from whatsapp_center.services import send_event_whatsapp_message
from whatsapp_center.utils import normalize_phone_number

User = get_user_model()

try:
    from company_manager.models import Company, CompanyUser
except Exception:
    Company = None
    CompanyUser = None

try:
    from auth_center.models import UserProfile
except Exception:
    UserProfile = None

try:
    from billing_center.models import CompanySubscription
except Exception:
    CompanySubscription = None


ALLOWED_MESSAGE_TYPES = {
    MessageType.TEXT,
    MessageType.DOCUMENT,
}

ALLOWED_AUDIENCE_TYPES = {
    BroadcastAudienceType.ALL_COMPANIES,
    BroadcastAudienceType.ACTIVE_COMPANIES,
    BroadcastAudienceType.EXPIRED_COMPANIES,
    BroadcastAudienceType.EXPIRING_COMPANIES,
    BroadcastAudienceType.COMPANY_ADMINS,
    BroadcastAudienceType.SYSTEM_USERS,
    BroadcastAudienceType.RAW_NUMBERS,
}

ALLOWED_STATUSES = {
    BroadcastStatus.DRAFT,
    BroadcastStatus.SCHEDULED,
    BroadcastStatus.RUNNING,
    BroadcastStatus.COMPLETED,
    BroadcastStatus.FAILED,
    BroadcastStatus.CANCELLED,
}

SYSTEM_INTERNAL_GROUPS = {"SYSTEM_ADMIN", "SUPPORT"}
COMPANY_ADMIN_LIKE_ROLES = {
    "ADMIN",
    "OWNER",
    "COMPANY_ADMIN",
    "HR_MANAGER",
    "SUPER_ADMIN",
}


@dataclass
class ResolvedRecipient:
    recipient_name: str
    recipient_phone: str
    recipient_type: str
    company_id: Optional[int] = None
    user_id: Optional[int] = None
    employee_id: Optional[int] = None


# ============================================================
# 🔧 Helpers
# ============================================================

def _json_body(request) -> dict:
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


def _normalize_raw_numbers(value) -> list[str]:
    if not value:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]

    return []


def _first_non_empty(*values) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _get_user_full_name(user) -> str:
    full_name = ""
    try:
        full_name = (user.get_full_name() or "").strip()
    except Exception:
        full_name = ""
    return full_name or getattr(user, "username", "") or "User"


def _get_user_whatsapp_phone(user) -> str:
    user_phone = _first_non_empty(
        getattr(user, "phone", ""),
        getattr(user, "phone_number", ""),
        getattr(user, "mobile", ""),
        getattr(user, "mobile_number", ""),
        getattr(user, "whatsapp_number", ""),
    )

    if user_phone:
        return user_phone

    if UserProfile is None:
        return ""

    try:
        profile = UserProfile.objects.filter(user=user).first()
    except Exception:
        profile = None

    if not profile:
        return ""

    return _first_non_empty(
        getattr(profile, "phone", ""),
        getattr(profile, "phone_number", ""),
        getattr(profile, "mobile", ""),
        getattr(profile, "mobile_number", ""),
        getattr(profile, "whatsapp_number", ""),
    )


def _get_company_phone(company) -> str:
    return _first_non_empty(
        getattr(company, "phone", ""),
        getattr(company, "phone_number", ""),
        getattr(company, "mobile", ""),
        getattr(company, "mobile_number", ""),
        getattr(company, "whatsapp_number", ""),
    )


def _get_company_name(company) -> str:
    return _first_non_empty(
        getattr(company, "name", ""),
        f"Company #{getattr(company, 'id', '')}",
    )


def _is_internal_user(user) -> bool:
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True

    try:
        group_names = set(user.groups.values_list("name", flat=True))
    except Exception:
        group_names = set()

    return bool(group_names & SYSTEM_INTERNAL_GROUPS)


def _serialize_broadcast(item: WhatsAppBroadcast) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "message_type": item.message_type,
        "audience_type": item.audience_type,
        "status": item.status,
        "scheduled_at": item.scheduled_at.isoformat() if item.scheduled_at else None,
        "started_at": item.started_at.isoformat() if item.started_at else None,
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        "recipient_count": item.total_recipients or 0,
        "total_recipients": item.total_recipients or 0,
        "sent_count": item.sent_count or 0,
        "failed_count": item.failed_count or 0,
        "message_preview": item.message_body or "",
        "message_body": item.message_body or "",
        "attachment_url": item.attachment_url or "",
        "attachment_name": item.attachment_name or "",
        "mime_type": item.mime_type or "",
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def _serialize_broadcast_recipient(item: WhatsAppBroadcastRecipient) -> dict:
    return {
        "id": item.id,
        "recipient_name": item.recipient_name,
        "recipient_phone": item.recipient_phone,
        "recipient_type": item.recipient_type,
        "delivery_status": item.delivery_status,
        "external_message_id": item.external_message_id or "",
        "failure_reason": item.failure_reason or "",
        "company_id": item.company_id,
        "user_id": item.user_id,
        "employee_id": item.employee_id,
        "sent_at": item.sent_at.isoformat() if item.sent_at else None,
        "delivered_at": item.delivered_at.isoformat() if item.delivered_at else None,
        "read_at": item.read_at.isoformat() if item.read_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _get_latest_subscription_map(company_ids: list[int]) -> dict[int, object]:
    if not company_ids or CompanySubscription is None:
        return {}

    rows = (
        CompanySubscription.objects
        .filter(company_id__in=company_ids)
        .select_related("company")
        .order_by("company_id", "-id")
    )

    latest_by_company: dict[int, object] = {}
    for row in rows:
        if row.company_id not in latest_by_company:
            latest_by_company[row.company_id] = row

    return latest_by_company


def _company_matches_audience(company, audience_type: str, latest_subscription=None) -> bool:
    if audience_type == BroadcastAudienceType.ALL_COMPANIES:
        return True

    if audience_type == BroadcastAudienceType.ACTIVE_COMPANIES:
        if latest_subscription is None:
            return False
        sub_status = str(getattr(latest_subscription, "status", "") or "").upper()
        end_date = getattr(latest_subscription, "end_date", None)
        if sub_status == "ACTIVE":
            return True
        if end_date and end_date >= timezone.now().date():
            return True
        return False

    if audience_type == BroadcastAudienceType.EXPIRED_COMPANIES:
        if latest_subscription is None:
            return True
        sub_status = str(getattr(latest_subscription, "status", "") or "").upper()
        end_date = getattr(latest_subscription, "end_date", None)
        if sub_status == "EXPIRED":
            return True
        if end_date and end_date < timezone.now().date():
            return True
        return False

    if audience_type == BroadcastAudienceType.EXPIRING_COMPANIES:
        if latest_subscription is None:
            return False
        end_date = getattr(latest_subscription, "end_date", None)
        if not end_date:
            return False
        today = timezone.now().date()
        return today <= end_date <= (today + timezone.timedelta(days=7))

    return False


def _add_resolved_recipient(
    bucket: list[ResolvedRecipient],
    seen_phones: set[str],
    *,
    phone: str,
    name: str,
    recipient_type: str,
    company_id: Optional[int] = None,
    user_id: Optional[int] = None,
    employee_id: Optional[int] = None,
) -> None:
    normalized = normalize_phone_number(phone)
    if not normalized:
        return

    if normalized in seen_phones:
        return

    seen_phones.add(normalized)
    bucket.append(
        ResolvedRecipient(
            recipient_name=(name or "").strip(),
            recipient_phone=normalized,
            recipient_type=recipient_type,
            company_id=company_id,
            user_id=user_id,
            employee_id=employee_id,
        )
    )


def _resolve_system_users_recipients() -> list[ResolvedRecipient]:
    seen_phones: set[str] = set()
    recipients: list[ResolvedRecipient] = []

    try:
        users = User.objects.filter(is_active=True).order_by("id")
    except Exception:
        users = User.objects.none()

    for user in users:
        if not _is_internal_user(user):
            continue

        phone = _get_user_whatsapp_phone(user)
        _add_resolved_recipient(
            recipients,
            seen_phones,
            phone=phone,
            name=_get_user_full_name(user),
            recipient_type=RecipientType.USER,
            user_id=user.id,
        )

    return recipients


def _resolve_company_admins_recipients() -> list[ResolvedRecipient]:
    if CompanyUser is None:
        return []

    seen_phones: set[str] = set()
    recipients: list[ResolvedRecipient] = []

    try:
        links = (
            CompanyUser.objects
            .select_related("user", "company")
            .filter(is_active=True, user__is_active=True)
            .order_by("id")
        )
    except Exception:
        links = []

    role_field_exists = False
    try:
        role_field_exists = "role" in {field.name for field in CompanyUser._meta.get_fields()}
    except Exception:
        role_field_exists = False

    for link in links:
        role_value = str(getattr(link, "role", "") or "").upper()

        if role_field_exists and role_value and role_value not in COMPANY_ADMIN_LIKE_ROLES:
            continue

        user = getattr(link, "user", None)
        company = getattr(link, "company", None)

        if not user:
            continue

        phone = _get_user_whatsapp_phone(user)
        _add_resolved_recipient(
            recipients,
            seen_phones,
            phone=phone,
            name=_get_user_full_name(user),
            recipient_type=RecipientType.COMPANY_ADMIN,
            company_id=getattr(company, "id", None),
            user_id=user.id,
        )

    return recipients


def _resolve_company_based_recipients(audience_type: str) -> list[ResolvedRecipient]:
    if Company is None:
        return []

    seen_phones: set[str] = set()
    recipients: list[ResolvedRecipient] = []

    try:
        companies = list(Company.objects.all().order_by("id"))
    except Exception:
        companies = []

    latest_map = _get_latest_subscription_map([company.id for company in companies])

    for company in companies:
        latest_subscription = latest_map.get(company.id)

        if not _company_matches_audience(
            company=company,
            audience_type=audience_type,
            latest_subscription=latest_subscription,
        ):
            continue

        company_phone = _get_company_phone(company)
        if company_phone:
            _add_resolved_recipient(
                recipients,
                seen_phones,
                phone=company_phone,
                name=_get_company_name(company),
                recipient_type=RecipientType.COMPANY,
                company_id=company.id,
            )
            continue

        owner = getattr(company, "owner", None)
        if owner:
            owner_phone = _get_user_whatsapp_phone(owner)
            _add_resolved_recipient(
                recipients,
                seen_phones,
                phone=owner_phone,
                name=_get_user_full_name(owner),
                recipient_type=RecipientType.COMPANY_ADMIN,
                company_id=company.id,
                user_id=getattr(owner, "id", None),
            )

    return recipients


def _resolve_raw_number_recipients(raw_numbers: list[str]) -> list[ResolvedRecipient]:
    seen_phones: set[str] = set()
    recipients: list[ResolvedRecipient] = []

    for raw_phone in raw_numbers:
        _add_resolved_recipient(
            recipients,
            seen_phones,
            phone=raw_phone,
            name="Raw Recipient",
            recipient_type=RecipientType.RAW,
        )

    return recipients


def _resolve_broadcast_recipients(broadcast: WhatsAppBroadcast) -> list[ResolvedRecipient]:
    if broadcast.audience_type == BroadcastAudienceType.RAW_NUMBERS:
        return _resolve_raw_number_recipients(broadcast.raw_numbers or [])

    if broadcast.audience_type == BroadcastAudienceType.SYSTEM_USERS:
        return _resolve_system_users_recipients()

    if broadcast.audience_type == BroadcastAudienceType.COMPANY_ADMINS:
        return _resolve_company_admins_recipients()

    if broadcast.audience_type in {
        BroadcastAudienceType.ALL_COMPANIES,
        BroadcastAudienceType.ACTIVE_COMPANIES,
        BroadcastAudienceType.EXPIRED_COMPANIES,
        BroadcastAudienceType.EXPIRING_COMPANIES,
    }:
        return _resolve_company_based_recipients(broadcast.audience_type)

    return []


def _build_broadcast_context(
    *,
    broadcast: WhatsAppBroadcast,
    recipient: WhatsAppBroadcastRecipient,
) -> dict:
    return {
        "message": broadcast.message_body or "",
        "broadcast_title": broadcast.title or "",
        "recipient_name": recipient.recipient_name or "",
        "recipient_phone": recipient.recipient_phone or "",
    }


# ============================================================
# 📋 List
# ============================================================

@login_required
@require_GET
def system_whatsapp_broadcasts(request):
    broadcasts = (
        WhatsAppBroadcast.objects
        .filter(scope_type=ScopeType.SYSTEM)
        .order_by("-created_at")[:100]
    )

    results = [_serialize_broadcast(item) for item in broadcasts]

    return json_ok(
        "System WhatsApp broadcasts loaded successfully",
        results=results,
        count=len(results),
    )


# ============================================================
# ➕ Create
# ============================================================

@login_required
@require_POST
def system_whatsapp_broadcast_create(request):
    body = _json_body(request)

    title = (body.get("title") or "").strip()
    message_type = (body.get("message_type") or MessageType.TEXT).strip()
    message_body = (body.get("message_body") or "").strip()
    audience_type = (
        body.get("audience_type") or BroadcastAudienceType.ALL_COMPANIES
    ).strip()
    status = (body.get("status") or BroadcastStatus.DRAFT).strip()
    raw_numbers = _normalize_raw_numbers(body.get("raw_numbers"))

    errors = {}

    if not title:
        errors["title"] = "title is required"

    if not message_body:
        errors["message_body"] = "message_body is required"

    if message_type not in ALLOWED_MESSAGE_TYPES:
        errors["message_type"] = "Invalid message_type"

    if audience_type not in ALLOWED_AUDIENCE_TYPES:
        errors["audience_type"] = "Invalid audience_type"

    if status not in ALLOWED_STATUSES:
        errors["status"] = "Invalid status"

    if audience_type == BroadcastAudienceType.RAW_NUMBERS and not raw_numbers:
        errors["raw_numbers"] = "raw_numbers is required when audience_type is RAW_NUMBERS"

    if errors:
        return json_bad_request("Validation error", errors=errors)

    try:
        total_recipients = (
            len(raw_numbers)
            if audience_type == BroadcastAudienceType.RAW_NUMBERS
            else 0
        )

        broadcast = WhatsAppBroadcast.objects.create(
            scope_type=ScopeType.SYSTEM,
            title=title,
            message_type=message_type,
            message_body=message_body,
            audience_type=audience_type,
            raw_numbers=raw_numbers,
            total_recipients=total_recipients,
            status=status,
            created_by=request.user,
        )

        return json_ok(
            "System WhatsApp broadcast created successfully",
            data=_serialize_broadcast(broadcast),
        )
    except Exception as exc:
        return json_server_error(
            "Failed to create system WhatsApp broadcast",
            error=str(exc),
        )


# ============================================================
# 🔎 Detail
# ============================================================

@login_required
@require_GET
def system_whatsapp_broadcast_detail(request, broadcast_id: int):
    try:
        broadcast = WhatsAppBroadcast.objects.get(
            id=broadcast_id,
            scope_type=ScopeType.SYSTEM,
        )
    except WhatsAppBroadcast.DoesNotExist:
        return json_bad_request("Broadcast not found")

    recipients = (
        broadcast.recipients
        .select_related("company", "user", "employee")
        .order_by("id")[:500]
    )

    return json_ok(
        "System WhatsApp broadcast detail loaded successfully",
        data=_serialize_broadcast(broadcast),
        recipients=[_serialize_broadcast_recipient(item) for item in recipients],
        recipients_count=recipients.count(),
    )


# ============================================================
# 🚀 Execute
# ============================================================

@login_required
@require_POST
def system_whatsapp_broadcast_execute(request, broadcast_id: int):
    body = _json_body(request)
    force = bool(body.get("force", False))

    try:
        broadcast = WhatsAppBroadcast.objects.get(
            id=broadcast_id,
            scope_type=ScopeType.SYSTEM,
        )
    except WhatsAppBroadcast.DoesNotExist:
        return json_bad_request("Broadcast not found")

    if broadcast.status == BroadcastStatus.RUNNING and not force:
        return json_bad_request("Broadcast is already running")

    if broadcast.status == BroadcastStatus.CANCELLED and not force:
        return json_bad_request("Cancelled broadcast cannot be executed without force=true")

    if broadcast.recipients.exists() and not force:
        return json_bad_request(
            "Broadcast already has recipients. Use force=true to rebuild and execute again."
        )

    try:
        with transaction.atomic():
            if force:
                broadcast.recipients.all().delete()
                broadcast.total_recipients = 0
                broadcast.sent_count = 0
                broadcast.failed_count = 0
                broadcast.started_at = None
                broadcast.completed_at = None
                broadcast.status = BroadcastStatus.DRAFT
                broadcast.save(
                    update_fields=[
                        "total_recipients",
                        "sent_count",
                        "failed_count",
                        "started_at",
                        "completed_at",
                        "status",
                        "updated_at",
                    ]
                )

            resolved = _resolve_broadcast_recipients(broadcast)

            if not resolved:
                broadcast.status = BroadcastStatus.FAILED
                broadcast.started_at = timezone.now()
                broadcast.completed_at = timezone.now()
                broadcast.total_recipients = 0
                broadcast.sent_count = 0
                broadcast.failed_count = 0
                broadcast.save(
                    update_fields=[
                        "status",
                        "started_at",
                        "completed_at",
                        "total_recipients",
                        "sent_count",
                        "failed_count",
                        "updated_at",
                    ]
                )
                return json_bad_request("No valid recipients found for this broadcast")

            recipient_rows = [
                WhatsAppBroadcastRecipient(
                    broadcast=broadcast,
                    company_id=item.company_id,
                    user_id=item.user_id,
                    employee_id=item.employee_id,
                    recipient_name=item.recipient_name,
                    recipient_phone=item.recipient_phone,
                    recipient_type=item.recipient_type,
                    delivery_status=DeliveryStatus.QUEUED,
                )
                for item in resolved
            ]
            WhatsAppBroadcastRecipient.objects.bulk_create(recipient_rows)

            broadcast.total_recipients = len(recipient_rows)
            broadcast.sent_count = 0
            broadcast.failed_count = 0
            broadcast.started_at = timezone.now()
            broadcast.completed_at = None
            broadcast.status = BroadcastStatus.RUNNING
            broadcast.save(
                update_fields=[
                    "total_recipients",
                    "sent_count",
                    "failed_count",
                    "started_at",
                    "completed_at",
                    "status",
                    "updated_at",
                ]
            )

        sent_count = 0
        failed_count = 0

        recipients = (
            broadcast.recipients
            .select_related("company", "user", "employee")
            .order_by("id")
        )

        for recipient in recipients:
            log = send_event_whatsapp_message(
                scope_type=ScopeType.SYSTEM,
                event_code="system_broadcast_manual",
                recipient_phone=recipient.recipient_phone,
                recipient_name=recipient.recipient_name,
                recipient_role=recipient.recipient_type,
                trigger_source=TriggerSource.BROADCAST,
                company=None,
                language_code="ar",
                context=_build_broadcast_context(
                    broadcast=broadcast,
                    recipient=recipient,
                ),
                related_model="WhatsAppBroadcast",
                related_object_id=str(broadcast.id),
                attachment_url=broadcast.attachment_url or "",
                attachment_name=broadcast.attachment_name or "",
                mime_type=broadcast.mime_type or "",
            )

            delivery_status = str(getattr(log, "delivery_status", "") or "")
            recipient.delivery_status = delivery_status or DeliveryStatus.FAILED
            recipient.external_message_id = getattr(log, "external_message_id", "") or ""
            recipient.failure_reason = getattr(log, "failure_reason", "") or ""

            if recipient.delivery_status == DeliveryStatus.SENT:
                recipient.sent_at = timezone.now()
                sent_count += 1
            elif recipient.delivery_status == DeliveryStatus.FAILED:
                failed_count += 1
            else:
                # أي حالة غير SENT نعتبرها فشلًا في هذا التنفيذ الأولي
                failed_count += 1
                if not recipient.failure_reason:
                    recipient.failure_reason = f"Unexpected delivery status: {recipient.delivery_status}"

            recipient.save(
                update_fields=[
                    "delivery_status",
                    "external_message_id",
                    "failure_reason",
                    "sent_at",
                ]
            )

        broadcast.sent_count = sent_count
        broadcast.failed_count = failed_count
        broadcast.completed_at = timezone.now()

        if sent_count > 0:
            broadcast.status = BroadcastStatus.COMPLETED
        else:
            broadcast.status = BroadcastStatus.FAILED

        broadcast.save(
            update_fields=[
                "sent_count",
                "failed_count",
                "completed_at",
                "status",
                "updated_at",
            ]
        )

        return json_ok(
            "System WhatsApp broadcast executed successfully",
            data=_serialize_broadcast(broadcast),
            stats={
                "total_recipients": broadcast.total_recipients,
                "sent_count": broadcast.sent_count,
                "failed_count": broadcast.failed_count,
            },
        )

    except Exception as exc:
        broadcast.status = BroadcastStatus.FAILED
        broadcast.completed_at = timezone.now()
        broadcast.save(update_fields=["status", "completed_at", "updated_at"])

        return json_server_error(
            "Failed to execute system WhatsApp broadcast",
            error=str(exc),
        )