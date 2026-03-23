"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  ArrowLeft,
  BellRing,
  Eye,
  Loader2,
  Megaphone,
  Play,
  Plus,
  RefreshCw,
  Search,
  Send,
  Target,
  TrendingUp,
  Users,
  XCircle,
  CheckCircle2,
  Clock3,
  AlertCircle,
  FileText,
} from "lucide-react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

type Locale = "ar" | "en"

type WhatsAppBroadcastItem = {
  id: number
  title?: string
  status?: string
  recipient_count?: number
  total_recipients?: number
  sent_count?: number
  failed_count?: number
  created_at?: string
  updated_at?: string
  message_preview?: string
  message_body?: string
  audience_type?: string
  message_type?: string
  scheduled_at?: string | null
  started_at?: string | null
  completed_at?: string | null
  attachment_url?: string
  attachment_name?: string
  mime_type?: string
}

type BroadcastRecipientItem = {
  id: number
  recipient_name?: string
  recipient_phone?: string
  recipient_type?: string
  delivery_status?: string
  external_message_id?: string
  failure_reason?: string
  company_id?: number | null
  user_id?: number | null
  employee_id?: number | null
  sent_at?: string | null
  delivered_at?: string | null
  read_at?: string | null
  created_at?: string | null
}

type BroadcastsResponse = {
  success?: boolean
  count?: number
  results?: WhatsAppBroadcastItem[]
  data?: WhatsAppBroadcastItem[]
  message?: string
  error?: string
}

type CreateBroadcastResponse = {
  success?: boolean
  message?: string
  data?: WhatsAppBroadcastItem
  errors?: Record<string, string>
  error?: string
}

type BroadcastDetailResponse = {
  success?: boolean
  message?: string
  error?: string
  data?: WhatsAppBroadcastItem
  recipients?: BroadcastRecipientItem[]
  recipients_count?: number
}

type ExecuteBroadcastResponse = {
  success?: boolean
  message?: string
  error?: string
  data?: WhatsAppBroadcastItem
  stats?: {
    total_recipients?: number
    sent_count?: number
    failed_count?: number
  }
}

type AudienceType =
  | "ALL_COMPANIES"
  | "SYSTEM_USERS"
  | "RAW_NUMBERS"

type BroadcastStatus =
  | "DRAFT"
  | "SCHEDULED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"

const API = {
  broadcasts: "/api/system/whatsapp/broadcasts/",
  createBroadcast: "/api/system/whatsapp/broadcasts/create/",
  detail: (id: number) => `/api/system/whatsapp/broadcasts/${id}/`,
  execute: (id: number) => `/api/system/whatsapp/broadcasts/${id}/execute/`,
} as const

