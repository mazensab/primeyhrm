"use client"

import { useParams, useRouter } from "next/navigation"
import { useEffect, useMemo, useState } from "react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"

import {
  CreditCard,
  Wallet,
  Banknote,
  ArrowLeft,
  Building2,
  ReceiptText,
  CheckCircle2,
  Landmark,
  FileText,
  ShieldCheck,
  Printer,
  QrCode
} from "lucide-react"

const API = "http://localhost:8000/api"

type PaymentMethod =
  | "CASH"
  | "BANK_TRANSFER"
  | "CREDIT_CARD"

interface InvoiceDetail {
  id: number
  invoice_number: string
  status: string
  company_name: string
  plan_name: string
  issue_date: string | null
  due_date: string | null
  subtotal: string | number
  discount: string | number
  vat: string | number
  total: string | number
  payment_method: string | null
  paid_at: string | null
  currency: string
}

export default function InvoicePage() {
  const params = useParams()
  const router = useRouter()

  /* ==============================
     SAFE PARAM
  ============================== */
  const invoiceNumber = useMemo(() => {
    const raw =
      params?.invoice_number ??
      params?.number

    return Array.isArray(raw) ? raw[0] : raw
  }, [params])

  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [paying, setPaying] = useState(false)
  const [method, setMethod] = useState<PaymentMethod>("CASH")
  const [qrValue, setQrValue] = useState("")

  /* ==============================
     HELPERS
  ============================== */
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

  function formatMoney(value: string | number | null | undefined) {
    const num = Number(value || 0)
    const currency = invoice?.currency || "SAR"

    if (Number.isNaN(num)) {
      return `0.00 ${currency}`
    }

    return `${num.toFixed(2)} ${currency}`
  }

  function getStatusBadgeVariant(status: string) {
    if (status === "PAID") return "default"
    if (status === "PENDING") return "secondary"
    return "destructive"
  }

  function getMethodLabel(value: PaymentMethod) {
    switch (value) {
      case "CASH":
        return "Cash"
      case "BANK_TRANSFER":
        return "Bank Transfer"
      case "CREDIT_CARD":
        return "Credit Card"
      default:
        return value
    }
  }

  function handlePrint() {
    try {
      window.print()
    } catch (error) {
      console.error("Print error:", error)
      toast.error("Failed to open print dialog")
    }
  }

  /* ==============================
     LOAD INVOICE
  ============================== */
  useEffect(() => {
    if (!invoiceNumber) {
      setLoading(false)
      setInvoice(null)
      return
    }

    async function loadInvoice() {
      try {
        setLoading(true)

        const res = await fetch(
          `${API}/system/invoices/${invoiceNumber}/`,
          {
            credentials: "include"
          }
        )

        const data = await res.json()

        if (!res.ok) {
          toast.error(data.error || "Invoice not found")
          setInvoice(null)
          return
        }

        setInvoice(data)
      } catch (error) {
        console.error("Load invoice error:", error)
        toast.error("Failed to load invoice")
        setInvoice(null)
      } finally {
        setLoading(false)
      }
    }

    loadInvoice()
  }, [invoiceNumber])

  /* ==============================
     QR VALUE
  ============================== */
  useEffect(() => {
    if (typeof window !== "undefined") {
      setQrValue(window.location.href)
    }
  }, [invoiceNumber])

  /* ==============================
     PAY
  ============================== */
  const pay = async () => {
    if (!invoice) return

    try {
      setPaying(true)

      const csrf = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrftoken="))
        ?.split("=")[1]

      const res = await fetch(
        `${API}/system/payments/confirm-cash/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf || ""
          },
          body: JSON.stringify({
            invoice_id: invoice.id,
            method
          })
        }
      )

      const data = await res.json()

      if (!res.ok) {
        toast.error(data.error || "Payment failed")
        return
      }

      toast.success("Payment completed")

      const refreshRes = await fetch(
        `${API}/system/invoices/${invoice.invoice_number}/`,
        {
          credentials: "include"
        }
      )

      const refreshData = await refreshRes.json()

      if (refreshRes.ok) {
        setInvoice(refreshData)
      }
    } catch (error) {
      console.error("Payment error:", error)
      toast.error("Payment failed")
    } finally {
      setPaying(false)
    }
  }

  /* ==============================
     LOADING
  ============================== */
  if (loading) {
    return (
      <div className="p-10">
        Loading invoice...
      </div>
    )
  }

  if (!invoice) {
    return (
      <div className="space-y-4 p-10">
        <div className="text-lg font-medium">
          Invoice not found
        </div>

        <Button
          variant="outline"
          onClick={() => router.push("/system/invoices")}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to invoices
        </Button>
      </div>
    )
  }

  const subtotal = Number(invoice.subtotal || 0)
  const discount = Number(invoice.discount || 0)
  const vat = Number(invoice.vat || 0)
  const total = Number(invoice.total || 0)

  const qrImageUrl = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(
    qrValue || invoice.invoice_number
  )}`

  /* ==============================
     UI
  ============================== */
  return (
    <>
      <style jsx global>{`
        @media print {
          @page {
            size: A4 portrait;
            margin: 8mm;
          }

          html,
          body {
            width: 210mm !important;
            height: 297mm !important;
            background: #ffffff !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }

          body * {
            visibility: hidden !important;
          }

          .print-invoice-block,
          .print-invoice-block * {
            visibility: visible !important;
          }

          .print-invoice-block {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 194mm !important;
            min-height: 279mm !important;
            max-height: 279mm !important;
            margin: 0 !important;
            padding: 0 !important;
            background: #ffffff !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            border: none !important;
            overflow: hidden !important;
          }

          .no-print {
            display: none !important;
          }

          .print-card {
            box-shadow: none !important;
            break-inside: avoid !important;
            page-break-inside: avoid !important;
          }

          .print-card,
          .print-card > div {
            overflow: visible !important;
          }

          .print-header {
            padding: 14px 14px 12px 14px !important;
          }

          .print-body {
            padding: 12px 14px 14px 14px !important;
            gap: 12px !important;
          }

          .print-icon-box {
            width: 34px !important;
            height: 34px !important;
            border-radius: 10px !important;
          }

          .print-icon-box svg {
            width: 18px !important;
            height: 18px !important;
          }

          .print-title {
            font-size: 16px !important;
            line-height: 1.2 !important;
          }

          .print-subtitle {
            font-size: 9px !important;
            line-height: 1.3 !important;
          }

          .print-top-meta {
            gap: 8px !important;
          }

          .print-meta-row {
            min-height: 30px !important;
            padding: 0 10px !important;
            border-radius: 10px !important;
            font-size: 9.5px !important;
          }

          .print-info-grid {
            gap: 10px !important;
          }

          .print-info-card {
            padding: 12px !important;
            border-radius: 14px !important;
          }

          .print-info-card h3 {
            font-size: 10px !important;
          }

          .print-info-card .print-company-name {
            font-size: 11px !important;
          }

          .print-info-card .print-small-text {
            font-size: 9px !important;
            line-height: 1.35 !important;
          }

          .print-items-wrap {
            border-radius: 14px !important;
            overflow: hidden !important;
          }

          .print-items-title {
            padding: 10px 14px !important;
            font-size: 10px !important;
          }

          .print-table-wrap {
            overflow: hidden !important;
          }

          .print-table {
            width: 100% !important;
            min-width: 100% !important;
            table-layout: fixed !important;
            border-collapse: collapse !important;
          }

          .print-table th,
          .print-table td {
            border-bottom: 1px solid #e5e7eb !important;
            padding: 8px 6px !important;
            text-align: left !important;
            font-size: 9.5px !important;
            color: #111827 !important;
            white-space: normal !important;
            word-break: break-word !important;
          }

          .print-table th {
            background: #f9fafb !important;
            font-weight: 700 !important;
          }

          .print-table th:nth-child(1),
          .print-table td:nth-child(1) {
            width: 30% !important;
          }

          .print-table th:nth-child(2),
          .print-table td:nth-child(2) {
            width: 28% !important;
          }

          .print-table th:nth-child(3),
          .print-table td:nth-child(3) {
            width: 8% !important;
          }

          .print-table th:nth-child(4),
          .print-table td:nth-child(4) {
            width: 17% !important;
          }

          .print-table th:nth-child(5),
          .print-table td:nth-child(5) {
            width: 17% !important;
          }

          .print-total-grid {
            display: grid !important;
            grid-template-columns: 1fr 120px !important;
            gap: 10px !important;
            align-items: stretch !important;
          }

          .print-total-card {
            padding: 12px !important;
            border-radius: 14px !important;
          }

          .print-total-row {
            font-size: 9.5px !important;
          }

          .print-total-final {
            font-size: 11px !important;
          }

          .print-qr-inline {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 14px !important;
            background: #ffffff !important;
            padding: 10px !important;
            min-height: 100% !important;
          }

          .print-qr-inline img {
            width: 88px !important;
            height: 88px !important;
            object-fit: contain !important;
          }
        }
      `}</style>

      <div className="mx-auto max-w-7xl space-y-6 p-6">
        <div className="flex flex-col gap-4 rounded-3xl border bg-background p-6 shadow-sm lg:flex-row lg:items-center lg:justify-between no-print">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <ReceiptText className="h-4 w-4" />
              Sales Invoice
            </div>

            <h1 className="text-3xl font-bold tracking-tight">
              {invoice.invoice_number}
            </h1>

            <p className="text-sm text-muted-foreground">
              Structured sales invoice view with billing summary and payment status.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Badge
              variant={getStatusBadgeVariant(invoice.status)}
              className="px-4 py-1 text-sm"
            >
              {invoice.status}
            </Badge>

            <Button
              variant="outline"
              onClick={handlePrint}
              className="gap-2"
            >
              <Printer className="h-4 w-4" />
              Print
            </Button>

            <Button
              variant="outline"
              onClick={() => router.push("/system/invoices")}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
          </div>
        </div>

        <div className="grid gap-6 xl:grid-cols-12">
          <Card className="print-invoice-block print-card overflow-hidden xl:col-span-8">
            <CardHeader className="print-header border-b bg-muted/30 pb-6">
              <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-4">
                  <div className="print-icon-box flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
                    <FileText className="h-7 w-7 text-primary" />
                  </div>

                  <div>
                    <CardTitle className="print-title text-2xl font-bold">
                      Sales Invoice
                    </CardTitle>
                    <p className="print-subtitle mt-1 text-sm text-muted-foreground">
                      Primey HR Cloud Billing Document
                    </p>
                  </div>
                </div>

                <div className="print-top-meta grid gap-3 text-sm lg:min-w-[280px]">
                  <div className="print-meta-row flex items-center justify-between rounded-xl border bg-background px-4 py-3">
                    <span className="text-muted-foreground">Invoice No.</span>
                    <span className="font-semibold">{invoice.invoice_number}</span>
                  </div>

                  <div className="print-meta-row flex items-center justify-between rounded-xl border bg-background px-4 py-3">
                    <span className="text-muted-foreground">Issue Date</span>
                    <span className="font-medium">{formatDate(invoice.issue_date)}</span>
                  </div>

                  <div className="print-meta-row flex items-center justify-between rounded-xl border bg-background px-4 py-3">
                    <span className="text-muted-foreground">Due Date</span>
                    <span className="font-medium">{formatDate(invoice.due_date)}</span>
                  </div>
                </div>
              </div>
            </CardHeader>

            <CardContent className="print-body space-y-6 p-6">
              <div className="print-info-grid grid gap-4 md:grid-cols-2">
                <div className="print-info-card rounded-2xl border p-5">
                  <div className="mb-4 flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-primary" />
                    <h3 className="font-semibold">Bill To</h3>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="print-company-name font-semibold text-base">
                      {invoice.company_name || "-"}
                    </div>
                    <div className="print-small-text text-muted-foreground">
                      Customer account for subscription billing
                    </div>
                    <div className="print-small-text text-muted-foreground">
                      Currency: {invoice.currency || "SAR"}
                    </div>
                  </div>
                </div>

                <div className="print-info-card rounded-2xl border p-5">
                  <div className="mb-4 flex items-center gap-2">
                    <Landmark className="h-4 w-4 text-primary" />
                    <h3 className="font-semibold">Invoice Summary</h3>
                  </div>

                  <div className="space-y-3 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Status</span>
                      <Badge variant={getStatusBadgeVariant(invoice.status)}>
                        {invoice.status}
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Payment Method</span>
                      <span className="font-medium">
                        {invoice.payment_method || "-"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Paid At</span>
                      <span className="font-medium">
                        {formatDate(invoice.paid_at)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="print-items-wrap overflow-hidden rounded-2xl border">
                <div className="print-items-title border-b bg-muted/40 px-5 py-4">
                  <h3 className="font-semibold">Invoice Items</h3>
                </div>

                <div className="print-table-wrap overflow-x-auto">
                  <table className="print-table w-full min-w-[700px]">
                    <thead>
                      <tr className="border-b bg-background">
                        <th className="px-5 py-4 text-left text-sm font-semibold">
                          Item
                        </th>
                        <th className="px-5 py-4 text-left text-sm font-semibold">
                          Description
                        </th>
                        <th className="px-5 py-4 text-left text-sm font-semibold">
                          Qty
                        </th>
                        <th className="px-5 py-4 text-left text-sm font-semibold">
                          Unit Price
                        </th>
                        <th className="px-5 py-4 text-left text-sm font-semibold">
                          Total
                        </th>
                      </tr>
                    </thead>

                    <tbody>
                      <tr className="border-b">
                        <td className="px-5 py-4 font-medium">
                          Subscription Plan
                        </td>
                        <td className="px-5 py-4 text-muted-foreground">
                          {invoice.plan_name || "Platform Subscription"}
                        </td>
                        <td className="px-5 py-4">1</td>
                        <td className="px-5 py-4">{formatMoney(subtotal)}</td>
                        <td className="px-5 py-4 font-semibold">
                          {formatMoney(subtotal)}
                        </td>
                      </tr>

                      {discount > 0 && (
                        <tr className="border-b">
                          <td className="px-5 py-4 font-medium">
                            Discount
                          </td>
                          <td className="px-5 py-4 text-muted-foreground">
                            Promotional or manual discount
                          </td>
                          <td className="px-5 py-4">1</td>
                          <td className="px-5 py-4">
                            -{formatMoney(discount)}
                          </td>
                          <td className="px-5 py-4 font-semibold">
                            -{formatMoney(discount)}
                          </td>
                        </tr>
                      )}

                      <tr>
                        <td className="px-5 py-4 font-medium">
                          VAT
                        </td>
                        <td className="px-5 py-4 text-muted-foreground">
                          Value Added Tax
                        </td>
                        <td className="px-5 py-4">1</td>
                        <td className="px-5 py-4">{formatMoney(vat)}</td>
                        <td className="px-5 py-4 font-semibold">
                          {formatMoney(vat)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="print-total-grid grid gap-4 md:grid-cols-[1fr_180px] md:items-stretch md:justify-end">
                <div className="print-total-card w-full rounded-2xl border bg-muted/20 p-5">
                  <div className="space-y-4">
                    <div className="print-total-row flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Subtotal</span>
                      <span className="font-medium">{formatMoney(subtotal)}</span>
                    </div>

                    <div className="print-total-row flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Discount</span>
                      <span className="font-medium">{formatMoney(discount)}</span>
                    </div>

                    <div className="print-total-row flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">VAT</span>
                      <span className="font-medium">{formatMoney(vat)}</span>
                    </div>

                    <div className="border-t pt-4">
                      <div className="print-total-final flex items-center justify-between text-lg font-bold">
                        <span>Total Due</span>
                        <span>{formatMoney(total)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="print-qr-inline flex flex-col items-center justify-center rounded-2xl border bg-white p-4">
                  <div className="mb-2 flex items-center gap-2 text-sm font-medium text-muted-foreground no-print">
                    <QrCode className="h-4 w-4" />
                    QR
                  </div>

                  <img
                    src={qrImageUrl}
                    alt="Invoice QR Code"
                    className="h-[140px] w-[140px] object-contain"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-6 xl:col-span-4 no-print">
            {invoice.status === "PAID" ? (
              <Card className="print-card border-green-200 bg-green-50/60">
                <CardContent className="space-y-4 p-6 text-center">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-green-100">
                    <CheckCircle2 className="h-7 w-7 text-green-600" />
                  </div>

                  <div className="text-2xl font-bold text-green-700">
                    Payment completed
                  </div>

                  <div className="space-y-2 text-sm text-muted-foreground">
                    <div>
                      Payment Method:{" "}
                      <span className="font-medium text-foreground">
                        {invoice.payment_method || "-"}
                      </span>
                    </div>

                    <div>
                      Paid At:{" "}
                      <span className="font-medium text-foreground">
                        {formatDate(invoice.paid_at)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <>
                <Card className="print-card">
                  <CardHeader>
                    <CardTitle>Select Payment Method</CardTitle>
                  </CardHeader>

                  <CardContent className="space-y-3">
                    <div
                      onClick={() => setMethod("CASH")}
                      className={`flex cursor-pointer items-center justify-between rounded-2xl border p-4 transition ${
                        method === "CASH"
                          ? "border-primary bg-primary/5"
                          : "hover:bg-muted/40"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Banknote className="h-5 w-5" />
                        <span className="font-medium">Cash</span>
                      </div>

                      {method === "CASH" && (
                        <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                      )}
                    </div>

                    <div
                      onClick={() => setMethod("BANK_TRANSFER")}
                      className={`flex cursor-pointer items-center justify-between rounded-2xl border p-4 transition ${
                        method === "BANK_TRANSFER"
                          ? "border-primary bg-primary/5"
                          : "hover:bg-muted/40"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Wallet className="h-5 w-5" />
                        <span className="font-medium">Bank Transfer</span>
                      </div>

                      {method === "BANK_TRANSFER" && (
                        <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                      )}
                    </div>

                    <div
                      onClick={() => setMethod("CREDIT_CARD")}
                      className={`flex cursor-pointer items-center justify-between rounded-2xl border p-4 transition ${
                        method === "CREDIT_CARD"
                          ? "border-primary bg-primary/5"
                          : "hover:bg-muted/40"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <CreditCard className="h-5 w-5" />
                        <span className="font-medium">Credit Card</span>
                      </div>

                      {method === "CREDIT_CARD" && (
                        <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card className="print-card">
                  <CardContent className="space-y-4 p-6">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <ShieldCheck className="h-4 w-4" />
                      Selected Method: {getMethodLabel(method)}
                    </div>

                    <Button
                      onClick={pay}
                      className="w-full"
                      disabled={paying}
                    >
                      {paying ? "Processing..." : `Pay ${formatMoney(total)}`}
                    </Button>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  )
}