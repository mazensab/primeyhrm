# 📂 smart_assistant/services.py — V11.1 Fixed
# 🔧 متوافق مع الهيكل الجديد بدون Billing Invoices

import logging
from django.utils import timezone
from company_manager.models import Company
from analytics_engine.models import Report

logger = logging.getLogger(__name__)

# ============================================================
# 🧠 1️⃣ Smart Assistant Core
# ============================================================
class SmartAssistantCore:

    def __init__(self, user):
        self.user = user

    def generate_insight(self):
        """تحليل ذكي بسيط بناءً على البيانات المتوفرة حالياً"""
        now = timezone.now()
        result = []

        try:
            # 🏢 الشركات الجديدة خلال 30 يوم
            new_companies = Company.objects.filter(
                created_at__gte=now - timezone.timedelta(days=30)
            ).count()
            if new_companies:
                result.append(f"🏢 تم تسجيل {new_companies} شركة جديدة خلال آخر 30 يومًا.")

            # 📊 تقارير Analytics
            pending_reports = Report.objects.filter(status="PENDING").count()
            if pending_reports:
                result.append(f"📄 يوجد {pending_reports} تقرير تحليلي قيد المراجعة.")

            if not result:
                result.append("✅ النظام يعمل بكفاءة ولا توجد مهام عاجلة.")

            return {
                "title": "تحليل دوري للنظام",
                "recommendation": "\n".join(result),
                "confidence": 0.95,
            }

        except Exception as e:
            logger.exception(e)
            return {
                "title": "خطأ",
                "recommendation": "⚠️ حدث خطأ أثناء جلب البيانات.",
                "confidence": 0.0,
            }


# ============================================================
# 🤖 2️⃣ Smart Query Engine
# ============================================================
class SmartQueryEngine:

    def __init__(self, user):
        self.user = user

    def analyze(self, query: str) -> str:
        if not query:
            return "❌ الرجاء إدخال استفسار واضح."

        query = query.strip().lower()
        now = timezone.now()

        try:
            # 🏢 الشركات الجديدة
            if "شركة" in query:
                count = Company.objects.filter(
                    created_at__gte=now - timezone.timedelta(days=30)
                ).count()
                return f"🏢 تم تسجيل {count} شركة جديدة خلال آخر 30 يومًا."

            # 📊 التقارير
            if "تقرير" in query or "تحليل" in query:
                total = Report.objects.count()
                pending = Report.objects.filter(status="PENDING").count()
                return f"📄 يوجد {pending} تقرير قيد المراجعة من أصل {total} تقرير."

            # ⏰ الوقت والتاريخ
            if "الوقت" in query or "الساعة" in query:
                return f"🕒 الآن {now.strftime('%A %d %B %Y - %H:%M')}"

            return "🤖 لم أفهم استفسارك، حاول سؤال: كم عدد الشركات الجديدة؟"

        except Exception:
            return "⚠️ حدث خطأ أثناء تحليل الاستفسار."
