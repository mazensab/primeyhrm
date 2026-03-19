"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  CommandIcon,
  SearchIcon,
  Home,
  Building2,
  CreditCard,
  FileText,
  Package,
  BadgePercent,
  Settings,
  Users,
  CalendarDays,
  Clock3,
  Wallet,
  UserCog,
  BarChart3,
  Fingerprint,
  type LucideIcon,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { DialogHeader, DialogTitle } from "@/components/ui/dialog";

/* =====================================================
   TYPES
===================================================== */

type AppLocale = "ar" | "en";

type SearchItem = {
  title: {
    ar: string;
    en: string;
  };
  href: string;
  icon?: LucideIcon;
  roles?: string[];
  apps?: string[];
};

type SearchGroup = {
  title: {
    ar: string;
    en: string;
  };
  items: SearchItem[];
};

/* =====================================================
   STATIC SEARCH DATA
===================================================== */

const systemSearchItems: SearchGroup[] = [
  {
    title: {
      ar: "لوحات النظام",
      en: "System Dashboards",
    },
    items: [
      {
        title: { ar: "الرئيسية", en: "Home" },
        href: "/system",
        icon: Home,
      },
      {
        title: { ar: "الشركات", en: "Companies" },
        href: "/system/companies",
        icon: Building2,
      },
      {
        title: { ar: "الاشتراكات", en: "Subscriptions" },
        href: "/system/subscriptions",
        icon: Package,
      },
      {
        title: { ar: "الباقات", en: "Plans" },
        href: "/system/plans",
        icon: Package,
      },
      {
        title: { ar: "المدفوعات", en: "Payments" },
        href: "/system/payments",
        icon: CreditCard,
      },
      {
        title: { ar: "الفواتير", en: "Invoices" },
        href: "/system/invoices",
        icon: FileText,
      },
      {
        title: { ar: "الخصومات", en: "Discounts" },
        href: "/system/discounts",
        icon: BadgePercent,
      },
      {
        title: { ar: "المستخدمون", en: "Users" },
        href: "/system/users",
        icon: Users,
      },
      {
        title: { ar: "الإعدادات", en: "Settings" },
        href: "/system/settings",
        icon: Settings,
      },
    ],
  },
];

const companySearchItems: SearchGroup[] = [
  {
    title: {
      ar: "الشركة",
      en: "Company",
    },
    items: [
      {
        title: { ar: "الرئيسية", en: "Home" },
        href: "/company",
        icon: Home,
      },
      {
        title: { ar: "الموظفون", en: "Employees" },
        href: "/company/employees",
        icon: Users,
        apps: ["employee"],
        roles: ["owner", "admin", "hr"],
      },
      {
        title: { ar: "الحضور", en: "Attendance" },
        href: "/company/attendance",
        icon: Clock3,
        apps: ["attendance"],
        roles: ["owner", "admin", "hr"],
      },
      {
        title: { ar: "الإجازات", en: "Leaves" },
        href: "/company/leaves",
        icon: CalendarDays,
        apps: ["leave"],
        roles: ["owner", "admin", "hr"],
      },
      {
        title: { ar: "الرواتب", en: "Payroll" },
        href: "/company/payroll",
        icon: Wallet,
        apps: ["payroll"],
        roles: ["owner", "admin"],
      },
      {
        title: { ar: "الأداء", en: "Performance" },
        href: "/company/performance",
        icon: BarChart3,
        apps: ["performance"],
        roles: ["owner", "admin", "hr"],
      },
      {
        title: { ar: "بيو تايم", en: "Biotime" },
        href: "/company/biotime",
        icon: Fingerprint,
        apps: ["biotime"],
        roles: ["owner", "admin", "hr"],
      },
      {
        title: { ar: "مستخدمو الشركة", en: "Company Users" },
        href: "/company/users",
        icon: UserCog,
        roles: ["owner", "admin"],
      },
      {
        title: { ar: "الإعدادات", en: "Settings" },
        href: "/company/settings",
        icon: Settings,
        roles: ["owner", "admin"],
      },
    ],
  },
];

/* =====================================================
   HELPERS
===================================================== */

function hasRequiredRole(
  itemRoles: string[] | undefined,
  currentRole: string
) {
  if (!itemRoles || itemRoles.length === 0) return true;
  return itemRoles.includes(currentRole);
}

