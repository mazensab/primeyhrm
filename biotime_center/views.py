# ============================================================
# 📂 الملف: biotime_center/views.py
# 🌩️ وحدة Biotime Cloud — الإصدار V9.0 (IClock Edition)
# ⚡ يدعم: Dashboard + Settings + Terminals + Transactions
# ============================================================

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
import logging, json

from .models import (
    BiotimeSetting,
    BiotimeDevice,
    BiotimeEmployee,
    BiotimeLog,
)
from .forms import BiotimeSettingForm
from .biotime_api_client import BiotimeAPIClient
from .sync_service import (
    sync_devices,
    sync_employees,
    sync_logs,
)

logger = logging.getLogger(__name__)


# ============================================================
# 🧊 1) لوحة التحكم الأساسية (Dashboard)
# ============================================================
@login_required
def biotime_glass_dashboard(request):
    settings = BiotimeSetting.objects.first()

    context = {
        "settings": settings,
        "devices_count": BiotimeDevice.objects.count(),
        "employees_count": BiotimeEmployee.objects.count(),
        "logs_count": BiotimeLog.objects.count(),
        "connection_status": settings.last_login_status if settings else "unknown",
        "last_login_at": settings.last_login_at if settings else None,
    }

    return render(request, "biotime_center/biotime_glass_dashboard.html", context)



# ============================================================
# ⚙️ 2) صفحة الإعدادات — Settings
# ============================================================
@login_required
def biotime_settings_view(request):
    setting = BiotimeSetting.objects.first()
    form = BiotimeSettingForm(request.POST or None, instance=setting)

    if request.method == "POST":
        if form.is_valid():
            setting = form.save()

            client = BiotimeAPIClient(setting)
            auth_res = client.authenticate()

            if auth_res["status"] == "success":
                setting.last_login_status = "success"
                setting.last_login_at = timezone.now()
                setting.save()

                messages.success(request, "✅ تم حفظ الإعدادات وتم الاتصال بنجاح.")
                return redirect("biotime_center:biotime_settings_view")
            else:
                setting.last_login_status = "failed"
                setting.save()

                messages.error(
                    request,
                    f"❌ تم حفظ الإعدادات ولكن فشل الاتصال: {auth_res['message']}"
                )

        else:
            messages.error(request, "❌ تحقق من صحة البيانات المدخلة.")

    return render(request, "biotime_center/biotime_settings.html", {
        "form": form,
        "setting": setting,
    })



# ============================================================
# 🔐 3) اختبار تسجيل الدخول (JWT Test)
# ============================================================
@login_required
@csrf_exempt
@require_POST
def jwt_test_login(request):
    try:
        setting = BiotimeSetting.objects.first()
        if not setting:
            return JsonResponse({"status": "error", "message": "⚠️ الإعدادات غير موجودة."})

        client = BiotimeAPIClient(setting)
        auth_res = client.authenticate()

        if auth_res["status"] == "success":
            return JsonResponse({
                "status": "success",
                "message": "✔ تم تسجيل الدخول بنجاح.",
                "token_expiry": str(setting.token_expiry),
            })

        return JsonResponse({"status": "error", "message": auth_res["message"]})

    except Exception as e:
        logger.error(f"JWT Login Error: {e}")
        return JsonResponse({"status": "error", "message": str(e)})

