"use client";

import { useEffect, useState } from "react";
import { Globe, PanelLeftClose, PanelLeftOpen } from "lucide-react";

import { Separator } from "@/components/ui/separator";
import Notifications from "@/components/layout/header/notifications";
import Search from "@/components/layout/header/search";
import ThemeSwitch from "@/components/layout/header/theme-switch";
import UserMenu from "@/components/layout/header/user-menu";
import { ThemeCustomizerPanel } from "@/components/theme-customizer";
import { ActiveThemeProvider } from "@/components/active-theme";
import { Button } from "@/components/ui/button";
import { useSidebar } from "@/components/ui/sidebar";

type AppLocale = "ar" | "en";

function applyLocaleToDocument(nextLocale: AppLocale) {
  if (typeof document === "undefined") return;

  document.documentElement.lang = nextLocale;
  document.documentElement.dir = nextLocale === "ar" ? "rtl" : "ltr";
  document.body.setAttribute("dir", nextLocale === "ar" ? "rtl" : "ltr");
}

function getStoredLocale(): AppLocale {
  try {
    if (typeof window === "undefined") return "ar";
    const savedLocale = window.localStorage.getItem("primey-locale");
    return savedLocale === "en" ? "en" : "ar";
  } catch (error) {
    console.error("Read locale error:", error);
    return "ar";
  }
}

export function SiteHeader() {
  const { toggleSidebar, open } = useSidebar();
  const [locale, setLocale] = useState<AppLocale>("ar");

  useEffect(() => {
    const syncLocale = () => {
      const nextLocale = getStoredLocale();
      setLocale(nextLocale);
      applyLocaleToDocument(nextLocale);
    };

    syncLocale();

    window.addEventListener("primey-locale-changed", syncLocale);
    window.addEventListener("storage", syncLocale);

    return () => {
      window.removeEventListener("primey-locale-changed", syncLocale);
      window.removeEventListener("storage", syncLocale);
    };
  }, []);

  const toggleLanguage = () => {
    try {
      const nextLocale: AppLocale = locale === "ar" ? "en" : "ar";
      setLocale(nextLocale);

      if (typeof window !== "undefined") {
        window.localStorage.setItem("primey-locale", nextLocale);
        window.dispatchEvent(new Event("primey-locale-changed"));
      }

      applyLocaleToDocument(nextLocale);
    } catch (error) {
      console.error("Language toggle error:", error);
    }
  };

  return (
    <header
      className="
        sticky top-0 z-50
        flex h-14 shrink-0 items-center
        border-b
        bg-background
        supports-[backdrop-filter]:bg-background/80
        backdrop-blur-xl
      "
    >
      <div className="flex w-full items-center gap-2 px-6">
        <Button onClick={toggleSidebar} size="icon" variant="ghost">
          {open ? <PanelLeftClose /> : <PanelLeftOpen />}
        </Button>

        <Separator orientation="vertical" className="mx-2 h-4" />

        <Search />

        <div className="ml-auto flex items-center gap-1.5">
          <Button
            type="button"
            size="icon"
            variant="ghost"
            onClick={toggleLanguage}
            className="h-9 w-9 rounded-xl"
            aria-label={locale === "ar" ? "Switch to English" : "التبديل إلى العربية"}
            title={locale === "ar" ? "Switch to English" : "التبديل إلى العربية"}
          >
            <Globe className="h-5 w-5" />
          </Button>

          <Notifications />
          <ThemeSwitch />

          <ActiveThemeProvider>
            <ThemeCustomizerPanel />
          </ActiveThemeProvider>

          <Separator orientation="vertical" className="mx-2 h-4" />

          <UserMenu />
        </div>
      </div>
    </header>
  );
}