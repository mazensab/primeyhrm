// ============================================================
// 📂 الملف: lib/whatsapp/constants.ts
// 🟢 Primey HR Cloud - WhatsApp Module Constants
// ------------------------------------------------------------
// ✅ الثوابت العامة الخاصة بموديول الواتساب
// ✅ API Paths
// ✅ القيم الافتراضية
// ✅ الفلاتر والحالات
// ============================================================

import type {
  ConversationStatusValue,
  Locale,
  MessageDeliveryStatus,
  MessageDirection,
  WhatsAppMessageType,
} from "@/lib/whatsapp/types"

export const WHATSAPP_API_PATHS = {
  status: "/api/system/whatsapp/status/",
  settings: "/api/system/whatsapp/settings/",
  inboxSummary: "/api/system/whatsapp/inbox/summary/",
  inboxList: "/api/system/whatsapp/inbox/",
  conversationDetail: (id: number) => `/api/system/whatsapp/inbox/${id}/`,
  conversationMessages: (id: number) =>
    `/api/system/whatsapp/inbox/${id}/messages/`,
  conversationMarkRead: (id: number) =>
    `/api/system/whatsapp/inbox/${id}/mark-read/`,
  conversationStatus: (id: number) =>
    `/api/system/whatsapp/inbox/${id}/status/`,
  conversationResolved: (id: number) =>
    `/api/system/whatsapp/inbox/${id}/resolved/`,
  conversationPinned: (id: number) =>
    `/api/system/whatsapp/inbox/${id}/pinned/`,
} as const

export const DEFAULT_WHATSAPP_SEARCH_LIMIT = 100

export const CONVERSATION_STATUS_OPTIONS: Array<{
  value: ConversationStatusValue | ""
  labelKey:
    | "all"
    | "filterOpen"
    | "filterClosed"
    | "filterArchived"
    | "filterSpam"
}> = [
  { value: "", labelKey: "all" },
  { value: "OPEN", labelKey: "filterOpen" },
  { value: "CLOSED", labelKey: "filterClosed" },
  { value: "ARCHIVED", labelKey: "filterArchived" },
  { value: "SPAM", labelKey: "filterSpam" },
]

export const CONVERSATION_ACTION_STATUSES: ConversationStatusValue[] = [
  "OPEN",
  "CLOSED",
  "ARCHIVED",
  "SPAM",
]

export const DELIVERY_STATUS_ORDER: MessageDeliveryStatus[] = [
  "PENDING",
  "QUEUED",
  "SENT",
  "DELIVERED",
  "READ",
  "FAILED",
  "UNKNOWN",
]

export const SUPPORTED_MESSAGE_DIRECTIONS: MessageDirection[] = [
  "INBOUND",
  "OUTBOUND",
]

export const SUPPORTED_MESSAGE_TYPES: WhatsAppMessageType[] = [
  "TEXT",
  "IMAGE",
  "VIDEO",
  "AUDIO",
  "VOICE",
  "DOCUMENT",
  "FILE",
  "STICKER",
  "LOCATION",
  "CONTACT",
  "SYSTEM",
  "UNKNOWN",
]

export const DEFAULT_LOCALE: Locale = "ar"

export const DEFAULT_EMPTY_VALUE = "—"