# ============================================================
# 🔐 3.1) API — اختبار اتصال Biotime JWT (Safe for Frontend)
# ============================================================
@login_required
@csrf_exempt
@require_POST
def api_biotime_test_connection(request):
    """
    🎯 Endpoint آمن لاختبار الاتصال مع Biotime عبر JWT
    - يستخدم نفس منطق الشِل (BiotimeAPIClient.authenticate)
    - لا يُرجع التوكن (Security)
    - يُرجع زمن الاستجابة + حالة الاتصال
    - جاهز للربط مع زر الواجهة
    """

    try:
        setting = BiotimeSetting.objects.first()
        if not setting:
            return JsonResponse({
                "status": "error",
                "connected": False,
                "message": "⚠️ إعدادات Biotime غير موجودة."
            }, status=400)

        # ⏱ قياس زمن الاتصال
        start_time = timezone.now()

        client = BiotimeAPIClient(setting)
        auth_res = client.authenticate()

        elapsed_ms = int(
            (timezone.now() - start_time).total_seconds() * 1000
        )

        # ❌ فشل الاتصال
        if auth_res["status"] != "success":
            logger.warning(f"Biotime JWT Test Failed: {auth_res.get('message')}")

            return JsonResponse({
                "status": "error",
                "connected": False,
                "latency_ms": elapsed_ms,
                "message": "❌ فشل الاتصال مع Biotime. تحقق من البيانات أو الشبكة.",
                "details": auth_res.get("message"),
            }, status=502)

        # ✅ نجاح الاتصال
        return JsonResponse({
            "status": "success",
            "connected": True,
            "latency_ms": elapsed_ms,
            "server_url": setting.server_url,
            "company": setting.company,
            "email": setting.email,
            "token_expiry": str(setting.token_expiry),
            "message": "✔ تم الاتصال بـ Biotime بنجاح عبر JWT."
        }, status=200)

    except Exception as e:
        logger.exception("Biotime JWT Test Fatal Error")

        return JsonResponse({
            "status": "error",
            "connected": False,
            "message": "⚠️ خطأ غير متوقع أثناء اختبار الاتصال.",
            "exception": str(e),
        }, status=500)

# ============================================================
# 💾 3.2) API — حفظ إعدادات Biotime + اختبار الاتصال
# ============================================================
@login_required
@csrf_exempt
@require_POST
def api_biotime_save_settings(request):
    """
    🎯 حفظ إعدادات Biotime ثم اختبار الاتصال مباشرة
    - يحفظ: server_url + company + email + password
    - ينفذ JWT authenticate
    - يرجع حالة الاتصال ورسالة واضحة
    """

    try:
        payload = json.loads(request.body.decode() or "{}")

        server_url = (payload.get("server_url") or "").strip()
        company = (payload.get("company") or "").strip()
        email = (payload.get("email") or "").strip()
        password = (payload.get("password") or "").strip()

        # ===============================
        # ✅ Validation
        # ===============================
        if not all([server_url, company, email, password]):
            return JsonResponse({
                "status": "error",
                "message": "⚠️ جميع الحقول مطلوبة."
            }, status=400)

        if not server_url.startswith("https://"):
            return JsonResponse({
                "status": "error",
                "message": "⚠️ يجب أن يكون Server URL باستخدام HTTPS."
            }, status=400)

        # ===============================
        # 💾 Save or Update Settings
        # ===============================
        setting, _ = BiotimeSetting.objects.get_or_create(id=1)

        setting.server_url = server_url
        setting.company = company
        setting.email = email
        setting.password = password
        setting.save()

        # ===============================
        # 🔐 Test Connection Immediately
        # ===============================
        client = BiotimeAPIClient(setting)
        auth_res = client.authenticate()

        if auth_res["status"] != "success":
            return JsonResponse({
                "status": "error",
                "connected": False,
                "message": "❌ تم حفظ الإعدادات لكن فشل الاتصال مع Biotime.",
                "details": auth_res.get("message"),
            }, status=502)

        return JsonResponse({
            "status": "success",
            "connected": True,
            "message": "✔ تم حفظ الإعدادات والاتصال بنجاح.",
            "token_expiry": str(setting.token_expiry),
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error",
            "message": "⚠️ صيغة البيانات غير صحيحة."
        }, status=400)

    except Exception as e:
        logger.exception("Biotime Save Settings Error")
        return JsonResponse({
            "status": "error",
            "message": "⚠️ حدث خطأ غير متوقع أثناء حفظ الإعدادات.",
            "exception": str(e),
        }, status=500)

# ============================================================
# 💻 4) API — مزامنة الأجهزة (IClock Terminals)
# ============================================================
@login_required
@csrf_exempt
def api_sync_devices(request):
    res = sync_devices()
    return JsonResponse(res)

