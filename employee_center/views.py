# ===============================================================
# 📂 employee_center/views.py
# 🧭 Employee Center — V15.8 Ultra Pro (FIXED & STABLE)
# ===============================================================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
from datetime import date

from company_manager.permissions import company_permission_required
from company_manager.models import Company, CompanyUser
from datetime import datetime

# 🔐 Subscription Enforcement
from company_manager.decorators.subscription_limits import enforce_employee_limit
from company_manager.decorators.subscription_enforcement import (
    SubscriptionInactiveError,
    PlanLimitReachedError,
)

# 💾 Models
from .models import (
    Employee,
    EmploymentInfo,
    FinancialInfo,
    EmployeeDocument,
    Contract,
    TerminationRecord,
    ResignationRecord,
    EoSBRecord,
    EmploymentHistory,
)

# 🧾 Forms
from .forms import (
    EmployeeForm,
    EmploymentInfoForm,
    FinancialInfoForm,
    EmployeeDocumentForm,
    ContractForm,
    TerminationRecordForm,
    ResignationRecordForm,
    EosbRecordForm,
)

# 🖨️ Printing


# ===============================================================
# 🔵 1) Dashboard
# ===============================================================
@login_required
@company_permission_required("employee_center.view_dashboard")
def employees_dashboard(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    total = Employee.objects.filter(company=company).count()
    active = Employee.objects.filter(company=company, status="active").count()
    on_leave = Employee.objects.filter(company=company, status="on_leave").count()
    resigned = Employee.objects.filter(company=company, status="resigned").count()
    terminated = Employee.objects.filter(company=company, status="terminated").count()

    recent = Employee.objects.filter(company=company).order_by("-id")[:5]

    contracts_summary = (
        Contract.objects.filter(company=company)
        .values("contract_type")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    return render(request, "employee_center/employee_dashboard.html", {
        "company": company,
        "total_employees": total,
        "active_employees": active,
        "on_leave": on_leave,
        "resigned": resigned,
        "terminated": terminated,
        "recent_employees": recent,
        "contracts_summary": contracts_summary,
        "today_attendance": [],
        "system_alerts": [],
    })


# ===============================================================
# 🔵 2) Employees List
# ===============================================================
@login_required
@company_permission_required("employee_center.view_employee")
def employees_list(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "name_asc")

    employees = Employee.objects.filter(company=company)

    if search:
        employees = employees.filter(
            Q(full_name__icontains=search) |
            Q(national_id__icontains=search) |
            Q(passport_number__icontains=search)
        )

    for emp in employees:
        first_contract = Contract.objects.filter(employee=emp).order_by("start_date").first()
        emp.hire_date = first_contract.start_date if first_contract else None

    if sort == "name_asc":
        employees = sorted(employees, key=lambda e: e.full_name or "")
    elif sort == "name_desc":
        employees = sorted(employees, key=lambda e: e.full_name or "", reverse=True)

    from django.core.paginator import Paginator
    paginator = Paginator(employees, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "employee_center/employee_list.html", {
        "company": company,
        "employees": page_obj,
        "page_obj": page_obj,
        "search": search,
        "sort": sort,
    })
# ===============================================================
# 🔵 3) Add Employee (User auto-created by signal)
# ===============================================================
@login_required
@company_permission_required("employee_center.add_employee")
@enforce_employee_limit
def employee_add(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    employee = form.save(commit=False)
                    employee.company = company
                    employee.save()

                    EmploymentInfo.objects.get_or_create(employee=employee)
                    FinancialInfo.objects.get_or_create(employee=employee)

                    CompanyUser.objects.get_or_create(
                        user=employee.user,
                        company=company,
                        defaults={"is_active": True},
                    )

                    messages.success(request, "✔ تم إضافة الموظف وإنشاء حساب الدخول")
                    return redirect("employee_center:employees_list", company_id=company.id)

            except (SubscriptionInactiveError, PlanLimitReachedError) as e:
                messages.error(request, str(e))

    else:
        form = EmployeeForm()

    return render(request, "employee_center/employee_add.html", {
        "company": company,
        "form": form,
    })


# ===============================================================
# 🔵 4) Edit Employee
# ===============================================================
@login_required
@company_permission_required("employee_center.change_employee")
def employee_edit(request, company_id, employee_id):
    company = get_object_or_404(Company, id=company_id)
    employee = get_object_or_404(Employee, id=employee_id, company=company)

    job_info = getattr(employee, "employment_info", None)
    finance_info = getattr(employee, "financial_info", None)

    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        job_form = EmploymentInfoForm(request.POST, instance=job_info)
        finance_form = FinancialInfoForm(request.POST, instance=finance_info)

        if form.is_valid() and job_form.is_valid() and finance_form.is_valid():
            form.save()
            job_form.save()
            finance_form.save()
            messages.success(request, "✔ تم تحديث بيانات الموظف")
            return redirect("employee_center:employee_detail", company_id, employee.id)

    else:
        form = EmployeeForm(instance=employee)
        job_form = EmploymentInfoForm(instance=job_info)
        finance_form = FinancialInfoForm(instance=finance_info)

    return render(request, "employee_center/employee_edit.html", {
        "company": company,
        "employee": employee,
        "form": form,
        "job_form": job_form,
        "finance_form": finance_form,
    })


# ===============================================================
# 🔵 5) Employee Detail
# ===============================================================
@login_required
@company_permission_required("employee_center.view_employee")
def employee_detail(request, company_id, employee_id):
    employee = get_object_or_404(Employee, id=employee_id, company_id=company_id)

    return render(request, "employee_center/employee_detail.html", {
        "company": employee.company,
        "employee": employee,
        "active_contract": employee.contracts.filter(is_active=True).first(),
        "job_info": getattr(employee, "employment_info", None),
        "finance_info": getattr(employee, "financial_info", None),
        "documents": employee.documents.all(),
    })

# ===============================================================
# 🔵 Contracts List — SAFE RESTORE
# ===============================================================
@login_required
@company_permission_required("employee_center.view_contract")
def contracts_list(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    # 🔐 حماية الوصول للشركة
    if not validate_company_access(request.user, company):
        messages.error(request, "⚠️ لا تملك صلاحية عرض العقود لهذه الشركة.")
        return redirect("control_center:dashboard")

    contracts = (
        Contract.objects
        .filter(company=company)
        .select_related("employee")
        .order_by("-start_date")
    )

    return render(
        request,
        "employee_center/contracts_list.html",
        {
            "company": company,
            "contracts": contracts,
        }
    )
# ===============================================================
# 🔵 Add Contract — SAFE RESTORE
# ===============================================================
@login_required
@company_permission_required("employee_center.add_contract")
def contract_add(request, company_id, employee_id=None):
    company = get_object_or_404(Company, id=company_id)

    # 🔐 حماية الوصول
    if not validate_company_access(request.user, company):
        messages.error(request, "⚠️ لا يمكنك إضافة عقد لهذه الشركة.")
        return redirect("control_center:dashboard")

    employee = None
    if employee_id:
        employee = get_object_or_404(
            Employee,
            id=employee_id,
            company=company
        )

    if request.method == "POST":
        form = ContractForm(request.POST)

        if form.is_valid():
            contract = form.save(commit=False)
            contract.company = company
            contract.employee = employee
            contract.save()

            messages.success(request, "✔ تم إضافة العقد بنجاح")
            return redirect(
                "employee_center:contracts_list",
                company_id=company.id
            )
    else:
        form = ContractForm()

    return render(
        request,
        "employee_center/contract_add.html",
        {
            "company": company,
            "employee": employee,
            "form": form,
        }
    )
# ===============================================================
# 🔵 Contract Detail — SAFE RESTORE
# ===============================================================
@login_required
@company_permission_required("employee_center.view_contract")
def contract_detail(request, company_id, contract_id):
    company = get_object_or_404(Company, id=company_id)
    contract = get_object_or_404(
        Contract,
        id=contract_id,
        company=company
    )

    # 🔐 حماية الوصول
    if not validate_company_access(request.user, company):
        messages.error(request, "⚠️ لا تملك صلاحية عرض هذا العقد.")
        return redirect(
            "employee_center:contracts_list",
            company_id=company.id
        )

    return render(
        request,
        "employee_center/contract_detail.html",
        {
            "company": company,
            "contract": contract,
            "employee": contract.employee,
        }
    )

# ===============================================================
# 🔵 Documents
# ===============================================================
@login_required
@company_permission_required("employee_center.view_document")
def documents_list(request, company_id, employee_id):
    employee = get_object_or_404(Employee, id=employee_id, company_id=company_id)
    return render(request, "employee_center/documents_list.html", {
        "company": employee.company,
        "employee": employee,
        "documents": employee.documents.all(),
    })
# ===============================================================
# 🔵 Add Document — SAFE RESTORE
# ===============================================================
@login_required
@company_permission_required("employee_center.add_document")
def document_add(request, company_id, employee_id):
    employee = get_object_or_404(
        Employee,
        id=employee_id,
        company_id=company_id
    )

    # 🔐 حماية الوصول
    if not validate_company_access(request.user, employee.company):
        messages.error(request, "⚠️ لا يمكنك رفع مستند لهذا الموظف.")
        return redirect(
            "employee_center:documents_list",
            company_id=employee.company.id,
            employee_id=employee.id
        )

    if request.method == "POST":
        form = EmployeeDocumentForm(request.POST, request.FILES)

        if form.is_valid():
            document = form.save(commit=False)
            document.employee = employee
            document.save()

            messages.success(request, "✔ تم رفع المستند بنجاح")
            return redirect(
                "employee_center:documents_list",
                company_id=employee.company.id,
                employee_id=employee.id
            )
    else:
        form = EmployeeDocumentForm()

    return render(
        request,
        "employee_center/document_add.html",
        {
            "company": employee.company,
            "employee": employee,
            "form": form,
        }
    )
# ===============================================================
# 🔴 Delete Document — SAFE RESTORE
# ===============================================================
@login_required
@company_permission_required("employee_center.delete_document")
def document_delete(request, company_id, document_id):
    document = get_object_or_404(
        EmployeeDocument,
        id=document_id,
        employee__company_id=company_id
    )

    employee = document.employee

    # 🔐 حماية الوصول
    if not validate_company_access(request.user, employee.company):
        messages.error(request, "⚠️ لا يمكنك حذف هذا المستند.")
        return redirect(
            "employee_center:documents_list",
            company_id=employee.company.id,
            employee_id=employee.id
        )

    if request.method == "POST":
        document.delete()
        messages.success(request, "🗑️ تم حذف المستند بنجاح")

    return redirect(
        "employee_center:documents_list",
        company_id=employee.company.id,
        employee_id=employee.id
    )
# ===============================================================
# 🚪 Employee Resignation — SAFE RESTORE
# ===============================================================
@login_required
@company_permission_required("employee_center.resign_employee")
def employee_resignation(request, company_id, employee_id):
    employee = get_object_or_404(
        Employee,
        id=employee_id,
        company_id=company_id
    )

    # 🔐 حماية الوصول
    if not validate_company_access(request.user, employee.company):
        messages.error(request, "⚠️ لا يمكنك تنفيذ هذه العملية.")
        return redirect(
            "employee_center:employee_detail",
            company_id=company_id,
            employee_id=employee.id
        )

    if request.method == "POST":
        resignation_date = request.POST.get("resignation_date")
        last_working_day = request.POST.get("last_working_day")
        reason = request.POST.get("reason")

        ResignationRecord.objects.create(
            employee=employee,
            resignation_date=resignation_date,
            last_working_day=last_working_day,
            reason=reason
        )

        # تحديث حالة الموظف
        employee.status = "resigned"
        employee.end_date = last_working_day
        employee.save(update_fields=["status", "end_date"])

        EmploymentHistory.objects.create(
            employee=employee,
            action_type="resignation",
            description=reason,
            effective_date=resignation_date
        )

        messages.success(request, "✅ تم تسجيل استقالة الموظف بنجاح")

        return redirect(
            "employee_center:employee_detail",
            company_id=company_id,
            employee_id=employee.id
        )

    return render(
        request,
        "employee_center/employee_resignation.html",
        {
            "employee": employee,
            "company": employee.company,
        }
    )
# ===============================================================
# 🖨️ Contract PDF Print — SAFE RESTORE
# ===============================================================
@login_required
@company_permission_required("employee_center.view_contract")
def contract_print_view(request, company_id, contract_id):
    contract = get_object_or_404(
        Contract,
        id=contract_id,
        company_id=company_id
    )

    employee = contract.employee

    # 🔐 حماية الوصول
    if not validate_company_access(request.user, employee.company):
        return HttpResponse("Unauthorized", status=401)

    engine = ContractPrintEngine(
        contract=contract,
        employee=employee,
        company=employee.company,
        template_path="employee_center/contract_print_pdf.html",
    )

    pdf = engine.render_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="contract_{employee.full_name}_{contract.start_date}.pdf"'
    )

    return response
# ===============================================================
# 🖨️ Contract PDF Print — SAFE RESTORE
# ===============================================================
@login_required
@company_permission_required("employee_center.view_contract")
def contract_print_view(request, company_id, contract_id):
    contract = get_object_or_404(
        Contract,
        id=contract_id,
        company_id=company_id
    )

    employee = contract.employee

    # 🔐 حماية الوصول
    if not validate_company_access(request.user, employee.company):
        return HttpResponse("Unauthorized", status=401)

    engine = ContractPrintEngine(
        contract=contract,
        employee=employee,
        company=employee.company,
        template_path="employee_center/contract_print_pdf.html",
    )

    pdf = engine.render_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="contract_{employee.full_name}_{contract.start_date}.pdf"'
    )

    return response


# ===============================================================
# 🔵 Termination
# ===============================================================
@login_required
@company_permission_required("employee_center.add_termination")
def terminate_employee(request, company_id, employee_id):
    employee = get_object_or_404(Employee, id=employee_id, company_id=company_id)

    if request.method == "POST":
        form = TerminationRecordForm(request.POST)
        if form.is_valid():
            term = form.save(commit=False)
            term.employee = employee
            term.save()

            employee.status = "terminated"
            employee.end_date = term.termination_date
            employee.save()

            messages.success(request, "✔ تم إنهاء الخدمة")
            return redirect("employee_center:employee_detail", company_id, employee_id)

    else:
        form = TerminationRecordForm()

    return render(request, "employee_center/termination_add.html", {
        "company": employee.company,
        "employee": employee,
        "form": form,
    })


# ===============================================================
# 🔵 PDF — Employee Card
# ===============================================================
@login_required
@company_permission_required("employee_center.view_employee")
def employee_card_pdf(request, company_id, employee_id):
    employee = get_object_or_404(Employee, id=employee_id, company_id=company_id)

    engine = EmployeeCardPrintEngine(
        employee=employee,
        company=employee.company,
        template_path="employee_center/employee_card_pdf.html",
    )

    pdf = engine.render_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="employee_{employee.id}.pdf"'
    return response
# ============================================================
# 🧩 Employee Profile Update API — FINAL (PRODUCTION SAFE)
# ============================================================

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.utils.dateparse import parse_date
import json

from employee_center.models import Employee


@login_required
@require_POST
@transaction.atomic
def update_employee_profile(request, employee_id):
    """
    ✅ Update employee personal/profile information
    - Uses Employee model directly
    - No separate Profile model
    - CSRF safe
    - Local & Production ready
    """

    # ---------------------------------------------------------
    # 🔐 Resolve Company Context (SAFE)
    # ---------------------------------------------------------
    company = getattr(request, "company", None)
    if not company:
        return JsonResponse(
            {"message": "User has no company context"},
            status=403
        )

    # ---------------------------------------------------------
    # 🔍 Get Employee
    # ---------------------------------------------------------
    try:
        employee = Employee.objects.select_for_update().get(
            id=employee_id,
            company=company
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"message": "Employee not found"},
            status=404
        )

    # ---------------------------------------------------------
    # 📦 Parse Payload
    # ---------------------------------------------------------
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse(
            {"message": "Invalid JSON payload"},
            status=400
        )

    # ---------------------------------------------------------
    # 🧠 Allowed Fields
    # ---------------------------------------------------------
    allowed_fields = [
        "full_name",
        "arabic_name",
        "national_id",
        "passport_number",
        "nationality",
        "gender",
        "employment_type",
        "join_date",
        "probation_end_date",
        "end_date",
    ]

    date_fields = {
        "join_date",
        "probation_end_date",
        "end_date",
    }

    updated_fields = []

    # ---------------------------------------------------------
    # ✏️ Apply Updates (SAFE)
    # ---------------------------------------------------------
    for field in allowed_fields:
        if field not in payload or not hasattr(employee, field):
            continue

        value = payload.get(field)

        # ⛔ تجاهل القيم الفارغة
        if value in (None, ""):
            continue

        # 🗓️ Handle Dates Safely
        if field in date_fields:
            parsed_date = parse_date(value)
            if not parsed_date:
                return JsonResponse(
                    {"message": f"Invalid date format for {field}"},
                    status=400
                )
            value = parsed_date

        setattr(employee, field, value)
        updated_fields.append(field)

    # ---------------------------------------------------------
    # 💾 Save
    # ---------------------------------------------------------
    if updated_fields:
        employee.save(update_fields=updated_fields)

    return JsonResponse(
        {
            "status": "updated",
            "updated_fields": updated_fields,
        },
        status=200
    )
