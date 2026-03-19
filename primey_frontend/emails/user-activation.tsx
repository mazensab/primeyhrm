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

export interface UserActivationEmailProps {
  fullName: string;
  username: string;
  email: string;
  role: string;
  companyName: string;
  activationUrl: string;
  expiresAt: string;
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

export default function UserActivationEmail({
  fullName = "مستخدم النظام",
  username = "system_user",
  email = "user@example.com",
  role = "SYSTEM_ADMIN",
  companyName = "Primey HR Cloud",
  activationUrl = "http://localhost:3000/activate-account/token",
  expiresAt = "2026-03-10 01:00 AM",
}: UserActivationEmailProps) {
  return (
    <EmailLayout
      previewText={`تفعيل حساب ${fullName} في Primey HR Cloud`}
      title="تفعيل حسابك في Primey HR Cloud"
      companyName="Primey HR Cloud"
    >
      <Text style={paragraph}>
        تم إنشاء حسابك بنجاح. لإكمال التفعيل، يرجى الضغط على الزر التالي
        وتعيين كلمة مرور آمنة.
      </Text>

      <Section style={infoBox}>
        <InfoRow label="الاسم" value={fullName} />
        <InfoRow label="اسم المستخدم" value={username} />
        <InfoRow label="البريد الإلكتروني" value={email} />
        <InfoRow label="الدور" value={role} />
        <InfoRow label="الجهة" value={companyName} />
        <InfoRow label="انتهاء الرابط" value={expiresAt} />
      </Section>

      <Section style={buttonWrap}>
        <Button href={activationUrl} style={button}>
          تفعيل الحساب
        </Button>
      </Section>

      <Text style={note}>
        لا تشارك رابط التفعيل مع أي شخص. إذا لم تطلب إنشاء هذا الحساب،
        فتجاهل هذه الرسالة.
      </Text>

      <Text style={muted}>الرابط المباشر:</Text>
      <Link href={activationUrl} style={link}>
        {activationUrl}
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

const note: React.CSSProperties = {
  margin: "0 0 10px",
  fontSize: "13px",
  lineHeight: "24px",
  color: "#b45309",
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