# ============================================================
# 📂 الملف: api/company/performance.py
# 🎯 Company Performance API
# Primey HR Cloud
# ============================================================

from __future__ import annotations

import json
import logging
from typing import Optional, Tuple

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from company_manager.models import CompanyUser
from employee_center.models import Employee
from performance_center.models import (
    PerformanceTemplate,
    PerformanceCategory,
    PerformanceItem,
    PerformanceReview,
    PerformanceAnswer,
    PerformanceWorkflowStatus,
)

logger = logging.getLogger(__name__)


# ============================================================
# Helpers
# ============================================================

def _json_body(request) -> dict:
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


def _get_active_company(request):
    """
    إحضار الشركة النشطة من الجلسة، مع fallback لأول شركة مرتبطة بالمستخدم.
    ملاحظة:
    role في CompanyUser عندنا ليس علاقة FK، لذلك لا يجوز وضعه داخل select_related.
    """
    user = request.user
    active_company_id = request.session.get("active_company_id")

    company_user_qs = (
        CompanyUser.objects
        .select_related("company")
        .filter(user=user)
    )

    if active_company_id:
        active_link = company_user_qs.filter(company_id=active_company_id).first()
        if active_link:
            return active_link.company, active_link

    fallback_link = company_user_qs.first()
    if fallback_link:
        return fallback_link.company, fallback_link

    return None, None


def _error(message: str, status: int = 400, extra: Optional[dict] = None):
    payload = {"status": "error", "message": message}
    if extra:
        payload.update(extra)
    return JsonResponse(payload, status=status)


def _safe_float(value):
    try:
        if value in ("", None):
            return None
        return float(value)
    except Exception:
        return None


def _review_queryset(company):
    """
    Queryset أساسي مع الشركة.
    نفترض أن Employee مرتبط بالشركة كما هو نمط المشروع.
    """
    return (
        PerformanceReview.objects
        .select_related("employee", "template")
        .prefetch_related(
            "answers__item__category",
            "workflow",
        )
        .filter(template__company=company)
        .order_by("-created_at")
    )


def _template_queryset(company):
    return (
        PerformanceTemplate.objects
        .filter(company=company)
        .prefetch_related("categories__items")
        .order_by("-created_at")
    )


