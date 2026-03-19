import { cookies } from "next/headers";
import Image from "next/image";
import Link from "next/link";
import {
  DribbbleIcon,
  FacebookIcon,
  LinkedinIcon,
  Twitter,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/* =========================================================
   🌐 Language Types
========================================================= */
type AppLang = "ar" | "en";

type FooterContent = {
  description: string;
  groups: {
    contact: string;
    platforms: string;
    help: string;
    socials: string;
  };
  links: {
    github: string;
    twitter: string;
    instagram: string;
    ios: string;
    android: string;
    web: string;
    contactUs: string;
    faq: string;
    feedback: string;
    twitch: string;
    discord: string;
    dribbble: string;
  };
  logoAlt: string;
};

/* =========================================================
   🌐 Language Helper
========================================================= */
async function getPageLang(): Promise<AppLang> {
  const cookieStore = await cookies();

  const cookieLang =
    cookieStore.get("lang")?.value ||
    cookieStore.get("locale")?.value ||
    cookieStore.get("NEXT_LOCALE")?.value ||
    "";

  const normalizedLang = cookieLang.toLowerCase();

  return normalizedLang.startsWith("ar") ? "ar" : "en";
}

/* =========================================================
   📝 Localized Content
========================================================= */
const content: Record<AppLang, FooterContent> = {
  ar: {
    description:
      "تعرّف على حلّنا السحابي المدعوم بالذكاء الاصطناعي لتخفيف عبء العمل، ورفع الكفاءة، ومساعدتك على اتخاذ قرارات أكثر دقة.",
    groups: {
      contact: "التواصل",
      platforms: "المنصات",
      help: "المساعدة",
      socials: "الشبكات الاجتماعية",
    },
    links: {
      github: "جيت هب",
      twitter: "تويتر",
      instagram: "إنستغرام",
      ios: "iOS",
      android: "أندرويد",
      web: "الويب",
      contactUs: "تواصل معنا",
      faq: "الأسئلة الشائعة",
      feedback: "ملاحظاتك",
      twitch: "تويتش",
      discord: "ديسكورد",
      dribbble: "دريبل",
    },
    logoAlt: "شعار Primey الرئيسي",
  },
  en: {
    description:
      "Meet our AI-powered SaaS solution to lighten your workload, increase efficiency and make more accurate decisions.",
    groups: {
      contact: "Contact",
      platforms: "Platforms",
      help: "Help",
      socials: "Socials",
    },
    links: {
      github: "Github",
      twitter: "Twitter",
      instagram: "Instagram",
      ios: "iOS",
      android: "Android",
      web: "Web",
      contactUs: "Contact Us",
      faq: "FAQ",
      feedback: "Feedback",
      twitch: "Twitch",
      discord: "Discord",
      dribbble: "Dribbble",
    },
    logoAlt: "Primey main hero logo",
  },
};

/* =========================================================
   🧩 Section
========================================================= */
export const FooterSection = async () => {
  const lang = await getPageLang();
  const isArabic = lang === "ar";
  const t = content[lang];

  return (
    <footer
      id="footer"
      className="container space-y-4 pb-4 lg:pb-8"
      dir={isArabic ? "rtl" : "ltr"}
    >
      <div className="bg-muted rounded-2xl border p-10">
        <div className="grid grid-cols-2 gap-x-12 gap-y-8 md:grid-cols-4 xl:grid-cols-6">
          <div className="col-span-full space-y-4 xl:col-span-2">
            <Link
              href="/"
              className={cn(
                "inline-flex w-full",
                isArabic ? "justify-start xl:justify-start" : "justify-start"
              )}
              aria-label={t.logoAlt}
            >
              <Image
                src="/hero logo.png"
                alt={t.logoAlt}
                width={1200}
                height={420}
                priority
                unoptimized
                className="
                  h-auto
                  w-full
                  max-w-[180px]
                  object-contain
                  sm:max-w-[220px]
                  md:max-w-[240px]
                  lg:max-w-[260px]
                "
              />
            </Link>

            <p className={cn("text-muted-foreground", isArabic && "text-right")}>
              {t.description}
            </p>
          </div>

          <div className={cn("flex flex-col gap-2", isArabic && "text-right")}>
            <h3 className="mb-2 text-lg font-bold">{t.groups.contact}</h3>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                {t.links.github}
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                {t.links.twitter}
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                {t.links.instagram}
              </Link>
            </div>
          </div>

          <div className={cn("flex flex-col gap-2", isArabic && "text-right")}>
            <h3 className="mb-2 text-lg font-bold">{t.groups.platforms}</h3>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                {t.links.ios}
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                {t.links.android}
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                {t.links.web}
              </Link>
            </div>
          </div>

          <div className={cn("flex flex-col gap-2", isArabic && "text-right")}>
            <h3 className="mb-2 text-lg font-bold">{t.groups.help}</h3>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                {t.links.contactUs}
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                {t.links.faq}
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                {t.links.feedback}
              </Link>
            </div>
          </div>

          <div className={cn("flex flex-col gap-2", isArabic && "text-right")}>
            <h3 className="mb-2 text-lg font-bold">{t.groups.socials}</h3>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                {t.links.twitch}
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                {t.links.discord}
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                {t.links.dribbble}
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div
        className={cn(
          "flex flex-col justify-between gap-4 sm:flex-row!",
          isArabic && "sm:flex-row-reverse!"
        )}
      >
        <div
          className={cn(
            "text-muted-foreground flex items-center justify-center gap-1 text-sm sm:justify-start",
            isArabic && "sm:justify-end"
          )}
        >
          <span>&copy; {new Date().getFullYear()}</span>
          <span>|</span>
          <Button variant="link" className="h-auto p-0" asChild>
            <Link target="_blank" href="https://bundui.io/">
              Bundui
            </Link>
          </Button>
          <span>.</span>
        </div>

        <div className="flex items-center justify-center gap-2">
          <Button size="icon" variant="ghost" className="hover:opacity-50" asChild>
            <Link href="#">
              <FacebookIcon />
            </Link>
          </Button>

          <Button size="icon" variant="ghost" className="hover:opacity-50" asChild>
            <Link href="#">
              <Twitter />
            </Link>
          </Button>

          <Button size="icon" variant="ghost" className="hover:opacity-50" asChild>
            <Link href="#">
              <DribbbleIcon />
            </Link>
          </Button>

          <Button size="icon" variant="ghost" className="hover:opacity-50" asChild>
            <Link href="#">
              <LinkedinIcon />
            </Link>
          </Button>
        </div>
      </div>
    </footer>
  );
};