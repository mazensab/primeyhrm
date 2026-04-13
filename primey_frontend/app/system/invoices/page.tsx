"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import * as XLSX from "xlsx"
import {
  Download,
  Printer,
  Loader2,
  ShieldCheck,
  ShieldX,
  Clock3,
  FileText,
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

import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

/* ======================================================
   API Helpers
====================================================== */

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, "")
}

function resolveApiBase() {
  const envApi = process.env.NEXT_PUBLIC_API_URL?.trim()

  if (envApi) {
    return trimTrailingSlash(envApi)
  }

  if (typeof window !== "undefined") {
    return trimTrailingSlash(window.location.origin)
  }

  return ""
}

type Locale = "ar" | "en"
type Direction = "rtl" | "ltr"

interface Invoice {
  id: number
  invoice_number: string
  company_name: string | null
  plan_name: string | null
  status: string
  total_amount: string
  issue_date: string | null
}

const translations = {
  ar: {
    pageTitle: "الفواتير",
    printTitle: "فواتير المنصة",
    printedAt: "تاريخ الطباعة",
    totalInvoices: "إجمالي الفواتير",
    statusFilter: "فلتر الحالة",
    dateRange: "الفترة",
    allStatuses: "كل الحالات",
    allDates: "كل التواريخ",
    searchPlaceholder: "ابحث برقم الفاتورة أو اسم الشركة...",
    resetFilters: "إعادة التصفية",
    print: "طباعة",
    exportExcel: "تصدير Excel",
    id: "المعرف",
    invoice: "الفاتورة",
    company: "الشركة",
    plan: "الخطة",
    amount: "المبلغ",
    status: "الحالة",
    date: "التاريخ",
    loadingInvoices: "جارٍ تحميل الفواتير...",
    noInvoicesFound: "لا توجد فواتير مطابقة",
    exportSuccess: "تم تصدير الملف بنجاح",
    exportError: "تعذر تصدير الملف",
    printError: "تعذر فتح نافذة الطباعة",
    printStarted: "تم فتح نافذة الطباعة",
    resetSuccess: "تمت إعادة تعيين الفلاتر",
    loadError: "تعذر تحميل الفواتير",
    statusPaid: "مدفوعة",
    statusPending: "معلقة",
    statusDraft: "مسودة",
    statusCancelled: "ملغاة",
    statusFailed: "فاشلة",
    statusOverdue: "متأخرة",
    statusUnknown: "غير معروف",
  },
  en: {
    pageTitle: "Invoices",
    printTitle: "Platform Invoices",
    printedAt: "Printed at",
    totalInvoices: "Total invoices",
    statusFilter: "Status filter",
    dateRange: "Date range",
    allStatuses: "All Statuses",
    allDates: "All Dates",
    searchPlaceholder: "Search by invoice number or company...",
    resetFilters: "Reset Filters",
    print: "Print",
    exportExcel: "Export Excel",
    id: "ID",
    invoice: "Invoice",
    company: "Company",
    plan: "Plan",
    amount: "Amount",
    status: "Status",
    date: "Date",
    loadingInvoices: "Loading invoices...",
    noInvoicesFound: "No matching invoices found",
    exportSuccess: "File exported successfully",
    exportError: "Failed to export file",
    printError: "Failed to open print dialog",
    printStarted: "Print dialog opened",
    resetSuccess: "Filters have been reset",
    loadError: "Failed to load invoices",
    statusPaid: "Paid",
    statusPending: "Pending",
    statusDraft: "Draft",
    statusCancelled: "Cancelled",
    statusFailed: "Failed",
    statusOverdue: "Overdue",
    statusUnknown: "Unknown",
  },
} as const

