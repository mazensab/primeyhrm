"use client"

// ============================================================
// 📂 الملف: components/whatsapp/chat-list-item.tsx
// 🟢 Mham Cloud - WhatsApp Chat List Item
// ------------------------------------------------------------
// ✅ إصلاح التصدير الخاطئ الذي جعل TypeScript يقرأ المكوّن
//    على أنه ChatListItemDropdownProps
// ✅ جعل ChatListItem يستقبل:
//    conversation / active / onSelect
// ✅ إزالة تمرير children إلى ChatListItemDropdown
// ✅ الحفاظ على نفس شكل العنصر الحالي
// ============================================================

import { useEffect, useState } from "react"
import { CheckCheck } from "lucide-react"

import ChatListItemDropdown from "./chat-list-item-dropdown"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"

type LocaleKey = "ar" | "en"
type Direction = "rtl" | "ltr"

type ConversationItem = {
  id: number
  title: string
  avatar?: string
  preview: string
  unreadCount: number
  lastMessageAt: string
  isResolved?: boolean
}

type ChatListItemProps = {
  conversation: ConversationItem
  active?: boolean
  onSelect?: (conversationId: number) => void
}

function getAvatarFallback(name: string) {
  const clean = (name || "").trim()
  if (!clean) return "NA"

  const parts = clean.split(/\s+/).filter(Boolean)
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase()
  }

  return `${parts[0][0] ?? ""}${parts[1][0] ?? ""}`.toUpperCase()
}

function getHtmlMeta(): { locale: LocaleKey; direction: Direction } {
  if (typeof document === "undefined") {
    return {
      locale: "en",
      direction: "ltr",
    }
  }

  const html = document.documentElement
  const lang = (html.lang || "en").toLowerCase()
  const dir = (html.dir || "ltr").toLowerCase()

  return {
    locale: lang.startsWith("ar") ? "ar" : "en",
    direction: dir === "rtl" ? "rtl" : "ltr",
  }
}

function normalizeEnglishDigits(value: string | number): string {
  const raw = String(value ?? "").trim()
  if (!raw) return ""

  const map: Record<string, string> = {
    "٠": "0",
    "١": "1",
    "٢": "2",
    "٣": "3",
    "٤": "4",
    "٥": "5",
    "٦": "6",
    "٧": "7",
    "٨": "8",
    "٩": "9",
    "۰": "0",
    "۱": "1",
    "۲": "2",
    "۳": "3",
    "۴": "4",
    "۵": "5",
    "۶": "6",
    "۷": "7",
    "۸": "8",
    "۹": "9",
  }

  return raw.replace(/[٠-٩۰-۹]/g, (char) => map[char] ?? char)
}

export default function ChatListItem({
  conversation,
  active = false,
  onSelect,
}: ChatListItemProps) {
  const [locale, setLocale] = useState<LocaleKey>("en")
  const [direction, setDirection] = useState<Direction>("ltr")

  useEffect(() => {
    const syncMeta = () => {
      const next = getHtmlMeta()
      setLocale(next.locale)
      setDirection(next.direction)
    }

    syncMeta()

    const observer = new MutationObserver(() => {
      syncMeta()
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    return () => {
      observer.disconnect()
    }
  }, [])

  const isArabic = locale === "ar"
  const safeLastMessageAt = normalizeEnglishDigits(conversation.lastMessageAt)
  const safeUnreadCount =
    conversation.unreadCount > 99
      ? "99+"
      : normalizeEnglishDigits(conversation.unreadCount)

  return (
    <div
      dir="ltr"
      onClick={() => onSelect?.(conversation.id)}
      className={cn(
        "group relative flex min-w-0 cursor-pointer items-center gap-4 px-6 py-4 transition-colors",
        active ? "bg-muted" : "hover:bg-muted/60"
      )}
    >
      <div className="relative shrink-0">
        <Avatar className="h-11 w-11">
          <AvatarImage src={conversation.avatar} alt={conversation.title} />
          <AvatarFallback className="text-[12px] font-medium">
            {getAvatarFallback(conversation.title)}
          </AvatarFallback>
        </Avatar>

        <span className="absolute bottom-0.5 right-0.5 h-2.5 w-2.5 rounded-full border-2 border-background bg-emerald-500" />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 items-start justify-between gap-3">
          <span
            dir={direction}
            className={cn(
              "min-w-0 flex-1 truncate text-[15px] font-semibold leading-6",
              isArabic ? "text-right" : "text-left"
            )}
          >
            {conversation.title}
          </span>

          <span
            dir="ltr"
            className="shrink-0 whitespace-nowrap text-[12px] leading-6 text-muted-foreground"
          >
            {safeLastMessageAt}
          </span>
        </div>

        <div className="mt-0.5 flex min-w-0 items-center gap-2">
          <CheckCheck className="h-4 w-4 shrink-0 text-emerald-500" />

          <span
            dir={direction}
            className={cn(
              "min-w-0 flex-1 truncate text-[13px] text-muted-foreground",
              isArabic ? "text-right" : "text-left"
            )}
          >
            {conversation.preview}
          </span>

          {conversation.unreadCount > 0 ? (
            <span
              dir="ltr"
              className="ms-auto inline-flex h-6 min-w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500 px-1.5 text-[11px] font-semibold text-white"
            >
              {safeUnreadCount}
            </span>
          ) : null}
        </div>
      </div>

      <div
        onClick={(event) => event.stopPropagation()}
        className={cn(
          "absolute inset-y-0 right-0 flex items-center px-4 opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-focus-within:opacity-100",
          active
            ? "bg-gradient-to-l from-muted via-muted/95 to-transparent"
            : "bg-gradient-to-l from-background via-background/95 to-transparent"
        )}
      >
        <ChatListItemDropdown />
      </div>
    </div>
  )
}