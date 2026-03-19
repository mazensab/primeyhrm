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

export interface CompanyWelcomeEmailProps {
  companyName: string;
  adminName: string;
  username: string;
  email: string;
  planName: string;
  startDate: string;
  loginUrl: string;
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

export default function CompanyWelcomeEmail({
  companyName = "شركة تجريبية",
  adminName = "مدير النظام",
  username = "admin",
  email = "admin@example.com",
  planName = "الباقة الأساسية",
  startDate = "2026-03-09",
  loginUrl = "http://localhost:3000/login",
}: CompanyWelcomeEmailProps) {
  return (
    <EmailLayout
      previewText={`تم تسجيل شركتك ${companyName} بنجاح في Primey HR Cloud`}
      title="مرحبًا بك في Primey HR Cloud 🎉"
      companyName="Primey HR Cloud"
    >
      <Text style={paragraph}>
        يسعدنا إبلاغك بأنه تم تسجيل شركتك بنجاح داخل المنصة،
        وأصبح حساب المسؤول جاهزًا لبدء استخدام النظام وإدارة الموظفين
        والاشتراكات والفواتير باحترافية.
      </Text>

      <Section style={infoBox}>
        <InfoRow label="اسم الشركة" value={companyName} />
        <InfoRow label="اسم المسؤول" value={adminName} />
        <InfoRow label="اسم المستخدم" value={username} />
        <InfoRow label="البريد الإلكتروني" value={email} />
        <InfoRow label="الباقة" value={planName} />
        <InfoRow label="تاريخ البداية" value={startDate} />
      </Section>

      <Section style={buttonWrap}>
        <Button href={loginUrl} style={button}>
          تسجيل الدخول
        </Button>
      </Section>

      <Text style={note}>
        تنبيه أمني: نوصي بعدم مشاركة بيانات الدخول مع أي طرف غير مخوّل.
      </Text>

      <Text style={muted}>
        إذا لم يعمل الزر، استخدم الرابط التالي:
      </Text>

      <Link href={loginUrl} style={link}>
        {loginUrl}
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