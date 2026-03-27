// ============================================================
// 📂 الملف: lib/whatsapp/mappers.ts
// 🟢 Primey HR Cloud - WhatsApp Data Mappers
// ------------------------------------------------------------
// ✅ تحويل بيانات API إلى Models جاهزة للواجهة
// ✅ الحفاظ على طبقة فصل واضحة بين الـ backend والـ UI
// ============================================================

import {
  getConversationDisplayName,
  getMessageBodyText,
  getMessageDirection,
  getMessageType,
  normalizeConversationStatus,
  normalizeDeliveryStatus,
} from "@/lib/whatsapp/formatters"
import type {
  ChatHeaderModel,
  ChatListItemModel,
  ChatMessageModel,
  ConversationDetailsModel,
  InboxConversation,
  InboxMessage,
} from "@/lib/whatsapp/types"

export function mapConversationToChatListItem(
  conversation: InboxConversation,
  mediaFallbackText = "Media message"
): ChatListItemModel {
  return {
    id: conversation.id,
    title: getConversationDisplayName({
      displayName: conversation.contact?.display_name,
      pushName: conversation.contact?.push_name,
      phoneNumber: conversation.contact?.phone_number,
      fallback: "بدون رقم",
    }),
    phoneNumber: conversation.contact?.phone_number || "—",
    preview: (conversation.last_message_preview || "").trim() || mediaFallbackText,
    lastMessageAt: conversation.last_message_at || null,
    unreadCount: Number(conversation.unread_count || 0),
    status: normalizeConversationStatus(conversation.status),
    isPinned: !!conversation.is_pinned,
    isResolved: !!conversation.is_resolved,
    assignedToName: conversation.assigned_to_name || "",
  }
}

export function mapConversationToChatHeader(
  conversation: InboxConversation
): ChatHeaderModel {
  return {
    id: conversation.id,
    title: getConversationDisplayName({
      displayName: conversation.contact?.display_name,
      pushName: conversation.contact?.push_name,
      phoneNumber: conversation.contact?.phone_number,
      fallback: "بدون رقم",
    }),
    phoneNumber: conversation.contact?.phone_number || "—",
    status: normalizeConversationStatus(conversation.status),
    unreadCount: Number(conversation.unread_count || 0),
    isPinned: !!conversation.is_pinned,
    isResolved: !!conversation.is_resolved,
    assignedToName: conversation.assigned_to_name || "",
    sessionName: conversation.session_name || "",
    lastSeenAt: conversation.contact?.last_seen_at || null,
  }
}

export function mapConversationToDetailsCard(
  conversation: InboxConversation,
  mediaFallbackText = "Media message"
): ConversationDetailsModel {
  return {
    id: conversation.id,
    contactName: getConversationDisplayName({
      displayName: conversation.contact?.display_name,
      pushName: conversation.contact?.push_name,
      phoneNumber: conversation.contact?.phone_number,
      fallback: "بدون رقم",
    }),
    phoneNumber: conversation.contact?.phone_number || "—",
    assignedToName: conversation.assigned_to_name || "",
    sessionName: conversation.session_name || "",
    status: normalizeConversationStatus(conversation.status),
    isPinned: !!conversation.is_pinned,
    isResolved: !!conversation.is_resolved,
    lastActivityAt: conversation.last_message_at || null,
    lastMessagePreview:
      (conversation.last_message_preview || "").trim() || mediaFallbackText,
  }
}

export function mapMessageToChatMessage(
  message: InboxMessage,
  mediaFallbackText = "Media message"
): ChatMessageModel {
  return {
    id: message.id,
    conversationId: message.conversation_id,
    direction: message.is_from_me
      ? "OUTBOUND"
      : getMessageDirection(message.direction),
    messageType: getMessageType(message.message_type, message.media_type) as ChatMessageModel["messageType"],
    body: getMessageBodyText({
      bodyText: message.body_text,
      caption: message.caption,
      mediaType: message.media_type,
      fallbackText: mediaFallbackText,
    }),
    caption: message.caption || "",
    senderName: message.sender_name || "",
    senderPhone: message.sender_phone || "",
    attachmentUrl: message.attachment_url || "",
    attachmentName: message.attachment_name || "",
    mimeType: message.mime_type || "",
    mediaType: message.media_type || "",
    deliveryStatus: normalizeDeliveryStatus(message.delivery_status),
    isRead: !!message.is_read,
    isFromMe: !!message.is_from_me,
    createdAt: message.message_created_at || message.created_at || null,
  }
}

export function mapConversationsToChatListItems(
  conversations: InboxConversation[],
  mediaFallbackText = "Media message"
): ChatListItemModel[] {
  return conversations.map((conversation) =>
    mapConversationToChatListItem(conversation, mediaFallbackText)
  )
}

export function mapMessagesToChatMessages(
  messages: InboxMessage[],
  mediaFallbackText = "Media message"
): ChatMessageModel[] {
  return messages.map((message) =>
    mapMessageToChatMessage(message, mediaFallbackText)
  )
}