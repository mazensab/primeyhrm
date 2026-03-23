"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  FileText,
  Globe,
  Loader2,
  MessageSquareText,
  Pencil,
  Plus,
  Power,
  RefreshCw,
  Save,
  Search,
  ShieldAlert,
  Sparkles,
  Trash2,
  Wifi,
  WifiOff,
  X,
  XCircle,
  AlertCircle,
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

type Locale = "ar" | "en"

type WhatsAppTemplateItem = {
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
}

type WhatsAppTemplatesResponse = {
  success?: boolean
  count?: number
  results?: WhatsAppTemplateItem[]
  data?: WhatsAppTemplateItem[]
  message?: string
}

type TemplateFormState = {
  event_code: string
  template_key: string
  template_name: string
  language_code: string
  message_type: string
  header_text: string
  body_text: string
  footer_text: string
  button_text: string
  button_url: string
  meta_template_name: string
  meta_template_namespace: string
  approval_status: string
  provider_status: string
  rejection_reason: string
  is_default: boolean
  is_active: boolean
}

const API = {
  templates: "/api/system/whatsapp/templates/",
  create: "/api/system/whatsapp/templates/create/",
  update: (id: number) => `/api/system/whatsapp/templates/${id}/update/`,
  toggle: (id: number) => `/api/system/whatsapp/templates/${id}/toggle/`,
  delete: (id: number) => `/api/system/whatsapp/templates/${id}/delete/`,
} as const

