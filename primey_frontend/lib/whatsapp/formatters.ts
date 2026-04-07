// ============================================================
// 📂 الملف: lib/whatsapp/formatters.ts
// 🟢 Mham Cloud - WhatsApp Formatters
// ------------------------------------------------------------
// ✅ تنسيقات التاريخ والأرقام والحالات
// ✅ دوال مساعدة خاصة بعرض واجهة الواتساب
// ============================================================

import type { ConversationStatusValue, Locale, MessageDeliveryStatus } from "@/lib/whatsapp/types"

export function detectLocale(): Locale {
  if (typeof document === "undefined") return "ar"

  const htmlLang = document.documentElement.lang?.toLowerCase() || ""
  return htmlLang.startsWith("en") ? "en" : "ar"
}

export function formatDate(value: string | null | undefined, locale: Locale): string {
  if (!value) return "—"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"

  return new Intl.DateTimeFormat(locale === "ar" ? "en-GB" : "en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    numberingSystem: "latn",
  }).format(date)
}

export function formatTime(value: string | null | undefined, locale: Locale): string {
  if (!value) return "—"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"

  return new Intl.DateTimeFormat(locale === "ar" ? "en-GB" : "en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
    numberingSystem: "latn",
  }).format(date)
}

export function formatNumber(value: number | null | undefined): string {
  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
  }).format(Number(value ?? 0))
}

export function normalizeConversationStatus(value?: string): ConversationStatusValue | "" {
  const status = (value || "").toUpperCase()

  if (status === "OPEN" || status === "CLOSED" || status === "ARCHIVED" || status === "SPAM") {
    return status
  }

  return ""
}

export function normalizeDeliveryStatus(value?: string): MessageDeliveryStatus {
  const status = (value || "").toUpperCase()

  if (
    status === "PENDING" ||
    status === "QUEUED" ||
    status === "SENT" ||
    status === "DELIVERED" ||
    status === "READ" ||
    status === "FAILED"
  ) {
    return status
  }

  return "UNKNOWN"
}

export function getConversationTone(status?: string): string {
  const value = (status || "").toUpperCase()

  if (value === "OPEN") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700"
  }

  if (value === "CLOSED") {
    return "border-slate-200 bg-slate-50 text-slate-700"
  }

  if (value === "ARCHIVED") {
    return "border-amber-200 bg-amber-50 text-amber-700"
  }

  if (value === "SPAM") {
    return "border-red-200 bg-red-50 text-red-700"
  }

  return "border-slate-200 bg-slate-50 text-slate-700"
}

export function getMessageDirection(value?: string): "INBOUND" | "OUTBOUND" {
  const direction = (value || "").toUpperCase()
  return direction === "OUTBOUND" ? "OUTBOUND" : "INBOUND"
}

export function getMessageType(value?: string, mediaType?: string): string {
  const raw = ((value || mediaType || "").trim() || "TEXT").toUpperCase()

  if (["TEXT", "IMAGE", "VIDEO", "AUDIO", "VOICE", "DOCUMENT", "FILE", "STICKER", "LOCATION", "CONTACT", "SYSTEM"].includes(raw)) {
    return raw
  }

  return "UNKNOWN"
}

export function getMessageBodyText(input: {
  bodyText?: string
  caption?: string
  mediaType?: string
  fallbackText?: string
}): string {
  const body = (input.bodyText || "").trim()
  const caption = (input.caption || "").trim()

  if (body) return body
  if (caption) return caption
  if (input.mediaType) return input.fallbackText || "Media message"

  return ""
}

export function getConversationDisplayName(input: {
  displayName?: string
  pushName?: string
  phoneNumber?: string
  fallback?: string
}): string {
  return (
    (input.displayName || "").trim() ||
    (input.pushName || "").trim() ||
    (input.phoneNumber || "").trim() ||
    input.fallback ||
    "—"
  )
}