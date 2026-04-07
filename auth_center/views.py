# ================================================================
# 📂 auth_center/views.py
# 🧭 Authentication & Identity — Mham Cloud V15.1 ULTRA STABLE
# ================================================================

import json
import logging

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from company_manager.models import CompanyUser
from billing_center.models import CompanySubscription

logger = logging.getLogger(__name__)
User = get_user_model()

# ================================================================
# 🧭 1) Login View (HTML ONLY — Admin / Legacy UI)
# ================================================================
def login_view(request):
    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()
        password = request.POST.get("password")

        if not identifier or not password:
            messages.error(request, "يرجى إدخال اسم المستخدم وكلمة المرور.")
            return redirect("auth_center:login")

        try:
            if "@" in identifier:
                user = User.objects.get(email__iexact=identifier)
            else:
                user = User.objects.get(username__iexact=identifier)
        except User.DoesNotExist:
            messages.error(request, "بيانات الدخول غير صحيحة.")
            return redirect("auth_center:login")

        auth_user = authenticate(
            request,
            username=user.username,
            password=password,
        )

        if not auth_user:
            messages.error(request, "كلمة المرور غير صحيحة.")
            return redirect("auth_center:login")

        login(request, auth_user)

        company_link = (
            CompanyUser.objects
            .filter(user=auth_user, is_active=True)
            .first()
        )

        if auth_user.is_superuser:
            return redirect("control_center:dashboard_system_owner")

        if company_link and company_link.role == "admin":
            return redirect("control_center:company_dashboard")

        if company_link and company_link.role == "hr":
            return redirect("control_center:company_hr_dashboard")

        return redirect("control_center:employee_dashboard")

    return render(request, "auth_center/login.html")


# ================================================================
# 🔐 2) Login API — Session Based (Next.js — NO REDIRECT)
# ================================================================
@csrf_exempt  # ✔ مقصود — Session Auth مع CSRF عبر Header
def login_api(request):
    """
    POST → Login (Session)
    GET  → Check authenticated
    """

    if request.method == "GET":
        return JsonResponse(
            {"authenticated": request.user.is_authenticated},
            status=200
        )

    if request.method != "POST":
        return JsonResponse(
            {"error": "METHOD_NOT_ALLOWED"},
            status=405
        )

    try:
        payload = json.loads(request.body or "{}")
        username = (payload.get("username") or "").strip()
        password = payload.get("password")

        if not username or not password:
            return JsonResponse(
                {"error": "MISSING_CREDENTIALS"},
                status=400
            )

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if not user:
            return JsonResponse(
                {"error": "INVALID_CREDENTIALS"},
                status=401
            )

        login(request, user)

        return JsonResponse(
            {
                "authenticated": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_superuser": user.is_superuser,
                },
            },
            status=200
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "INVALID_JSON"},
            status=400
        )

    except Exception as e:
        logger.exception("Login API failed")
        return JsonResponse(
            {
                "error": "LOGIN_FAILED",
                "details": str(e),
            },
            status=500
        )


# ================================================================
# 👤 3) WhoAmI API — JSON ONLY (NO REDIRECT EVER)
# ================================================================
def whoami_api(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"authenticated": False},
            status=401
        )

    user = request.user

    company_link = (
        CompanyUser.objects
        .filter(user=user)
        .select_related("company")
        .first()
    )

    subscription_payload = None

    if company_link and company_link.company:
        subscription = (
            CompanySubscription.objects
            .filter(company=company_link.company)
            .order_by("-end_date")
            .first()
        )

        if subscription:
            subscription_payload = {
                "status": subscription.status,
                "end_date": subscription.end_date,
                "mode": (
                    "read_only"
                    if subscription.end_date
                    and subscription.end_date < now().date()
                    else "full"
                ),
            }

    return JsonResponse(
        {
            "authenticated": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_superuser": user.is_superuser,
            },
            "company": (
                {
                    "id": company_link.company.id,
                    "name": company_link.company.name,
                    "role": company_link.role,
                }
                if company_link else None
            ),
            "subscription": subscription_payload,
        },
        status=200
    )


# ================================================================
# 🚪 4) Logout (Session Safe)
# ================================================================
@login_required
def logout_view(request):
    logout(request)
    return redirect("auth_center:login")


# ================================================================
# 🔐 5) Forgot Password (HTML — Placeholder Safe)
# ================================================================
def forgot_password_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()

        if not email or not User.objects.filter(email__iexact=email).exists():
            messages.error(request, "البريد غير موجود في النظام.")
            return redirect("auth_center:forgot_password")

        # 🔒 لاحقًا: Email Token Flow
        messages.success(request, "تم إرسال رابط إعادة التعيين إلى بريدك.")
        return redirect("auth_center:login")

    return render(request, "auth_center/forgot_password.html")


# ================================================================
# 🔑 6) Change Password
# ================================================================
@login_required
def change_password_view(request):
    if request.method == "POST":
        p1 = request.POST.get("password1")
        p2 = request.POST.get("password2")

        if not p1 or p1 != p2:
            messages.error(request, "كلمتا المرور غير متطابقتين.")
            return redirect("auth_center:change_password")

        user = request.user
        user.set_password(p1)
        user.save()

        messages.success(
            request,
            "تم تغيير كلمة المرور بنجاح. يرجى تسجيل الدخول مجددًا."
        )
        return redirect("auth_center:login")

    return render(request, "auth_center/change_password.html")


# ================================================================
# 👤 7) Profile
# ================================================================
@login_required
def profile_view(request):
    return render(request, "auth_center/profile.html")


# ================================================================
# ✏️ 8) Edit Profile
# ================================================================
@login_required
def profile_edit_view(request):
    user = request.user

    if request.method == "POST":
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.email = request.POST.get("email", "").strip()

        if "avatar" in request.FILES:
            avatar_file = request.FILES["avatar"]
            path = default_storage.save(
                f"avatars/{user.id}.png",
                avatar_file
            )
            user.avatar = path

        user.save()
        messages.success(request, "تم تحديث الملف الشخصي بنجاح.")
        return redirect("auth_center:profile")

    return render(request, "auth_center/profile_edit.html")
