"use client"

// ============================================================
// 📂 الملف: components/whatsapp/chat-list.tsx
// 🟢 Mham Cloud - WhatsApp Chat List
// ------------------------------------------------------------
// ✅ حل نهائي لمشكلة التباس الاستيراد مع chat-list-item
// ✅ دمج عنصر المحادثة داخل نفس الملف لتجاوز خطأ build
// ✅ الحفاظ على نفس الشكل والسلوك الحالي
// ✅ دعم عربي/ إنجليزي فعليًا
// ✅ احترام RTL داخل النصوص فقط
// ✅ الأرقام دائمًا بالإنجليزية
// ============================================================

import { useEffect, useMemo, useState } from "react"
import { CheckCheck, Plus, Search } from "lucide-react"

import ChatListItemDropdown from "./chat-list-item-dropdown"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

type LocaleKey = "ar" | "en"
type Direction = "rtl" | "ltr"

type RawChatItem = {
  id?: number
  user?: {
    name?: string
    avatar?: string
  }
  last_message?: string
  unread_count?: number
  updated_at?: string
  is_resolved?: boolean
}

type ChatListProps = {
  chats: RawChatItem[]
}

type NormalizedChatItem = {
  id: number
  title: string
  avatar: string
  preview: string
  unreadCount: number
  lastMessageAt: string
  isResolved: boolean
}

type ChatListRowProps = {
  conversation: NormalizedChatItem
  active?: boolean
  onSelect?: (conversationId: number) => void
}

function normalizeChat(chat: RawChatItem): NormalizedChatItem {
  return {
    id: Number(chat.id ?? 0),
    title: chat.user?.name || "WhatsApp Contact",
    avatar: chat.user?.avatar || "",
    preview: chat.last_message || "—",
    unreadCount: Number(chat.unread_count ?? 0),
    lastMessageAt: chat.updated_at || "",
    isResolved: Boolean(chat.is_resolved ?? false),
  }
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

function toEnglishDigits(value: string | number): string {
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

function getAvatarFallback(name: string) {
  const clean = (name || "").trim()
  if (!clean) return "NA"

  const parts = clean.split(/\s+/).filter(Boolean)
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase()
  }

  return `${parts[0][0] ?? ""}${parts[1][0] ?? ""}`.toUpperCase()
}

const translations = {
  ar: {
    title: "المحادثات",
    searchPlaceholder: "ابحث في المحادثات...",
    empty: "لا توجد محادثات",
    addLabel: "إضافة",
  },
  en: {
    title: "Chats",
    searchPlaceholder: "Chats search...",
    empty: "No chat found",
    addLabel: "Add",
  },
} as const

function ChatListRow({
  conversation,
  active = false,
  onSelect,
}: ChatListRowProps) {
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
  const safeLastMessageAt = toEnglishDigits(conversation.lastMessageAt)
  const safeUnreadCount =
    conversation.unreadCount > 99
      ? "99+"
      : toEnglishDigits(conversation.unreadCount)

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

export default function ChatList({ chats }: ChatListProps) {
  const [locale, setLocale] = useState<LocaleKey>("en")
  const [direction, setDirection] = useState<Direction>("ltr")
  const [search, setSearch] = useState("")
  const [selectedChatId, setSelectedChatId] = useState<number | null>(
    chats?.[1]?.id
      ? Number(chats[1].id)
      : chats?.[0]?.id
        ? Number(chats[0].id)
        : null
  )

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

  const t = translations[locale]

  const normalizedChats = useMemo(() => {
    return (chats || []).map(normalizeChat)
  }, [chats])

  const filteredChats = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return normalizedChats

    return normalizedChats.filter((chat) => {
      return (
        chat.title.toLowerCase().includes(term) ||
        chat.preview.toLowerCase().includes(term)
      )
    })
  }, [normalizedChats, search])

  const totalChats = useMemo(() => {
    return toEnglishDigits(normalizedChats.length)
  }, [normalizedChats])

  return (
    <div dir="ltr" className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="shrink-0 px-6 pb-3 pt-6">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <h2 className="truncate text-[20px] font-semibold leading-none lg:text-[21px]">
              {t.title}
            </h2>

            <span
              dir="ltr"
              className="inline-flex h-8 min-w-8 items-center justify-center rounded-full border px-2 text-[12px] font-medium"
            >
              {totalChats}
            </span>
          </div>

          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label={t.addLabel}
            className="h-11 w-11 rounded-full shadow-none"
          >
            <Plus className="h-5 w-5" />
          </Button>
        </div>
      </div>

      <div className="shrink-0 px-6 pb-3">
        <div className="relative flex items-center">
          <Search className="pointer-events-none absolute left-4 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            value={search}
            dir={direction}
            className={cn(
              "h-11 rounded-[14px] border ps-11 pe-4 text-[14px] shadow-none",
              locale === "ar" ? "text-right" : "text-left"
            )}
            placeholder={t.searchPlaceholder}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
      </div>

      <div className="min-h-0 flex-1">
        <div className="flex h-[calc(100vh_-_18rem)] lg:h-[calc(100vh_-_15.8rem)]">
          <ScrollArea className="w-full min-w-0">
            <div className="block min-w-0 divide-y">
              {filteredChats.length ? (
                filteredChats.map((chat) => (
                  <ChatListRow
                    key={chat.id}
                    conversation={chat}
                    active={selectedChatId === chat.id}
                    onSelect={(conversationId: number) =>
                      setSelectedChatId(conversationId)
                    }
                  />
                ))
              ) : (
                <div className="mt-4 px-6 text-center text-sm text-muted-foreground">
                  {t.empty}
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}