function getDocumentLocale(): Locale {
  if (typeof document === "undefined") return "en"

  const htmlLang = (document.documentElement.lang || "").toLowerCase().trim()
  if (htmlLang.startsWith("ar")) return "ar"
  if (htmlLang.startsWith("en")) return "en"

  const bodyLang = (document.body?.getAttribute("lang") || "").toLowerCase().trim()
  if (bodyLang.startsWith("ar")) return "ar"
  if (bodyLang.startsWith("en")) return "en"

  const htmlDir = (document.documentElement.dir || "").toLowerCase().trim()
  if (htmlDir === "rtl") return "ar"
  if (htmlDir === "ltr") return "en"

  if (typeof navigator !== "undefined") {
    const lang = (navigator.language || "").toLowerCase()
    if (lang.startsWith("ar")) return "ar"
  }

  return "en"
}

function getDocumentDirection(locale: Locale): Direction {
  if (typeof document === "undefined") {
    return locale === "ar" ? "rtl" : "ltr"
  }

  const dir = (document.documentElement.dir || "").toLowerCase().trim()
  if (dir === "rtl" || dir === "ltr") return dir as Direction

  return locale === "ar" ? "rtl" : "ltr"
}

function normalizeStatus(status: string | null | undefined) {
  return String(status || "").trim().toUpperCase()
}

function formatDate(date: string | null) {
  if (!date) return "-"

  const parsed = new Date(date)
  if (Number.isNaN(parsed.getTime())) return "-"

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

function getDateOnly(date: string | null) {
  if (!date) return ""

  const parsed = new Date(date)
  if (Number.isNaN(parsed.getTime())) return ""

  const year = parsed.getFullYear()
  const month = String(parsed.getMonth() + 1).padStart(2, "0")
  const day = String(parsed.getDate()).padStart(2, "0")

  return `${year}-${month}-${day}`
}

function formatAmountEn(value: string | number | null | undefined) {
  const numberValue = Number(value || 0)

  if (Number.isNaN(numberValue)) {
    return "0.00"
  }

  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numberValue)
}

function getLocalizedStatus(status: string, locale: Locale) {
  const t = translations[locale]
  const normalized = normalizeStatus(status)

  if (normalized === "PAID") return t.statusPaid
  if (normalized === "PENDING") return t.statusPending
  if (normalized === "DRAFT") return t.statusDraft
  if (normalized === "CANCELLED" || normalized === "CANCELED") return t.statusCancelled
  if (normalized === "FAILED") return t.statusFailed
  if (normalized === "OVERDUE") return t.statusOverdue

  return t.statusUnknown
}

function getStatusClasses(status: string) {
  const normalized = normalizeStatus(status)

  if (normalized === "PAID") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700"
  }

  if (
    normalized === "FAILED" ||
    normalized === "CANCELLED" ||
    normalized === "CANCELED" ||
    normalized === "OVERDUE"
  ) {
    return "border-red-200 bg-red-50 text-red-700"
  }

  return "border-amber-200 bg-amber-50 text-amber-700"
}

