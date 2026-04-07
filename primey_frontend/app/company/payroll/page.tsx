"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Banknote,
  CalendarRange,
  CheckCircle2,
  CircleDollarSign,
  Eye,
  FileSpreadsheet,
  Loader2,
  PlayCircle,
  RefreshCw,
  RotateCcw,
  Search,
  Wallet,
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Card,
  CardContent,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

type Locale = "ar" | "en"
type RunStatus = "DRAFT" | "CALCULATED" | "APPROVED" | "PAID" | string
type PaymentMethod = "BANK" | "CASH"

type PayrollRun = {
  id: number
  month: string
  status: RunStatus
  total_net?: number | string
  progress_percent?: number | string
  accounting_consistency?: boolean
  total_employees?: number
  amounts?: {
    total_remaining?: number | string
  }
}

type RunPaymentDialogState = {
  open: boolean
  run: PayrollRun | null
  method: PaymentMethod
  reference: string
  notes: string
}

type Dictionary = {
  pageTitle: string
  pageDescription: string
  createRun: string
  refresh: string
  exportExcel: string
  searchAndFilters: string
  searchPlaceholder: string
  filterAll: string
  filterDraft: string
  filterCalculated: string
  filterApproved: string
  filterPaid: string
  runsList: string
  month: string
  status: string
  employees: string
  totalNet: string
  progress: string
  accounting: string
  actions: string
  view: string
  calculate: string
  approve: string
  reset: string
  pay: string
  loading: string
  noData: string
  loadFailed: string
  actionFailed: string
  exportSuccess: string
  totalRuns: string
  approvedRuns: string
  paidRuns: string
  totalPayroll: string
  yes: string
  no: string
  draft: string
  calculated: string
  approved: string
  paid: string
  unknown: string
  createPrompt: string
  createPromptHint: string
  createSuccess: string
  calculateSuccess: string
  approveSuccess: string
  resetSuccess: string
  paySuccess: string
  printHint: string
  quickActions: string
  searchHint: string
  employeesUnit: string
  createDialogTitle: string
  createDialogDescription: string
  createDialogMonthLabel: string
  createDialogCancel: string
  createDialogSubmit: string
  runPaymentDialogTitle: string
  runPaymentDialogDescription: string
  runPaymentDialogMonth: string
  runPaymentDialogMethod: string
  runPaymentDialogReference: string
  runPaymentDialogReferencePlaceholder: string
  runPaymentDialogNotes: string
  runPaymentDialogNotesPlaceholder: string
  runPaymentDialogRemaining: string
  runPaymentDialogCancel: string
  runPaymentDialogSubmit: string
  runPaymentReferenceRequired: string
}

