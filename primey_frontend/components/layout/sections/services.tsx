import { cookies } from "next/headers";

import { ProService, serviceList } from "@/@data/services";
import SectionContainer from "@/components/layout/section-container";
import SectionHeader from "@/components/layout/section-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

/* =========================================================
   🌐 Language Types
========================================================= */
type AppLang = "ar" | "en";

type ServiceItemTranslation = {
  title: string;
  description: string;
};

type ServicesContent = {
  subTitle: string;
  title: string;
  description: string;
  proLabel: string;
  items: ServiceItemTranslation[];
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
const content: Record<AppLang, ServicesContent> = {
  ar: {
    subTitle: "الخدمات",
    title: "نمِّ أعمالك",
    description:
      "من التسويق والمبيعات إلى العمليات والاستراتيجية، لدينا الخبرة التي تساعدك على تحقيق أهدافك بثقة وكفاءة.",
    proLabel: "احترافي",
    items: [
      {
        title: "الاستراتيجية والنمو",
        description:
          "نساعدك على بناء مسار نمو أوضح من خلال حلول عملية واستراتيجيات تدعم توسع أعمالك واستدامتها.",
      },
      {
        title: "تحسين العمليات",
        description:
          "قم بتبسيط إجراءاتك اليومية ورفع الكفاءة التشغيلية عبر خدمات مصممة لتقليل التعقيد وتحسين الأداء.",
      },
      {
        title: "المبيعات والتفاعل",
        description:
          "عزّز تواصلك مع العملاء وادعم فرص التحويل والنمو من خلال تجارب أكثر فاعلية وتنظيمًا.",
      },
      {
        title: "الدعم والتطوير",
        description:
          "نوفر لك دعمًا متواصلًا وخدمات تطوير تساعدك على تحسين التجربة العامة وتوسيع قدرات المنصة.",
      },
    ],
  },
  en: {
    subTitle: "Services",
    title: "Grow Your Business",
    description:
      "From marketing and sales to operations and strategy, we have the expertise to help you achieve your goals.",
    proLabel: "PRO",
    items: [
      {
        title: "Strategy & Growth",
        description:
          "We help you build a clearer growth path through practical solutions and strategies that support sustainable expansion.",
      },
      {
        title: "Operations Optimization",
        description:
          "Streamline your daily workflows and improve operational efficiency with services designed to reduce complexity.",
      },
      {
        title: "Sales & Engagement",
        description:
          "Strengthen customer interaction and improve conversion opportunities through more effective and organized experiences.",
      },
      {
        title: "Support & Development",
        description:
          "We provide ongoing support and development services that help you improve the overall experience and expand platform capabilities.",
      },
    ],
  },
};

/* =========================================================
   🧩 Section
========================================================= */
export const ServicesSection = async () => {
  const lang = await getPageLang();
  const isArabic = lang === "ar";
  const t = content[lang];

  return (
    <SectionContainer id="solutions">
      <div dir={isArabic ? "rtl" : "ltr"}>
        <SectionHeader
          subTitle={t.subTitle}
          title={t.title}
          description={t.description}
        />

        <div className="mx-auto grid w-full max-w-(--breakpoint-lg) gap-6 sm:grid-cols-2 lg:grid-cols-2">
          {serviceList.map(({ title, description, pro }, index) => {
            const translatedItem = t.items[index];

            return (
              <Card key={title} className="bg-muted relative h-full gap-2">
                <CardHeader>
                  <CardTitle className={cn("text-lg", isArabic && "text-right")}>
                    {translatedItem?.title || title}
                  </CardTitle>
                </CardHeader>

                <CardContent>
                  <p className={cn("text-muted-foreground", isArabic && "text-right")}>
                    {translatedItem?.description || description}
                  </p>
                </CardContent>

                <Badge
                  data-pro={ProService.YES === pro}
                  variant="secondary"
                  className={cn(
                    "absolute data-[pro=false]:hidden",
                    isArabic ? "-top-2 -left-3" : "-top-2 -right-3"
                  )}
                >
                  {t.proLabel}
                </Badge>
              </Card>
            );
          })}
        </div>
      </div>
    </SectionContainer>
  );
};