function InvoiceStatusPill({
  status,
  locale,
}: {
  status: string
  locale: Locale
}) {
  const normalized = normalizeStatus(status)
  const label = getLocalizedStatus(status, locale)

  const Icon =
    normalized === "PAID"
      ? ShieldCheck
      : normalized === "FAILED" ||
          normalized === "CANCELLED" ||
          normalized === "CANCELED" ||
          normalized === "OVERDUE"
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

export default function InvoicesPage() {
  const API = useMemo(() => resolveApiBase(), [])

  const [locale, setLocale] = useState<Locale>("en")
  const [direction, setDirection] = useState<Direction>("ltr")

  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)

  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("ALL")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")

  const t = translations[locale]
  const isArabic = locale === "ar"

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
    window.addEventListener("focus", syncLocale)

    return () => {
      observer.disconnect()
      window.removeEventListener("languagechange", syncLocale)
      window.removeEventListener("focus", syncLocale)
    }
  }, [])

  useEffect(() => {
    async function loadInvoices() {
      if (!API) {
        setLoading(false)
        return
      }

      try {
        const res = await fetch(`${API}/api/system/invoices/`, {
          credentials: "include",
          cache: "no-store",
        })

        const data = await res.json()

        if (!res.ok) {
          toast.error(data?.error || translations[getDocumentLocale()].loadError)
          return
        }

        setInvoices(Array.isArray(data?.data?.results) ? data.data.results : [])
      } catch (error) {
        console.error("Load invoices error:", error)
        toast.error(translations[getDocumentLocale()].loadError)
      } finally {
        setLoading(false)
      }
    }

    void loadInvoices()
  }, [API])

  const invoiceStatuses = useMemo(() => {
    return Array.from(
      new Set(
        invoices
          .map((invoice) => normalizeStatus(invoice.status))
          .filter(Boolean)
      )
    )
  }, [invoices])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()

    return invoices.filter((invoice) => {
      const matchesSearch =
        !q ||
        invoice.invoice_number.toLowerCase().includes(q) ||
        (invoice.company_name || "").toLowerCase().includes(q)

      const normalized = normalizeStatus(invoice.status)

      const matchesStatus =
        statusFilter === "ALL" || normalized === statusFilter

      const invoiceDate = getDateOnly(invoice.issue_date)

      const matchesDateFrom =
        !dateFrom || (invoiceDate && invoiceDate >= dateFrom)

      const matchesDateTo =
        !dateTo || (invoiceDate && invoiceDate <= dateTo)

      return matchesSearch && matchesStatus && matchesDateFrom && matchesDateTo
    })
  }, [invoices, search, statusFilter, dateFrom, dateTo])

  function handlePrint() {
    try {
      window.print()
      toast.success(t.printStarted)
    } catch (error) {
      console.error("Print error:", error)
      toast.error(t.printError)
    }
  }

  function handleExportExcel() {
    try {
      const rows = filtered.map((invoice) => ({
        ID: invoice.id,
        Invoice: invoice.invoice_number,
        Company: invoice.company_name || "-",
        Plan: invoice.plan_name || "-",
        Amount_SAR: formatAmountEn(invoice.total_amount),
        Status: normalizeStatus(invoice.status),
        Date: formatDate(invoice.issue_date),
      }))

      const worksheet = XLSX.utils.json_to_sheet(rows)
      const workbook = XLSX.utils.book_new()

      XLSX.utils.book_append_sheet(workbook, worksheet, "Invoices")

      const today = new Date().toISOString().split("T")[0]
      XLSX.writeFile(workbook, `platform_invoices_${today}.xlsx`)

      toast.success(t.exportSuccess)
    } catch (error) {
      console.error("Excel export error:", error)
      toast.error(t.exportError)
    }
  }

  function resetFilters() {
    setSearch("")
    setStatusFilter("ALL")
    setDateFrom("")
    setDateTo("")
    toast.success(t.resetSuccess)
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
            padding: 0 0 10px 0 !important;
            margin: 0 0 10px 0 !important;
            border-bottom: 1px solid #d1d5db !important;
          }

          .print-topbar {
            display: flex !important;
            align-items: flex-start !important;
            justify-content: space-between !important;
            gap: 16px !important;
            margin-bottom: 8px !important;
            direction: ltr !important;
          }

          .print-meta {
            display: block !important;
            flex: 1 !important;
          }

          .print-logo-wrap {
            display: flex !important;
            justify-content: flex-end !important;
            align-items: flex-start !important;
            min-width: 180px !important;
            flex-shrink: 0 !important;
          }

          .print-logo {
            display: block !important;
            width: 140px !important;
            max-width: 140px !important;
            height: auto !important;
            object-fit: contain !important;
          }

          .print-meta-line {
            display: block !important;
            font-size: 12px !important;
            color: #374151 !important;
            margin-top: 4px !important;
          }

          .print-title {
            font-size: 22px !important;
            font-weight: 700 !important;
            color: #111827 !important;
            margin: 0 !important;
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

          img:not(.print-logo) {
            display: none !important;
          }

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

      <div dir={direction} className="space-y-6 p-6">
        <div className="print-area">
          <Card className="print-card overflow-hidden">
            <CardHeader className="print-header space-y-4">
              <div className="print-topbar">
                <div className="print-meta">
                  <CardTitle className="print-title">
                    {t.printTitle}
                  </CardTitle>

                  <div className="hidden print-meta-line print:block force-en" dir="ltr">
                    {t.printedAt}: {formatPrintDate()}
                  </div>

                  <div className="hidden print-meta-line print:block force-en" dir="ltr">
                    {t.totalInvoices}: {filtered.length}
                  </div>

                  <div className="hidden print-meta-line print:block">
                    {t.statusFilter}:{" "}
                    <span className="force-en" dir="ltr">
                      {statusFilter === "ALL" ? t.allStatuses : statusFilter}
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

                <div className="print-logo-wrap hidden print:flex">
                  <img
                    src="/logo/primey.svg"
                    alt="Primey Logo"
                    className="print-logo"
                  />
                </div>
              </div>

              <div className="no-print flex flex-col gap-3">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div className="w-full lg:max-w-sm">
                    <Input
                      placeholder={t.searchPlaceholder}
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className={isArabic ? "text-right" : "text-left"}
                    />
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={resetFilters}
                    >
                      {t.resetFilters}
                    </Button>

                    <Button
                      type="button"
                      variant="outline"
                      onClick={handlePrint}
                      className="gap-2"
                    >
                      <Printer className="h-4 w-4" />
                      {t.print}
                    </Button>

                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleExportExcel}
                      className="gap-2"
                      disabled={loading || filtered.length === 0}
                    >
                      <Download className="h-4 w-4" />
                      {t.exportExcel}
                    </Button>
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background outline-none transition placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50"
                    dir={direction}
                  >
                    <option value="ALL">{t.allStatuses}</option>
                    {invoiceStatuses.map((status) => (
                      <option key={status} value={status}>
                        {status}
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

            <CardContent className="print-table-wrap overflow-x-visible p-0 sm:p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[70px]">{t.id}</TableHead>
                    <TableHead className="w-[180px]">{t.invoice}</TableHead>
                    <TableHead>{t.company}</TableHead>
                    <TableHead className="w-[150px]">{t.plan}</TableHead>
                    <TableHead className="w-[140px]">{t.amount}</TableHead>
                    <TableHead className="w-[140px]">{t.status}</TableHead>
                    <TableHead className="w-[120px]">{t.date}</TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">
                        <div className="flex items-center justify-center gap-2">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          {t.loadingInvoices}
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : filtered.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">
                        {t.noInvoicesFound}
                      </TableCell>
                    </TableRow>
                  ) : (
                    filtered.map((invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell className="force-en" dir="ltr">
                          #{invoice.id}
                        </TableCell>

                        <TableCell className="print-invoice force-en" dir="ltr">
                          <Link
                            href={`/system/invoices/${invoice.invoice_number}`}
                            className="inline-flex items-center gap-2 font-medium text-blue-600 hover:underline"
                          >
                            <FileText className="h-4 w-4 shrink-0" />
                            {invoice.invoice_number}
                          </Link>
                        </TableCell>

                        <TableCell className="print-company">
                          {invoice.company_name || "-"}
                        </TableCell>

                        <TableCell>
                          {invoice.plan_name || "-"}
                        </TableCell>

                        <TableCell>
                          <span className="print-amount force-en" dir="ltr">
                            {formatAmountEn(invoice.total_amount)} SAR
                          </span>
                        </TableCell>

                        <TableCell>
                          <InvoiceStatusPill
                            status={invoice.status}
                            locale={locale}
                          />
                        </TableCell>

                        <TableCell className="print-date force-en" dir="ltr">
                          {formatDate(invoice.issue_date)}
                        </TableCell>
                      </TableRow>
                    ))
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