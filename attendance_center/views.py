# ============================================================
# 📂 Attendance Center — Views V16 Ultra Pro (Final)
# ============================================================
# ✔ RBAC
# ✔ Full Biotime Integration
# ✔ AttendanceSyncService Integrated
# ✔ Policies API V2
# ✔ Exports Engine
# ------------------------------------------------------------

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

# ================================
# 📌 Models
# ================================
from attendance_center.models import (
    AttendanceRecord,
    AttendanceSetting,
    AttendanceDevice,
    AttendancePolicy,
    EmployeeAttendancePolicy,
)

from employee_center.models import Employee
from biotime_center.models import BiotimeDevice
from .biotime_api import BiotimeAPI

from django.contrib.auth.decorators import login_required
from company_manager.utils import company_required, permission_required
from attendance_center.services.sync_biotime_to_attendance import AttendanceSyncService

# ================================
# 📌 Services (Business Logic)
# ================================
from attendance_center.services.services import PolicyService, KPIService
from attendance_center.services.sync_biotime_to_attendance import AttendanceSyncService

# ================================
# 📌 Exports
# ================================
import csv
import openpyxl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


# ============================================================
# 🏠 1) Attendance List — اليوم الحالي
# ============================================================
@login_required
def attendance_list(request):
    company = request.user.company
    today = timezone.localdate()

    records = AttendanceRecord.objects.filter(
        employee__company=company,
        date=today
    ).select_related("employee")

    return render(request, "attendance_center/attendance_list.html", {
        "records": records,
        "today": today
    })


# ============================================================
# 👤 2) Detailed Attendance for Employee
# ============================================================
@login_required
def attendance_detail(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id, company=request.user.company)

    records = AttendanceRecord.objects.filter(
        employee=employee
    ).order_by("-date")

    return render(request, "attendance_center/attendance_detail.html", {
        "employee": employee,
        "records": records
    })


# ============================================================
# 📊 3) Dashboard
# ============================================================
@login_required
def attendance_dashboard(request):
    company = request.user.company
    return render(request, "attendance_center/dashboard.html", {"company": company})


