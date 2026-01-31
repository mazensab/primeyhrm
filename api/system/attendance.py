# ============================================================
# 🖥️ System Attendance APIs — FINAL
# Primey HR Cloud
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required

from attendance_center.models import AttendanceRecord
from attendance_center.scheduler import scheduler


# ============================================================
# 📊 System Overview
# ============================================================

@staff_member_required
@require_http_methods(["GET"])
def system_attendance_overview(request):
    data = {
        "total_records": AttendanceRecord.objects.count(),
        "today": AttendanceRecord.objects.filter(
            date=AttendanceRecord.today()
        ).count(),
        "from_biotime": AttendanceRecord.objects.filter(
            synced_from_biotime=True
        ).count(),
    }

    return JsonResponse({"status": "success", "data": data})


# ============================================================
# ⏸️ Scheduler Pause
# ============================================================

@staff_member_required
@require_http_methods(["POST"])
def pause_attendance_scheduler(request):
    scheduler.pause()
    return JsonResponse({"status": "paused"})


# ============================================================
# ▶️ Scheduler Resume
# ============================================================

@staff_member_required
@require_http_methods(["POST"])
def resume_attendance_scheduler(request):
    scheduler.resume()
    return JsonResponse({"status": "running"})
