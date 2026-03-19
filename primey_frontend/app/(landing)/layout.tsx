import { cookies } from "next/headers";
import { Navbar } from "@/components/layout/navbar";

type AppLocale = "ar" | "en";

function normalizeLocale(value?: string | null): AppLocale {
  const normalized = (value || "").trim().toLowerCase();

  if (
    normalized === "ar" ||
    normalized.startsWith("ar-") ||
    normalized.startsWith("ar_")
  ) {
    return "ar";
  }

  return "en";
}

export default async function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();

  const locale = normalizeLocale(
    cookieStore.get("lang")?.value ||
      cookieStore.get("locale")?.value ||
      cookieStore.get("NEXT_LOCALE")?.value
  );

  return (
    <>
      <Navbar initialLocale={locale} />
      {children}
    </>
  );
}