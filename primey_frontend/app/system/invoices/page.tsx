"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import * as XLSX from "xlsx"
import { Download, Printer } from "lucide-react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table"

import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"

const API = "http://localhost:8000/api"

interface Invoice {
  id: number
  invoice_number: string
  company_name: string | null
  plan_name: string | null
  status: string
  total_amount: string
  issue_date: string | null
}

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)

  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("ALL")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")

  /* ===============================
     LOAD INVOICES
  =============================== */
  useEffect(() => {
    async function loadInvoices() {
      try {
        const res = await fetch(`${API}/system/invoices/`, {
          credentials: "include"
        })

        const data = await res.json()

        if (!res.ok) {
          toast.error(data.error || "Failed to load invoices")
          return
        }

        setInvoices(data?.data?.results || [])
      } catch (error) {
        console.error("Load invoices error:", error)
        toast.error("Failed to load invoices")
      } finally {
        setLoading(false)
      }
    }

    loadInvoices()
  }, [])

  /* ===============================
     HELPERS
  =============================== */
  function formatDate(date: string | null) {
    if (!date) return "-"

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

  function getDateOnly(date: string | null) {
    if (!date) return ""

    const parsed = new Date(date)

    if (Number.isNaN(parsed.getTime())) {
      return ""
    }

    const year = parsed.getFullYear()
    const month = String(parsed.getMonth() + 1).padStart(2, "0")
    const day = String(parsed.getDate()).padStart(2, "0")

    return `${year}-${month}-${day}`
  }

  const invoiceStatuses = useMemo(() => {
    return Array.from(
      new Set(
        invoices
          .map((invoice) => (invoice.status || "").trim().toUpperCase())
          .filter(Boolean)
      )
    )
  }, [invoices])

  /* ===============================
     FILTER
  =============================== */
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()

    return invoices.filter((invoice) => {
      const matchesSearch =
        !q ||
        invoice.invoice_number.toLowerCase().includes(q) ||
        (invoice.company_name || "").toLowerCase().includes(q)

      const normalizedStatus = (invoice.status || "").trim().toUpperCase()

      const matchesStatus =
        statusFilter === "ALL" || normalizedStatus === statusFilter

      const invoiceDate = getDateOnly(invoice.issue_date)

      const matchesDateFrom =
        !dateFrom || (invoiceDate && invoiceDate >= dateFrom)

      const matchesDateTo =
        !dateTo || (invoiceDate && invoiceDate <= dateTo)

      return (
        matchesSearch &&
        matchesStatus &&
        matchesDateFrom &&
        matchesDateTo
      )
    })
  }, [invoices, search, statusFilter, dateFrom, dateTo])

  /* ===============================
     ACTIONS
  =============================== */
  function handlePrint() {
    try {
      window.print()
    } catch (error) {
      console.error("Print error:", error)
      toast.error("Failed to open print dialog")
    }
  }

  function handleExportExcel() {
    try {
      const rows = filtered.map((invoice) => ({
        ID: invoice.id,
        Invoice: invoice.invoice_number,
        Company: invoice.company_name || "-",
        Plan: invoice.plan_name || "-",
        Amount_SAR: invoice.total_amount,
        Status: invoice.status,
        Date: formatDate(invoice.issue_date)
      }))

      const worksheet = XLSX.utils.json_to_sheet(rows)
      const workbook = XLSX.utils.book_new()

      XLSX.utils.book_append_sheet(workbook, worksheet, "Invoices")

      const today = new Date().toISOString().split("T")[0]
      XLSX.writeFile(workbook, `platform_invoices_${today}.xlsx`)

      toast.success("Excel exported successfully")
    } catch (error) {
      console.error("Excel export error:", error)
      toast.error("Failed to export Excel")
    }
  }

  function resetFilters() {
    setSearch("")
    setStatusFilter("ALL")
    setDateFrom("")
    setDateTo("")
  }

  /* ===============================
     UI
  =============================== */
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
          .print-invoice {
            white-space: nowrap !important;
          }

          .print-company {
            white-space: normal !important;
            word-break: break-word !important;
          }
        }
      `}</style>

      <div className="space-y-6 p-6">
        <div className="print-area">
          <Card className="print-card overflow-hidden">
            <CardHeader className="print-header space-y-4">
              <div className="print-topbar">
                <div className="print-meta">
                  <CardTitle className="print-title">
                    Platform Invoices
                  </CardTitle>

                  <div className="hidden print-meta-line print:block">
                    Printed at: {formatPrintDate()}
                  </div>

                  <div className="hidden print-meta-line print:block">
                    Total invoices: {filtered.length}
                  </div>

                  <div className="hidden print-meta-line print:block">
                    Status filter:{" "}
                    {statusFilter === "ALL" ? "All Statuses" : statusFilter}
                  </div>

                  <div className="hidden print-meta-line print:block">
                    Date range:{" "}
                    {dateFrom || dateTo
                      ? `${dateFrom || "—"} → ${dateTo || "—"}`
                      : "All Dates"}
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
                {/* الصف الأول: البحث + الأزرار */}
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div className="w-full lg:max-w-sm">
                    <Input
                      placeholder="Search invoice or company..."
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                    />
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={resetFilters}
                    >
                      Reset Filters
                    </Button>

                    <Button
                      type="button"
                      variant="outline"
                      onClick={handlePrint}
                      className="gap-2"
                    >
                      <Printer className="h-4 w-4" />
                      Print
                    </Button>

                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleExportExcel}
                      className="gap-2"
                      disabled={loading || filtered.length === 0}
                    >
                      <Download className="h-4 w-4" />
                      Export Excel
                    </Button>
                  </div>
                </div>

                {/* الصف الثاني: الفلاتر */}
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background outline-none transition placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50"
                  >
                    <option value="ALL">All Statuses</option>
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
                  />

                  <Input
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                  />
                </div>
              </div>
            </CardHeader>

            <CardContent className="print-table-wrap overflow-x-visible p-0 sm:p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[70px]">ID</TableHead>
                    <TableHead className="w-[180px]">Invoice</TableHead>
                    <TableHead>Company</TableHead>
                    <TableHead className="w-[150px]">Plan</TableHead>
                    <TableHead className="w-[140px]">Amount</TableHead>
                    <TableHead className="w-[120px]">Status</TableHead>
                    <TableHead className="w-[120px]">Date</TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={7}>
                        Loading invoices...
                      </TableCell>
                    </TableRow>
                  ) : filtered.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7}>
                        No invoices found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filtered.map((invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell>
                          #{invoice.id}
                        </TableCell>

                        <TableCell className="print-invoice">
                          <Link
                            href={`/system/invoices/${invoice.invoice_number}`}
                            className="font-medium text-blue-600 hover:underline"
                          >
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
                          <span className="print-amount">
                            {invoice.total_amount} SAR
                          </span>
                        </TableCell>

                        <TableCell>
                          <Badge
                            variant={
                              invoice.status === "PAID"
                                ? "default"
                                : invoice.status === "PENDING"
                                  ? "secondary"
                                  : "destructive"
                            }
                          >
                            {invoice.status}
                          </Badge>
                        </TableCell>

                        <TableCell className="print-date">
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