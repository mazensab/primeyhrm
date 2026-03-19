"use client";

import { useEffect, useState } from "react";
import { Label } from "@/components/ui/label";
import { useThemeConfig } from "@/components/active-theme";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { BanIcon } from "lucide-react";

type AppLocale = "ar" | "en";

export function ThemeScaleSelector() {
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
      console.error("Scale selector locale initialization error:", error);
    }
  }, []);

  const isArabic = locale === "ar";

  return (
    <div className="flex flex-col gap-3">
      <Label htmlFor="roundedCorner" className={isArabic ? "text-right" : "text-left"}>
        {isArabic ? "المقياس:" : "Scale:"}
      </Label>

      <div>
        <ToggleGroup
          className="w-full"
          value={theme.scale}
          type="single"
          onValueChange={(value) => {
            if (value) setTheme({ ...theme, scale: value as any });
          }}
        >
          <ToggleGroupItem variant="outline" className="grow" value="none">
            <BanIcon />
          </ToggleGroupItem>

          <ToggleGroupItem variant="outline" className="grow" value="sm">
            XS
          </ToggleGroupItem>

          <ToggleGroupItem variant="outline" className="grow" value="lg">
            LG
          </ToggleGroupItem>
        </ToggleGroup>
      </div>
    </div>
  );
}