import { cookies } from "next/headers";

import DiscordIcon from "@/components/icons/discord-icon";
import SectionContainer from "@/components/layout/section-container";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

/* =========================================================
   🌐 Language Types
========================================================= */
type AppLang = "ar" | "en";

type CommunityContent = {
  titleStart: string;
  titleHighlight: string;
  description: string;
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
const communityContent: Record<AppLang, CommunityContent> = {
  ar: {
    titleStart: "هل أنت مستعد للانضمام إلى هذا",
    titleHighlight: "المجتمع؟",
    description:
      "انضم إلى مجتمعنا النشط على ديسكورد، وتواصل وشارك وتطور مع أشخاص لديهم نفس الاهتمامات والطموح.",
    buttonText: "اضغط وابدأ الآن",
  },
  en: {
    titleStart: "Ready to join this",
    titleHighlight: "Community?",
    description:
      "Join our vibrant Discord community! Connect, share, and grow with like-minded enthusiasts.",
    buttonText: "Click to dive in!",
  },
};

/* =========================================================
   🧩 Section
========================================================= */
export async function CommunitySection() {
  const lang = await getPageLang();
  const isArabic = lang === "ar";
  const t = communityContent[lang];

  return (
    <SectionContainer>
      <div className="mx-auto lg:max-w-(--breakpoint-lg)">
        <Card>
          <CardHeader>
            <CardTitle className="flex flex-col items-center text-center text-3xl font-bold md:text-4xl">
              <DiscordIcon className="text-[#5e7ce9]" />

              <div className={isArabic ? "leading-relaxed" : ""}>
                {t.titleStart}{" "}
                <span className="from-primary/60 to-primary bg-linear-to-b bg-clip-text text-transparent">
                  {t.titleHighlight}
                </span>
              </div>
            </CardTitle>
          </CardHeader>

          <CardContent className="text-muted-foreground mx-auto max-w-screen-sm space-y-4 text-center text-xl">
            <p>{t.description}</p>
          </CardContent>

          <CardFooter className="justify-center">
            <Button size="lg" asChild>
              <a
                href="https://discord.com/"
                target="_blank"
                rel="noopener noreferrer"
              >
                {t.buttonText}
              </a>
            </Button>
          </CardFooter>
        </Card>
      </div>
    </SectionContainer>
  );
}