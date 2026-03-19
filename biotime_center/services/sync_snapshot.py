def build_employee_snapshot(employee):
    return {
        "name": employee.full_name,
        "department": (
            employee.department.biotime_code
            if employee.department else None
        ),
        "position": (
            employee.job_title.biotime_code
            if employee.job_title else None
        ),
        "areas": sorted([
            b.biotime_code
            for b in employee.branches.all()
            if b.biotime_code
        ]),
        "is_active": employee.user.is_active,
    }
