"use client";

import { useEffect, useState } from "react";
import { DEFAULT_THEME, THEMES } from "@/lib/themes";
import { useThemeConfig } from "@/components/active-theme";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

type AppLocale = "ar" | "en";

function getPresetName(name: string, locale: AppLocale) {
  if (locale === "en") return name;

  const map: Record<string, string> = {
    Default: "الافتراضي",
    Underground: "أندرجراوند",
    "Rose Garden": "حديقة الورد",
    "Lake View": "إطلالة البحيرة",
    "Sunset Glow": "وهج الغروب",
    "Forest Whisper": "همس الغابة",
    "Ocean Breeze": "نسيم المحيط",
    "Lavender Dream": "حلم اللافندر",
  };

  return map[name] || name;
}

export function PresetSelector() {
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
      console.error("Preset selector locale initialization error:", error);
    }
  }, []);

  const isArabic = locale === "ar";

  const handlePreset = (value: string) => {
    setTheme({ ...theme, ...DEFAULT_THEME, preset: value as any });
  };

  const selectedTheme = THEMES.find((item) => item.value === theme.preset);

  return (
    <div className="flex flex-col gap-3">
      <Label className={isArabic ? "text-right" : "text-left"}>
        {isArabic ? "نمط المظهر:" : "Theme preset:"}
      </Label>

      <Select value={theme.preset} onValueChange={(value) => handlePreset(value)}>
        <SelectTrigger className={`w-full ${isArabic ? "text-right" : "text-left"}`}>
          <SelectValue
            placeholder={isArabic ? "اختر نمطًا" : "Select a theme"}
          >
            {selectedTheme ? getPresetName(selectedTheme.name, locale) : null}
          </SelectValue>
        </SelectTrigger>

        <SelectContent align="end">
          {THEMES.map((item) => (
            <SelectItem key={item.name} value={item.value}>
              <div className="flex shrink-0 gap-1">
                {item.colors.map((color, key) => (
                  <span
                    key={key}
                    className="size-2 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
              {getPresetName(item.name, locale)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}