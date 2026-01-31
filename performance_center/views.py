from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Q
from django.utils import timezone

from .models import (
    PerformanceTemplate,
    PerformanceCategory,
    PerformanceItem,
    PerformanceReview,
    PerformanceAnswer,
    PerformanceWorkflowStatus,
)

from company_manager.models import Company
from employee_center.models import Employee


# ================================================================
# 📌 1) Dashboard — لوحة التحكم الرئيسية
# ================================================================
@login_required
def performance_dashboard(request):
    company = request.user.company_memberships.first().company

    total_reviews = PerformanceReview.objects.filter(
        employee__company=company
    ).count()

    pending_self = PerformanceReview.objects.filter(
        employee__company=company,
        status="SELF_PENDING"
    ).count()

    pending_manager = PerformanceReview.objects.filter(
        employee__company=company,
        status="MANAGER_PENDING"
    ).count()

    pending_hr = PerformanceReview.objects.filter(
        employee__company=company,
        status="HR_PENDING"
    ).count()

    completed = PerformanceReview.objects.filter(
        employee__company=company,
        status="COMPLETED"
    ).count()

    context = {
        "company": company,
        "total_reviews": total_reviews,
        "pending_self": pending_self,
        "pending_manager": pending_manager,
        "pending_hr": pending_hr,
        "completed": completed,
    }

    return render(request, "performance_center/dashboard.html", context)


# ================================================================
# 📌 2) Templates — إدارة قوالب التقييم
# ================================================================
@login_required
def template_list(request):
    company = request.user.company_memberships.first().company
    templates = PerformanceTemplate.objects.filter(company=company)
    return render(request, "performance_center/template_list.html", {"templates": templates})


@login_required
def template_add(request):
    company = request.user.company_memberships.first().company

    if request.method == "POST":
        name = request.POST.get("name")
        period = request.POST.get("period")
        description = request.POST.get("description")

        PerformanceTemplate.objects.create(
            company=company,
            name=name,
            period=period,
            description=description,
        )

        messages.success(request, "تم إنشاء قالب التقييم بنجاح")
        return redirect("performance:template_list")

    return render(request, "performance_center/template_add.html")


@login_required
def template_edit(request, template_id):
    template = get_object_or_404(PerformanceTemplate, id=template_id)

    if request.method == "POST":
        template.name = request.POST.get("name")
        template.period = request.POST.get("period")
        template.description = request.POST.get("description")
        template.save()

        messages.success(request, "تم تعديل القالب بنجاح")
        return redirect("performance:template_list")

    return render(request, "performance_center/template_edit.html", {"template": template})


@login_required
def template_delete(request, template_id):
    template = get_object_or_404(PerformanceTemplate, id=template_id)
    template.delete()
    messages.success(request, "تم حذف القالب بنجاح")
    return redirect("performance:template_list")


# ================================================================
# 📌 3) Categories — فئات التقييم
# ================================================================
@login_required
def category_list(request, template_id):
    template = get_object_or_404(PerformanceTemplate, id=template_id)
    categories = template.categories.all()
    return render(request, "performance_center/category_list.html", {"template": template, "categories": categories})


@login_required
def category_add(request, template_id):
    template = get_object_or_404(PerformanceTemplate, id=template_id)

    if request.method == "POST":
        name = request.POST.get("name")
        weight = request.POST.get("weight")

        PerformanceCategory.objects.create(
            template=template,
            name=name,
            weight=weight,
        )

        messages.success(request, "تم إضافة الفئة بنجاح")
        return redirect("performance:category_list", template_id=template.id)

    return render(request, "performance_center/category_add.html", {"template": template})


@login_required
def category_edit(request, category_id):
    category = get_object_or_404(PerformanceCategory, id=category_id)

    if request.method == "POST":
        category.name = request.POST.get("name")
        category.weight = request.POST.get("weight")
        category.save()

        messages.success(request, "تم تعديل الفئة بنجاح")
        return redirect("performance:category_list", template_id=category.template.id)

    return render(request, "performance_center/category_edit.html", {"category": category})


