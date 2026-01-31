# ================================================================
# 📘 Leave Center — Views V22 Ultra Pro (Part 1 — 25%)
# ================================================================
# ✔ RBAC كامل (Employee / Manager / HR / Admin)
# ✔ LeaveTypeColorEngine V3 — ألوان ديناميكية
# ✔ Workflow + Rules + Approval Engines
# ✔ تحسين الأداء select_related
# ---------------------------------------------------------------

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.timezone import now
from django.http import JsonResponse

from company_manager.models import Company, CompanyUser
from employee_center.models import Employee
from .models import LeaveRequest, LeaveType, ApprovalLog, LeaveBalance
from .forms import LeaveRequestForm
from .colors import LeaveTypeColorEngine   # ⭐ اعتماد محرك الألوان الجديد


# ================================================================
# 🎭 أداة مساعدة: الحصول على دور المستخدم داخل الشركة
# ================================================================
def get_user_role(user, company):
    cu = CompanyUser.objects.filter(user=user, company=company).first()
    return cu.role if cu else None


# ================================================================
# 🟩 Leave List — RBAC Filtering V3 + Enhanced Colors
# ================================================================
@login_required
def leave_list(request, company_id):
    """
    قائمة الإجازات حسب صلاحيات المستخدم:
    - employee → طلباته فقط
    - manager → طلبات موظفيه
    - hr/admin → جميع الطلبات

    + يدعم: status / type / employee filters
    + ألوان ديناميكية لكل نوع إجازة (LeaveTypeColorEngine)
    """

    company = get_object_or_404(Company, id=company_id)
    user = request.user

    user_role = get_user_role(user, company)

    # قاعدة البيانات الأساسية
    queryset = LeaveRequest.objects.filter(company=company).select_related(
        "employee", "leave_type"
    ).order_by("-created_at")

    # ------------------------------------------------------------
    # 🔐 RBAC Filtering
    # ------------------------------------------------------------

    # الموظف → يشاهد طلباته فقط
    if user_role == "employee":
        queryset = queryset.filter(employee__user=user)

    # المدير → يشاهد موظفي فريقه فقط
    elif user_role == "manager":
        team_members = Employee.objects.filter(manager=user, company=company)
        queryset = queryset.filter(employee__in=team_members)

    # HR/Admin → كامل الصلاحية (لا تعديل مطلوب)

    # ------------------------------------------------------------
    # 🔍 فلترة إضافية عبر الواجهة
    # ------------------------------------------------------------
    status_filter = request.GET.get("status")
    type_filter = request.GET.get("type")
    emp_filter = request.GET.get("employee")

    if status_filter:
        queryset = queryset.filter(status=status_filter)

    if type_filter:
        queryset = queryset.filter(leave_type_id=type_filter)

    if emp_filter:
        queryset = queryset.filter(employee_id=emp_filter)

    # ------------------------------------------------------------
    # 🎨 ألوان أنواع الإجازات (LeaveTypeColorEngine V3)
    # ------------------------------------------------------------
    color_engine = LeaveTypeColorEngine(company)
    leave_type_colors = {
        lt.id: color_engine.get_color(lt.id)
        for lt in LeaveType.objects.filter(company=company)
    }

    # ------------------------------------------------------------
    # 📄 السياق + القالب
    # ------------------------------------------------------------
    context = {
        "company": company,
        "leaves": queryset,
        "page_title": "طلبات الإجازات",
        "user_role": user_role,
        "types": LeaveType.objects.filter(company=company),
        "employees": Employee.objects.filter(company=company),
        "leave_type_colors": leave_type_colors,
    }

    return render(request, "leave_center/leave_list.html", context)


