"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"

import * as XLSX from "xlsx"
import {
  Printer,
  Landmark,
  FileText,
  Loader2,
  ShieldCheck,
  ShieldX,
  Clock3,
} from "lucide-react"
import { toast } from "sonner"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type Locale = "ar" | "en"
type Direction = "rtl" | "ltr"

interface Payment {
  id: number
  company_name: string
  invoice_number: string
  method: string
  amount: number
  status: string
  paid_at: string
}

interface Stats {
  total_revenue: number
  today_payments: number
  month_payments: number
  success_rate: number
}

interface PendingDraft {
  draft_id: number
  company_name: string
  plan_name: string
  duration: string
  payment_method: string | null
  status: string
  total_amount: number
  created_at?: string | null
  admin_name?: string | null
  admin_email?: string | null
}

interface RawPendingDraft {
  draft_id?: number | string | null
  id?: number | string | null
  company_name?: string | null
  plan_name?: string | null
  plan?: {
    name?: string | null
  } | null
  subscription_plan_name?: string | null
  duration?: string | null
  payment_method?: string | null
  status?: string | null
  total_amount?: number | string | null
  pricing?: {
    total?: number | string | null
  } | null
  total?: number | string | null
  created_at?: string | null
  admin_name?: string | null
  admin_email?: string | null
  admin?: {
    name?: string | null
    email?: string | null
  } | null
}

const translations = {
  ar: {
    loadingPayments: "جارٍ تحميل المدفوعات...",
    totalRevenue: "إجمالي الإيرادات",
    paymentsToday: "مدفوعات اليوم",
    thisMonth: "هذا الشهر",
    successRate: "معدل النجاح",
    pendingRequests: "طلبات التسجيل البنكي المعلقة",
    pendingRequestsDesc:
      "طلبات التسجيل عبر التحويل البنكي التي تنتظر المراجعة الداخلية.",
    pendingCount: "معلق",
    loadingPending: "جارٍ تحميل طلبات التسجيل المعلقة...",
    noPendingRequests: "لا توجد حاليًا طلبات تسجيل بنكي معلقة.",
    draft: "المسودة",
    company: "الشركة",
    plan: "الخطة",
    duration: "المدة",
    method: "الطريقة",
    amount: "المبلغ",
    status: "الحالة",
    created: "تاريخ الإنشاء",
    action: "الإجراء",
    review: "مراجعة",
    platformPayments: "مدفوعات المنصة",
    printedAt: "تاريخ الطباعة",
    totalPayments: "إجمالي المدفوعات",
    paymentMethod: "طريقة الدفع",
    dateRange: "الفترة",
    allMethods: "كل الطرق",
    allDates: "كل التواريخ",
    searchPlaceholder: "ابحث باسم الشركة أو رقم الفاتورة...",
    resetFilters: "إعادة التصفية",
    exportExcel: "تصدير Excel",
    print: "طباعة",
    id: "المعرف",
    invoice: "الفاتورة",
    date: "التاريخ",
    details: "التفاصيل",
    view: "عرض",
    noPaymentsFound: "لا توجد مدفوعات مطابقة للفلاتر المحددة.",
    draftStatus: "مسودة",
    confirmedStatus: "مؤكد",
    paidStatus: "مدفوع",
    monthly: "شهري",
    yearly: "سنوي",
    allMethodsOption: "كل الطرق",
    exportSuccess: "تم تصدير الملف بنجاح",
    exportError: "تعذر تصدير الملف",
    printStarted: "تم فتح نافذة الطباعة",
    printError: "تعذر تنفيذ الطباعة",
    filtersReset: "تمت إعادة تعيين الفلاتر",
    paymentsLoadError: "تعذر تحميل المدفوعات",
    pendingLoadError: "تعذر تحميل الطلبات المعلقة",
  },
  en: {
    loadingPayments: "Loading payments...",
    totalRevenue: "Total Revenue",
    paymentsToday: "Payments Today",
    thisMonth: "This Month",
    successRate: "Success Rate",
    pendingRequests: "Pending Onboarding Requests",
    pendingRequestsDesc:
      "Bank transfer registration requests waiting for internal approval.",
    pendingCount: "pending",
    loadingPending: "Loading pending onboarding requests...",
    noPendingRequests: "No pending bank transfer onboarding requests found.",
    draft: "Draft",
    company: "Company",
    plan: "Plan",
    duration: "Duration",
    method: "Method",
    amount: "Amount",
    status: "Status",
    created: "Created",
    action: "Action",
    review: "Review",
    platformPayments: "Platform Payments",
    printedAt: "Printed at",
    totalPayments: "Total payments",
    paymentMethod: "Payment method",
    dateRange: "Date range",
    allMethods: "All Methods",
    allDates: "All Dates",
    searchPlaceholder: "Search company or invoice...",
    resetFilters: "Reset Filters",
    exportExcel: "Export Excel",
    print: "Print",
    id: "ID",
    invoice: "Invoice",
    date: "Date",
    details: "Details",
    view: "View",
    noPaymentsFound: "No payments found for the selected filters.",
    draftStatus: "Draft",
    confirmedStatus: "Confirmed",
    paidStatus: "Paid",
    monthly: "Monthly",
    yearly: "Yearly",
    allMethodsOption: "All Methods",
    exportSuccess: "File exported successfully",
    exportError: "Failed to export file",
    printStarted: "Print dialog opened",
    printError: "Failed to print",
    filtersReset: "Filters have been reset",
    paymentsLoadError: "Failed to load payments",
    pendingLoadError: "Failed to load pending requests",
  },
} as const