const translations = {
  ar: {
    title: "البث الجماعي للنظام",
    description: "إدارة ومتابعة الحملات والإرسال الجماعي من لوحة النظام.",
    back: "رجوع",
    refresh: "تحديث",
    createBroadcast: "إنشاء بث جديد",
    creating: "جارٍ الإنشاء...",
    totalCampaigns: "إجمالي الحملات",
    completed: "المكتملة",
    running: "قيد التنفيذ",
    totalRecipients: "إجمالي المستلمين",
    searchTitle: "بحث",
    searchDesc: "ابحث عن الحملة بالعنوان أو الحالة",
    searchPlaceholder: "عنوان الحملة أو الحالة...",
    noCampaigns: "لا توجد حملات بث",
    noCampaignsDesc: "سيظهر هنا أي بث جماعي يتم إنشاؤه لاحقًا.",
    createdAt: "تاريخ الإنشاء",
    updatedAt: "آخر تحديث",
    recipients: "المستلمون",
    sent: "تم الإرسال",
    failed: "فشل",
    messagePreview: "معاينة الرسالة",
    noPreview: "لا توجد معاينة متاحة لهذه الحملة.",
    details: "التفاصيل",
    viewDetails: "عرض التفاصيل",
    execute: "تنفيذ",
    forceExecute: "تنفيذ بالقوة",
    executing: "جارٍ التنفيذ...",
    executeSuccess: "تم تنفيذ الحملة بنجاح",
    executeFailed: "تعذر تنفيذ الحملة",
    hasFailures: "توجد إخفاقات",
    failedLoad: "تعذر تحميل البث الجماعي",
    createFailed: "تعذر إنشاء البث الجماعي",
    createSuccess: "تم إنشاء البث الجماعي بنجاح",
    detailFailed: "تعذر تحميل تفاصيل الحملة",
    completedLabel: "مكتمل",
    runningLabel: "قيد التنفيذ",
    scheduledLabel: "مجدول",
    failedLabel: "فشل",
    draftLabel: "مسودة",
    cancelledLabel: "ملغي",
    unknown: "غير معروف",
    createDialogTitle: "إنشاء حملة بث جماعي",
    createDialogDesc: "أنشئ حملة جديدة مع نص الرسالة والجمهور المستهدف.",
    titleLabel: "عنوان الحملة",
    titlePlaceholder: "مثال: تنبيه تجديد الاشتراك",
    messageLabel: "نص الرسالة",
    messagePlaceholder: "اكتب نص الرسالة التي سيتم إرسالها...",
    audienceLabel: "نوع الجمهور",
    audiencePlaceholder: "اختر نوع الجمهور",
    rawNumbersLabel: "أرقام الجوال",
    rawNumbersDesc: "أدخل كل رقم في سطر مستقل عند اختيار أرقام مخصصة.",
    rawNumbersPlaceholder: "9665xxxxxxxx\n9665xxxxxxxx",
    statusLabel: "الحالة",
    statusPlaceholder: "اختر الحالة الابتدائية",
    audienceAllCompanies: "كل الشركات",
    audienceSystemUsers: "مستخدمو النظام",
    audienceRawNumbers: "أرقام مخصصة",
    save: "حفظ",
    cancel: "إلغاء",
    close: "إغلاق",
    messageRequired: "نص الرسالة مطلوب",
    titleRequired: "عنوان الحملة مطلوب",
    csrfMissing:
      "تعذر العثور على CSRF Token. حدّث الصفحة أو تأكد من تحميل الجلسة بشكل صحيح.",
    detailDialogTitle: "تفاصيل الحملة",
    detailDialogDesc: "عرض معلومات الحملة والمستلمين ونتائج الإرسال.",
    recipientName: "اسم المستلم",
    recipientPhone: "رقم المستلم",
    recipientType: "نوع المستلم",
    deliveryStatus: "حالة التسليم",
    failureReason: "سبب الفشل",
    noRecipients: "لا يوجد مستلمون بعد",
    startedAt: "بدأت في",
    completedAt: "اكتملت في",
    audienceType: "الجمهور",
    messageType: "نوع الرسالة",
    stats: "الإحصائيات",
    sentCount: "المرسل",
    failedCount: "الفاشل",
    totalCount: "الإجمالي",
    rawRecipient: "مستلم مخصص",
    companyRecipient: "شركة",
    companyAdminRecipient: "مدير شركة",
    userRecipient: "مستخدم",
    employeeRecipient: "موظف",
    queuedStatus: "في الانتظار",
    sentStatus: "تم الإرسال",
    deliveredStatus: "تم التسليم",
    readStatus: "تمت القراءة",
    failedStatus: "فشل",
    cancelledStatus: "ملغي",
    draftStatus: "مسودة",
    loading: "جاري تحميل الحملات...",
    badgeTitle: "WhatsApp Broadcasts",
  },
  en: {
    title: "System Broadcasts",
    description: "Manage and monitor campaigns and bulk sending from the system panel.",
    back: "Back",
    refresh: "Refresh",
    createBroadcast: "Create Broadcast",
    creating: "Creating...",
    totalCampaigns: "Total Campaigns",
    completed: "Completed",
    running: "Running",
    totalRecipients: "Total Recipients",
    searchTitle: "Search",
    searchDesc: "Search campaign by title or status",
    searchPlaceholder: "Campaign title or status...",
    noCampaigns: "No broadcasts found",
    noCampaignsDesc: "Any bulk broadcast created later will appear here.",
    createdAt: "Created At",
    updatedAt: "Updated At",
    recipients: "Recipients",
    sent: "Sent",
    failed: "Failed",
    messagePreview: "Message Preview",
    noPreview: "No preview available for this campaign.",
    details: "Details",
    viewDetails: "View Details",
    execute: "Execute",
    forceExecute: "Force Execute",
    executing: "Executing...",
    executeSuccess: "Broadcast executed successfully",
    executeFailed: "Unable to execute broadcast",
    hasFailures: "There are failures",
    failedLoad: "Unable to load broadcasts",
    createFailed: "Unable to create broadcast",
    createSuccess: "Broadcast created successfully",
    detailFailed: "Unable to load broadcast detail",
    completedLabel: "Completed",
    runningLabel: "Running",
    scheduledLabel: "Scheduled",
    failedLabel: "Failed",
    draftLabel: "Draft",
    cancelledLabel: "Cancelled",
    unknown: "Unknown",
    createDialogTitle: "Create Broadcast Campaign",
    createDialogDesc: "Create a new campaign with message body and target audience.",
    titleLabel: "Campaign Title",
    titlePlaceholder: "Example: Subscription Renewal Alert",
    messageLabel: "Message Body",
    messagePlaceholder: "Write the message that will be sent...",
    audienceLabel: "Audience Type",
    audiencePlaceholder: "Choose audience type",
    rawNumbersLabel: "Phone Numbers",
    rawNumbersDesc: "Enter one number per line when using raw numbers.",
    rawNumbersPlaceholder: "9665xxxxxxxx\n9665xxxxxxxx",
    statusLabel: "Status",
    statusPlaceholder: "Choose initial status",
    audienceAllCompanies: "All Companies",
    audienceSystemUsers: "System Users",
    audienceRawNumbers: "Raw Numbers",
    save: "Save",
    cancel: "Cancel",
    close: "Close",
    messageRequired: "Message body is required",
    titleRequired: "Campaign title is required",
    csrfMissing:
      "CSRF token was not found. Refresh the page or make sure the session is loaded correctly.",
    detailDialogTitle: "Broadcast Detail",
    detailDialogDesc: "View campaign info, recipients, and delivery results.",
    recipientName: "Recipient Name",
    recipientPhone: "Recipient Phone",
    recipientType: "Recipient Type",
    deliveryStatus: "Delivery Status",
    failureReason: "Failure Reason",
    noRecipients: "No recipients yet",
    startedAt: "Started At",
    completedAt: "Completed At",
    audienceType: "Audience",
    messageType: "Message Type",
    stats: "Statistics",
    sentCount: "Sent",
    failedCount: "Failed",
    totalCount: "Total",
    rawRecipient: "Raw Recipient",
    companyRecipient: "Company",
    companyAdminRecipient: "Company Admin",
    userRecipient: "User",
    employeeRecipient: "Employee",
    queuedStatus: "Queued",
    sentStatus: "Sent",
    deliveredStatus: "Delivered",
    readStatus: "Read",
    failedStatus: "Failed",
    cancelledStatus: "Cancelled",
    draftStatus: "Draft",
    loading: "Loading broadcasts...",
    badgeTitle: "WhatsApp Broadcasts",
  },
} as const