const translations: Record<Locale, Dictionary> = {
  ar: {
    pageTitle: "الرواتب",
    pageDescription: "إدارة تشغيلات الرواتب وسجلات الدفع بشكل احترافي ومتجاوب مع جميع الأجهزة",
    createRun: "إنشاء تشغيل",
    refresh: "تحديث",
    exportExcel: "Excel",
    searchAndFilters: "البحث والفلاتر",
    searchPlaceholder: "ابحث بالشهر مثل 2026-03 أو بالحالة...",
    filterAll: "الكل",
    filterDraft: "مسودة",
    filterCalculated: "محسوبة",
    filterApproved: "معتمدة",
    filterPaid: "مدفوعة",
    runsList: "تشغيلات الرواتب",
    month: "الشهر",
    status: "الحالة",
    employees: "الموظفون",
    totalNet: "إجمالي الصافي",
    progress: "التقدم",
    accounting: "التطابق",
    actions: "الإجراءات",
    view: "عرض",
    calculate: "حساب",
    approve: "اعتماد",
    reset: "إعادة ضبط",
    pay: "دفع",
    loading: "جاري تحميل تشغيلات الرواتب...",
    noData: "لا توجد تشغيلات مطابقة",
    loadFailed: "تعذر تحميل بيانات الرواتب",
    actionFailed: "تعذر تنفيذ الإجراء",
    exportSuccess: "تم تصدير بيانات الرواتب بنجاح",
    totalRuns: "إجمالي التشغيلات",
    approvedRuns: "التشغيلات المعتمدة",
    paidRuns: "التشغيلات المدفوعة",
    totalPayroll: "إجمالي الرواتب",
    yes: "نعم",
    no: "لا",
    draft: "مسودة",
    calculated: "محسوبة",
    approved: "معتمدة",
    paid: "مدفوعة",
    unknown: "غير معروف",
    createPrompt: "أدخل شهر التشغيل",
    createPromptHint: "يجب أن يكون التنسيق بالصيغة YYYY-MM",
    createSuccess: "تم إنشاء التشغيل بنجاح",
    calculateSuccess: "تم احتساب التشغيل بنجاح",
    approveSuccess: "تم اعتماد التشغيل بنجاح",
    resetSuccess: "تمت إعادة التشغيل إلى مسودة",
    paySuccess: "تم دفع التشغيل بنجاح",
    printHint: "الأرقام والتواريخ في الصفحة تُعرض دائمًا بالإنجليزية",
    quickActions: "إجراءات سريعة",
    searchHint: "يمكنك البحث بالشهر أو بالحالة مثل APPROVED / PAID",
    employeesUnit: "موظف",
    createDialogTitle: "إنشاء تشغيل رواتب جديد",
    createDialogDescription: "اختر شهر التشغيل من داخل واجهة النظام ثم احفظ العملية.",
    createDialogMonthLabel: "شهر التشغيل",
    createDialogCancel: "إلغاء",
    createDialogSubmit: "حفظ",
    runPaymentDialogTitle: "دفع تشغيل الرواتب",
    runPaymentDialogDescription: "حدد نوع الدفع وأدخل تفاصيل العملية قبل تنفيذ الدفع الكامل.",
    runPaymentDialogMonth: "شهر التشغيل",
    runPaymentDialogMethod: "نوع الدفع",
    runPaymentDialogReference: "مرجع التحويل",
    runPaymentDialogReferencePlaceholder: "مثال: TRX-2026-0001",
    runPaymentDialogNotes: "ملاحظات",
    runPaymentDialogNotesPlaceholder: "اكتب ملاحظة داخلية إن وجدت",
    runPaymentDialogRemaining: "الإجمالي المتبقي",
    runPaymentDialogCancel: "إلغاء",
    runPaymentDialogSubmit: "تأكيد الدفع",
    runPaymentReferenceRequired: "مرجع التحويل مطلوب عند اختيار التحويل البنكي",
  },
  en: {
    pageTitle: "Payroll",
    pageDescription: "Manage payroll runs and payment operations in a professional responsive interface",
    createRun: "Create Run",
    refresh: "Refresh",
    exportExcel: "Excel",
    searchAndFilters: "Search & Filters",
    searchPlaceholder: "Search by month like 2026-03 or by status...",
    filterAll: "All",
    filterDraft: "Draft",
    filterCalculated: "Calculated",
    filterApproved: "Approved",
    filterPaid: "Paid",
    runsList: "Payroll Runs",
    month: "Month",
    status: "Status",
    employees: "Employees",
    totalNet: "Total Net",
    progress: "Progress",
    accounting: "Accounting",
    actions: "Actions",
    view: "View",
    calculate: "Calculate",
    approve: "Approve",
    reset: "Reset",
    pay: "Pay",
    loading: "Loading payroll runs...",
    noData: "No matching payroll runs found",
    loadFailed: "Failed to load payroll data",
    actionFailed: "Failed to complete the action",
    exportSuccess: "Payroll data exported successfully",
    totalRuns: "Total Runs",
    approvedRuns: "Approved Runs",
    paidRuns: "Paid Runs",
    totalPayroll: "Total Payroll",
    yes: "Yes",
    no: "No",
    draft: "Draft",
    calculated: "Calculated",
    approved: "Approved",
    paid: "Paid",
    unknown: "Unknown",
    createPrompt: "Enter payroll month",
    createPromptHint: "Month format must be YYYY-MM",
    createSuccess: "Payroll run created successfully",
    calculateSuccess: "Payroll run calculated successfully",
    approveSuccess: "Payroll run approved successfully",
    resetSuccess: "Payroll run reset to draft successfully",
    paySuccess: "Payroll run paid successfully",
    printHint: "Numbers and dates on this page are always rendered in English",
    quickActions: "Quick Actions",
    searchHint: "You can search by month or status like APPROVED / PAID",
    employeesUnit: "Employees",
    createDialogTitle: "Create New Payroll Run",
    createDialogDescription: "Select the payroll month from the system UI and save the operation.",
    createDialogMonthLabel: "Payroll Month",
    createDialogCancel: "Cancel",
    createDialogSubmit: "Save",
    runPaymentDialogTitle: "Pay Payroll Run",
    runPaymentDialogDescription: "Choose the payment method and enter the payment details before paying the full run.",
    runPaymentDialogMonth: "Payroll Month",
    runPaymentDialogMethod: "Payment Method",
    runPaymentDialogReference: "Transfer Reference",
    runPaymentDialogReferencePlaceholder: "Example: TRX-2026-0001",
    runPaymentDialogNotes: "Notes",
    runPaymentDialogNotesPlaceholder: "Write an internal note if needed",
    runPaymentDialogRemaining: "Total Remaining",
    runPaymentDialogCancel: "Cancel",
    runPaymentDialogSubmit: "Confirm Payment",
    runPaymentReferenceRequired: "Transfer reference is required for bank transfer",
  },
}

