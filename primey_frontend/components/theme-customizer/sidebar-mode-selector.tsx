"use client";

import { useEffect, useState } from "react";
import { Label } from "@/components/ui/label";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useSidebar } from "@/components/ui/sidebar";

type AppLocale = "ar" | "en";

export function SidebarModeSelector() {
  const { toggleSidebar } = useSidebar();
  const [locale, setLocale] = useState<AppLocale>("ar");

  useEffect(() => {
    try {
      const savedLocale =
        typeof window !== "undefined"
          ? (window.localStorage.getItem("primey-locale") as AppLocale | null)
          : null;

      setLocale(savedLocale === "en" ? "en" : "ar");
    } catch (error) {
      console.error("Sidebar mode selector locale initialization error:", error);
    }
  }, []);

  const isArabic = locale === "ar";

  return (
    <div className="hidden flex-col gap-3 lg:flex">
      <Label className={isArabic ? "text-right" : "text-left"}>
        {isArabic ? "وضع الشريط الجانبي:" : "Sidebar mode:"}
      </Label>

      <ToggleGroup className="w-full" type="single" onValueChange={() => toggleSidebar()}>
        <ToggleGroupItem variant="outline" className="grow" value="full">
          {isArabic ? "افتراضي" : "Default"}
        </ToggleGroupItem>

        <ToggleGroupItem variant="outline" className="grow" value="centered">
          {isArabic ? "أيقونات" : "Icon"}
        </ToggleGroupItem>
      </ToggleGroup>
    </div>
  );
}