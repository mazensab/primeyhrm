# ======================================================================
# 📌 Primey HR Cloud — Company Manager
# 📁 File: view_user.py (LEGH Edition + Subscription Enforced)
# ======================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.contrib.auth import get_user_model

from company_manager.models import (
    Company,
    CompanyUser,
    CompanyRole,
)

# 🔐 Subscription Enforcement
from company_manager.decorators.subscription_limits import enforce_user_limit
from company_manager.decorators.subscription_enforcement import (
    SubscriptionInactiveError,
    PlanLimitReachedError,
)

User = get_user_model()


# ======================================================================
# 🔐 حماية الوصول — ensure_company_access
# ======================================================================
def ensure_company_access(func):
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("auth_center:login")

        # المستخدم يجب أن يكون مرتبطًا بشركة عبر CompanyUser
        if not CompanyUser.objects.filter(
            user=request.user,
            is_active=True
        ).exists():
            return HttpResponse("🚫 لا تملك صلاحية الوصول.", status=403)

        return func(request, *args, **kwargs)

    return wrapper


# ======================================================================
# ➕ إضافة مستخدم شركة — Users Limit Enforced
# ======================================================================
@login_required
@ensure_company_access
@enforce_user_limit
def user_add(request, company_id):

    company = get_object_or_404(Company, id=company_id)
    roles = CompanyRole.objects.filter(company=company)

    # المستخدمون المرتبطون بالفعل بهذه الشركة
    existing_user_ids = CompanyUser.objects.filter(
        company=company
    ).values_list("user_id", flat=True)

    # جميع مستخدمي النظام غير المضافين لهذه الشركة
    available_users = User.objects.exclude(
        id__in=existing_user_ids
    )

    try:
        if request.method == "POST":

            user_id = request.POST.get("user")
            role_id = request.POST.get("role")

            if not user_id:
                messages.error(request, "⚠️ يجب اختيار مستخدم.")
                return redirect("company_manager:user_add", company_id=company.id)

            user = get_object_or_404(User, id=user_id)

            if CompanyUser.objects.filter(
                company=company,
                user=user
            ).exists():
                messages.error(request, "⚠️ المستخدم مضاف مسبقًا لهذه الشركة.")
                return redirect("company_manager:user_add", company_id=company.id)

            role = (
                get_object_or_404(CompanyRole, id=role_id)
                if role_id else None
            )

            CompanyUser.objects.create(
                company=company,
                user=user,
                role=role,
                is_active=True
            )

            messages.success(request, "👤 تم إضافة المستخدم للشركة بنجاح.")
            return redirect("company_manager:users_list", company_id=company.id)

    except SubscriptionInactiveError:
        messages.error(
            request,
            "🔒 لا يمكن إضافة مستخدم — اشتراك الشركة غير نشط حاليًا."
        )
        return redirect("company_manager:users_list", company_id=company.id)

    except PlanLimitReachedError:
        messages.error(
            request,
            "🚫 تم الوصول إلى الحد الأقصى لمستخدمي الشركة في باقتك. "
            "قم بترقية الاشتراك لإضافة مستخدم جديد."
        )
        return redirect("company_manager:users_list", company_id=company.id)

    return render(
        request,
        "company_manager/users/user_add.html",
        {
            "company": company,
            "roles": roles,
            "available_users": available_users,
        }
    )

# ======================================================================
# 👥 قائمة مستخدمي الشركة
# ======================================================================
@login_required
@ensure_company_access
def users_list(request, company_id):

    company = get_object_or_404(Company, id=company_id)

    users = (
        CompanyUser.objects
        .select_related("user", "role")
        .filter(company=company)
        .order_by("user__username")
    )

    search = request.GET.get("search", "").strip()
    if search:
        users = users.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )

    return render(
        request,
        "company_manager/users/users_list.html",
        {
            "company": company,
            "users": users,
            "search": search,
        }
    )

# ======================================================================
# 🔁 تفعيل / تعطيل مستخدم الشركة
# ======================================================================
@login_required
@ensure_company_access
def user_toggle(request, company_id, user_id):

    company = get_object_or_404(Company, id=company_id)

    company_user = get_object_or_404(
        CompanyUser,
        id=user_id,
        company=company
    )

    company_user.is_active = not company_user.is_active
    company_user.save(update_fields=["is_active"])

    if company_user.is_active:
        messages.success(request, "✅ تم تفعيل المستخدم.")
    else:
        messages.warning(request, "⛔ تم تعطيل المستخدم.")

    return redirect(
        "company_manager:users_list",
        company_id=company.id
    )
