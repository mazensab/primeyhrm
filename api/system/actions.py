from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.timezone import now

from company_manager.models import Company
from django.core.mail import send_mail


# ================================================================
# 🟦 Helper — Validate Input
# ================================================================
def get_param(request, name, default=None):
    return request.POST.get(name, default)


# ================================================================
# 🟩 1) Create New Company
# ================================================================
@require_POST
def create_company(request):
    """
    إنشاء شركة جديدة على مستوى النظام (Super Admin)
    البيانات المطلوبة:
        - name
        - owner_email (لاحقاً نربطه بإنشاء User)
        - subscription_plan
        - subscription_end
    """

    name = get_param(request, "name")
    plan = get_param(request, "subscription_plan", "basic")
    sub_end = get_param(request, "subscription_end")

    if not name:
        return JsonResponse({"error": "Company name is required"}, status=400)

    company = Company.objects.create(
        name=name,
        subscription_plan=plan,
        subscription_end=sub_end,
        is_active=True,
    )

    return JsonResponse({
        "status": "success",
        "message": "Company created successfully",
        "company_id": company.id
    }, status=201)


# ================================================================
# 🟨 2) Suspend / Activate Company
# ================================================================
@require_POST
def toggle_company_status(request):
    """
    تفعيل أو تعليق شركة:
        - company_id
        - action: suspend / activate
    """

    company_id = get_param(request, "company_id")
    action = get_param(request, "action")

    if not company_id or not action:
        return JsonResponse({"error": "company_id and action are required"}, status=400)

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)

    if action == "suspend":
        company.is_active = False
    elif action == "activate":
        company.is_active = True
    else:
        return JsonResponse({"error": "Invalid action"}, status=400)

    company.save()

    return JsonResponse({
        "status": "success",
        "message": f"Company {action}d successfully"
    }, status=200)


# ================================================================
# 🟧 3) Change Subscription Plan
# ================================================================
@require_POST
def change_plan(request):
    """
    تغيير خطة اشتراك شركة:
        - company_id
        - subscription_plan
    """

    company_id = get_param(request, "company_id")
    plan = get_param(request, "subscription_plan")

    if not company_id or not plan:
        return JsonResponse({"error": "company_id and subscription_plan are required"}, status=400)

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)

    company.subscription_plan = plan
    company.save()

    return JsonResponse({
        "status": "success",
        "message": "Subscription plan updated"
    }, status=200)


# ================================================================
# 🟪 4) Broadcast Message to All Companies
# ================================================================
@require_POST
def broadcast_message(request):
    """
    إرسال رسالة بريدية إلى جميع الشركات:
        - subject
        - message
    """

    subject = get_param(request, "subject")
    message = get_param(request, "message")

    if not subject or not message:
        return JsonResponse({"error": "subject and message are required"}, status=400)

    emails = Company.objects.exclude(owner_email=None).values_list("owner_email", flat=True)

    # Placeholder — Email backend must be configured
    for email in emails:
        try:
            send_mail(subject, message, "noreply@primey.cloud", [email])
        except:
            pass  # لن نكسر الـ API

    return JsonResponse({
        "status": "success",
        "message": "Broadcast message sent"
    }, status=200)
# ================================================================
# 🟦 5) Impersonate a Company (SUPER ADMIN ONLY)
# ================================================================
@require_POST
def impersonate_company(request):
    """
    🔥 يسمح لسوبر أدمن بالدخول إلى شركة كأنه مديرها.
    البيانات المطلوبة:
        - company_id
    """

    company_id = get_param(request, "company_id")

    if not company_id:
        return JsonResponse({"error": "company_id is required"}, status=400)

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)

    # إنشاء رمز جلسة جديد مع بيانات impersonation
    session_payload = {
        "role": "COMPANY_OWNER",         # الدور الظاهري
        "true_role": "SUPER_ADMIN",      # الدور الحقيقي
        "impersonate_company_id": str(company.id),
        "timestamp": str(now()),
    }

    # يتم ترميزها لاحقاً حسب نظام JWT لديك
    return JsonResponse({
        "status": "success",
        "message": f"Impersonating company {company.name}",
        "session": session_payload
    }, status=200)