@login_required
def category_delete(request, category_id):
    category = get_object_or_404(PerformanceCategory, id=category_id)
    template_id = category.template.id
    category.delete()
    messages.success(request, "تم حذف الفئة")
    return redirect("performance:category_list", template_id=template_id)


# ================================================================
# 📌 4) Items — عناصر التقييم داخل كل فئة
# ================================================================
@login_required
def item_list(request, category_id):
    category = get_object_or_404(PerformanceCategory, id=category_id)
    items = category.items.all()
    return render(request, "performance_center/item_list.html", {"category": category, "items": items})


@login_required
def item_add(request, category_id):
    category = get_object_or_404(PerformanceCategory, id=category_id)

    if request.method == "POST":
        question = request.POST.get("question")
        item_type = request.POST.get("item_type")
        max_score = request.POST.get("max_score")
        weight = request.POST.get("weight")

        PerformanceItem.objects.create(
            category=category,
            question=question,
            item_type=item_type,
            max_score=max_score,
            weight=weight,
        )

        messages.success(request, "تم إضافة عنصر التقييم بنجاح")
        return redirect("performance:item_list", category_id=category.id)

    return render(request, "performance_center/item_add.html", {"category": category})


@login_required
def item_edit(request, item_id):
    item = get_object_or_404(PerformanceItem, id=item_id)

    if request.method == "POST":
        item.question = request.POST.get("question")
        item.item_type = request.POST.get("item_type")
        item.max_score = request.POST.get("max_score")
        item.weight = request.POST.get("weight")
        item.save()

        messages.success(request, "تم تعديل عنصر التقييم بنجاح")
        return redirect("performance:item_list", category_id=item.category.id)

    return render(request, "performance_center/item_edit.html", {"item": item})


@login_required
def item_delete(request, item_id):
    item = get_object_or_404(PerformanceItem, id=item_id)
    category_id = item.category.id
    item.delete()
    messages.success(request, "تم حذف العنصر")
    return redirect("performance:item_list", category_id=category_id)


# ================================================================
# 📌 5) Reviews — إدارة تقييمات الموظفين
# ================================================================
@login_required
def review_list(request):
    company = request.user.company_memberships.first().company
    reviews = PerformanceReview.objects.filter(employee__company=company)
    return render(request, "performance_center/review_list.html", {"reviews": reviews})


@login_required
def review_start(request, employee_id, template_id):
    employee = get_object_or_404(Employee, id=employee_id)
    template = get_object_or_404(PerformanceTemplate, id=template_id)

    # منع تكرار نفس الفترة
    period_label = f"{timezone.now().year}"

    existing = PerformanceReview.objects.filter(
        employee=employee,
        template=template,
        period_label=period_label
    ).first()

    if existing:
        messages.error(request, "هذا الموظف لديه تقييم لنفس الفترة بالفعل")
        return redirect("performance:review_list")

    review = PerformanceReview.objects.create(
        employee=employee,
        template=template,
        period_label=period_label
    )

    PerformanceWorkflowStatus.objects.create(review=review)

    messages.success(request, "تم إنشاء تقييم الموظف")
    return redirect("performance:review_detail", review_id=review.id)


@login_required
def review_detail(request, review_id):
    review = get_object_or_404(PerformanceReview, id=review_id)
    answers = review.answers.all()
    categories = review.template.categories.all()

    return render(request, "performance_center/review_detail.html", {
        "review": review,
        "answers": answers,
        "categories": categories,
    })


