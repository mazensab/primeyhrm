"use client";

import React, { useEffect, useState } from "react";

import { featureList } from "@/@data/features";
import Icon from "@/components/icon";
import SectionContainer from "@/components/layout/section-container";
import SectionHeader from "@/components/layout/section-header";
import { CardTitle } from "@/components/ui/card";
import { CardHover, CardsHover } from "@/components/ui/extras/cards-hover";
import { cn } from "@/lib/utils";

/* =========================================================
   🌐 Language Types
========================================================= */
type AppLang = "ar" | "en";

type FeatureItemTranslation = {
  title: string;
  description: string;
};

type FeaturesContent = {
  subTitle: string;
  title: string;
  description: string;
  items: FeatureItemTranslation[];
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
   📝 Localized Content
========================================================= */
const content: Record<AppLang, FeaturesContent> = {
  ar: {
    subTitle: "المميزات",
    title: "كل ما تحتاجه للنجاح",
    description:
      "توفر منصتنا المتكاملة جميع الأدوات التي تحتاجها لتحسين موقعك، رفع الأداء، وتعزيز تجربة المستخدم بشكل احترافي.",
    items: [
      {
        title: "تحليلات ذكية",
        description:
          "احصل على رؤى واضحة تساعدك على فهم الأداء واتخاذ قرارات مبنية على البيانات بثقة أكبر.",
      },
      {
        title: "أداء أعلى",
        description:
          "حسّن سرعة وكفاءة تجربتك الرقمية من خلال أدوات مصممة لرفع الأداء وتقليل التعقيد.",
      },
      {
        title: "تجربة مستخدم أفضل",
        description:
          "قدّم تجربة أكثر سلاسة وتنظيمًا لعملائك وفريقك عبر واجهات حديثة وسهلة الاستخدام.",
      },
      {
        title: "مرونة في التوسع",
        description:
          "ابدأ بسهولة وتوسع مع نمو أعمالك دون الحاجة إلى إعادة بناء تدفقاتك من الصفر.",
      },
      {
        title: "إدارة مركزية",
        description:
          "تحكم في العمليات والبيانات والأدوات من مكان واحد يسهّل المتابعة والإدارة اليومية.",
      },
      {
        title: "تكامل سلس",
        description:
          "اربط منصتك مع الأدوات والأنظمة التي تحتاجها لتبسيط العمل وتحقيق أعلى إنتاجية.",
      },
    ],
  },
  en: {
    subTitle: "Features",
    title: "Everything You Need to Succeed",
    description:
      "Our comprehensive platform provides all the tools you need to optimize your website, boost performance, and enhance user experience.",
    items: [
      {
        title: "Smart Analytics",
        description:
          "Get clear insights that help you understand performance and make confident, data-driven decisions.",
      },
      {
        title: "Higher Performance",
        description:
          "Improve speed and operational efficiency with tools designed to boost performance and reduce complexity.",
      },
      {
        title: "Better User Experience",
        description:
          "Deliver a smoother and more organized experience for both your customers and your internal team.",
      },
      {
        title: "Scalable Flexibility",
        description:
          "Start simply and scale as your business grows without rebuilding your workflows from scratch.",
      },
      {
        title: "Centralized Management",
        description:
          "Manage operations, data, and tools from one place to simplify oversight and daily administration.",
      },
      {
        title: "Seamless Integration",
        description:
          "Connect your platform with the tools and systems you need to streamline work and maximize productivity.",
      },
    ],
  },
};

/* =========================================================
   🧩 Section
========================================================= */
export const FeaturesSection = () => {
  const [value, setValue] = React.useState<string | null>(null);
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
    <SectionContainer id="features">
      <div dir={dir}>
        <SectionHeader
          subTitle={t.subTitle}
          title={t.title}
          description={t.description}
        />

        <CardsHover
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          value={value}
          onValueChange={setValue}
        >
          {featureList.map((card, index) => {
            const translatedItem = t.items[index];

            return (
              <CardHover
                key={card.icon}
                value={card.icon}
                className={cn(
                  "flex items-start gap-6",
                  isArabic && "flex-row-reverse text-right"
                )}
              >
                <div className="space-y-4">
                  <CardTitle className={cn("text-lg", isArabic && "text-right")}>
                    {translatedItem?.title || card.title}
                  </CardTitle>

                  <p
                    className={cn(
                      "text-muted-foreground font-normal",
                      isArabic && "text-right"
                    )}
                  >
                    {translatedItem?.description || card.description}
                  </p>
                </div>

                <div className="bg-primary/20 ring-primary/10 rounded-full p-2 ring-8">
                  <Icon name={card.icon} className="text-primary size-6" />
                </div>
              </CardHover>
            );
          })}
        </CardsHover>
      </div>
    </SectionContainer>
  );
};