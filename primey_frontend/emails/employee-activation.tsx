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

export interface EmployeeActivationEmailProps {
  employeeName: string;
  employeeCode: string;
  username: string;
  companyName: string;
  department: string;
  jobTitle: string;
  activationUrl: string;
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

export default function EmployeeActivationEmail({
  employeeName = "أحمد محمد",
  employeeCode = "EMP-001",
  username = "ahmad",
  companyName = "شركة تجريبية",
  department = "الموارد البشرية",
  jobTitle = "أخصائي موارد بشرية",
  activationUrl = "http://localhost:3000/employee/activate/token",
}: EmployeeActivationEmailProps) {
  return (
    <EmailLayout
      previewText={`تم تجهيز حساب الموظف ${employeeName}`}
      title="تم إنشاء حساب الموظف بنجاح"
      companyName="Primey HR Cloud"
    >
      <Text style={paragraph}>
        تم تجهيز حسابك للدخول إلى بوابة الموظفين. يمكنك الآن تفعيل الحساب
        وإكمال إعداد كلمة المرور للوصول إلى خدماتك داخل النظام.
      </Text>

      <Section style={infoBox}>
        <InfoRow label="اسم الموظف" value={employeeName} />
        <InfoRow label="الرقم الوظيفي" value={employeeCode} />
        <InfoRow label="اسم المستخدم" value={username} />
        <InfoRow label="الشركة" value={companyName} />
        <InfoRow label="القسم" value={department} />
        <InfoRow label="الوظيفة" value={jobTitle} />
      </Section>

      <Section style={buttonWrap}>
        <Button href={activationUrl} style={button}>
          تفعيل حساب الموظف
        </Button>
      </Section>

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