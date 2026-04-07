# ======================================================================
# 📌 Mham Cloud — Company Manager
# 📁 File: view_branch.py (LEGH Edition + Subscription Enforced)
# ======================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from company_manager.models import Company, CompanyBranch

# 🔐 Subscription Enforcement
from company_manager.decorators.subscription_limits import enforce_branch_limit
from company_manager.decorators.subscription_enforcement import (
    SubscriptionInactiveError,
    PlanLimitReachedError,
)


# ======================================================================
# 🔐 Minimal Access Layer — LEGH
# ======================================================================
def ensure_company_access(func):
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("auth_center:login")

        profile = getattr(request.user, "employee_profile", None)
        if not profile or not profile.company:
            return HttpResponse("🚫 لا تملك صلاحية الوصول.", status=403)

        return func(request, *args, **kwargs)
    return wrapper


# ======================================================================
# 📄 قائمة الفروع — Branch List
# ======================================================================
@login_required
@ensure_company_access
def branch_list(request, company_id):

    company = get_object_or_404(Company, id=company_id)
    query = request.GET.get("q", "").strip()

    branches = CompanyBranch.objects.filter(company=company, is_active=True)

    if query:
        branches = branches.filter(
            Q(name__icontains=query) |
            Q(city__icontains=query) |
            Q(address__icontains=query)
        )

    return render(
        request,
        "company_manager/branches/branch_list.html",
        {"company": company, "branches": branches, "query": query},
    )


# ======================================================================
# ➕ إضافة فرع — Branch Add (Subscription Enforced)
# ======================================================================
@login_required
@ensure_company_access
@enforce_branch_limit
def branch_add(request, company_id):

    company = get_object_or_404(Company, id=company_id)

    try:
        if request.method == "POST":

            name = request.POST.get("name")
            city = request.POST.get("city", "")
            address = request.POST.get("address", "")

            if not name:
                messages.error(request, "⚠️ اسم الفرع مطلوب.")
                return redirect("company_manager:branch_add", company_id=company.id)

            CompanyBranch.objects.create(
                company=company,
                name=name,
                city=city,
                address=address,
                is_active=True
            )

            messages.success(request, "✅ تم إضافة الفرع بنجاح.")
            return redirect("company_manager:branch_list", company_id=company.id)

    except SubscriptionInactiveError:
        messages.error(
            request,
            "🔒 لا يمكن إضافة فرع — اشتراك الشركة غير نشط حاليًا."
        )
        return redirect("company_manager:branch_list", company_id=company.id)

    except PlanLimitReachedError:
        messages.error(
            request,
            "🚫 تم الوصول إلى الحد الأقصى للفروع في باقتك. "
            "قم بترقية الاشتراك لإضافة فرع جديد."
        )
        return redirect("company_manager:branch_list", company_id=company.id)

    return render(
        request,
        "company_manager/branches/branch_add.html",
        {"company": company},
    )


# ======================================================================
# ✏️ تعديل فرع — Branch Edit
# ======================================================================
@login_required
@ensure_company_access
def branch_edit(request, company_id, branch_id):

    company = get_object_or_404(Company, id=company_id)
    branch = get_object_or_404(CompanyBranch, id=branch_id, company=company)

    if request.method == "POST":

        branch.name = request.POST.get("name")
        branch.city = request.POST.get("city", "")
        branch.address = request.POST.get("address", "")
        branch.save()

        messages.success(request, "✔️ تم تحديث بيانات الفرع.")
        return redirect("company_manager:branch_list", company_id=company.id)

    return render(
        request,
        "company_manager/branches/branch_edit.html",
        {"company": company, "branch": branch},
    )


# ======================================================================
# 🗑️ حذف فرع — Soft Delete
# ======================================================================
@login_required
@ensure_company_access
def branch_delete(request, company_id, branch_id):

    company = get_object_or_404(Company, id=company_id)
    branch = get_object_or_404(CompanyBranch, id=branch_id, company=company)

    branch.is_active = False
    branch.save()

    messages.warning(request, "❌ تم إيقاف الفرع.")
    return redirect("company_manager:branch_list", company_id=company.id)


# ======================================================================
# 🔄 تفعيل / إيقاف فرع — Toggle
# ======================================================================
@login_required
@ensure_company_access
def branch_toggle(request, company_id, branch_id):

    company = get_object_or_404(Company, id=company_id)
    branch = get_object_or_404(CompanyBranch, id=branch_id, company=company)

    branch.is_active = not branch.is_active
    branch.save()

    if branch.is_active:
        messages.success(request, "✅ تم تفعيل الفرع.")
    else:
        messages.warning(request, "⛔ تم إيقاف الفرع.")

    return redirect("company_manager:branch_list", company_id=company.id)
