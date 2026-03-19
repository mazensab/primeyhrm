import { cookies } from "next/headers";

import { sponsors } from "@/@data/sponsors";
import Icon from "@/components/icon";
import { InfiniteSlider } from "@/components/ui/extras/infinite-slider";
import { cn } from "@/lib/utils";

/* =========================================================
   🌐 Language Types
========================================================= */
type AppLang = "ar" | "en";

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
   🧩 Section
========================================================= */
export const SponsorsSection = async () => {
  const lang = await getPageLang();
  const isArabic = lang === "ar";

  return (
    <section className="pb-12 lg:pb-24" dir={isArabic ? "rtl" : "ltr"}>
      <div className="container mask-r-from-50% mask-r-to-90% mask-l-from-50% mask-l-to-90%">
        <InfiniteSlider gap={50} speedOnHover={40}>
          {sponsors.map(({ icon, name }) => (
            <div
              key={name}
              className={cn(
                "flex items-center text-xl font-medium md:text-2xl",
                isArabic && "flex-row-reverse"
              )}
            >
              <Icon
                name={icon}
                className={cn(
                  "text-foreground size-6",
                  isArabic ? "ml-3" : "mr-3"
                )}
              />
              {name}
            </div>
          ))}
        </InfiniteSlider>
      </div>
    </section>
  );
};