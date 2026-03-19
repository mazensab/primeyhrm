import * as React from "react";
import {
  Hr,
  Link,
  Section,
  Text,
} from "@react-email/components";

interface EmailFooterProps {
  companyName?: string;
}

const APP_URL =
  process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

export default function EmailFooter({
  companyName = "Primey HR Cloud",
}: EmailFooterProps) {
  return (
    <Section style={footer}>
      <Hr style={hr} />

      <Text style={footerText}>
        تم إرسال هذه الرسالة من خلال نظام {companyName}.
      </Text>

      <Text style={footerText}>
        الموقع:
        {" "}
        <Link href={APP_URL} style={link}>
          {APP_URL}
        </Link>
      </Text>

      <Text style={footerText}>
        الدعم الفني:
        {" "}
        <Link href="mailto:info@primeyride.com" style={link}>
          info@primeyride.com
        </Link>
      </Text>

      <Text style={footerMuted}>
        © 2026 {companyName}. جميع الحقوق محفوظة.
      </Text>
    </Section>
  );
}

const footer: React.CSSProperties = {
  padding: "8px 24px 26px",
  textAlign: "center",
};

const hr: React.CSSProperties = {
  borderColor: "#e5e7eb",
  margin: "16px 0 20px",
};

const footerText: React.CSSProperties = {
  margin: "0 0 8px",
  color: "#475569",
  fontSize: "13px",
  lineHeight: "22px",
};

const footerMuted: React.CSSProperties = {
  margin: "8px 0 0",
  color: "#94a3b8",
  fontSize: "12px",
  lineHeight: "20px",
};

const link: React.CSSProperties = {
  color: "#2563eb",
  textDecoration: "none",
};