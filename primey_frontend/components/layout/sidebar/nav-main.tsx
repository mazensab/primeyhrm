"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";

import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";

import {
  ChevronLeft,
  ChevronRight,
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
  MessageCircle,
  Send,
  type LucideIcon,
} from "lucide-react";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

/* =====================================================
   TYPES
===================================================== */

type AppLocale = "ar" | "en";

type NavItem = {
  title: {
    ar: string;
    en: string;
  };
  href: string;
  icon?: LucideIcon;
  items?: NavItem[];
  newTab?: boolean;
  isNew?: boolean;
  isComing?: boolean;
  isDataBadge?: string;
  roles?: string[];
  apps?: string[];
};

type NavGroup = {
  title: {
    ar: string;
    en: string;
  };
  items: NavItem[];
};

type NavMainProps = {
  type: "system" | "company";
};

/* =====================================================
   SYSTEM NAV
===================================================== */

const systemNavItems: NavGroup[] = [
  {
    title: {
      ar: "لوحات النظام",
      en: "Dashboards",
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
        title: { ar: "واتساب", en: "WhatsApp" },
        href: "/system/whatsapp",
        icon: MessageCircle,
        items: [
          {
            title: { ar: "الرئيسية", en: "Overview" },
            href: "/system/whatsapp",
          },
          {
            title: { ar: "الإعدادات", en: "Settings" },
            href: "/system/whatsapp/settings",
          },
          {
            title: { ar: "السجل", en: "Logs" },
            href: "/system/whatsapp/logs",
          },
          {
            title: { ar: "القوالب", en: "Templates" },
            href: "/system/whatsapp/templates",
          },
          {
            title: { ar: "البث الجماعي", en: "Broadcasts" },
            href: "/system/whatsapp/broadcasts",
          },
        ],
      },
      {
        title: { ar: "الإعدادات", en: "Settings" },
        href: "/system/settings",
        icon: Settings,
      },
    ],
  },
];

/* =====================================================
   COMPANY NAV
===================================================== */

const companyNavItems: NavGroup[] = [
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
        title: { ar: "واتساب", en: "WhatsApp" },
        href: "/company/whatsapp",
        icon: Send,
        roles: ["owner", "admin", "hr"],
        items: [
          {
            title: { ar: "الرئيسية", en: "Overview" },
            href: "/company/whatsapp",
          },
          {
            title: { ar: "الإعدادات", en: "Settings" },
            href: "/company/whatsapp/settings",
          },
          {
            title: { ar: "السجل", en: "Logs" },
            href: "/company/whatsapp/logs",
          },
          {
            title: { ar: "القوالب", en: "Templates" },
            href: "/company/whatsapp/templates",
          },
        ],
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

function isItemActive(pathname: string, href: string) {
  if (href === "/system" || href === "/company") {
    return pathname === href;
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

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

/* =====================================================
   COMPONENT
===================================================== */

export function NavMain({ type }: NavMainProps) {
  const pathname = usePathname();
  const session = useAuth();

  const [locale, setLocale] = useState<AppLocale>("ar");

  const companyRole = (session?.role || "").toLowerCase();
  const enabledApps = Array.isArray(session?.subscription?.apps)
    ? session.subscription.apps.map((app: string) => String(app).toLowerCase())
    : [];

  useEffect(() => {
    const syncLocale = () => {
      setLocale(getStoredLocale());
    };

    syncLocale();

    window.addEventListener("primey-locale-changed", syncLocale);
    window.addEventListener("storage", syncLocale);

    return () => {
      window.removeEventListener("primey-locale-changed", syncLocale);
      window.removeEventListener("storage", syncLocale);
    };
  }, []);

  const isArabic = locale === "ar";
  const ChevronIcon = isArabic ? ChevronLeft : ChevronRight;

  const navItems = useMemo(() => {
    if (type === "system") {
      return systemNavItems;
    }

    return companyNavItems
      .map((group) => ({
        ...group,
        items: group.items.filter((item) => {
          const roleAllowed = hasRequiredRole(item.roles, companyRole);
          const appAllowed = hasRequiredApps(item.apps, enabledApps);
          return roleAllowed && appAllowed;
        }),
      }))
      .filter((group) => group.items.length > 0);
  }, [type, companyRole, enabledApps]);

  return (
    <>
      {navItems.map((nav) => (
        <SidebarGroup key={nav.title.en}>
          <SidebarGroupLabel>
            {isArabic ? nav.title.ar : nav.title.en}
          </SidebarGroupLabel>

          <SidebarGroupContent>
            <SidebarMenu>
              {nav.items.map((item) => {
                const Icon = item.icon;
                const itemTitle = isArabic ? item.title.ar : item.title.en;

                if (item.items?.length) {
                  return (
                    <SidebarMenuItem key={item.title.en}>
                      <Collapsible
                        defaultOpen={item.items.some((s) =>
                          isItemActive(pathname, s.href)
                        )}
                      >
                        <CollapsibleTrigger asChild>
                          <SidebarMenuButton
                            tooltip={itemTitle}
                            isActive={
                              isItemActive(pathname, item.href) ||
                              item.items.some((s) => isItemActive(pathname, s.href))
                            }
                          >
                            <div
                              className={`flex w-full items-center gap-2 ${
                                isArabic ? "flex-row-reverse text-right" : "flex-row text-left"
                              }`}
                            >
                              {Icon && <Icon className="shrink-0" />}
                              <span className="flex-1">{itemTitle}</span>
                              <ChevronIcon className="shrink-0" />
                            </div>     
                         </SidebarMenuButton>
                        </CollapsibleTrigger>

                        <CollapsibleContent>
                          <SidebarMenuSub>
                            {item.items.map((sub) => (
                              <SidebarMenuSubItem key={sub.title.en}>
                                <SidebarMenuSubButton
                                  asChild
                                  isActive={isItemActive(pathname, sub.href)}
                                >
                                  <Link href={sub.href}>
                                    <span>
                                      {isArabic ? sub.title.ar : sub.title.en}
                                    </span>
                                  </Link>
                                </SidebarMenuSubButton>
                              </SidebarMenuSubItem>
                            ))}
                          </SidebarMenuSub>
                        </CollapsibleContent>
                      </Collapsible>
                    </SidebarMenuItem>
                  );
                }

                return (
                  <SidebarMenuItem key={item.title.en}>
                    <SidebarMenuButton
                      tooltip={itemTitle}
                      isActive={isItemActive(pathname, item.href)}
                      asChild
                    >
                      <Link
                        href={item.href}
                        target={item.newTab ? "_blank" : undefined}
                        className={`flex w-full items-center gap-2 ${
                          isArabic ? "flex-row-reverse text-right" : "flex-row text-left"
                        }`}
                      >
                        {Icon && <Icon className="shrink-0" />}
                        <span className="flex-1">{itemTitle}</span>
                      </Link>                      
                    </SidebarMenuButton>

                    {item.isNew && (
                      <SidebarMenuBadge>
                        {isArabic ? "جديد" : "New"}
                      </SidebarMenuBadge>
                    )}
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      ))}
    </>
  );
}