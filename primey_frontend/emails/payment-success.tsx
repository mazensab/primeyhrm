import * as React from "react";
import {
  Button,
  Column,
  Link,
  Row,
  Section,
  Text,
} from "@react-email/components";

import EmailLayout from "@/components/emails/email-layout";

export interface PaymentSuccessEmailProps {
  companyName: string;
  invoiceNumber: string;
  paymentNumber: string;
  amount: string;
  paymentMethod: string;
  paidAt: string;
  status: string;
  invoiceUrl: string;
}

function InfoRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <Row style={row}>
      <Column style={labelCol}>
        <Text style={labelText}>{label}</Text>
      </Column>
      <Column>
        <Text style={valueText}>{value}</Text>
      </Column>
    </Row>
  );
}

export default function PaymentSuccessEmail({
  companyName = "شركة تجريبية",
  invoiceNumber = "INV-2026-0001",
  paymentNumber = "PAY-2026-0001",
  amount = "1,500 SAR",
  paymentMethod = "BANK_TRANSFER",
  paidAt = "2026-03-09 01:00 AM",
  status = "PAID",
  invoiceUrl = "http://localhost:3000/system/invoices/1",
}: PaymentSuccessEmailProps) {
  return (
    <EmailLayout
      previewText={`تم استلام دفعتك بنجاح للشركة ${companyName}`}
      title="تم استلام دفعتك بنجاح ✅"
      companyName="Mham Cloud"
    >
      <Text style={paragraph}>
        نشكرك على السداد. تم تسجيل عملية الدفع بنجاح وتحديث حالة الفاتورة
        إلى مدفوعة. وسيتم إرفاق نسخة PDF من الفاتورة مع هذه الرسالة
        عند الربط من جهة الباكند.
      </Text>

      <Section style={successBox}>
        <Text style={successTitle}>تم تأكيد الدفع</Text>
        <Text style={successAmount}>{amount}</Text>
      </Section>

      <Section style={infoBox}>
        <InfoRow label="اسم الشركة" value={companyName} />
        <InfoRow label="رقم الفاتورة" value={invoiceNumber} />
        <InfoRow label="رقم الدفعة" value={paymentNumber} />
        <InfoRow label="طريقة الدفع" value={paymentMethod} />
        <InfoRow label="تاريخ الدفع" value={paidAt} />
        <InfoRow label="الحالة" value={status} />
      </Section>

      <Section style={buttonWrap}>
        <Button href={invoiceUrl} style={button}>
          عرض الفاتورة
        </Button>
      </Section>

      <Text style={muted}>
        إذا لم يعمل الزر، استخدم الرابط التالي:
      </Text>

      <Link href={invoiceUrl} style={link}>
        {invoiceUrl}
      </Link>
    </EmailLayout>
  );
}

const paragraph: React.CSSProperties = {
  margin: "0 0 18px",
  fontSize: "15px",
  lineHeight: "28px",
  color: "#334155",
};

const successBox: React.CSSProperties = {
  backgroundColor: "#ecfdf5",
  border: "1px solid #a7f3d0",
  borderRadius: "14px",
  padding: "18px",
  textAlign: "center",
  marginBottom: "18px",
};

const successTitle: React.CSSProperties = {
  margin: "0 0 8px",
  fontSize: "14px",
  fontWeight: 700,
  color: "#065f46",
};

const successAmount: React.CSSProperties = {
  margin: 0,
  fontSize: "24px",
  fontWeight: 700,
  color: "#047857",
};

const infoBox: React.CSSProperties = {
  backgroundColor: "#f8fafc",
  border: "1px solid #e2e8f0",
  borderRadius: "14px",
  padding: "16px",
};

const row: React.CSSProperties = {
  borderBottom: "1px solid #e5e7eb",
};

const labelCol: React.CSSProperties = {
  width: "150px",
};

const labelText: React.CSSProperties = {
  margin: "10px 0",
  fontSize: "14px",
  fontWeight: 700,
  color: "#0f172a",
};

const valueText: React.CSSProperties = {
  margin: "10px 0",
  fontSize: "14px",
  color: "#475569",
};

const buttonWrap: React.CSSProperties = {
  textAlign: "center",
  padding: "24px 0 16px",
};

const button: React.CSSProperties = {
  backgroundColor: "#0f172a",
  color: "#ffffff",
  fontSize: "14px",
  fontWeight: 700,
  textDecoration: "none",
  borderRadius: "12px",
  padding: "14px 24px",
  display: "inline-block",
};

const muted: React.CSSProperties = {
  margin: "0 0 8px",
  fontSize: "13px",
  color: "#64748b",
};

const link: React.CSSProperties = {
  color: "#2563eb",
  fontSize: "13px",
  textDecoration: "none",
};