# 📂 الملف: notification_center/services_hr.py
# 🧠 HR Notification Engine — Primey HR Cloud V1.0
# 🚀 إشعارات الموارد البشرية الرسمية (موظفين + عقود + إجازات + نهاية خدمة)

from django.contrib.auth import get_user_model
from django.utils import timezone

from notification_center.services import create_notification
from employee_center.models import Employee, Contract
from leave_center.models import LeaveRequest

User = get_user_model()


# =============================================================
# 👤 1) إشعار عند إضافة موظف جديد
# =============================================================
def notify_employee_created(employee: Employee):
    """
    يُرسل إشعارًا للمدير عند إضافة موظف جديد.
    """
    managers = User.objects.filter(is_staff=True)

    for m in managers:
        create_notification(
            recipient=m,
            title="👤 موظف جديد",
            message=f"تم إضافة الموظف {employee.full_name} إلى الشركة.",
            notification_type="hr_employee",
            severity="success",
            link=f"/employee-center/{employee.company.id}/employee/{employee.id}/"
        )


# =============================================================
# 📝 2) إشعار تحديث بيانات الموظف
# =============================================================
def notify_employee_updated(employee: Employee):
    managers = User.objects.filter(is_staff=True)

    for m in managers:
        create_notification(
            recipient=m,
            title="📝 تحديث بيانات موظف",
            message=f"تم تحديث بيانات الموظف {employee.full_name}.",
            notification_type="hr_employee",
            severity="info",
            link=f"/employee-center/{employee.company.id}/employee/{employee.id}/"
        )


# =============================================================
# 📄 3) إشعار عند إنشاء عقد
# =============================================================
def notify_contract_created(contract: Contract):
    employee = contract.employee
    managers = User.objects.filter(is_staff=True)

    for m in managers:
        create_notification(
            recipient=m,
            title="📄 عقد جديد",
            message=f"تم إنشاء عقد جديد للموظف {employee.full_name}.",
            notification_type="hr_contract",
            severity="success",
            link=f"/employee-center/{employee.company.id}/contract/{contract.id}/"
        )


# =============================================================
# ⚠️ 4) إشعار انتهاء عقد
# =============================================================
def notify_contract_expiring(contract: Contract):
    employee = contract.employee
    managers = User.objects.filter(is_staff=True)

    for m in managers:
        create_notification(
            recipient=m,
            title="⚠️ عقد على وشك الانتهاء",
            message=f"عقد الموظف {employee.full_name} ينتهي بتاريخ {contract.end_date}.",
            notification_type="hr_contract",
            severity="warning",
            link=f"/employee-center/{employee.company.id}/contract/{contract.id}/"
        )


# =============================================================
# 📁 5) إشعار عند رفع مستند للموظف
# =============================================================
def notify_document_uploaded(employee: Employee, document_name: str):
    managers = User.objects.filter(is_staff=True)

    for m in managers:
        create_notification(
            recipient=m,
            title="📁 مستند جديد",
            message=f"تم رفع مستند ({document_name}) للموظف {employee.full_name}.",
            notification_type="hr_document",
            severity="info",
            link=f"/employee-center/{employee.company.id}/employee/{employee.id}/documents/"
        )


# =============================================================
# 🏖 6) إشعار طلب إجازة جديد
# =============================================================
def notify_leave_requested(leave: LeaveRequest):
    employee = leave.employee
    approvers = User.objects.filter(is_staff=True)

    for a in approvers:
        create_notification(
            recipient=a,
            title="🏖 طلب إجازة جديد",
            message=f"قام {employee.full_name} بتقديم طلب إجازة ({leave.leave_type.name}).",
            notification_type="hr_leave",
            severity="info",
            link=f"/leave-center/{employee.company.id}/requests/{leave.id}/"
        )


# =============================================================
# ✅ 7) إشعار الموافقة على الإجازة
# =============================================================
def notify_leave_approved(leave: LeaveRequest):
    create_notification(
        recipient=leave.employee.user,
        title="✅ تم قبول طلب الإجازة",
        message=f"تمت الموافقة على الإجازة ({leave.leave_type.name}).",
        notification_type="hr_leave",
        severity="success",
        link=f"/leave-center/{leave.employee.company.id}/requests/{leave.id}/"
    )


# =============================================================
# ❌ 8) إشعار رفض الإجازة
# =============================================================
def notify_leave_rejected(leave: LeaveRequest):
    create_notification(
        recipient=leave.employee.user,
        title="❌ تم رفض طلب الإجازة",
        message=f"تم رفض الإجازة ({leave.leave_type.name}).",
        notification_type="hr_leave",
        severity="error",
        link=f"/leave-center/{leave.employee.company.id}/requests/{leave.id}/"
    )


# =============================================================
# 🛑 9) إشعار إنهاء خدمة موظف
# =============================================================
def notify_employee_terminated(employee: Employee):
    managers = User.objects.filter(is_staff=True)

    for m in managers:
        create_notification(
            recipient=m,
            title="🛑 إنهاء خدمة",
            message=f"تم إنهاء خدمة الموظف {employee.full_name}.",
            notification_type="hr_termination",
            severity="error",
            link=f"/employee-center/{employee.company.id}/employee/{employee.id}/"
        )


# =============================================================
# 💰 10) إشعار إنشاء مكافأة نهاية الخدمة
# =============================================================
def notify_eosb_created(employee: Employee, amount: float):
    managers = User.objects.filter(is_staff=True)

    for m in managers:
        create_notification(
            recipient=m,
            title="💰 مكافأة نهاية خدمة",
            message=f"تم احتساب مكافأة نهاية الخدمة للموظف {employee.full_name} بمبلغ {amount} ريال.",
            notification_type="hr_eosb",
            severity="success",
            link=f"/employee-center/{employee.company.id}/employee/{employee.id}/"
        )
