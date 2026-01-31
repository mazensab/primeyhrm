# ======================================================================
# 📌 Primey HR Cloud — Company Manager
# 📁 File: view_department.py (LEGH Edition)
# ======================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import logging
import re
import requests

from company_manager.models import Company, CompanyDepartment

# 🔌 Biotime
from biotime_center.models import BiotimeSetting
from biotime_center.biotime_api_client import BiotimeAPIClient


logger = logging.getLogger(__name__)


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
# 🧠 أدوات مساعدة — Biotime Sync Helpers
# ======================================================================

def _normalize_code(value: str, prefix: str) -> str:
    """
    توليد كود آمن لـ Biotime:
    - أحرف كبيرة
    - بدون مسافات أو رموز
    """
    base = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper())
    base = base.strip("-")[:32]
    return f"{prefix}-{base}"


def sync_department_to_biotime(company: Company, department: CompanyDepartment):
    """
    🔄 إنشاء Area + Department في Biotime بنفس اسم القسم
    - لا يكسر العملية في حال الفشل
    - يسجل الأخطاء فقط
    """

    try:
        setting = BiotimeSetting.objects.filter(company=company).first()
        if not setting:
            logger.warning("⚠️ No BiotimeSetting found for company %s", company.id)
            return

        client = BiotimeAPIClient(setting)
        token = client.get_token()
        if not token:
            logger.error("❌ Biotime token not available")
            return

        base_url = setting.server_url.rstrip("/")
        headers = {
            "Authorization": f"JWT {token}",
            "Content-Type": "application/json",
        }

        # ==========================
        # 🏗 Create Area
        # ==========================
        area_payload = {
            "area_name": department.name,
            "area_code": _normalize_code(department.name, "AREA"),
        }

        areas_url = f"{base_url}/personnel/api/areas/"
        area_res = requests.post(
            areas_url,
            json=area_payload,
            headers=headers,
            timeout=20
        )

        logger.info(
            "🌍 Biotime Area Create [%s]: %s",
            area_res.status_code,
            area_res.text[:300]
        )

        # ==========================
        # 🏢 Create Department
        # ==========================
        dept_payload = {
            "dept_name": department.name,
            "dept_code": _normalize_code(department.name, "DEPT"),
        }

        departments_url = f"{base_url}/personnel/api/departments/"
        dept_res = requests.post(
            departments_url,
            json=dept_payload,
            headers=headers,
            timeout=20
        )

        logger.info(
            "🏢 Biotime Department Create [%s]: %s",
            dept_res.status_code,
            dept_res.text[:300]
        )

    except Exception as e:
        logger.exception("🔥 Biotime sync failed for department %s: %s", department.id, e)


# ======================================================================
# 📄 1) قائمة الأقسام — Department List
# ======================================================================
@login_required
@ensure_company_access
def department_list(request, company_id):

    company = get_object_or_404(Company, id=company_id)
    query = request.GET.get("q", "").strip()

    departments = CompanyDepartment.objects.filter(
        company=company,
        is_active=True
    ).order_by("-created_at")

    if query:
        departments = departments.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    return render(
        request,
        "company_manager/departments/department_list.html",
        {
            "company": company,
            "departments": departments,
            "query": query,
        }
    )


# ======================================================================
# ➕ 2) إضافة قسم جديد — Department Add
# ======================================================================
@login_required
@ensure_company_access
def department_add(request, company_id):

    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":

        name = request.POST.get("name")
        description = request.POST.get("description", "")

        if not name:
            messages.error(request, "⚠️ اسم القسم مطلوب.")
            return redirect("company_manager:department_add", company_id=company.id)

        department = CompanyDepartment.objects.create(
            company=company,
            name=name,
            description=description,
            is_active=True
        )

        # 🔄 PATCH — Sync to Biotime (Safe / Non-blocking)
        sync_department_to_biotime(company, department)

        messages.success(request, "✅ تم إضافة القسم بنجاح.")
        return redirect("company_manager:department_list", company_id=company.id)

    return render(
        request,
        "company_manager/departments/department_add.html",
        {"company": company},
    )


# ======================================================================
# ✏️ 3) تعديل قسم — Department Edit
# ======================================================================
@login_required
@ensure_company_access
def department_edit(request, company_id, department_id):

    company = get_object_or_404(Company, id=company_id)
    department = get_object_or_404(CompanyDepartment, id=department_id, company=company)

    if request.method == "POST":

        department.name = request.POST.get("name")
        department.description = request.POST.get("description", "")
        department.save()

        messages.success(request, "✔️ تم تحديث بيانات القسم.")
        return redirect("company_manager:department_list", company_id=company.id)

    return render(
        request,
        "company_manager/departments/department_edit.html",
        {
            "company": company,
            "department": department,
        }
    )


# ======================================================================
# 🗑️ 4) حذف قسم — Soft Delete
# ======================================================================
@login_required
@ensure_company_access
def department_delete(request, company_id, department_id):

    company = get_object_or_404(Company, id=company_id)
    department = get_object_or_404(CompanyDepartment, id=department_id, company=company)

    department.is_active = False
    department.save()

    messages.warning(request, "❌ تم إيقاف القسم.")
    return redirect("company_manager:department_list", company_id=company.id)


# ======================================================================
# 🔄 5) تفعيل / إيقاف قسم — Toggle
# ======================================================================
@login_required
@ensure_company_access
def department_toggle(request, company_id, department_id):

    company = get_object_or_404(Company, id=company_id)
    department = get_object_or_404(CompanyDepartment, id=department_id, company=company)

    department.is_active = not department.is_active
    department.save()

    if department.is_active:
        messages.success(request, "✅ تم تفعيل القسم.")
    else:
        messages.warning(request, "⛔ تم إيقاف القسم.")

    return redirect("company_manager:department_list", company_id=company.id)