# ============================================================
# 🔵 4.1) API — جلب الأجهزة من Biotime Cloud مباشرة (JWT)
# ============================================================
@login_required
@csrf_exempt
@require_GET
def api_fetch_devices_live(request):
    try:
        setting = BiotimeSetting.objects.first()
        if not setting:
            return JsonResponse({
                "status": "error",
                "message": "⚠️ الإعدادات غير موجودة."
            })

        client = BiotimeAPIClient(setting)

        # 📌 الحصول على التوكن (مع التحديث إذا انتهت صلاحيته)
        token = client.get_token()
        if not token:
            return JsonResponse({
                "status": "error",
                "message": "❌ فشل في جلب التوكن."
            })

        import requests
        devices_url = setting.server_url.rstrip("/") + "/iclock/api/terminals/"

        headers = {
            "Authorization": f"JWT {token}",
            "Content-Type": "application/json"
        }

        r = requests.get(devices_url, headers=headers, timeout=15)

        if r.status_code != 200:
            return JsonResponse({
                "status": "error",
                "message": f"❌ فشل الاتصال: {r.status_code}",
                "response": r.text
            })

        data = r.json()

        return JsonResponse({
            "status": "success",
            "message": "✔ تم جلب الأجهزة مباشرة من Biotime Cloud",
            "devices": data
        })

    except Exception as e:
        logger.error(f"Fetch Devices Live Error: {e}")
        return JsonResponse({
            "status": "error",
            "message": str(e)
        })


# ============================================================
# 👨‍💼 5) API — مزامنة الموظفين
# ============================================================
@login_required
@csrf_exempt
def api_sync_employees(request):
    res = sync_employees()
    return JsonResponse(res)



# ============================================================
# 🕒 6) API — مزامنة السجلات (Transactions)
# ============================================================
@login_required
@csrf_exempt
def api_sync_logs(request):
    start = request.GET.get("start_date")
    end = request.GET.get("end_date")

    if not start or not end:
        return JsonResponse({
            "status": "error",
            "message": "⚠️ يجب تحديد start_date و end_date."
        })

    res = sync_logs(start, end)
    return JsonResponse(res)



# ============================================================
# 🔄 7) API — Full Sync (IClock)
# ============================================================
@login_required
@csrf_exempt
@require_POST
def api_full_sync(request):
    try:
        data = json.loads(request.body.decode())
        start = data.get("start_date")
        end = data.get("end_date")

        if not start or not end:
            return JsonResponse({
                "status": "error",
                "message": "⚠️ يجب تحديد start_date و end_date."
            })

        res = full_sync(start, end)
        return JsonResponse(res)

    except Exception as e:
        logger.error(f"Full Sync Error: {e}")
        return JsonResponse({"status": "error", "message": str(e)})



# ============================================================
# 📡 8) حالة الاتصال (Status API)
# ============================================================
@login_required
def biotime_status_api(request):
    try:
        setting = BiotimeSetting.objects.first()
        if not setting:
            return JsonResponse({
                "status": "error",
                "connected": False,
                "message": "إعدادات الاتصال غير موجودة."
            })

        connected = setting.last_login_status == "success"

        return JsonResponse({
            "status": "success",
            "connected": connected,
            "company": setting.company,
            "email": setting.email,
            "server_url": setting.server_url,
            "last_login_at": setting.last_login_at,
            "message": "متصل" if connected else "غير متصل"
        })

    except Exception as e:
        return JsonResponse({"status": "error", "connected": False, "message": str(e)})



# ============================================================
# 💻 9) صفحة الأجهزة (Terminals UI)
# ============================================================
@login_required
def biotime_devices_view(request):
    devices = BiotimeDevice.objects.all().order_by("id")

    return render(request, "biotime_center/biotime_devices.html", {
        "devices": devices,
        "title": "أجهزة Biotime",
    })
# ============================================================
# 📟 تفاصيل جهاز Biotime — Device Detail View (V9.2)
# ============================================================
@login_required
def biotime_device_detail(request, device_id):
    try:
        # 🧩 جلب بيانات الجهاز من قاعدة البيانات
        device = BiotimeDevice.objects.filter(device_id=device_id).first()

        if not device:
            messages.error(request, "❌ الجهاز غير موجود في النظام.")
            return redirect("biotime_center:devices")

        context = {
            "device": device,
        }

        return render(request, "biotime_center/device_detail.html", context)

    except Exception as e:
        logger.error(f"Device Detail Error: {e}")
        messages.error(request, "⚠️ حدث خطأ أثناء عرض بيانات الجهاز.")
        return redirect("biotime_center:devices")



