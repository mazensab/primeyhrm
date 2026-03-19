from datetime import date
from django.db.utils import ProgrammingError
from leave_center.models import LeavePolicy, CompanyAnnualLeavePolicy


class PolicyResolver:
    """
    Leave Policy Resolver — Merge Strategy (Phase F.5.2)
    CompanyAnnualLeavePolicy + LeavePolicy
    Multi-Tenant Safe
    """

    @staticmethod
    def resolve(employee, leave_type):

        # ====================================================
        # 🟢 1) Company Annual Policy (if annual)
        # ====================================================
        company_policy = None

        if leave_type.category == "annual":
            try:
                company_policy = CompanyAnnualLeavePolicy.objects.filter(
                    company=employee.company,
                    is_active=True
                ).first()
            except ProgrammingError:
                company_policy = None

        # ====================================================
        # 🟣 2) LeavePolicy (per type)
        # ====================================================
        try:
            leave_policy = LeavePolicy.objects.filter(
                company=employee.company,
                leave_type=leave_type,
                is_active=True
            ).first()
        except ProgrammingError:
            leave_policy = None

        # ====================================================
        # 🧠 Service Years Calculation
        # ====================================================
        years_of_service = 0
        if hasattr(employee, "work_start_date") and employee.work_start_date:
            years_of_service = (
                date.today().year - employee.work_start_date.year
            )

        # ====================================================
        # 🎯 Merge Logic
        # ====================================================

        # 1️⃣ allowed_days
        if company_policy:
            allowed_days = company_policy.annual_days
        elif leave_policy:
            allowed_days = leave_policy.default_days
        else:
            allowed_days = leave_type.annual_balance or 0

        # Service Rule from LeavePolicy (إن وجد)
        if leave_policy:
            if (
                leave_policy.min_service_years
                and leave_policy.days_after_service
                and years_of_service >= leave_policy.min_service_years
            ):
                allowed_days = leave_policy.days_after_service

        # 2️⃣ Behavioral Flags (من LeavePolicy فقط)
        paid = leave_policy.paid_leave if leave_policy else True
        requires_manager = (
            leave_policy.requires_manager_approval if leave_policy else True
        )
        requires_hr = (
            leave_policy.requires_hr_approval if leave_policy else False
        )
        max_consecutive = (
            leave_policy.max_consecutive_days if leave_policy else None
        )
        gender_restriction = (
            leave_policy.gender_restriction if leave_policy else None
        )

        return {
            "allowed_days": allowed_days,
            "paid": paid,
            "requires_manager": requires_manager,
            "requires_hr": requires_hr,
            "max_consecutive": max_consecutive,
            "gender_restriction": gender_restriction,
            "carry_forward_enabled": (
                company_policy.carry_forward_enabled
                if company_policy else False
            ),
            "carry_forward_limit": (
                company_policy.carry_forward_limit
                if company_policy else None
            ),
            "reset_month": (
                company_policy.reset_month
                if company_policy else None
            ),
        }