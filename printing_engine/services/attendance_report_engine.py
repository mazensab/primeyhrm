# ============================================================
# 📂 AttendanceReportPrintEngine — V1 Ultra Pro
# 🧾 محرك طباعة تقارير الحضور
# ------------------------------------------------------------
# ✔ مبني على BasePrintEngine
# ✔ يدعم QR Code
# ✔ يدعم تقرير شهر كامل أو فترة مخصصة
# ✔ يستخدم قوالب system (Glass UI PDF)
# ============================================================

from .base_engine import BasePrintEngine
from django.utils import timezone


class AttendanceReportPrintEngine(BasePrintEngine):
    """
    🧠 محرك طباعة تقارير الحضور
    - payroll_center : يستخدم الحضور كعامل دعم للرواتب
    - attendance_center : طباعة تقارير مفصلة للموظف / الشركة
    """

    def __init__(self, company, records, mode="monthly", period=None):
        """
        ⬅ parameters:
            company : شركة التقرير
            records : قائمة الحضور AttendanceRecord queryset
            mode    : monthly / range / employee
            period  : dict(start=, end=) إذا كان التقرير Range
        """

        self.company = company
        self.records = records
        self.mode = mode
        self.period = period  # dict(start, end)

        # ---------- إعداد نص QR ----------
        if mode == "monthly":
            title = f"Monthly Attendance Report — {timezone.now().strftime('%Y-%m')}"
        elif mode == "range":
            title = f"Attendance Report — {period['start']} → {period['end']}"
        else:
            title = "Attendance Report"

        qr_text = (
            f"{title}\n"
            f"Company: {company.name}\n"
            f"Records: {records.count()}\n"
            f"Primey HR Cloud"
        )

        qr_base64 = BasePrintEngine.generate_qr(qr_text)

        # ---------- السياق النهائي ----------
        context = {
            "company": company,
            "records": records,
            "mode": mode,
            "period": period,
            "qr_image_base64": qr_base64,
            "generated_at": timezone.now(),
        }

        super().__init__("attendance_center/attendance_report_pdf.html", context)
