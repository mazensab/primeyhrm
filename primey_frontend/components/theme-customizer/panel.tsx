"use client";

import { useEffect, useState } from "react";
import { Palette } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  PresetSelector,
  SidebarModeSelector,
  ThemeScaleSelector,
  ColorModeSelector,
  ContentLayoutSelector,
  ThemeRadiusSelector,
  ResetThemeButton,
} from "@/components/theme-customizer/index";
import { useIsMobile } from "@/hooks/use-mobile";

type AppLocale = "ar" | "en";

export function ThemeCustomizerPanel() {
  const isMobile = useIsMobile();
  const [locale, setLocale] = useState<AppLocale>("ar");

  useEffect(() => {
    try {
      const savedLocale =
        typeof window !== "undefined"
          ? (window.localStorage.getItem("primey-locale") as AppLocale | null)
          : null;

      setLocale(savedLocale === "en" ? "en" : "ar");
    } catch (error) {
      console.error("Theme customizer panel locale initialization error:", error);
    }
  }, []);

  const isArabic = locale === "ar";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button size="icon-sm" variant="ghost">
          <Palette />
          <span className="sr-only">
            {isArabic ? "تخصيص المظهر" : "Customize theme"}
          </span>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        dir={isArabic ? "rtl" : "ltr"}
        align={isMobile ? "center" : isArabic ? "start" : "end"}
        className={`w-80 p-4 shadow-xl ${
          isArabic ? "ml-4 lg:ml-0" : "mr-4 lg:mr-0"
        }`}
      >
        <div className="grid space-y-4">
          <PresetSelector />
          <ThemeScaleSelector />
          <ThemeRadiusSelector />
          <ColorModeSelector />
          <ContentLayoutSelector />
          <SidebarModeSelector />
        </div>

        <ResetThemeButton />
      </DropdownMenuContent>
    </DropdownMenu>
  );
}