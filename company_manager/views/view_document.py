# ======================================================================
# 📌 Mham Cloud — Company Manager
# 📁 File: view_document.py (LEGH Edition)
# ======================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse

from company_manager.models import (
    Company,
    CompanyDocument,
)


# ======================================================================
# 🔐 حماية الوصول — ensure_company_access
# ======================================================================
def ensure_company_access(func):
    """تحقق سريع من أن المستخدم ينتمي لشركة."""
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("auth_center:login")

        profile = getattr(request.user, "employee_profile", None)
        if not profile or not profile.company:
            return HttpResponse("🚫 لا تملك صلاحية الوصول.", status=403)

        return func(request, *args, **kwargs)

    return wrapper


# ======================================================================
# 📄 1) قائمة الوثائق — Documents List
# ======================================================================
@login_required
@ensure_company_access
def documents_list(request, company_id):

    company = get_object_or_404(Company, id=company_id)
    query = request.GET.get("q", "").strip()

    documents = CompanyDocument.objects.filter(
        company=company,
        is_active=True
    ).order_by("-uploaded_at")

    if query:
        documents = documents.filter(
            Q(description__icontains=query) |
            Q(file__icontains=query) |
            Q(uploaded_by__first_name__icontains=query) |
            Q(uploaded_by__email__icontains=query)
        )

    return render(
        request,
        "company_manager/documents/documents_list.html",
        {
            "company": company,
            "documents": documents,
            "query": query,
        }
    )


# ======================================================================
# ➕ 2) إضافة وثيقة — Upload Document
# ======================================================================
@login_required
@ensure_company_access
def document_add(request, company_id):

    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":

        file = request.FILES.get("file")
        description = request.POST.get("description", "")

        if not file:
            messages.error(request, "⚠️ الرجاء اختيار ملف.")
            return redirect("company_manager:document_add", company_id=company.id)

        CompanyDocument.objects.create(
            company=company,
            file=file,
            description=description,
            uploaded_by=request.user,
            is_active=True
        )

        messages.success(request, "📄 تم رفع الوثيقة بنجاح.")
        return redirect("company_manager:documents_list", company_id=company.id)

    return render(
        request,
        "company_manager/documents/document_add.html",
        {"company": company}
    )


# ======================================================================
# ✏️ 3) تعديل وصف الوثيقة — Edit Description
# ======================================================================
@login_required
@ensure_company_access
def document_edit(request, company_id, document_id):

    company = get_object_or_404(Company, id=company_id)
    document = get_object_or_404(CompanyDocument, id=document_id, company=company)

    if request.method == "POST":

        document.description = request.POST.get("description", "")
        document.save()

        messages.success(request, "✔️ تم تحديث وصف الوثيقة.")
        return redirect("company_manager:documents_list", company_id=company.id)

    return render(
        request,
        "company_manager/documents/document_edit.html",
        {
            "company": company,
            "document": document,
        }
    )


# ======================================================================
# 🗑️ 4) حذف وثيقة — Soft Delete
# ======================================================================
@login_required
@ensure_company_access
def document_delete(request, company_id, document_id):

    company = get_object_or_404(Company, id=company_id)
    document = get_object_or_404(CompanyDocument, id=document_id, company=company)

    document.is_active = False
    document.save()

    messages.warning(request, "❌ تم حذف الوثيقة.")
    return redirect("company_manager:documents_list", company_id=company.id)
