# ======================================================================
# 📌 Mham Cloud — Company Manager
# 📁 File: view_office.py (LEGH Edition)
# ======================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from company_manager.models import (
    Company,
    CompanyBranch,
    CompanyOffice,
)


# ======================================================================
# 🔐 حماية الوصول إلى الشركة
# ======================================================================
def ensure_company_access(func):
    """تحقّق سريع بأن المستخدم ينتمي لشركة."""
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("auth_center:login")

        profile = getattr(request.user, "employee_profile", None)
        if not profile or not profile.company:
            return HttpResponse("🚫 لا تملك صلاحية الوصول.", status=403)

        return func(request, *args, **kwargs)

    return wrapper


# ======================================================================
# 📄 1) عرض قائمة المكاتب — Offices List
# ======================================================================
@login_required
@ensure_company_access
def offices_list(request, company_id):

    company = get_object_or_404(Company, id=company_id)

    query = request.GET.get("q", "").strip()

    offices = CompanyOffice.objects.filter(
        company=company,
        is_active=True
    ).select_related("branch").order_by("-created_at")

    if query:
        offices = offices.filter(
            Q(name__icontains=query) |
            Q(branch__name__icontains=query) |
            Q(floor__icontains=query) |
            Q(room_number__icontains=query)
        )

    return render(
        request,
        "company_manager/offices/offices_list.html",
        {
            "company": company,
            "offices": offices,
            "query": query,
        }
    )


# ======================================================================
# ➕ 2) إضافة مكتب جديد — Add Office
# ======================================================================
@login_required
@ensure_company_access
def office_add(request, company_id):

    company = get_object_or_404(Company, id=company_id)
    branches = CompanyBranch.objects.filter(company=company, is_active=True)

    if request.method == "POST":

        branch_id = request.POST.get("branch")
        name = request.POST.get("name")
        floor = request.POST.get("floor", "")
        room_number = request.POST.get("room_number", "")

        if not name:
            messages.error(request, "⚠️ اسم المكتب مطلوب.")
            return redirect("company_manager:office_add", company_id=company.id)

        branch = get_object_or_404(CompanyBranch, id=branch_id, company=company)

        CompanyOffice.objects.create(
            company=company,
            branch=branch,
            name=name,
            floor=floor,
            room_number=room_number,
            is_active=True
        )

        messages.success(request, "🏢 تم إضافة المكتب بنجاح.")
        return redirect("company_manager:offices_list", company_id=company.id)

    return render(
        request,
        "company_manager/offices/office_add.html",
        {
            "company": company,
            "branches": branches,
        }
    )


# ======================================================================
# ✏️ 3) تعديل مكتب — Edit
# ======================================================================
@login_required
@ensure_company_access
def office_edit(request, company_id, office_id):

    company = get_object_or_404(Company, id=company_id)
    office = get_object_or_404(CompanyOffice, id=office_id, company=company)
    branches = CompanyBranch.objects.filter(company=company, is_active=True)

    if request.method == "POST":

        branch_id = request.POST.get("branch")
        name = request.POST.get("name")
        floor = request.POST.get("floor", "")
        room_number = request.POST.get("room_number", "")

        branch = get_object_or_404(CompanyBranch, id=branch_id, company=company)

        office.branch = branch
        office.name = name
        office.floor = floor
        office.room_number = room_number
        office.save()

        messages.success(request, "✔️ تم تحديث بيانات المكتب.")
        return redirect("company_manager:offices_list", company_id=company.id)

    return render(
        request,
        "company_manager/offices/office_edit.html",
        {
            "company": company,
            "office": office,
            "branches": branches,
        }
    )


# ======================================================================
# 🗑️ 4) حذف مكتب — Soft Delete
# ======================================================================
@login_required
@ensure_company_access
def office_delete(request, company_id, office_id):

    company = get_object_or_404(Company, id=company_id)
    office = get_object_or_404(CompanyOffice, id=office_id, company=company)

    office.is_active = False
    office.save()

    messages.warning(request, "❌ تم حذف المكتب.")
    return redirect("company_manager:offices_list", company_id=company.id)


# ======================================================================
# 🔄 5) تفعيل / إيقاف مكتب — Toggle
# ======================================================================
@login_required
@ensure_company_access
def office_toggle(request, company_id, office_id):

    company = get_object_or_404(Company, id=company_id)
    office = get_object_or_404(CompanyOffice, id=office_id, company=company)

    office.is_active = not office.is_active
    office.save()

    if office.is_active:
        messages.success(request, "✅ تم تفعيل المكتب.")
    else:
        messages.warning(request, "⛔ تم إيقاف المكتب.")

    return redirect("company_manager:offices_list", company_id=company.id)