def _serialize_template(template: PerformanceTemplate) -> dict:
    categories_payload = []

    for category in template.categories.all().order_by("name"):
        items_payload = []
        for item in category.items.all().order_by("weight", "id"):
            items_payload.append({
                "id": item.id,
                "question": item.question,
                "item_type": item.item_type,
                "max_score": item.max_score,
                "weight": item.weight,
            })

        categories_payload.append({
            "id": category.id,
            "name": category.name,
            "weight": category.weight,
            "items_count": len(items_payload),
            "items": items_payload,
        })

    return {
        "id": template.id,
        "name": template.name,
        "period": template.period,
        "description": template.description,
        "is_active": template.is_active,
        "categories_count": len(categories_payload),
        "categories": categories_payload,
        "created_at": template.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": template.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _serialize_review(review: PerformanceReview) -> dict:
    workflow = getattr(review, "workflow", None)

    employee_name = getattr(review.employee, "full_name", None) or getattr(review.employee, "name", None) or str(review.employee)
    employee_email = getattr(review.employee, "email", None)
    employee_phone = getattr(review.employee, "mobile_number", None) or getattr(review.employee, "phone", None)
    employee_avatar = getattr(review.employee, "photo_url", None) or getattr(review.employee, "avatar", None)

    answers_payload = []
    for answer in review.answers.all():
        item = answer.item
        category = item.category if item else None

        answers_payload.append({
            "id": answer.id,
            "item_id": item.id if item else None,
            "question": item.question if item else None,
            "item_type": item.item_type if item else None,
            "max_score": item.max_score if item else None,
            "item_weight": item.weight if item else None,
            "category_id": category.id if category else None,
            "category_name": category.name if category else None,

            "self_answer": answer.self_answer,
            "manager_answer": answer.manager_answer,
            "hr_answer": answer.hr_answer,

            "self_score": answer.self_score,
            "manager_score": answer.manager_score,
            "hr_score": answer.hr_score,
        })

    return {
        "id": review.id,
        "employee": {
            "id": review.employee_id,
            "name": employee_name,
            "email": employee_email,
            "phone": employee_phone,
            "avatar": employee_avatar,
        },
        "template": {
            "id": review.template_id,
            "name": review.template.name if review.template else None,
            "period": review.template.period if review.template else None,
        },
        "period_label": review.period_label,
        "status": review.status,
        "self_score": review.self_score,
        "manager_score": review.manager_score,
        "hr_score": review.hr_score,
        "final_score": review.final_score,
        "final_decision": review.final_decision,
        "workflow": {
            "self_completed": workflow.self_completed if workflow else False,
            "manager_completed": workflow.manager_completed if workflow else False,
            "hr_completed": workflow.hr_completed if workflow else False,
            "last_update": workflow.last_update.strftime("%Y-%m-%d %H:%M:%S") if workflow else None,
        },
        "answers_count": len(answers_payload),
        "answers": answers_payload,
        "created_at": review.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": review.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _get_role_flags(company_user: CompanyUser) -> Tuple[bool, bool, bool]:
    """
    تحديد صلاحيات مرنة حسب نوع حقل role:
    - إذا كان نصيًا: نقرأه مباشرة
    - إذا كان object relation مستقبلًا: نحاول قراءة name
    """
    raw_role = getattr(company_user, "role", "")

    if isinstance(raw_role, str):
        role_name = raw_role.strip().upper()
    else:
        role_name = str(getattr(raw_role, "name", raw_role or "")).strip().upper()

    is_admin = role_name in {"ADMIN", "OWNER", "SUPER_ADMIN"}
    is_manager = role_name in {"ADMIN", "OWNER", "SUPER_ADMIN", "MANAGER", "HR_MANAGER", "TEAM_LEAD"}
    is_hr = role_name in {"ADMIN", "OWNER", "SUPER_ADMIN", "HR", "HR_MANAGER"}

    return is_admin, is_manager, is_hr


def _recalculate_review_scores(review: PerformanceReview) -> None:
    """
    إعادة حساب مجاميع الدرجات على مستوى التقييم.
    """
    answers = review.answers.select_related("item").all()

    self_scores = []
    manager_scores = []
    hr_scores = []

    for ans in answers:
        if ans.self_score is not None:
            self_scores.append(ans.self_score)
        if ans.manager_score is not None:
            manager_scores.append(ans.manager_score)
        if ans.hr_score is not None:
            hr_scores.append(ans.hr_score)

    review.self_score = round(sum(self_scores), 2) if self_scores else None
    review.manager_score = round(sum(manager_scores), 2) if manager_scores else None
    review.hr_score = round(sum(hr_scores), 2) if hr_scores else None

    final_candidates = [x for x in [review.self_score, review.manager_score, review.hr_score] if x is not None]
    review.final_score = round(sum(final_candidates) / len(final_candidates), 2) if final_candidates else None
    review.save(update_fields=["self_score", "manager_score", "hr_score", "final_score", "updated_at"])


def _ensure_answer_rows(review: PerformanceReview) -> None:
    """
    إنشاء صفوف الإجابات تلقائيًا لكل عناصر القالب.
    """
    template_items = PerformanceItem.objects.filter(category__template=review.template).select_related("category")
    existing_item_ids = set(
        PerformanceAnswer.objects.filter(review=review).values_list("item_id", flat=True)
    )

    to_create = []
    for item in template_items:
        if item.id not in existing_item_ids:
            to_create.append(PerformanceAnswer(review=review, item=item))

    if to_create:
        PerformanceAnswer.objects.bulk_create(to_create)


# ============================================================
# Dashboard
# ============================================================

@login_required
@require_GET
def performance_dashboard(request):
    company, company_user = _get_active_company(request)
    if not company or not company_user:
        return _error("لم يتم العثور على شركة نشطة للمستخدم.", 403)

    reviews_qs = _review_queryset(company)
    templates_qs = _template_queryset(company)

    status_summary = {
        "self_pending": reviews_qs.filter(status="SELF_PENDING").count(),
        "manager_pending": reviews_qs.filter(status="MANAGER_PENDING").count(),
        "hr_pending": reviews_qs.filter(status="HR_PENDING").count(),
        "completed": reviews_qs.filter(status="COMPLETED").count(),
    }

    recent_reviews = [_serialize_review(obj) for obj in reviews_qs[:5]]

    return JsonResponse({
        "status": "ok",
        "summary": {
            "templates_count": templates_qs.count(),
            "reviews_count": reviews_qs.count(),
            "completed_reviews_count": status_summary["completed"],
            "average_final_score": reviews_qs.aggregate(avg=Avg("final_score")).get("avg"),
            "status_summary": status_summary,
        },
        "recent_reviews": recent_reviews,
    })


# ============================================================
# Templates
# ============================================================

@login_required
@require_GET
def performance_templates_list(request):
    company, company_user = _get_active_company(request)
    if not company:
        return _error("لم يتم العثور على شركة نشطة.", 403)

    active_only = request.GET.get("active")
    qs = _template_queryset(company)

    if active_only in {"1", "true", "TRUE", "yes"}:
        qs = qs.filter(is_active=True)

    return JsonResponse({
        "status": "ok",
        "templates": [_serialize_template(obj) for obj in qs],
    })


@login_required
@require_POST
def performance_template_create(request):
    company, company_user = _get_active_company(request)
    if not company or not company_user:
        return _error("لم يتم العثور على شركة نشطة.", 403)

    is_admin, _, is_hr = _get_role_flags(company_user)
    if not (is_admin or is_hr):
        return _error("ليس لديك صلاحية إنشاء قوالب التقييم.", 403)

    data = _json_body(request)

    name = str(data.get("name", "")).strip()
    period = str(data.get("period", "YEARLY")).strip().upper()
    description = str(data.get("description", "")).strip()
    is_active = bool(data.get("is_active", True))
    categories = data.get("categories", [])

    if not name:
        return _error("اسم القالب مطلوب.")

    if period not in {"YEARLY", "QUARTERLY", "MONTHLY"}:
        return _error("نوع الفترة غير صالح.")

    if not isinstance(categories, list) or not categories:
        return _error("يجب إرسال categories كمصفوفة وتحتوي على الأقل فئة واحدة.")

    try:
        with transaction.atomic():
            template = PerformanceTemplate.objects.create(
                company=company,
                name=name,
                period=period,
                description=description or None,
                is_active=is_active,
            )

            for category_data in categories:
                category_name = str(category_data.get("name", "")).strip()
                category_weight = int(category_data.get("weight", 20) or 20)
                items = category_data.get("items", [])

                if not category_name:
                    raise ValueError("كل فئة يجب أن تحتوي على اسم.")
                if not isinstance(items, list) or not items:
                    raise ValueError(f"الفئة [{category_name}] يجب أن تحتوي على عناصر.")

                category = PerformanceCategory.objects.create(
                    template=template,
                    name=category_name,
                    weight=category_weight,
                )

                for item_data in items:
                    question = str(item_data.get("question", "")).strip()
                    item_type = str(item_data.get("item_type", "SCORE")).strip().upper()
                    max_score = int(item_data.get("max_score", 5) or 5)
                    weight = int(item_data.get("weight", 10) or 10)

                    if not question:
                        raise ValueError(f"يوجد عنصر بدون سؤال داخل الفئة [{category_name}].")
                    if item_type not in {"SCORE", "TEXT"}:
                        raise ValueError(f"نوع العنصر غير صالح داخل الفئة [{category_name}].")

                    PerformanceItem.objects.create(
                        category=category,
                        question=question,
                        item_type=item_type,
                        max_score=max_score,
                        weight=weight,
                    )

    except ValueError as exc:
        logger.warning("Performance template validation error: %s", exc)
        return _error(str(exc))
    except Exception as exc:
        logger.exception("Performance template create failed: %s", exc)
        return _error("تعذر إنشاء قالب التقييم.", 500)

    template = _template_queryset(company).get(id=template.id)
    return JsonResponse({
        "status": "ok",
        "message": "تم إنشاء قالب التقييم بنجاح.",
        "template": _serialize_template(template),
    })


# ============================================================
# Reviews
# ============================================================

@login_required
@require_GET
def performance_reviews_list(request):
    company, company_user = _get_active_company(request)
    if not company:
        return _error("لم يتم العثور على شركة نشطة.", 403)

    qs = _review_queryset(company)

    status_filter = str(request.GET.get("status", "")).strip().upper()
    employee_id = request.GET.get("employee_id")
    template_id = request.GET.get("template_id")
    search = str(request.GET.get("search", "")).strip()

    if status_filter:
        qs = qs.filter(status=status_filter)

    if employee_id:
        qs = qs.filter(employee_id=employee_id)

    if template_id:
        qs = qs.filter(template_id=template_id)

    if search:
        qs = qs.filter(
            Q(employee__full_name__icontains=search) |
            Q(employee__name__icontains=search) |
            Q(period_label__icontains=search) |
            Q(template__name__icontains=search)
        )

    return JsonResponse({
        "status": "ok",
        "reviews": [_serialize_review(obj) for obj in qs],
    })


@login_required
@require_GET
def performance_review_detail(request, review_id: int):
    company, company_user = _get_active_company(request)
    if not company:
        return _error("لم يتم العثور على شركة نشطة.", 403)

    review = _review_queryset(company).filter(id=review_id).first()
    if not review:
        return _error("التقييم غير موجود.", 404)

    _ensure_answer_rows(review)
    review = _review_queryset(company).get(id=review.id)

    return JsonResponse({
        "status": "ok",
        "review": _serialize_review(review),
    })


@login_required
@require_POST
def performance_review_create(request):
    company, company_user = _get_active_company(request)
    if not company or not company_user:
        return _error("لم يتم العثور على شركة نشطة.", 403)

    is_admin, is_manager, is_hr = _get_role_flags(company_user)
    if not (is_admin or is_manager or is_hr):
        return _error("ليس لديك صلاحية إنشاء تقييم جديد.", 403)

    data = _json_body(request)

    employee_id = data.get("employee_id")
    template_id = data.get("template_id")
    period_label = str(data.get("period_label", "")).strip()

    if not employee_id:
        return _error("employee_id مطلوب.")
    if not template_id:
        return _error("template_id مطلوب.")
    if not period_label:
        return _error("period_label مطلوب.")

    employee = Employee.objects.filter(id=employee_id).first()
    if not employee:
        return _error("الموظف غير موجود.", 404)

    template = PerformanceTemplate.objects.filter(id=template_id, company=company).first()
    if not template:
        return _error("قالب التقييم غير موجود أو لا يخص الشركة الحالية.", 404)

    existing = PerformanceReview.objects.filter(
        employee_id=employee_id,
        template_id=template_id,
        period_label=period_label,
    ).first()
    if existing:
        return _error(
            "يوجد تقييم لنفس الموظف ونفس القالب ونفس الدورة مسبقًا.",
            409,
            extra={"review_id": existing.id},
        )

    try:
        with transaction.atomic():
            review = PerformanceReview.objects.create(
                employee=employee,
                template=template,
                period_label=period_label,
                status="SELF_PENDING",
            )

            _ensure_answer_rows(review)

            PerformanceWorkflowStatus.objects.create(
                review=review,
                self_completed=False,
                manager_completed=False,
                hr_completed=False,
            )

    except Exception as exc:
        logger.exception("Performance review create failed: %s", exc)
        return _error("تعذر إنشاء التقييم.", 500)

    review = _review_queryset(company).get(id=review.id)

    return JsonResponse({
        "status": "ok",
        "message": "تم إنشاء تقييم الأداء بنجاح.",
        "review": _serialize_review(review),
    })


# ============================================================
# Submit Answers
# ============================================================

@login_required
@require_POST
def performance_submit_self(request, review_id: int):
    company, company_user = _get_active_company(request)
    if not company:
        return _error("لم يتم العثور على شركة نشطة.", 403)

    review = _review_queryset(company).filter(id=review_id).first()
    if not review:
        return _error("التقييم غير موجود.", 404)

    data = _json_body(request)
    answers = data.get("answers", [])

    if not isinstance(answers, list) or not answers:
        return _error("يجب إرسال answers كمصفوفة.")

    try:
        with transaction.atomic():
            _ensure_answer_rows(review)

            for row in answers:
                answer_id = row.get("answer_id")
                item_id = row.get("item_id")

                answer = None
                if answer_id:
                    answer = PerformanceAnswer.objects.filter(
                        id=answer_id,
                        review=review,
                    ).select_related("item").first()
                elif item_id:
                    answer = PerformanceAnswer.objects.filter(
                        review=review,
                        item_id=item_id,
                    ).select_related("item").first()

                if not answer:
                    raise ValueError("تعذر العثور على أحد عناصر الإجابة.")

                answer.self_answer = row.get("answer")
                if answer.item.item_type == "SCORE":
                    score = _safe_float(row.get("score"))
                    if score is not None and score > answer.item.max_score:
                        raise ValueError(f"درجة الموظف أكبر من الحد الأقصى للسؤال: {answer.item.question}")
                    answer.self_score = score
                answer.save()

            workflow, _ = PerformanceWorkflowStatus.objects.get_or_create(review=review)
            workflow.self_completed = True
            workflow.save(update_fields=["self_completed", "last_update"])

            review.status = "MANAGER_PENDING"
            review.save(update_fields=["status", "updated_at"])

            _recalculate_review_scores(review)

    except ValueError as exc:
        return _error(str(exc))
    except Exception as exc:
        logger.exception("Performance self submit failed: %s", exc)
        return _error("تعذر حفظ تقييم الموظف.", 500)

    review = _review_queryset(company).get(id=review.id)
    return JsonResponse({
        "status": "ok",
        "message": "تم إرسال تقييم الموظف بنجاح.",
        "review": _serialize_review(review),
    })


@login_required
@require_POST
def performance_submit_manager(request, review_id: int):
    company, company_user = _get_active_company(request)
    if not company or not company_user:
        return _error("لم يتم العثور على شركة نشطة.", 403)

    _, is_manager, _ = _get_role_flags(company_user)
    if not is_manager:
        return _error("ليس لديك صلاحية تقييم المدير.", 403)

    review = _review_queryset(company).filter(id=review_id).first()
    if not review:
        return _error("التقييم غير موجود.", 404)

    data = _json_body(request)
    answers = data.get("answers", [])

    if not isinstance(answers, list) or not answers:
        return _error("يجب إرسال answers كمصفوفة.")

    try:
        with transaction.atomic():
            _ensure_answer_rows(review)

            for row in answers:
                answer_id = row.get("answer_id")
                item_id = row.get("item_id")

                answer = None
                if answer_id:
                    answer = PerformanceAnswer.objects.filter(
                        id=answer_id,
                        review=review,
                    ).select_related("item").first()
                elif item_id:
                    answer = PerformanceAnswer.objects.filter(
                        review=review,
                        item_id=item_id,
                    ).select_related("item").first()

                if not answer:
                    raise ValueError("تعذر العثور على أحد عناصر الإجابة.")

                answer.manager_answer = row.get("answer")
                if answer.item.item_type == "SCORE":
                    score = _safe_float(row.get("score"))
                    if score is not None and score > answer.item.max_score:
                        raise ValueError(f"درجة المدير أكبر من الحد الأقصى للسؤال: {answer.item.question}")
                    answer.manager_score = score
                answer.save()

            workflow, _ = PerformanceWorkflowStatus.objects.get_or_create(review=review)
            workflow.manager_completed = True
            workflow.save(update_fields=["manager_completed", "last_update"])

            review.status = "HR_PENDING"
            review.save(update_fields=["status", "updated_at"])

            _recalculate_review_scores(review)

    except ValueError as exc:
        return _error(str(exc))
    except Exception as exc:
        logger.exception("Performance manager submit failed: %s", exc)
        return _error("تعذر حفظ تقييم المدير.", 500)

    review = _review_queryset(company).get(id=review.id)
    return JsonResponse({
        "status": "ok",
        "message": "تم إرسال تقييم المدير بنجاح.",
        "review": _serialize_review(review),
    })


@login_required
@require_POST
def performance_submit_hr(request, review_id: int):
    company, company_user = _get_active_company(request)
    if not company or not company_user:
        return _error("لم يتم العثور على شركة نشطة.", 403)

    _, _, is_hr = _get_role_flags(company_user)
    if not is_hr:
        return _error("ليس لديك صلاحية تقييم الموارد البشرية.", 403)

    review = _review_queryset(company).filter(id=review_id).first()
    if not review:
        return _error("التقييم غير موجود.", 404)

    data = _json_body(request)
    answers = data.get("answers", [])
    final_decision = str(data.get("final_decision", review.final_decision or "NORMAL")).strip().upper()

    if not isinstance(answers, list) or not answers:
        return _error("يجب إرسال answers كمصفوفة.")

    if final_decision not in {"NORMAL", "PROMOTION", "BONUS", "WARNING", "IMPROVEMENT_PLAN"}:
        return _error("القرار النهائي غير صالح.")

    try:
        with transaction.atomic():
            _ensure_answer_rows(review)

            for row in answers:
                answer_id = row.get("answer_id")
                item_id = row.get("item_id")

                answer = None
                if answer_id:
                    answer = PerformanceAnswer.objects.filter(
                        id=answer_id,
                        review=review,
                    ).select_related("item").first()
                elif item_id:
                    answer = PerformanceAnswer.objects.filter(
                        review=review,
                        item_id=item_id,
                    ).select_related("item").first()

                if not answer:
                    raise ValueError("تعذر العثور على أحد عناصر الإجابة.")

                answer.hr_answer = row.get("answer")
                if answer.item.item_type == "SCORE":
                    score = _safe_float(row.get("score"))
                    if score is not None and score > answer.item.max_score:
                        raise ValueError(f"درجة HR أكبر من الحد الأقصى للسؤال: {answer.item.question}")
                    answer.hr_score = score
                answer.save()

            workflow, _ = PerformanceWorkflowStatus.objects.get_or_create(review=review)
            workflow.hr_completed = True
            workflow.save(update_fields=["hr_completed", "last_update"])

            review.status = "COMPLETED"
            review.final_decision = final_decision
            review.save(update_fields=["status", "final_decision", "updated_at"])

            _recalculate_review_scores(review)

    except ValueError as exc:
        return _error(str(exc))
    except Exception as exc:
        logger.exception("Performance HR submit failed: %s", exc)
        return _error("تعذر حفظ تقييم الموارد البشرية.", 500)

    review = _review_queryset(company).get(id=review.id)
    return JsonResponse({
        "status": "ok",
        "message": "تم اعتماد تقييم الموارد البشرية وإكمال التقييم بنجاح.",
        "review": _serialize_review(review),
    })


# ============================================================
# Workflow
# ============================================================

@login_required
@require_GET
def performance_workflow_status(request, review_id: int):
    company, company_user = _get_active_company(request)
    if not company:
        return _error("لم يتم العثور على شركة نشطة.", 403)

    review = _review_queryset(company).filter(id=review_id).first()
    if not review:
        return _error("التقييم غير موجود.", 404)

    workflow, _ = PerformanceWorkflowStatus.objects.get_or_create(review=review)

    return JsonResponse({
        "status": "ok",
        "workflow": {
            "review_id": review.id,
            "status": review.status,
            "self_completed": workflow.self_completed,
            "manager_completed": workflow.manager_completed,
            "hr_completed": workflow.hr_completed,
            "last_update": workflow.last_update.strftime("%Y-%m-%d %H:%M:%S"),
        }
    })


# ============================================================
# Simple lookup endpoints for frontend bootstrapping
# ============================================================

@login_required
@require_GET
def performance_employees_lookup(request):
    company, company_user = _get_active_company(request)
    if not company:
        return _error("لم يتم العثور على شركة نشطة.", 403)

    employees = Employee.objects.filter(company=company).order_by("id")

    payload = []
    for emp in employees:
        payload.append({
            "id": emp.id,
            "name": getattr(emp, "full_name", None) or getattr(emp, "name", None) or str(emp),
            "email": getattr(emp, "email", None),
            "phone": getattr(emp, "mobile_number", None) or getattr(emp, "phone", None),
            "avatar": getattr(emp, "photo_url", None) or getattr(emp, "avatar", None),
        })

    return JsonResponse({
        "status": "ok",
        "employees": payload,
    })