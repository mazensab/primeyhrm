"use client";

import { useEffect, useState } from "react";
import { useThemeConfig } from "@/components/active-theme";
import { Button } from "@/components/ui/button";
import { DEFAULT_THEME } from "@/lib/themes";

type AppLocale = "ar" | "en";

export function ResetThemeButton() {
  const { setTheme } = useThemeConfig();
  const [locale, setLocale] = useState<AppLocale>("ar");

  useEffect(() => {
    try {
      const savedLocale =
        typeof window !== "undefined"
          ? (window.localStorage.getItem("primey-locale") as AppLocale | null)
          : null;

      setLocale(savedLocale === "en" ? "en" : "ar");
    } catch (error) {
      console.error("Reset theme locale initialization error:", error);
    }
  }, []);

  const isArabic = locale === "ar";

  const resetThemeHandle = () => {
    setTheme(DEFAULT_THEME);
  };

  return (
    <Button className="mt-4 w-full" onClick={resetThemeHandle}>
      {isArabic ? "إعادة إلى الافتراضي" : "Reset to Default"}
    </Button>
  );
}