// ============================================================
// 📂 الملف: lib/whatsapp/types.ts
// 🟢 Mham Cloud - WhatsApp Module Types
// ------------------------------------------------------------
// ✅ أنواع البيانات الأساسية الخاصة بموديول الواتساب
// ✅ جاهزة لصفحة المحادثات الاحترافية
// ✅ متوافقة مع System WhatsApp APIs الحالية
// ============================================================

export type Locale = "ar" | "en"

export type ConversationStatusValue = "OPEN" | "CLOSED" | "ARCHIVED" | "SPAM"

export type MessageDeliveryStatus =
  | "PENDING"
  | "QUEUED"
  | "SENT"
  | "DELIVERED"
  | "READ"
  | "FAILED"
  | "UNKNOWN"

export type MessageDirection = "INBOUND" | "OUTBOUND"

export type WhatsAppMessageType =
  | "TEXT"
  | "IMAGE"
  | "VIDEO"
  | "AUDIO"
  | "VOICE"
  | "DOCUMENT"
  | "FILE"
  | "STICKER"
  | "LOCATION"
  | "CONTACT"
  | "SYSTEM"
  | "UNKNOWN"

export type WhatsAppScopeType = "SYSTEM" | "COMPANY" | "UNKNOWN"

export type WhatsAppStatusPayload = {
  success?: boolean
  connected?: boolean
  provider?: string
  phone_number_id?: string | null
  business_account_id?: string | null
  webhook_verified?: boolean
  mode?: string
  last_check_at?: string | null
  company_scope_enabled?: boolean
  system_scope_enabled?: boolean
  pending_templates?: number
  failed_messages?: number
}

export type WhatsAppSettingsPayload = {
  success?: boolean
  config?: {
    is_active?: boolean
    provider?: string
    app_name?: string
    access_token_masked?: string
    phone_number_id?: string
    business_account_id?: string
    webhook_verify_token_masked?: string
    default_country_code?: string
    allow_broadcasts?: boolean
    send_test_enabled?: boolean
  }
}

export type InboxContact = {
  id: number
  scope_type?: string
  company_id?: number | null
  phone_number?: string
  display_name?: string
  push_name?: string
  wa_jid?: string
  profile_name?: string
  is_blocked?: boolean
  is_business?: boolean
  last_message_at?: string | null
  last_seen_at?: string | null
  notes?: string
  extra_json?: Record<string, unknown>
}

export type InboxConversation = {
  id: number
  scope_type?: string
  company_id?: number | null
  status?: string
  subject?: string
  assigned_to_id?: number | null
  assigned_to_name?: string
  session_name?: string
  unread_count?: number
  last_message_preview?: string
  last_message_at?: string | null
  is_pinned?: boolean
  is_muted?: boolean
  is_resolved?: boolean
  extra_json?: Record<string, unknown>
  contact?: InboxContact
}

export type InboxMessage = {
  id: number
  conversation_id: number
  scope_type?: string
  company_id?: number | null
  direction?: string
  message_type?: string
  external_message_id?: string
  provider?: string
  provider_status?: string
  delivery_status?: string
  wa_jid?: string
  sender_phone?: string
  sender_name?: string
  body_text?: string
  caption?: string
  attachment_url?: string
  attachment_name?: string
  mime_type?: string
  media_type?: string
  is_read?: boolean
  is_from_me?: boolean
  replied_to_external_message_id?: string
  payload_json?: Record<string, unknown>
  extra_json?: Record<string, unknown>
  webhook_event_id?: number | null
  message_log_id?: number | null
  message_created_at?: string | null
  sent_at?: string | null
  delivered_at?: string | null
  read_at?: string | null
  failed_at?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export type InboxSummary = {
  total_conversations?: number
  open_conversations?: number
  closed_conversations?: number
  archived_conversations?: number
  spam_conversations?: number
  unread_conversations?: number
  resolved_conversations?: number
  pinned_conversations?: number
}

export type InboxSummaryPayload = {
  success?: boolean
  scope_type?: string
  summary?: InboxSummary
}

export type InboxListPayload = {
  success?: boolean
  scope_type?: string
  count?: number
  results?: InboxConversation[]
}

export type InboxDetailPayload = {
  success?: boolean
  conversation?: InboxConversation
}

export type InboxMessagesPayload = {
  success?: boolean
  conversation?: InboxConversation
  count?: number
  results?: InboxMessage[]
}

export type DashboardState = {
  loading: boolean
  refreshing: boolean
  status: WhatsAppStatusPayload | null
  settings: WhatsAppSettingsPayload | null
  inboxSummary: InboxSummary | null
  conversations: InboxConversation[]
  selectedConversation: InboxConversation | null
  messages: InboxMessage[]
  loadingMessages: boolean
}

export type ConversationFiltersState = {
  search: string
  status: ConversationStatusValue | ""
  onlyUnread: boolean
}

export type ChatListItemModel = {
  id: number
  title: string
  phoneNumber: string
  preview: string
  lastMessageAt: string | null
  unreadCount: number
  status: ConversationStatusValue | ""
  isPinned: boolean
  isResolved: boolean
  assignedToName: string
}

export type ChatHeaderModel = {
  id: number
  title: string
  phoneNumber: string
  status: ConversationStatusValue | ""
  unreadCount: number
  isPinned: boolean
  isResolved: boolean
  assignedToName: string
  sessionName: string
  lastSeenAt: string | null
}

export type ChatMessageModel = {
  id: number
  conversationId: number
  direction: MessageDirection
  messageType: WhatsAppMessageType
  body: string
  caption: string
  senderName: string
  senderPhone: string
  attachmentUrl: string
  attachmentName: string
  mimeType: string
  mediaType: string
  deliveryStatus: MessageDeliveryStatus
  isRead: boolean
  isFromMe: boolean
  createdAt: string | null
}

export type ConversationDetailsModel = {
  id: number
  contactName: string
  phoneNumber: string
  assignedToName: string
  sessionName: string
  status: ConversationStatusValue | ""
  isPinned: boolean
  isResolved: boolean
  lastActivityAt: string | null
  lastMessagePreview: string
}

export type QuickStatsItem = {
  label: string
  value: string
  iconName:
    | "message-circle"
    | "bell-ring"
    | "check-circle"
    | "pin"
    | "activity"
    | "trending-up"
}

export type QuickLinkItem = {
  title: string
  href: string
  description: string
  iconName:
    | "settings"
    | "logs"
    | "templates"
    | "broadcasts"
    | "message-circle"
}

export type MarkReadResponsePayload = {
  success?: boolean
  conversation?: InboxConversation
}

export type TogglePinnedResponsePayload = {
  success?: boolean
  conversation?: InboxConversation
}

export type ToggleResolvedResponsePayload = {
  success?: boolean
  conversation?: InboxConversation
}

export type UpdateConversationStatusResponsePayload = {
  success?: boolean
  conversation?: InboxConversation
}