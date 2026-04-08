import { Check, CheckCheck } from "lucide-react"

// ============================================================
// 📂 الملف: components/whatsapp/message-status-icon.tsx
// 🟢 Mham Cloud - WhatsApp Message Status Icon
// ------------------------------------------------------------
// ✅ إزالة الاستيراد المكسور من "@/types"
// ✅ تعريف النوع محليًا لتجاوز خطأ build
// ✅ الحفاظ على نفس سلوك الأيقونات الحالي
// ============================================================

type MessageStatus = "read" | "forwarded" | "sent"

type MessageStatusIconProps = {
  status: MessageStatus
}

export default function MessageStatusIcon({
  status,
}: MessageStatusIconProps) {
  switch (status) {
    case "read":
      return <CheckCheck className="h-4 w-4 flex-shrink-0 text-green-500" />

    case "forwarded":
      return (
        <CheckCheck className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
      )

    case "sent":
      return <Check className="h-4 w-4 flex-shrink-0 text-muted-foreground" />

    default:
      return null
  }
}