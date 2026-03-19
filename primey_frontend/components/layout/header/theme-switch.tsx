"use client";

import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import { MoonIcon, SunIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

type AppLocale = "ar" | "en";

export default function ThemeSwitch() {
  const [mounted, setMounted] = useState(false);
  const [locale, setLocale] = useState<AppLocale>("ar");
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    setMounted(true);

    try {
      const savedLocale =
        typeof window !== "undefined"
          ? (window.localStorage.getItem("primey-locale") as AppLocale | null)
          : null;

      setLocale(savedLocale === "en" ? "en" : "ar");
    } catch (error) {
      console.error("Theme switch locale initialization error:", error);
    }
  }, []);

  if (!mounted) {
    return null;
  }

  const isArabic = locale === "ar";

  return (
    <Button
      size="icon-sm"
      variant="ghost"
      className="relative"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
    >
      {theme === "light" ? <MoonIcon /> : <SunIcon />}
      <span className="sr-only">
        {isArabic ? "تبديل المظهر" : "Toggle theme"}
      </span>
    </Button>
  );
}