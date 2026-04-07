import * as React from "react";
import {
  Img,
  Section,
  Text,
} from "@react-email/components";

interface EmailHeaderProps {
  companyName?: string;
}

const APP_URL =
  process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

const LOGO_URL =
  "https://drive.google.com/uc?export=view&id=1a0Y1SK3n-Hn9QDZa7Ge24r3--B8zXbTd";

export default function EmailHeader({
  companyName = "Mham Cloud",
}: EmailHeaderProps) {
  return (
    <Section style={header}>
      <Img
        src={LOGO_URL}
        alt={companyName}
        width="148"
        height="48"
        style={logo}
      />

      <Text style={subtitle}>
        نظام احترافي لإدارة الشركات والموظفين والفوترة والاشتراكات
      </Text>
    </Section>
  );
}

const header: React.CSSProperties = {
  background: "linear-gradient(135deg, #0f172a 0%, #111827 100%)",
  padding: "30px 24px 24px",
  textAlign: "center",
};

const logo: React.CSSProperties = {
  margin: "0 auto 14px",
  objectFit: "contain",
  display: "block",
};

const subtitle: React.CSSProperties = {
  margin: 0,
  color: "#cbd5e1",
  fontSize: "14px",
  lineHeight: "24px",
};