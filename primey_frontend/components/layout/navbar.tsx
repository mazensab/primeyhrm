"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  Languages,
  Menu,
} from "lucide-react";

import { productList, routeList } from "@/@data/navbar";

import Icon from "@/components/icon";
import {
  Sheet,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ToggleTheme } from "@/components/layout/toogle-theme";
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";

type AppLocale = "ar" | "en";

type NavbarProps = {
  initialLocale?: AppLocale;
};

function normalizeLocale(value?: string | null): AppLocale {
  const normalized = (value || "").trim().toLowerCase();

  if (
    normalized === "ar" ||
    normalized.startsWith("ar-") ||
    normalized.startsWith("ar_")
  ) {
    return "ar";
  }

  return "en";
}

function setLocaleCookie(locale: AppLocale) {
  const oneYearInSeconds = 60 * 60 * 24 * 365;

  document.cookie = `lang=${locale}; path=/; max-age=${oneYearInSeconds}; samesite=lax`;
  document.cookie = `locale=${locale}; path=/; max-age=${oneYearInSeconds}; samesite=lax`;
  document.cookie = `NEXT_LOCALE=${locale}; path=/; max-age=${oneYearInSeconds}; samesite=lax`;
}

export const Navbar = ({ initialLocale = "ar" }: NavbarProps) => {
  const router = useRouter();
  const [isOpen, setIsOpen] = React.useState(false);
  const [locale, setLocale] = useState<AppLocale>(initialLocale);

  useEffect(() => {
    try {
      const savedLocale =
        typeof window !== "undefined"
          ? window.localStorage.getItem("primey-locale")
          : null;

      const cookieLocale =
        typeof document !== "undefined"
          ? document.cookie
              .split("; ")
              .find((item) => item.startsWith("lang="))
              ?.split("=")[1]
          : null;

      const nextLocale = normalizeLocale(
        savedLocale || cookieLocale || initialLocale
      );

      setLocale(nextLocale);

      if (typeof window !== "undefined") {
        window.localStorage.setItem("primey-locale", nextLocale);
      }

      if (typeof document !== "undefined") {
        document.documentElement.lang = nextLocale;
        document.documentElement.dir = nextLocale === "ar" ? "rtl" : "ltr";
        document.body.setAttribute("dir", nextLocale === "ar" ? "rtl" : "ltr");
      }
    } catch (error) {
      console.error("Navbar locale initialization error:", error);
    }
  }, [initialLocale]);

  const isArabic = locale === "ar";
  const ArrowIcon = isArabic ? ChevronLeftIcon : ChevronRightIcon;

  const toggleLanguage = () => {
    try {
      const nextLocale: AppLocale = locale === "ar" ? "en" : "ar";
      setLocale(nextLocale);

      if (typeof window !== "undefined") {
        window.localStorage.setItem("primey-locale", nextLocale);
      }

      if (typeof document !== "undefined") {
        setLocaleCookie(nextLocale);
        document.documentElement.lang = nextLocale;
        document.documentElement.dir = nextLocale === "ar" ? "rtl" : "ltr";
        document.body.setAttribute("dir", nextLocale === "ar" ? "rtl" : "ltr");
      }

      router.refresh();
    } catch (error) {
      console.error("Navbar language toggle error:", error);
    }
  };

  return (
    <header className="sticky top-3 z-40 lg:top-5">
      <div className="container">
        <div
          className={cn(
            "flex items-center justify-between",
            "min-h-[64px] rounded-[26px]",
            "border border-white/35 bg-white/45",
            "px-4 py-2",
            "shadow-[0_8px_30px_rgba(15,23,42,0.08)]",
            "backdrop-blur-xl supports-[backdrop-filter]:bg-white/35",
            "sm:min-h-[68px] sm:px-5",
            "lg:min-h-[74px] lg:px-6"
          )}
        >
          <Link
            href="/login"
            className="flex shrink-0 cursor-pointer items-center transition hover:opacity-85"
            aria-label="Primey HR Cloud"
          >
            <Image
              src="/hero logo.png"
              alt="Primey HR Cloud"
              width={1200}
              height={420}
              priority
              unoptimized
              className={cn(
                "h-auto w-auto object-contain",
                "max-w-[96px]",
                "sm:max-w-[108px]",
                "md:max-w-[118px]",
                "lg:max-w-[132px]",
                "xl:max-w-[142px]"
              )}
            />
          </Link>

          {/* Mobile */}
          <div className="flex items-center gap-2 lg:hidden">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={toggleLanguage}
              className={cn(
                "h-8 rounded-xl border-white/40",
                "bg-white/55 px-3 text-sm",
                "shadow-sm backdrop-blur-md",
                "hover:bg-white/70"
              )}
            >
              <Languages className="h-4 w-4" />
              <span>{isArabic ? "EN" : "عربي"}</span>
            </Button>

            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className={cn(
                    "h-8 w-8 rounded-xl",
                    "bg-white/40 backdrop-blur-md",
                    "hover:bg-white/60",
                    "lg:hidden"
                  )}
                  onClick={() => setIsOpen(!isOpen)}
                >
                  <Menu className="h-4 w-4" />
                </Button>
              </SheetTrigger>

              <SheetContent
                side={isArabic ? "right" : "left"}
                className={cn(
                  "flex flex-col justify-between",
                  "rounded-tl-2xl rounded-bl-2xl",
                  "border-white/30 bg-white/80",
                  "backdrop-blur-xl",
                  "data-[state=open]:duration-300"
                )}
              >
                <div>
                  <SheetHeader className={cn("mb-4", isArabic ? "mr-4" : "ml-4")}>
                    <SheetTitle className="flex items-center">
                      <Link
                        href="/login"
                        onClick={() => setIsOpen(false)}
                        className="flex cursor-pointer items-center transition hover:opacity-85"
                        aria-label="Primey HR Cloud"
                      >
                        <Image
                          src="/hero logo.png"
                          alt="Primey HR Cloud"
                          width={1200}
                          height={420}
                          priority
                          unoptimized
                          className="h-auto w-auto max-w-[118px] object-contain sm:max-w-[130px]"
                        />
                      </Link>
                    </SheetTitle>
                  </SheetHeader>

                  <div className="flex flex-col gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      className={cn(
                        "border-white/40 bg-white/60 text-base backdrop-blur-md hover:bg-white/75",
                        isArabic
                          ? "justify-end text-right"
                          : "justify-start text-left"
                      )}
                      onClick={toggleLanguage}
                    >
                      <Languages className="h-4 w-4" />
                      {isArabic ? "التبديل إلى الإنجليزية" : "Switch to Arabic"}
                    </Button>

                    {routeList.map(({ href, label }) => (
                      <Button
                        key={href}
                        onClick={() => setIsOpen(false)}
                        asChild
                        variant="ghost"
                        className={cn(
                          "text-base hover:bg-white/55",
                          isArabic
                            ? "justify-end text-right"
                            : "justify-start text-left"
                        )}
                      >
                        <Link href={href}>
                          {isArabic ? label.ar : label.en}
                        </Link>
                      </Button>
                    ))}
                  </div>
                </div>

                <SheetFooter
                  className={cn(
                    "flex-col justify-start sm:flex-col",
                    isArabic ? "items-end" : "items-start"
                  )}
                >
                  <Separator className="mb-2 bg-white/40" />
                  <ToggleTheme />
                </SheetFooter>
              </SheetContent>
            </Sheet>
          </div>

          {/* Desktop */}
          <NavigationMenu className="mx-auto hidden lg:block">
            <NavigationMenuList className="gap-1 xl:gap-2">
              <NavigationMenuItem>
                <NavigationMenuTrigger
                  className={cn(
                    "h-9 rounded-xl bg-transparent px-3",
                    "text-sm font-medium text-foreground",
                    "hover:bg-white/45",
                    "data-[state=open]:bg-white/55"
                  )}
                >
                  {isArabic ? "المنتجات" : "Products"}
                </NavigationMenuTrigger>

                <NavigationMenuContent className="border-white/30 bg-white/90 backdrop-blur-xl">
                  <div className="w-72 gap-4">
                    <ul className="flex flex-col">
                      {productList.map(({ title, description, icon }) => (
                        <li key={title.en}>
                          <Link
                            href="/"
                            className="flex items-center gap-4 rounded-md p-4 text-sm hover:bg-white/60"
                          >
                            <div className="bg-primary/15 ring-primary/10 flex size-8 items-center justify-center rounded-full p-2 ring-8">
                              <Icon
                                name={icon}
                                className="text-primary size-5 shrink-0"
                              />
                            </div>

                            <div className={isArabic ? "text-right" : "text-left"}>
                              <p className="text-foreground mb-1 leading-none font-semibold">
                                {isArabic ? title.ar : title.en}
                              </p>
                              <p className="text-muted-foreground line-clamp-2">
                                {isArabic ? description.ar : description.en}
                              </p>
                            </div>
                          </Link>
                        </li>
                      ))}
                    </ul>
                  </div>
                </NavigationMenuContent>
              </NavigationMenuItem>

              <NavigationMenuItem className="flex items-center gap-1 xl:gap-2">
                {routeList.map(({ href, label }) => (
                  <NavigationMenuLink
                    key={href}
                    asChild
                    className={cn(
                      navigationMenuTriggerStyle(),
                      "h-9 rounded-xl bg-transparent px-3 text-sm font-medium xl:px-4",
                      "hover:bg-white/45!"
                    )}
                  >
                    <Link href={href}>
                      {isArabic ? label.ar : label.en}
                    </Link>
                  </NavigationMenuLink>
                ))}
              </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>

          <div className="hidden items-center gap-2 lg:flex">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={toggleLanguage}
              className={cn(
                "h-8 rounded-xl border-white/40",
                "bg-white/55 px-3 text-sm",
                "shadow-sm backdrop-blur-md",
                "hover:bg-white/70"
              )}
            >
              <Languages className="h-4 w-4" />
              <span>{isArabic ? "EN" : "عربي"}</span>
            </Button>

            <div className="rounded-xl bg-white/40 p-1 backdrop-blur-md">
              <ToggleTheme />
            </div>

            <div className="flex items-center gap-1 xl:gap-2">
              <Button
                size="sm"
                variant="ghost"
                asChild
                className="h-9 rounded-xl px-4 text-sm hover:bg-white/45"
              >
                <Link href="/login">
                  {isArabic ? "تسجيل الدخول" : "Log in"}
                </Link>
              </Button>

              <Button
                size="sm"
                asChild
                className="h-9 rounded-xl px-4 text-sm shadow-sm xl:px-5"
              >
                <Link href="/register">
                  {isArabic ? "ابدأ الآن" : "Get Started"}
                  <ArrowIcon className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};