function hasRequiredApps(
  itemApps: string[] | undefined,
  enabledApps: string[]
) {
  if (!itemApps || itemApps.length === 0) return true;
  return itemApps.some((app) => enabledApps.includes(app));
}

/* =====================================================
   COMPONENT
===================================================== */

export default function Search() {
  const [open, setOpen] = useState(false);
  const [locale, setLocale] = useState<AppLocale>("ar");

  const router = useRouter();
  const pathname = usePathname();
  const session = useAuth();

  const companyRole = (session?.role || "").toLowerCase();
  const enabledApps = Array.isArray(session?.subscription?.apps)
    ? session.subscription.apps.map((app: string) => String(app).toLowerCase())
    : [];

  const isArabic = locale === "ar";

  useEffect(() => {
    try {
      const savedLocale =
        typeof window !== "undefined"
          ? (window.localStorage.getItem("primey-locale") as AppLocale | null)
          : null;

      setLocale(savedLocale === "en" ? "en" : "ar");
    } catch (error) {
      console.error("Search locale initialization error:", error);
    }
  }, []);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const searchItems = useMemo<SearchGroup[]>(() => {
    if (pathname?.startsWith("/company")) {
      return companySearchItems
        .map((group) => ({
          ...group,
          items: group.items.filter((item) => {
            const roleAllowed = hasRequiredRole(item.roles, companyRole);
            const appAllowed = hasRequiredApps(item.apps, enabledApps);
            return roleAllowed && appAllowed;
          }),
        }))
        .filter((group) => group.items.length > 0);
    }

    if (pathname?.startsWith("/system")) {
      return systemSearchItems;
    }

    return [];
  }, [pathname, companyRole, enabledApps]);

  return (
    <div className="lg:flex-1">
      <div className="relative hidden max-w-sm flex-1 lg:block">
        <SearchIcon
          className={`text-muted-foreground absolute top-1/2 h-4 w-4 -translate-y-1/2 ${
            isArabic ? "right-3" : "left-3"
          }`}
        />

        <Input
          className={`h-9 w-full cursor-pointer rounded-md border text-sm shadow-xs ${
            isArabic ? "pl-4 pr-10 text-right" : "pr-4 pl-10 text-left"
          }`}
          placeholder={isArabic ? "ابحث..." : "Search..."}
          type="search"
          onFocus={() => setOpen(true)}
          readOnly
        />

        <div
          className={`absolute top-1/2 hidden -translate-y-1/2 items-center gap-0.5 rounded-sm bg-zinc-200 p-1 font-mono text-xs font-medium sm:flex dark:bg-neutral-700 ${
            isArabic ? "left-2" : "right-2"
          }`}
        >
          <CommandIcon className="size-3" />
          <span>k</span>
        </div>
      </div>

      <div className="block lg:hidden">
        <Button size="icon" variant="ghost" onClick={() => setOpen(true)}>
          <SearchIcon />
        </Button>
      </div>

      <CommandDialog open={open} onOpenChange={setOpen}>
        <VisuallyHidden>
          <DialogHeader>
            <DialogTitle>
              {isArabic ? "بحث التنقل" : "Search navigation"}
            </DialogTitle>
          </DialogHeader>
        </VisuallyHidden>

        <CommandInput
          placeholder={
            isArabic ? "اكتب أمرًا أو ابحث..." : "Type a command or search..."
          }
        />

        <CommandList>
          <CommandEmpty>
            {isArabic ? "لم يتم العثور على نتائج." : "No results found."}
          </CommandEmpty>

          {searchItems.map((group) => (
            <React.Fragment key={`${group.title.en}-${group.title.ar}`}>
              <CommandGroup heading={isArabic ? group.title.ar : group.title.en}>
                {(group.items || []).map((item) => (
                  <CommandItem
                    key={item.href}
                    onSelect={() => {
                      setOpen(false);
                      router.push(item.href);
                    }}
                    className={isArabic ? "text-right" : "text-left"}
                  >
                    {item.icon && (
                      <item.icon
                        className={isArabic ? "ml-2 h-4 w-4" : "mr-2 h-4 w-4"}
                      />
                    )}
                    <span>{isArabic ? item.title.ar : item.title.en}</span>
                  </CommandItem>
                ))}
              </CommandGroup>

              <CommandSeparator />
            </React.Fragment>
          ))}
        </CommandList>
      </CommandDialog>
    </div>
  );
}