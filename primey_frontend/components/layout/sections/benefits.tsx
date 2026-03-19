import { cookies } from "next/headers";

import { benefitList } from "@/@data/benefits";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Icon from "@/components/icon";
import { cn } from "@/lib/utils";
import SectionContainer from "../section-container";
import SectionHeader from "../section-header";

/* =========================================================
   🌐 Language Types
========================================================= */
type AppLang = "ar" | "en";

type BenefitTranslation = {
  title: string;
  description: string;
};

type BenefitsContent = {
  subTitle: string;
  title: string;
  description: string;
  items: BenefitTranslation[];
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
const benefitsContent: Record<AppLang, BenefitsContent> = {
  ar: {
    subTitle: "المزايا",
    title: "ماذا نقدم لك؟",
    description:
      "كل الحلول الذكية والمبتكرة التي تحتاجها لتنمية أعمالك موجودة هنا. نحن نضيف قيمة حقيقية لأعمالك من خلال مزايا تبسّط سير العمل، وترفع الكفاءة، وتدعم قراراتك بثقة.",
    items: [
      {
        title: "تحسين الكفاءة التشغيلية",
        description:
          "نساعدك على تبسيط العمليات اليومية وتقليل الأعمال اليدوية المكررة حتى يعمل فريقك بسرعة ودقة أكبر.",
      },
      {
        title: "اتخاذ قرارات أفضل",
        description:
          "من خلال الرؤى الذكية والتقارير الواضحة، يمكنك متابعة الأداء واتخاذ قرارات مبنية على بيانات فعلية.",
      },
      {
        title: "تجربة عمل أكثر سلاسة",
        description:
          "نوفر لك أدوات حديثة وسهلة الاستخدام تجعل إدارة الأعمال أكثر تنظيمًا ومرونة وراحة لفريقك.",
      },
      {
        title: "نمو قابل للتوسع",
        description:
          "حلولنا مصممة لتدعم تطور أعمالك وتساعدك على التوسع بثبات دون تعقيد أو فوضى تشغيلية.",
      },
    ],
  },
  en: {
    subTitle: "Benefits",
    title: "What Do We Bring to You?",
    description:
      "All the innovative solutions you need to grow your business are here. We add value to your business with features that simplify your workflow, increase efficiency, and strengthen your decisions.",
    items: [
      {
        title: "Operational Efficiency",
        description:
          "We help you streamline daily operations and reduce repetitive manual work so your team can move faster and more accurately.",
      },
      {
        title: "Smarter Decision Making",
        description:
          "With clear insights and intelligent reporting, you can track performance and make decisions based on real data.",
      },
      {
        title: "Smoother Work Experience",
        description:
          "We provide modern, easy-to-use tools that make business management more organized, flexible, and comfortable for your team.",
      },
      {
        title: "Scalable Growth",
        description:
          "Our solutions are built to support your business growth and help you scale confidently without operational complexity.",
      },
    ],
  },
};

/* =========================================================
   🧩 Section
========================================================= */
export const BenefitsSection = async () => {
  const lang = await getPageLang();
  const isArabic = lang === "ar";
  const t = benefitsContent[lang];

  return (
    <SectionContainer id="benefits">
      <div className="grid lg:grid-cols-2 lg:gap-24">
        <div>
          <SectionHeader
            className={cn(
              "sticky max-w-full text-center lg:top-[22rem]",
              isArabic ? "lg:text-right" : "lg:text-start"
            )}
            subTitle={t.subTitle}
            title={t.title}
            description={t.description}
          />
        </div>

        <div className="flex w-full flex-col gap-6 lg:gap-[14rem]">
          {benefitList.map(({ icon, title }, index) => {
            const translatedItem = t.items[index];

            return (
              <Card
                key={title}
                className={cn("group/number bg-background lg:sticky")}
                style={{ top: `${20 + index + 2}rem` }}>
                <CardHeader>
                  <div className="flex justify-between">
                    <Icon
                      name={icon}
                      className="text-primary bg-primary/20 ring-primary/10 mb-6 size-10 rounded-full p-2 ring-8"
                    />
                    <span className="text-muted-foreground/15 group-hover/number:text-muted-foreground/30 text-5xl font-bold transition-all delay-75">
                      0{index + 1}
                    </span>
                  </div>

                  <CardTitle className={cn("text-lg", isArabic && "text-right")}>
                    {translatedItem?.title || title}
                  </CardTitle>
                </CardHeader>

                <CardContent
                  className={cn("text-muted-foreground", isArabic && "text-right")}>
                  {translatedItem?.description || ""}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </SectionContainer>
  );
};