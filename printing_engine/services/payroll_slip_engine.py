# ============================================================
# 💰 PayrollSlipPrintEngine — V3 Ultra Pro
# ✔ يدعم 4 قوالب (standard / signature / thermal / legacy)
# ✔ QR يتضمن صافي الراتب والموظف والشهر
# ✔ يدعم xhtml2pdf + Tajawal Fonts
# ============================================================

from .base_engine import BasePrintEngine


class PayrollSlipPrintEngine(BasePrintEngine):
    """
    🧠 محرك طباعة إيصال الراتب — نسخة Ultra Pro 2025
    """

    TEMPLATE_MAP = {
        "standard": "payroll_center/payslip_v2.html",
        "signature": "payroll_center/payslip_v5_signature.html",
        "thermal": "payroll_center/payslip_thermal.html",
        "legacy": "payroll_center/payroll_payslip_pdf.html",
    }

    def __init__(self, payroll, company, mode="standard"):

        self.payroll = payroll
        self.company = company
        self.mode = mode if mode in self.TEMPLATE_MAP else "standard"

        template_path = self.TEMPLATE_MAP[self.mode]

        # QR 🔵
        qr_text = (
            f"Employee: {payroll.employee.full_name}\n"
            f"Month: {payroll.month.strftime('%Y-%m')}\n"
            f"Net Salary: {payroll.net_salary} SAR\n"
            f"Primey HR Cloud"
        )
        qr_img = BasePrintEngine.generate_qr(qr_text)

        # 🧩 السياق
        context = {
            "payroll": payroll,
            "company": company,
            "qr_image_base64": qr_img,
            "mode": self.mode,
        }

        super().__init__(template_path, context)
