import { cookies } from "next/headers";

import { FAQList } from "@/@data/faq";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { cn } from "@/lib/utils";
import SectionHeader from "../section-header";
import SectionContainer from "../section-container";

/* =========================================================
   🌐 Language Types
========================================================= */
type AppLang = "ar" | "en";

type FAQItemTranslation = {
  question: string;
  answer: string;
};

type FAQContent = {
  subTitle: string;
  title: string;
  items: FAQItemTranslation[];
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
const faqContent: Record<AppLang, FAQContent> = {
  ar: {
    subTitle: "الأسئلة الشائعة",
    title: "الأسئلة الأكثر شيوعًا",
    items: [
      {
        question: "ما الذي يميز منصتكم عن الحلول الأخرى؟",
        answer:
          "نقدم تجربة حديثة وسهلة الاستخدام تجمع بين الأداء العالي، التصميم الاحترافي، والمرونة التي تحتاجها الشركات للنمو وإدارة أعمالها بكفاءة.",
      },
      {
        question: "هل يمكنني البدء بسرعة دون خبرة تقنية كبيرة؟",
        answer:
          "نعم، تم تصميم المنصة لتكون سهلة الاستخدام وسريعة الإعداد، بحيث تتمكن من البدء والاستفادة منها دون تعقيد تقني.",
      },
      {
        question: "هل المنصة مناسبة للشركات الصغيرة والمتوسطة؟",
        answer:
          "بالتأكيد، المنصة مناسبة للشركات الصغيرة والمتوسطة، كما أنها قابلة للتوسع لدعم احتياجات الأعمال الأكبر مستقبلًا.",
      },
      {
        question: "هل يتوفر دعم فني عند الحاجة؟",
        answer:
          "نعم، نوفر دعمًا فنيًا لمساعدتك في الاستفسارات، حل المشكلات، وضمان تجربة تشغيل مستقرة وسلسة.",
      },
      {
        question: "هل يمكن تخصيص المنصة حسب احتياجات العمل؟",
        answer:
          "نعم، توفر المنصة مرونة عالية تسمح بتكييفها مع متطلبات العمل المختلفة وسير الإجراءات داخل شركتك.",
      },
    ],
  },
  en: {
    subTitle: "FAQS",
    title: "Common Questions",
    items: [
      {
        question: "What makes your platform different from other solutions?",
        answer:
          "We provide a modern, easy-to-use experience that combines strong performance, professional design, and the flexibility businesses need to grow efficiently.",
      },
      {
        question: "Can I get started quickly without deep technical experience?",
        answer:
          "Yes, the platform is designed to be easy to use and quick to set up, so you can start benefiting from it without technical complexity.",
      },
      {
        question: "Is the platform suitable for small and medium-sized businesses?",
        answer:
          "Absolutely. The platform works well for small and medium-sized businesses and can scale to support larger operations over time.",
      },
      {
        question: "Is technical support available when needed?",
        answer:
          "Yes, we provide technical support to help with questions, resolve issues, and ensure a smooth and stable experience.",
      },
      {
        question: "Can the platform be customized to fit our business needs?",
        answer:
          "Yes, the platform offers strong flexibility that allows it to adapt to different business requirements and internal workflows.",
      },
    ],
  },
};

/* =========================================================
   🧩 Section
========================================================= */
export const FAQSection = async () => {
  const lang = await getPageLang();
  const isArabic = lang === "ar";
  const t = faqContent[lang];

  return (
    <SectionContainer>
      <div dir={isArabic ? "rtl" : "ltr"}>
        <SectionHeader subTitle={t.subTitle} title={t.title} />

        <div className="max-w-(--breakpoint-sm) mx-auto">
          <Accordion type="single" collapsible className="AccordionRoot">
            {FAQList.map(({ question, answer, value }, index) => {
              const translatedItem = t.items[index];

              return (
                <AccordionItem key={value} value={value}>
                  <AccordionTrigger
                    className={cn(
                      "text-lg",
                      isArabic ? "text-right" : "text-left"
                    )}
                  >
                    {translatedItem?.question || question}
                  </AccordionTrigger>

                  <AccordionContent
                    className={cn(
                      "text-base text-muted-foreground",
                      isArabic && "text-right"
                    )}
                  >
                    {translatedItem?.answer || answer}
                  </AccordionContent>
                </AccordionItem>
              );
            })}
          </Accordion>
        </div>
      </div>
    </SectionContainer>
  );
};