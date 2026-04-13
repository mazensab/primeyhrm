"use client";

import { BellIcon, CheckCheckIcon, ClockIcon } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useIsMobile } from "@/hooks/use-mobile";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";

/* =========================================================
   🌍 Locale Types
========================================================= */
type AppLocale = "ar" | "en";

interface Notification {
  id: number;
  title: string;
  message: string;
  severity: string;
  notification_type: string;
  is_read: boolean;
  link?: string | null;
  created_at: string;
}

/* =========================================================
   🔗 Helpers - Resolve API & WS Base Safely
========================================================= */
function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

function resolveApiBase(): string {
  const envApi = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (envApi) {
    return trimTrailingSlash(envApi);
  }

  if (typeof window !== "undefined") {
    return trimTrailingSlash(window.location.origin);
  }

  return "";
}

function resolveWsBase(): string {
  const envWs = process.env.NEXT_PUBLIC_WS_URL?.trim();

  if (envWs) {
    return trimTrailingSlash(envWs);
  }

  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}`;
  }

  return "";
}

const Notifications = () => {
  const isMobile = useIsMobile();
  const pathname = usePathname();
  const router = useRouter();

  const [locale, setLocale] = useState<AppLocale>("ar");
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [markingAll, setMarkingAll] = useState<boolean>(false);

  const socketRef = useRef<WebSocket | null>(null);

  const isArabic = locale === "ar";

  /* =========================================================
     🧭 Detect Current Scope
  ========================================================= */
  const isCompanyScope = useMemo(() => {
    return pathname?.startsWith("/company");
  }, [pathname]);

  const apiRoot = useMemo(() => resolveApiBase(), []);
  const wsRoot = useMemo(() => resolveWsBase(), []);

  const apiBase = useMemo(() => {
    if (!apiRoot) return "";

    return isCompanyScope
      ? `${apiRoot}/api/company/notifications`
      : `${apiRoot}/api/system/notifications`;
  }, [apiRoot, isCompanyScope]);

  const wsNotificationsUrl = useMemo(() => {
    if (!wsRoot) return "";

    // حالياً قناة النظام تعمل على مستوى المستخدم الحالي
    return `${wsRoot}/ws/system/notifications/`;
  }, [wsRoot]);

  const pageHref = isCompanyScope
    ? "/company/notifications"
    : "/system/notifications";

  /* =========================================================
     🍪 Load Locale from localStorage
  ========================================================= */
  useEffect(() => {
    try {
      const savedLocale =
        typeof window !== "undefined"
          ? (window.localStorage.getItem("primey-locale") as AppLocale | null)
          : null;

      setLocale(savedLocale === "en" ? "en" : "ar");
    } catch (error) {
      console.error("Notifications locale initialization error", error);
    }
  }, []);

  /* =========================================================
     📥 Load Notifications from Backend
  ========================================================= */
  async function loadNotifications() {
    if (!apiBase) {
      setNotifications([]);
      setUnreadCount(0);
      return;
    }

    try {
      setLoading(true);

      const res = await fetch(`${apiBase}/`, {
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        throw new Error(`Failed to load notifications: ${res.status}`);
      }

      const data = await res.json();

      setNotifications(Array.isArray(data.results) ? data.results : []);
      setUnreadCount(Number(data.unread_count || 0));
    } catch (err) {
      console.error("Notifications load error", err);
      setNotifications([]);
      setUnreadCount(0);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadNotifications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiBase]);

  /* =========================================================
     🔔 WebSocket Realtime Notifications
  ========================================================= */
  useEffect(() => {
    if (!wsNotificationsUrl) return;

    let socket: WebSocket | null = null;

    try {
      socket = new WebSocket(wsNotificationsUrl);
      socketRef.current = socket;

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as Notification;

          setNotifications((prev) => [payload, ...prev]);
          setUnreadCount((prev) => prev + 1);
        } catch (err) {
          console.error("Realtime notification parse error", err);
        }
      };

      socket.onerror = (error) => {
        console.error("Notification socket error", error);
      };

      socket.onclose = () => {
        console.log("Notification socket closed");
      };
    } catch (error) {
      console.error("Notification socket initialization error", error);
    }

    return () => {
      try {
        socketRef.current?.close();
      } catch (error) {
        console.error("Notification socket close error", error);
      } finally {
        socketRef.current = null;
      }
    };
  }, [wsNotificationsUrl]);

  /* =========================================================
     ✅ Mark Single Notification as Read
  ========================================================= */
  async function markAsRead(id: number) {
    if (!apiBase) return;

    try {
      const res = await fetch(`${apiBase}/read/${id}/`, {
        method: "POST",
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error(`Failed to mark notification as read: ${res.status}`);
      }

      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );

      setUnreadCount((prev) => (prev > 0 ? prev - 1 : 0));
    } catch (err) {
      console.error("Mark read error", err);
    }
  }

  /* =========================================================
     ✅ Mark All Notifications as Read
  ========================================================= */
  async function markAllAsRead() {
    if (unreadCount <= 0 || !apiBase) return;

    try {
      setMarkingAll(true);

      const res = await fetch(`${apiBase}/read-all/`, {
        method: "POST",
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error(`Failed to mark all notifications as read: ${res.status}`);
      }

      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error("Mark all read error", err);
    } finally {
      setMarkingAll(false);
    }
  }

  /* =========================================================
     🕒 Format Date by Locale
  ========================================================= */
  function formatNotificationDate(value: string) {
    try {
      return new Date(value).toLocaleString(isArabic ? "ar-SA" : "en-US");
    } catch {
      return value;
    }
  }

  /* =========================================================
     🖱️ Handle Notification Click
  ========================================================= */
  async function handleNotificationClick(item: Notification) {
    if (!item.is_read) {
      await markAsRead(item.id);
    }

    if (item.link) {
      router.push(item.link);
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button size="icon-sm" variant="ghost" className="relative">
          <BellIcon />

          {unreadCount > 0 && (
            <span className="bg-destructive absolute end-0.5 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full px-1 text-[10px] text-white">
              {unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align={isMobile ? "center" : isArabic ? "start" : "end"}
        className="ms-4 w-80 p-0"
      >
        <DropdownMenuLabel className="bg-background dark:bg-muted sticky top-0 z-10 p-0">
          <div className="flex items-center justify-between border-b px-4 py-4">
            <div className="font-medium">
              {isArabic ? "الإشعارات" : "Notifications"}
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={markAllAsRead}
                disabled={unreadCount <= 0 || markingAll}
                className="text-muted-foreground hover:text-foreground inline-flex items-center gap-1 text-xs transition disabled:cursor-not-allowed disabled:opacity-50"
              >
                <CheckCheckIcon className="size-3.5" />
                {isArabic ? "قراءة الكل" : "Read all"}
              </button>

              <Link
                href={pageHref}
                className="text-muted-foreground hover:text-foreground text-xs transition"
              >
                {isArabic ? "عرض الكل" : "View all"}
              </Link>
            </div>
          </div>
        </DropdownMenuLabel>

        <ScrollArea className="h-[350px]">
          {loading && (
            <div className="text-muted-foreground p-6 text-center text-sm">
              {isArabic ? "جاري تحميل الإشعارات..." : "Loading notifications..."}
            </div>
          )}

          {!loading && notifications.length === 0 && (
            <div className="text-muted-foreground p-6 text-center text-sm">
              {isArabic ? "لا توجد إشعارات" : "No notifications"}
            </div>
          )}

          {!loading &&
            notifications.map((item) => (
              <DropdownMenuItem
                key={item.id}
                onClick={() => handleNotificationClick(item)}
                className="group flex cursor-pointer items-start gap-9 rounded-none border-b px-4 py-3"
              >
                <div className="flex flex-1 items-start gap-2">
                  <div className="flex-none">
                    <Avatar className="size-8">
                      <AvatarFallback>
                        {item.title?.charAt(0) || (isArabic ? "إ" : "N")}
                      </AvatarFallback>
                    </Avatar>
                  </div>

                  <div className="flex flex-1 flex-col gap-1">
                    <div className="truncate text-sm font-medium">
                      {item.title}
                    </div>

                    <div className="text-muted-foreground line-clamp-1 text-xs">
                      {item.message}
                    </div>

                    <div className="text-muted-foreground flex items-center gap-1 text-xs">
                      <ClockIcon className="size-3" />
                      {formatNotificationDate(item.created_at)}
                    </div>
                  </div>
                </div>

                {!item.is_read && (
                  <div className="flex-0">
                    <span className="bg-destructive/80 block size-2 rounded-full border" />
                  </div>
                )}
              </DropdownMenuItem>
            ))}
        </ScrollArea>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default Notifications;