function getCookie(name: string) {
  if (typeof document === "undefined") return null

  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift() || null
  }

  return null
}

function detectLocale(): Locale {
  if (typeof document !== "undefined") {
    const htmlLang = document.documentElement.lang?.toLowerCase().trim() || ""
    if (htmlLang.startsWith("ar")) return "ar"
    if (htmlLang.startsWith("en")) return "en"

    const htmlDir = document.documentElement.dir?.toLowerCase().trim() || ""
    if (htmlDir === "rtl") return "ar"
    if (htmlDir === "ltr") return "en"

    const cookieLocale =
      getCookie("locale") ||
      getCookie("lang") ||
      getCookie("NEXT_LOCALE")

    if (cookieLocale?.toLowerCase().startsWith("ar")) return "ar"
    if (cookieLocale?.toLowerCase().startsWith("en")) return "en"

    const localStorageLocale =
      typeof window !== "undefined"
        ? window.localStorage.getItem("primey-locale")
        : null

    if (localStorageLocale?.toLowerCase().startsWith("ar")) return "ar"
    if (localStorageLocale?.toLowerCase().startsWith("en")) return "en"
  }

  if (typeof navigator !== "undefined") {
    const language = navigator.language?.toLowerCase() || ""
    if (language.startsWith("ar")) return "ar"
  }

  return "en"
}

function getApiBaseUrl() {
  const envBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim()
  if (envBase) return envBase.replace(/\/+$/, "")

  if (typeof window !== "undefined") {
    const { origin, hostname, port } = window.location

    if (port === "3000") {
      return `${window.location.protocol}//${hostname}:8000`
    }

    return origin.replace(/\/+$/, "")
  }

  return "http://localhost:8000"
}

function formatNumber(value?: number | string | null, maximumFractionDigits = 0) {
  if (value === null || value === undefined || value === "") return "0"

  const numericValue =
    typeof value === "number" ? value : Number(String(value).replace(/,/g, ""))

  if (Number.isNaN(numericValue)) return String(value)

  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
    minimumFractionDigits: 0,
    maximumFractionDigits,
  }).format(numericValue)
}

function formatMonth(value?: string | null) {
  if (!value) return "—"

  const clean = String(value).trim()
  if (/^\d{4}-\d{2}$/.test(clean)) return clean

  const date = new Date(clean)
  if (Number.isNaN(date.getTime())) return clean

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")

  return `${year}-${month}`
}

function getCurrentMonthValue() {
  return new Date().toISOString().slice(0, 7)
}

function downloadCsv(filename: string, rows: string[][]) {
  const csvContent = rows
    .map((row) =>
      row
        .map((cell) => `"${String(cell ?? "").replace(/"/g, '""')}"`)
        .join(",")
    )
    .join("\n")

  const blob = new Blob([`\uFEFF${csvContent}`], {
    type: "text/csv;charset=utf-8;",
  })

  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")

  link.href = url
  link.setAttribute("download", filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function getStatusLabel(status: RunStatus, locale: Locale) {
  const normalized = String(status || "").toUpperCase()

  if (normalized === "DRAFT") return locale === "ar" ? "مسودة" : "Draft"
  if (normalized === "CALCULATED") return locale === "ar" ? "محسوبة" : "Calculated"
  if (normalized === "APPROVED") return locale === "ar" ? "معتمدة" : "Approved"
  if (normalized === "PAID") return locale === "ar" ? "مدفوعة" : "Paid"

  return status || (locale === "ar" ? "غير معروف" : "Unknown")
}

function getStatusClasses(status: RunStatus) {
  const normalized = String(status || "").toUpperCase()

  if (normalized === "PAID") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700"
  }

  if (normalized === "APPROVED") {
    return "border-blue-200 bg-blue-50 text-blue-700"
  }

  if (normalized === "CALCULATED") {
    return "border-amber-200 bg-amber-50 text-amber-700"
  }

  return "border-slate-200 bg-slate-50 text-slate-700"
}

function StatusBadge({
  status,
  locale,
}: {
  status: RunStatus
  locale: Locale
}) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
        getStatusClasses(status),
      ].join(" ")}
    >
      {getStatusLabel(status, locale)}
    </span>
  )
}

function getTableAlignClass(
  kind: "start" | "center" | "end",
  isArabic: boolean
) {
  if (kind === "center") return "text-center"
  if (kind === "end") return isArabic ? "text-left" : "text-right"
  return isArabic ? "text-right" : "text-left"
}

function getDefaultRunPaymentDialogState(): RunPaymentDialogState {
  return {
    open: false,
    run: null,
    method: "BANK",
    reference: "",
    notes: "",
  }
}

