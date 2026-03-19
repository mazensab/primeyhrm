"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";

import {
  BadgeCheck,
  Bell,
  ChevronLeftIcon,
  ChevronRightIcon,
  CreditCard,
  LogOut,
  Sparkles,
} from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { Progress } from "@/components/ui/progress";

type AppLocale = "ar" | "en";

export default function UserMenu() {
  const router = useRouter();
  const session = useAuth();

  const [loading, setLoading] = useState(false);
  const [locale, setLocale] = useState<AppLocale>("ar");

  const isArabic = locale === "ar";

  useEffect(() => {
    try {
      const savedLocale =
        typeof window !== "undefined"
          ? (window.localStorage.getItem("primey-locale") as AppLocale | null)
          : null;

      setLocale(savedLocale === "en" ? "en" : "ar");
    } catch (error) {
      console.error("User menu locale initialization error:", error);
    }
  }, []);

  const userName = session?.user?.full_name || session?.user?.username || (isArabic ? "مستخدم" : "User");

  const userEmail = session?.user?.email || "";

  const avatarFallback = userName?.charAt(0)?.toUpperCase() || (isArabic ? "م" : "U");

  const daysRemaining = session?.subscription?.days_remaining;

  const subscriptionRemainingText = useMemo(() => {
    if (typeof daysRemaining !== "number") {
      return isArabic ? "مدة الاشتراك غير متوفرة" : "Subscription duration unavailable";
    }

    if (daysRemaining < 0) {
      return isArabic ? "انتهى الاشتراك" : "Subscription has expired";
    }

    if (daysRemaining === 0) {
      return isArabic ? "ينتهي الاشتراك اليوم" : "Subscription ends today";
    }

    if (daysRemaining === 1) {
      return isArabic ? "متبقي يوم واحد على الاشتراك" : "1 day remaining in subscription";
    }

    return isArabic
      ? `متبقي ${daysRemaining} يوم على الاشتراك`
      : `${daysRemaining} days remaining in subscription`;
  }, [daysRemaining, isArabic]);

  const progressValue = useMemo(() => {
    if (typeof daysRemaining !== "number") return 0;
    if (daysRemaining <= 0) return 0;
    if (daysRemaining >= 365) return 100;

    return Math.max(0, Math.min(100, Math.round((daysRemaining / 365) * 100)));
  }, [daysRemaining]);

  const getCSRFToken = () => {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : "";
  };

  const handleLogout = async () => {
    if (loading) return;
    setLoading(true);

    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/csrf/`, {
        method: "GET",
        credentials: "include",
      });

      const csrfToken = getCSRFToken();

      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/logout/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
      });
    } catch {
      // Force client logout anyway
    }

    localStorage.setItem("primey_logout", Date.now().toString());
    router.replace("/login");
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Avatar>
          {session?.user?.avatar ? (
            <AvatarImage
              src={session.user.avatar}
              alt={userName}
              referrerPolicy="no-referrer"
            />
          ) : null}
          <AvatarFallback className="rounded-lg">{avatarFallback}</AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        className="w-(--radix-dropdown-menu-trigger-width) min-w-60"
        align={isArabic ? "start" : "end"}
      >
        <DropdownMenuLabel className="p-0">
          <div className={`flex items-center gap-2 px-1 py-1.5 text-sm ${isArabic ? "text-right" : "text-left"}`}>
            <Avatar>
              {session?.user?.avatar ? (
                <AvatarImage
                  src={session.user.avatar}
                  alt={userName}
                  referrerPolicy="no-referrer"
                />
              ) : null}
              <AvatarFallback className="rounded-lg">{avatarFallback}</AvatarFallback>
            </Avatar>

            <div className={`grid flex-1 text-sm leading-tight ${isArabic ? "text-right" : "text-left"}`}>
              <span className="truncate font-semibold">{userName}</span>
              <span className="text-muted-foreground truncate text-xs">{userEmail}</span>
            </div>
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <DropdownMenuGroup>
          <DropdownMenuItem asChild>
            <Link href="https://shadcnuikit.com/pricing" target="_blank">
              <Sparkles />
              {isArabic ? "الترقية إلى النسخة الاحترافية" : "Upgrade to Pro"}
            </Link>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuGroup>
          <DropdownMenuItem onClick={() => router.push("/company/profile")}>
            <BadgeCheck />
            {isArabic ? "الحساب" : "Account"}
          </DropdownMenuItem>

          <DropdownMenuItem onClick={() => router.push("/company/billing")}>
            <CreditCard />
            {isArabic ? "الفوترة" : "Billing"}
          </DropdownMenuItem>

          <DropdownMenuItem asChild>
            <Link href="/company/notifications">
              <Bell />
              {isArabic ? "الإشعارات" : "Notifications"}
            </Link>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={handleLogout}
          disabled={loading}
          className="cursor-pointer text-red-600 focus:text-red-600"
        >
          <LogOut />
          {loading ? (isArabic ? "جارٍ تسجيل الخروج..." : "Signing out...") : isArabic ? "تسجيل الخروج" : "Log out"}
        </DropdownMenuItem>

        <div className="bg-muted mt-1.5 rounded-md border">
          <div className="space-y-3 p-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">
                {isArabic ? "الاشتراك" : "Subscription"}
              </h4>

              <div className="text-muted-foreground flex items-center text-sm">
                {isArabic ? (
                  <>
                    <ChevronLeftIcon className="ml-1 h-4 w-4" />
                    <span>
                      {typeof daysRemaining === "number"
                        ? `${Math.max(daysRemaining, 0)} ${isArabic ? "ي" : "d"}`
                        : "--"}
                    </span>
                  </>
                ) : (
                  <>
                    <span>
                      {typeof daysRemaining === "number"
                        ? `${Math.max(daysRemaining, 0)}d`
                        : "--"}
                    </span>
                    <ChevronRightIcon className="ml-1 h-4 w-4" />
                  </>
                )}
              </div>
            </div>

            <Progress value={progressValue} indicatorColor="bg-primary" />

            <div className={`text-muted-foreground flex items-center text-sm ${isArabic ? "text-right" : "text-left"}`}>
              {subscriptionRemainingText}
            </div>
          </div>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}