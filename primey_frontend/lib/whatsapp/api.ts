// ============================================================
// 📂 الملف: lib/whatsapp/api.ts
// 🟢 Primey HR Cloud - WhatsApp API Helpers
// ------------------------------------------------------------
// ✅ جميع دوال الجلب والإرسال الخاصة بموديول الواتساب
// ✅ آمنة ومرنة وتدعم fallback URL candidates
// ============================================================

import { DEFAULT_WHATSAPP_SEARCH_LIMIT, WHATSAPP_API_PATHS } from "@/lib/whatsapp/constants"
import type {
  ConversationStatusValue,
  InboxDetailPayload,
  InboxListPayload,
  InboxMessagesPayload,
  InboxSummaryPayload,
  MarkReadResponsePayload,
  TogglePinnedResponsePayload,
  ToggleResolvedResponsePayload,
  UpdateConversationStatusResponsePayload,
  WhatsAppSettingsPayload,
  WhatsAppStatusPayload,
} from "@/lib/whatsapp/types"

function getApiBaseCandidates(): string[] {
  const fromEnv = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "")
  const fromWindow =
    typeof window !== "undefined" ? window.location.origin.replace(/\/$/, "") : ""

  return Array.from(new Set([fromEnv, fromWindow, ""])).filter(Boolean)
}

function buildCandidateUrls(path: string): string[] {
  const cleanPath = path.startsWith("/") ? path : `/${path}`
  const variants = new Set<string>()

  const bases = ["", ...getApiBaseCandidates()]

  for (const base of bases) {
    const full = base ? `${base}${cleanPath}` : cleanPath
    const withoutSlash = full.endsWith("/") ? full.slice(0, -1) : full
    const withSlash = `${withoutSlash}/`

    variants.add(full)
    variants.add(withoutSlash)
    variants.add(withSlash)
  }

  return Array.from(variants).filter(Boolean)
}

export async function safeFetchJson<T>(path: string): Promise<T | null> {
  const candidates = buildCandidateUrls(path)
  let lastError: Error | null = null

  for (const candidate of candidates) {
    try {
      const response = await fetch(candidate, {
        method: "GET",
        credentials: "include",
        cache: "no-store",
        redirect: "follow",
        headers: {
          Accept: "application/json",
        },
      })

      if (!response.ok) {
        lastError = new Error(`Request failed: ${response.status} for ${candidate}`)
        continue
      }

      return (await response.json()) as T
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("Unknown fetch error")
    }
  }

  throw lastError || new Error(`Request failed for ${path}`)
}

export async function safePostJson<T>(
  path: string,
  body?: Record<string, string | number | boolean | null | undefined>
): Promise<T | null> {
  const candidates = buildCandidateUrls(path)
  let lastError: Error | null = null

  for (const candidate of candidates) {
    try {
      const payload = new URLSearchParams()

      Object.entries(body || {}).forEach(([key, value]) => {
        if (value === undefined || value === null) return
        payload.append(key, String(value))
      })

      const response = await fetch(candidate, {
        method: "POST",
        credentials: "include",
        cache: "no-store",
        redirect: "follow",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
        body: payload.toString(),
      })

      if (!response.ok) {
        lastError = new Error(`Request failed: ${response.status} for ${candidate}`)
        continue
      }

      return (await response.json()) as T
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("Unknown post error")
    }
  }

  throw lastError || new Error(`Request failed for ${path}`)
}

export async function fetchWhatsAppStatus() {
  return safeFetchJson<WhatsAppStatusPayload>(WHATSAPP_API_PATHS.status)
}

export async function fetchWhatsAppSettings() {
  return safeFetchJson<WhatsAppSettingsPayload>(WHATSAPP_API_PATHS.settings)
}

export async function fetchInboxSummary() {
  return safeFetchJson<InboxSummaryPayload>(WHATSAPP_API_PATHS.inboxSummary)
}

export async function fetchInboxConversations(params?: {
  search?: string
  status?: ConversationStatusValue | ""
  onlyUnread?: boolean
  limit?: number
}) {
  const query = new URLSearchParams()

  if (params?.search) query.set("search", params.search)
  if (params?.status) query.set("status", params.status)
  if (params?.onlyUnread) query.set("only_unread", "true")
  query.set("limit", String(params?.limit ?? DEFAULT_WHATSAPP_SEARCH_LIMIT))

  const path = `${WHATSAPP_API_PATHS.inboxList}?${query.toString()}`
  return safeFetchJson<InboxListPayload>(path)
}

export async function fetchConversationDetail(conversationId: number) {
  return safeFetchJson<InboxDetailPayload>(
    WHATSAPP_API_PATHS.conversationDetail(conversationId)
  )
}

export async function fetchConversationMessages(conversationId: number) {
  return safeFetchJson<InboxMessagesPayload>(
    WHATSAPP_API_PATHS.conversationMessages(conversationId)
  )
}

export async function markConversationRead(conversationId: number) {
  return safePostJson<MarkReadResponsePayload>(
    WHATSAPP_API_PATHS.conversationMarkRead(conversationId)
  )
}

export async function toggleConversationPinned(
  conversationId: number,
  isPinned: boolean
) {
  return safePostJson<TogglePinnedResponsePayload>(
    WHATSAPP_API_PATHS.conversationPinned(conversationId),
    { is_pinned: isPinned }
  )
}

export async function toggleConversationResolved(
  conversationId: number,
  isResolved: boolean
) {
  return safePostJson<ToggleResolvedResponsePayload>(
    WHATSAPP_API_PATHS.conversationResolved(conversationId),
    { is_resolved: isResolved }
  )
}

export async function updateConversationStatus(
  conversationId: number,
  status: ConversationStatusValue
) {
  return safePostJson<UpdateConversationStatusResponsePayload>(
    WHATSAPP_API_PATHS.conversationStatus(conversationId),
    { status }
  )
}