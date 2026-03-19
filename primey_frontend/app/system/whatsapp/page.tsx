"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Activity,
  ArrowUpRight,
  BellRing,
  Bot,
  Building2,
  CheckCircle2,
  Clock3,
  FileText,
  Loader2,
  MessageCircle,
  MessageSquareText,
  RefreshCw,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  Users,
  Wifi,
  WifiOff,
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
import { Separator } from "@/components/ui/separator"

type Locale = "ar" | "en"

type WhatsAppStatusPayload = {
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

type WhatsAppSettingsPayload = {
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

type WhatsAppLogItem = {
  id: number
  status?: string
  direction?: string
  message_type?: string
  recipient_phone?: string
  template_name?: string
  created_at?: string
  provider_message_id?: string
  error_message?: string
}

type WhatsAppLogsPayload = {
  success?: boolean
  count?: number
  results?: WhatsAppLogItem[]
}

type WhatsAppTemplateItem = {
  id: number
  name?: string
  template_type?: string
  language?: string
  category?: string
  status?: string
  updated_at?: string
}

type WhatsAppTemplatesPayload = {
  success?: boolean
  count?: number
  results?: WhatsAppTemplateItem[]
}

type WhatsAppBroadcastItem = {
  id: number
  title?: string
  status?: string
  recipient_count?: number
  sent_count?: number
  failed_count?: number
  created_at?: string
}

type WhatsAppBroadcastsPayload = {
  success?: boolean
  count?: number
  results?: WhatsAppBroadcastItem[]
}

type DashboardState = {
  loading: boolean
  refreshing: boolean
  status: WhatsAppStatusPayload | null
  settings: WhatsAppSettingsPayload | null
  logs: WhatsAppLogItem[]
  templates: WhatsAppTemplateItem[]
  broadcasts: WhatsAppBroadcastItem[]
}

const API_PATHS = {
  status: "/api/system/whatsapp/status/",
  settings: "/api/system/whatsapp/settings/",
  logs: "/api/system/whatsapp/logs/",
  templates: "/api/system/whatsapp/templates/",
  broadcasts: "/api/system/whatsapp/broadcasts/",
} as const

const translations = {
  ar: {
    centerBadge: "System WhatsApp Center",
    pageTitle: "مركز واتساب للنظام",
    pageDescription: "إدارة الربط، القوالب، السجل، والبث الجماعي على مستوى النظام بالكامل.",
    refresh: "تحديث",
    settings: "الإعدادات",
    connected: "متصل",
    disconnected: "غير متصل",
    active: "نشط",
    inactive: "غير نشط",
    whatsappConnection: "حالة ربط واتساب",
    whatsappConnectionDesc: "نظرة سريعة على حالة المزود، التفعيل، والتحقق من الويبهوك.",
    phoneNumberId: "Phone Number ID",
    notConfigured: "غير مضبوط",
    webhook: "Webhook",
    verified: "موثق",
    pendingOrUnknown: "قيد الانتظار / غير معروف",
    systemStatus: "حالة النظام",
    approvedTemplates: "القوالب المعتمدة",
    sentMessages: "الرسائل المرسلة",
    broadcasts: "عمليات البث",
    lastCheck: "آخر فحص",
    outOf: "من أصل",
    failed: "الفاشلة",
    systemLevelReady: "مهيأة على مستوى النظام",
    quickAccess: "الوصول السريع",
    quickAccessDesc: "الانتقال إلى أهم أقسام واتساب للنظام بسرعة.",
    logs: "السجل",
    templates: "القوالب",
    broadcastsLabel: "البث الجماعي",
    smartSummary: "ملخص ذكي",
    smartSummaryDesc: "حالة واتساب للنظام باختصار",
    provider: "المزود",
    systemScope: "System Scope",
    companyScope: "Company Scope",
    enabled: "مفعل",
    undefined: "غير محدد",
    pendingTemplates: "Pending Templates",
    failedMessages: "Failed Messages",
    latestMessages: "آخر الرسائل",
    latestMessagesDesc: "أحدث الأنشطة في سجل رسائل واتساب على مستوى النظام.",
    viewAll: "عرض الكل",
    noMessagesYet: "لا توجد رسائل حتى الآن",
    noMessagesDesc: "سيظهر هنا آخر سجل إرسال بمجرد بدء الاستخدام.",
    noTemplatesYet: "لا توجد قوالب بعد",
    noBroadcastsYet: "لا توجد حملات بث بعد",
    latestTemplates: "آخر القوالب",
    latestTemplatesDesc: "أحدث القوالب المعرفة بالنظام",
    latestBroadcasts: "آخر حملات البث",
    latestBroadcastsDesc: "أحدث العمليات الجماعية",
    recipients: "المستلمون",
    sent: "المرسلة",
    untitledTemplate: "قالب بدون اسم",
    noRecipient: "بدون رقم مستلم",
    message: "رسالة",
    dashboardLoadError: "تعذر تحميل لوحة واتساب للنظام",
    settingsCardTitle: "الإعدادات",
    settingsCardDesc: "مزود الخدمة، التفعيل، مفاتيح الربط، وإعدادات الإرسال.",
    logsCardDesc: "تتبع الرسائل، الحالات، والفشل ومحاولات الإرسال.",
    templatesCardDesc: "إدارة قوالب التنبيهات والإشعارات الجاهزة للإرسال.",
    broadcastsCardDesc: "إرسال الحملات والتنبيهات إلى عدة مستلمين من لوحة النظام.",
  },
  en: {
    centerBadge: "System WhatsApp Center",
    pageTitle: "System WhatsApp Center",
    pageDescription: "Manage connection, templates, logs, and broadcasts across the entire system.",
    refresh: "Refresh",
    settings: "Settings",
    connected: "Connected",
    disconnected: "Disconnected",
    active: "Active",
    inactive: "Inactive",
    whatsappConnection: "WhatsApp Connection Status",
    whatsappConnectionDesc: "Quick overview of provider health, activation status, and webhook verification.",
    phoneNumberId: "Phone Number ID",
    notConfigured: "Not configured",
    webhook: "Webhook",
    verified: "Verified",
    pendingOrUnknown: "Pending / Unknown",
    systemStatus: "System Status",
    approvedTemplates: "Approved Templates",
    sentMessages: "Sent Messages",
    broadcasts: "Broadcasts",
    lastCheck: "Last check",
    outOf: "Out of",
    failed: "Failed",
    systemLevelReady: "Configured at system level",
    quickAccess: "Quick Access",
    quickAccessDesc: "Jump quickly to the most important WhatsApp system areas.",
    logs: "Logs",
    templates: "Templates",
    broadcastsLabel: "Broadcasts",
    smartSummary: "Smart Summary",
    smartSummaryDesc: "System WhatsApp status at a glance",
    provider: "Provider",
    systemScope: "System Scope",
    companyScope: "Company Scope",
    enabled: "Enabled",
    undefined: "Undefined",
    pendingTemplates: "Pending Templates",
    failedMessages: "Failed Messages",
    latestMessages: "Latest Messages",
    latestMessagesDesc: "Most recent activities in system-level WhatsApp message logs.",
    viewAll: "View all",
    noMessagesYet: "No messages yet",
    noMessagesDesc: "Recent sending activity will appear here once usage begins.",
    noTemplatesYet: "No templates yet",
    noBroadcastsYet: "No broadcasts yet",
    latestTemplates: "Latest Templates",
    latestTemplatesDesc: "Most recently defined templates in the system",
    latestBroadcasts: "Latest Broadcasts",
    latestBroadcastsDesc: "Most recent bulk operations",
    recipients: "Recipients",
    sent: "Sent",
    untitledTemplate: "Untitled Template",
    noRecipient: "No recipient number",
    message: "Message",
    dashboardLoadError: "Unable to load the system WhatsApp dashboard",
    settingsCardTitle: "Settings",
    settingsCardDesc: "Provider, activation, credentials, and sending configuration.",
    logsCardDesc: "Track messages, statuses, failures, and sending attempts.",
    templatesCardDesc: "Manage ready-made notification and alert templates.",
    broadcastsCardDesc: "Send campaigns and alerts to multiple recipients from the system panel.",
  },
} as const

function detectLocale(): Locale {
  if (typeof document === "undefined") return "ar"

  const htmlLang = document.documentElement.lang?.toLowerCase() || ""
  return htmlLang.startsWith("en") ? "en" : "ar"
}

function getApiBaseCandidates(): string[] {
  const fromEnv = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "")
  const fromWindow = typeof window !== "undefined" ? window.location.origin.replace(/\/$/, "") : ""

  return Array.from(new Set([fromEnv, fromWindow, ""]))
}

function buildCandidateUrls(path: string): string[] {
  const cleanPath = path.startsWith("/") ? path : `/${path}`
  const variants = new Set<string>()

  for (const base of getApiBaseCandidates()) {
    const full = base ? `${base}${cleanPath}` : cleanPath
    const withoutSlash = full.endsWith("/") ? full.slice(0, -1) : full
    const withSlash = `${withoutSlash}/`

    variants.add(full)
    variants.add(withoutSlash)
    variants.add(withSlash)
  }

  return Array.from(variants).filter(Boolean)
}

function formatDate(value: string | null | undefined, locale: Locale) {
  if (!value) return "—"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"

  return new Intl.DateTimeFormat(locale === "ar" ? "en-GB" : "en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

function statusLabel(status: string | undefined, locale: Locale) {
  const value = (status || "").toUpperCase()

  const labels: Record<string, { ar: string; en: string }> = {
    SENT: { ar: "تم الإرسال", en: "Sent" },
    DELIVERED: { ar: "تم التسليم", en: "Delivered" },
    READ: { ar: "تمت القراءة", en: "Read" },
    FAILED: { ar: "فشل", en: "Failed" },
    PENDING: { ar: "قيد الانتظار", en: "Pending" },
    APPROVED: { ar: "معتمد", en: "Approved" },
    REJECTED: { ar: "مرفوض", en: "Rejected" },
    DRAFT: { ar: "مسودة", en: "Draft" },
    RUNNING: { ar: "قيد التنفيذ", en: "Running" },
    COMPLETED: { ar: "مكتمل", en: "Completed" },
  }

  if (labels[value]) return labels[value][locale]
  return status || (locale === "ar" ? "غير معروف" : "Unknown")
}

function statusVariant(
  status?: string
): "default" | "secondary" | "destructive" | "outline" {
  const value = (status || "").toUpperCase()

  if (["FAILED", "REJECTED"].includes(value)) return "destructive"
  if (["SENT", "DELIVERED", "READ", "APPROVED", "COMPLETED"].includes(value)) return "default"
  if (["PENDING", "DRAFT", "RUNNING"].includes(value)) return "secondary"
  return "outline"
}

async function safeFetchJson<T>(path: string): Promise<T | null> {
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

export default function SystemWhatsAppPage() {
  const [locale, setLocale] = useState<Locale>("ar")
  const [state, setState] = useState<DashboardState>({
    loading: true,
    refreshing: false,
    status: null,
    settings: null,
    logs: [],
    templates: [],
    broadcasts: [],
  })

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

  const loadDashboard = useCallback(
    async (isRefresh = false) => {
      try {
        setState((prev) => ({
          ...prev,
          loading: isRefresh ? prev.loading : true,
          refreshing: isRefresh,
        }))

        const [statusRes, settingsRes, logsRes, templatesRes, broadcastsRes] =
          await Promise.allSettled([
            safeFetchJson<WhatsAppStatusPayload>(API_PATHS.status),
            safeFetchJson<WhatsAppSettingsPayload>(API_PATHS.settings),
            safeFetchJson<WhatsAppLogsPayload>(API_PATHS.logs),
            safeFetchJson<WhatsAppTemplatesPayload>(API_PATHS.templates),
            safeFetchJson<WhatsAppBroadcastsPayload>(API_PATHS.broadcasts),
          ])

        const status = statusRes.status === "fulfilled" ? statusRes.value : null
        const settings = settingsRes.status === "fulfilled" ? settingsRes.value : null
        const logs =
          logsRes.status === "fulfilled" ? (logsRes.value?.results ?? []) : []
        const templates =
          templatesRes.status === "fulfilled" ? (templatesRes.value?.results ?? []) : []
        const broadcasts =
          broadcastsRes.status === "fulfilled" ? (broadcastsRes.value?.results ?? []) : []

        const hasHardFailure =
          statusRes.status === "rejected" &&
          settingsRes.status === "rejected" &&
          logsRes.status === "rejected" &&
          templatesRes.status === "rejected" &&
          broadcastsRes.status === "rejected"

        setState({
          loading: false,
          refreshing: false,
          status,
          settings,
          logs,
          templates,
          broadcasts,
        })

        if (hasHardFailure) {
          toast.error(t.dashboardLoadError)
        }
      } catch (error) {
        console.error("System WhatsApp dashboard load error:", error)
        setState((prev) => ({
          ...prev,
          loading: false,
          refreshing: false,
        }))
        toast.error(t.dashboardLoadError)
      }
    },
    [t.dashboardLoadError]
  )

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  const isConnected = !!state.status?.connected
  const isActive = !!state.settings?.config?.is_active
  const providerName =
    state.status?.provider || state.settings?.config?.provider || "Meta / Cloud API"

  const metrics = useMemo(() => {
    const totalLogs = state.logs.length
    const failedLogs = state.logs.filter(
      (item) => (item.status || "").toUpperCase() === "FAILED"
    ).length
    const sentLogs = state.logs.filter((item) =>
      ["SENT", "DELIVERED", "READ"].includes((item.status || "").toUpperCase())
    ).length
    const approvedTemplates = state.templates.filter(
      (item) => (item.status || "").toUpperCase() === "APPROVED"
    ).length

    return {
      totalLogs,
      failedLogs,
      sentLogs,
      totalTemplates: state.templates.length,
      approvedTemplates,
      totalBroadcasts: state.broadcasts.length,
    }
  }, [state.logs, state.templates, state.broadcasts])

  return (
    <div dir={isArabic ? "rtl" : "ltr"} className="space-y-6 p-4 md:p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full border bg-background/70 px-3 py-1 text-sm shadow-sm backdrop-blur">
            <Sparkles className="h-4 w-4" />
            <span>{t.centerBadge}</span>
          </div>

          <div>
            <h1 className="text-2xl font-bold tracking-tight md:text-3xl">{t.pageTitle}</h1>
            <p className="text-muted-foreground">{t.pageDescription}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            onClick={() => loadDashboard(true)}
            disabled={state.refreshing}
            className="gap-2"
          >
            {state.refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            {t.refresh}
          </Button>

          <Button asChild className="gap-2">
            <Link href="/system/whatsapp/settings">
              <Settings2 className="h-4 w-4" />
              {t.settings}
            </Link>
          </Button>
        </div>
      </div>

      <Card className="overflow-hidden border-0 shadow-xl">
        <div className="bg-gradient-to-l from-primary/10 via-background to-background">
          <CardHeader className="pb-4">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={isConnected ? "default" : "destructive"} className="gap-1">
                    {isConnected ? (
                      <Wifi className="h-3.5 w-3.5" />
                    ) : (
                      <WifiOff className="h-3.5 w-3.5" />
                    )}
                    {isConnected ? t.connected : t.disconnected}
                  </Badge>

                  <Badge variant={isActive ? "default" : "secondary"}>
                    {isActive ? t.active : t.inactive}
                  </Badge>

                  <Badge variant="outline">{providerName}</Badge>
                </div>

                <div>
                  <CardTitle className="text-xl">{t.whatsappConnection}</CardTitle>
                  <CardDescription className="mt-1">{t.whatsappConnectionDesc}</CardDescription>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border bg-background/80 p-4 shadow-sm backdrop-blur">
                  <p className="text-xs text-muted-foreground">{t.phoneNumberId}</p>
                  <p className="mt-1 truncate text-sm font-semibold">
                    {state.status?.phone_number_id ||
                      state.settings?.config?.phone_number_id ||
                      t.notConfigured}
                  </p>
                </div>

                <div className="rounded-2xl border bg-background/80 p-4 shadow-sm backdrop-blur">
                  <p className="text-xs text-muted-foreground">{t.webhook}</p>
                  <div className="mt-1 flex items-center gap-2 text-sm font-semibold">
                    {state.status?.webhook_verified ? (
                      <>
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        <span>{t.verified}</span>
                      </>
                    ) : (
                      <>
                        <Clock3 className="h-4 w-4 text-amber-600" />
                        <span>{t.pendingOrUnknown}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </CardHeader>
        </div>

        <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.systemStatus}</span>
              <ShieldCheck className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-2xl font-bold">{isActive ? t.active : t.inactive}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {t.lastCheck}: {formatDate(state.status?.last_check_at, locale)}
            </p>
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.approvedTemplates}</span>
              <FileText className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-2xl font-bold">{metrics.approvedTemplates}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {t.outOf} {metrics.totalTemplates}
            </p>
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.sentMessages}</span>
              <Send className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-2xl font-bold">{metrics.sentLogs}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {t.failed}: {metrics.failedLogs}
            </p>
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.broadcasts}</span>
              <Target className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-2xl font-bold">{metrics.totalBroadcasts}</p>
            <p className="mt-1 text-xs text-muted-foreground">{t.systemLevelReady}</p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-4">
        <Card className="border-0 shadow-lg xl:col-span-3">
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle>{t.quickAccess}</CardTitle>
                <CardDescription>{t.quickAccessDesc}</CardDescription>
              </div>
            </div>
          </CardHeader>

          <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Link
              href="/system/whatsapp/settings"
              className="group rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className="flex items-center justify-between">
                <Settings2 className="h-5 w-5 text-primary" />
                <ArrowUpRight className="h-4 w-4 text-muted-foreground transition group-hover:text-foreground" />
              </div>
              <h3 className="mt-4 font-semibold">{t.settingsCardTitle}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{t.settingsCardDesc}</p>
            </Link>

            <Link
              href="/system/whatsapp/logs"
              className="group rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className="flex items-center justify-between">
                <Activity className="h-5 w-5 text-primary" />
                <ArrowUpRight className="h-4 w-4 text-muted-foreground transition group-hover:text-foreground" />
              </div>
              <h3 className="mt-4 font-semibold">{t.logs}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{t.logsCardDesc}</p>
            </Link>

            <Link
              href="/system/whatsapp/templates"
              className="group rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className="flex items-center justify-between">
                <MessageSquareText className="h-5 w-5 text-primary" />
                <ArrowUpRight className="h-4 w-4 text-muted-foreground transition group-hover:text-foreground" />
              </div>
              <h3 className="mt-4 font-semibold">{t.templates}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{t.templatesCardDesc}</p>
            </Link>

            <Link
              href="/system/whatsapp/broadcasts"
              className="group rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className="flex items-center justify-between">
                <BellRing className="h-5 w-5 text-primary" />
                <ArrowUpRight className="h-4 w-4 text-muted-foreground transition group-hover:text-foreground" />
              </div>
              <h3 className="mt-4 font-semibold">{t.broadcastsLabel}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{t.broadcastsCardDesc}</p>
            </Link>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle>{t.smartSummary}</CardTitle>
            <CardDescription>{t.smartSummaryDesc}</CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="rounded-2xl border p-4">
              <div className="flex items-center gap-3">
                <Bot className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">{t.provider}</p>
                  <p className="font-semibold">{providerName}</p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border p-4">
              <div className="flex items-center gap-3">
                <Building2 className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">{t.systemScope}</p>
                  <p className="font-semibold">
                    {state.status?.system_scope_enabled ? t.enabled : t.undefined}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border p-4">
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">{t.companyScope}</p>
                  <p className="font-semibold">
                    {state.status?.company_scope_enabled ? t.enabled : t.undefined}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border p-4">
              <div className="flex items-center gap-3">
                <TrendingUp className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">{t.pendingTemplates}</p>
                  <p className="font-semibold">{state.status?.pending_templates ?? 0}</p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border p-4">
              <div className="flex items-center gap-3">
                <MessageCircle className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">{t.failedMessages}</p>
                  <p className="font-semibold">
                    {state.status?.failed_messages ?? metrics.failedLogs}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="border-0 shadow-lg xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between gap-4">
            <div>
              <CardTitle>{t.latestMessages}</CardTitle>
              <CardDescription>{t.latestMessagesDesc}</CardDescription>
            </div>

            <Button asChild variant="outline" className="gap-2">
              <Link href="/system/whatsapp/logs">
                {t.viewAll}
                <ArrowUpRight className="h-4 w-4" />
              </Link>
            </Button>
          </CardHeader>

          <CardContent className="space-y-3">
            {state.loading ? (
              <div className="flex min-h-[240px] items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            ) : state.logs.length === 0 ? (
              <div className="rounded-2xl border border-dashed p-8 text-center">
                <p className="font-medium">{t.noMessagesYet}</p>
                <p className="mt-1 text-sm text-muted-foreground">{t.noMessagesDesc}</p>
              </div>
            ) : (
              state.logs.slice(0, 6).map((item, index) => (
                <div key={item.id}>
                  <div className="flex flex-col gap-3 rounded-2xl border p-4 md:flex-row md:items-center md:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant={statusVariant(item.status)}>
                          {statusLabel(item.status, locale)}
                        </Badge>
                        <Badge variant="outline">{item.message_type || t.message}</Badge>
                        {item.template_name ? (
                          <Badge variant="secondary">{item.template_name}</Badge>
                        ) : null}
                      </div>

                      <p className="mt-3 truncate text-sm font-semibold">
                        {item.recipient_phone || t.noRecipient}
                      </p>

                      <p className="mt-1 text-xs text-muted-foreground">
                        {formatDate(item.created_at, locale)}
                      </p>

                      {item.error_message ? (
                        <p className="mt-2 text-xs text-destructive">{item.error_message}</p>
                      ) : null}
                    </div>

                    <div className="shrink-0 text-xs text-muted-foreground">
                      {item.provider_message_id || "—"}
                    </div>
                  </div>

                  {index !== state.logs.slice(0, 6).length - 1 ? (
                    <Separator className="my-3" />
                  ) : null}
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card className="border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between gap-4">
              <div>
                <CardTitle>{t.latestTemplates}</CardTitle>
                <CardDescription>{t.latestTemplatesDesc}</CardDescription>
              </div>

              <Button asChild variant="outline" size="sm">
                <Link href="/system/whatsapp/templates">{t.viewAll}</Link>
              </Button>
            </CardHeader>

            <CardContent className="space-y-3">
              {state.loading ? (
                <div className="flex min-h-[140px] items-center justify-center">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                </div>
              ) : state.templates.length === 0 ? (
                <div className="rounded-2xl border border-dashed p-6 text-center text-sm text-muted-foreground">
                  {t.noTemplatesYet}
                </div>
              ) : (
                state.templates.slice(0, 4).map((template) => (
                  <div key={template.id} className="rounded-2xl border p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate font-semibold">
                          {template.name || t.untitledTemplate}
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {template.language || "—"} • {template.category || "—"}
                        </p>
                      </div>

                      <Badge variant={statusVariant(template.status)}>
                        {statusLabel(template.status, locale)}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between gap-4">
              <div>
                <CardTitle>{t.latestBroadcasts}</CardTitle>
                <CardDescription>{t.latestBroadcastsDesc}</CardDescription>
              </div>

              <Button asChild variant="outline" size="sm">
                <Link href="/system/whatsapp/broadcasts">{t.viewAll}</Link>
              </Button>
            </CardHeader>

            <CardContent className="space-y-3">
              {state.loading ? (
                <div className="flex min-h-[140px] items-center justify-center">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                </div>
              ) : state.broadcasts.length === 0 ? (
                <div className="rounded-2xl border border-dashed p-6 text-center text-sm text-muted-foreground">
                  {t.noBroadcastsYet}
                </div>
              ) : (
                state.broadcasts.slice(0, 4).map((broadcast) => (
                  <div key={broadcast.id} className="rounded-2xl border p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate font-semibold">
                          {broadcast.title || `Broadcast #${broadcast.id}`}
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {t.recipients}: {broadcast.recipient_count ?? 0} • {t.sent}: {broadcast.sent_count ?? 0}
                        </p>
                      </div>

                      <Badge variant={statusVariant(broadcast.status)}>
                        {statusLabel(broadcast.status, locale)}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}