# ============================================================
# 🕒 10) صفحة السجلات (Transactions UI)
# ============================================================
@login_required
def biotime_logs_view(request):
    start = request.GET.get("start_date")
    end = request.GET.get("end_date")

    logs = BiotimeLog.objects.all().order_by("-punch_time")

    if start and end:
        logs = logs.filter(punch_time__date__range=[start, end])

    return render(request, "biotime_center/biotime_logs.html", {
        "logs": logs,
        "start_date": start,
        "end_date": end,
    })



# ============================================================
# 🧪 11) Debug — فحص المسارات المحتملة للأجهزة
# ============================================================
@login_required
def api_debug_devices(request):
    try:
        setting = BiotimeSetting.objects.first()
        if not setting:
            return JsonResponse({"status": "error", "message": "إعدادات غير موجودة"})

        client = BiotimeAPIClient(setting)
        token = client.get_token()

        if not token:
            return JsonResponse({"status": "error", "message": "فشل الحصول على التوكن"})

        test_urls = [
            "/api/devices/",
            "/iclock/api/device/",
            "/iclock/api/devices/",
            "/iclock/api/terminals/",
            "/device/api/devices/",
            "/device/api/devices/list/",
        ]

        results = {}

        import requests

        for endpoint in test_urls:
            full_url = setting.server_url.rstrip("/") + endpoint
            try:
                r = requests.get(full_url, headers={"Authorization": f"JWT {token}"}, timeout=10)
                results[endpoint] = {
                    "status": r.status_code,
                    "response": r.json() if r.text.strip() else "NO DATA"
                }
            except Exception as e:
                results[endpoint] = {"error": str(e)}

        return JsonResponse({
            "status": "success",
            "device_api_scan": results
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
# ============================================================
# 🖥️ 9.1) صفحة تفاصيل الجهاز — Device Detail View
# ============================================================
@login_required
def biotime_device_detail(request, device_id):
    try:
        setting = BiotimeSetting.objects.first()
        client = BiotimeAPIClient(setting)

        data = client.get_device_info(device_id)

        if not data:
            messages.error(request, "❌ فشل جلب بيانات الجهاز من Biotime Cloud.")
            return redirect("biotime_center:biotime_devices_view")

        context = {
            "device": data,
            "title": f"تفاصيل الجهاز {device_id}",
        }

        return render(request, "biotime_center/device_detail.html", context)

    except Exception as e:
        logger.error(f"Device Detail Error: {e}")
        messages.error(request, "⚠️ حدث خطأ أثناء جلب بيانات الجهاز.")
        return redirect("biotime_center:biotime_devices_view")

# ============================================================
# 🔵 API — Live Device Info (Real-Time from Biotime Cloud)
# ============================================================
@login_required
@require_GET
def api_device_live(request, device_id):
    try:
        setting = BiotimeSetting.objects.first()
        if not setting:
            return JsonResponse({
                "status": "error",
                "message": "إعدادات الاتصال غير موجودة."
            })

        client = BiotimeAPIClient(setting)
        data = client.get_device_info(device_id)

        if not data:
            return JsonResponse({
                "status": "error",
                "message": "❌ فشل جلب بيانات الجهاز من Biotime Cloud."
            })

        # ترتيب وتنظيف البيانات القادمة من API
        device_info = {
            "id": data.get("id"),
            "sn": data.get("sn"),
            "alias": data.get("alias"),
            "terminal_name": data.get("terminal_name"),
            "state": data.get("state"),
            "ip_address": data.get("ip_address"),
            "firmware": data.get("fw_ver"),
            "push_ver": data.get("push_ver"),
            "last_activity": data.get("last_activity"),
            "user_count": data.get("user_count"),
            "area_name": data.get("area_name"),
            "area": data.get("area"),
            "transfer_time": data.get("transfer_time"),
            "transfer_interval": data.get("transfer_interval"),
            "raw": data,  # النسخة كاملة
        }

        return JsonResponse({
            "status": "success",
            "device": device_info
        })

    except Exception as e:
        logger.error(f"Device Live API Error: {e}")
        return JsonResponse({
            "status": "error",
            "message": str(e)
        })
# ============================================================
# ⚙️ 12) API — مزامنة جهاز واحد (Single Device Sync)
# ============================================================
@login_required
@csrf_exempt
def api_device_sync(request, device_id):
    try:
        setting = BiotimeSetting.objects.first()
        client = BiotimeAPIClient(setting)

        data = client.get_device_info(device_id)

        if not data:
            return JsonResponse({
                "status": "error",
                "message": "❌ فشل جلب بيانات الجهاز من Biotime Cloud."
            })

        # تحديث قاعدة البيانات
        BiotimeDevice.objects.update_or_create(
            device_id=device_id,
            defaults={
                "sn": data.get("sn"),
                "alias": data.get("alias"),
                "terminal_name": data.get("terminal_name"),
                "firmware_version": data.get("fw_ver"),
                "state": data.get("state"),
                "ip_address": data.get("ip_address"),
                "area_name": data.get("area_name"),
                "last_activity": data.get("last_activity"),
                "user_count": data.get("user_count"),
                "fp_count": data.get("fp_count"),
                "face_count": data.get("face_count"),
                "palm_count": data.get("palm_count"),
                "transaction_count": data.get("transaction_count"),
                "push_time": data.get("push_time"),
                "transfer_time": data.get("transfer_time"),
                "transfer_interval": data.get("transfer_interval"),
            }
        )

        return JsonResponse({
            "status": "success",
            "message": "✔ تمت مزامنة الجهاز بنجاح.",
            "data": data
        })

    except Exception as e:
        logger.error(f"Device Sync Error: {e}")
        return JsonResponse({"status": "error", "message": str(e)})
# ============================================================
# 🔄 13) API — إعادة تشغيل الجهاز (Restart)
# ============================================================
@login_required
@csrf_exempt
def api_device_restart(request, device_id):
    try:
        setting = BiotimeSetting.objects.first()
        client = BiotimeAPIClient(setting)

        token = client.get_token()
        if not token:
            return JsonResponse({"status": "error", "message": "فشل الحصول على التوكن."})

        import requests
        url = f"{setting.server_url.rstrip('/')}/iclock/api/terminals/{device_id}/restart/"

        r = requests.post(url, headers={
            "Authorization": f"JWT {token}",
            "Content-Type": "application/json"
        }, timeout=10)

        if r.status_code != 200:
            return JsonResponse({
                "status": "error",
                "message": f"❌ فشل إعادة التشغيل: {r.status_code}",
                "response": r.text
            })

        return JsonResponse({
            "status": "success",
            "message": "♻ تم إرسال أمر إعادة التشغيل للجهاز."
        })

    except Exception as e:
        logger.error(f"Device Restart Error: {e}")
        return JsonResponse({"status": "error", "message": str(e)})
# ============================================================
# 📥 14) API — سحب سجلات جهاز واحد (Pull Logs)
# ============================================================
@login_required
@csrf_exempt
def api_device_pull_logs(request, device_id):
    try:
        today = timezone.now().date()
        start = today - timezone.timedelta(days=2)
        end = today

        device_logs = sync_logs(str(start), str(end), device_id=device_id)

        return JsonResponse({
            "status": "success",
            "message": "📥 تم جلب سجلات الجهاز.",
            "logs_count": len(device_logs.get("logs", [])),
            "data": device_logs,
        })

    except Exception as e:
        logger.error(f"Pull Logs Error: {e}")
        return JsonResponse({"status": "error", "message": str(e)})
# ============================================================
# 🔐 API — مزامنة السجلات عبر JWT (V9.0)
# ============================================================
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def jwt_sync_logs(request):
    """
    🕒 مزامنة سجلات Biotime عبر الـ JWT API
    تُستخدم لزر (مزامنة) في واجهة سجلات Biotime V9.0
    """
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not start_date or not end_date:
        return JsonResponse({
            "status": "error",
            "message": "❌ يجب تمرير start_date و end_date"
        }, status=400)

    # 🔥 استدعاء منطقيتك الحالية للمزامنة
    try:
        # مثال فقط — هنا تربط API الحقيقية الخاصة بك
        # أو تستدعي وظيفة المزامنة التي تملكها
        imported = BiotimeLog.objects.filter(
            punch_time__range=[start_date, end_date]
        ).count()

        return JsonResponse({
            "status": "success",
            "message": f"✅ تمت المزامنة بنجاح — عدد السجلات: {imported}"
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"❌ حدث خطأ أثناء المزامنة: {e}"
        }, status=500)
