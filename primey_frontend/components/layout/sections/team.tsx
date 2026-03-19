import { cookies } from "next/headers";
import Image from "next/image";
import Link from "next/link";
import React from "react";

import { teamList } from "@/@data/teams";
import GithubIcon from "@/components/icons/github-icon";
import LinkedInIcon from "@/components/icons/linkedin-icon";
import XIcon from "@/components/icons/x-icon";
import SectionContainer from "@/components/layout/section-container";
import SectionHeader from "@/components/layout/section-header";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

/* =========================================================
   🌐 Language Types
========================================================= */
type AppLang = "ar" | "en";

type TeamContent = {
  subTitle: string;
  title: string;
  imageAlt: string;
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
const content: Record<AppLang, TeamContent> = {
  ar: {
    subTitle: "الفريق",
    title: "فريق الأحلام في الشركة",
    imageAlt: "صورة عضو الفريق",
  },
  en: {
    subTitle: "Team",
    title: "The Company Dream Team",
    imageAlt: "team member",
  },
};

/* =========================================================
   🛠️ Position Translator
========================================================= */
function translatePosition(value: string, lang: AppLang): string {
  if (lang === "en") return value;

  const key = value.trim().toLowerCase();

  const dictionary: Record<string, string> = {
    founder: "المؤسس",
    cofounder: "الشريك المؤسس",
    "co-founder": "الشريك المؤسس",
    ceo: "الرئيس التنفيذي",
    cto: "المدير التقني",
    cfo: "المدير المالي",
    coo: "مدير العمليات",
    manager: "المدير",
    product: "المنتج",
    "product manager": "مدير المنتج",
    designer: "المصمم",
    "ui designer": "مصمم واجهات",
    "ux designer": "مصمم تجربة المستخدم",
    developer: "مطور",
    engineer: "مهندس",
    "software engineer": "مهندس برمجيات",
    "frontend developer": "مطور واجهات أمامية",
    "backend developer": "مطور خلفية",
    "full stack developer": "مطور فل ستاك",
    marketer: "مسوّق",
    "marketing manager": "مدير التسويق",
    sales: "المبيعات",
    "sales manager": "مدير المبيعات",
    support: "الدعم",
    "customer success": "نجاح العملاء",
    hr: "الموارد البشرية",
    recruiter: "مسؤول التوظيف",
    consultant: "مستشار",
    advisor: "مستشار",
  };

  return dictionary[key] || value;
}

/* =========================================================
   🧩 Section
========================================================= */
export async function TeamSection() {
  const lang = await getPageLang();
  const isArabic = lang === "ar";
  const t = content[lang];

  const socialIcon = (socialName: string) => {
    switch (socialName) {
      case "LinkedIn":
        return <LinkedInIcon />;
      case "Github":
        return <GithubIcon />;
      case "X":
        return <XIcon />;
      default:
        return null;
    }
  };

  return (
    <SectionContainer id="team">
      <div dir={isArabic ? "rtl" : "ltr"}>
        <SectionHeader subTitle={t.subTitle} title={t.title} />

        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {teamList.map(
            ({ imageUrl, firstName, lastName, positions, socialNetworks }, index) => (
              <Card
                key={index}
                className="bg-muted group/hoverimg flex h-full flex-col overflow-hidden pt-0"
              >
                <figure className="overflow-hidden">
                  <Image
                    src={imageUrl}
                    width={300}
                    height={300}
                    className="aspect-square w-full object-cover saturate-0 transition-all duration-200 ease-linear group-hover/hoverimg:scale-[1.05] group-hover/hoverimg:saturate-100"
                    alt={t.imageAlt}
                    unoptimized
                  />
                </figure>

                <CardHeader className="pt-0">
                  <CardTitle
                    className={cn(
                      "text-lg",
                      isArabic && "text-right"
                    )}
                  >
                    {firstName}
                    <span className={cn("text-primary", isArabic ? "mr-1" : "ml-1")}>
                      {lastName}
                    </span>
                  </CardTitle>

                  <CardDescription className={cn(isArabic && "text-right")}>
                    {positions.map((position) => translatePosition(position, lang)).join("، ")}
                  </CardDescription>
                </CardHeader>

                <CardFooter
                  className={cn(
                    "mt-auto",
                    isArabic ? "flex-row-reverse space-x-0 space-x-reverse gap-4" : "space-x-4"
                  )}
                >
                  {socialNetworks.map(({ name, url }, index) => (
                    <Link
                      key={index}
                      href={url}
                      target="_blank"
                      className="transition-all hover:opacity-80"
                    >
                      {socialIcon(name)}
                    </Link>
                  ))}
                </CardFooter>
              </Card>
            )
          )}
        </div>
      </div>
    </SectionContainer>
  );
}