function detectLocale(): Locale {
  if (typeof document === "undefined") return "ar"
  const htmlLang = document.documentElement.lang?.toLowerCase() || ""
  return htmlLang.startsWith("en") ? "en" : "ar"
}

function getApiBaseCandidates(): string[] {
  const envBase = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "")
  const browserBase =
    typeof window !== "undefined" ? window.location.origin.replace(/\/$/, "") : ""

  return Array.from(new Set([envBase, browserBase, ""]))
}

function buildGetCandidateUrls(path: string): string[] {
  const cleanPath = path.startsWith("/") ? path : `/${path}`
  const urls = new Set<string>()

  for (const base of getApiBaseCandidates()) {
    const full = base ? `${base}${cleanPath}` : cleanPath
    const noTrailing = full.endsWith("/") ? full.slice(0, -1) : full
    urls.add(full)
    urls.add(noTrailing)
    urls.add(`${noTrailing}/`)
  }

  return Array.from(urls).filter(Boolean)
}

function buildStrictUrl(path: string): string {
  const cleanPath = path.startsWith("/") ? path : `/${path}`
  const envBase = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "")
  const browserBase =
    typeof window !== "undefined" ? window.location.origin.replace(/\/$/, "") : ""

  const base = envBase || browserBase || ""
  return base ? `${base}${cleanPath}` : cleanPath
}

function getCsrfToken(): string {
  if (typeof document === "undefined") return ""
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ""
}

async function fetchJson<T>(path: string): Promise<T> {
  const candidates = buildGetCandidateUrls(path)
  let lastError: Error | null = null

  for (const url of candidates) {
    try {
      const response = await fetch(url, {
        method: "GET",
        credentials: "include",
        cache: "no-store",
        headers: { Accept: "application/json" },
      })

      const data = (await response.json()) as T & {
        message?: string
        error?: string
      }

      if (!response.ok) {
        const msg =
          data?.message ||
          data?.error ||
          `GET ${url} failed with ${response.status}`
        lastError = new Error(msg)
        continue
      }

      return data
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("Unknown fetch error")
    }
  }

  throw lastError || new Error(`Failed to fetch ${path}`)
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const csrfToken = getCsrfToken()
  const url = buildStrictUrl(path)

  const response = await fetch(url, {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify(body),
  })

  const data = (await response.json()) as T & {
    success?: boolean
    message?: string
    error?: string
  }

  if (!response.ok) {
    const msg =
      data?.message ||
      data?.error ||
      `POST ${url} failed with ${response.status}`
    throw new Error(msg)
  }

  return data
}