# ============================================================
# 🔌 4) Biotime Test Connection
# ============================================================
@login_required
def test_biotime_connection(request):
    settings = AttendanceSetting.objects.filter(company=request.user.company).first()

    if not settings:
        return JsonResponse({"success": False, "message": "لا توجد إعدادات Biotime مفعلة"}, status=400)

    try:
        api = BiotimeAPI(settings.biotime_server_url, settings.api_key)
        api.ping()
        return JsonResponse({"success": True, "message": "الاتصال ناجح ✔"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# ============================================================
# 🛰️ 5) Devices Management
# ============================================================
@login_required
def attendance_settings_devices(request):
    company = request.user.company

    devices = AttendanceDevice.objects.filter(
        company=company
    ).select_related("device")

    return render(request, "attendance_center/biotime_devices.html", {"devices": devices})


@login_required
def sync_attendance_devices(request):
    settings = AttendanceSetting.objects.filter(company=request.user.company).first()

    if not settings:
        return JsonResponse({"success": False, "message": "لا توجد إعدادات متاحة"})

    try:
        api = BiotimeAPI(settings.biotime_server_url, settings.api_key)
        devices = api.get_devices()

        for d in devices:
            device_obj, created = BiotimeDevice.objects.get_or_create(
                device_id=d["id"],
                defaults={"device_name": d["name"]}
            )
            AttendanceDevice.objects.get_or_create(
                company=request.user.company,
                device=device_obj
            )

        return JsonResponse({"success": True, "message": "✔ تمت مزامنة الأجهزة"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


# ============================================================
# 🔄 6) Manual Attendance Sync (One-Click)
# ============================================================
@login_required
def attendance_sync(request):
    company = request.user.company

    settings = AttendanceSetting.objects.filter(company=company).first()
    if not settings:
        return JsonResponse({"success": False, "message": "لا توجد إعدادات متاحة"})

    try:
        # استخدام خدمة المزامنة الاحترافية
        sync_service = AttendanceSyncService(company)
        created = sync_service.sync_all()

        return JsonResponse({"success": True,
                             "message": f"✔ تمت المزامنة — {created} سجل جديد"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})

# ===============================================================
# ⚡ Live Sync — مزامنة فورية مع أجهزة Biotime (V4 Ultra Pro)
# ===============================================================

from attendance_center.services.sync_biotime_to_attendance import AttendanceSyncService

@company_required
@login_required
def live_sync_biotime(request, company_id=None):
    """
    ⚡ مزامنة فورية لسجلات Biotime وتحويلها مباشرة إلى AttendanceRecord.
    - تستخدم في لوحة التحكم أو زر Sync Now
    - ترجع JSON للاستعمال في الـ AJAX
    """

    try:
        sync_service = AttendanceSyncService()
        result = sync_service.sync_today()  # مزامنة اليوم فقط

        return JsonResponse({
            "status": result.get("status"),
            "message": result.get("message"),
            "synced": result.get("synced"),
            "skipped": result.get("skipped"),
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"خطأ أثناء المزامنة الفورية: {e}"
        }, status=500)

# ============================================================
# 📡 7) Dashboard KPIs
# ============================================================
@login_required
def attendance_dashboard_api(request, company_id):
    company = request.user.company

    if company.id != company_id:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    kpis = KPIService.get_company_kpis(company)

    return JsonResponse({"success": True, "data": kpis}, safe=False)


# ============================================================
# 📡 8) Unified Attendance Policies API — V1 Ultra Pro
# ============================================================
@login_required
def attendance_policies_api(request):
    company = request.user.company

    search = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "-id")
    page = int(request.GET.get("page", 1))
    per_page = int(request.GET.get("per_page", 10))

    qs = AttendancePolicy.objects.filter(company=company)

    if search:
        qs = qs.filter(
            Q(weekend_days__icontains=search)
            | Q(overtime_rate__icontains=search)
            | Q(work_start__icontains=search)
            | Q(work_end__icontains=search)
        )

    allowed_sort = ["id", "-id", "work_start", "-work_start", "work_end", "-work_end",
                    "overtime_rate", "-overtime_rate"]
    if sort not in allowed_sort:
        sort = "-id"

    qs = qs.order_by(sort)

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page)

    data = []
    for policy in page_obj:
        assigned_count = EmployeeAttendancePolicy.objects.filter(
            company_policy=policy
        ).count()

        weekend_display = policy.weekend_days.replace(",", " - ")

        name = f"سياسة الدوام من {policy.work_start} إلى {policy.work_end}"

        data.append({
            "id": policy.id,
            "name": name,
            "working_days": weekend_display,
            "assigned_count": assigned_count,
        })

    return JsonResponse({
        "success": True,
        "count": paginator.count,
        "page": page_obj.number,
        "pages": paginator.num_pages,
        "per_page": per_page,
        "data": data,
        "sorting": sort,
        "search": search,
    }, safe=False)


# ============================================================
# 📤 9) Export Engine — CSV / Excel / PDF
# ============================================================

@login_required
def attendance_policies_export_csv(request):
    company = request.user.company
    qs = AttendancePolicy.objects.filter(company=company)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="attendance_policies.csv"'

    writer = csv.writer(response)
    writer.writerow(["اسم السياسة", "أيام العمل", "عدد الموظفين"])

    for p in qs:
        count = EmployeeAttendancePolicy.objects.filter(company_policy=p).count()
        days = p.weekend_days.replace(",", " - ")
        name = f"سياسة الدوام من {p.work_start} إلى {p.work_end}"
        writer.writerow([name, days, count])

    return response


@login_required
def attendance_policies_export_excel(request):
    company = request.user.company
    qs = AttendancePolicy.objects.filter(company=company)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Policies"

    ws.append(["اسم السياسة", "أيام العمل", "عدد الموظفين"])

    for p in qs:
        count = EmployeeAttendancePolicy.objects.filter(company_policy=p).count()
        days = p.weekend_days.replace(",", " - ")
        name = f"سياسة الدوام من {p.work_start} إلى {p.work_end}"
        ws.append([name, days, count])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="attendance_policies.xlsx"'

    wb.save(response)
    return response


@login_required
def attendance_policies_export_pdf(request):
    company = request.user.company
    qs = AttendancePolicy.objects.filter(company=company)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="attendance_policies.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.setFont("Helvetica", 12)

    y = 800
    pdf.drawString(50, y, "📄 تقرير سياسات الحضور — Mham Cloud")
    y -= 40

    for p in qs:
        count = EmployeeAttendancePolicy.objects.filter(company_policy=p).count()
        days = p.weekend_days.replace(",", " - ")
        name = f"سياسة الدوام: {p.work_start} — {p.work_end}"

        pdf.drawString(50, y, f"- {name}")
        y -= 20
        pdf.drawString(80, y, f"الأيام: {days}")
        y -= 20
        pdf.drawString(80, y, f"عدد الموظفين: {count}")
        y -= 30

        if y < 80:
            pdf.showPage()
            y = 800

    pdf.save()
    return response
# ============================================================
# 📂 Attendance Printing Views — V1 Ultra Pro
# 🧾 طباعة تقارير الحضور (شهري — فترة — موظف)
# ============================================================

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

from .models import AttendanceRecord
from employee_center.models import Employee
from company_manager.models import Company



# 🖨️ Printing Engine


# ============================================================
# 🧾 1) Monthly Attendance Report (Company-Wide)
# ============================================================
@login_required
def attendance_print_monthly(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    today = timezone.now()
    month_start = today.replace(day=1)
    month_end = today

    records = AttendanceRecord.objects.filter(
        employee__company=company,
        timestamp__range=[month_start, month_end]
    ).order_by("-timestamp")

    engine = AttendanceReportPrintEngine(
        company=company,
        records=records,
        mode="monthly"
    )

    pdf_binary = engine.render_pdf()
    filename = f"attendance_monthly_{company.name}_{today.strftime('%Y_%m')}.pdf"

    response = HttpResponse(pdf_binary, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ============================================================
# 🧾 2) Range Attendance Report
# ============================================================
@login_required
def attendance_print_range(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    start = request.GET.get("start")
    end = request.GET.get("end")

    if not start or not end:
        return HttpResponse("❌ يجب تحديد تاريخ البداية والنهاية ?start=YYYY-MM-DD&end=YYYY-MM-DD")

    records = AttendanceRecord.objects.filter(
        employee__company=company,
        timestamp__date__range=[start, end]
    ).order_by("-timestamp")

    period = {"start": start, "end": end}

    engine = AttendanceReportPrintEngine(
        company=company,
        records=records,
        mode="range",
        period=period
    )

    pdf_binary = engine.render_pdf()
    filename = f"attendance_{company.name}_{start}_to_{end}.pdf"

    response = HttpResponse(pdf_binary, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ============================================================
# 🧾 3) Single Employee Attendance Report
# ============================================================
@login_required
def attendance_print_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    company = employee.company

    records = AttendanceRecord.objects.filter(
        employee=employee
    ).order_by("-timestamp")

    period = {
        "start": records.last().timestamp.date() if records else None,
        "end": records.first().timestamp.date() if records else None,
    }

    engine = AttendanceReportPrintEngine(
        company=company,
        records=records,
        mode="employee",
        period=period
    )

    pdf_binary = engine.render_pdf()
    filename = f"attendance_{employee.full_name}_{timezone.now().strftime('%Y_%m_%d')}.pdf"

    response = HttpResponse(pdf_binary, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
# ============================================================
# 📊 Attendance Analytics — V14 Ultra Pro
# ============================================================
@login_required
@company_required
@permission_required("attendance_center", "view")
def attendance_analytics(request, company_id):
    """
    📊 واجهة التحليلات الذكية لنظام الحضور
    - رسوم بيانية
    - تصفية حسب التاريخ
    - أيام العمل
    - ساعات التأخير
    """
    company = get_object_or_404(Company, id=company_id)

    context = {
        "company": company,
        "page_title": "تحليلات الحضور",
    }

    return render(request, "attendance_center/analytics_dashboard.html", context)



# ============================================================
# 🔍 فلترة التحليلات — API
# ============================================================
@login_required
@company_required
@permission_required("attendance_center", "view")
def attendance_filter(request, company_id):
    """
    🔍 API — فلترة البيانات حسب التاريخ
    """
    company = get_object_or_404(Company, id=company_id)

    start = request.GET.get("start")
    end = request.GET.get("end")

    # TODO: لاحقًا نربطها بمحرك WorkdayEngine + Leave Integration

    return JsonResponse({
        "status": "success",
        "start": start,
        "end": end,
        "data": [],
    })
# ============================================================
# ⚙️ Attendance Settings Center — V13 Ultra Pro
# ============================================================

@login_required
@company_required
@permission_required("attendance_center", "view")
def attendance_settings(request, company_id):
    """
    ⚙️ صفحة إعدادات نظام الحضور — Biotime Integration + WorkdayEngine
    """
    company = get_object_or_404(Company, id=company_id)
    
    setting = AttendanceSetting.objects.filter(company=company).first()

    return render(request, "attendance_center/settings.html", {
        "company": company,
        "setting": setting,
    })


# ------------------------------------------------------------
# ✏ تعديل الإعدادات
# ------------------------------------------------------------
@login_required
@company_required
@permission_required("attendance_center", "edit")
def attendance_settings_edit(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    setting = AttendanceSetting.objects.filter(company=company).first()

    if request.method == "POST":
        server_url = request.POST.get("server_url")
        api_key = request.POST.get("api_key")
        auto_sync = request.POST.get("auto_sync") == "on"

        if setting:
            setting.biotime_server_url = server_url
            setting.api_key = api_key
            setting.auto_sync_enabled = auto_sync
            setting.save()
        else:
            AttendanceSetting.objects.create(
                company=company,
                biotime_server_url=server_url,
                api_key=api_key,
                auto_sync_enabled=auto_sync,
            )

        return redirect("attendance_center:attendance_settings", company_id=company.id)

    return render(request, "attendance_center/settings_edit.html", {
        "company": company,
        "setting": setting,
    })


# ------------------------------------------------------------
# 🔌 اختبار الاتصال مع Biotime
# ------------------------------------------------------------
@login_required
@company_required
@permission_required("attendance_center", "view")
def attendance_settings_connection_test(request, company_id):
    """
    🔌 اختبار اتصال فعلي مع خادم Biotime باستخدام إعدادات الشركة
    """
    company = get_object_or_404(Company, id=company_id)
    setting = AttendanceSetting.objects.filter(company=company).first()

    if not setting:
        return JsonResponse({"status": "error", "message": "لم يتم ضبط الإعدادات بعد."})

    try:
        from attendance_center.biotime_api import get_biotime_token
        token = get_biotime_token()

        if token:
            return JsonResponse({"status": "success", "message": "تم الاتصال بنجاح!"})
        else:
            return JsonResponse({"status": "error", "message": "فشل الحصول على التوكن."})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
# ============================================================
# 📘 Attendance Policies V3 Ultra Pro — Restore
# ============================================================

from .models import AttendancePolicy, EmployeeAttendancePolicy
from .forms import AttendancePolicyForm
from django.contrib import messages


# ------------------------------------------------------------
# 📋 قائمة السياسات
# ------------------------------------------------------------
@login_required
@company_required
@permission_required("attendance_center", "view")
def attendance_policies_list(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    policies = AttendancePolicy.objects.filter(company=company).order_by("-created_at")

    return render(request, "attendance_center/policies_list.html", {
        "company": company,
        "policies": policies,
    })


# ------------------------------------------------------------
# ➕ إضافة سياسة
# ------------------------------------------------------------
@login_required
@company_required
@permission_required("attendance_center", "create")
def attendance_policy_add(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":
        form = AttendancePolicyForm(request.POST)
        if form.is_valid():
            policy = form.save(commit=False)
            policy.company = company
            policy.save()
            messages.success(request, "✔ تم إضافة السياسة بنجاح")
            return redirect("attendance_center:attendance_policies_list", company_id=company.id)
    else:
        form = AttendancePolicyForm()

    return render(request, "attendance_center/policy_add.html", {
        "company": company,
        "form": form,
    })


# ------------------------------------------------------------
# ✏ تعديل سياسة
# ------------------------------------------------------------
@login_required
@company_required
@permission_required("attendance_center", "edit")
def attendance_policy_edit(request, company_id, policy_id):
    company = get_object_or_404(Company, id=company_id)
    policy = get_object_or_404(AttendancePolicy, id=policy_id, company=company)

    if request.method == "POST":
        form = AttendancePolicyForm(request.POST, instance=policy)
        if form.is_valid():
            form.save()
            messages.success(request, "✔ تم تعديل السياسة بنجاح")
            return redirect("attendance_center:attendance_policies_list", company_id=company.id)
    else:
        form = AttendancePolicyForm(instance=policy)

    return render(request, "attendance_center/policy_edit.html", {
        "company": company,
        "policy": policy,
        "form": form,
    })


# ------------------------------------------------------------
# 👥 ربط موظفين بسياسة
# ------------------------------------------------------------
@login_required
@company_required
@permission_required("attendance_center", "edit")
def attendance_policy_assign(request, company_id, policy_id):
    company = get_object_or_404(Company, id=company_id)
    policy = get_object_or_404(AttendancePolicy, id=policy_id, company=company)

    employees = Employee.objects.filter(company=company)

    if request.method == "POST":
        selected_ids = request.POST.getlist("employees")

        # حذف القديم
        EmployeeAttendancePolicy.objects.filter(policy=policy).delete()

        # ربط جديد
        for emp_id in selected_ids:
            EmployeeAttendancePolicy.objects.create(
                company=company,
                employee_id=emp_id,
                policy=policy
            )

        messages.success(request, "✔ تم تحديث الموظفين المرتبطين بالسياسة")
        return redirect("attendance_center:attendance_policies_list", company_id=company.id)

    return render(request, "attendance_center/policy_assign.html", {
        "company": company,
        "policy": policy,
        "employees": employees,
    })


# ------------------------------------------------------------
# 🎯 تجاوز السياسة لموظف محدد
# ------------------------------------------------------------
@login_required
@company_required
@permission_required("attendance_center", "edit")
def attendance_employee_override(request, company_id, policy_id):
    company = get_object_or_404(Company, id=company_id)
    policy = get_object_or_404(AttendancePolicy, id=policy_id, company=company)

    employees = Employee.objects.filter(company=company)

    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        form = AttendancePolicyForm(request.POST, instance=policy)

        if employee_id and form.is_valid():
            EmployeeAttendancePolicy.objects.update_or_create(
                company=company,
                employee_id=employee_id,
                policy=policy,
                defaults={"override": True}
            )

            messages.success(request, "✔ تم تطبيق التجاوز للموظف")
            return redirect("attendance_center:attendance_policies_list", company_id=company.id)

    return render(request, "attendance_center/policy_employee_override.html", {
        "company": company,
        "policy": policy,
        "employees": employees,
    })
