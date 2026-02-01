# ============================================================
# 🖨️ BasePrintEngine — Primey HR Cloud V5 Ultra Pro
# ✔ مبني على xhtml2pdf (متوافق 100% مع Windows)
# ✔ يدعم الخطوط العربية Tajawal (Regular / Medium / Bold)
# ✔ يدعم QR Base64
# ✔ يحمّل CSS موحد للطباعة print_style.css
# ============================================================

import os
import base64
from django.conf import settings
from django.template.loader import render_to_string
try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None

from io import BytesIO
import qrcode


class BasePrintEngine:
    """
    🧠 محرك الطباعة الأساسي لجميع الوحدات (عقود، رواتب، بطاقات، خطابات…)
    """

    def __init__(self, template_path, context={}):
        self.template_path = template_path
        self.context = context
        self.context["static_css"] = "/static/css/print_style.css"

    # ----------------------------------------------------------
    # 🔵 1) توليد QR Base64
    # ----------------------------------------------------------
    @staticmethod
    def generate_qr(text):
        qr = qrcode.QRCode(box_size=4, border=2)
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return img_str

    # ----------------------------------------------------------
    # 🔵 2) تسجيل الخطوط
    # ----------------------------------------------------------
    @staticmethod
    def register_fonts():
        from xhtml2pdf.default import DEFAULT_FONT
        from xhtml2pdf.files import pisaFileObject

        fonts_path = os.path.join(settings.BASE_DIR, "static", "fonts")

        DEFAULT_FONT["Tajawal"] = {
            "regular": pisaFileObject(os.path.join(fonts_path, "Tajawal-Regular.ttf")),
            "bold": pisaFileObject(os.path.join(fonts_path, "Tajawal-Bold.ttf")),
            "italic": pisaFileObject(os.path.join(fonts_path, "Tajawal-Medium.ttf")),
        }

    # ----------------------------------------------------------
    # 🔵 3) توليد PDF
    # ----------------------------------------------------------
    def render_pdf(self):
        BasePrintEngine.register_fonts()

        html = render_to_string(self.template_path, self.context)

        pdf_buffer = BytesIO()
        pisa.CreatePDF(
            src=html,
            dest=pdf_buffer,
            encoding="UTF-8",
        )

        return pdf_buffer.getvalue()
