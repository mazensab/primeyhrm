import { cookies } from "next/headers";
import type { Metadata } from "next";

import { BenefitsSection } from "@/components/layout/sections/benefits";
import { CommunitySection } from "@/components/layout/sections/community";
import { ContactSection } from "@/components/layout/sections/contact";
import { FAQSection } from "@/components/layout/sections/faq";
import { FeaturesSection } from "@/components/layout/sections/features";
import { FooterSection } from "@/components/layout/sections/footer";
import { HeroSection } from "@/components/layout/sections/hero";
import { NewsletterSection } from "@/components/layout/sections/newsletter";
import { PricingSection } from "@/components/layout/sections/pricing";
import { ServicesSection } from "@/components/layout/sections/services";
import { SponsorsSection } from "@/components/layout/sections/sponsors";
import { TeamSection } from "@/components/layout/sections/team";
import { TestimonialSection } from "@/components/layout/sections/testimonial";

/* =========================================================
   🌐 Language Helpers
========================================================= */
type AppLang = "ar" | "en";

function normalizeLang(value?: string | null): AppLang {
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

async function getPageLang(): Promise<AppLang> {
  const cookieStore = await cookies();

  const cookieLang =
    cookieStore.get("lang")?.value ||
    cookieStore.get("locale")?.value ||
    cookieStore.get("NEXT_LOCALE")?.value;

  return normalizeLang(cookieLang);
}

function getPageDirection(lang: AppLang): "rtl" | "ltr" {
  return lang === "ar" ? "rtl" : "ltr";
}

/* =========================================================
   🧾 Dynamic Metadata
========================================================= */
export async function generateMetadata(): Promise<Metadata> {
  const lang = await getPageLang();
  const isArabic = lang === "ar";

  const title = isArabic
    ? "Primey HR Cloud — منصة سحابية ذكية لإدارة الموارد البشرية"
    : "Primey HR Cloud — Smart Cloud HR Management Platform";

  const description = isArabic
    ? "Primey HR Cloud منصة احترافية لإدارة الموارد البشرية، الحضور، الرواتب، الإجازات، والأداء ضمن تجربة SaaS حديثة ومتعددة اللغات."
    : "Primey HR Cloud is a professional SaaS platform for HR, attendance, payroll, leave management, and performance with a modern multilingual experience.";

  const imageAlt = isArabic
    ? "Primey HR Cloud Landing Page"
    : "Primey HR Cloud Landing Page";

  return {
    title,
    description,
    openGraph: {
      type: "website",
      title,
      description,
      images: [
        {
          url: "/seo.jpg",
          width: 1200,
          height: 630,
          alt: imageAlt,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: ["/seo.jpg"],
    },
  };
}

/* =========================================================
   🏠 Home Page
========================================================= */
export default async function Home() {
  const lang = await getPageLang();
  const dir = getPageDirection(lang);

  return (
    <main lang={lang} dir={dir} className="w-full" suppressHydrationWarning>
      <HeroSection />
      <SponsorsSection />
      <BenefitsSection />
      <FeaturesSection />
      <ServicesSection />
      <TestimonialSection />
      <TeamSection />
      <PricingSection />
      <CommunitySection />
      <ContactSection />
      <FAQSection />
      <NewsletterSection />
      <FooterSection />
    </main>
  );
}