"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  FileText,
  Globe,
  Loader2,
  MessageSquareText,
  Pencil,
  Plus,
  Power,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  Trash2,
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

type Locale = "ar" | "en"

type CompanyWhatsAppTemplateItem = {
  id: number
  name?: string
  template_name?: string
  template_key?: string
  template_type?: string
  message_type?: string
  language?: string
  language_code?: string
  category?: string
  event_code?: string
  status?: string
  approval_status?: string
  provider_status?: string
  rejection_reason?: string
  updated_at?: string
  last_synced_at?: string
  body_preview?: string
  body_text?: string
  header_text?: string
  footer_text?: string
  button_text?: string
  button_url?: string
  meta_template_name?: string
  meta_template_namespace?: string
  is_active?: boolean
  is_default?: boolean
  version?: number
  scope_type?: string
}

type CompanyWhatsAppTemplatesResponse = {
  success?: boolean
  count?: number
  results?: CompanyWhatsAppTemplateItem[]
  data?: CompanyWhatsAppTemplateItem[]
  message?: string
}

type TemplateFormState = {
  template_name: string
  template_key: string
  message_type: string
  language_code: string
  event_code: string
  approval_status: string
  body_text: string
  header_text: string
  footer_text: string
  button_text: string
  button_url: string
  is_default: boolean
  is_active: boolean
}

const API = {
  templates: "/api/company/whatsapp/templates/",
  create: "/api/company/whatsapp/templates/create/",
  update: (id: number) => `/api/company/whatsapp/templates/${id}/update/`,
  toggle: (id: number) => `/api/company/whatsapp/templates/${id}/toggle/`,
  remove: (id: number) => `/api/company/whatsapp/templates/${id}/delete/`,
} as const

