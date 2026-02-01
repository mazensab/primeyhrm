# ============================================================
# 🖨️ BasePrintEngine — Primey HR Cloud V5 Ultra Pro
# ✔ دعم Browser PDF (بدون كسر التشغيل)
# ✔ دعم الخطوط العربية Tajawal
# ✔ QR Base64
# ============================================================

import os
import base64
from io import BytesIO

from django.conf import settings
from django.template.loader import render_to_string
import qrcode

# ------------------------------------------------------------
# 🟡 xhtml2pdf (اختياري — لا يكسر النظام)
# ------------------------------------------------------------
try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None


class BasePrintEngine:
    """
    🧠 محرك الطباعة الأساسي
    """

    def __init__(self, template_path, context=None):
        self.template_path = template_path
        self.context = context or {}
        self.context["static_css"] = "/static/css/print_style.css"

    # ----------------------------------------------------------
    # 🔵 1) QR Base64
    # ----------------------------------------------------------
    @staticmethod
    def generate_qr(text):
        qr = qrcode.QRCode(box_size=4, border=2)
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    # ----------------------------------------------------------
    # 🔵 2) تسجيل الخطوط (PDF فقط)
    # ----------------------------------------------------------
    @staticmethod
    def register_fonts():
        if not pisa:
            return

        from xhtml2pdf.default import DEFAULT_FONT
        from xhtml2pdf.files import pisaFileObject

        fonts_path = os.path.join(settings.BASE_DIR, "static", "fonts")

        DEFAULT_FONT["Tajawal"] = {
            "regular": pisaFileObject(os.path.join(fonts_path, "Tajawal-Regular.ttf")),
            "bold": pisaFileObject(os.path.join(fonts_path, "Tajawal-Bold.ttf")),
            "italic": pisaFileObject(os.path.join(fonts_path, "Tajawal-Medium.ttf")),
        }

    # ----------------------------------------------------------
    # 🔵 3) PDF (اختياري)
    # ----------------------------------------------------------
    def render_pdf(self):
        if not pisa:
            raise RuntimeError("xhtml2pdf غير مثبت — PDF Engine معطل")

        BasePrintEngine.register_fonts()

        html = render_to_string(self.template_path, self.context)

        pdf_buffer = BytesIO()
        pisa.CreatePDF(
            src=html,
            dest=pdf_buffer,
            encoding="UTF-8",
        )

        return pdf_buffer.getvalue()
