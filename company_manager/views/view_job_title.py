# ======================================================================
# 📌 Mham Cloud — Company Manager
# 📁 File: view_job_title.py (LEGH Edition)
# ======================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from company_manager.models import (
    Company,
    JobTitle,
)


# ======================================================================
# 🔐 حماية الوصول للشركة — LEGH
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
# 📄 1) قائمة المسميات الوظيفية — JobTitle List
# ======================================================================
@login_required
@ensure_company_access
def job_title_list(request, company_id):

    company = get_object_or_404(Company, id=company_id)
    query = request.GET.get("q", "").strip()

    job_titles = JobTitle.objects.filter(
        company=company,
        is_active=True
    ).order_by("-created_at")

    if query:
        job_titles = job_titles.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    return render(
        request,
        "company_manager/job_titles/job_title_list.html",
        {
            "company": company,
            "job_titles": job_titles,
            "query": query,
        }
    )


# ======================================================================
# ➕ 2) إضافة مسمى وظيفي — JobTitle Add
# ======================================================================
@login_required
@ensure_company_access
def job_title_add(request, company_id):

    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":

        name = request.POST.get("name")
        description = request.POST.get("description", "")

        if not name:
            messages.error(request, "⚠️ اسم المسمى مطلوب.")
            return redirect("company_manager:job_title_add", company_id=company.id)

        JobTitle.objects.create(
            company=company,
            name=name,
            description=description,
            is_active=True
        )

        messages.success(request, "✅ تم إضافة المسمى الوظيفي بنجاح.")
        return redirect("company_manager:job_title_list", company_id=company.id)

    return render(
        request,
        "company_manager/job_titles/job_title_add.html",
        {"company": company},
    )


# ======================================================================
# ✏️ 3) تعديل مسمى وظيفي — JobTitle Edit
# ======================================================================
@login_required
@ensure_company_access
def job_title_edit(request, company_id, job_id):

    company = get_object_or_404(Company, id=company_id)
    job = get_object_or_404(JobTitle, id=job_id, company=company)

    if request.method == "POST":

        job.name = request.POST.get("name")
        job.description = request.POST.get("description", "")
        job.save()

        messages.success(request, "✔️ تم تحديث بيانات المسمى الوظيفي.")
        return redirect("company_manager:job_title_list", company_id=company.id)

    return render(
        request,
        "company_manager/job_titles/job_title_edit.html",
        {
            "company": company,
            "job": job,
        }
    )


# ======================================================================
# 🗑️ 4) حذف مسمى وظيفي — Soft Delete
# ======================================================================
@login_required
@ensure_company_access
def job_title_delete(request, company_id, job_id):

    company = get_object_or_404(Company, id=company_id)
    job = get_object_or_404(JobTitle, id=job_id, company=company)

    job.is_active = False
    job.save()

    messages.warning(request, "❌ تم إيقاف المسمى الوظيفي.")
    return redirect("company_manager:job_title_list", company_id=company.id)


# ======================================================================
# 🔄 5) تفعيل / إيقاف مسمى وظيفي — Toggle
# ======================================================================
@login_required
@ensure_company_access
def job_title_toggle(request, company_id, job_id):

    company = get_object_or_404(Company, id=company_id)
    job = get_object_or_404(JobTitle, id=job_id, company=company)

    job.is_active = not job.is_active
    job.save()

    if job.is_active:
        messages.success(request, "✅ تم تفعيل المسمى الوظيفي.")
    else:
        messages.warning(request, "⛔ تم إيقاف المسمى الوظيفي.")

    return redirect("company_manager:job_title_list", company_id=company.id)
