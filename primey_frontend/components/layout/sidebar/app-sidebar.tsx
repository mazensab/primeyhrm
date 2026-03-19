"use client";

import * as React from "react";
import { useEffect, useRef, useState } from "react";
import {
  ChevronsUpDown,
  ShoppingBagIcon,
  UserCircle2Icon,
  Building2,
  Shield,
} from "lucide-react";
import { PlusIcon } from "@radix-ui/react-icons";
import { usePathname } from "next/navigation";
import { useIsTablet } from "@/hooks/use-mobile";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { NavMain } from "@/components/layout/sidebar/nav-main";
import { NavUser } from "@/components/layout/sidebar/nav-user";
import { ScrollArea } from "@/components/ui/scroll-area";
import Logo from "@/components/layout/logo";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type AppLocale = "ar" | "en";

type AppSidebarProps = React.ComponentProps<typeof Sidebar> & {
  type: "system" | "company";
};

export function AppSidebar({ type, ...props }: AppSidebarProps) {
  const pathname = usePathname();
  const { setOpen, setOpenMobile, isMobile, dir } = useSidebar();
  const isTablet = useIsTablet();

  const [locale, setLocale] = useState<AppLocale>("ar");
  const hasInitializedResponsiveState = useRef(false);

  useEffect(() => {
    if (isMobile) setOpenMobile(false);
  }, [pathname, isMobile, setOpenMobile]);

  // ======================================================
  // ✅ ضبط أولي فقط حسب المقاس
  // لا نعيد فرض open في كل مرة حتى لا يتعطل زر التصغير
  // ======================================================
  useEffect(() => {
    if (!hasInitializedResponsiveState.current) {
      setOpen(!isTablet);
      hasInitializedResponsiveState.current = true;
    }
  }, [isTablet, setOpen]);

  useEffect(() => {
    try {
      const savedLocale =
        typeof window !== "undefined"
          ? (window.localStorage.getItem("primey-locale") as AppLocale | null)
          : null;

      setLocale(savedLocale === "en" ? "en" : "ar");
    } catch (error) {
      console.error("Sidebar locale initialization error:", error);
    }
  }, []);

  const isArabic = locale === "ar";
  const isSystem = type === "system";

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton className="hover:text-foreground h-10 group-data-[collapsible=icon]:px-0!">
                  <Logo />
                  <ChevronsUpDown className="ms-auto group-data-[collapsible=icon]:hidden" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>

              <DropdownMenuContent
                className="mt-4 w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
                side={isMobile ? "bottom" : dir === "rtl" ? "left" : "right"}
                align="end"
                sideOffset={4}
              >
                <DropdownMenuLabel className={isArabic ? "text-right" : "text-left"}>
                  {isSystem
                    ? isArabic
                      ? "مساحة عمل النظام"
                      : "System Workspace"
                    : isArabic
                      ? "مساحة عمل الشركة"
                      : "Company Workspace"}
                </DropdownMenuLabel>

                <DropdownMenuSeparator />

                {isSystem ? (
                  <>
                    <DropdownMenuItem className="flex items-center gap-3">
                      <div className="flex size-8 items-center justify-center rounded-md border">
                        <Shield className="text-muted-foreground size-4" />
                      </div>
                      <div className={`flex flex-col ${isArabic ? "text-right" : "text-left"}`}>
                        <span className="text-sm font-medium">
                          {isArabic ? "لوحة النظام" : "System Dashboard"}
                        </span>
                        <span className="text-xs text-green-700">
                          {isArabic ? "نشط" : "Active"}
                        </span>
                      </div>
                    </DropdownMenuItem>

                    <DropdownMenuItem className="flex items-center gap-3">
                      <div className="flex size-8 items-center justify-center rounded-md border">
                        <ShoppingBagIcon className="text-muted-foreground size-4" />
                      </div>
                      <div className={`flex flex-col ${isArabic ? "text-right" : "text-left"}`}>
                        <span className="text-sm font-medium">
                          {isArabic ? "إدارة المنصة" : "Platform Management"}
                        </span>
                        <span className="text-muted-foreground text-xs">
                          {isArabic ? "منطقة الإدارة" : "Admin Area"}
                        </span>
                      </div>
                    </DropdownMenuItem>
                  </>
                ) : (
                  <>
                    <DropdownMenuItem className="flex items-center gap-3">
                      <div className="flex size-8 items-center justify-center rounded-md border">
                        <Building2 className="text-muted-foreground size-4" />
                      </div>
                      <div className={`flex flex-col ${isArabic ? "text-right" : "text-left"}`}>
                        <span className="text-sm font-medium">
                          {isArabic ? "لوحة الشركة" : "Company Dashboard"}
                        </span>
                        <span className="text-xs text-green-700">
                          {isArabic ? "نشط" : "Active"}
                        </span>
                      </div>
                    </DropdownMenuItem>

                    <DropdownMenuItem className="flex items-center gap-3">
                      <div className="flex size-8 items-center justify-center rounded-md border">
                        <UserCircle2Icon className="text-muted-foreground size-4" />
                      </div>
                      <div className={`flex flex-col ${isArabic ? "text-right" : "text-left"}`}>
                        <span className="text-sm font-medium">
                          {isArabic ? "مساحة الموظفين" : "Employee Workspace"}
                        </span>
                        <span className="text-muted-foreground text-xs">
                          {isArabic ? "منطقة الشركة" : "Company Area"}
                        </span>
                      </div>
                    </DropdownMenuItem>
                  </>
                )}

                <DropdownMenuSeparator />

                {isSystem ? (
                  <button
                    type="button"
                    disabled
                    className="inline-flex h-9 w-full items-center justify-center gap-2 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground opacity-50"
                  >
                    <PlusIcon />
                    {isArabic ? "مساحة عمل جديدة" : "New Workspace"}
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled
                    className="inline-flex h-9 w-full items-center justify-center gap-2 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground opacity-50"
                  >
                    <PlusIcon />
                    {isArabic ? "تطبيقات الشركة" : "Company Apps"}
                  </button>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <ScrollArea className="h-full">
          <NavMain type={type} />
        </ScrollArea>
      </SidebarContent>

      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  );
}