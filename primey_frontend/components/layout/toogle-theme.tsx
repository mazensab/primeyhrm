"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { Button } from "../ui/button";

type AppLocale = "ar" | "en";

export const ToggleTheme = () => {
  const { theme, setTheme } = useTheme();
  const [locale, setLocale] = useState<AppLocale>("ar");

  useEffect(() => {
    try {
      const savedLocale =
        typeof window !== "undefined"
          ? (window.localStorage.getItem("primey-locale") as AppLocale | null)
          : null;

      setLocale(savedLocale === "en" ? "en" : "ar");
    } catch (error) {
      console.error("Toggle theme locale initialization error:", error);
    }
  }, []);

  const isArabic = locale === "ar";

  return (
    <Button
      type="button"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
      size="icon"
      variant="ghost"
    >
      <div className="flex items-center gap-2 dark:hidden">
        <Moon />
        <span className="block lg:hidden">
          {isArabic ? "داكن" : "Dark"}
        </span>
      </div>

      <div className="hidden items-center gap-2 dark:flex">
        <Sun />
        <span className="block lg:hidden">
          {isArabic ? "فاتح" : "Light"}
        </span>
      </div>

      <span className="sr-only">
        {isArabic ? "تغيير المظهر" : "Change theme"}
      </span>
    </Button>
  );
};