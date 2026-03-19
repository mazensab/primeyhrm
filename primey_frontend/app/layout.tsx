import React from "react";
import { cookies } from "next/headers";
import { cn } from "@/lib/utils";
import type { Metadata } from "next";
import { Inter, Bricolage_Grotesque } from "next/font/google";
import "./globals.css";

import { ThemeProvider } from "@/components/layout/theme-provider";
import { Toaster } from "sonner";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const bricolageGrotesque = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--bricolage-grotesque",
});

type AppLocale = "ar" | "en";

function normalizeLocale(value?: string | null): AppLocale {
  const normalized = (value || "").trim().toLowerCase();

  if (
    normalized === "ar" ||
    normalized.startsWith("ar-") ||
    normalized.startsWith("ar_")
  ) {
    return "ar";
  }

  return "en";
}

// ======================================================
// 🌐 Metadata — Favicon + Title
// ======================================================

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"
  ),
  title: "Primey HR Cloud",
  description: "Primey HR Cloud Platform",
  icons: {
    icon: "/favicon.ico",
  },
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();

  const locale = normalizeLocale(
    cookieStore.get("lang")?.value ||
      cookieStore.get("locale")?.value ||
      cookieStore.get("NEXT_LOCALE")?.value
  );

  const dir = locale === "ar" ? "rtl" : "ltr";

  return (
    <html
      lang={locale}
      dir={dir}
      suppressHydrationWarning
      className="scroll-smooth"
    >
      <body
        dir={dir}
        className={cn(
          "from-muted to-primary/5 min-h-screen bg-gradient-to-tl antialiased",
          inter.variable,
          inter.className,
          bricolageGrotesque.variable
        )}
        suppressHydrationWarning
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster richColors position="top-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}