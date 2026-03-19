"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Activity,
  ArrowUpRight,
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
  Sparkles,
  Wifi,
  WifiOff,
  XCircle,
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

type StatusPayload = {
  success?: boolean
  connected?: boolean
  configured?: boolean
  provider?: string
  phone_number_id?: string | null
  business_account_id?: string | null
  webhook_verified?: boolean
  last_check_at?: string | null
  is_active?: boolean
}

type SettingsConfig = {
  is_active?: boolean
  is_enabled?: boolean
  provider?: string
  company_name?: string
  allow_templates?: boolean
  send_test_enabled?: boolean
}

type SettingsPayload = {
  success?: boolean
  config?: SettingsConfig
}

type LogItem = {
  id: number
  status?: string
  recipient_phone?: string
  template_name?: string
  created_at?: string
  error_message?: string
}

type LogsPayload = {
  success?: boolean
  results?: LogItem[]
}

type TemplateItem = {
  id: number
  name?: string
  language?: string
  status?: string
  category?: string
}

type TemplatesPayload = {
  success?: boolean
  results?: TemplateItem[]
}

const API = {
  status: "/api/company/whatsapp/status/",
  settings: "/api/company/whatsapp/settings/",
  logs: "/api/company/whatsapp/logs/",
  templates: "/api/company/whatsapp/templates/",
}

function formatDate(value?: string | null) {
  if (!value) return "—"
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return "—"
  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d)
}

function statusVariant(
  status?: string
): "default" | "secondary" | "destructive" | "outline" {
  const v = (status || "").toUpperCase()
  if (["SENT", "DELIVERED", "READ", "APPROVED"].includes(v)) return "default"
  if (["PENDING", "DRAFT"].includes(v)) return "secondary"
  if (["FAILED", "REJECTED"].includes(v)) return "destructive"
  return "outline"
}

function statusLabel(status?: string) {
  const v = (status || "").toUpperCase()
  switch (v) {
    case "SENT":
      return "تم الإرسال"
    case "DELIVERED":
      return "تم التسليم"
    case "READ":
      return "تمت القراءة"
    case "FAILED":
      return "فشل"
    case "PENDING":
      return "قيد الانتظار"
    case "APPROVED":
      return "معتمد"
    case "REJECTED":
      return "مرفوض"
    default:
      return status || "غير معروف"
  }
}

