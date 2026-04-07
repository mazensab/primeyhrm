import { Check, CheckCheck, CircleCheck } from "lucide-react"

import { MediaListItemType } from "@/types"

// ============================================================
// 📂 الملف: components/whatsapp/media-list-item.tsx
// 🟢 Mham Cloud - WhatsApp Media List Item
// ------------------------------------------------------------
// ✅ توحيد أحجام الأيقونات
// ✅ تحسين الإرجاع الافتراضي
// ✅ أقرب بصريًا للنسخة المدفوعة
// ============================================================

export default function MediaListItem({ type }: MediaListItemType) {
  const baseClassName = "h-3.5 w-3.5 shrink-0"

  switch (type) {
    case "image":
      return <CircleCheck className={`${baseClassName} text-emerald-500`} />

    case "pdf_file":
      return <CheckCheck className={`${baseClassName} text-muted-foreground`} />

    case "text_file":
      return <Check className={`${baseClassName} text-muted-foreground`} />

    default:
      return null
  }
}