const translations = {
  ar: {
    title: "قوالب واتساب النظام",
    description:
      "إدارة ومراجعة القوالب الجاهزة المستخدمة في الإشعارات والأحداث.",
    back: "رجوع",
    refresh: "تحديث",
    create: "إنشاء قالب",
    edit: "تعديل",
    delete: "حذف",
    toggle: "تفعيل/تعطيل",
    save: "حفظ",
    saving: "جاري الحفظ...",
    cancel: "إلغاء",
    deleteConfirm: "هل أنت متأكد من حذف هذا القالب؟",
    deleteSuccess: "تم حذف القالب بنجاح",
    toggleSuccess: "تم تحديث حالة القالب بنجاح",
    createSuccess: "تم إنشاء القالب بنجاح",
    updateSuccess: "تم تحديث القالب بنجاح",
    formCreateTitle: "إنشاء قالب جديد",
    formEditTitle: "تعديل القالب",
    formDescription: "أدخل بيانات القالب ثم احفظ التغييرات.",
    totalTemplates: "إجمالي القوالب",
    approved: "المعتمدة",
    pending: "قيد المراجعة",
    rejected: "المرفوضة",
    draft: "المسودات",
    filters: "الفلاتر",
    filtersDesc: "ابحث عن القالب حسب الاسم أو اللغة أو التصنيف",
    search: "بحث",
    searchPlaceholder: "اسم القالب، اللغة، التصنيف...",
    status: "الحالة",
    syncStatus: "حالة المزامنة",
    providerSync: "مزامنة المزود",
    lastSyncedAt: "آخر مزامنة",
    rejectionReason: "سبب الرفض",
    all: "الكل",
    currentResults: "النتائج الحالية",
    noTemplates: "لا توجد قوالب مطابقة",
    noTemplatesDesc: "سيظهر هنا ما يتم إنشاؤه أو مزامنته من القوالب.",
    lastUpdate: "آخر تحديث",
    type: "النوع",
    language: "اللغة",
    category: "التصنيف",
    contentPreview: "معاينة المحتوى",
    noPreview: "لا توجد معاينة متاحة لهذا القالب.",
    rejectedHint:
      "هذا القالب مرفوض حاليًا ويحتاج مراجعة قبل استخدامه.",
    failedLoad: "تعذر تحميل قوالب واتساب",
    failedSave: "تعذر حفظ القالب",
    failedDelete: "تعذر حذف القالب",
    failedToggle: "تعذر تحديث حالة القالب",
    approvedLabel: "معتمد",
    rejectedLabel: "مرفوض",
    pendingLabel: "قيد المراجعة",
    draftLabel: "مسودة",
    syncedLabel: "متزامن",
    notSyncedLabel: "غير متزامن",
    failedSyncLabel: "فشل التزامن",
    unknown: "غير معروف",
    totalCount: "إجمالي السجلات",
    active: "نشط",
    inactive: "غير نشط",
    defaultTemplate: "افتراضي",
    version: "الإصدار",
    yes: "نعم",
    no: "لا",
    eventCode: "رمز الحدث",
    templateKey: "المفتاح الداخلي",
    templateName: "اسم القالب",
    bodyText: "نص الرسالة",
    headerText: "الهيدر",
    footerText: "الفوتر",
    buttonText: "نص الزر",
    buttonUrl: "رابط الزر",
    metaTemplateName: "اسم قالب المزود",
    metaTemplateNamespace: "Namespace المزود",
    isDefault: "افتراضي",
    isActive: "نشط",
    requiredFieldsHint: "الحقول الأساسية: رمز الحدث، المفتاح، اللغة، النوع، النص.",
    loadingTemplates: "جاري تحميل القوالب...",
    fieldRequired: "مطلوب",
    badgeTitle: "WhatsApp Templates",
  },
  en: {
    title: "System WhatsApp Templates",
    description:
      "Manage and review ready-made templates used in notifications and events.",
    back: "Back",
    refresh: "Refresh",
    create: "Create Template",
    edit: "Edit",
    delete: "Delete",
    toggle: "Toggle",
    save: "Save",
    saving: "Saving...",
    cancel: "Cancel",
    deleteConfirm: "Are you sure you want to delete this template?",
    deleteSuccess: "Template deleted successfully",
    toggleSuccess: "Template status updated successfully",
    createSuccess: "Template created successfully",
    updateSuccess: "Template updated successfully",
    formCreateTitle: "Create New Template",
    formEditTitle: "Edit Template",
    formDescription: "Enter template details and save your changes.",
    totalTemplates: "Total Templates",
    approved: "Approved",
    pending: "Under Review",
    rejected: "Rejected",
    draft: "Drafts",
    filters: "Filters",
    filtersDesc: "Search by template name, language, or category",
    search: "Search",
    searchPlaceholder: "Template name, language, category...",
    status: "Status",
    syncStatus: "Sync Status",
    providerSync: "Provider Sync",
    lastSyncedAt: "Last Sync",
    rejectionReason: "Rejection Reason",
    all: "All",
    currentResults: "Current Results",
    noTemplates: "No matching templates",
    noTemplatesDesc: "Templates created or synced will appear here.",
    lastUpdate: "Last Update",
    type: "Type",
    language: "Language",
    category: "Category",
    contentPreview: "Content Preview",
    noPreview: "No preview available for this template.",
    rejectedHint:
      "This template is currently rejected and needs review before use.",
    failedLoad: "Unable to load WhatsApp templates",
    failedSave: "Unable to save template",
    failedDelete: "Unable to delete template",
    failedToggle: "Unable to update template status",
    approvedLabel: "Approved",
    rejectedLabel: "Rejected",
    pendingLabel: "Pending Review",
    draftLabel: "Draft",
    syncedLabel: "Synced",
    notSyncedLabel: "Not Synced",
    failedSyncLabel: "Sync Failed",
    unknown: "Unknown",
    totalCount: "Total Records",
    active: "Active",
    inactive: "Inactive",
    defaultTemplate: "Default",
    version: "Version",
    yes: "Yes",
    no: "No",
    eventCode: "Event Code",
    templateKey: "Template Key",
    templateName: "Template Name",
    bodyText: "Message Body",
    headerText: "Header",
    footerText: "Footer",
    buttonText: "Button Text",
    buttonUrl: "Button URL",
    metaTemplateName: "Provider Template Name",
    metaTemplateNamespace: "Provider Namespace",
    isDefault: "Default",
    isActive: "Active",
    requiredFieldsHint:
      "Required fields: event code, template key, language, type, body.",
    loadingTemplates: "Loading templates...",
    fieldRequired: "is required",
    badgeTitle: "WhatsApp Templates",
  },
} as const

const defaultFormState: TemplateFormState = {
  event_code: "",
  template_key: "",
  template_name: "",
  language_code: "ar",
  message_type: "TEXT",
  header_text: "",
  body_text: "",
  footer_text: "",
  button_text: "",
  button_url: "",
  meta_template_name: "",
  meta_template_namespace: "",
  approval_status: "DRAFT",
  provider_status: "NOT_SYNCED",
  rejection_reason: "",
  is_default: false,
  is_active: true,
}

function detectLocale(): Locale {
  if (typeof document === "undefined") return "ar"
  const htmlLang = document.documentElement.lang?.toLowerCase() || ""
  return htmlLang.startsWith("en") ? "en" : "ar"
}

