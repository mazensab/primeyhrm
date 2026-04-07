"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  FacebookIcon,
  LinkedinIcon,
  Twitter,
  Instagram,
  Youtube,
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
    facebook: string;
    twitter: string;
    instagram: string;
    ios: string;
    android: string;
    web: string;
    contactUs: string;
    faq: string;
    feedback: string;
    youtube: string;
    linkedin: string;
  };
  logoAlt: string;
};

/* =========================================================
   🍪 Cookie Helpers
========================================================= */
function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;

  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`));

  return match ? decodeURIComponent(match.split("=")[1]) : null;
}

function getCurrentLang(): AppLang {
  const cookieLang =
    getCookie("lang") || getCookie("locale") || getCookie("NEXT_LOCALE") || "";

  return cookieLang.toLowerCase().startsWith("ar") ? "ar" : "en";
}

/* =========================================================
   🔗 External Links
========================================================= */
const SOCIAL_LINKS = {
  facebook: "https://www.facebook.com/mhamcloud",
  instagram: "https://www.instagram.com/mhamcloud",
  twitter: "https://twitter.com/mhamcloud",
  youtube: "https://www.youtube.com/@mhamcloud",
  linkedin: "https://in.linkedin.com/company/mhamcloud",
} as const;

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
      facebook: "فيسبوك",
      twitter: "إكس",
      instagram: "إنستغرام",
      ios: "iOS",
      android: "أندرويد",
      web: "الويب",
      contactUs: "تواصل معنا",
      faq: "الأسئلة الشائعة",
      feedback: "ملاحظاتك",
      youtube: "يوتيوب",
      linkedin: "لينكدإن",
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
      facebook: "Facebook",
      twitter: "X",
      instagram: "Instagram",
      ios: "iOS",
      android: "Android",
      web: "Web",
      contactUs: "Contact Us",
      faq: "FAQ",
      feedback: "Feedback",
      youtube: "YouTube",
      linkedin: "LinkedIn",
    },
    logoAlt: "Primey main hero logo",
  },
};

/* =========================================================
   🧩 Section
========================================================= */
export const FooterSection = () => {
  const [lang, setLang] = useState<AppLang>("en");

  useEffect(() => {
    const updateLang = () => {
      setLang(getCurrentLang());
    };

    updateLang();

    const observer = new MutationObserver(() => {
      updateLang();
    });

    if (typeof document !== "undefined") {
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["lang", "dir"],
      });
    }

    return () => observer.disconnect();
  }, []);

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
              <a
                href={SOCIAL_LINKS.facebook}
                target="_blank"
                rel="noopener noreferrer"
                className="opacity-60 hover:opacity-100"
              >
                {t.links.facebook}
              </a>
            </div>

            <div>
              <a
                href={SOCIAL_LINKS.twitter}
                target="_blank"
                rel="noopener noreferrer"
                className="opacity-60 hover:opacity-100"
              >
                {t.links.twitter}
              </a>
            </div>

            <div>
              <a
                href={SOCIAL_LINKS.instagram}
                target="_blank"
                rel="noopener noreferrer"
                className="opacity-60 hover:opacity-100"
              >
                {t.links.instagram}
              </a>
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
              <a
                href={SOCIAL_LINKS.youtube}
                target="_blank"
                rel="noopener noreferrer"
                className="opacity-60 hover:opacity-100"
              >
                {t.links.youtube}
              </a>
            </div>

            <div>
              <a
                href={SOCIAL_LINKS.linkedin}
                target="_blank"
                rel="noopener noreferrer"
                className="opacity-60 hover:opacity-100"
              >
                {t.links.linkedin}
              </a>
            </div>

            <div>
              <a
                href={SOCIAL_LINKS.instagram}
                target="_blank"
                rel="noopener noreferrer"
                className="opacity-60 hover:opacity-100"
              >
                {t.links.instagram}
              </a>
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
          <span className="font-medium">Mhamcloud</span>
          <span>.</span>
        </div>

        <div className="flex items-center justify-center gap-2">
          <Button size="icon" variant="ghost" className="hover:opacity-50" asChild>
            <a
              href={SOCIAL_LINKS.facebook}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Facebook"
            >
              <FacebookIcon />
            </a>
          </Button>

          <Button size="icon" variant="ghost" className="hover:opacity-50" asChild>
            <a
              href={SOCIAL_LINKS.twitter}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Twitter X"
            >
              <Twitter />
            </a>
          </Button>

          <Button size="icon" variant="ghost" className="hover:opacity-50" asChild>
            <a
              href={SOCIAL_LINKS.instagram}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Instagram"
            >
              <Instagram />
            </a>
          </Button>

          <Button size="icon" variant="ghost" className="hover:opacity-50" asChild>
            <a
              href={SOCIAL_LINKS.youtube}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="YouTube"
            >
              <Youtube />
            </a>
          </Button>

          <Button size="icon" variant="ghost" className="hover:opacity-50" asChild>
            <a
              href={SOCIAL_LINKS.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="LinkedIn"
            >
              <LinkedinIcon />
            </a>
          </Button>
        </div>
      </div>
    </footer>
  );
};