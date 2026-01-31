# ============================================================
# 📂 الملف: biotime_center/tests/test_biotime_sync.py
# 🧪 اختبار تكامل سجلات Biotime مع Attendance Center
# 🚀 الإصدار V1.0 الرسمي — Developed by Mazen 2025
# ============================================================

from django.utils import timezone
from biotime_center.models import BiotimeLog
from employee_center.models import Employee
from attendance_center.models import AttendanceRecord

def run_biotime_to_attendance_test(start_date=None, end_date=None):
    """
    🧠 اختبار عملي لربط السجلات بين Biotime و Attendance Center
    ✅ يقوم بمحاكاة تنفيذ api_jwt_sync_to_attendance ولكن من الـ shell مباشرة
    """
    print("🚀 بدء الاختبار اليدوي لتكامل Biotime → Attendance Center")

    start_date = start_date or timezone.now().date()
    end_date = end_date or timezone.now().date()

    # 🕒 جلب السجلات من BiotimeLog
    logs = BiotimeLog.objects.filter(
        punch_time__date__range=[start_date, end_date]
    ).select_related("employee")

    if not logs.exists():
        print(f"⚠️ لا توجد سجلات Biotime بين {start_date} و {end_date}")
        return

    total = logs.count()
    synced = 0
    skipped = 0

    for log in logs:
        try:
            emp = Employee.objects.filter(biotime_code=log.employee.employee_id).first()
            if not emp:
                skipped += 1
                print(f"⚠️ لم يتم العثور على موظف مطابق لـ {log.employee.full_name}")
                continue

            record, created = AttendanceRecord.objects.update_or_create(
                employee=emp,
                date=log.punch_time.date(),
                defaults={
                    "synced_from_biotime": True,
                    "check_in": log.punch_time.time()
                    if log.event_type == "check_in" else None,
                    "check_out": log.punch_time.time()
                    if log.event_type == "check_out" else None,
                },
            )
            synced += 1
            print(f"✅ تمت مزامنة: {emp} — {log.event_type} ({log.punch_time})")

        except Exception as e:
            print(f"❌ خطأ أثناء معالجة {log.id}: {e}")

    print("--------------------------------------------------------")
    print(f"📦 إجمالي السجلات: {total}")
    print(f"✅ تمت المزامنة: {synced}")
    print(f"⚠️ تم تخطي: {skipped}")
    print(f"🕒 الفترة: {start_date} → {end_date}")
    print("--------------------------------------------------------")
    print("🏁 تم إكمال الاختبار بنجاح.")
