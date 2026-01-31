# ================================================================
# 🧾 CompaniesPrintEngine — Primey HR Cloud V1 Ultra Pro
# ================================================================
# ✔ مبني على BasePrintEngine
# ✔ يدعم الخط العربي + QR
# ✔ جاهز لطباعة قائمة الشركات
# ✔ متوافق 100% مع print_style.css
# ================================================================

from .base_engine import BasePrintEngine


class CompaniesPrintEngine(BasePrintEngine):
    """
    🧾 محرك طباعة قائمة الشركات — CompaniesPrintEngine V1
    --------------------------------------------------------
    - يقوم بتمرير قائمة الشركات للقالب
    - يعتمد على BasePrintEngine (الخطوط + QR + CSS)
    """

    def __init__(self, companies):
        context = {
            "companies": companies,
        }

        super().__init__(
            template_path="company_manager/export/companies_print.html",
            context=context
        )
