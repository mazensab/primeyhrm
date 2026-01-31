# 📂 الملف: notification_center/urls.py
# 🧭 نظام توجيه روابط مركز الإشعارات الذكي (Notification Center V5.6)
# 🚀 متكامل مع واجهات API + WebSocket + Smart Assistant
# ===============================================================
# ✅ لوحة عرض الإشعارات (Dashboard)
# ✅ واجهات API: (Unread + Create + Mark Single + Mark All)
# ✅ جاهز لتكامل البث الفوري (WebSocket Consumer)
# ===============================================================
from django.urls import path
from . import views

app_name = "notification_center"

urlpatterns = [

    # صفحة عرض الإشعارات
    path("", views.notification_list, name="notification_list"),

    # تعليم إشعار واحد كمقروء
    path("read/<int:notification_id>/", views.mark_as_read, name="mark_as_read"),

    # تعليم كل الإشعارات كمقروء
    path("read-all/", views.mark_all_as_read, name="mark_all_as_read"),

    # إعادة تحميل قائمة الإشعارات غير المقروءة (للـ Dropdown)
    path("dropdown/", views.dropdown_notifications, name="dropdown_notifications"),
]
