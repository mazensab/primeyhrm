"use client"

// ============================================================
// 📂 الملف: components/whatsapp/chat-list.tsx
// 🟢 Primey HR Cloud - WhatsApp Chat List
// ------------------------------------------------------------
// ✅ إزالة البطاقة الخارجية عن قائمة الدردشات
// ✅ جعل القائمة جزءًا من الصفحة مثل المرجع
// ✅ الاستفادة الكاملة من العرض الموسّع القادم من page.tsx
// ✅ الحفاظ على الهيدر والبحث والقائمة نفسها
// ✅ دعم عربي / إنجليزي فعليًا
// ✅ احترام RTL داخل النصوص فقط
// ✅ الأرقام دائمًا بالإنجليزية
// ============================================================

import { useEffect, useMemo, useState } from "react"
import { Plus, Search } from "lucide-react"

import ChatListItem from "./chat-list-item"
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
      {/* Header */}
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

      {/* Search */}
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

      {/* List */}
      <div className="min-h-0 flex-1">
        <div className="flex h-[calc(100vh_-_18rem)] lg:h-[calc(100vh_-_15.8rem)]">
          <ScrollArea className="w-full min-w-0">
            <div className="block min-w-0 divide-y">
              {filteredChats.length ? (
                filteredChats.map((chat) => (
                  <ChatListItem
                    key={chat.id}
                    conversation={chat}
                    active={selectedChatId === chat.id}
                    onSelect={(conversationId) =>
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