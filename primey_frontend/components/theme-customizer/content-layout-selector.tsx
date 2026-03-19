"use client";

import { useEffect, useState } from "react";
import { Label } from "@/components/ui/label";
import { useThemeConfig } from "@/components/active-theme";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

type AppLocale = "ar" | "en";

export function ContentLayoutSelector() {
  const { theme, setTheme } = useThemeConfig();
  const [locale, setLocale] = useState<AppLocale>("ar");

  useEffect(() => {
    try {
      const savedLocale =
        typeof window !== "undefined"
          ? (window.localStorage.getItem("primey-locale") as AppLocale | null)
          : null;

      setLocale(savedLocale === "en" ? "en" : "ar");
    } catch (error) {
      console.error("Content layout selector locale initialization error:", error);
    }
  }, []);

  const isArabic = locale === "ar";

  return (
    <div className="hidden flex-col gap-3 lg:flex">
      <Label className={isArabic ? "text-right" : "text-left"}>
        {isArabic ? "تخطيط المحتوى" : "Content layout"}
      </Label>

      <ToggleGroup
        className="w-full"
        value={theme.contentLayout}
        type="single"
        onValueChange={(value) => {
          if (value) setTheme({ ...theme, contentLayout: value as any });
        }}
      >
        <ToggleGroupItem variant="outline" className="grow" value="full">
          {isArabic ? "كامل" : "Full"}
        </ToggleGroupItem>

        <ToggleGroupItem variant="outline" className="grow" value="centered">
          {isArabic ? "متمركز" : "Centered"}
        </ToggleGroupItem>
      </ToggleGroup>
    </div>
  );
}