function formatDate(value: string | null | undefined) {
  if (!value) return "—"
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return "—"

  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    numberingSystem: "latn",
  }).format(d)
}

function formatNumber(value: number | null | undefined) {
  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
  }).format(Number(value ?? 0))
}

function getStatusTone(status?: string) {
  const v = (status || "").toUpperCase()

  if (["COMPLETED", "SENT", "DELIVERED", "READ"].includes(v)) {
    return {
      className: "border-emerald-200 bg-emerald-50 text-emerald-700",
      icon: CheckCircle2,
    }
  }

  if (["RUNNING", "SCHEDULED", "QUEUED"].includes(v)) {
    return {
      className: "border-amber-200 bg-amber-50 text-amber-700",
      icon: Clock3,
    }
  }

  if (["FAILED", "CANCELLED"].includes(v)) {
    return {
      className: "border-red-200 bg-red-50 text-red-700",
      icon: AlertCircle,
    }
  }

  return {
    className: "border-slate-200 bg-slate-50 text-slate-700",
    icon: FileText,
  }
}

function StatusBadge({
  status,
  locale,
}: {
  status?: string
  locale: Locale
}) {
  const tone = getStatusTone(status)
  const Icon = tone.icon

  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
        tone.className,
      ].join(" ")}
    >
      <Icon className="me-1 h-3.5 w-3.5" />
      {statusLabel(status, locale)}
    </span>
  )
}

function statusLabel(status: string | undefined, locale: Locale) {
  const v = (status || "").toUpperCase()
  const map: Record<string, { ar: string; en: string }> = {
    COMPLETED: { ar: "مكتمل", en: "Completed" },
    RUNNING: { ar: "قيد التنفيذ", en: "Running" },
    SCHEDULED: { ar: "مجدول", en: "Scheduled" },
    FAILED: { ar: "فشل", en: "Failed" },
    DRAFT: { ar: "مسودة", en: "Draft" },
    CANCELLED: { ar: "ملغي", en: "Cancelled" },
    QUEUED: { ar: "في الانتظار", en: "Queued" },
    SENT: { ar: "تم الإرسال", en: "Sent" },
    DELIVERED: { ar: "تم التسليم", en: "Delivered" },
    READ: { ar: "تمت القراءة", en: "Read" },
  }
  return map[v]?.[locale] || translations[locale].unknown
}

function recipientTypeLabel(value: string | undefined, locale: Locale) {
  const v = (value || "").toUpperCase()
  const map: Record<string, { ar: string; en: string }> = {
    RAW: { ar: "مستلم مخصص", en: "Raw Recipient" },
    COMPANY: { ar: "شركة", en: "Company" },
    COMPANY_ADMIN: { ar: "مدير شركة", en: "Company Admin" },
    USER: { ar: "مستخدم", en: "User" },
    EMPLOYEE: { ar: "موظف", en: "Employee" },
  }
  return map[v]?.[locale] || value || translations[locale].unknown
}

function audienceLabel(value: string | undefined, locale: Locale) {
  const v = (value || "").toUpperCase()
  const map: Record<string, { ar: string; en: string }> = {
    ALL_COMPANIES: { ar: "كل الشركات", en: "All Companies" },
    SYSTEM_USERS: { ar: "مستخدمو النظام", en: "System Users" },
    RAW_NUMBERS: { ar: "أرقام مخصصة", en: "Raw Numbers" },
  }
  return map[v]?.[locale] || value || translations[locale].unknown
}

function normalizeBroadcastsResponse(
  payload: BroadcastsResponse | null | undefined
): WhatsAppBroadcastItem[] {
  const rows = payload?.results || payload?.data || []
  return rows.map((item) => ({
    ...item,
    recipient_count: Number(item.recipient_count ?? item.total_recipients ?? 0),
    message_preview: item.message_preview || item.message_body || "",
  }))
}

