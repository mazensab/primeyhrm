# ============================================================
# 📂 api/company/payroll/salary_slip.py
# 🧾 Salary Slip API — Enterprise Snapshot Layer (Enhanced)
# 🔒 Multi-Tenant Safe
# ============================================================

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from payroll_center.models import PayrollRecord
from company_manager.models import CompanyUser
from employee_center.models import Employee
from api.company.employee import _resolve_company


# ============================================================
# 🧾 Company Admin Salary Slip
# ============================================================

class CompanyPayrollSalarySlipAPIView(APIView):
    """
    GET /api/company/payroll/slip/<record_id>/
    - Read Only
    - Snapshot Driven
    - Company Scoped
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):

        # ----------------------------------------------------
        # 🔐 Resolve Company Context
        # ----------------------------------------------------
        try:
            company_user = CompanyUser.objects.select_related("company").get(
                user=request.user
            )
        except CompanyUser.DoesNotExist:
            return Response(
                {"detail": "Company context not found."},
                status=status.HTTP_403_FORBIDDEN
            )

        company = company_user.company

        # ----------------------------------------------------
        # 📥 Fetch Payroll Record (Company Scoped)
        # ----------------------------------------------------
        try:
            record = (
                PayrollRecord.objects
                .select_related(
                    "employee",
                    "employee__department",
                    "employee__job_title",
                    "employee__financial_info",
                    "run",
                    "run__company",
                    "contract",
                )
                .prefetch_related("employee__branches")
                .get(
                    id=record_id,
                    run__company=company
                )
            )
        except PayrollRecord.DoesNotExist:
            return Response(
                {"detail": "Payroll record not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        employee = record.employee
        contract = record.contract

        response_data = {
            "id": record.id,
            "company": {
                "id": company.id,
                "name": company.name,
            },
            "employee": {
                "id": employee.id,
                "full_name": employee.full_name,
                "employee_number": getattr(employee, "employee_number", None),
                "department": (
                    employee.department.name
                    if employee.department else None
                ),
                "job_title": (
                    employee.job_title.name
                    if employee.job_title else None
                ),
                "branches": [
                    branch.name for branch in employee.branches.all()
                ],
            },
            "contract": {
                "id": contract.id if contract else None,
                "contract_type": getattr(contract, "contract_type", None),
            },
            "financial_info": {
                "basic_salary": float(
                    getattr(
                        getattr(employee, "financial_info", None),
                        "basic_salary",
                        0
                    )
                )
            },
            "month": record.month.strftime("%Y-%m"),
            "run": {
                "id": record.run.id,
                "status": record.run.status,
            },
            "payment_status": record.status,
            "salary": {
                "base_salary": float(record.base_salary),
                "allowance": float(record.allowance),
                "bonus": float(record.bonus),
                "overtime": float(record.overtime),
                "deductions": float(record.deductions),
                "net_salary": float(record.net_salary),
            },
            "breakdown": record.breakdown or {},
            "generated_at": record.updated_at,
        }

        return Response(response_data, status=status.HTTP_200_OK)


# ======================================================
# 🧾 Employee Self-Service Salary Slip
# ======================================================

@require_GET
@login_required
def employee_self_salary_slip(request, record_id):

    company = _resolve_company(request)
    if not company:
        return JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )

    try:
        employee = Employee.objects.get(
            user=request.user,
            company=company,
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employee profile not found"},
            status=403,
        )

    try:
        record = (
            PayrollRecord.objects
            .select_related(
                "run",
                "run__company",
                "employee__department",
                "employee__job_title",
                "employee__financial_info",
                "contract",
            )
            .prefetch_related("employee__branches")
            .get(
                id=record_id,
                employee=employee,
                run__company=company,
            )
        )
    except PayrollRecord.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Salary slip not found"},
            status=404,
        )

    emp = record.employee

    return JsonResponse({
        "status": "ok",
        "record_id": record.id,
        "company": record.run.company.name,
        "month": record.month.strftime("%Y-%m"),
        "run_status": record.run.status,
        "payment_status": record.status,
        "employee": {
            "full_name": emp.full_name,
            "employee_number": getattr(emp, "employee_number", None),
            "department": (
                emp.department.name if emp.department else None
            ),
            "job_title": (
                emp.job_title.name if emp.job_title else None
            ),
            "branches": [
                b.name for b in emp.branches.all()
            ],
        },
        "salary": {
            "base_salary": float(record.base_salary),
            "allowance": float(record.allowance),
            "bonus": float(record.bonus),
            "overtime": float(record.overtime),
            "deductions": float(record.deductions),
            "net_salary": float(record.net_salary),
        },
        "breakdown": record.breakdown or {},
        "generated_at": record.updated_at,
    })


# ======================================================
# 📋 Employee Self-Slips List
# ======================================================

@require_GET
@login_required
def employee_self_slips_list(request):

    company = _resolve_company(request)
    if not company:
        return JsonResponse(
            {"status": "error", "message": "Company context missing"},
            status=403,
        )

    try:
        employee = Employee.objects.get(
            user=request.user,
            company=company,
        )
    except Employee.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employee profile not found"},
            status=403,
        )

    records = (
        PayrollRecord.objects
        .filter(employee=employee)
        .select_related("run")
        .order_by("-month")
    )

    results = [
        {
            "record_id": r.id,
            "month": r.month.strftime("%Y-%m"),
            "net_salary": float(r.net_salary),
            "payment_status": r.status,
            "run_status": r.run.status,
        }
        for r in records
    ]

    return JsonResponse({
        "status": "ok",
        "count": len(results),
        "results": results,
    })
