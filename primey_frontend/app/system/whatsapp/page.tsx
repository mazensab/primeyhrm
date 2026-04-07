"use client"

// ============================================================
// 📂 الملف: app/system/whatsapp/page.tsx
// 🟢 Mham Cloud - System WhatsApp Dashboard
// ------------------------------------------------------------
// ✅ الصفحة الرئيسية لموديول واتساب النظام
// ✅ Dashboard نظيف واحترافي
// ✅ مرتبط بصفحة المحادثات الجديدة
// ✅ مبني على نفس الـ APIs الحالية
// ============================================================

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Activity,
  ArrowUpRight,
  BellRing,
  Bot,
  Building2,
  CheckCircle2,
  MessageCircle,
  MessageSquareText,
  RefreshCw,
  Settings2,
  Sparkles,
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

import {
  fetchInboxConversations,
  fetchInboxSummary,
  fetchWhatsAppSettings,
  fetchWhatsAppStatus,
} from "@/lib/whatsapp/api"
import { WHATSAPP_TRANSLATIONS } from "@/lib/whatsapp/constants"
import {
  detectLocale,
  formatDate,
  formatNumber,
} from "@/lib/whatsapp/formatters"
import type {
  InboxConversation,
  InboxSummary,
  Locale,
  WhatsAppSettingsPayload,
  WhatsAppStatusPayload,
} from "@/lib/whatsapp/types"

type DashboardState = {
  loading: boolean
  refreshing: boolean
  status: WhatsAppStatusPayload | null
  settings: WhatsAppSettingsPayload | null
  inboxSummary: InboxSummary | null
  latestConversations: InboxConversation[]
}

