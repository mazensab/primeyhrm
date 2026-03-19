import { cookies } from "next/headers";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import SectionContainer from "@/components/layout/section-container";
import SectionHeader from "@/components/layout/section-header";

/* =========================================================
   🌐 Language Types
========================================================= */
type AppLang = "ar" | "en";

type NewsletterContent = {
  titleStart: string;
  titleHighlight: string;
  description: string;
  emailPlaceholder: string;
  emailAriaLabel: string;
  buttonText: string;
};

/* =========================================================
   🌐 Language Helper
========================================================= */
async function getPageLang(): Promise<AppLang> {
  const cookieStore = await cookies();

  const cookieLang =
    cookieStore.get("lang")?.value ||
    cookieStore.get("locale")?.value ||
    cookieStore.get("NEXT_LOCALE")?.value;

  return cookieLang === "ar" ? "ar" : "en";
}

/* =========================================================
   📝 Localized Content
========================================================= */
const content: Record<AppLang, NewsletterContent> = {
  ar: {
    titleStart: "انضم إلى",
    titleHighlight: "نشرتنا اليومية",
    description:
      "اشترك ليصلك آخر التحديثات، والرؤى المهمة، والعروض الحصرية مباشرة إلى بريدك الإلكتروني.",
    emailPlaceholder: "contact@bundui.com",
    emailAriaLabel: "البريد الإلكتروني",
    buttonText: "اشتراك",
  },
  en: {
    titleStart: "Join Our Daily",
    titleHighlight: "Newsletter",
    description:
      "Subscribe to receive the latest updates, insights, and exclusive offers directly to your inbox.",
    emailPlaceholder: "contact@bundui.com",
    emailAriaLabel: "email",
    buttonText: "Subscribe",
  },
};

/* =========================================================
   🧩 Section
========================================================= */
export async function NewsletterSection() {
  const lang = await getPageLang();
  const isArabic = lang === "ar";
  const t = content[lang];

  return (
    <SectionContainer>
      <div dir={isArabic ? "rtl" : "ltr"}>
        <SectionHeader
          title={
            <>
              {t.titleStart}{" "}
              <span className="from-primary/60 to-primary bg-linear-to-b bg-clip-text text-transparent">
                {t.titleHighlight}
              </span>
            </>
          }
          description={t.description}
        />

        <form className="mx-auto flex w-full flex-col gap-4 md:w-6/12 md:flex-row md:gap-2 lg:w-4/12">
          <Input
            placeholder={t.emailPlaceholder}
            className="bg-muted/50 dark:bg-muted/80"
            aria-label={t.emailAriaLabel}
            dir="ltr"
          />
          <Button>{t.buttonText}</Button>
        </form>
      </div>
    </SectionContainer>
  );
}