"use client"

// ============================================================
// 📂 الملف: components/whatsapp/chat-content.tsx
// 🟢 Primey HR Cloud - WhatsApp Chat Content
// ------------------------------------------------------------
// ✅ إزالة البطاقة الخارجية عن الدردشة المفتوحة
// ✅ جعل منطقة الشات جزءًا من الصفحة مثل المرجع
// ✅ الإبقاء على نفس السلوك الحالي للهيدر والرسائل والفوتر
// ============================================================

import { useEffect, useMemo, useState } from "react"

import ChatHeader from "./chat-header"
import ChatFooter from "./chat-footer"
import ChatBubble from "./chat-bubbles"
import UserDetailSheet from "./user-detail-sheet"

import { ScrollArea } from "@/components/ui/scroll-area"

type LocaleKey = "ar" | "en"
type Direction = "rtl" | "ltr"

const translations = {
  ar: {
    composerPlaceholder: "اكتب رسالة...",
    send: "إرسال",
    comingSoon: "قريبًا",
  },
  en: {
    composerPlaceholder: "Enter message...",
    send: "Send",
    comingSoon: "Coming soon",
  },
} as const

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

export default function ChatContent() {
  const [locale, setLocale] = useState<LocaleKey>("en")
  const [direction, setDirection] = useState<Direction>("ltr")
  const [message, setMessage] = useState("")

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

  const footerTranslations = translations[locale]

  const demoMessages = useMemo(
    () => [
      {
        id: 1,
        type: "text",
        own_message: false,
        content:
          "I know how important this file is to you. You can trust me ;) I know how important this file is to you. You can trust me ;) know how important this file is to you. You can trust me ;)",
      },
      {
        id: 2,
        type: "text",
        own_message: true,
        content:
          "I know how important this file is to you. You can trust me ;) me ;)",
      },
      {
        id: 3,
        type: "image",
        own_message: true,
        content: "",
        data: {
          images: [
            "https://images.unsplash.com/photo-1517142089942-ba376ce32a2e?q=80&w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=1200&auto=format&fit=crop",
          ],
        },
      },
    ],
    []
  )

  const handleSend = () => {
    if (!message.trim()) return
    setMessage("")
  }

  return (
    <div dir={direction} className="flex h-full min-h-0 flex-col overflow-hidden">
      {/* Header */}
      <div className="shrink-0">
        <ChatHeader />
      </div>

      {/* Messages */}
      <div className="min-h-0 flex-1 overflow-hidden px-2 pb-2 lg:px-4 lg:pb-4">
        <ScrollArea className="h-full">
          <div className="flex min-h-full flex-col lg:h-[calc(100vh_-_13.8rem)]">
            <div className="flex flex-col gap-4 py-4 lg:py-0">
              {demoMessages.map((item) => (
                <ChatBubble key={item.id} message={item} type={item.type} />
              ))}
            </div>
          </div>
        </ScrollArea>
      </div>

      {/* Footer */}
      <div className="shrink-0 px-2 pb-2 pt-1 lg:px-4 lg:pb-4 lg:pt-2">
        <ChatFooter
          value={message}
          t={footerTranslations}
          onChange={setMessage}
          onSend={handleSend}
        />
      </div>

      <UserDetailSheet />
    </div>
  )
}