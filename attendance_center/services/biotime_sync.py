# 📂 الملف: attendance_center/services/biotime_sync.py
# 🧭 وحدة المزامنة مع نظام Biotime API
# 🚀 الإصدار V3.70 — تكامل آمن + معالجة ذكية + إدارة أخطاء احترافية

import requests
from datetime import datetime
from django.db import transaction
from django.conf import settings
from attendance_center.models import AttendanceRecord
from employee_center.models import Employee

# ===========================================================
# ⚙️ الإعدادات الافتراضية للاتصال (يمكن تعديلها من Settings Center لاحقًا)
# ===========================================================
BIOTIME_API_BASE = getattr(settings, "BIOTIME_API_BASE", "https://biotime.example.com/api/")
BIOTIME_TOKEN = getattr(settings, "BIOTIME_TOKEN", None)
BIOTIME_TIMEOUT = getattr(settings, "BIOTIME_TIMEOUT", 20)  # ⏱️ أقصى وقت للانتظار بالثواني

# ===========================================================
# 🔒 دالة رئيسية لجلب السجلات من Biotime
# ===========================================================
def fetch_biotime_attendance_records():
    """
    📡 الاتصال بنظام Biotime API وجلب السجلات اليومية
    - الاتصال يتم عبر HTTPS
    - يعتمد على رمز مصادقة (Bearer Token)
    - يعيد قائمة من السجلات الجاهزة للحفظ
    """
    if not BIOTIME_TOKEN:
        raise ConnectionError("⚠️ لم يتم إعداد مفتاح API Token الخاص بـ Biotime في الإعدادات.")

    url = f"{BIOTIME_API_BASE.rstrip('/')}/attendance/records"
    headers = {
        "Authorization": f"Bearer {BIOTIME_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=BIOTIME_TIMEOUT, verify=True)
        response.raise_for_status()  # 🔒 تحقق من أن الاتصال ناجح (رمز 200)
        data = response.json()

        # ✅ التحقق من تنسيق البيانات
        if not isinstance(data, list):
            raise ValueError("❌ تنسيق بيانات Biotime غير متوقع (يجب أن تكون قائمة JSON).")

        records = []
        for rec in data:
            # مثال على هيكل السجل المتوقع من Biotime
            # {
            #   "emp_code": "EMP001",
            #   "date": "2025-11-02",
            #   "check_in": "08:31:00",
            #   "check_out": "17:02:00",
            #   "status": "present"
            # }

            emp_code = rec.get("emp_code")
            date_str = rec.get("date")

            if not emp_code or not date_str:
                continue  # ⛔ تجاهل السجلات الناقصة

            records.append({
                "emp_code": emp_code,
                "date": datetime.strptime(date_str, "%Y-%m-%d").date(),
                "check_in": rec.get("check_in"),
                "check_out": rec.get("check_out"),
                "status": rec.get("status", "present"),
            })

        return records

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"❌ فشل الاتصال بخادم Biotime: {str(e)}")
    except ValueError as e:
        raise ValueError(f"⚠️ خطأ في تحليل البيانات: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"🚨 خطأ غير متوقع أثناء المزامنة: {str(e)}")


# ===========================================================
# 💾 دالة لحفظ السجلات في قاعدة البيانات
# ===========================================================
@transaction.atomic
def sync_attendance_to_db(records):
    """
    💾 حفظ السجلات المستوردة في قاعدة البيانات
    - يمنع التكرار
    - يسجّل السجلات الجديدة فقط
    """
    added_count = 0

    for rec in records:
        try:
            emp_code = rec.get("emp_code")
            employee = Employee.objects.filter(code=emp_code).first()
            if not employee:
                continue  # ⛔ تجاهل الموظفين غير المسجلين

            _, created = AttendanceRecord.objects.get_or_create(
                employee=employee,
                date=rec["date"],
                defaults={
                    "check_in": rec.get("check_in"),
                    "check_out": rec.get("check_out"),
                    "status": rec.get("status", "present"),
                    "synced_from_biotime": True,
                },
            )

            if created:
                added_count += 1

        except Exception as e:
            print(f"⚠️ فشل في حفظ سجل لموظف {rec.get('emp_code')}: {str(e)}")
            continue

    return added_count


# ===========================================================
# 🔄 دالة تنفيذ المزامنة الكاملة
# ===========================================================
def run_biotime_sync():
    """
    🔁 تنفيذ دورة المزامنة الكاملة:
    1️⃣ جلب البيانات من Biotime
    2️⃣ حفظها في قاعدة البيانات
    3️⃣ إعادة عدد السجلات الجديدة التي تمت إضافتها
    """
    records = fetch_biotime_attendance_records()
    added = sync_attendance_to_db(records)
    return added