export default function SystemWhatsAppBroadcastsPage() {
  const [locale, setLocale] = useState<Locale>("ar")
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [creating, setCreating] = useState(false)
  const [broadcasts, setBroadcasts] = useState<WhatsAppBroadcastItem[]>([])
  const [query, setQuery] = useState("")
  const [createOpen, setCreateOpen] = useState(false)

  const [detailOpen, setDetailOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailData, setDetailData] = useState<WhatsAppBroadcastItem | null>(null)
  const [detailRecipients, setDetailRecipients] = useState<BroadcastRecipientItem[]>([])

  const [executingId, setExecutingId] = useState<number | null>(null)

  const [title, setTitle] = useState("")
  const [messageBody, setMessageBody] = useState("")
  const [audienceType, setAudienceType] = useState<AudienceType>("ALL_COMPANIES")
  const [status, setStatus] = useState<BroadcastStatus>("DRAFT")
  const [rawNumbers, setRawNumbers] = useState("")

  useEffect(() => {
    setLocale(detectLocale())

    const observer = new MutationObserver(() => {
      setLocale(detectLocale())
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    return () => observer.disconnect()
  }, [])

  const t = translations[locale]
  const isArabic = locale === "ar"

  const resetCreateForm = () => {
    setTitle("")
    setMessageBody("")
    setAudienceType("ALL_COMPANIES")
    setStatus("DRAFT")
    setRawNumbers("")
  }

  const loadBroadcasts = useCallback(
    async (isRefresh = false) => {
      try {
        if (isRefresh) setRefreshing(true)
        else setLoading(true)

        const data = await fetchJson<BroadcastsResponse>(API.broadcasts)
        setBroadcasts(normalizeBroadcastsResponse(data))
      } catch (error) {
        console.error("System WhatsApp broadcasts load error:", error)
        toast.error(error instanceof Error ? error.message : t.failedLoad)
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [t.failedLoad]
  )

  useEffect(() => {
    loadBroadcasts()
  }, [loadBroadcasts])

  const handleCreateBroadcast = async () => {
    const cleanTitle = title.trim()
    const cleanMessage = messageBody.trim()
    const csrfToken = getCsrfToken()

    if (!cleanTitle) {
      toast.error(t.titleRequired)
      return
    }

    if (!cleanMessage) {
      toast.error(t.messageRequired)
      return
    }

    if (!csrfToken) {
      toast.error(t.csrfMissing)
      return
    }

    const parsedRawNumbers = rawNumbers
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)

    try {
      setCreating(true)

      const response = await postJson<CreateBroadcastResponse>(
        API.createBroadcast,
        {
          title: cleanTitle,
          message_type: "TEXT",
          message_body: cleanMessage,
          audience_type: audienceType,
          raw_numbers: audienceType === "RAW_NUMBERS" ? parsedRawNumbers : [],
          status,
        }
      )

      if (!response?.success) {
        throw new Error(response?.message || response?.error || t.createFailed)
      }

      toast.success(response?.message || t.createSuccess)
      setCreateOpen(false)
      resetCreateForm()
      await loadBroadcasts(true)
    } catch (error) {
      console.error("Create broadcast error:", error)
      toast.error(error instanceof Error ? error.message : t.createFailed)
    } finally {
      setCreating(false)
    }
  }

  const handleOpenDetail = async (broadcastId: number) => {
    try {
      setDetailOpen(true)
      setDetailLoading(true)

      const response = await fetchJson<BroadcastDetailResponse>(API.detail(broadcastId))
      setDetailData(response?.data || null)
      setDetailRecipients(response?.recipients || [])
    } catch (error) {
      console.error("Broadcast detail load error:", error)
      toast.error(error instanceof Error ? error.message : t.detailFailed)
      setDetailOpen(false)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleExecuteBroadcast = async (broadcastId: number, force = false) => {
    const csrfToken = getCsrfToken()

    if (!csrfToken) {
      toast.error(t.csrfMissing)
      return
    }

    try {
      setExecutingId(broadcastId)

      const response = await postJson<ExecuteBroadcastResponse>(
        API.execute(broadcastId),
        { force }
      )

      if (!response?.success) {
        throw new Error(response?.message || response?.error || t.executeFailed)
      }

      toast.success(response?.message || t.executeSuccess)
      await loadBroadcasts(true)

      if (detailOpen && detailData?.id === broadcastId) {
        await handleOpenDetail(broadcastId)
      }
    } catch (error) {
      console.error("Broadcast execute error:", error)
      toast.error(error instanceof Error ? error.message : t.executeFailed)
    } finally {
      setExecutingId(null)
    }
  }

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return broadcasts.filter((item) => {
      const haystack = [
        item.title,
        item.status,
        item.message_preview,
        item.audience_type,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()

      return !q || haystack.includes(q)
    })
  }, [broadcasts, query])

  const stats = useMemo(() => {
    const total = broadcasts.length
    const completed = broadcasts.filter(
      (x) => (x.status || "").toUpperCase() === "COMPLETED"
    ).length
    const running = broadcasts.filter((x) =>
      ["RUNNING", "SCHEDULED"].includes((x.status || "").toUpperCase())
    ).length
    const recipients = broadcasts.reduce(
      (acc, item) => acc + Number(item.recipient_count || 0),
      0
    )

    return { total, completed, running, recipients }
  }, [broadcasts])

  return (
    <div dir={isArabic ? "rtl" : "ltr"} className="space-y-6 p-4 md:p-6">
      <Card className="overflow-hidden border-0 shadow-sm">
        <CardContent className="p-0">
          <div className="relative bg-gradient-to-br from-background via-background to-muted/40 p-5 md:p-6">
            <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 rounded-full border bg-background/80 px-3 py-1 text-xs font-medium text-muted-foreground shadow-sm backdrop-blur">
                  <Megaphone className="h-3.5 w-3.5 text-primary" />
                  <span>{t.badgeTitle}</span>
                </div>

                <div className="space-y-1">
                  <h1 className="text-2xl font-bold tracking-tight md:text-3xl">{t.title}</h1>
                  <p className="max-w-2xl text-sm leading-6 text-muted-foreground md:text-base">
                    {t.description}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button asChild variant="outline" className="gap-2">
                  <Link href="/system/whatsapp">
                    <ArrowLeft className="h-4 w-4" />
                    {t.back}
                  </Link>
                </Button>

                <Button
                  variant="outline"
                  onClick={() => loadBroadcasts(true)}
                  disabled={refreshing}
                  className="gap-2"
                >
                  {refreshing ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  {t.refresh}
                </Button>

                <Dialog
                  open={createOpen}
                  onOpenChange={(open) => {
                    setCreateOpen(open)
                    if (!open) resetCreateForm()
                  }}
                >
                  <DialogTrigger asChild>
                    <Button className="gap-2">
                      <Plus className="h-4 w-4" />
                      {t.createBroadcast}
                    </Button>
                  </DialogTrigger>

                  <DialogContent className="sm:max-w-2xl">
                    <DialogHeader>
                      <DialogTitle>{t.createDialogTitle}</DialogTitle>
                      <DialogDescription>{t.createDialogDesc}</DialogDescription>
                    </DialogHeader>

                    <div className="grid gap-4 py-2">
                      <div className="grid gap-2">
                        <Label htmlFor="broadcast-title">{t.titleLabel}</Label>
                        <Input
                          id="broadcast-title"
                          value={title}
                          onChange={(e) => setTitle(e.target.value)}
                          placeholder={t.titlePlaceholder}
                        />
                      </div>

                      <div className="grid gap-2">
                        <Label htmlFor="broadcast-message">{t.messageLabel}</Label>
                        <Textarea
                          id="broadcast-message"
                          value={messageBody}
                          onChange={(e) => setMessageBody(e.target.value)}
                          placeholder={t.messagePlaceholder}
                          className="min-h-[140px]"
                        />
                      </div>

                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="grid gap-2">
                          <Label>{t.audienceLabel}</Label>
                          <Select
                            value={audienceType}
                            onValueChange={(value: AudienceType) => setAudienceType(value)}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder={t.audiencePlaceholder} />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="ALL_COMPANIES">
                                {t.audienceAllCompanies}
                              </SelectItem>
                              <SelectItem value="SYSTEM_USERS">
                                {t.audienceSystemUsers}
                              </SelectItem>
                              <SelectItem value="RAW_NUMBERS">
                                {t.audienceRawNumbers}
                              </SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="grid gap-2">
                          <Label>{t.statusLabel}</Label>
                          <Select
                            value={status}
                            onValueChange={(value: BroadcastStatus) => setStatus(value)}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder={t.statusPlaceholder} />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="DRAFT">{t.draftLabel}</SelectItem>
                              <SelectItem value="SCHEDULED">{t.scheduledLabel}</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      {audienceType === "RAW_NUMBERS" ? (
                        <div className="grid gap-2">
                          <Label htmlFor="broadcast-raw-numbers">{t.rawNumbersLabel}</Label>
                          <Textarea
                            id="broadcast-raw-numbers"
                            dir="ltr"
                            value={rawNumbers}
                            onChange={(e) => setRawNumbers(e.target.value)}
                            placeholder={t.rawNumbersPlaceholder}
                            className="min-h-[120px]"
                          />
                          <p className="text-xs text-muted-foreground">
                            {t.rawNumbersDesc}
                          </p>
                        </div>
                      ) : null}
                    </div>

                    <DialogFooter className="gap-2 sm:justify-end">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setCreateOpen(false)
                          resetCreateForm()
                        }}
                        disabled={creating}
                      >
                        {t.cancel}
                      </Button>

                      <Button
                        type="button"
                        onClick={handleCreateBroadcast}
                        disabled={creating}
                        className="gap-2"
                      >
                        {creating ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Send className="h-4 w-4" />
                        )}
                        {creating ? t.creating : t.save}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="border-0 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.totalCampaigns}</span>
              <Megaphone className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-2xl font-bold tabular-nums" dir="ltr">
              {formatNumber(stats.total)}
            </p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.completed}</span>
              <Send className="h-4 w-4 text-emerald-600" />
            </div>
            <p className="mt-3 text-2xl font-bold tabular-nums" dir="ltr">
              {formatNumber(stats.completed)}
            </p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.running}</span>
              <TrendingUp className="h-4 w-4 text-amber-600" />
            </div>
            <p className="mt-3 text-2xl font-bold tabular-nums" dir="ltr">
              {formatNumber(stats.running)}
            </p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.totalRecipients}</span>
              <Users className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-2xl font-bold tabular-nums" dir="ltr">
              {formatNumber(stats.recipients)}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle>{t.searchTitle}</CardTitle>
          <CardDescription>{t.searchDesc}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative max-w-xl">
            <Search className="pointer-events-none absolute end-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t.searchPlaceholder}
              className="pe-10"
            />
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        {loading ? (
          <Card className="col-span-full border-0 shadow-sm">
            <CardContent className="flex min-h-[260px] items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">{t.loading}</p>
              </div>
            </CardContent>
          </Card>
        ) : filtered.length === 0 ? (
          <Card className="col-span-full border-0 shadow-sm">
            <CardContent className="p-10 text-center">
              <BellRing className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
              <p className="font-medium">{t.noCampaigns}</p>
              <p className="mt-1 text-sm text-muted-foreground">{t.noCampaignsDesc}</p>
            </CardContent>
          </Card>
        ) : (
          filtered.map((item) => {
            const isExecuting = executingId === item.id
            const currentStatus = (item.status || "").toUpperCase()
            const canExecute = ["DRAFT", "SCHEDULED", "FAILED", "CANCELLED"].includes(currentStatus)
            const canForceExecute = ["COMPLETED", "RUNNING", "FAILED", "CANCELLED"].includes(currentStatus)

            return (
              <Card
                key={item.id}
                className="border-0 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
              >
                <CardHeader>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <CardTitle className="text-lg">
                        {item.title || `Broadcast #${formatNumber(item.id)}`}
                      </CardTitle>
                      <CardDescription className="mt-1" dir="ltr">
                        {t.createdAt}: {formatDate(item.created_at)}
                      </CardDescription>
                    </div>

                    <StatusBadge status={item.status} locale={locale} />
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">{t.recipients}</p>
                      <p className="mt-1 text-sm font-semibold tabular-nums" dir="ltr">
                        {formatNumber(item.recipient_count ?? 0)}
                      </p>
                    </div>
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">{t.sent}</p>
                      <p className="mt-1 text-sm font-semibold tabular-nums" dir="ltr">
                        {formatNumber(item.sent_count ?? 0)}
                      </p>
                    </div>
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">{t.failed}</p>
                      <p className="mt-1 text-sm font-semibold text-destructive tabular-nums" dir="ltr">
                        {formatNumber(item.failed_count ?? 0)}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-xl border bg-muted/30 p-4">
                    <p className="text-xs text-muted-foreground">{t.messagePreview}</p>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-6">
                      {item.message_preview || t.noPreview}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-2"
                      onClick={() => handleOpenDetail(item.id)}
                    >
                      <Eye className="h-4 w-4" />
                      {t.viewDetails}
                    </Button>

                    {canExecute ? (
                      <Button
                        size="sm"
                        className="gap-2"
                        onClick={() => handleExecuteBroadcast(item.id, false)}
                        disabled={isExecuting}
                      >
                        {isExecuting ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                        {isExecuting ? t.executing : t.execute}
                      </Button>
                    ) : null}

                    {canForceExecute ? (
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-2"
                        onClick={() => handleExecuteBroadcast(item.id, true)}
                        disabled={isExecuting}
                      >
                        {isExecuting ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Target className="h-4 w-4" />
                        )}
                        {t.forceExecute}
                      </Button>
                    ) : null}

                    {(item.failed_count || 0) > 0 ? (
                      <Badge variant="destructive" className="gap-1">
                        <XCircle className="h-3.5 w-3.5" />
                        {t.hasFailures}
                      </Badge>
                    ) : null}
                  </div>
                </CardContent>
              </Card>
            )
          })
        )}
      </div>

      <Dialog
        open={detailOpen}
        onOpenChange={(open) => {
          setDetailOpen(open)
          if (!open) {
            setDetailData(null)
            setDetailRecipients([])
          }
        }}
      >
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-5xl">
          <DialogHeader>
            <DialogTitle>{t.detailDialogTitle}</DialogTitle>
            <DialogDescription>{t.detailDialogDesc}</DialogDescription>
          </DialogHeader>

          {detailLoading ? (
            <div className="flex min-h-[240px] items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : !detailData ? (
            <div className="py-10 text-center text-sm text-muted-foreground">
              {t.detailFailed}
            </div>
          ) : (
            <div className="space-y-6">
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="min-w-0">
                      <CardTitle>{detailData.title || `Broadcast #${formatNumber(detailData.id)}`}</CardTitle>
                      <CardDescription dir="ltr">
                        {t.createdAt}: {formatDate(detailData.created_at)}
                      </CardDescription>
                    </div>

                    <StatusBadge status={detailData.status} locale={locale} />
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">{t.audienceType}</p>
                      <p className="mt-1 text-sm font-semibold">
                        {audienceLabel(detailData.audience_type, locale)}
                      </p>
                    </div>
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">{t.messageType}</p>
                      <p className="mt-1 text-sm font-semibold" dir="ltr">
                        {detailData.message_type || "—"}
                      </p>
                    </div>
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">{t.startedAt}</p>
                      <p className="mt-1 text-sm font-semibold" dir="ltr">
                        {formatDate(detailData.started_at)}
                      </p>
                    </div>
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">{t.completedAt}</p>
                      <p className="mt-1 text-sm font-semibold" dir="ltr">
                        {formatDate(detailData.completed_at)}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-xl border p-4">
                    <p className="text-sm font-semibold">{t.stats}</p>
                    <div className="mt-3 grid gap-3 md:grid-cols-3">
                      <div className="rounded-xl border p-3">
                        <p className="text-xs text-muted-foreground">{t.totalCount}</p>
                        <p className="mt-1 text-sm font-semibold tabular-nums" dir="ltr">
                          {formatNumber(detailData.total_recipients ?? detailData.recipient_count ?? 0)}
                        </p>
                      </div>
                      <div className="rounded-xl border p-3">
                        <p className="text-xs text-muted-foreground">{t.sentCount}</p>
                        <p className="mt-1 text-sm font-semibold tabular-nums" dir="ltr">
                          {formatNumber(detailData.sent_count ?? 0)}
                        </p>
                      </div>
                      <div className="rounded-xl border p-3">
                        <p className="text-xs text-muted-foreground">{t.failedCount}</p>
                        <p className="mt-1 text-sm font-semibold text-destructive tabular-nums" dir="ltr">
                          {formatNumber(detailData.failed_count ?? 0)}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-xl border bg-muted/30 p-4">
                    <p className="text-xs text-muted-foreground">{t.messagePreview}</p>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-6">
                      {detailData.message_preview || detailData.message_body || t.noPreview}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle>{t.recipients}</CardTitle>
                  <CardDescription dir="ltr">
                    {detailRecipients.length > 0 ? formatNumber(detailRecipients.length) : t.noRecipients}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {detailRecipients.length === 0 ? (
                    <div className="py-6 text-center text-sm text-muted-foreground">
                      {t.noRecipients}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {detailRecipients.map((recipient) => (
                        <div
                          key={recipient.id}
                          className="rounded-2xl border p-4"
                        >
                          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                            <div className="space-y-2">
                              <p className="text-sm font-semibold">
                                {recipient.recipient_name || "—"}
                              </p>
                              <p className="text-xs text-muted-foreground" dir="ltr">
                                {t.recipientPhone}: {recipient.recipient_phone || "—"}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {t.recipientType}: {recipientTypeLabel(recipient.recipient_type, locale)}
                              </p>
                              {recipient.failure_reason ? (
                                <p className="text-xs text-destructive">
                                  {t.failureReason}: {recipient.failure_reason}
                                </p>
                              ) : null}
                            </div>

                            <div className="flex flex-wrap items-center gap-2">
                              <StatusBadge status={recipient.delivery_status} locale={locale} />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setDetailOpen(false)}>
              {t.close}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}