export default function CompanyWhatsAppPage() {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [status, setStatus] = useState<StatusPayload | null>(null)
  const [settings, setSettings] = useState<SettingsPayload | null>(null)
  const [logs, setLogs] = useState<LogItem[]>([])
  const [templates, setTemplates] = useState<TemplateItem[]>([])

  const loadData = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true)
      else setLoading(true)

      const [statusRes, settingsRes, logsRes, templatesRes] = await Promise.all([
        fetch(API.status, {
          credentials: "include",
          cache: "no-store",
          headers: { Accept: "application/json" },
        }),
        fetch(API.settings, {
          credentials: "include",
          cache: "no-store",
          headers: { Accept: "application/json" },
        }),
        fetch(API.logs, {
          credentials: "include",
          cache: "no-store",
          headers: { Accept: "application/json" },
        }),
        fetch(API.templates, {
          credentials: "include",
          cache: "no-store",
          headers: { Accept: "application/json" },
        }),
      ])

      if (!statusRes.ok || !settingsRes.ok || !logsRes.ok || !templatesRes.ok) {
        throw new Error("One or more requests failed")
      }

      const statusData = (await statusRes.json()) as StatusPayload
      const settingsData = (await settingsRes.json()) as SettingsPayload
      const logsData = (await logsRes.json()) as LogsPayload
      const templatesData = (await templatesRes.json()) as TemplatesPayload

      setStatus(statusData)
      setSettings(settingsData)
      setLogs(logsData?.results || [])
      setTemplates(templatesData?.results || [])
    } catch (error) {
      console.error("Company WhatsApp dashboard load error:", error)
      toast.error("تعذر تحميل لوحة واتساب للشركة")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const stats = useMemo(() => {
    const sent = logs.filter((x) =>
      ["SENT", "DELIVERED", "READ"].includes((x.status || "").toUpperCase())
    ).length
    const failed = logs.filter(
      (x) => (x.status || "").toUpperCase() === "FAILED"
    ).length
    const approvedTemplates = templates.filter(
      (x) => (x.status || "").toUpperCase() === "APPROVED"
    ).length

    return {
      totalLogs: logs.length,
      sent,
      failed,
      templates: templates.length,
      approvedTemplates,
    }
  }, [logs, templates])

  return (
    <div className="space-y-6 p-4 md:p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full border bg-background/70 px-3 py-1 text-sm shadow-sm backdrop-blur">
            <Sparkles className="h-4 w-4" />
            <span>Company WhatsApp Center</span>
          </div>

          <div>
            <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
              واتساب الشركة
            </h1>
            <p className="text-muted-foreground">
              إدارة الربط والسجل والقوالب والإرسال التجريبي على مستوى شركتك.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="gap-2"
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            تحديث
          </Button>

          <Button asChild className="gap-2">
            <Link href="/company/whatsapp/settings">
              <Settings2 className="h-4 w-4" />
              الإعدادات
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
                  <Badge
                    variant={status?.connected ? "default" : "destructive"}
                    className="gap-1"
                  >
                    {status?.connected ? (
                      <Wifi className="h-3.5 w-3.5" />
                    ) : (
                      <WifiOff className="h-3.5 w-3.5" />
                    )}
                    {status?.connected ? "متصل" : "غير متصل"}
                  </Badge>

                  <Badge
                    variant={settings?.config?.is_active ? "default" : "secondary"}
                  >
                    {settings?.config?.is_active ? "نشط" : "غير نشط"}
                  </Badge>

                  <Badge variant="outline">
                    {status?.provider || settings?.config?.provider || "meta_cloud_api"}
                  </Badge>
                </div>

                <div>
                  <CardTitle className="text-xl">ملخص الربط الحالي</CardTitle>
                  <CardDescription className="mt-1">
                    حالة مزود واتساب وبيانات الحساب الخاصة بالشركة.
                  </CardDescription>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border bg-background/80 p-4 shadow-sm backdrop-blur">
                  <p className="text-xs text-muted-foreground">Phone Number ID</p>
                  <p className="mt-1 truncate text-sm font-semibold">
                    {status?.phone_number_id || "غير مضبوط"}
                  </p>
                </div>

                <div className="rounded-2xl border bg-background/80 p-4 shadow-sm backdrop-blur">
                  <p className="text-xs text-muted-foreground">آخر فحص</p>
                  <p className="mt-1 text-sm font-semibold">
                    {formatDate(status?.last_check_at)}
                  </p>
                </div>
              </div>
            </div>
          </CardHeader>
        </div>

        <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">إجمالي الرسائل</span>
              <MessageCircle className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-2xl font-bold">{stats.totalLogs}</p>
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">الناجحة</span>
              <Send className="h-4 w-4 text-emerald-600" />
            </div>
            <p className="mt-3 text-2xl font-bold">{stats.sent}</p>
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">الفاشلة</span>
              <XCircle className="h-4 w-4 text-destructive" />
            </div>
            <p className="mt-3 text-2xl font-bold">{stats.failed}</p>
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">القوالب المعتمدة</span>
              <FileText className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-2xl font-bold">{stats.approvedTemplates}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              من أصل {stats.templates} قالب
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-4">
        <Card className="border-0 shadow-lg xl:col-span-3">
          <CardHeader>
            <CardTitle>الوصول السريع</CardTitle>
            <CardDescription>
              الانتقال لأهم أقسام واتساب الخاصة بالشركة.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            <Link
              href="/company/whatsapp/settings"
              className="group rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <Settings2 className="h-5 w-5 text-primary" />
              <h3 className="mt-4 font-semibold">الإعدادات</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                ضبط بيانات الربط وإرسال رسالة اختبار.
              </p>
              <ArrowUpRight className="mt-4 h-4 w-4 text-muted-foreground transition group-hover:text-foreground" />
            </Link>

            <Link
              href="/company/whatsapp/logs"
              className="group rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <Activity className="h-5 w-5 text-primary" />
              <h3 className="mt-4 font-semibold">السجل</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                عرض الحالات والرسائل والمحاولات.
              </p>
              <ArrowUpRight className="mt-4 h-4 w-4 text-muted-foreground transition group-hover:text-foreground" />
            </Link>

            <Link
              href="/company/whatsapp/templates"
              className="group rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <MessageSquareText className="h-5 w-5 text-primary" />
              <h3 className="mt-4 font-semibold">القوالب</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                استعراض القوالب المفعلة والقابلة للاستخدام.
              </p>
              <ArrowUpRight className="mt-4 h-4 w-4 text-muted-foreground transition group-hover:text-foreground" />
            </Link>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle>ملخص سريع</CardTitle>
            <CardDescription>نظرة مختصرة على الحالة الحالية</CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="rounded-2xl border p-4">
              <div className="flex items-center gap-3">
                <Building2 className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">الشركة</p>
                  <p className="font-semibold">
                    {settings?.config?.company_name || "الحساب الحالي"}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border p-4">
              <div className="flex items-center gap-3">
                <Bot className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">المزود</p>
                  <p className="font-semibold">
                    {status?.provider || settings?.config?.provider || "meta_cloud_api"}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border p-4">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">Webhook</p>
                  <p className="font-semibold">
                    {status?.webhook_verified ? "Verified" : "Pending / Unknown"}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border p-4">
              <div className="flex items-center gap-3">
                <Clock3 className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">رسائل الاختبار</p>
                  <p className="font-semibold">
                    {settings?.config?.send_test_enabled ? "مفعلة" : "معطلة"}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle>آخر الرسائل</CardTitle>
            <CardDescription>أحدث سجل مرسل من حساب الشركة</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {loading ? (
              <div className="flex min-h-[180px] items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            ) : logs.length === 0 ? (
              <div className="rounded-2xl border border-dashed p-8 text-center text-sm text-muted-foreground">
                لا توجد رسائل بعد
              </div>
            ) : (
              logs.slice(0, 4).map((item) => (
                <div key={item.id} className="rounded-2xl border p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={statusVariant(item.status)}>
                      {statusLabel(item.status)}
                    </Badge>
                    {item.template_name ? (
                      <Badge variant="secondary">{item.template_name}</Badge>
                    ) : null}
                  </div>

                  <p className="mt-3 text-sm font-semibold">
                    {item.recipient_phone || "—"}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {formatDate(item.created_at)}
                  </p>

                  {item.error_message ? (
                    <p className="mt-2 text-xs text-destructive">{item.error_message}</p>
                  ) : null}
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle>آخر القوالب</CardTitle>
            <CardDescription>القوالب المتاحة داخل حساب الشركة</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {loading ? (
              <div className="flex min-h-[180px] items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            ) : templates.length === 0 ? (
              <div className="rounded-2xl border border-dashed p-8 text-center text-sm text-muted-foreground">
                لا توجد قوالب بعد
              </div>
            ) : (
              templates.slice(0, 4).map((item) => (
                <div key={item.id} className="rounded-2xl border p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold">{item.name || `Template #${item.id}`}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {item.language || "—"} • {item.category || "—"}
                      </p>
                    </div>

                    <Badge variant={statusVariant(item.status)}>
                      {statusLabel(item.status)}
                    </Badge>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}