const translations = {
  ar: {
    badge: "WhatsApp Templates",
    title: "قوالب واتساب للشركة",
    description:
      "استعراض القوالب المتاحة للشركة، سواء الخاصة بالشركة أو الموروثة من النظام، مع دعم كامل للإضافة والتعديل والإدارة.",
    back: "رجوع",
    refresh: "تحديث",
    create: "إنشاء قالب",
    createTitle: "إنشاء قالب جديد",
    createDescription: "أدخل بيانات القالب الجديد الخاص بالشركة.",
    editTitle: "تعديل القالب",
    editDescription: "يمكن تعديل قوالب الشركة فقط من هذه الصفحة.",
    save: "حفظ",
    saving: "جاري الحفظ...",
    cancel: "إلغاء",
    delete: "حذف",
    deleting: "جاري الحذف...",
    edit: "تعديل",
    enable: "تفعيل",
    disable: "تعطيل",
    totalTemplates: "إجمالي القوالب",
    approved: "المعتمدة",
    pending: "قيد المراجعة",
    rejected: "المرفوضة",
    draft: "المسودات",
    filters: "الفلاتر",
    filtersDesc: "ابحث عن القالب حسب الاسم أو اللغة أو التصنيف",
    currentResults: "النتائج الحالية",
    search: "بحث",
    searchPlaceholder: "اسم القالب، اللغة، التصنيف...",
    status: "الحالة",
    all: "الكل",
    type: "النوع",
    language: "اللغة",
    category: "التصنيف",
    scope: "النطاق",
    providerSync: "مزامنة المزود",
    lastSyncedAt: "آخر مزامنة",
    lastUpdate: "آخر تحديث",
    version: "الإصدار",
    defaultTemplate: "افتراضي",
    active: "نشط",
    inactive: "غير نشط",
    systemScope: "نظام",
    companyScope: "شركة",
    contentPreview: "معاينة المحتوى",
    noPreview: "لا توجد معاينة متاحة لهذا القالب.",
    noTemplates: "لا توجد قوالب مطابقة",
    noTemplatesDesc:
      "سيظهر هنا ما تم مزامنته أو إتاحته للشركة من القوالب الجاهزة.",
    failedLoad: "تعذر تحميل قوالب واتساب للشركة",
    approvedLabel: "معتمد",
    rejectedLabel: "مرفوض",
    pendingLabel: "قيد المراجعة",
    draftLabel: "مسودة",
    syncedLabel: "متزامن",
    notSyncedLabel: "غير متزامن",
    failedSyncLabel: "فشل التزامن",
    unknown: "غير معروف",
    rejectedHint: "هذا القالب مرفوض حاليًا ويحتاج مراجعة قبل استخدامه.",
    rejectionReason: "سبب الرفض",
    loading: "جاري تحميل القوالب...",
    templateName: "اسم القالب",
    templateKey: "مفتاح القالب",
    messageType: "نوع الرسالة",
    languageCode: "رمز اللغة",
    eventCode: "رمز الحدث / التصنيف",
    approvalStatus: "حالة الاعتماد",
    bodyText: "محتوى القالب",
    headerText: "الهيدر",
    footerText: "الفوتر",
    buttonText: "نص الزر",
    buttonUrl: "رابط الزر",
    yes: "نعم",
    no: "لا",
    isDefault: "افتراضي",
    isActive: "نشط",
    companyOnlyAction: "هذه العملية متاحة فقط لقوالب الشركة",
    createSuccess: "تم إنشاء القالب بنجاح",
    updateSuccess: "تم تحديث القالب بنجاح",
    toggleSuccess: "تم تحديث حالة القالب بنجاح",
    deleteSuccess: "تم حذف القالب بنجاح",
    confirmDeleteTitle: "حذف القالب",
    confirmDeleteDesc: "هل أنت متأكد من حذف هذا القالب؟ لا يمكن التراجع بعد ذلك.",
    confirmDeleteButton: "تأكيد الحذف",
  },
  en: {
    badge: "WhatsApp Templates",
    title: "Company WhatsApp Templates",
    description:
      "Browse company templates, including company-level and inherited system templates, with full create/update management support.",
    back: "Back",
    refresh: "Refresh",
    create: "Create Template",
    createTitle: "Create New Template",
    createDescription: "Enter the details for the new company template.",
    editTitle: "Edit Template",
    editDescription: "Only company templates can be edited from this page.",
    save: "Save",
    saving: "Saving...",
    cancel: "Cancel",
    delete: "Delete",
    deleting: "Deleting...",
    edit: "Edit",
    enable: "Enable",
    disable: "Disable",
    totalTemplates: "Total Templates",
    approved: "Approved",
    pending: "Under Review",
    rejected: "Rejected",
    draft: "Drafts",
    filters: "Filters",
    filtersDesc: "Search by template name, language, or category",
    currentResults: "Current Results",
    search: "Search",
    searchPlaceholder: "Template name, language, category...",
    status: "Status",
    all: "All",
    type: "Type",
    language: "Language",
    category: "Category",
    scope: "Scope",
    providerSync: "Provider Sync",
    lastSyncedAt: "Last Sync",
    lastUpdate: "Last Update",
    version: "Version",
    defaultTemplate: "Default",
    active: "Active",
    inactive: "Inactive",
    systemScope: "System",
    companyScope: "Company",
    contentPreview: "Content Preview",
    noPreview: "No preview available for this template.",
    noTemplates: "No matching templates",
    noTemplatesDesc:
      "Templates synced or exposed to the company will appear here.",
    failedLoad: "Unable to load company WhatsApp templates",
    approvedLabel: "Approved",
    rejectedLabel: "Rejected",
    pendingLabel: "Pending Review",
    draftLabel: "Draft",
    syncedLabel: "Synced",
    notSyncedLabel: "Not Synced",
    failedSyncLabel: "Sync Failed",
    unknown: "Unknown",
    rejectedHint:
      "This template is currently rejected and needs review before use.",
    rejectionReason: "Rejection Reason",
    loading: "Loading templates...",
    templateName: "Template Name",
    templateKey: "Template Key",
    messageType: "Message Type",
    languageCode: "Language Code",
    eventCode: "Event Code / Category",
    approvalStatus: "Approval Status",
    bodyText: "Template Body",
    headerText: "Header",
    footerText: "Footer",
    buttonText: "Button Text",
    buttonUrl: "Button URL",
    yes: "Yes",
    no: "No",
    isDefault: "Default",
    isActive: "Active",
    companyOnlyAction: "This action is only available for company templates",
    createSuccess: "Template created successfully",
    updateSuccess: "Template updated successfully",
    toggleSuccess: "Template status updated successfully",
    deleteSuccess: "Template deleted successfully",
    confirmDeleteTitle: "Delete Template",
    confirmDeleteDesc: "Are you sure you want to delete this template? This cannot be undone.",
    confirmDeleteButton: "Confirm Delete",
  },
} as const

const initialFormState: TemplateFormState = {
  template_name: "",
  template_key: "",
  message_type: "TEXT",
  language_code: "ar",
  event_code: "general",
  approval_status: "DRAFT",
  body_text: "",
  header_text: "",
  footer_text: "",
  button_text: "",
  button_url: "",
  is_default: false,
  is_active: true,
}

