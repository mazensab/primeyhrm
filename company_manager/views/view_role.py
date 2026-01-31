# ==================================================================
# 🎛️ Company Roles — Ultra Fix V4
# Primey HR Cloud — Company Manager
# ==================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from company_manager.models import Company, CompanyRole
from company_manager.role_templates import ROLE_TEMPLATES, DEFAULT_ROLE_TEMPLATES


# ==================================================================
# 🔐 حماية مبسّطة — نفس حماية view_company
# ==================================================================
def ensure_company_access(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("auth_center:login")
        return func(request, *args, **kwargs)
    return wrapper


# ==================================================================
# 📄 1) قائمة الأدوار — Company Roles List
# ==================================================================
@login_required
@ensure_company_access
def role_list(request):
    company_id = request.GET.get("company")
    if not company_id:
        messages.error(request, "⚠️ يجب تحديد الشركة أولاً.")
        return redirect("company_manager:company_list")

    company = get_object_or_404(Company, id=company_id)
    roles = company.roles.all()

    return render(
        request,
        "company_manager/roles/role_list.html",
        {"company": company, "roles": roles},
    )


# ==================================================================
# ➕ 2) إضافة دور جديد — Add Role
# ==================================================================
@login_required
@ensure_company_access
def role_add(request):
    company_id = request.GET.get("company")
    if not company_id:
        messages.error(request, "⚠️ لا يمكن إضافة دور بدون شركة.")
        return redirect("company_manager:company_list")

    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        template_key = request.POST.get("template")

        if not name:
            messages.error(request, "⚠️ اسم الدور مطلوب.")
            return redirect(request.path + f"?company={company.id}")

        # صلاحيات من القالب
        permissions = ROLE_TEMPLATES.get(template_key, {})

        role = CompanyRole.objects.create(
            company=company,
            name=name,
            description=description,
            permissions=permissions,
        )

        messages.success(request, "✅ تم إنشاء الدور بنجاح.")
        return redirect(f"/companies/roles/?company={company.id}")

    return render(
        request,
        "company_manager/roles/role_add.html",
        {
            "company": company,
            "templates": DEFAULT_ROLE_TEMPLATES,
            "MODULES": ROLE_TEMPLATES.get("MODULES", {})
        },
    )


# ==================================================================
# ✏️ 3) تعديل دور — Edit Role
# ==================================================================
@login_required
@ensure_company_access
def role_edit(request, role_id):
    role = get_object_or_404(CompanyRole, id=role_id)
    company = role.company

    if request.method == "POST":
        role.name = request.POST.get("name")
        role.description = request.POST.get("description")
        template_key = request.POST.get("template")

        # تحديث الصلاحيات من القالب
        if template_key:
            role.permissions = ROLE_TEMPLATES.get(template_key, role.permissions)

        role.save()

        messages.success(request, "✔️ تم تحديث الدور بنجاح.")
        return redirect(f"/companies/roles/?company={company.id}")

    return render(
        request,
        "company_manager/roles/role_edit.html",
        {
            "role": role,
            "company": company,
            "templates": DEFAULT_ROLE_TEMPLATES,
            "MODULES": ROLE_TEMPLATES.get("MODULES", {})
        },
    )


# ==================================================================
# 🗑️ 4) حذف دور — Delete Role
# ==================================================================
@login_required
@ensure_company_access
def role_delete(request, role_id):
    role = get_object_or_404(CompanyRole, id=role_id)
    company = role.company

    # لا يمكن حذف دور مرتبط بمستخدمين
    if role.company_users.exists():
        messages.error(request, "❌ لا يمكن حذف دور مرتبط بمستخدمين.")
        return redirect(f"/companies/roles/?company={company.id}")

    role.delete()
    messages.warning(request, "🗑️ تم حذف الدور.")

    return redirect(f"/companies/roles/?company={company.id}")
