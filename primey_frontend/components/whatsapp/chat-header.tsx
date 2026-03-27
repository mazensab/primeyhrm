"use client"

// ============================================================
// 📂 الملف: components/whatsapp/chat-header.tsx
// 🟢 Primey HR Cloud - WhatsApp Chat Header
// ------------------------------------------------------------
// ✅ إعادة بناء الهيدر على روح المرجع المدفوع
// ✅ تكبير مدروس للهيدر بدل النسخة المصغرة السابقة
// ✅ تحسين avatar / title / status / action buttons
// ============================================================

import { Ellipsis, PhoneCall, Video } from "lucide-react"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"

function getAvatarFallback(name: string) {
  const clean = (name || "").trim()
  if (!clean) return "NA"

  const parts = clean.split(/\s+/).filter(Boolean)
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase()
  }

  return `${parts[0][0] ?? ""}${parts[1][0] ?? ""}`.toUpperCase()
}

export default function ChatHeader() {
  const contactName = "Nickola Peever"
  const contactStatus = "Online"
  const contactAvatar = "/avatars/02.png"

  return (
    <div className="flex items-center justify-between px-4 py-3 md:px-5 md:py-3.5">
      <div className="flex min-w-0 items-center gap-3">
        <Avatar className="h-10 w-10 shrink-0 md:h-11 md:w-11">
          <AvatarImage src={contactAvatar} alt={contactName} />
          <AvatarFallback className="text-[12px] font-medium">
            {getAvatarFallback(contactName)}
          </AvatarFallback>
        </Avatar>

        <div className="min-w-0">
          <p className="truncate text-[15px] font-semibold leading-none md:text-[16px]">
            {contactName}
          </p>
          <p className="mt-1.5 truncate text-[12px] leading-none text-emerald-500">
            {contactStatus}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="h-10 w-10 rounded-xl border shadow-none"
        >
          <Video className="h-4 w-4" />
        </Button>

        <Button
          type="button"
          variant="outline"
          size="icon"
          className="h-10 w-10 rounded-xl border shadow-none"
        >
          <PhoneCall className="h-4 w-4" />
        </Button>

        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-10 w-10 rounded-xl"
        >
          <Ellipsis className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}