function getCookie(name: string): string {
  if (typeof document === "undefined") return ""
  const match = document.cookie.match(new RegExp(`(^|;\\s*)${name}=([^;]*)`))
  return match ? decodeURIComponent(match[2]) : ""
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

async function fetchJson<T>(path: string): Promise<T> {
  const candidates = buildCandidateUrls(path)
  let lastError: Error | null = null

  for (const url of candidates) {
    try {
      const response = await fetch(url, {
        method: "GET",
        credentials: "include",
        cache: "no-store",
        headers: { Accept: "application/json" },
      })

      if (!response.ok) {
        lastError = new Error(`GET ${url} failed with ${response.status}`)
        continue
      }

      return (await response.json()) as T
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("Unknown fetch error")
    }
  }

  throw lastError || new Error(`Failed to fetch ${path}`)
}

async function postJson<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const candidates = buildCandidateUrls(path)
  let lastError: Error | null = null
  const csrfToken = getCookie("csrftoken")

  for (const url of candidates) {
    try {
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

      if (!response.ok) {
        let message = `POST ${url} failed with ${response.status}`
        try {
          const errorData = await response.json()
          message = errorData?.message || message
        } catch {}
        lastError = new Error(message)
        continue
      }

      return (await response.json()) as T
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("Unknown post error")
    }
  }

  throw lastError || new Error(`Failed to post ${path}`)
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

function normalizeStatus(status?: string) {
  return (status || "").toUpperCase()
}

function normalizeTemplate(item: WhatsAppTemplateItem): WhatsAppTemplateItem {
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
  }
}

function statusLabel(status: string | undefined, locale: Locale) {
  const v = normalizeStatus(status)
  const map: Record<string, { ar: string; en: string }> = {
    APPROVED: { ar: "معتمد", en: "Approved" },
    REJECTED: { ar: "مرفوض", en: "Rejected" },
    PENDING: { ar: "قيد المراجعة", en: "Pending Review" },
    DRAFT: { ar: "مسودة", en: "Draft" },
  }
  return map[v]?.[locale] || translations[locale].unknown
}

function syncLabel(status: string | undefined, locale: Locale) {
  const v = normalizeStatus(status)
  const map: Record<string, { ar: string; en: string }> = {
    SYNCED: { ar: "متزامن", en: "Synced" },
    NOT_SYNCED: { ar: "غير متزامن", en: "Not Synced" },
    FAILED: { ar: "فشل التزامن", en: "Sync Failed" },
  }
  return map[v]?.[locale] || translations[locale].unknown
}

function getStatusButtonClass(active: boolean) {
  if (active) {
    return "border-primary bg-primary text-primary-foreground shadow-sm hover:bg-primary/90"
  }
  return "border-border/60 bg-background text-foreground hover:bg-muted/70"
}

function getApprovalTone(status?: string) {
  const value = normalizeStatus(status)

  if (value === "APPROVED") {
    return {
      className: "border-emerald-200 bg-emerald-50 text-emerald-700",
      icon: CheckCircle2,
    }
  }

  if (value === "REJECTED") {
    return {
      className: "border-red-200 bg-red-50 text-red-700",
      icon: XCircle,
    }
  }

  if (value === "PENDING") {
    return {
      className: "border-amber-200 bg-amber-50 text-amber-700",
      icon: Clock3,
    }
  }

  return {
    className: "border-slate-200 bg-slate-50 text-slate-700",
    icon: FileText,
  }
}

function getSyncTone(status?: string) {
  const value = normalizeStatus(status)

  if (value === "SYNCED") {
    return {
      className: "border-emerald-200 bg-emerald-50 text-emerald-700",
      icon: Wifi,
    }
  }

  if (value === "FAILED") {
    return {
      className: "border-red-200 bg-red-50 text-red-700",
      icon: AlertCircle,
    }
  }

  if (value === "NOT_SYNCED") {
    return {
      className: "border-amber-200 bg-amber-50 text-amber-700",
      icon: WifiOff,
    }
  }

  return {
    className: "border-slate-200 bg-slate-50 text-slate-700",
    icon: Globe,
  }
}

function StatusBadge({
  status,
  locale,
}: {
  status?: string
  locale: Locale
}) {
  const tone = getApprovalTone(status)
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

function SyncBadge({
  status,
  locale,
}: {
  status?: string
  locale: Locale
}) {
  const tone = getSyncTone(status)
  const Icon = tone.icon

  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
        tone.className,
      ].join(" ")}
    >
      <Icon className="me-1 h-3.5 w-3.5" />
      {syncLabel(status, locale)}
    </span>
  )
}

