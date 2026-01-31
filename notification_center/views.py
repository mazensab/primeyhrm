from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from .models import Notification


# ============================================================
# 📄 صفحة عرض جميع الإشعارات (مقروء + غير مقروء)
# ============================================================
@login_required
def notification_list(request):
    unread = Notification.objects.filter(recipient=request.user, is_read=False)
    read = Notification.objects.filter(recipient=request.user, is_read=True)

    return render(request, "notification_center/notification_list.html", {
        "unread": unread,
        "read": read,
    })


# ============================================================
# 🔔 تعليم إشعار واحد كمقروء
# ============================================================
@login_required
def mark_as_read(request, notification_id):

    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)

    if not notification.is_read:
        notification.mark_as_read()

    if notification.link:
        return redirect(notification.link)

    return redirect("notification_center:notification_list")


# ============================================================
# 🔔 تعليم جميع الإشعارات كمقروء
# ============================================================
@login_required
def mark_all_as_read(request):

    qs = Notification.objects.filter(recipient=request.user, is_read=False)
    for n in qs:
        n.mark_as_read()

    return redirect("notification_center:notification_list")


# ============================================================
# 🔄 إعادة تحميل قائمة Dropdown (غير المقروء فقط)
# ============================================================
@login_required
def dropdown_notifications(request):

    unread = Notification.objects.filter(recipient=request.user, is_read=False).order_by("-created_at")

    return render(request, "notification_center/notifications_dropdown.html", {
        "unread": unread
    })
