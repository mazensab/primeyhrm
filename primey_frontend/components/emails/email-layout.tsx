import * as React from "react";
import {
  Body,
  Container,
  Head,
  Html,
  Preview,
  Section,
  Text,
} from "@react-email/components";

import EmailHeader from "@/components/emails/email-header";
import EmailFooter from "@/components/emails/email-footer";

interface EmailLayoutProps {
  previewText: string;
  title: string;
  children: React.ReactNode;
  companyName?: string;
}

export default function EmailLayout({
  previewText,
  title,
  children,
  companyName = "Primey HR Cloud",
}: EmailLayoutProps) {
  return (
    <Html lang="ar" dir="rtl">
      <Head />
      <Preview>{previewText}</Preview>

      <Body style={body}>
        <Container style={container}>
          <EmailHeader companyName={companyName} />

          <Section style={contentSection}>
            <Text style={titleStyle}>{title}</Text>

            <Section style={card}>
              {children}
            </Section>
          </Section>

          <EmailFooter companyName={companyName} />
        </Container>
      </Body>
    </Html>
  );
}

const body: React.CSSProperties = {
  margin: 0,
  padding: "24px 12px",
  backgroundColor: "#f6f8fb",
  fontFamily: "Tahoma, Arial, 'Segoe UI', sans-serif",
  direction: "rtl",
};

const container: React.CSSProperties = {
  maxWidth: "680px",
  margin: "0 auto",
  backgroundColor: "#ffffff",
  border: "1px solid #e8eef7",
  borderRadius: "20px",
  overflow: "hidden",
};

const contentSection: React.CSSProperties = {
  padding: "28px 24px 8px",
};

const titleStyle: React.CSSProperties = {
  margin: "0 0 16px",
  fontSize: "24px",
  fontWeight: 700,
  color: "#0f172a",
  lineHeight: "1.5",
};

const card: React.CSSProperties = {
  backgroundColor: "#ffffff",
  border: "1px solid #e5e7eb",
  borderRadius: "16px",
  padding: "24px",
};