# ================================================================
# 📄 Leave Detail — RBAC + Workflow Fix + Colors V3
# ================================================================
@login_required
def leave_detail(request, leave_id):
    """
    عرض تفاصيل طلب الإجازة:
    ✔ الموظف → يرى طلبه فقط
    ✔ المدير → يرى موظفي فريقه
    ✔ HR/Admin → الوصول كامل
    + دمج ألوان النوع LeaveTypeColorEngine
    """

    leave_obj = get_object_or_404(LeaveRequest, id=leave_id)
    company = leave_obj.company
    user = request.user

    user_role = get_user_role(user, company)

    # ------------------------------------------------------------
    # 🔐 RBAC: حماية التفاصيل
    # ------------------------------------------------------------

    # 1) الموظف → يشاهد طلبه فقط
    if user_role == "employee":
        if leave_obj.employee.user != user:
            messages.error(request, "❌ لا تملك صلاحية لعرض هذا الطلب.")
            return redirect("leave_center:leave_list", company.id)

    # 2) المدير → يشاهد موظفي فريقه فقط
    elif user_role == "manager":
        if leave_obj.employee.manager != user:
            messages.error(request, "❌ الموظف ليس ضمن فريقك.")
            return redirect("leave_center:leave_list", company.id)

    # 3) HR/Admin → الوصول مفتوح

    # ------------------------------------------------------------
    # 🎨 ألوان الإجازة الحالية
    # ------------------------------------------------------------
    color_engine = LeaveTypeColorEngine(company)
    color = color_engine.get_color(leave_obj.leave_type.id)

    # ------------------------------------------------------------
    # 📄 بيانات العرض
    # ------------------------------------------------------------
    context = {
        "company": company,
        "leave": leave_obj,
        "color": color,   # ⭐ إضافة للألوان في واجهة التفاصيل
        "user_role": user_role,
        "approval_logs": leave_obj.approval_logs.all().order_by("-created_at"),
        "page_title": "تفاصيل الإجازة"
    }

    return render(request, "leave_center/leave_detail.html", context)

# ============================================================
# 🟩 إنشاء طلب إجازة — دمج RulesEngine + WorkflowEngine + ApprovalEngine
# ============================================================
@login_required
def leave_add(request, company_id):

    company = get_object_or_404(Company, id=company_id)
    employee = request.user.employee

    # السماح لموظفين الشركة فقط
    if employee.company.id != company.id:
        messages.error(request, "غير مصرح لك بالوصول.")
        return redirect("leave_center:leave_list", company.id)

    # ----------------------------
    # 📌 POST — تنفيذ طلب الإجازة
    # ----------------------------
    if request.method == "POST":
        form = LeaveRequestForm(request.POST, request.FILES)

        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = employee
            leave.company = company
            leave.status = "pending"
            leave.save()

            # =====================================================
            # 🔥 1) Rules Engine — التحقق من الرصيد + النوع + المرفق
            # =====================================================
            from .engines import LeaveRulesEngine, LeaveWorkflowEngine, LeaveApprovalEngine

            rules = LeaveRulesEngine(leave)
            ok, msg = rules.validate()

            if not ok:
                leave.delete()  # طلب غير صالح — لا يدخل النظام
                messages.error(request, msg)
                return redirect("leave_center:leave_add", company.id)

            # =====================================================
            # 🔥 2) Workflow Engine — تحديد مسار الموافقة
            # =====================================================
            workflow = LeaveWorkflowEngine(leave)
            flow = workflow.get_workflow()

            # Auto-approved أنواع مثل (زواج / وفاة)
            if "auto" in flow:
                approval = LeaveApprovalEngine(leave, request.user)
                approval.approve("موافقة تلقائية حسب نوع الإجازة")
                messages.success(request, "✔ تمت الموافقة تلقائيًا على الإجازة.")
                return redirect("leave_center:leave_list", company.id)

            # إذا المسار يبدأ بالمدير
            if flow[0] == "manager":
                leave.status = "pending"
                leave.save()

            # إذا HR Only
            if flow[0] == "hr":
                leave.status = "waiting_hr"
                leave.save()

            # =====================================================
            # 🔥 3) تسجيل لوج الإنشاء
            # =====================================================
            ApprovalLog.objects.create(
                leave_request=leave,
                action="created",
                performed_by=request.user,
                comment="تم إنشاء الطلب"
            )

            messages.success(request, "✔ تم تقديم طلب الإجازة بنجاح.")
            return redirect("leave_center:leave_list", company.id)

        else:
            messages.error(request, "الرجاء التحقق من البيانات المدخلة.")

    # ----------------------------
    # GET — عرض الفورم
    # ----------------------------
    else:
        form = LeaveRequestForm()

    leave_types = LeaveType.objects.filter(company=company)

    return render(request, "leave_center/leave_add.html", {
        "company": company,
        "employee": employee,
        "form": form,
        "leave_types": leave_types,
    })


