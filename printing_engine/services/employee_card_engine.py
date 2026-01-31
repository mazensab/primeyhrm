# ============================================================
# 🪪 EmployeeCardPrintEngine — V4 Ultra Pro
# ✔ يدعم QR
# ✔ مناسب للهوية / بطاقة العمل
# ✔ يطبع بتنسيق PDF كامل
# ============================================================

from .base_engine import BasePrintEngine


class EmployeeCardPrintEngine(BasePrintEngine):
    """
    🧠 محرك طباعة بطاقة الموظف
    """

    def __init__(self, employee, company,
                 template_path="employee_center/employee_card_pdf.html"):

        self.employee = employee
        self.company = company

        # QR 🔵
        qr_text = (
            f"Employee: {employee.first_name} {employee.last_name}\n"
            f"Company: {company.name}\n"
            f"National ID: {employee.national_id}\n"
            f"Primey HR Cloud"
        )
        qr_img = BasePrintEngine.generate_qr(qr_text)

        # 🧩 السياق
        context = {
            "employee": employee,
            "company": company,
            "qr_image_base64": qr_img,
        }

        super().__init__(template_path, context)