function getDocumentLocale(): Locale {
  if (typeof document === "undefined") return "en"
  const lang = (document.documentElement.lang || "en").toLowerCase()
  return lang.startsWith("ar") ? "ar" : "en"
}

function getDocumentDirection(locale: Locale): Direction {
  if (typeof document === "undefined") {
    return locale === "ar" ? "rtl" : "ltr"
  }

  const dir = (document.documentElement.dir || "").toLowerCase()
  if (dir === "rtl" || dir === "ltr") return dir as Direction
  return locale === "ar" ? "rtl" : "ltr"
}

function normalizeStatus(status: string) {
  return (status || "").trim().toUpperCase()
}

function getStatusClasses(status: string) {
  const normalized = normalizeStatus(status)

  if (normalized === "ACTIVE" || normalized === "PAID" || normalized === "CONFIRMED") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700"
  }

  if (
    normalized === "EXPIRED" ||
    normalized === "FAILED" ||
    normalized === "REJECTED" ||
    normalized === "CANCELLED" ||
    normalized === "CANCELED"
  ) {
    return "border-red-200 bg-red-50 text-red-700"
  }

  return "border-amber-200 bg-amber-50 text-amber-700"
}

function StatusPill({
  status,
  label,
}: {
  status: string
  label: string
}) {
  const normalized = normalizeStatus(status)

  const Icon =
    normalized === "ACTIVE" || normalized === "PAID" || normalized === "CONFIRMED"
      ? ShieldCheck
      : normalized === "EXPIRED" ||
          normalized === "FAILED" ||
          normalized === "REJECTED" ||
          normalized === "CANCELLED" ||
          normalized === "CANCELED"
        ? ShieldX
        : Clock3

  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
        getStatusClasses(status),
      ].join(" ")}
    >
      <Icon className="me-1 h-3.5 w-3.5" />
      {label}
    </span>
  )
}

