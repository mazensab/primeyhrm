from django.http import JsonResponse
from django.contrib.auth import get_user_model

from company_manager.models import CompanyUser
from employee_center.models import Employee
from auth_center.models import ActiveUserSession, UserProfile
from billing_center.models import CompanySubscription

User = get_user_model()


def _anonymous_payload():
    return {
        "authenticated": False,
        "user": None,
        "is_superuser": False,
        "role": None,
        "company": None,
        "company_id": None,
        "companies": [],
        "active_company_id": None,
        "subscription": {
            "apps": [],
            "apps_snapshot": [],
            "days_remaining": None,
        },
        "impersonation": {
            "active": False,
        },
    }


def _normalize_apps(value):
    """
    توحيد apps إلى list[str] آمنة
    """
    if not value:
        return []

    if isinstance(value, list):
        return [
            str(item).strip().lower()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, tuple):
        return [
            str(item).strip().lower()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, str):
        return [
            item.strip().lower()
            for item in value.split(",")
            if item.strip()
        ]

    return []


def _resolve_company_subscription(company_id):
    """
    أحدث اشتراك للشركة
    """
    if not company_id:
        return None

    return (
        CompanySubscription.objects
        .select_related("plan")
        .filter(company_id=company_id)
        .order_by("-id")
        .first()
    )


def _resolve_subscription_apps_payload(auth_user, resolved_company_id):
    """
    مصدر التطبيقات الفعلي للفرونت:
    - apps_snapshot: القيمة الخام المخزنة على الاشتراك
    - apps: القيمة الفعالة المستخدمة في الواجهة

    القرار المعتمد هنا:
    1) إذا كانت plan.apps موجودة وتختلف عن apps_snapshot → نعتمد plan.apps
       لأن هذا يغطي حالة تغيير الباقة بدون مزامنة snapshot بعد
    2) إذا لم توجد plan.apps نستخدم apps_snapshot
    3) وإلا []
    """
    empty = {
        "apps": [],
        "apps_snapshot": [],
    }

    if auth_user.is_superuser:
        return empty

    subscription = _resolve_company_subscription(resolved_company_id)
    if not subscription:
        return empty

    raw_snapshot = _normalize_apps(
        getattr(subscription, "apps_snapshot", None)
    )

    plan_apps = _normalize_apps(
        getattr(getattr(subscription, "plan", None), "apps", None)
    )

    # ------------------------------------------------
    # ✅ Effective apps for frontend
    # ------------------------------------------------
    effective_apps = []

    if plan_apps and plan_apps != raw_snapshot:
        effective_apps = plan_apps
    elif raw_snapshot:
        effective_apps = raw_snapshot
    elif plan_apps:
        effective_apps = plan_apps

    return {
        "apps": effective_apps,
        "apps_snapshot": raw_snapshot,
    }


def _resolve_days_remaining(auth_user, resolved_company_id):
    """
    حساب الأيام المتبقية من الاشتراك بشكل آمن
    """
    if auth_user.is_superuser:
        return None

    subscription = _resolve_company_subscription(resolved_company_id)
    if not subscription or not getattr(subscription, "end_date", None):
        return None

    try:
        from django.utils.timezone import now
        remaining = (subscription.end_date - now().date()).days
        return remaining
    except Exception:
        return None