export const WHATSAPP_TRANSLATIONS = {
  ar: {
    centerBadge: "System WhatsApp Inbox",
    pageTitle: "صندوق واتساب للنظام",
    pageDescription:
      "إدارة المحادثات الواردة، متابعة الرسائل، والتحكم بحالة المحادثة من واجهة احترافية موحدة.",
    refresh: "تحديث",
    settings: "الإعدادات",
    conversations: "المحادثات",
    connected: "متصل",
    disconnected: "غير متصل",
    active: "نشط",
    inactive: "غير نشط",
    whatsappConnection: "حالة الربط والصندوق",
    whatsappConnectionDesc:
      "نظرة سريعة على حالة الاتصال، مزود الواتساب، وإحصائيات صندوق المحادثات.",
    phoneNumberId: "Phone Number ID",
    notConfigured: "غير مضبوط",
    webhook: "Webhook",
    verified: "موثق",
    pendingOrUnknown: "قيد الانتظار / غير معروف",
    provider: "المزود",
    systemStatus: "حالة النظام",
    totalConversations: "إجمالي المحادثات",
    unreadConversations: "غير المقروءة",
    resolvedConversations: "المحلولة",
    pinnedConversations: "المثبتة",
    openConversations: "المفتوحة",
    quickAccess: "الوصول السريع",
    quickAccessDesc: "الانتقال السريع إلى بقية وحدات واتساب للنظام.",
    logs: "السجل",
    templates: "القوالب",
    broadcastsLabel: "البث الجماعي",
    smartSummary: "ملخص الصندوق",
    smartSummaryDesc: "إحصاءات سريعة للمحادثات الحالية",
    systemScope: "System Scope",
    companyScope: "Company Scope",
    enabled: "مفعل",
    undefined: "غير محدد",
    pendingTemplates: "Pending Templates",
    failedMessages: "Failed Messages",
    dashboardLoadError: "تعذر تحميل صندوق واتساب للنظام",
    searchPlaceholder: "ابحث بالاسم أو الرقم أو آخر رسالة...",
    inboxListTitle: "المحادثات",
    inboxListDesc: "كل المحادثات الواردة على مستوى النظام",
    noConversations: "لا توجد محادثات حتى الآن",
    noConversationsDesc:
      "ستظهر هنا المحادثات الواردة تلقائيًا عند وصول أول رسالة.",
    conversationDetails: "تفاصيل المحادثة",
    messagesTitle: "الرسائل",
    messagesDesc: "عرض المحادثة الحالية مع جميع الرسائل المرتبطة بها",
    noMessagesYet: "لا توجد رسائل في هذه المحادثة",
    noMessagesDesc: "بمجرد وصول رسائل جديدة ستظهر هنا تلقائيًا.",
    selectConversation: "اختر محادثة",
    selectConversationDesc:
      "اختر محادثة من القائمة الجانبية لعرض الرسائل والتفاصيل.",
    markRead: "تعليم كمقروءة",
    resolve: "حل المحادثة",
    unresolve: "إلغاء الحل",
    pin: "تثبيت",
    unpin: "إلغاء التثبيت",
    statusOpen: "فتح",
    statusClosed: "إغلاق",
    statusArchived: "أرشفة",
    statusSpam: "سبام",
    unknown: "غير معروف",
    unread: "غير مقروء",
    read: "مقروء",
    message: "رسالة",
    attachment: "مرفق",
    sender: "المرسل",
    assignedTo: "المسؤول",
    noAssigned: "غير معيّن",
    contactPhone: "رقم التواصل",
    sessionName: "اسم الجلسة",
    lastActivity: "آخر نشاط",
    preview: "المعاينة",
    filters: "الفلاتر",
    all: "الكل",
    onlyUnread: "غير المقروء فقط",
    filterOpen: "مفتوحة",
    filterClosed: "مغلقة",
    filterArchived: "مؤرشفة",
    filterSpam: "سبام",
    markReadSuccess: "تم تعليم المحادثة كمقروءة",
    pinSuccess: "تم تحديث حالة التثبيت",
    resolveSuccess: "تم تحديث حالة الحل",
    statusSuccess: "تم تحديث حالة المحادثة",
    actionFailed: "تعذر تنفيذ العملية",
    noRecipient: "بدون رقم",
    connectedNow: "الربط يعمل بشكل سليم",
    disconnectedNow: "الربط غير متصل حاليًا",
    lastCheck: "آخر فحص",
    viewSettings: "عرض الإعدادات",
    fromSystem: "من النظام",
    fromContact: "من جهة الاتصال",
    closedLabel: "مغلقة",
    archivedLabel: "مؤرشفة",
    spamLabel: "سبام",
    openLabel: "مفتوحة",
    resolvedLabel: "محلولة",
    unresolvedLabel: "غير محلولة",
    pinnedLabel: "مثبتة",
    mediaMessage: "رسالة وسائط",
    comingSoon: "قريبًا",
    composerPlaceholder: "اكتب رسالتك هنا...",
    send: "إرسال",
    loading: "جاري التحميل...",
  },
  en: {
    centerBadge: "System WhatsApp Inbox",
    pageTitle: "System WhatsApp Inbox",
    pageDescription:
      "Manage inbound conversations, review messages, and control conversation state from one professional interface.",
    refresh: "Refresh",
    settings: "Settings",
    conversations: "Conversations",
    connected: "Connected",
    disconnected: "Disconnected",
    active: "Active",
    inactive: "Inactive",
    whatsappConnection: "Connection & Inbox Status",
    whatsappConnectionDesc:
      "Quick view of connectivity, provider, and inbox statistics.",
    phoneNumberId: "Phone Number ID",
    notConfigured: "Not configured",
    webhook: "Webhook",
    verified: "Verified",
    pendingOrUnknown: "Pending / Unknown",
    provider: "Provider",
    systemStatus: "System Status",
    totalConversations: "Total Conversations",
    unreadConversations: "Unread",
    resolvedConversations: "Resolved",
    pinnedConversations: "Pinned",
    openConversations: "Open",
    quickAccess: "Quick Access",
    quickAccessDesc:
      "Quickly jump to the rest of the system WhatsApp modules.",
    logs: "Logs",
    templates: "Templates",
    broadcastsLabel: "Broadcasts",
    smartSummary: "Inbox Summary",
    smartSummaryDesc: "Fast statistics for current conversations",
    systemScope: "System Scope",
    companyScope: "Company Scope",
    enabled: "Enabled",
    undefined: "Undefined",
    pendingTemplates: "Pending Templates",
    failedMessages: "Failed Messages",
    dashboardLoadError: "Unable to load the system WhatsApp inbox",
    searchPlaceholder: "Search by name, number, or latest message...",
    inboxListTitle: "Conversations",
    inboxListDesc: "All inbound conversations at system level",
    noConversations: "No conversations yet",
    noConversationsDesc:
      "Inbound conversations will appear here automatically once the first message arrives.",
    conversationDetails: "Conversation Details",
    messagesTitle: "Messages",
    messagesDesc: "Display the current conversation with all linked messages",
    noMessagesYet: "No messages in this conversation",
    noMessagesDesc:
      "Messages will appear here automatically as soon as they arrive.",
    selectConversation: "Select a conversation",
    selectConversationDesc:
      "Choose a conversation from the sidebar to view details and messages.",
    markRead: "Mark as read",
    resolve: "Resolve",
    unresolve: "Unresolve",
    pin: "Pin",
    unpin: "Unpin",
    statusOpen: "Open",
    statusClosed: "Close",
    statusArchived: "Archive",
    statusSpam: "Spam",
    unknown: "Unknown",
    unread: "Unread",
    read: "Read",
    message: "Message",
    attachment: "Attachment",
    sender: "Sender",
    assignedTo: "Assigned To",
    noAssigned: "Unassigned",
    contactPhone: "Contact Phone",
    sessionName: "Session Name",
    lastActivity: "Last Activity",
    preview: "Preview",
    filters: "Filters",
    all: "All",
    onlyUnread: "Unread only",
    filterOpen: "Open",
    filterClosed: "Closed",
    filterArchived: "Archived",
    filterSpam: "Spam",
    markReadSuccess: "Conversation marked as read",
    pinSuccess: "Pinned state updated",
    resolveSuccess: "Resolved state updated",
    statusSuccess: "Conversation status updated",
    actionFailed: "Unable to complete the action",
    noRecipient: "No recipient",
    connectedNow: "Connection is healthy",
    disconnectedNow: "Connection is currently offline",
    lastCheck: "Last check",
    viewSettings: "View settings",
    fromSystem: "From system",
    fromContact: "From contact",
    closedLabel: "Closed",
    archivedLabel: "Archived",
    spamLabel: "Spam",
    openLabel: "Open",
    resolvedLabel: "Resolved",
    unresolvedLabel: "Unresolved",
    pinnedLabel: "Pinned",
    mediaMessage: "Media message",
    comingSoon: "Coming soon",
    composerPlaceholder: "Write your message here...",
    send: "Send",
    loading: "Loading...",
  },
} as const