# ============================================================
# ✔ الموافقة على طلب الإجازة — Approve Request (V22 Ultra Pro)
# ============================================================
@login_required
def approve_request(request, leave_id):

    leave = get_object_or_404(LeaveRequest, id=leave_id)
    employee = request.user.employee
    company = leave.company

    # حماية الشركة
    if employee.company.id != company.id:
        messages.error(request, "غير مصرح لك بالوصول.")
        return redirect("leave_center:leave_list", company.id)

    # ------------------------------------------------------------
    # 🔐 صلاحيات الموافقة (Manager / HR / Admin)
    # ------------------------------------------------------------
    if employee.role not in ["manager", "hr", "admin"]:
        messages.error(request, "لا تملك صلاحيات الموافقة على الإجازات.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # 🧠 Workflow Engine لمعرفة المرحلة
    # ------------------------------------------------------------
    from .engines import LeaveWorkflowEngine, LeaveApprovalEngine

    workflow = LeaveWorkflowEngine(leave)
    flow = workflow.get_workflow()

    # إذا نوع الإجازة Auto-approved → لا يجب الوصول لهذه الصفحة
    if "auto" in flow:
        messages.error(request, "هذا النوع من الإجازات يتم الموافقة عليه تلقائيًا.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # ✳️ Manager-only approval
    # ------------------------------------------------------------
    if flow == ["manager"]:
        if employee.role not in ["manager", "admin"]:
            messages.error(request, "هذه الإجازة تتطلب موافقة المدير فقط.")
            return redirect("leave_center:leave_detail", leave.id)

        # موافقة مباشرة
        approval = LeaveApprovalEngine(leave, request.user)
        approval.approve("موافقة المدير")
        messages.success(request, "✔ تمت الموافقة على الإجازة.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # ✳️ HR-only approval
    # ------------------------------------------------------------
    if flow == ["hr"]:
        if employee.role not in ["hr", "admin"]:
            messages.error(request, "هذه الإجازة تتطلب موافقة HR فقط.")
            return redirect("leave_center:leave_detail", leave.id)

        approval = LeaveApprovalEngine(leave, request.user)
        approval.approve("موافقة HR")
        messages.success(request, "✔ تمت الموافقة على الإجازة.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # ✳️ Manager → HR Workflow
    # ------------------------------------------------------------
    # المرحلة الأولى: المدير
    if leave.status == "pending" and "manager" in flow:
        if employee.role not in ["manager", "admin"]:
            messages.error(request, "يجب أن يوافق المدير أولاً.")
            return redirect("leave_center:leave_detail", leave.id)

        # انتقال إلى HR
        leave.status = "waiting_hr"
        leave.save()

        # Log
        ApprovalLog.objects.create(
            leave_request=leave,
            action="approved_manager",
            comment="موافقة المدير",
            performed_by=request.user
        )

        messages.success(request, "✔ تمت الموافقة من المدير — بانتظار HR.")
        return redirect("leave_center:leave_detail", leave.id)

    # المرحلة الثانية: HR
    if leave.status == "waiting_hr" and "hr" in flow:
        if employee.role not in ["hr", "admin"]:
            messages.error(request, "هذه المرحلة تتطلب موافقة HR.")
            return redirect("leave_center:leave_detail", leave.id)

        # موافقة نهائية
        approval = LeaveApprovalEngine(leave, request.user)
        approval.approve("موافقة HR")

        messages.success(request, "✔ تمت الموافقة النهائية على الإجازة.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # أي حالة غير متوقعة
    # ------------------------------------------------------------
    messages.error(request, "لا يمكن إتمام العملية — حالة الطلب غير صالحة.")
    return redirect("leave_center:leave_detail", leave.id)


# ============================================================
# ❌ رفض طلب الإجازة — Reject Request (V22 Ultra Pro)
# ============================================================
@login_required
def reject_request(request, leave_id):

    leave = get_object_or_404(LeaveRequest, id=leave_id)
    employee = request.user.employee
    company = leave.company

    # حماية الشركة
    if employee.company.id != company.id:
        messages.error(request, "غير مصرح لك بالوصول.")
        return redirect("leave_center:leave_list", company.id)

    # ------------------------------------------------------------
    # 🔐 RBAC — صلاحيات الرفض
    # ------------------------------------------------------------
    if employee.role not in ["manager", "hr", "admin"]:
        messages.error(request, "لا تملك صلاحية رفض الإجازة.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # 🧠 Workflow Engine
    # ------------------------------------------------------------
    from .engines import LeaveWorkflowEngine, LeaveApprovalEngine

    workflow = LeaveWorkflowEngine(leave)
    flow = workflow.get_workflow()

    # Auto-approved أنواع مثل زواج/وفاة → لا يجوز رفضها
    if "auto" in flow:
        messages.error(request, "لا يمكن رفض هذا النوع من الإجازات (موافقة تلقائية).")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # 📝 يجب أن يكون هناك سبب (POST only)
    # ------------------------------------------------------------
    if request.method != "POST":
        messages.error(request, "يجب إرسال سبب الرفض.")
        return redirect("leave_center:leave_detail", leave.id)

    comment = request.POST.get("comment", "").strip()
    if not comment:
        messages.error(request, "الرجاء كتابة سبب الرفض.")
        return redirect("leave_center:leave_detail", leave.id)

    approval = LeaveApprovalEngine(leave, request.user)

    # ------------------------------------------------------------
    # ✳️ Manager-only Flow
    # ------------------------------------------------------------
    if flow == ["manager"]:
        if employee.role not in ["manager", "admin"]:
            messages.error(request, "هذه الإجازة تتطلب قرار المدير فقط.")
            return redirect("leave_center:leave_detail", leave.id)

        approval.reject(comment)
        messages.success(request, "❌ تم رفض الطلب من المدير.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # ✳️ HR-only Flow
    # ------------------------------------------------------------
    if flow == ["hr"]:
        if employee.role not in ["hr", "admin"]:
            messages.error(request, "هذه الإجازة تتطلب قرار HR فقط.")
            return redirect("leave_center:leave_detail", leave.id)

        approval.reject(comment)
        messages.success(request, "❌ تم رفض الطلب من قسم الموارد البشرية.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # ✳️ Manager → HR Flow
    # ------------------------------------------------------------

    # المرحلة 1 — المدير يرفض
    if leave.status == "pending" and "manager" in flow:
        if employee.role not in ["manager", "admin"]:
            messages.error(request, "لا يمكنك رفض الطلب — بانتظار المدير.")
            return redirect("leave_center:leave_detail", leave.id)

        approval.reject(comment)

        messages.success(request, "❌ تم رفض الطلب من المدير.")
        return redirect("leave_center:leave_detail", leave.id)

    # المرحلة 2 — HR يرفض
    if leave.status == "waiting_hr" and "hr" in flow:
        if employee.role not in ["hr", "admin"]:
            messages.error(request, "لا يمكنك رفض الطلب — بانتظار HR.")
            return redirect("leave_center:leave_detail", leave.id)

        approval.reject(comment)

        messages.success(request, "❌ تم رفض الطلب من قسم الموارد البشرية.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # حالات غير صالحة
    # ------------------------------------------------------------
    messages.error(request, "لا يمكن رفض هذا الطلب في وضعه الحالي.")
    return redirect("leave_center:leave_detail", leave.id)

# ============================================================
# ⚫ إلغاء طلب الإجازة — Cancel Leave (V22 Ultra Pro)
# ============================================================
@login_required
def cancel_leave(request, leave_id):

    leave = get_object_or_404(LeaveRequest, id=leave_id)
    employee = request.user.employee
    company = leave.company

    # حماية الشركة
    if employee.company.id != company.id:
        messages.error(request, "غير مصرح لك بالوصول.")
        return redirect("leave_center:leave_list", company.id)

    # ------------------------------------------------------------
    # 📝 صلاحية إلغاء الطلب
    # ------------------------------------------------------------
    is_owner = (leave.employee == employee)
    is_manager = (employee.role == "manager")
    is_hr = (employee.role == "hr")
    is_admin = (employee.role == "admin")

    if not (is_owner or is_manager or is_hr or is_admin):
        messages.error(request, "لا تملك صلاحية إلغاء هذا الطلب.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # ⛔ منع إلغاء طلب تمت الموافقة عليه
    # ------------------------------------------------------------
    if leave.status == "approved":
        messages.error(request, "لا يمكن إلغاء طلب تمت الموافقة عليه.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # ⛔ منع إلغاء طلب تم رفضه مسبقًا
    # ------------------------------------------------------------
    if leave.status == "rejected":
        messages.error(request, "لا يمكن إلغاء طلب تم رفضه مسبقًا.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # ⛔ منع إلغاء طلب تم إلغاؤه سابقًا
    # ------------------------------------------------------------
    if leave.status == "cancelled":
        messages.error(request, "تم إلغاء هذا الطلب سابقًا.")
        return redirect("leave_center:leave_detail", leave.id)

    # ------------------------------------------------------------
    # 🟣 تنفيذ الإلغاء + تسجيل اللوج
    # ------------------------------------------------------------
    from .engines import LeaveApprovalEngine

    approval = LeaveApprovalEngine(leave, request.user)
    approval.cancel("تم إلغاء الطلب بواسطة المستخدم")

    messages.success(request, "⚫ تم إلغاء طلب الإجازة بنجاح.")
    return redirect("leave_center:leave_detail", leave.id)


# ================================================================
# 🔄 Cancel Request — للموظف فقط
# ================================================================
@login_required
def cancel_request(request, leave_id):
    """
    إلغاء طلب الإجازة:
    ✔ الموظف يلغي طلبه فقط
    ✔ لا يمكن إلغاء طلب تم الموافقة عليه مسبقًا
    """

    leave_obj = get_object_or_404(LeaveRequest, id=leave_id)
    company = leave_obj.company
    user = request.user

    user_role = get_user_role(user, company)

    # الموظف فقط
    if user_role != "employee":
        messages.error(request, "❌ فقط الموظف يمكنه إلغاء طلبه.")
        return redirect("leave_center:leave_detail", leave_obj.id)

    if leave_obj.employee.user != user:
        messages.error(request, "❌ لا يمكنك إلغاء طلب يخص موظف آخر.")
        return redirect("leave_center:leave_detail", leave_obj.id)

    if leave_obj.status == "approved":
        messages.error(request, "⚠️ لا يمكن إلغاء طلب تم الموافقة عليه.")
        return redirect("leave_center:leave_detail", leave_obj.id)

    leave_obj.status = "cancelled"
    leave_obj.save()

    ApprovalLog.objects.create(
        leave_request=leave_obj,
        performed_by=user,
        action="cancelled",
        comment="تم إلغاء الطلب من الموظف"
    )

    messages.success(request, "✔ تم إلغاء الإجازة.")
    return redirect("leave_center:leave_detail", leave_obj.id)


# ================================================================
# 📅 Calendar View — FullCalendar V3 (RBAC + Filters Ready)
# ================================================================
@login_required
def leave_calendar(request, company_id):
    """
    صفحة التقويم الزمني لجميع الإجازات
    RBAC:
    - employee → إجازاته فقط
    - manager → موظفي فريقه فقط
    - HR/Admin → الجميع
    """
    company = get_object_or_404(Company, id=company_id)
    user = request.user
    user_role = get_user_role(user, company)

    employees = Employee.objects.filter(company=company)
    types = LeaveType.objects.filter(company=company)

    # ألوان الإجازات (لأسطورة التقويم)
    color_engine = LeaveTypeColorEngine(company)
    leave_type_colors = {
        lt.id: color_engine.get_color(lt.id) for lt in types
    }

    context = {
        "company": company,
        "employees": employees,
        "types": types,
        "leave_type_colors": leave_type_colors,
        "user_role": user_role,
        "page_title": "تقويم الإجازات",
    }
    return render(request, "leave_center/leave_calendar.html", context)


# ============================================================
# 📅 API — Calendar Events Provider (V22 Ultra Pro + Colors V3)
# ============================================================
@login_required
def calendar_events(request, company_id):

    company = get_object_or_404(Company, id=company_id)
    employee = request.user.employee

    # حماية الشركة
    if employee.company.id != company.id:
        return JsonResponse([], safe=False)

    # ------------------------------------------------------------
    # 📌 قراءة الفلاتر
    # ------------------------------------------------------------
    start = request.GET.get("start")
    end = request.GET.get("end")
    filter_type = request.GET.get("type")
    filter_employee = request.GET.get("employee")

    # ------------------------------------------------------------
    # 📌 QueryBase — RBAC Smart Filtering V3
    # ------------------------------------------------------------
    qs = LeaveRequest.objects.filter(
        company=company,
        start_date__lte=end,
        end_date__gte=start
    ).select_related("leave_type", "employee")

    role = employee.role

    # 🔹 الموظف يرى نفسه فقط
    if role == "employee":
        qs = qs.filter(employee=employee)

    # 🔹 المدير يرى أعضاء فريقه فقط
    elif role == "manager":
        qs = qs.filter(employee__department=employee.department)

    # 🔹 HR / Admin → وصول كامل

    # ------------------------------------------------------------
    # 🔍 فلاتر نوع الإجازة + الموظف
    # ------------------------------------------------------------
    if filter_type:
        qs = qs.filter(leave_type_id=filter_type)

    if filter_employee:
        qs = qs.filter(employee_id=filter_employee)

    # ------------------------------------------------------------
    # 🎨 ألوان الأحداث — محرك الألوان V3
    # ------------------------------------------------------------
    color_engine = LeaveTypeColorEngine(company)

    events = []

    for leave in qs:
        color = color_engine.get_color(leave.leave_type.id)

        events.append({
            "id": leave.id,
            "title": leave.leave_type.name,
            "start": str(leave.start_date),
            "end": str(leave.end_date),
            "backgroundColor": color["bg"],
            "textColor": color["text"],
            "extendedProps": {
                "employee": leave.employee.full_name,
                "start_date": str(leave.start_date),
                "end_date": str(leave.end_date),
                "type": leave.leave_type.name,
            }
        })

    return JsonResponse(events, safe=False)
# ================================================================
# 📊 Leave Balance Page — RBAC Smart View (V3 Ultra Pro)
# ================================================================
@login_required
def leave_balance_view(request, company_id):
    """
    عرض أرصدة الإجازات
    RBAC:
    - employee → رصيده فقط
    - manager → موظفي قسمه
    - HR/Admin → كل الشركة
    """

    company = get_object_or_404(Company, id=company_id)
    user = request.user
    user_role = get_user_role(user, company)

    # ------------------------------------------------------------
    # RBAC Filtering
    # ------------------------------------------------------------
    if user_role == "employee":
        balances = LeaveBalance.objects.filter(employee__user=user)

    elif user_role == "manager":
        team = Employee.objects.filter(
            manager=user,
            company=company
        )
        balances = LeaveBalance.objects.filter(employee__in=team)

    else:
        balances = LeaveBalance.objects.filter(
            employee__company=company
        )

    context = {
        "company": company,
        "balances": balances,
        "page_title": "أرصدة الإجازات"
    }

    return render(request, "leave_center/leave_balance.html", context)


# ================================================================
# 🔄 Reset Employee Leave Balance (Manual Reset)
# ================================================================
@login_required
def reset_leave_balance(request, company_id, employee_id, leave_type_id):
    """
    إعادة ضبط رصيد الإجازة يدويًا
    RBAC:
    - HR/Admin فقط
    """

    company = get_object_or_404(Company, id=company_id)
    user_role = get_user_role(request.user, company)

    if user_role not in ["hr", "admin"]:
        messages.error(request, "❌ غير مصرح لك بتنفيذ هذا الإجراء.")
        return redirect("leave_center:leave_balance", company.id)

    employee = get_object_or_404(Employee, id=employee_id, company=company)
    leave_type = get_object_or_404(LeaveType, id=leave_type_id, company=company)

    balance = LeaveBalance.objects.filter(
        employee=employee,
        leave_type=leave_type
    ).first()

    if not balance:
        messages.error(request, "❌ لا يوجد رصيد مرتبط.")
        return redirect("leave_center:leave_balance", company.id)

    old_value = balance.remaining_balance
    balance.remaining_balance = leave_type.annual_balance
    balance.save()

    # ------------------------------------------------------------
    # 📝 تسجيل سجل ResetHistory — يدعم التقويم السنوي
    # ------------------------------------------------------------
    from .models import ResetHistory

    ResetHistory.objects.create(
        company=company,
        employee=employee,
        leave_type=leave_type,
        old_balance=old_value,
        new_balance=leave_type.annual_balance,
        year=now().year,
        performed_by=request.user,
    )

    messages.success(request, "✔ تم إعادة ضبط الرصيد.")
    return redirect("leave_center:leave_balance", company.id)


# ================================================================
# 🟦 Apply Leave To Attendance (When Approved)
# ================================================================
@login_required
def apply_leave_to_attendance(request, leave_id):
    """
    عند الموافقة على الإجازة → يصبح غياب مصرح به في الحضور
    (سيتم تفعيل التكامل مع Attendance Center لاحقًا)
    """

    leave_obj = get_object_or_404(LeaveRequest, id=leave_id)
    company = leave_obj.company
    user = request.user

    user_role = get_user_role(user, company)

    if user_role not in ["manager", "hr", "admin"]:
        messages.error(request, "❌ غير مسموح.")
        return redirect("leave_center:leave_detail", leave_obj.id)

    # TODO: التكامل مع Attendance Center (Biotime Sync)
    messages.info(request, "ℹ سيتم التكامل مع وحدة الحضور لاحقًا.")

    return redirect("leave_center:leave_detail", leave_obj.id)


# ================================================================
# 🗑 Delete Leave — HR/Admin Only (V21 Ultra Pro)
# ================================================================
@login_required
def delete_leave(request, leave_id):
    """
    حذف طلب الإجازة — HR/Admin فقط
    """

    leave_obj = get_object_or_404(LeaveRequest, id=leave_id)
    company = leave_obj.company
    user_role = get_user_role(request.user, company)

    if user_role not in ["hr", "admin"]:
        messages.error(request, "❌ غير مسموح بالحذف.")
        return redirect("leave_center:leave_detail", leave_obj.id)

    leave_obj.delete()

    messages.success(request, "✔ تم حذف طلب الإجازة.")
    return redirect("leave_center:leave_list", company.id)
