"use client";

import { useEffect, useState } from "react";
import { reviewList } from "@/@data/reviews";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious
} from "@/components/ui/carousel";
import { Star } from "lucide-react";
import SectionContainer from "@/components/layout/section-container";
import SectionHeader from "@/components/layout/section-header";
import { cn } from "@/lib/utils";

/* =========================================================
   🌐 Language Types
========================================================= */
type AppLang = "ar" | "en";

type TestimonialContent = {
  subTitle: string;
  title: string;
  description: string;
  imageAlt: string;
  reviews: string[];
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
const content: Record<AppLang, TestimonialContent> = {
  ar: {
    subTitle: "آراء العملاء",
    title: "محبوب من الفرق حول العالم",
    description:
      "لا تكتفِ بكلامنا فقط. اطّلع على ما يقوله عملاؤنا عن تجربتهم معنا.",
    imageAlt: "صورة العميل",
    reviews: [
      "تجربة رائعة فعلًا. المنصة ساعدتنا على تنظيم العمل وتحسين الكفاءة بشكل ملحوظ.",
      "واجهة ممتازة وسهلة الاستخدام، والدعم كان سريعًا واحترافيًا جدًا.",
      "من أفضل الحلول التي استخدمناها لإدارة العمل وتحسين تجربة الفريق.",
      "وفرت لنا وقتًا كبيرًا وساعدتنا على اتخاذ قرارات أوضح اعتمادًا على البيانات.",
      "المنصة مرنة، حديثة، ومناسبة جدًا لنمو الأعمال وتوسّعها.",
      "حل احترافي متكامل أحدث فرقًا واضحًا في طريقة إدارتنا للعمليات اليومية."
    ]
  },
  en: {
    subTitle: "Testimonials",
    title: "Loved by Teams Worldwide",
    description:
      "Don't just take our word for it. See what our customers have to say about their experience.",
    imageAlt: "customer avatar",
    reviews: [
      "An excellent experience overall. The platform helped us streamline operations and improve efficiency significantly.",
      "Great interface, easy to use, and the support team was fast and professional.",
      "One of the best solutions we have used to manage work and improve our team experience.",
      "It saved us a lot of time and helped us make clearer decisions based on real data.",
      "The platform is flexible, modern, and highly suitable for growing businesses.",
      "A complete professional solution that made a clear difference in how we manage daily operations."
    ]
  }
};

/* =========================================================
   🧩 Section
========================================================= */
export const TestimonialSection = () => {
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
        attributeFilter: ["lang", "dir"]
      });
    }

    return () => observer.disconnect();
  }, []);

  const isArabic = lang === "ar";
  const dir = isArabic ? "rtl" : "ltr";
  const t = content[lang];

  return (
    <SectionContainer id="testimonials">
      <div dir={dir}>
        <SectionHeader
          subTitle={t.subTitle}
          title={t.title}
          description={t.description}
        />

        <Carousel
          opts={{
            align: "start"
          }}
          className="relative mx-auto w-[80%] sm:w-[90%] lg:max-w-(--breakpoint-xl)"
        >
          <CarouselContent>
            {reviewList.map((review, index) => (
              <CarouselItem key={review.name} className="md:basis-1/2 lg:basis-1/3">
                <Card className="bg-muted h-full">
                  <CardContent className="flex h-full flex-col gap-4">
                    <div
                      className={cn(
                        "flex gap-1",
                        isArabic && "justify-end"
                      )}
                    >
                      <Star className="size-4 fill-orange-400 text-orange-400" />
                      <Star className="size-4 fill-orange-400 text-orange-400" />
                      <Star className="size-4 fill-orange-400 text-orange-400" />
                      <Star className="size-4 fill-orange-400 text-orange-400" />
                      <Star className="size-4 fill-orange-400 text-orange-400" />
                    </div>

                    <p className={cn(isArabic && "text-right")}>
                      {t.reviews[index] || review.comment}
                    </p>

                    <div
                      className={cn(
                        "flex flex-row items-center gap-4",
                        isArabic && "flex-row-reverse"
                      )}
                    >
                      <Avatar className="size-12">
                        <AvatarImage src={review.image} alt={t.imageAlt} />
                        <AvatarFallback>
                          {review.name
                            ?.split(" ")
                            .slice(0, 2)
                            .map((part) => part.charAt(0))
                            .join("")
                            .toUpperCase() || "NA"}
                        </AvatarFallback>
                      </Avatar>

                      <div
                        className={cn(
                          "flex flex-col space-y-1",
                          isArabic && "items-end text-right"
                        )}
                      >
                        <CardTitle>{review.name}</CardTitle>
                        <CardDescription>{review.userName}</CardDescription>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </CarouselItem>
            ))}
          </CarouselContent>

          <CarouselPrevious />
          <CarouselNext />
        </Carousel>
      </div>
    </SectionContainer>
  );
};