# ================================================================
# 📌 6) Self Evaluation — تقييم الموظف لنفسه
# ================================================================
@login_required
def self_review(request, review_id):
    review = get_object_or_404(PerformanceReview, id=review_id)

    categories = review.template.categories.prefetch_related("items")

    if request.method == "POST":
        for category in categories:
            for item in category.items.all():
                field = f"item_{item.id}"
                score = request.POST.get(field)

                answer, created = PerformanceAnswer.objects.get_or_create(
                    review=review,
                    item=item,
                )

                answer.self_score = score
                answer.save()

        review.self_score = review.answers.aggregate(Avg("self_score"))["self_score__avg"]
        review.status = "MANAGER_PENDING"
        review.save()

        review.workflow.self_completed = True
        review.workflow.save()

        messages.success(request, "تم إرسال تقييم الموظف")
        return redirect("performance:review_detail", review_id=review.id)

    return render(request, "performance_center/self_review.html", {
        "review": review,
        "categories": categories,
    })


# ================================================================
# 📌 7) Manager Review — تقييم المدير
# ================================================================
@login_required
def manager_review(request, review_id):
    review = get_object_or_404(PerformanceReview, id=review_id)
    categories = review.template.categories.prefetch_related("items")

    if request.method == "POST":
        for category in categories:
            for item in category.items.all():
                field = f"item_{item.id}"
                score = request.POST.get(field)

                answer, _ = PerformanceAnswer.objects.get_or_create(
                    review=review,
                    item=item,
                )

                answer.manager_score = score
                answer.save()

        review.manager_score = review.answers.aggregate(Avg("manager_score"))["manager_score__avg"]
        review.status = "HR_PENDING"
        review.save()

        review.workflow.manager_completed = True
        review.workflow.save()

        messages.success(request, "تم إرسال تقييم المدير")
        return redirect("performance:review_detail", review_id=review.id)

    return render(request, "performance_center/manager_review.html", {
        "review": review,
        "categories": categories,
    })


# ================================================================
# 📌 8) HR Review — تقييم الموارد البشرية
# ================================================================
@login_required
def hr_review(request, review_id):
    review = get_object_or_404(PerformanceReview, id=review_id)
    categories = review.template.categories.prefetch_related("items")

    if request.method == "POST":
        for category in categories:
            for item in category.items.all():
                field = f"item_{item.id}"
                score = request.POST.get(field)

                answer, _ = PerformanceAnswer.objects.get_or_create(
                    review=review,
                    item=item,
                )

                answer.hr_score = score
                answer.save()

        review.hr_score = review.answers.aggregate(Avg("hr_score"))["hr_score__avg"]
        review.status = "COMPLETED"
        review.final_score = (
            (review.self_score or 0) +
            (review.manager_score or 0) +
            (review.hr_score or 0)
        ) / 3
        review.save()

        review.workflow.hr_completed = True
        review.workflow.save()

        messages.success(request, "تم اعتماد تقييم HR")
        return redirect("performance:review_detail", review_id=review.id)

    return render(request, "performance_center/hr_review.html", {
        "review": review,
        "categories": categories,
    })
# ================================================================
# 📊 Views — Performance Center Reports (PDF + Excel)
# ================================================================
from django.http import HttpResponse
from .reports import (
    generate_review_pdf,
    generate_employee_summary_pdf,
    export_reviews_excel,
)


# ------------------------------------------------------------
# 📝 1) تقرير PDF لتقييم واحد — Review Detail PDF
# ------------------------------------------------------------
@login_required
def review_pdf_view(request, review_id):
    """
    🔥 إنشاء PDF لتقرير تقييم واحد
    """
    return generate_review_pdf(review_id)


# ------------------------------------------------------------
# 👤 2) تقرير شامل لموظف واحد — Employee Summary PDF
# ------------------------------------------------------------
@login_required
def employee_summary_pdf_view(request, employee_id):
    """
    🔥 إنشاء تقرير PDF لجميع تقييمات الموظف
    """
    return generate_employee_summary_pdf(employee_id)


# ------------------------------------------------------------
# 📊 3) تصدير Excel — جميع التقييمات
# ------------------------------------------------------------
@login_required
def reviews_excel_export(request):
    """
    🔥 إنشاء ملف Excel يحتوي جميع التقييمات داخل النظام
    """
    return export_reviews_excel()
