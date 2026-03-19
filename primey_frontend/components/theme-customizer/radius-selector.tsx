"use client";

import { useEffect, useState } from "react";
import { Label } from "@/components/ui/label";
import { useThemeConfig } from "@/components/active-theme";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { BanIcon } from "lucide-react";

type AppLocale = "ar" | "en";

export function ThemeRadiusSelector() {
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
      console.error("Radius selector locale initialization error:", error);
    }
  }, []);

  const isArabic = locale === "ar";

  return (
    <div className="flex flex-col gap-3">
      <Label htmlFor="roundedCorner" className={isArabic ? "text-right" : "text-left"}>
        {isArabic ? "الاستدارة:" : "Radius:"}
      </Label>

      <ToggleGroup
        className="w-full"
        value={theme.radius}
        type="single"
        onValueChange={(value) => {
          if (value) setTheme({ ...theme, radius: value as any });
        }}
      >
        <ToggleGroupItem variant="outline" className="grow" value="none">
          <BanIcon />
        </ToggleGroupItem>
        <ToggleGroupItem variant="outline" className="grow" value="sm">
          SM
        </ToggleGroupItem>
        <ToggleGroupItem variant="outline" className="grow" value="md">
          MD
        </ToggleGroupItem>
        <ToggleGroupItem variant="outline" className="grow" value="lg">
          LG
        </ToggleGroupItem>
        <ToggleGroupItem variant="outline" className="grow" value="xl">
          XL
        </ToggleGroupItem>
      </ToggleGroup>
    </div>
  );
}