def apiWhoAmI(request):
    user = request.user

    # ============================================================
    # 🔒 Anonymous (NO 401 — avoid redirect loops)
    # ============================================================
    if not user.is_authenticated:
        return JsonResponse(_anonymous_payload(), status=200)

    # ============================================================
    # 👤 Base User Payload
    # ============================================================

    profile = (
        UserProfile.objects
        .filter(user=user)
        .only("avatar_url", "phone_number", "whatsapp_number")
        .first()
    )

    avatar = None
    phone = None

    if profile:
        if profile.avatar_url:
            avatar = profile.avatar_url

        phone = profile.phone_number or profile.whatsapp_number or None

    user_payload = {
        "id": user.id,
        "username": user.username,
        "email": user.email or None,
        "full_name": (user.get_full_name() or "").strip() or user.username,
        "avatar": avatar,
        "phone": phone,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }

    # ============================================================
    # 🏢 ALL USER COMPANIES (MULTI-TENANT SOURCE OF TRUTH)
    # ============================================================
    companies = []
    active_company = None
    company_id = None

    group_names = set(user.groups.values_list("name", flat=True))

    is_internal_system_user = (
        user.is_superuser
        or "SYSTEM_ADMIN" in group_names
        or "SUPPORT" in group_names
    )

    role = "system" if is_internal_system_user else "company"

    company_links_qs = (
        CompanyUser.objects
        .select_related("company")
        .filter(user=user, is_active=True)
        .order_by("-id")
    )

    company_links = list(company_links_qs)

    for link in company_links:
        if not link.company:
            continue

        companies.append(
            {
                "id": link.company.id,
                "name": link.company.name,
                "role": (
                    link.role.lower()
                    if link.role
                    else "company"
                ),
            }
        )

    # ============================================================
    # 🔐 Impersonation State
    # ============================================================
    impersonation_active = bool(request.session.get("impersonation_active"))
    impersonation_company_id = request.session.get("impersonation_company_id")
    impersonation_payload = {
        "active": impersonation_active,
        "source_user_id": request.session.get("impersonation_source_user_id"),
        "source_username": request.session.get("impersonation_source_username"),
        "source_email": request.session.get("impersonation_source_email"),
        "company_id": impersonation_company_id,
        "company_name": request.session.get("impersonation_company_name"),
        "company_user_id": request.session.get("impersonation_company_user_id"),
        "target_user_id": request.session.get("impersonation_target_user_id"),
        "target_username": request.session.get("impersonation_target_username"),
        "target_role": request.session.get("impersonation_target_role"),
    }

    # ============================================================
    # Active Company (SESSION FIRST, SAFE DEFAULT SECOND)
    # ============================================================
    preferred_company_id = (
        impersonation_company_id
        or request.session.get("active_company_id")
    )

    primary_link = None

    if preferred_company_id:
        for link in company_links:
            if link.company and link.company.id == preferred_company_id:
                primary_link = link
                break

    if primary_link is None and company_links:
        primary_link = company_links[0]

    if primary_link and primary_link.company:
        active_company = {
            "id": primary_link.company.id,
            "name": primary_link.company.name,
        }

        company_id = primary_link.company.id

        if not is_internal_system_user:
            role = (
                primary_link.role.lower()
                if primary_link.role
                else "company"
            )

        employee = (
            Employee.objects
            .filter(
                user=user,
                company=primary_link.company,
            )
            .only("full_name")
            .first()
        )

        if employee and employee.full_name:
            user_payload["full_name"] = employee.full_name

    # ============================================================
    # 📦 Subscription Apps (COMPANY SCOPED)
    # ============================================================
    subscription_payload = _resolve_subscription_apps_payload(user, company_id)

    # ============================================================
    # ⏳ Subscription Status
    # ============================================================
    days_remaining = _resolve_days_remaining(user, company_id)

    # ============================================================
    # 🔐 Ω+ SESSION SYNC LAYER (PATCH ONLY)
    # ============================================================
    session_key = request.session.session_key
    session_version = request.session.get("session_version", 1)

    try:
        if session_key:
            active_session = (
                ActiveUserSession.objects
                .filter(
                    session_key=session_key,
                    is_active=True,
                )
                .only("session_version")
                .first()
            )

            if active_session:
                session_version = active_session.session_version
            else:
                request.session.flush()
                return JsonResponse(_anonymous_payload(), status=200)

    except Exception:
        pass

    # ============================================================
    # ✅ FINAL RESPONSE (ENTERPRISE CONTRACT)
    # ============================================================
    return JsonResponse(
        {
            "authenticated": True,
            "user": user_payload,
            "is_superuser": user.is_superuser,
            "role": role,

            "company": active_company,
            "company_id": company_id,
            "active_company_id": company_id,

            "companies": companies,

            "subscription": {
                "apps": subscription_payload["apps"],
                "apps_snapshot": subscription_payload["apps_snapshot"],
                "days_remaining": days_remaining,
            },

            "impersonation": impersonation_payload,

            "session": {
                "key": session_key,
                "version": session_version,
            },
        },
        status=200,
    )