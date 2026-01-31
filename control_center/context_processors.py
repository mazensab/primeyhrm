# 📦 control_center/context_processors.py
# 🧭 Primey HR Cloud 2026 — Global Context Provider (V2)
# 💡 يمرّر معلومات المستخدم والشركة والإشعارات لجميع القوالب ديناميكيًا

from company_manager.models import Company
from notification_center.models import Notification

def global_context(request):
    company = None
    notifications = []
    current_user = None

    if request.user.is_authenticated:
        current_user = request.user

        # ✅ البحث الصحيح عبر الحقل created_by بدل owner
        company = Company.objects.filter(created_by=current_user).first()

        # 🔔 جلب آخر 10 إشعارات للمستخدم الحالي
        notifications = (
            Notification.objects.filter(recipient=current_user)
            .order_by("-created_at")[:10]
        )

    return {
        "company": company,
        "notifications": notifications,
        "current_user": current_user,
    }