export default function CompanyPayrollPage() {
  const router = useRouter()

  const [locale, setLocale] = useState<Locale>("en")
  const [runs, setRuns] = useState<PayrollRun[]>([])
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<
    "ALL" | "DRAFT" | "CALCULATED" | "APPROVED" | "PAID"
  >("ALL")
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [actioningKey, setActioningKey] = useState<string | null>(null)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [createMonth, setCreateMonth] = useState(getCurrentMonthValue())
  const [runPaymentDialog, setRunPaymentDialog] = useState<RunPaymentDialogState>(
    getDefaultRunPaymentDialogState()
  )

  const apiBaseUrl = getApiBaseUrl()
  const t = translations[locale]
  const isArabic = locale === "ar"
  const dir = isArabic ? "rtl" : "ltr"

  useEffect(() => {
    const applyLocale = () => {
      setLocale(detectLocale())
    }

    applyLocale()

    const htmlElement = document.documentElement
    const observer = new MutationObserver(() => {
      applyLocale()
    })

    observer.observe(htmlElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    window.addEventListener("languagechange", applyLocale)
    window.addEventListener("focus", applyLocale)

    return () => {
      observer.disconnect()
      window.removeEventListener("languagechange", applyLocale)
      window.removeEventListener("focus", applyLocale)
    }
  }, [])

  const loadRuns = useCallback(
    async (silent = false) => {
      if (silent) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      try {
        const res = await fetch(`${apiBaseUrl}/api/company/payroll/runs/`, {
          method: "GET",
          credentials: "include",
          cache: "no-store",
          headers: {
            Accept: "application/json",
          },
        })

        if (!res.ok) {
          throw new Error(`Failed with status ${res.status}`)
        }

        const data = await res.json()
        setRuns(Array.isArray(data) ? data : [])
      } catch (error) {
        console.error("Failed loading payroll runs:", error)
        setRuns([])
        toast.error(t.loadFailed)
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [apiBaseUrl, t.loadFailed]
  )

  useEffect(() => {
    void loadRuns()
  }, [loadRuns])

  const postRunAction = async (
    runId: number,
    endpoint: "calculate" | "approve" | "reset" | "pay",
    successMessage: string,
    payload?: Record<string, unknown>
  ) => {
    const actionKey = `${endpoint}-${runId}`
    setActioningKey(actionKey)

    try {
      const csrftoken = getCookie("csrftoken")
      const res = await fetch(
        `${apiBaseUrl}/api/company/payroll/runs/${runId}/${endpoint}/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken || "",
          },
          body: JSON.stringify(payload ?? {}),
        }
      )

      const data = await res.json().catch(() => null)

      if (!res.ok) {
        const message =
          data?.detail ||
          data?.error ||
          t.actionFailed

        toast.error(String(message))
        return false
      }

      toast.success(successMessage)
      await loadRuns(true)
      return true
    } catch (error) {
      console.error(`Failed action ${endpoint}:`, error)
      toast.error(t.actionFailed)
      return false
    } finally {
      setActioningKey(null)
    }
  }

  const openCreateRunDialog = () => {
    setCreateMonth(getCurrentMonthValue())
    setCreateDialogOpen(true)
  }

  const submitCreateRun = async () => {
    const cleanedMonth = createMonth.trim()

    if (!/^\d{4}-\d{2}$/.test(cleanedMonth)) {
      toast.error(t.createPromptHint)
      return
    }

    setActioningKey("create-run")

    try {
      const csrftoken = getCookie("csrftoken")
      const res = await fetch(`${apiBaseUrl}/api/company/payroll/runs/create/`, {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken || "",
        },
        body: JSON.stringify({
          month: cleanedMonth,
        }),
      })

      const data = await res.json().catch(() => null)

      if (!res.ok) {
        const message =
          data?.detail ||
          data?.error ||
          t.actionFailed

        toast.error(String(message))
        return
      }

      setCreateDialogOpen(false)
      toast.success(t.createSuccess)
      await loadRuns(true)
    } catch (error) {
      console.error("Create payroll run failed:", error)
      toast.error(t.actionFailed)
    } finally {
      setActioningKey(null)
    }
  }

  const openRunPaymentDialog = (run: PayrollRun) => {
    setRunPaymentDialog({
      open: true,
      run,
      method: "BANK",
      reference: "",
      notes: "",
    })
  }

  const closeRunPaymentDialog = () => {
    if (runPaymentDialog.run && actioningKey === `pay-${runPaymentDialog.run.id}`) {
      return
    }
    setRunPaymentDialog(getDefaultRunPaymentDialogState())
  }

  const submitRunPaymentDialog = async () => {
    const run = runPaymentDialog.run
    if (!run) return

    if (runPaymentDialog.method === "BANK" && !runPaymentDialog.reference.trim()) {
      toast.error(t.runPaymentReferenceRequired)
      return
    }

    const success = await postRunAction(
      run.id,
      "pay",
      t.paySuccess,
      {
        payment_method: runPaymentDialog.method,
        method: runPaymentDialog.method,
        reference: runPaymentDialog.reference.trim() || null,
        notes: runPaymentDialog.notes.trim() || null,
      }
    )

    if (success) {
      setRunPaymentDialog(getDefaultRunPaymentDialogState())
    }
  }

  const filteredRuns = useMemo(() => {
    const term = search.trim().toLowerCase()

    return runs.filter((run) => {
      const monthMatches = formatMonth(run.month).toLowerCase().includes(term)
      const statusMatches = String(run.status || "").toLowerCase().includes(term)

      const matchesSearch = !term || monthMatches || statusMatches
      const matchesStatus =
        statusFilter === "ALL" ||
        String(run.status || "").toUpperCase() === statusFilter

      return matchesSearch && matchesStatus
    })
  }, [runs, search, statusFilter])

  const stats = useMemo(() => {
    const totalRuns = runs.length
    const approvedRuns = runs.filter(
      (run) => String(run.status).toUpperCase() === "APPROVED"
    ).length
    const paidRuns = runs.filter(
      (run) => String(run.status).toUpperCase() === "PAID"
    ).length

    const totalPayroll = runs.reduce((sum, run) => {
      const value =
        typeof run.total_net === "number"
          ? run.total_net
          : Number(String(run.total_net ?? 0).replace(/,/g, ""))

      return sum + (Number.isNaN(value) ? 0 : value)
    }, 0)

    return {
      totalRuns,
      approvedRuns,
      paidRuns,
      totalPayroll,
    }
  }, [runs])

  const exportExcel = () => {
    const rows = [
      [
        t.month,
        t.status,
        t.employees,
        t.totalNet,
        t.progress,
        t.accounting,
      ],
      ...filteredRuns.map((run) => [
        formatMonth(run.month),
        getStatusLabel(run.status, locale),
        formatNumber(run.total_employees ?? 0),
        formatNumber(run.total_net ?? 0, 2),
        `${formatNumber(run.progress_percent ?? 0)}%`,
        run.accounting_consistency ? t.yes : t.no,
      ]),
    ]

    downloadCsv("payroll-runs.csv", rows)
    toast.success(t.exportSuccess)
  }

  const selectedRun = runPaymentDialog.run
  const selectedRunRemaining = selectedRun
    ? selectedRun.amounts?.total_remaining ?? selectedRun.total_net ?? 0
    : 0

  return (
    <div dir={dir} className="space-y-6">
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent dir={dir} className="sm:max-w-md rounded-2xl">
          <DialogHeader className="space-y-2">
            <DialogTitle className="text-xl font-semibold">
              {t.createDialogTitle}
            </DialogTitle>
            <DialogDescription className="text-sm text-muted-foreground">
              {t.createDialogDescription}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 py-2">
            <label className="text-sm font-medium">
              {t.createDialogMonthLabel}
            </label>
            <Input
              type="month"
              value={createMonth}
              onChange={(e) => setCreateMonth(e.target.value)}
              dir="ltr"
              className="h-11"
            />
            <p className="text-xs text-muted-foreground">
              {t.createPromptHint}
            </p>
          </div>

          <DialogFooter className="gap-2 sm:justify-start">
            <Button
              type="button"
              variant="outline"
              onClick={() => setCreateDialogOpen(false)}
              disabled={actioningKey === "create-run"}
            >
              {t.createDialogCancel}
            </Button>

            <Button
              type="button"
              onClick={() => void submitCreateRun()}
              disabled={actioningKey === "create-run"}
              className="gap-2"
            >
              {actioningKey === "create-run" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CalendarRange className="h-4 w-4" />
              )}
              {t.createDialogSubmit}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={runPaymentDialog.open} onOpenChange={(open) => {
        if (!open) closeRunPaymentDialog()
      }}>
        <DialogContent dir={dir} className="sm:max-w-xl rounded-3xl p-0 overflow-hidden">
          <div className="border-b bg-muted/20 px-6 py-5">
            <DialogHeader className="space-y-2">
              <DialogTitle className="text-xl font-semibold">
                {t.runPaymentDialogTitle}
              </DialogTitle>
              <DialogDescription className="text-sm text-muted-foreground">
                {t.runPaymentDialogDescription}
              </DialogDescription>
            </DialogHeader>
          </div>

          <div className="space-y-5 px-6 py-6">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border bg-muted/20 p-4">
                <p className="text-xs text-muted-foreground">{t.runPaymentDialogMonth}</p>
                <p className="mt-1 font-semibold tabular-nums">
                  {selectedRun ? formatMonth(selectedRun.month) : "—"}
                </p>
              </div>

              <div className="rounded-2xl border bg-muted/20 p-4">
                <p className="text-xs text-muted-foreground">{t.runPaymentDialogRemaining}</p>
                <p className="mt-1 font-semibold tabular-nums">
                  {formatNumber(selectedRunRemaining, 2)}
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                {t.runPaymentDialogMethod}
              </label>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  type="button"
                  variant={runPaymentDialog.method === "BANK" ? "default" : "outline"}
                  className="h-11 rounded-2xl"
                  onClick={() =>
                    setRunPaymentDialog((prev) => ({
                      ...prev,
                      method: "BANK",
                    }))
                  }
                >
                  {locale === "ar" ? "تحويل بنكي" : "Bank Transfer"}
                </Button>

                <Button
                  type="button"
                  variant={runPaymentDialog.method === "CASH" ? "default" : "outline"}
                  className="h-11 rounded-2xl"
                  onClick={() =>
                    setRunPaymentDialog((prev) => ({
                      ...prev,
                      method: "CASH",
                      reference: "",
                    }))
                  }
                >
                  {locale === "ar" ? "نقدي" : "Cash"}
                </Button>
              </div>
            </div>

            {runPaymentDialog.method === "BANK" && (
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  {t.runPaymentDialogReference}
                </label>
                <Input
                  value={runPaymentDialog.reference}
                  onChange={(e) =>
                    setRunPaymentDialog((prev) => ({
                      ...prev,
                      reference: e.target.value,
                    }))
                  }
                  placeholder={t.runPaymentDialogReferencePlaceholder}
                  dir="ltr"
                  className="h-11 rounded-2xl"
                />
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium">
                {t.runPaymentDialogNotes}
              </label>
              <textarea
                value={runPaymentDialog.notes}
                onChange={(e) =>
                  setRunPaymentDialog((prev) => ({
                    ...prev,
                    notes: e.target.value,
                  }))
                }
                placeholder={t.runPaymentDialogNotesPlaceholder}
                className="min-h-[110px] w-full rounded-2xl border bg-background px-3 py-3 text-sm outline-none ring-0 transition placeholder:text-muted-foreground focus:border-ring"
              />
            </div>
          </div>

          <DialogFooter className="border-t bg-muted/10 px-6 py-4 sm:justify-between">
            <Button
              type="button"
              variant="outline"
              className="rounded-2xl"
              onClick={closeRunPaymentDialog}
              disabled={!!selectedRun && actioningKey === `pay-${selectedRun.id}`}
            >
              {t.runPaymentDialogCancel}
            </Button>

            <Button
              type="button"
              className="gap-2 rounded-2xl"
              onClick={() => void submitRunPaymentDialog()}
              disabled={!selectedRun || actioningKey === `pay-${selectedRun?.id}`}
            >
              {selectedRun && actioningKey === `pay-${selectedRun.id}` ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Banknote className="h-4 w-4" />
              )}
              {t.runPaymentDialogSubmit}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            {t.pageTitle}
          </h1>
          <p className="text-sm text-muted-foreground md:text-base">
            {t.pageDescription}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            onClick={openCreateRunDialog}
            disabled={actioningKey === "create-run"}
            className="gap-2"
          >
            {actioningKey === "create-run" ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <CalendarRange className="h-4 w-4" />
            )}
            {t.createRun}
          </Button>

          <Button variant="outline" onClick={exportExcel} className="gap-2">
            <FileSpreadsheet className="h-4 w-4" />
            {t.exportExcel}
          </Button>

          <Button
            variant="outline"
            onClick={() => void loadRuns(true)}
            disabled={refreshing || loading}
            className="gap-2"
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

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.totalRuns}</p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumber(stats.totalRuns)}
              </p>
            </div>
            <div className="rounded-2xl border bg-muted/40 p-3">
              <Wallet className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.approvedRuns}</p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumber(stats.approvedRuns)}
              </p>
            </div>
            <div className="rounded-2xl border bg-muted/40 p-3">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.paidRuns}</p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumber(stats.paidRuns)}
              </p>
            </div>
            <div className="rounded-2xl border bg-muted/40 p-3">
              <Banknote className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.totalPayroll}</p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumber(stats.totalPayroll, 2)}
              </p>
            </div>
            <div className="rounded-2xl border bg-muted/40 p-3">
              <CircleDollarSign className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/60">
        <CardHeader className="pb-3">
          <CardTitle className="text-base md:text-lg">
            {t.searchAndFilters}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="relative">
            <Search
              className={[
                "absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                isArabic ? "right-3" : "left-3",
              ].join(" ")}
            />

            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t.searchPlaceholder}
              className={isArabic ? "pr-10" : "pl-10"}
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {[
              { key: "ALL", label: t.filterAll },
              { key: "DRAFT", label: t.filterDraft },
              { key: "CALCULATED", label: t.filterCalculated },
              { key: "APPROVED", label: t.filterApproved },
              { key: "PAID", label: t.filterPaid },
            ].map((item) => {
              const active = statusFilter === item.key

              return (
                <Button
                  key={item.key}
                  type="button"
                  variant={active ? "default" : "outline"}
                  size="sm"
                  onClick={() =>
                    setStatusFilter(
                      item.key as
                        | "ALL"
                        | "DRAFT"
                        | "CALCULATED"
                        | "APPROVED"
                        | "PAID"
                    )
                  }
                  className="rounded-xl"
                >
                  {item.label}
                </Button>
              )
            })}
          </div>

          <p className="text-xs text-muted-foreground">{t.searchHint}</p>
        </CardContent>
      </Card>

      <Card className="hidden border-border/60 lg:block">
        <CardHeader>
          <CardTitle className="text-base md:text-lg">
            {t.runsList}
          </CardTitle>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-14 text-muted-foreground">
              <Loader2 className="me-2 h-5 w-5 animate-spin" />
              {t.loading}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className={getTableAlignClass("center", isArabic)}>
                    {t.month}
                  </TableHead>
                  <TableHead className={getTableAlignClass("center", isArabic)}>
                    {t.status}
                  </TableHead>
                  <TableHead className={getTableAlignClass("center", isArabic)}>
                    {t.employees}
                  </TableHead>
                  <TableHead className={getTableAlignClass("center", isArabic)}>
                    {t.totalNet}
                  </TableHead>
                  <TableHead className={getTableAlignClass("center", isArabic)}>
                    {t.progress}
                  </TableHead>
                  <TableHead className={getTableAlignClass("center", isArabic)}>
                    {t.accounting}
                  </TableHead>
                  <TableHead className={getTableAlignClass("end", isArabic)}>
                    {t.actions}
                  </TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {filteredRuns.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="py-12 text-center text-muted-foreground"
                    >
                      {t.noData}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredRuns.map((run) => {
                    const normalizedStatus = String(run.status || "").toUpperCase()

                    return (
                      <TableRow key={run.id}>
                        <TableCell className="align-middle text-center font-medium tabular-nums whitespace-nowrap">
                          {formatMonth(run.month)}
                        </TableCell>

                        <TableCell className="align-middle text-center whitespace-nowrap">
                          <StatusBadge status={run.status} locale={locale} />
                        </TableCell>

                        <TableCell className="align-middle text-center tabular-nums whitespace-nowrap">
                          {formatNumber(run.total_employees ?? 0)}
                        </TableCell>

                        <TableCell className="align-middle text-center tabular-nums whitespace-nowrap">
                          {formatNumber(run.total_net ?? 0, 2)}
                        </TableCell>

                        <TableCell className="align-middle text-center tabular-nums whitespace-nowrap">
                          {formatNumber(run.progress_percent ?? 0)}%
                        </TableCell>

                        <TableCell className="align-middle text-center whitespace-nowrap">
                          <span className="text-sm">
                            {run.accounting_consistency ? t.yes : t.no}
                          </span>
                        </TableCell>

                        <TableCell className={getTableAlignClass("end", isArabic)}>
                          <div
                            className={[
                              "flex flex-wrap gap-2",
                              isArabic ? "justify-start" : "justify-end",
                            ].join(" ")}
                          >
                            <Button
                              size="sm"
                              variant="outline"
                              className="gap-2"
                              onClick={() => router.push(`/company/payroll/${run.id}`)}
                            >
                              <Eye className="h-4 w-4" />
                              {t.view}
                            </Button>

                            {normalizedStatus === "DRAFT" && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="gap-2"
                                disabled={actioningKey === `calculate-${run.id}`}
                                onClick={() =>
                                  void postRunAction(
                                    run.id,
                                    "calculate",
                                    t.calculateSuccess
                                  )
                                }
                              >
                                {actioningKey === `calculate-${run.id}` ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <PlayCircle className="h-4 w-4" />
                                )}
                                {t.calculate}
                              </Button>
                            )}

                            {normalizedStatus === "CALCULATED" && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="gap-2"
                                disabled={actioningKey === `approve-${run.id}`}
                                onClick={() =>
                                  void postRunAction(
                                    run.id,
                                    "approve",
                                    t.approveSuccess
                                  )
                                }
                              >
                                {actioningKey === `approve-${run.id}` ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <CheckCircle2 className="h-4 w-4" />
                                )}
                                {t.approve}
                              </Button>
                            )}

                            {(normalizedStatus === "CALCULATED" ||
                              normalizedStatus === "APPROVED") && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="gap-2"
                                disabled={actioningKey === `reset-${run.id}`}
                                onClick={() =>
                                  void postRunAction(
                                    run.id,
                                    "reset",
                                    t.resetSuccess
                                  )
                                }
                              >
                                {actioningKey === `reset-${run.id}` ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <RotateCcw className="h-4 w-4" />
                                )}
                                {t.reset}
                              </Button>
                            )}

                            {normalizedStatus === "APPROVED" && (
                              <Button
                                size="sm"
                                className="gap-2"
                                disabled={actioningKey === `pay-${run.id}`}
                                onClick={() => openRunPaymentDialog(run)}
                              >
                                {actioningKey === `pay-${run.id}` ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Banknote className="h-4 w-4" />
                                )}
                                {t.pay}
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:hidden">
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="text-base md:text-lg">
              {t.runsList}
            </CardTitle>
          </CardHeader>

          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-14 text-muted-foreground">
                <Loader2 className="me-2 h-5 w-5 animate-spin" />
                {t.loading}
              </div>
            ) : filteredRuns.length === 0 ? (
              <div className="py-10 text-center text-sm text-muted-foreground">
                {t.noData}
              </div>
            ) : (
              <div className="space-y-4">
                {filteredRuns.map((run) => {
                  const normalizedStatus = String(run.status || "").toUpperCase()

                  return (
                    <div
                      key={run.id}
                      className="rounded-2xl border border-border/60 bg-background p-4 shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <Wallet className="h-4 w-4 shrink-0 text-muted-foreground" />
                            <h3 className="font-semibold tabular-nums">
                              {formatMonth(run.month)}
                            </h3>
                          </div>

                          <p className="text-sm text-muted-foreground">
                            #{formatNumber(run.id)} ·{" "}
                            {formatNumber(run.total_employees ?? 0)} {t.employeesUnit}
                          </p>
                        </div>

                        <StatusBadge status={run.status} locale={locale} />
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">
                            {t.totalNet}
                          </p>
                          <p className="mt-1 font-medium tabular-nums">
                            {formatNumber(run.total_net ?? 0, 2)}
                          </p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">
                            {t.progress}
                          </p>
                          <p className="mt-1 font-medium tabular-nums">
                            {formatNumber(run.progress_percent ?? 0)}%
                          </p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">
                            {t.employees}
                          </p>
                          <p className="mt-1 font-medium tabular-nums">
                            {formatNumber(run.total_employees ?? 0)}
                          </p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">
                            {t.accounting}
                          </p>
                          <p className="mt-1 font-medium">
                            {run.accounting_consistency ? t.yes : t.no}
                          </p>
                        </div>
                      </div>

                      <div className="mt-4 space-y-3">
                        <div className="flex flex-wrap gap-2">
                          <Button
                            variant="outline"
                            className="flex-1 gap-2"
                            onClick={() => router.push(`/company/payroll/${run.id}`)}
                          >
                            <Eye className="h-4 w-4" />
                            {t.view}
                          </Button>

                          {normalizedStatus === "APPROVED" && (
                            <Button
                              className="flex-1 gap-2"
                              disabled={actioningKey === `pay-${run.id}`}
                              onClick={() => openRunPaymentDialog(run)}
                            >
                              {actioningKey === `pay-${run.id}` ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Banknote className="h-4 w-4" />
                              )}
                              {t.pay}
                            </Button>
                          )}
                        </div>

                        <div className="flex flex-wrap gap-2">
                          {normalizedStatus === "DRAFT" && (
                            <Button
                              variant="outline"
                              className="flex-1 gap-2"
                              disabled={actioningKey === `calculate-${run.id}`}
                              onClick={() =>
                                void postRunAction(
                                  run.id,
                                  "calculate",
                                  t.calculateSuccess
                                )
                              }
                            >
                              {actioningKey === `calculate-${run.id}` ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <PlayCircle className="h-4 w-4" />
                              )}
                              {t.calculate}
                            </Button>
                          )}

                          {normalizedStatus === "CALCULATED" && (
                            <Button
                              variant="outline"
                              className="flex-1 gap-2"
                              disabled={actioningKey === `approve-${run.id}`}
                              onClick={() =>
                                void postRunAction(
                                  run.id,
                                  "approve",
                                  t.approveSuccess
                                )
                              }
                            >
                              {actioningKey === `approve-${run.id}` ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <CheckCircle2 className="h-4 w-4" />
                              )}
                              {t.approve}
                            </Button>
                          )}

                          {(normalizedStatus === "CALCULATED" ||
                            normalizedStatus === "APPROVED") && (
                            <Button
                              variant="outline"
                              className="flex-1 gap-2"
                              disabled={actioningKey === `reset-${run.id}`}
                              onClick={() =>
                                void postRunAction(run.id, "reset", t.resetSuccess)
                              }
                            >
                              {actioningKey === `reset-${run.id}` ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <RotateCcw className="h-4 w-4" />
                              )}
                              {t.reset}
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <p className="text-xs text-muted-foreground">{t.printHint}</p>
    </div>
  )
}