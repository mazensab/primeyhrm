# 📂 الملف: smart_assistant/urls.py
# 🤖 نظام توجيه روابط المساعد الذكي — Primey HR Cloud V11.0
# 🚀 تكامل شامل مع Control Center + Analytics Engine + WebSocket + Notification Center
# ============================================================
# ✅ لوحة المساعد الزجاجية (Dashboard)
# ✅ واجهة المحادثة التفاعلية (Panel)
# ✅ توليد التحليل الذكي (AI Insight Generation)
# ✅ تحديث التوصيات (Refresh Recommendations)
# ✅ تحليل الاستفسارات النصية (Smart Query)
# ✅ اختبار البث الحي (WebSocket Live API)
# ✅ الاقتراحات التحليلية الجاهزة (Smart Suggestions)
# ============================================================

from django.urls import path
from django.http import HttpResponseRedirect
from . import views

app_name = "smart_assistant"

urlpatterns = [
    # 🏠 0️⃣ إعادة توجيه تلقائية للوحة المساعد
    path("", lambda request: HttpResponseRedirect("/smart-assistant/dashboard/"), name="assistant_root"),

    # 🧭 1️⃣ لوحة التحكم الزجاجية للمساعد الذكي
    path("dashboard/", views.assistant_dashboard, name="assistant_dashboard"),

    # 💬 2️⃣ واجهة المساعد التفاعلية (Panel)
    path("panel/", views.assistant_panel, name="assistant_panel"),

    # ⚡ 3️⃣ API — توليد تحليل ذكي جديد
    path("api/generate/", views.api_generate_ai_insight, name="api_generate_ai_insight"),

    # 🔁 4️⃣ API — تحديث التوصيات الذكية
    path("api/refresh/", views.api_refresh_recommendations, name="api_refresh_recommendations"),

    # 💡 5️⃣ API — الاقتراحات الجاهزة (Smart Suggestions)
    path("api/suggestions/", views.assistant_api, name="assistant_api"),

    # 🧠 6️⃣ API — تحليل استفسارات المستخدم (Smart Query)
    path("api/query/", views.assistant_query_api, name="assistant_query_api"),

    # 🌐 7️⃣ API — اختبار اتصال WebSocket (Live Readiness)
    path("api/live/", views.assistant_live_api, name="assistant_live_api"),
]