function detectLocale(): Locale {
  if (typeof document === "undefined") return "ar"
  const htmlLang = document.documentElement.lang?.toLowerCase() || ""
  return htmlLang.startsWith("en") ? "en" : "ar"
}

function getCsrfToken(): string {
  if (typeof document === "undefined") return ""
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ""
}

function getApiBaseCandidates(): string[] {
  const envBase = (process.env.NEXT_PUBLIC_API_URL || "")
    .trim()
    .replace(/\/$/, "")
  const browserBase =
    typeof window !== "undefined" ? window.location.origin.replace(/\/$/, "") : ""

  return Array.from(new Set([envBase, browserBase, ""]))
}

function buildCandidateUrls(path: string): string[] {
  const cleanPath = path.startsWith("/") ? path : `/${path}`
  const normalizedPath = cleanPath.endsWith("/") ? cleanPath : `${cleanPath}/`
  const urls = new Set<string>()

  for (const base of getApiBaseCandidates()) {
    const full = base ? `${base}${normalizedPath}` : normalizedPath
    urls.add(full)
  }

  return Array.from(urls).filter(Boolean)
}

async function requestJson<T>(
  path: string,
  method: "GET" | "POST",
  body?: unknown
): Promise<T> {
  const candidates = buildCandidateUrls(path)
  let lastError: Error | null = null

  for (const url of candidates) {
    try {
      const response = await fetch(url, {
        method,
        credentials: "include",
        cache: "no-store",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          ...(method !== "GET" ? { "X-CSRFToken": getCsrfToken() } : {}),
        },
        ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        const message =
          data?.message ||
          data?.error ||
          `${method} ${url} failed with ${response.status}`
        lastError = new Error(message)
        continue
      }

      return data as T
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("Unknown request error")
    }
  }

  throw lastError || new Error(`Failed request to ${path}`)
}

function normalizeStatus(status?: string) {
  return (status || "").toUpperCase()
}

function normalizeTemplate(
  item: CompanyWhatsAppTemplateItem
): CompanyWhatsAppTemplateItem {
  return {
    ...item,
    name:
      item.name ||
      item.template_name ||
      item.template_key ||
      `Template #${item.id}`,
    template_type: item.template_type || item.message_type || "—",
    language: item.language || item.language_code || "—",
    category: item.category || item.event_code || "—",
    status: item.status || item.approval_status || "DRAFT",
    body_preview: item.body_preview || item.body_text || "",
    is_active: typeof item.is_active === "boolean" ? item.is_active : true,
  }
}

function formatDate(value: string | null | undefined) {
  if (!value) return "—"
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return "—"

  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(d)
}

function statusVariant(
  status?: string
): "default" | "secondary" | "destructive" | "outline" {
  const v = normalizeStatus(status)
  if (v === "APPROVED") return "default"
  if (v === "REJECTED") return "destructive"
  if (v === "PENDING") return "secondary"
  return "outline"
}

function statusLabel(status: string | undefined, locale: Locale) {
  const map: Record<string, { ar: string; en: string }> = {
    APPROVED: { ar: "معتمد", en: "Approved" },
    REJECTED: { ar: "مرفوض", en: "Rejected" },
    PENDING: { ar: "قيد المراجعة", en: "Pending Review" },
    DRAFT: { ar: "مسودة", en: "Draft" },
  }
  const v = normalizeStatus(status)
  return map[v]?.[locale] || status || translations[locale].unknown
}

function syncVariant(
  status?: string
): "default" | "secondary" | "destructive" | "outline" {
  const v = normalizeStatus(status)
  if (v === "SYNCED") return "default"
  if (v === "FAILED") return "destructive"
  if (v === "NOT_SYNCED") return "secondary"
  return "outline"
}

function syncLabel(status: string | undefined, locale: Locale) {
  const map: Record<string, { ar: string; en: string }> = {
    SYNCED: { ar: "متزامن", en: "Synced" },
    NOT_SYNCED: { ar: "غير متزامن", en: "Not Synced" },
    FAILED: { ar: "فشل التزامن", en: "Sync Failed" },
  }
  const v = normalizeStatus(status)
  return map[v]?.[locale] || status || translations[locale].unknown
}

function scopeLabel(scope: string | undefined, locale: Locale) {
  const v = (scope || "").toUpperCase()
  if (v === "SYSTEM") return translations[locale].systemScope
  if (v === "COMPANY") return translations[locale].companyScope
  return translations[locale].unknown
}

