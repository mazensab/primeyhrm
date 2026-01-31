# ======================================================================
# 📌 Primey HR Cloud — Company Manager
# 📁 File: view_company.py (LEGH Edition - Ultra Clean 2025)
# ======================================================================

from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.timezone import now

from company_manager.models import (
    Company,
    CompanyUser,
    CompanyRole,
)
from company_manager.forms import CompanyForm

# 🔗 Billing (CompanySubscription ONLY — FINAL)
from billing_center.models import CompanySubscription

from printing_engine.services.companies_print_engine import CompaniesPrintEngine

import openpyxl
from openpyxl.styles import Font, Alignment


# ======================================================================
# 🔐 حماية الشركة — LEGH Edition (Clean & Safe)
# ======================================================================
def ensure_company_access(view_func):
    """يتأكد أن المستخدم مسجل دخول فقط — نسخة LEGH"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("auth_center:login")
        return view_func(request, *args, **kwargs)
    return wrapper


# ======================================================================
# 📄 1) قائمة الشركات — Company List
# ======================================================================
@login_required
@ensure_company_access
def company_list(request):

    query  = request.GET.get("q", "").strip()
    sort   = request.GET.get("sort", "")
    status = request.GET.get("status", "")

    companies = Company.objects.all()

    if query:
        companies = companies.filter(
            Q(name__icontains=query) |
            Q(domain__icontains=query)
        )

    if status == "active":
        companies = companies.filter(is_active=True)
    elif status == "inactive":
        companies = companies.filter(is_active=False)

    if sort == "name_asc":
        companies = companies.order_by("name")
    elif sort == "name_desc":
        companies = companies.order_by("-name")
    elif sort == "created_old":
        companies = companies.order_by("created_at")
    else:
        companies = companies.order_by("-created_at")

    total = companies.count()
    active_count = companies.filter(is_active=True).count()

    today = now().date()
    avg_age = int(
        sum((today - c.created_at.date()).days for c in companies) / total
    ) if total > 0 else 0

    paginator = Paginator(companies, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "company_manager/company_list.html",
        {
            "companies": companies,
            "page_obj": page_obj,
            "query": query,
            "sort": sort,
            "status": status,
            "active_count": active_count,
            "avg_age": avg_age,
        },
    )


# ======================================================================
# ➕ 2) إضافة شركة — 🔒 C FINAL (ACTIVE ONLY)
# ======================================================================
@login_required
@ensure_company_access
def company_add(request):

    if request.method == "POST":
        form = CompanyForm(request.POST, request.FILES)

        if form.is_valid():

            # ==========================================================
            # 🔒 REQUIRE ACTIVE CompanySubscription
            # ==========================================================
            active_subscription = (
                CompanySubscription.objects
                .filter(
                    company__companyuser__user=request.user,
                    status="ACTIVE",
                )
                .select_related("plan")
                .first()
            )

            if not active_subscription or not active_subscription.plan:
                messages.error(
                    request,
                    "🚫 لا يمكنك إنشاء شركة بدون اشتراك نشط."
                )
                return redirect("company_manager:company_list")

            used_companies = (
                CompanyUser.objects
                .filter(user=request.user, is_active=True)
                .values("company")
                .distinct()
                .count()
            )

            if used_companies >= active_subscription.plan.max_companies:
                messages.error(
                    request,
                    "🚫 وصلت إلى الحد الأقصى لعدد الشركات في باقتك."
                )
                return redirect("company_manager:company_list")

            # ==========================================================
            # ✅ إنشاء الشركة فقط
            # الاشتراك PENDING يُنشأ تلقائيًا من Signals
            # ==========================================================
            company = form.save(commit=False)
            company.is_active = True
            company.save()

            messages.success(
                request,
                "✅ تم إنشاء الشركة. الاشتراك بانتظار التفعيل."
            )
            return redirect("company_manager:company_list")

        messages.error(request, "⚠️ يوجد أخطاء في البيانات.")

    else:
        form = CompanyForm()

    return render(
        request,
        "company_manager/company_add.html",
        {"form": form},
    )


# ======================================================================
# ✏️ 3) تعديل شركة
# ======================================================================
@login_required
@ensure_company_access
def company_edit(request, company_id):

    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":
        company.name = request.POST.get("name")
        company.domain = request.POST.get("domain")
        company.industry = request.POST.get("industry", "")
        company.save()

        messages.success(request, "✔️ تم تحديث بيانات الشركة.")
        return redirect("company_manager:company_list")

    return render(
        request,
        "company_manager/company_edit.html",
        {"company": company},
    )


# ======================================================================
# 📄 4) تفاصيل شركة
# ======================================================================
@login_required
@ensure_company_access
def company_detail(request, company_id):

    company = get_object_or_404(Company, id=company_id)

    return render(
        request,
        "company_manager/company_detail.html",
        {"company": company},
    )


# ======================================================================
# 🗑️ 5) إيقاف شركة — Soft Delete
# ======================================================================
@login_required
@ensure_company_access
def company_delete(request, company_id):

    company = get_object_or_404(Company, id=company_id)
    company.is_active = False
    company.save()

    messages.warning(request, "❌ تم إيقاف الشركة.")
    return redirect("company_manager:company_list")


# ======================================================================
# 🔄 6) تفعيل / إيقاف شركة
# ======================================================================
@login_required
@ensure_company_access
def toggle_company_status(request, company_id):

    company = get_object_or_404(Company, id=company_id)
    company.is_active = not company.is_active
    company.save()

    messages.success(
        request,
        "✅ تم تفعيل الشركة." if company.is_active else "⛔ تم إيقاف الشركة."
    )

    return redirect("company_manager:company_list")


# ======================================================================
# 🧾 7) HTML Print View
# ======================================================================
@login_required
@ensure_company_access
def company_print_view(request):
    companies = Company.objects.all()
    engine = CompaniesPrintEngine(companies)
    return HttpResponse(engine.generate_html())


# ======================================================================
# 🧾 8) PDF Print View
# ======================================================================
@login_required
@ensure_company_access
def company_print_pdf(request):

    companies = Company.objects.all()
    engine = CompaniesPrintEngine(companies)
    pdf_bytes = engine.render_pdf()

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=companies.pdf"
    return response


# ======================================================================
# 🧾 9) Excel Export
# ======================================================================
@login_required
@ensure_company_access
def company_export_excel(request):

    companies = Company.objects.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Companies"

    headers = ["اسم الشركة", "الدومين", "الحالة", "تاريخ الإنشاء"]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    for c in companies:
        ws.append([
            c.name,
            c.domain,
            "نشطة" if c.is_active else "موقفة",
            c.created_at.strftime("%Y-%m-%d"),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="companies.xlsx"'
    wb.save(response)
    return response


# ======================================================================
# 👤 10) Impersonate Company — Ultra Pro
# ======================================================================
@login_required
@ensure_company_access
def impersonate_company(request, company_id):

    if not request.user.is_superuser:
        messages.error(request, "🚫 الميزة مخصصة لمالك النظام فقط.")
        return redirect("company_manager:company_list")

    company = get_object_or_404(Company, id=company_id)

    company_user, _ = CompanyUser.objects.get_or_create(
        company=company,
        user=request.user,
        defaults={"is_active": True},
    )

    owner_role, _ = CompanyRole.objects.get_or_create(
        company=company,
        name="Company Owner",
        defaults={
            "description": "Full access for company owner.",
            "permissions": {"*": True},
            "is_system_role": False,
        },
    )

    company_user.roles.add(owner_role)

    request.session["active_company_id"] = company.id
    request.session["active_company_name"] = company.name

    messages.success(request, f"✔️ تم تسجيل الدخول كشركة: {company.name}")
    return redirect(f"/employee/{company.id}/dashboard/")


# ======================================================================
# ✅ Alias Fix — keep urls stable (NO BREAKING CHANGES)
# ======================================================================
def company_pdf_view(request):
    """
    Alias for backward compatibility.
    Some urls.py expects company_pdf_view
    """
    return company_print_pdf(request)
