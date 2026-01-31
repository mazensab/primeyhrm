# ============================================================
# 📄 ContractPrintEngine — V5 Ultra Pro
# ✔ مبني بالكامل على BasePrintEngine (xhtml2pdf)
# ✔ QR يدعم بيانات العقد + الموظف + الشركة
# ✔ يستخدم قوالب HTML داخل employee_center/contract_print_pdf.html
# ============================================================

from .base_engine import BasePrintEngine


class ContractPrintEngine(BasePrintEngine):
    """
    🧠 محرك طباعة العقود — الإصدار الخامس
    """

    def __init__(self, contract, employee, company,
                 template_path="employee_center/contract_print_pdf.html"):

        self.contract = contract
        self.employee = employee
        self.company = company

        # QR 🔵
        qr_text = (
            f"Contract No: {contract.contract_number}\n"
            f"Employee: {employee.first_name} {employee.last_name}\n"
            f"Company: {company.name}\n"
            f"Start: {contract.start_date}\n"
            f"Primey HR Cloud"
        )
        qr_img = BasePrintEngine.generate_qr(qr_text)

        # 🧩 السياق
        context = {
            "contract": contract,
            "employee": employee,
            "company": company,
            "qr_image_base64": qr_img,
        }

        super().__init__(template_path, context)
