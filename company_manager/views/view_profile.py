# ======================================================================
# 📌 Mham Cloud — Company Manager — CompanyProfile Views
# 📌 File: view_profile.py (V28 Ultra Stable)
# ======================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from ..models import Company, CompanyProfile


# ======================================================================
# 🔐 حماية الشركة
# ======================================================================

def ensure_company_access(func):
    """🔒 التأكد أن المستخدم ينتمي لشركة"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("auth_center:login")
        profile = getattr(request.user, "employee_profile", None)
        if not profile or not profile.company:
            return render(request, "errors/403.html", status=403)
        return func(request, *args, **kwargs)
    return wrapper


# ======================================================================
# ⚙️ Company Settings — General Info
# ======================================================================

@login_required
@ensure_company_access
def company_settings(request, company_id):
    """
    ⚙️ الإعدادات العامة للشركة:
    - اسم الشركة
    - الدومين
    - النشاط
    - اللغة، العملة، المنطقة الزمنية
    """
    company = get_object_or_404(Company, id=company_id)
    profile, _ = CompanyProfile.objects.get_or_create(company=company)

    if request.method == "POST":

        # تحديث بيانات الشركة
        company.name = request.POST.get("name", company.name)
        company.domain = request.POST.get("domain", company.domain)
        company.industry = request.POST.get("industry", company.industry)
        company.save()

        # تحديث بيانات الملف
        profile.language = request.POST.get("language", profile.language)
        profile.currency = request.POST.get("currency", profile.currency)
        profile.timezone = request.POST.get("timezone", profile.timezone)
        profile.save()

        messages.success(request, "✔️ تم تحديث الإعدادات العامة.")
        return redirect("company_manager:company_settings", company_id=company.id)

    return render(request, "company_manager/settings/company_settings.html", {
        "company": company,
        "profile": profile,
    })


# ======================================================================
# 🎨 Company Branding (Logo + Theme)
# ======================================================================

@login_required
@ensure_company_access
def company_settings_branding(request, company_id):
    """
    🎨 تغيير شعار الشركة + الثيم
    """
    company = get_object_or_404(Company, id=company_id)
    profile, _ = CompanyProfile.objects.get_or_create(company=company)

    if request.method == "POST":

        if "logo" in request.FILES:
            profile.logo = request.FILES["logo"]

        profile.theme = request.POST.get("theme", profile.theme)
        profile.save()

        messages.success(request, "🎨 تم تحديث الهوية البصرية.")
        return redirect("company_manager:company_settings_branding", company_id=company.id)

    return render(request, "company_manager/settings/company_branding.html", {
        "company": company,
        "profile": profile
    })


# ======================================================================
# 🧩 Company Modules / Feature Flags
# ======================================================================

@login_required
@ensure_company_access
def company_settings_modules(request, company_id):
    """
    🧩 تفعيل أو تعطيل وحدات النظام
    """
    company = get_object_or_404(Company, id=company_id)
    profile, _ = CompanyProfile.objects.get_or_create(company=company)

    available_modules = {
        "EMPLOYEE_CENTER": "إدارة الموظفين",
        "ATTENDANCE_CENTER": "الحضور والانصراف",
        "LEAVE_CENTER": "الإجازات",
        "PAYROLL_CENTER": "الرواتب",
        "PERFORMANCE_CENTER": "التقييم",
        "DOCUMENT_CENTER": "وثائق الشركة",
    }

    if request.method == "POST":
        selected = request.POST.getlist("modules")
        profile.features = selected
        profile.save()

        messages.success(request, "🧩 تم تحديث الوحدات.")
        return redirect("company_manager:company_settings_modules", company_id=company.id)

    return render(request, "company_manager/settings/company_modules.html", {
        "company": company,
        "profile": profile,
        "available_modules": available_modules,
    })


# ======================================================================
# 🔔 Notifications Settings
# ======================================================================

@login_required
@ensure_company_access
def company_settings_notifications(request, company_id):
    """
    🔔 إعدادات الإشعارات:
    - البريد الإلكتروني
    - الإشعارات الداخلية
    """
    company = get_object_or_404(Company, id=company_id)
    profile, _ = CompanyProfile.objects.get_or_create(company=company)

    settings = profile.settings or {}

    if request.method == "POST":
        settings["notify_email"] = request.POST.get("notify_email", "on")
        settings["notify_system"] = request.POST.get("notify_system", "on")

        profile.settings = settings
        profile.save()

        messages.success(request, "🔔 تم تحديث إعدادات الإشعارات.")
        return redirect("company_manager:company_settings_notifications", company_id=company.id)

    return render(request, "company_manager/settings/company_notifications.html", {
        "company": company,
        "profile": profile,
        "settings": settings,
    })


# ======================================================================
# 🔐 Company Security Settings
# ======================================================================

@login_required
@ensure_company_access
def company_settings_security(request, company_id):
    """
    🔐 إعدادات الأمان:
    - تفعيل الدعوات فقط
    - قفل تعديل الأدوار
    """
    company = get_object_or_404(Company, id=company_id)
    profile, _ = CompanyProfile.objects.get_or_create(company=company)

    settings = profile.settings or {}

    if request.method == "POST":
        settings["invite_only"] = request.POST.get("invite_only", "off")
        settings["lock_role_edit"] = request.POST.get("lock_role_edit", "off")

        profile.settings = settings
        profile.save()

        messages.success(request, "🔐 تم تحديث إعدادات الأمان.")
        return redirect("company_manager:company_settings_security", company_id=company.id)

    return render(request, "company_manager/settings/company_security.html", {
        "company": company,
        "profile": profile,
        "settings": settings,
    })