function getStatusButtonClass(active: boolean) {
  if (active) {
    return "border-primary bg-primary text-primary-foreground shadow-sm hover:bg-primary/90"
  }
  return "border-border/60 bg-background text-foreground hover:bg-muted/70"
}

function isCompanyTemplate(item: CompanyWhatsAppTemplateItem) {
  return (item.scope_type || "").toUpperCase() === "COMPANY"
}

export default function CompanyWhatsAppTemplatesPage() {
  const [locale, setLocale] = useState<Locale>("ar")
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [templates, setTemplates] = useState<CompanyWhatsAppTemplateItem[]>([])
  const [query, setQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("ALL")

  const [openCreate, setOpenCreate] = useState(false)
  const [openEdit, setOpenEdit] = useState(false)
  const [openDelete, setOpenDelete] = useState(false)

  const [selectedTemplate, setSelectedTemplate] =
    useState<CompanyWhatsAppTemplateItem | null>(null)
  const [form, setForm] = useState<TemplateFormState>(initialFormState)

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

  const loadTemplates = useCallback(
    async (isRefresh = false) => {
      try {
        if (isRefresh) setRefreshing(true)
        else setLoading(true)

        const response = await requestJson<CompanyWhatsAppTemplatesResponse>(
          API.templates,
          "GET"
        )
        const rawItems = response?.results || response?.data || []
        setTemplates(rawItems.map(normalizeTemplate))
      } catch (error) {
        console.error("Company WhatsApp templates load error:", error)
        toast.error(error instanceof Error ? error.message : t.failedLoad)
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [t.failedLoad]
  )

  useEffect(() => {
    loadTemplates()
  }, [loadTemplates])

  const stats = useMemo(() => {
    const total = templates.length
    const approved = templates.filter(
      (x) => normalizeStatus(x.status) === "APPROVED"
    ).length
    const pending = templates.filter(
      (x) => normalizeStatus(x.status) === "PENDING"
    ).length
    const rejected = templates.filter(
      (x) => normalizeStatus(x.status) === "REJECTED"
    ).length
    const draft = templates.filter(
      (x) => normalizeStatus(x.status) === "DRAFT"
    ).length

    return { total, approved, pending, rejected, draft }
  }, [templates])

  const filteredTemplates = useMemo(() => {
    const q = query.trim().toLowerCase()

    return templates.filter((item) => {
      const matchesStatus =
        statusFilter === "ALL" || normalizeStatus(item.status) === statusFilter

      const haystack = [
        item.name,
        item.template_name,
        item.template_key,
        item.template_type,
        item.message_type,
        item.language,
        item.language_code,
        item.category,
        item.event_code,
        item.body_preview,
        item.scope_type,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()

      return matchesStatus && (!q || haystack.includes(q))
    })
  }, [templates, query, statusFilter])

  const statusOptions = useMemo(
    () => [
      { value: "ALL", label: t.all, count: stats.total },
      { value: "APPROVED", label: t.approvedLabel, count: stats.approved },
      { value: "PENDING", label: t.pendingLabel, count: stats.pending },
      { value: "REJECTED", label: t.rejectedLabel, count: stats.rejected },
      { value: "DRAFT", label: t.draftLabel, count: stats.draft },
    ],
    [
      stats,
      t.all,
      t.approvedLabel,
      t.pendingLabel,
      t.rejectedLabel,
      t.draftLabel,
    ]
  )

  const resetForm = () => {
    setForm(initialFormState)
  }

  const fillFormFromTemplate = (item: CompanyWhatsAppTemplateItem) => {
    setForm({
      template_name: item.template_name || item.name || "",
      template_key: item.template_key || "",
      message_type: item.message_type || item.template_type || "TEXT",
      language_code: item.language_code || item.language || "ar",
      event_code: item.event_code || item.category || "general",
      approval_status: item.approval_status || item.status || "DRAFT",
      body_text: item.body_text || item.body_preview || "",
      header_text: item.header_text || "",
      footer_text: item.footer_text || "",
      button_text: item.button_text || "",
      button_url: item.button_url || "",
      is_default: !!item.is_default,
      is_active: item.is_active !== false,
    })
  }

  const handleCreateOpen = () => {
    resetForm()
    setSelectedTemplate(null)
    setOpenCreate(true)
  }

  const handleEditOpen = (item: CompanyWhatsAppTemplateItem) => {
    if (!isCompanyTemplate(item)) {
      toast.error(t.companyOnlyAction)
      return
    }
    setSelectedTemplate(item)
    fillFormFromTemplate(item)
    setOpenEdit(true)
  }

  const handleDeleteOpen = (item: CompanyWhatsAppTemplateItem) => {
    if (!isCompanyTemplate(item)) {
      toast.error(t.companyOnlyAction)
      return
    }
    setSelectedTemplate(item)
    setOpenDelete(true)
  }

  const handleCreateSubmit = async () => {
    try {
      setSubmitting(true)
      await requestJson(API.create, "POST", form)
      toast.success(t.createSuccess)
      setOpenCreate(false)
      resetForm()
      await loadTemplates(true)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t.failedLoad)
    } finally {
      setSubmitting(false)
    }
  }

  const handleEditSubmit = async () => {
    if (!selectedTemplate) return

    try {
      setSubmitting(true)
      await requestJson(API.update(selectedTemplate.id), "POST", form)
      toast.success(t.updateSuccess)
      setOpenEdit(false)
      setSelectedTemplate(null)
      resetForm()
      await loadTemplates(true)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t.failedLoad)
    } finally {
      setSubmitting(false)
    }
  }

  const handleToggleTemplate = async (item: CompanyWhatsAppTemplateItem) => {
    if (!isCompanyTemplate(item)) {
      toast.error(t.companyOnlyAction)
      return
    }

    try {
      await requestJson(API.toggle(item.id), "POST")
      toast.success(t.toggleSuccess)
      await loadTemplates(true)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t.failedLoad)
    }
  }

  const handleDeleteConfirm = async () => {
    if (!selectedTemplate) return

    try {
      setDeleting(true)
      await requestJson(API.remove(selectedTemplate.id), "POST")
      toast.success(t.deleteSuccess)
      setOpenDelete(false)
      setSelectedTemplate(null)
      await loadTemplates(true)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t.failedLoad)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div dir={isArabic ? "rtl" : "ltr"} className="space-y-6 p-4 md:p-6">
      <Card className="overflow-hidden border-0 shadow-sm">
        <CardContent className="p-0">
          <div className="relative bg-gradient-to-br from-background via-background to-muted/40 p-5 md:p-6">
            <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 rounded-full border bg-background/80 px-3 py-1 text-xs font-medium text-muted-foreground shadow-sm backdrop-blur">
                  <MessageSquareText className="h-3.5 w-3.5 text-primary" />
                  <span>{t.badge}</span>
                </div>

                <div className="space-y-1">
                  <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
                    {t.title}
                  </h1>
                  <p className="max-w-2xl text-sm leading-6 text-muted-foreground md:text-base">
                    {t.description}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button asChild variant="outline" className="gap-2 shadow-sm">
                  <Link href="/company/whatsapp">
                    <ArrowLeft className="h-4 w-4" />
                    {t.back}
                  </Link>
                </Button>

                <Button
                  variant="outline"
                  onClick={() => loadTemplates(true)}
                  disabled={refreshing}
                  className="gap-2 shadow-sm"
                >
                  {refreshing ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  {t.refresh}
                </Button>

                <Button onClick={handleCreateOpen} className="gap-2 shadow-sm">
                  <Plus className="h-4 w-4" />
                  {t.create}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="border-0 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
          <CardContent className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">{t.totalTemplates}</p>
                <p className="text-3xl font-bold tracking-tight">{stats.total}</p>
              </div>
              <div className="rounded-2xl bg-primary/10 p-2.5 text-primary">
                <FileText className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
          <CardContent className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">{t.approved}</p>
                <p className="text-3xl font-bold tracking-tight">{stats.approved}</p>
              </div>
              <div className="rounded-2xl bg-emerald-500/10 p-2.5 text-emerald-600">
                <CheckCircle2 className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
          <CardContent className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">{t.pending}</p>
                <p className="text-3xl font-bold tracking-tight">{stats.pending}</p>
              </div>
              <div className="rounded-2xl bg-amber-500/10 p-2.5 text-amber-600">
                <Sparkles className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
          <CardContent className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">{t.rejected}</p>
                <p className="text-3xl font-bold tracking-tight">{stats.rejected}</p>
              </div>
              <div className="rounded-2xl bg-destructive/10 p-2.5 text-destructive">
                <XCircle className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-0 shadow-sm">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <CardTitle className="text-lg">{t.filters}</CardTitle>
              <CardDescription className="mt-1">
                {t.filtersDesc}
              </CardDescription>
            </div>

            <div className="inline-flex w-fit items-center rounded-full border bg-muted/40 px-3 py-1.5 text-sm text-muted-foreground">
              {t.currentResults}:{" "}
              <span className="ms-1.5 font-bold text-foreground">
                {filteredTemplates.length}
              </span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-5">
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
            <div className="space-y-2">
              <Label className="text-sm font-medium">{t.search}</Label>
              <div className="relative">
                <Search className="pointer-events-none absolute end-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t.searchPlaceholder}
                  className="h-11 rounded-xl border-border/60 bg-background pe-10 shadow-sm"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium">{t.status}</Label>
              <div className="flex flex-wrap gap-2">
                {statusOptions.map((option) => {
                  const active = statusFilter === option.value

                  return (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setStatusFilter(option.value)}
                      className={`inline-flex h-10 items-center gap-2 rounded-xl border px-3 text-sm font-medium transition-all ${getStatusButtonClass(
                        active
                      )}`}
                    >
                      <span>{option.label}</span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs ${
                          active
                            ? "bg-primary-foreground/15 text-primary-foreground"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {option.count}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <Card className="border-0 shadow-sm">
          <CardContent className="flex min-h-[280px] items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-7 w-7 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">{t.loading}</p>
            </div>
          </CardContent>
        </Card>
      ) : filteredTemplates.length === 0 ? (
        <Card className="border-0 shadow-sm">
          <CardContent className="flex min-h-[300px] flex-col items-center justify-center p-10 text-center">
            <div className="mb-4 rounded-2xl bg-muted/60 p-4">
              <MessageSquareText className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-lg font-semibold">{t.noTemplates}</p>
            <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
              {t.noTemplatesDesc}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 2xl:grid-cols-2">
          {filteredTemplates.map((template) => {
            const canManage = isCompanyTemplate(template)

            return (
              <Card
                key={template.id}
                className="border-0 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
              >
                <CardHeader className="pb-4">
                  <div className="flex flex-col gap-4">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0 space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <CardTitle className="truncate text-lg font-semibold">
                            {template.name || `Template #${template.id}`}
                          </CardTitle>

                          {template.is_default ? (
                            <Badge variant="outline" className="rounded-full">
                              {t.defaultTemplate}
                            </Badge>
                          ) : null}

                          <Badge
                            variant={template.is_active ? "default" : "secondary"}
                            className="rounded-full"
                          >
                            {template.is_active ? t.active : t.inactive}
                          </Badge>

                          <Badge variant="outline" className="rounded-full">
                            {scopeLabel(template.scope_type, locale)}
                          </Badge>
                        </div>

                        <CardDescription className="text-xs md:text-sm">
                          {t.lastUpdate}: {formatDate(template.updated_at)}
                        </CardDescription>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Badge
                          variant={statusVariant(template.status)}
                          className="w-fit rounded-full px-3 py-1 text-xs"
                        >
                          {statusLabel(template.status, locale)}
                        </Badge>

                        <Badge
                          variant={syncVariant(template.provider_status)}
                          className="w-fit rounded-full px-3 py-1 text-xs"
                        >
                          {syncLabel(template.provider_status, locale)}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="rounded-2xl border bg-background p-4 shadow-sm">
                      <p className="text-xs text-muted-foreground">{t.type}</p>
                      <p className="mt-1.5 text-sm font-semibold">
                        {template.template_type || "—"}
                      </p>
                    </div>

                    <div className="rounded-2xl border bg-background p-4 shadow-sm">
                      <p className="text-xs text-muted-foreground">{t.language}</p>
                      <div className="mt-1.5 flex items-center gap-2 text-sm font-semibold">
                        <Globe className="h-4 w-4 text-primary" />
                        <span>{template.language || "—"}</span>
                      </div>
                    </div>

                    <div className="rounded-2xl border bg-background p-4 shadow-sm">
                      <p className="text-xs text-muted-foreground">{t.category}</p>
                      <p className="mt-1.5 break-words text-sm font-semibold">
                        {template.category || "—"}
                      </p>
                    </div>
                  </div>

                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="rounded-2xl border bg-background p-4 shadow-sm">
                      <p className="text-xs text-muted-foreground">{t.providerSync}</p>
                      <div className="mt-1.5 flex items-center gap-2 text-sm font-semibold">
                        {normalizeStatus(template.provider_status) === "SYNCED" ? (
                          <Wifi className="h-4 w-4 text-emerald-600" />
                        ) : normalizeStatus(template.provider_status) === "FAILED" ? (
                          <AlertTriangle className="h-4 w-4 text-destructive" />
                        ) : (
                          <WifiOff className="h-4 w-4 text-amber-600" />
                        )}
                        <span>{syncLabel(template.provider_status, locale)}</span>
                      </div>
                    </div>

                    <div className="rounded-2xl border bg-background p-4 shadow-sm">
                      <p className="text-xs text-muted-foreground">{t.lastSyncedAt}</p>
                      <p className="mt-1.5 text-sm font-semibold">
                        {formatDate(template.last_synced_at)}
                      </p>
                    </div>

                    <div className="rounded-2xl border bg-background p-4 shadow-sm">
                      <p className="text-xs text-muted-foreground">{t.version}</p>
                      <p className="mt-1.5 text-sm font-semibold">
                        {template.version || 1}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-2xl border bg-muted/30 p-4">
                    <p className="text-xs font-medium text-muted-foreground">
                      {t.contentPreview}
                    </p>
                    <p className="mt-2 line-clamp-5 text-sm leading-7 text-foreground/90">
                      {template.body_preview || t.noPreview}
                    </p>
                  </div>

                  {normalizeStatus(template.status) === "REJECTED" ? (
                    <div className="space-y-3">
                      <div className="rounded-2xl border border-destructive/20 bg-destructive/5 p-3.5">
                        <div className="flex items-start gap-2">
                          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                          <p className="text-xs leading-6 text-muted-foreground">
                            {t.rejectedHint}
                          </p>
                        </div>
                      </div>

                      {template.rejection_reason ? (
                        <div className="rounded-2xl border border-amber-200 bg-amber-50/60 p-3.5 dark:border-amber-900/30 dark:bg-amber-950/20">
                          <div className="flex items-start gap-2">
                            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                            <div className="space-y-1">
                              <p className="text-xs font-medium text-amber-700 dark:text-amber-400">
                                {t.rejectionReason}
                              </p>
                              <p className="text-xs leading-6 text-muted-foreground">
                                {template.rejection_reason}
                              </p>
                            </div>
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ) : null}

                  <div className="flex flex-wrap gap-2 border-t pt-4">
                    <Button
                      variant="outline"
                      className="gap-2"
                      onClick={() => handleEditOpen(template)}
                      disabled={!canManage}
                    >
                      <Pencil className="h-4 w-4" />
                      {t.edit}
                    </Button>

                    <Button
                      variant="outline"
                      className="gap-2"
                      onClick={() => handleToggleTemplate(template)}
                      disabled={!canManage}
                    >
                      <Power className="h-4 w-4" />
                      {template.is_active ? t.disable : t.enable}
                    </Button>

                    <Button
                      variant="destructive"
                      className="gap-2"
                      onClick={() => handleDeleteOpen(template)}
                      disabled={!canManage}
                    >
                      <Trash2 className="h-4 w-4" />
                      {t.delete}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* =======================================================
          ➕ Create Dialog
      ======================================================== */}
      <Dialog open={openCreate} onOpenChange={setOpenCreate}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>{t.createTitle}</DialogTitle>
            <DialogDescription>{t.createDescription}</DialogDescription>
          </DialogHeader>

          <TemplateForm
            locale={locale}
            form={form}
            onChange={setForm}
          />

          <DialogFooter className="gap-2 sm:justify-end">
            <Button
              variant="outline"
              onClick={() => setOpenCreate(false)}
              disabled={submitting}
            >
              {t.cancel}
            </Button>
            <Button onClick={handleCreateSubmit} disabled={submitting}>
              {submitting ? t.saving : t.save}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* =======================================================
          ✏️ Edit Dialog
      ======================================================== */}
      <Dialog open={openEdit} onOpenChange={setOpenEdit}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>{t.editTitle}</DialogTitle>
            <DialogDescription>{t.editDescription}</DialogDescription>
          </DialogHeader>

          <TemplateForm
            locale={locale}
            form={form}
            onChange={setForm}
          />

          <DialogFooter className="gap-2 sm:justify-end">
            <Button
              variant="outline"
              onClick={() => setOpenEdit(false)}
              disabled={submitting}
            >
              {t.cancel}
            </Button>
            <Button onClick={handleEditSubmit} disabled={submitting}>
              {submitting ? t.saving : t.save}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* =======================================================
          🗑 Delete Dialog
      ======================================================== */}
      <Dialog open={openDelete} onOpenChange={setOpenDelete}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t.confirmDeleteTitle}</DialogTitle>
            <DialogDescription>{t.confirmDeleteDesc}</DialogDescription>
          </DialogHeader>

          <DialogFooter className="gap-2 sm:justify-end">
            <Button
              variant="outline"
              onClick={() => setOpenDelete(false)}
              disabled={deleting}
            >
              {t.cancel}
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deleting}
            >
              {deleting ? t.deleting : t.confirmDeleteButton}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function TemplateForm({
  locale,
  form,
  onChange,
}: {
  locale: Locale
  form: TemplateFormState
  onChange: React.Dispatch<React.SetStateAction<TemplateFormState>>
}) {
  const t = translations[locale]

  const updateField = <K extends keyof TemplateFormState>(
    key: K,
    value: TemplateFormState[K]
  ) => {
    onChange((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  return (
    <div className="grid gap-4 py-2">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>{t.templateName}</Label>
          <Input
            value={form.template_name}
            onChange={(e) => updateField("template_name", e.target.value)}
            placeholder={t.templateName}
          />
        </div>

        <div className="space-y-2">
          <Label>{t.templateKey}</Label>
          <Input
            value={form.template_key}
            onChange={(e) => updateField("template_key", e.target.value)}
            placeholder="employee_absent_alert"
          />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="space-y-2">
          <Label>{t.messageType}</Label>
          <Select
            value={form.message_type}
            onValueChange={(value) => updateField("message_type", value)}
          >
            <SelectTrigger>
              <SelectValue placeholder={t.messageType} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="TEXT">TEXT</SelectItem>
              <SelectItem value="TEMPLATE">TEMPLATE</SelectItem>
              <SelectItem value="INTERACTIVE">INTERACTIVE</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>{t.languageCode}</Label>
          <Select
            value={form.language_code}
            onValueChange={(value) => updateField("language_code", value)}
          >
            <SelectTrigger>
              <SelectValue placeholder={t.languageCode} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ar">ar</SelectItem>
              <SelectItem value="en">en</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>{t.approvalStatus}</Label>
          <Select
            value={form.approval_status}
            onValueChange={(value) => updateField("approval_status", value)}
          >
            <SelectTrigger>
              <SelectValue placeholder={t.approvalStatus} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="DRAFT">DRAFT</SelectItem>
              <SelectItem value="PENDING">PENDING</SelectItem>
              <SelectItem value="APPROVED">APPROVED</SelectItem>
              <SelectItem value="REJECTED">REJECTED</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>{t.eventCode}</Label>
          <Input
            value={form.event_code}
            onChange={(e) => updateField("event_code", e.target.value)}
            placeholder="general"
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label>{t.bodyText}</Label>
        <Textarea
          value={form.body_text}
          onChange={(e) => updateField("body_text", e.target.value)}
          placeholder={t.bodyText}
          className="min-h-[140px]"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>{t.headerText}</Label>
          <Input
            value={form.header_text}
            onChange={(e) => updateField("header_text", e.target.value)}
            placeholder={t.headerText}
          />
        </div>

        <div className="space-y-2">
          <Label>{t.footerText}</Label>
          <Input
            value={form.footer_text}
            onChange={(e) => updateField("footer_text", e.target.value)}
            placeholder={t.footerText}
          />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>{t.buttonText}</Label>
          <Input
            value={form.button_text}
            onChange={(e) => updateField("button_text", e.target.value)}
            placeholder={t.buttonText}
          />
        </div>

        <div className="space-y-2">
          <Label>{t.buttonUrl}</Label>
          <Input
            value={form.button_url}
            onChange={(e) => updateField("button_url", e.target.value)}
            placeholder="https://example.com"
          />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>{t.isDefault}</Label>
          <Select
            value={form.is_default ? "true" : "false"}
            onValueChange={(value) => updateField("is_default", value === "true")}
          >
            <SelectTrigger>
              <SelectValue placeholder={t.isDefault} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="false">{t.no}</SelectItem>
              <SelectItem value="true">{t.yes}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>{t.isActive}</Label>
          <Select
            value={form.is_active ? "true" : "false"}
            onValueChange={(value) => updateField("is_active", value === "true")}
          >
            <SelectTrigger>
              <SelectValue placeholder={t.isActive} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="true">{t.yes}</SelectItem>
              <SelectItem value="false">{t.no}</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  )
}