function mapTemplateToForm(template: WhatsAppTemplateItem): TemplateFormState {
  return {
    event_code: template.event_code || "",
    template_key: template.template_key || "",
    template_name: template.template_name || "",
    language_code: template.language_code || "ar",
    message_type: template.message_type || "TEXT",
    header_text: template.header_text || "",
    body_text: template.body_text || "",
    footer_text: template.footer_text || "",
    button_text: template.button_text || "",
    button_url: template.button_url || "",
    meta_template_name: template.meta_template_name || "",
    meta_template_namespace: template.meta_template_namespace || "",
    approval_status: template.approval_status || "DRAFT",
    provider_status: template.provider_status || "NOT_SYNCED",
    rejection_reason: template.rejection_reason || "",
    is_default: !!template.is_default,
    is_active: typeof template.is_active === "boolean" ? template.is_active : true,
  }
}

export default function SystemWhatsAppTemplatesPage() {
  const [locale, setLocale] = useState<Locale>("ar")
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null)
  const [templates, setTemplates] = useState<WhatsAppTemplateItem[]>([])
  const [query, setQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("ALL")
  const [showForm, setShowForm] = useState(false)
  const [editingTemplateId, setEditingTemplateId] = useState<number | null>(null)
  const [form, setForm] = useState<TemplateFormState>(defaultFormState)

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

        const response = await fetchJson<WhatsAppTemplatesResponse>(API.templates)
        const rawItems = response?.results || response?.data || []
        const normalizedItems = rawItems.map(normalizeTemplate)
        setTemplates(normalizedItems)
      } catch (error) {
        console.error("System WhatsApp templates load error:", error)
        toast.error(t.failedLoad)
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

    return {
      total,
      approved,
      pending,
      rejected,
      draft,
    }
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
        item.rejection_reason,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()

      return matchesStatus && (!q || haystack.includes(q))
    })
  }, [templates, query, statusFilter])

  const statusOptions = useMemo(
    () => [
      {
        value: "ALL",
        label: t.all,
        count: stats.total,
      },
      {
        value: "APPROVED",
        label: t.approvedLabel,
        count: stats.approved,
      },
      {
        value: "PENDING",
        label: t.pendingLabel,
        count: stats.pending,
      },
      {
        value: "REJECTED",
        label: t.rejectedLabel,
        count: stats.rejected,
      },
      {
        value: "DRAFT",
        label: t.draftLabel,
        count: stats.draft,
      },
    ],
    [stats, t.all, t.approvedLabel, t.pendingLabel, t.rejectedLabel, t.draftLabel]
  )

  const resetForm = () => {
    setForm(defaultFormState)
    setEditingTemplateId(null)
    setShowForm(false)
  }

  const openCreateForm = () => {
    setForm(defaultFormState)
    setEditingTemplateId(null)
    setShowForm(true)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  const openEditForm = (template: WhatsAppTemplateItem) => {
    setForm(mapTemplateToForm(template))
    setEditingTemplateId(template.id)
    setShowForm(true)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  const handleFormChange = <
    K extends keyof TemplateFormState
  >(
    key: K,
    value: TemplateFormState[K]
  ) => {
    setForm((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  const validateForm = () => {
    if (!form.event_code.trim()) {
      toast.error(`${t.eventCode} ${t.fieldRequired}`)
      return false
    }
    if (!form.template_key.trim()) {
      toast.error(`${t.templateKey} ${t.fieldRequired}`)
      return false
    }
    if (!form.language_code.trim()) {
      toast.error(`${t.language} ${t.fieldRequired}`)
      return false
    }
    if (!form.message_type.trim()) {
      toast.error(`${t.type} ${t.fieldRequired}`)
      return false
    }
    if (!form.body_text.trim()) {
      toast.error(`${t.bodyText} ${t.fieldRequired}`)
      return false
    }
    return true
  }

  const handleSubmit = async () => {
    if (!validateForm()) return

    try {
      setSubmitting(true)

      const payload = {
        ...form,
        event_code: form.event_code.trim(),
        template_key: form.template_key.trim(),
        template_name: form.template_name.trim(),
        language_code: form.language_code.trim().toLowerCase(),
        message_type: form.message_type.trim().toUpperCase(),
        header_text: form.header_text.trim(),
        body_text: form.body_text.trim(),
        footer_text: form.footer_text.trim(),
        button_text: form.button_text.trim(),
        button_url: form.button_url.trim(),
        meta_template_name: form.meta_template_name.trim(),
        meta_template_namespace: form.meta_template_namespace.trim(),
        approval_status: form.approval_status.trim().toUpperCase(),
        provider_status: form.provider_status.trim().toUpperCase(),
        rejection_reason: form.rejection_reason.trim(),
      }

      if (editingTemplateId) {
        await postJson(API.update(editingTemplateId), payload)
        toast.success(t.updateSuccess)
      } else {
        await postJson(API.create, payload)
        toast.success(t.createSuccess)
      }

      resetForm()
      await loadTemplates(true)
    } catch (error) {
      console.error("Template submit error:", error)
      toast.error(
        error instanceof Error && error.message ? error.message : t.failedSave
      )
    } finally {
      setSubmitting(false)
    }
  }

  const handleToggle = async (templateId: number) => {
    try {
      setActionLoadingId(templateId)
      await postJson(API.toggle(templateId), {})
      toast.success(t.toggleSuccess)
      await loadTemplates(true)
    } catch (error) {
      console.error("Template toggle error:", error)
      toast.error(
        error instanceof Error && error.message ? error.message : t.failedToggle
      )
    } finally {
      setActionLoadingId(null)
    }
  }

  const handleDelete = async (templateId: number) => {
    const confirmed = window.confirm(t.deleteConfirm)
    if (!confirmed) return

    try {
      setActionLoadingId(templateId)
      await postJson(API.delete(templateId), {})
      toast.success(t.deleteSuccess)

      if (editingTemplateId === templateId) {
        resetForm()
      }

      await loadTemplates(true)
    } catch (error) {
      console.error("Template delete error:", error)
      toast.error(
        error instanceof Error && error.message ? error.message : t.failedDelete
      )
    } finally {
      setActionLoadingId(null)
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
                  <span>{t.badgeTitle}</span>
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
                <Button
                  type="button"
                  onClick={openCreateForm}
                  className="gap-2 shadow-sm"
                >
                  <Plus className="h-4 w-4" />
                  {t.create}
                </Button>

                <Button asChild variant="outline" className="gap-2 shadow-sm">
                  <Link href="/system/whatsapp">
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
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {showForm ? (
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle>
                  {editingTemplateId ? t.formEditTitle : t.formCreateTitle}
                </CardTitle>
                <CardDescription>{t.formDescription}</CardDescription>
              </div>

              <Button
                type="button"
                variant="outline"
                onClick={resetForm}
                className="gap-2"
              >
                <X className="h-4 w-4" />
                {t.cancel}
              </Button>
            </div>
          </CardHeader>

          <CardContent className="space-y-5">
            <div className="rounded-2xl border bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
              {t.requiredFieldsHint}
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              <div className="space-y-2">
                <Label>{t.eventCode}</Label>
                <Input
                  dir="ltr"
                  value={form.event_code}
                  onChange={(e) => handleFormChange("event_code", e.target.value)}
                  placeholder="company_created"
                />
              </div>

              <div className="space-y-2">
                <Label>{t.templateKey}</Label>
                <Input
                  dir="ltr"
                  value={form.template_key}
                  onChange={(e) => handleFormChange("template_key", e.target.value)}
                  placeholder="system_company_created_ar"
                />
              </div>

              <div className="space-y-2">
                <Label>{t.templateName}</Label>
                <Input
                  value={form.template_name}
                  onChange={(e) => handleFormChange("template_name", e.target.value)}
                  placeholder={locale === "ar" ? "إنشاء شركة جديدة" : "Create company"}
                />
              </div>

              <div className="space-y-2">
                <Label>{t.language}</Label>
                <select
                  dir="ltr"
                  value={form.language_code}
                  onChange={(e) => handleFormChange("language_code", e.target.value)}
                  className="h-10 w-full rounded-xl border border-border bg-background px-3 text-sm outline-none"
                >
                  <option value="ar">ar</option>
                  <option value="en">en</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label>{t.type}</Label>
                <select
                  dir="ltr"
                  value={form.message_type}
                  onChange={(e) => handleFormChange("message_type", e.target.value)}
                  className="h-10 w-full rounded-xl border border-border bg-background px-3 text-sm outline-none"
                >
                  <option value="TEXT">TEXT</option>
                  <option value="TEMPLATE">TEMPLATE</option>
                  <option value="DOCUMENT">DOCUMENT</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label>{t.status}</Label>
                <select
                  dir="ltr"
                  value={form.approval_status}
                  onChange={(e) => handleFormChange("approval_status", e.target.value)}
                  className="h-10 w-full rounded-xl border border-border bg-background px-3 text-sm outline-none"
                >
                  <option value="DRAFT">DRAFT</option>
                  <option value="PENDING">PENDING</option>
                  <option value="APPROVED">APPROVED</option>
                  <option value="REJECTED">REJECTED</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label>{t.providerSync}</Label>
                <select
                  dir="ltr"
                  value={form.provider_status}
                  onChange={(e) => handleFormChange("provider_status", e.target.value)}
                  className="h-10 w-full rounded-xl border border-border bg-background px-3 text-sm outline-none"
                >
                  <option value="NOT_SYNCED">NOT_SYNCED</option>
                  <option value="SYNCED">SYNCED</option>
                  <option value="FAILED">FAILED</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label>{t.metaTemplateName}</Label>
                <Input
                  dir="ltr"
                  value={form.meta_template_name}
                  onChange={(e) =>
                    handleFormChange("meta_template_name", e.target.value)
                  }
                  placeholder="provider_template_name"
                />
              </div>

              <div className="space-y-2">
                <Label>{t.metaTemplateNamespace}</Label>
                <Input
                  dir="ltr"
                  value={form.meta_template_namespace}
                  onChange={(e) =>
                    handleFormChange("meta_template_namespace", e.target.value)
                  }
                  placeholder="namespace"
                />
              </div>

              <div className="space-y-2">
                <Label>{t.headerText}</Label>
                <Input
                  value={form.header_text}
                  onChange={(e) => handleFormChange("header_text", e.target.value)}
                  placeholder="Header"
                />
              </div>

              <div className="space-y-2">
                <Label>{t.footerText}</Label>
                <Input
                  value={form.footer_text}
                  onChange={(e) => handleFormChange("footer_text", e.target.value)}
                  placeholder="Footer"
                />
              </div>

              <div className="space-y-2">
                <Label>{t.buttonText}</Label>
                <Input
                  value={form.button_text}
                  onChange={(e) => handleFormChange("button_text", e.target.value)}
                  placeholder={locale === "ar" ? "فتح" : "Open"}
                />
              </div>

              <div className="space-y-2 md:col-span-2 xl:col-span-3">
                <Label>{t.buttonUrl}</Label>
                <Input
                  dir="ltr"
                  value={form.button_url}
                  onChange={(e) => handleFormChange("button_url", e.target.value)}
                  placeholder="https://example.com"
                />
              </div>

              <div className="space-y-2 md:col-span-2 xl:col-span-3">
                <Label>{t.bodyText}</Label>
                <textarea
                  value={form.body_text}
                  onChange={(e) => handleFormChange("body_text", e.target.value)}
                  placeholder={locale === "ar" ? "مرحبًا {{company_name}} ..." : "Hello {{company_name}} ..."}
                  className="min-h-[140px] w-full rounded-2xl border border-border bg-background px-3 py-3 text-sm outline-none"
                />
              </div>

              <div className="space-y-2 md:col-span-2 xl:col-span-3">
                <Label>{t.rejectionReason}</Label>
                <textarea
                  value={form.rejection_reason}
                  onChange={(e) =>
                    handleFormChange("rejection_reason", e.target.value)
                  }
                  placeholder={locale === "ar" ? "سبب الرفض عند الحاجة" : "Rejection reason if needed"}
                  className="min-h-[90px] w-full rounded-2xl border border-border bg-background px-3 py-3 text-sm outline-none"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="flex items-center justify-between rounded-2xl border bg-background px-4 py-3">
                <span className="text-sm font-medium">{t.isDefault}</span>
                <input
                  type="checkbox"
                  checked={form.is_default}
                  onChange={(e) => handleFormChange("is_default", e.target.checked)}
                  className="h-4 w-4"
                />
              </label>

              <label className="flex items-center justify-between rounded-2xl border bg-background px-4 py-3">
                <span className="text-sm font-medium">{t.isActive}</span>
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => handleFormChange("is_active", e.target.checked)}
                  className="h-4 w-4"
                />
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                type="button"
                onClick={handleSubmit}
                disabled={submitting}
                className="gap-2"
              >
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                {submitting ? t.saving : t.save}
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={resetForm}
                disabled={submitting}
                className="gap-2"
              >
                <X className="h-4 w-4" />
                {t.cancel}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="border-0 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
          <CardContent className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">{t.totalTemplates}</p>
                <p className="text-3xl font-bold tracking-tight tabular-nums" dir="ltr">
                  {formatNumber(stats.total)}
                </p>
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
                <p className="text-3xl font-bold tracking-tight tabular-nums" dir="ltr">
                  {formatNumber(stats.approved)}
                </p>
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
                <p className="text-3xl font-bold tracking-tight tabular-nums" dir="ltr">
                  {formatNumber(stats.pending)}
                </p>
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
                <p className="text-3xl font-bold tracking-tight tabular-nums" dir="ltr">
                  {formatNumber(stats.rejected)}
                </p>
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
              <span className="ms-1.5 font-bold text-foreground tabular-nums" dir="ltr">
                {formatNumber(filteredTemplates.length)}
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
                        className={`rounded-full px-2 py-0.5 text-xs tabular-nums ${
                          active
                            ? "bg-primary-foreground/15 text-primary-foreground"
                            : "bg-muted text-muted-foreground"
                        }`}
                        dir="ltr"
                      >
                        {formatNumber(option.count)}
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
              <p className="text-sm text-muted-foreground">
                {t.loadingTemplates}
              </p>
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
          {filteredTemplates.map((template) => (
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
                          {template.name || `Template #${formatNumber(template.id)}`}
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
                      </div>

                      <CardDescription className="text-xs md:text-sm" dir="ltr">
                        {t.lastUpdate}: {formatDate(template.updated_at)}
                      </CardDescription>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <StatusBadge status={template.status} locale={locale} />
                      <SyncBadge status={template.provider_status} locale={locale} />
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="gap-2"
                      onClick={() => openEditForm(template)}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      {t.edit}
                    </Button>

                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="gap-2"
                      disabled={actionLoadingId === template.id}
                      onClick={() => handleToggle(template.id)}
                    >
                      {actionLoadingId === template.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Power className="h-3.5 w-3.5" />
                      )}
                      {t.toggle}
                    </Button>

                    <Button
                      type="button"
                      size="sm"
                      variant="destructive"
                      className="gap-2"
                      disabled={actionLoadingId === template.id}
                      onClick={() => handleDelete(template.id)}
                    >
                      {actionLoadingId === template.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="h-3.5 w-3.5" />
                      )}
                      {t.delete}
                    </Button>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-2xl border bg-background p-4 shadow-sm">
                    <p className="text-xs text-muted-foreground">{t.type}</p>
                    <p className="mt-1.5 text-sm font-semibold" dir="ltr">
                      {template.template_type || "—"}
                    </p>
                  </div>

                  <div className="rounded-2xl border bg-background p-4 shadow-sm">
                    <p className="text-xs text-muted-foreground">{t.language}</p>
                    <div className="mt-1.5 flex items-center gap-2 text-sm font-semibold" dir="ltr">
                      <Globe className="h-4 w-4 text-primary" />
                      <span>{template.language || "—"}</span>
                    </div>
                  </div>

                  <div className="rounded-2xl border bg-background p-4 shadow-sm">
                    <p className="text-xs text-muted-foreground">{t.category}</p>
                    <p className="mt-1.5 break-words text-sm font-semibold" dir="ltr">
                      {template.category || "—"}
                    </p>
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-2xl border bg-background p-4 shadow-sm">
                    <p className="text-xs text-muted-foreground">{t.providerSync}</p>
                    <div className="mt-1.5">
                      <SyncBadge status={template.provider_status} locale={locale} />
                    </div>
                  </div>

                  <div className="rounded-2xl border bg-background p-4 shadow-sm">
                    <p className="text-xs text-muted-foreground">{t.lastSyncedAt}</p>
                    <p className="mt-1.5 text-sm font-semibold" dir="ltr">
                      {formatDate(template.last_synced_at)}
                    </p>
                  </div>

                  <div className="rounded-2xl border bg-background p-4 shadow-sm">
                    <p className="text-xs text-muted-foreground">{t.version}</p>
                    <p className="mt-1.5 text-sm font-semibold tabular-nums" dir="ltr">
                      {formatNumber(template.version || 1)}
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
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}