export default function SystemPaymentsPage() {
  const [locale, setLocale] = useState<Locale>("en")
  const [direction, setDirection] = useState<Direction>("ltr")

  const [payments, setPayments] = useState<Payment[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  const [pendingDrafts, setPendingDrafts] = useState<PendingDraft[]>([])
  const [pendingDraftsLoading, setPendingDraftsLoading] = useState(true)

  const [search, setSearch] = useState("")
  const [paymentMethod, setPaymentMethod] = useState("ALL")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")

  const t = translations[locale]

  useEffect(() => {
    const syncLocale = () => {
      const nextLocale = getDocumentLocale()
      const nextDirection = getDocumentDirection(nextLocale)
      setLocale(nextLocale)
      setDirection(nextDirection)
    }

    syncLocale()

    if (typeof document === "undefined") return

    const observer = new MutationObserver(() => {
      syncLocale()
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    window.addEventListener("languagechange", syncLocale)

    return () => {
      observer.disconnect()
      window.removeEventListener("languagechange", syncLocale)
    }
  }, [])

  useEffect(() => {
    async function fetchPayments() {
      try {
        const res = await fetch(`${API}/api/system/payments/`, {
          credentials: "include",
          cache: "no-store",
        })

        if (!res.ok) {
          throw new Error(`Payments request failed with status ${res.status}`)
        }

        const data = await res.json()

        const paymentsList: Payment[] = Array.isArray(data)
          ? data
          : Array.isArray(data?.payments)
            ? data.payments
            : []

        setPayments(paymentsList)
        setStats(data?.stats || null)
      } catch (error) {
        console.error("Failed to load payments", error)
        toast.error(t.paymentsLoadError)
      } finally {
        setLoading(false)
      }
    }

    fetchPayments()
  }, [t.paymentsLoadError])

  useEffect(() => {
    async function fetchPendingDrafts() {
      try {
        setPendingDraftsLoading(true)

        const candidateEndpoints = [
          `${API}/api/system/onboarding/pending-drafts/`,
          `${API}/api/system/onboarding/drafts/`,
        ]

        let loaded = false

        for (const endpoint of candidateEndpoints) {
          try {
            const res = await fetch(endpoint, {
              credentials: "include",
              cache: "no-store",
            })

            if (!res.ok) continue

            const data = await res.json()

            const rawDrafts: RawPendingDraft[] = Array.isArray(data)
              ? data
              : Array.isArray(data?.drafts)
                ? data.drafts
                : Array.isArray(data?.results)
                  ? data.results
                  : []

            const normalized: PendingDraft[] = rawDrafts
              .map((item: RawPendingDraft): PendingDraft => ({
                draft_id: Number(item?.draft_id ?? item?.id ?? 0),
                company_name: item?.company_name || "-",
                plan_name:
                  item?.plan_name ||
                  item?.plan?.name ||
                  item?.subscription_plan_name ||
                  "-",
                duration: item?.duration || "-",
                payment_method: item?.payment_method || null,
                status: item?.status || "-",
                total_amount: Number(
                  item?.total_amount ?? item?.pricing?.total ?? item?.total ?? 0
                ),
                created_at: item?.created_at || null,
                admin_name: item?.admin_name || item?.admin?.name || null,
                admin_email: item?.admin_email || item?.admin?.email || null,
              }))
              .filter(
                (item: PendingDraft) =>
                  item.draft_id > 0 &&
                  item.status !== "PAID" &&
                  (item.payment_method === "BANK_TRANSFER" ||
                    item.payment_method === null ||
                    item.payment_method === "")
              )

            setPendingDrafts(normalized)
            loaded = true
            break
          } catch (endpointError) {
            console.error(
              `Failed to load pending drafts from ${endpoint}`,
              endpointError
            )
          }
        }

        if (!loaded) {
          setPendingDrafts([])
        }
      } catch (error) {
        console.error("Failed to load pending onboarding drafts", error)
        setPendingDrafts([])
        toast.error(t.pendingLoadError)
      } finally {
        setPendingDraftsLoading(false)
      }
    }

    fetchPendingDrafts()
  }, [t.pendingLoadError])

  function formatDate(date: string) {
    const parsed = new Date(date)

    if (Number.isNaN(parsed.getTime())) {
      return "-"
    }

    const year = parsed.getFullYear()
    const month = String(parsed.getMonth() + 1).padStart(2, "0")
    const day = String(parsed.getDate()).padStart(2, "0")

    return `${year}/${month}/${day}`
  }

  function formatPrintDate() {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, "0")
    const day = String(now.getDate()).padStart(2, "0")
    const hours = String(now.getHours()).padStart(2, "0")
    const minutes = String(now.getMinutes()).padStart(2, "0")

    return `${year}/${month}/${day} ${hours}:${minutes}`
  }

  function normalizeMethod(method: string) {
    return (method || "").trim().toUpperCase()
  }

  function getDateOnly(dateString: string) {
    const parsed = new Date(dateString)

    if (Number.isNaN(parsed.getTime())) {
      return ""
    }

    const year = parsed.getFullYear()
    const month = String(parsed.getMonth() + 1).padStart(2, "0")
    const day = String(parsed.getDate()).padStart(2, "0")

    return `${year}-${month}-${day}`
  }

  function formatMoney(value: number | string | null | undefined, currency = "SAR") {
    const num = Number(value || 0)

    if (Number.isNaN(num)) {
      return `0.00 ${currency}`
    }

    return `${num.toFixed(2)} ${currency}`
  }

  function getDraftStatusLabel(status: string) {
    switch ((status || "").toUpperCase()) {
      case "DRAFT":
        return t.draftStatus
      case "CONFIRMED":
        return t.confirmedStatus
      case "PAID":
        return t.paidStatus
      default:
        return status || "-"
    }
  }

  function getDurationLabel(duration: string) {
    switch ((duration || "").toLowerCase()) {
      case "monthly":
        return t.monthly
      case "yearly":
        return t.yearly
      default:
        return duration || "-"
    }
  }

  const paymentMethods = useMemo(() => {
    return Array.from(
      new Set(
        payments
          .map((payment) => normalizeMethod(payment.method))
          .filter(Boolean)
      )
    )
  }, [payments])

  const filteredPayments = useMemo(() => {
    const q = search.trim().toLowerCase()

    return payments.filter((payment) => {
      const matchesSearch =
        payment.company_name.toLowerCase().includes(q) ||
        payment.invoice_number.toLowerCase().includes(q)

      const matchesMethod =
        paymentMethod === "ALL" ||
        normalizeMethod(payment.method) === paymentMethod

      const paymentDate = getDateOnly(payment.paid_at)

      const matchesDateFrom = !dateFrom || (paymentDate && paymentDate >= dateFrom)

      const matchesDateTo = !dateTo || (paymentDate && paymentDate <= dateTo)

      return matchesSearch && matchesMethod && matchesDateFrom && matchesDateTo
    })
  }, [payments, search, paymentMethod, dateFrom, dateTo])

  const exportExcel = () => {
    try {
      const data = filteredPayments.map((payment) => ({
        ID: payment.id,
        Company: payment.company_name,
        Invoice: payment.invoice_number,
        Method: payment.method,
        Amount: Number(payment.amount).toFixed(2),
        Status: payment.status,
        Date: formatDate(payment.paid_at),
      }))

      const worksheet = XLSX.utils.json_to_sheet(data)
      const workbook = XLSX.utils.book_new()

      XLSX.utils.book_append_sheet(workbook, worksheet, "Payments")
      XLSX.writeFile(workbook, "primey_payments.xlsx")
      toast.success(t.exportSuccess)
    } catch (error) {
      console.error("Failed to export excel", error)
      toast.error(t.exportError)
    }
  }

  const handlePrint = () => {
    try {
      window.print()
      toast.success(t.printStarted)
    } catch (error) {
      console.error("Failed to print", error)
      toast.error(t.printError)
    }
  }

  const resetFilters = () => {
    setSearch("")
    setPaymentMethod("ALL")
    setDateFrom("")
    setDateTo("")
    toast.success(t.filtersReset)
  }

  if (loading) {
    return (
      <div
        dir={direction}
        className="p-6 text-sm text-muted-foreground"
      >
        {t.loadingPayments}
      </div>
    )
  }

  return (
    <>
      <style jsx global>{`
        @media print {
          @page {
            size: A4 landscape;
            margin: 6mm;
          }

          html,
          body {
            margin: 0 !important;
            padding: 0 !important;
            background: #ffffff !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }

          body * {
            visibility: hidden !important;
          }

          .print-area,
          .print-area * {
            visibility: visible !important;
          }

          .print-area {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            background: #ffffff !important;
            overflow: visible !important;
          }

          .no-print {
            display: none !important;
          }

          .print-card {
            width: 100% !important;
            max-width: 100% !important;
            border: none !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            background: #ffffff !important;
            overflow: visible !important;
            margin: 0 !important;
          }

          .print-card > div {
            overflow: visible !important;
          }

          .print-header {
            display: block !important;
            padding: 0 0 12px 0 !important;
            margin: 0 0 12px 0 !important;
            border-bottom: 1px solid #d1d5db !important;
          }

          .print-branding {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            margin: 0 0 12px 0 !important;
          }

          .print-logo {
            display: block !important;
            width: 180px !important;
            max-width: 180px !important;
            height: auto !important;
            object-fit: contain !important;
            margin: 0 auto 10px auto !important;
          }

          .print-title {
            font-size: 22px !important;
            font-weight: 700 !important;
            color: #111827 !important;
            margin: 0 !important;
            text-align: center !important;
          }

          .print-meta-line {
            display: block !important;
            font-size: 12px !important;
            color: #374151 !important;
            margin-top: 4px !important;
            text-align: center !important;
          }

          .print-table-wrap {
            width: 100% !important;
            overflow: visible !important;
            padding: 0 !important;
            margin: 0 !important;
          }

          .print-table-wrap [data-slot="table-container"],
          .print-table-wrap .relative,
          .print-table-wrap .w-full,
          .print-table-wrap .overflow-auto,
          .print-table-wrap .overflow-x-auto {
            overflow: visible !important;
            width: 100% !important;
            max-width: 100% !important;
          }

          table {
            width: 100% !important;
            min-width: 100% !important;
            border-collapse: collapse !important;
            table-layout: auto !important;
          }

          thead {
            display: table-header-group !important;
          }

          tbody {
            display: table-row-group !important;
          }

          tr {
            page-break-inside: avoid !important;
            break-inside: avoid !important;
          }

          th,
          td {
            font-size: 12px !important;
            line-height: 1.45 !important;
            color: #111827 !important;
            padding: 9px 8px !important;
            border-bottom: 1px solid #e5e7eb !important;
            white-space: normal !important;
            word-break: break-word !important;
            overflow: visible !important;
            text-align: left !important;
            vertical-align: middle !important;
          }

          th {
            font-weight: 700 !important;
            background: #f9fafb !important;
          }

          a {
            color: #111827 !important;
            text-decoration: none !important;
            pointer-events: none !important;
          }

          [data-slot="badge"],
          .inline-flex.items-center.rounded-full {
            border: 1px solid #d1d5db !important;
            background: transparent !important;
            color: #111827 !important;
            box-shadow: none !important;
            padding: 2px 8px !important;
          }

          .print-amount,
          .print-date,
          .print-invoice,
          .force-en {
            white-space: nowrap !important;
            direction: ltr !important;
            unicode-bidi: embed !important;
          }

          .print-company {
            white-space: normal !important;
            word-break: break-word !important;
          }
        }
      `}</style>

      <div dir={direction} className="space-y-6">
        {stats && (
          <div className="no-print grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader>
                <CardTitle>{t.totalRevenue}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold force-en" dir="ltr">
                  {formatMoney(stats.total_revenue)}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t.paymentsToday}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold force-en" dir="ltr">
                  {stats.today_payments}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t.thisMonth}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold force-en" dir="ltr">
                  {stats.month_payments}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t.successRate}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold force-en" dir="ltr">
                  {Number(stats.success_rate || 0).toFixed(2)}%
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <Card className="no-print">
          <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2">
                <Landmark className="h-5 w-5" />
                {t.pendingRequests}
              </CardTitle>

              <div className="text-sm text-muted-foreground">
                {t.pendingRequestsDesc}
              </div>
            </div>

            <Badge variant="outline">
              <span className="force-en" dir="ltr">
                {pendingDrafts.length}
              </span>{" "}
              {t.pendingCount}
            </Badge>
          </CardHeader>

          <CardContent>
            {pendingDraftsLoading ? (
              <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                {t.loadingPending}
              </div>
            ) : pendingDrafts.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[90px]">{t.draft}</TableHead>
                    <TableHead>{t.company}</TableHead>
                    <TableHead>{t.plan}</TableHead>
                    <TableHead className="w-[120px]">{t.duration}</TableHead>
                    <TableHead className="w-[150px]">{t.method}</TableHead>
                    <TableHead className="w-[130px]">{t.amount}</TableHead>
                    <TableHead className="w-[130px]">{t.status}</TableHead>
                    <TableHead className="w-[140px]">{t.created}</TableHead>
                    <TableHead className="w-[140px]">{t.action}</TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {pendingDrafts.map((draft) => (
                    <TableRow key={draft.draft_id}>
                      <TableCell className="force-en" dir="ltr">
                        #{draft.draft_id}
                      </TableCell>

                      <TableCell>
                        <div className="font-medium">{draft.company_name}</div>
                        {draft.admin_email ? (
                          <div className="text-xs text-muted-foreground force-en" dir="ltr">
                            {draft.admin_email}
                          </div>
                        ) : null}
                      </TableCell>

                      <TableCell>{draft.plan_name}</TableCell>

                      <TableCell>{getDurationLabel(draft.duration)}</TableCell>

                      <TableCell>
                        <Badge variant="secondary">
                          {draft.payment_method || "BANK_TRANSFER"}
                        </Badge>
                      </TableCell>

                      <TableCell className="force-en" dir="ltr">
                        {formatMoney(draft.total_amount)}
                      </TableCell>

                      <TableCell>
                        <StatusPill
                          status={draft.status}
                          label={getDraftStatusLabel(draft.status)}
                        />
                      </TableCell>

                      <TableCell className="force-en" dir="ltr">
                        {draft.created_at ? formatDate(draft.created_at) : "-"}
                      </TableCell>

                      <TableCell>
                        <Button asChild size="sm" variant="outline" className="gap-2">
                          <Link href={`/system/payments/${draft.draft_id}`}>
                            <FileText className="h-4 w-4" />
                            {t.review}
                          </Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="rounded-2xl border border-dashed p-8 text-center text-sm text-muted-foreground">
                {t.noPendingRequests}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="print-area">
          <Card className="print-card">
            <CardHeader className="print-header space-y-4">
              <div className="print-branding">
                <img
                  src="/logo/primey.svg"
                  alt="Primey Logo"
                  className="print-logo hidden print:block"
                />

                <CardTitle className="print-title">
                  {t.platformPayments}
                </CardTitle>

                <div className="hidden print-meta-line print:block force-en" dir="ltr">
                  {t.printedAt}: {formatPrintDate()}
                </div>

                <div className="hidden print-meta-line print:block force-en" dir="ltr">
                  {t.totalPayments}: {filteredPayments.length}
                </div>

                <div className="hidden print-meta-line print:block">
                  {t.paymentMethod}:{" "}
                  <span className="force-en" dir="ltr">
                    {paymentMethod === "ALL" ? t.allMethods : paymentMethod}
                  </span>
                </div>

                <div className="hidden print-meta-line print:block">
                  {t.dateRange}:{" "}
                  <span className="force-en" dir="ltr">
                    {dateFrom || dateTo
                      ? `${dateFrom || "—"} → ${dateTo || "—"}`
                      : t.allDates}
                  </span>
                </div>
              </div>

              <div className="no-print flex flex-col gap-3">
                <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
                  <div className="w-full xl:max-w-md">
                    <Input
                      placeholder={t.searchPlaceholder}
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                    />
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button variant="outline" onClick={resetFilters}>
                      {t.resetFilters}
                    </Button>

                    <Button variant="outline" onClick={exportExcel}>
                      {t.exportExcel}
                    </Button>

                    <Button
                      variant="outline"
                      onClick={handlePrint}
                      className="gap-2"
                    >
                      <Printer className="h-4 w-4" />
                      {t.print}
                    </Button>
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  <select
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background outline-none transition placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50"
                    dir={direction}
                  >
                    <option value="ALL">{t.allMethodsOption}</option>
                    {paymentMethods.map((method) => (
                      <option key={method} value={method}>
                        {method}
                      </option>
                    ))}
                  </select>

                  <Input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    dir="ltr"
                    lang="en"
                    className="force-en"
                  />

                  <Input
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    dir="ltr"
                    lang="en"
                    className="force-en"
                  />
                </div>
              </div>
            </CardHeader>

            <CardContent className="print-table-wrap">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[70px]">{t.id}</TableHead>
                    <TableHead>{t.company}</TableHead>
                    <TableHead className="w-[190px]">{t.invoice}</TableHead>
                    <TableHead className="w-[120px]">{t.method}</TableHead>
                    <TableHead className="w-[120px]">{t.amount}</TableHead>
                    <TableHead className="w-[120px]">{t.status}</TableHead>
                    <TableHead className="w-[120px]">{t.date}</TableHead>
                    <TableHead className="no-print w-[110px]">{t.details}</TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {filteredPayments.length > 0 ? (
                    filteredPayments.map((payment) => (
                      <TableRow key={payment.id}>
                        <TableCell className="force-en" dir="ltr">
                          #{payment.id}
                        </TableCell>

                        <TableCell className="print-company">
                          {payment.company_name}
                        </TableCell>

                        <TableCell className="print-invoice force-en" dir="ltr">
                          <Link
                            href={`/system/invoices/${payment.invoice_number}`}
                            className="font-medium text-blue-600 hover:underline"
                          >
                            {payment.invoice_number}
                          </Link>
                        </TableCell>

                        <TableCell>
                          <Badge variant="secondary">
                            {payment.method}
                          </Badge>
                        </TableCell>

                        <TableCell>
                          <span className="print-amount force-en" dir="ltr">
                            {formatMoney(payment.amount)}
                          </span>
                        </TableCell>

                        <TableCell>
                          <StatusPill
                            status={payment.status}
                            label={payment.status}
                          />
                        </TableCell>

                        <TableCell className="print-date force-en" dir="ltr">
                          {formatDate(payment.paid_at)}
                        </TableCell>

                        <TableCell className="no-print">
                          <Button asChild variant="outline" size="sm">
                            <Link href={`/system/payments/pay/${payment.id}`}>
                              {t.view}
                            </Link>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={8}
                        className="py-10 text-center text-muted-foreground"
                      >
                        {t.noPaymentsFound}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  )
}