export default function SystemWhatsAppPage() {
  const [locale, setLocale] = useState<Locale>("ar")
  const [state, setState] = useState<DashboardState>({
    loading: true,
    refreshing: false,
    status: null,
    settings: null,
    inboxSummary: null,
    latestConversations: [],
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

  const t = WHATSAPP_TRANSLATIONS[locale]
  const isArabic = locale === "ar"

  const loadDashboard = useCallback(
    async (isRefresh = false) => {
      try {
        setState((prev) => ({
          ...prev,
          loading: isRefresh ? prev.loading : true,
          refreshing: isRefresh,
        }))

        const [statusRes, settingsRes, summaryRes, conversationsRes] =
          await Promise.allSettled([
            fetchWhatsAppStatus(),
            fetchWhatsAppSettings(),
            fetchInboxSummary(),
            fetchInboxConversations({
              limit: 6,
            }),
          ])

        const status = statusRes.status === "fulfilled" ? statusRes.value : null
        const settings = settingsRes.status === "fulfilled" ? settingsRes.value : null
        const inboxSummary =
          summaryRes.status === "fulfilled" ? summaryRes.value?.summary ?? null : null
        const latestConversations =
          conversationsRes.status === "fulfilled"
            ? conversationsRes.value?.results ?? []
            : []

        setState({
          loading: false,
          refreshing: false,
          status,
          settings,
          inboxSummary,
          latestConversations,
        })
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
    state.status?.provider || state.settings?.config?.provider || "WhatsApp Web Session"

  const summary = state.inboxSummary || {}

  const quickStats = useMemo(
    () => [
      {
        label: t.totalConversations,
        value: formatNumber(summary.total_conversations ?? 0),
        icon: MessageCircle,
      },
      {
        label: t.unreadConversations,
        value: formatNumber(summary.unread_conversations ?? 0),
        icon: BellRing,
      },
      {
        label: t.resolvedConversations,
        value: formatNumber(summary.resolved_conversations ?? 0),
        icon: CheckCircle2,
      },
      {
        label: t.pinnedConversations,
        value: formatNumber(summary.pinned_conversations ?? 0),
        icon: Activity,
      },
    ],
    [
      summary.pinned_conversations,
      summary.resolved_conversations,
      summary.total_conversations,
      summary.unread_conversations,
      t.pinnedConversations,
      t.resolvedConversations,
      t.totalConversations,
      t.unreadConversations,
    ]
  )

  const handleRefresh = async () => {
    await loadDashboard(true)
  }

  return (
    <div dir={isArabic ? "rtl" : "ltr"} className="space-y-6 p-4 md:p-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full border bg-background/70 px-3 py-1 text-sm shadow-sm backdrop-blur">
            <Sparkles className="h-4 w-4" />
            <span>{t.centerBadge}</span>
          </div>

          <div>
            <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
              {t.pageTitle}
            </h1>
            <p className="text-muted-foreground">{t.pageDescription}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={state.refreshing}
            className="gap-2"
          >
            <RefreshCw
              className={`h-4 w-4 ${state.refreshing ? "animate-spin" : ""}`}
            />
            {t.refresh}
          </Button>

          <Button asChild variant="outline" className="gap-2">
            <Link href="/system/whatsapp/conversations">
              <MessageCircle className="h-4 w-4" />
              {t.conversations}
            </Link>
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
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
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
                  <CardDescription className="mt-1">
                    {t.whatsappConnectionDesc}
                  </CardDescription>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border bg-background/80 p-4 shadow-sm backdrop-blur">
                  <p className="text-xs text-muted-foreground">{t.phoneNumberId}</p>
                  <p className="mt-1 truncate text-sm font-semibold" dir="ltr">
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
                        <Activity className="h-4 w-4 text-amber-600" />
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
          {quickStats.map((item) => {
            const Icon = item.icon

            return (
              <div key={item.label} className="rounded-2xl border bg-background p-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">{item.label}</span>
                  <Icon className="h-4 w-4 text-primary" />
                </div>

                <p className="mt-3 text-2xl font-bold tabular-nums" dir="ltr">
                  {item.value}
                </p>

                <p className="mt-1 text-xs text-muted-foreground">
                  {isConnected ? t.connectedNow : t.disconnectedNow}
                </p>
              </div>
            )
          })}
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-4">
        <Card className="border-0 shadow-lg xl:col-span-3">
          <CardHeader>
            <CardTitle>{t.quickAccess}</CardTitle>
            <CardDescription>{t.quickAccessDesc}</CardDescription>
          </CardHeader>

          <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Link
              href="/system/whatsapp/conversations"
              className="group rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className="flex items-center justify-between">
                <MessageCircle className="h-5 w-5 text-primary" />
                <ArrowUpRight className="h-4 w-4 text-muted-foreground transition group-hover:text-foreground" />
              </div>
              <h3 className="mt-4 font-semibold">{t.conversations}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{t.messagesDesc}</p>
            </Link>

            <Link
              href="/system/whatsapp/settings"
              className="group rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className="flex items-center justify-between">
                <Settings2 className="h-5 w-5 text-primary" />
                <ArrowUpRight className="h-4 w-4 text-muted-foreground transition group-hover:text-foreground" />
              </div>
              <h3 className="mt-4 font-semibold">{t.settings}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{t.viewSettings}</p>
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
              <p className="mt-1 text-sm text-muted-foreground">
                {t.pendingTemplates}: {formatNumber(state.status?.pending_templates ?? 0)}
              </p>
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
              <p className="mt-1 text-sm text-muted-foreground">
                {t.failedMessages}: {formatNumber(state.status?.failed_messages ?? 0)}
              </p>
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
                  <p className="text-sm text-muted-foreground">{t.lastCheck}</p>
                  <p className="font-semibold" dir="ltr">
                    {formatDate(state.status?.last_check_at, locale)}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-0 shadow-xl">
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle>{t.inboxListTitle}</CardTitle>
            <CardDescription>{t.inboxListDesc}</CardDescription>
          </div>

          <Button asChild className="gap-2">
            <Link href="/system/whatsapp/conversations">
              <MessageCircle className="h-4 w-4" />
              {t.conversations}
            </Link>
          </Button>
        </CardHeader>

        <CardContent>
          {state.loading ? (
            <div className="flex min-h-[240px] items-center justify-center">
              <RefreshCw className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : state.latestConversations.length === 0 ? (
            <div className="rounded-2xl border border-dashed p-8 text-center">
              <p className="font-medium">{t.noConversations}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {t.noConversationsDesc}
              </p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {state.latestConversations.map((conversation) => {
                const contact =
                  conversation.contact?.display_name ||
                  conversation.contact?.push_name ||
                  conversation.contact?.phone_number ||
                  t.noRecipient

                return (
                  <Link
                    key={conversation.id}
                    href="/system/whatsapp/conversations"
                    className="rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:shadow-md"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-semibold">{contact}</p>
                        <p className="mt-1 truncate text-xs text-muted-foreground" dir="ltr">
                          {conversation.contact?.phone_number || t.noRecipient}
                        </p>

                        <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">
                          {conversation.last_message_preview || "—"}
                        </p>
                      </div>

                      {(conversation.unread_count || 0) > 0 ? (
                        <Badge variant="destructive" dir="ltr">
                          {formatNumber(conversation.unread_count)}
                        </Badge>
                      ) : null}
                    </div>

                    <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
                      <span>{conversation.status || t.unknown}</span>
                      <span dir="ltr">{formatDate(conversation.last_message_at, locale)}</span>
                    </div>
                  </Link>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}