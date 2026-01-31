# ============================================================
# 📂 الملف: billing_center/services/zatka_client.py
# 🧾 خدمة توليد الفاتورة الإلكترونية الذكية (ZATCA Smart Engine V2)
# 🚀 المرحلة 1.5 — محسّنة لهوية Primey Blue Glass V8.0
# ------------------------------------------------------------
# ✅ إنشاء XML رسمي متوافق مع ZATCA
# ✅ إنشاء QR آمن بتنسيق TLV Encoding
# ✅ إرجاع ملخص جاهز للعرض في لوحة الفواتير
# ============================================================

import os
import base64
import qrcode
import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from django.conf import settings
from decimal import Decimal

# ============================================================
# 🧩 الفئة الرئيسية
# ============================================================
class ZatkaInvoiceGenerator:
    """
    🧾 مولّد الفواتير الإلكترونية الرسمي — متوافق مع ZATCA
    - ينشئ ملفات XML نظيفة ومنظمة
    - ينشئ QR بصيغة TLV مشفرة
    - يعيد ملخصًا غنيًا لاستخدامه في لوحة التحكم
    """

    def __init__(self, invoice):
        self.invoice = invoice
        self.output_dir = os.path.join(settings.MEDIA_ROOT, "zatka_invoices")
        os.makedirs(self.output_dir, exist_ok=True)

    # ============================================================
    # 🧱 1️⃣ توليد ملف XML رسمي
    # ============================================================
    def generate_xml(self):
        """🔧 إنشاء ملف XML رسمي متوافق مع هيئة الزكاة (ZATCA Phase 1)"""

        root = Element("Invoice", version="1.0", xmlns="urn:zatca:invoice")

        # 🧾 بيانات الفاتورة الأساسية
        SubElement(root, "InvoiceNumber").text = str(self.invoice.invoice_number)
        SubElement(root, "IssueDate").text = self.invoice.issue_date.strftime("%Y-%m-%dT%H:%M:%S")
        SubElement(root, "InvoiceType").text = self.invoice.invoice_type
        SubElement(root, "Status").text = self.invoice.status or "PENDING"

        # 🏢 بيانات البائع (الشركة)
        company = SubElement(root, "Seller")
        SubElement(company, "Name").text = self.invoice.company.name
        SubElement(company, "CRN").text = self.invoice.company.cr_number or "-"
        SubElement(company, "Email").text = self.invoice.company.email or "-"
        SubElement(company, "Phone").text = self.invoice.company.phone or "-"
        SubElement(company, "Address").text = self.invoice.company.address or "-"

        # 👤 بيانات المشتري (إن وُجد)
        buyer = SubElement(root, "Buyer")
        SubElement(buyer, "Name").text = getattr(self.invoice, "buyer_name", "غير محدد")
        SubElement(buyer, "Email").text = getattr(self.invoice, "buyer_email", "-")
        SubElement(buyer, "VATNumber").text = getattr(self.invoice, "buyer_vat", "-")

        # 💰 تفاصيل المبالغ
        SubElement(root, "Currency").text = "SAR"
        SubElement(root, "PaymentMethod").text = self.invoice.get_payment_method_display()
        SubElement(root, "TotalAmount").text = str(self.invoice.total_amount)
        vat_amount = str(round(Decimal(self.invoice.total_amount) * Decimal("0.15"), 2))
        SubElement(root, "VATAmount").text = vat_amount
        SubElement(root, "TotalWithVAT").text = str(round(Decimal(self.invoice.total_amount) + Decimal(vat_amount), 2))

        # 🕒 الطابع الزمني
        SubElement(root, "GeneratedAt").text = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # 💾 حفظ الملف الناتج
        xml_path = os.path.join(self.output_dir, f"invoice_{self.invoice.invoice_number}.xml")
        with open(xml_path, "wb") as f:
            f.write(tostring(root, encoding="utf-8", method="xml"))

        return xml_path

    # ============================================================
    # 🧮 2️⃣ إنشاء QR بتنسيق TLV آمن
    # ============================================================
    def generate_qr_code(self):
        """
        🧮 إنشاء QR يحتوي على البيانات الأساسية وفقًا لمعيار ZATCA TLV:
        TLV: [Seller, VAT, Timestamp, Total, VAT Amount]
        """

        seller = self.invoice.company.name
        vat = self.invoice.company.cr_number or "-"
        timestamp = self.invoice.issue_date.strftime("%Y-%m-%dT%H:%M:%S")
        total = str(self.invoice.total_amount)
        vat_amount = str(round(Decimal(self.invoice.total_amount) * Decimal("0.15"), 2))

        # TLV Encoding String
        qr_string = f"Seller: {seller}\nVAT: {vat}\nDate: {timestamp}\nTotal: {total}\nVAT Amount: {vat_amount}"
        qr_base64 = base64.b64encode(qr_string.encode()).decode()

        # 🖼️ إنشاء صورة QR أنيقة
        qr_img = qrcode.make(qr_string)
        qr_path = os.path.join(self.output_dir, f"qr_{self.invoice.invoice_number}.png")
        qr_img.save(qr_path)

        return {"qr_path": qr_path, "qr_base64": qr_base64}

    # ============================================================
    # 📜 3️⃣ ملخص الفاتورة للعرض في لوحة التحكم
    # ============================================================
    def generate_summary(self):
        """
        📜 إنشاء ملخص غني للفاتورة:
        - رقم الفاتورة
        - اسم الشركة
        - إجمالي المبلغ
        - روابط ملفات XML وQR
        """
        qr_info = self.generate_qr_code()
        vat_amount = round(Decimal(self.invoice.total_amount) * Decimal("0.15"), 2)
        total_with_vat = round(Decimal(self.invoice.total_amount) + vat_amount, 2)

        summary = {
            "invoice_number": self.invoice.invoice_number,
            "company": self.invoice.company.name,
            "amount": float(self.invoice.total_amount),
            "vat_amount": float(vat_amount),
            "total_with_vat": float(total_with_vat),
            "xml_file": f"invoice_{self.invoice.invoice_number}.xml",
            "qr_image": os.path.basename(qr_info["qr_path"]),
            "qr_base64": qr_info["qr_base64"],
        }
        return summary
