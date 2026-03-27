"use client"

// ============================================================
// 📂 الملف: app/system/whatsapp/conversations/page.tsx
// 🟢 Primey HR Cloud - System WhatsApp Conversations Page
// ------------------------------------------------------------
// ✅ تقليل عرض قائمة الدردشات لتقترب من المرجع
// ✅ الحفاظ على المساحة الكافية للعناصر داخل الصف
// ✅ دعم عربي / إنجليزي فعليًا
// ✅ احترام RTL / LTR
// ✅ الأرقام والتواريخ دائمًا بالإنجليزية
// ============================================================

import { useEffect, useMemo, useState } from "react"

import ChatList from "@/components/whatsapp/chat-list"
import ChatContent from "@/components/whatsapp/chat-content"

type LocaleKey = "ar" | "en"
type Direction = "rtl" | "ltr"

type ChatItem = {
  id: number
  user: {
    name: string
    avatar: string
  }
  last_message: string
  unread_count: number
  updated_at: string
  is_resolved: boolean
}

const baseChats = [
  {
    id: 1,
    user: {
      name: "Jacquenetta Slowgrave",
      avatar: "/avatars/01.png",
    },
    lastMessage: {
      ar: "ممتاز، متحمس لذلك. أراك هناك.",
      en: "Great! Looking forward to it. See you there.",
    },
    unreadCount: 8,
    updatedAt: "2026-03-26T10:20:00+03:00",
    isResolved: false,
  },
  {
    id: 2,
    user: {
      name: "Nickola Peever",
      avatar: "/avatars/02.png",
    },
    lastMessage: {
      ar: "ممتاز جدًا، كنت أرغب بتجربة ذلك المكان.",
      en: "Sounds perfect! I've been wanting to try that place.",
    },
    unreadCount: 2,
    updatedAt: "2026-03-26T09:50:00+03:00",
    isResolved: false,
  },
  {
    id: 3,
    user: {
      name: "Farand Hume",
      avatar: "",
    },
    lastMessage: {
      ar: "ما رأيك الساعة 7 مساءً في المطعم الإيطالي الجديد؟",
      en: "How about 7 PM at the new Italian place downtown?",
    },
    unreadCount: 0,
    updatedAt: "2026-03-25T20:15:00+03:00",
    isResolved: false,
  },
  {
    id: 4,
    user: {
      name: "Ossie Peasey",
      avatar: "",
    },
    lastMessage: {
      ar: "أهلًا، نعم بالتأكيد. ما الوقت المناسب لك؟",
      en: "Hey Bonnie, yes, definitely! What time works best?",
    },
    unreadCount: 0,
    updatedAt: "2026-03-13T16:40:00+03:00",
    isResolved: false,
  },
  {
    id: 5,
    user: {
      name: "Hall Negri",
      avatar: "",
    },
    lastMessage: {
      ar: "لا مشكلة إطلاقًا، سأحجز طاولة وأرسل لك.",
      en: "No worries at all! I'll grab a table and text you.",
    },
    unreadCount: 0,
    updatedAt: "2026-03-24T14:30:00+03:00",
    isResolved: false,
  },
  {
    id: 6,
    user: {
      name: "Elyssa Segot",
      avatar: "",
    },
    lastMessage: {
      ar: "لقد أخبرتني اليوم فقط.",
      en: "She just told me today.",
    },
    unreadCount: 0,
    updatedAt: "2026-03-25T11:00:00+03:00",
    isResolved: false,
  },
] as const

function formatEnglishDateTime(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return ""
  }

  return new Intl.DateTimeFormat("en-GB-u-nu-latn", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  }).format(date)
}

function getHtmlLocale(): { locale: LocaleKey; direction: Direction } {
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

export default function Page() {
  const [locale, setLocale] = useState<LocaleKey>("en")
  const [direction, setDirection] = useState<Direction>("ltr")

  useEffect(() => {
    const syncHtmlMeta = () => {
      const { locale: nextLocale, direction: nextDirection } = getHtmlLocale()
      setLocale(nextLocale)
      setDirection(nextDirection)
    }

    syncHtmlMeta()

    const observer = new MutationObserver(() => {
      syncHtmlMeta()
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    return () => {
      observer.disconnect()
    }
  }, [])

  const chats: ChatItem[] = useMemo(() => {
    return baseChats.map((chat) => ({
      id: chat.id,
      user: chat.user,
      last_message: chat.lastMessage[locale],
      unread_count: chat.unreadCount,
      updated_at: formatEnglishDateTime(chat.updatedAt),
      is_resolved: chat.isResolved,
    }))
  }, [locale])

  return (
    <div dir={direction} className="h-[calc(100vh-7rem)] overflow-hidden">
      <div className="flex h-full flex-col gap-4 xl:flex-row xl:gap-5">
        <div className="w-full xl:w-[440px] xl:min-w-[440px] xl:max-w-[440px]">
          <div className="h-full">
            <ChatList chats={chats} />
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <ChatContent />
        </div>
      </div>
    </div>
  )
}