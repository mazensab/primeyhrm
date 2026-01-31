# ===============================================================
# 📂 الملف: employee_center/views_sync.py
# 🧭 Sync Center — V24.2 Ultra Pro (Phase B1 Enabled | RBAC Fixed)
# 🚀 Live Search + Sorting + Pagination (AJAX)
# ===============================================================

import logging

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone

from company_manager.utils import company_required, permission_required
from company_manager.models import Company

from biotime_center.models import BiotimeEmployee
from .models import SyncLog, Employee

logger = logging.getLogger(__name__)


# ===============================================================
# 🔍 (A) عرض سجلات المزامنة — مع الفرز Sorting
# ===============================================================

@login_required
@company_required
@permission_required("employee_center", "view")
def sync_logs(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    # عوامل التصفية
    service = request.GET.get("service", "")
    status = request.GET.get("status", "")
    sort_by = request.GET.get("sort_by", "created_at")
    direction = request.GET.get("direction", "desc")

    # عكس الاتجاه
    sort_field = f"-{sort_by}" if direction == "desc" else sort_by

    logs = SyncLog.objects.filter(company=company)

    if service:
        logs = logs.filter(sync_type__icontains=service)

    if status:
        logs = logs.filter(status=status)

    # الفرز
    logs = logs.order_by(sort_field)

    # ترقيم الصفحات
    paginator = Paginator(logs, 20)
    page = request.GET.get("page", 1)
    logs_page = paginator.get_page(page)

    return render(request, "employee_center/sync_logs.html", {
        "company": company,
        "logs": logs_page,
        "service": service,
        "status": status,
        "sort_by": sort_by,
        "direction": direction,
    })


# ===============================================================
# 🔍 (B) AJAX — البحث الفوري + الفرز
# ===============================================================

@login_required
@company_required
@permission_required("employee_center", "view")
def sync_logs_search(request, company_id):

    query = request.GET.get("q", "")
    sort_by = request.GET.get("sort_by", "created_at")
    direction = request.GET.get("direction", "desc")

    company = get_object_or_404(Company, id=company_id)

    sort_field = f"-{sort_by}" if direction == "desc" else sort_by

    logs = SyncLog.objects.filter(company=company)

    # البحث الفوري
    if query:
        logs = logs.filter(
            Q(sync_type__icontains=query) |
            Q(status__icontains=query) |
            Q(error_message__icontains=query)
        )

    logs = logs.order_by(sort_field)

    paginator = Paginator(logs, 20)
    page = request.GET.get("page", 1)
    logs_page = paginator.get_page(page)

    html = render(
        request,
        "employee_center/partials/sync_logs_table.html",
        {
            "logs": logs_page,
            "sort_by": sort_by,
            "direction": direction,
            "service": "",
            "status": "",
        }
    )

    return HttpResponse(html)


# ===============================================================
# 👥 Sync Employees — Phase B1
# 🔗 Link Only (BiotimeEmployee → Employee.biotime_code)
# ⛔ No Employee Creation
# ⛔ No User Creation
# ===============================================================

@login_required
@company_required
@permission_required("employee_center", "view")
def sync_employees(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    started_at = timezone.now()

    total = 0
    linked = 0
    skipped = 0
    failed = 0

    biotime_employees = BiotimeEmployee.objects.all()
    total = biotime_employees.count()

    logger.info(
        f"🔵 [Phase B1] Biotime → Employee Linking started "
        f"(company={company.id}, total={total})"
    )

    with transaction.atomic():
        for bt in biotime_employees:
            try:
                biotime_code = bt.employee_id

                if not biotime_code:
                    skipped += 1
                    logger.warning("⚠️ Skipped BiotimeEmployee (missing employee_id).")
                    continue

                # 🔎 البحث عن موظف غير مرتبط داخل نفس الشركة
                employee = (
                    Employee.objects
                    .select_related("user")
                    .filter(company=company, biotime_code__isnull=True)
                    .filter(
                        Q(national_id=biotime_code) |
                        Q(user__username=biotime_code)
                    )
                    .first()
                )

                if not employee:
                    skipped += 1
                    continue

                # 🔗 ربط الموظف مع Biotime
                employee.biotime_code = biotime_code
                employee.save(update_fields=["biotime_code"])

                linked += 1

                logger.info(
                    f"✅ Linked Employee(id={employee.id}) "
                    f"with BiotimeCode={biotime_code}"
                )

            except Exception as exc:
                failed += 1
                logger.exception(
                    f"❌ Failed linking BiotimeEmployee="
                    f"{getattr(bt, 'employee_id', 'N/A')}: {exc}"
                )

    finished_at = timezone.now()

    # 🧮 تحديد حالة المزامنة
    if failed == 0:
        status = "success"
    elif linked > 0:
        status = "partial"
    else:
        status = "failed"

    # 📝 تسجيل النتيجة في SyncLog
    SyncLog.objects.create(
        company=company,
        sync_type="employees",
        status=status,
        total_records=total,
        success_count=linked,
        failed_count=failed,
        error_message=None if failed == 0 else "Some employees failed to link.",
        started_at=started_at,
        finished_at=finished_at,
    )

    return JsonResponse({
        "status": status,
        "total": total,
        "linked": linked,
        "skipped": skipped,
        "failed": failed,
        "message": (
            f"✔ Sync completed — Linked: {linked}, "
            f"Skipped: {skipped}, Failed: {failed}"
        ),
    })


# ===============================================================
# 🟦 Sync Placeholders — (جاهزة للمراحل القادمة)
# ===============================================================

@login_required
@company_required
@permission_required("employee_center", "view")
def sync_departments(request, company_id):
    return JsonResponse({
        "status": "ok",
        "action": "sync_departments",
        "message": "Sync Departments Placeholder — سيتم بناء Sync Center لاحقاً."
    })


@login_required
@company_required
@permission_required("employee_center", "view")
def sync_jobtitles(request, company_id):
    return JsonResponse({
        "status": "ok",
        "action": "sync_jobtitles",
        "message": "Sync Job Titles Placeholder — سيتم بناء Sync Center لاحقاً."
    })


# ===============================================================
# 🔵 Sync Logs — الصفحة الرئيسية (بدون AJAX)
# ===============================================================

@login_required
@company_required
@permission_required("employee_center", "view")
def sync_logs_page(request, company_id):
    """
    الصفحة الرئيسية لسجلات المزامنة.
    هذه الدالة فقط تعرض القالب الأساسي الذي يحتوي على البحث + الفرز + AJAX.
    """
    company = get_object_or_404(Company, id=company_id)
    return render(request, "employee_center/sync_logs.html", {
        "company": company,
    })


# ===============================================================
# 🔵 Sync Logs API — إرجاع البيانات للـ AJAX (نسخة جدول فقط)
# ===============================================================

@login_required
@company_required
@permission_required("employee_center", "view")
def sync_logs_api(request, company_id):
    """
    API مخصّص لإرجاع جدول السجلات فقط (للاستخدام في AJAX Pagination + Sorting)
    """
    company = get_object_or_404(Company, id=company_id)

    service = request.GET.get("service", "")
    status = request.GET.get("status", "")
    sort_by = request.GET.get("sort_by", "created_at")
    direction = request.GET.get("direction", "desc")
    page = request.GET.get("page", 1)

    sort_field = f"-{sort_by}" if direction == "desc" else sort_by

    logs = SyncLog.objects.filter(company=company)

    if service:
        logs = logs.filter(sync_type__icontains=service)

    if status:
        logs = logs.filter(status=status)

    logs = logs.order_by(sort_field)

    paginator = Paginator(logs, 20)
    logs_page = paginator.get_page(page)

    return render(
        request,
        "employee_center/partials/sync_logs_table.html",
        {
            "logs": logs_page,
            "sort_by": sort_by,
            "direction": direction,
        }
    )
