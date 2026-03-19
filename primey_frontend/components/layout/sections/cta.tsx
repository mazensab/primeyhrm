"use client";

import Image from "next/image";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";

import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/* =========================================================
   🌐 Language Types
========================================================= */
type AppLang = "ar" | "en";

type PricingCtaContent = {
  title: string;
  description: string;
  scheduleDemo: string;
  startTrial: string;
  imageAlt: string;
};

/* =========================================================
   🌐 Localized Content
========================================================= */
const content: Record<AppLang, PricingCtaContent> = {
  ar: {
    title: "هل أنت مستعد لتحويل موقعك إلى تجربة أقوى؟",
    description:
      "انضم إلى آلاف العملاء الراضين الذين حسّنوا مواقعهم ورفعوا معدلات التحويل باستخدام منصة Metro المدعومة بالذكاء الاصطناعي.",
    scheduleDemo: "احجز عرضًا تجريبيًا",
    startTrial: "ابدأ التجربة المجانية",
    imageAlt: "صورة توضيحية للمنصة",
  },
  en: {
    title: "Ready to Transform Your Website?",
    description:
      "Join thousands of satisfied customers who have optimized their websites and boosted conversions with Metro's AI-powered platform.",
    scheduleDemo: "Schedule a Demo",
    startTrial: "Start Free Trial",
    imageAlt: "shadcn landing page",
  },
};

/* =========================================================
   🍪 Cookie Helper
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
    getCookie("lang") || getCookie("locale") || getCookie("NEXT_LOCALE");

  return cookieLang === "ar" ? "ar" : "en";
}

/* =========================================================
   🧩 Section
========================================================= */
export function PricingCtaSection() {
  const [lang, setLang] = useState<AppLang>("en");

  useEffect(() => {
    const updateLang = () => setLang(getCurrentLang());

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
  const dir = isArabic ? "rtl" : "ltr";
  const t = content[lang];

  return (
    <div className="pt-10 lg:pt-20" dir={dir}>
      <div className="from-muted to-muted/50 relative flex flex-col justify-between gap-4 overflow-hidden rounded-xl border bg-gradient-to-br lg:flex-row! lg:gap-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className={cn(
            "flex max-w-lg flex-col gap-6 py-4 ps-4 pe-4 md:py-10 md:ps-10 md:pe-0",
            isArabic && "lg:text-right"
          )}
        >
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            {t.title}
          </h2>

          <p className="text-muted-foreground md:text-lg">
            {t.description}
          </p>

          <div
            className={cn(
              "flex flex-col gap-4 sm:flex-row!",
              isArabic && "sm:flex-row-reverse!"
            )}
          >
            <Button variant="outline">{t.scheduleDemo}</Button>

            <Button className="gap-2">
              {t.startTrial}
              {isArabic ? <ChevronLeft /> : <ChevronRight />}
            </Button>
          </div>
        </motion.div>

        <figure className="relative h-75 w-full lg:mt-10">
          <Image
            fill
            className="bottom-0 self-end object-cover lg:rounded-tl-lg"
            src="/hero.png"
            alt={t.imageAlt}
            unoptimized
          />
        </figure>
      </div>
    </div>
  );
}