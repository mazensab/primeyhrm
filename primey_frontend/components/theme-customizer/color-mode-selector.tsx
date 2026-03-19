"use client";

import { useEffect, useState } from "react";
import { Label } from "@/components/ui/label";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useTheme } from "next-themes";

type AppLocale = "ar" | "en";

export function ColorModeSelector() {
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
      console.error("Color mode selector locale initialization error:", error);
    }
  }, []);

  const isArabic = locale === "ar";

  return (
    <div className="flex flex-col gap-3">
      <Label htmlFor="roundedCorner" className={isArabic ? "text-right" : "text-left"}>
        {isArabic ? "وضع الألوان:" : "Color mode:"}
      </Label>

      <ToggleGroup
        className="w-full"
        value={theme}
        type="single"
        onValueChange={(value) => {
          if (value) setTheme(value);
        }}
      >
        <ToggleGroupItem variant="outline" className="grow" value="light">
          {isArabic ? "فاتح" : "Light"}
        </ToggleGroupItem>

        <ToggleGroupItem variant="outline" className="grow" value="dark">
          {isArabic ? "داكن" : "Dark"}
        </ToggleGroupItem>
      </ToggleGroup>
    </div>
  );
}