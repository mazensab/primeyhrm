"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table"
import {
  Loader2,
  ShieldCheck,
  ShieldX,
  Clock3,
} from "lucide-react"

/* ======================================================
   API Helpers
====================================================== */

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, "")
}

function resolveApiBase() {
  const envApi = process.env.NEXT_PUBLIC_API_URL?.trim()

  if (envApi) {
    const value = trimTrailingSlash(envApi)
    return value.endsWith("/api") ? value : `${value}/api`
  }

  if (typeof window !== "undefined") {
    return `${trimTrailingSlash(window.location.origin)}/api`
  }

  return "/api"
}

/* ======================================================
   Types
====================================================== */

interface Subscription {
  id: number
  company_name: string
  company_id: number
  plan_name: string
  status: string
  start_date: string
  end_date: string
  price: number
  billing_cycle: string
  created_at: string
}

interface Renewal {
  id: number
  date: string
  plan: string
  amount: number
}

interface Invoice {
  id: number
  invoice: string
  amount: number
  status: string
  date: string
}

interface Payment {
  id: number
  amount: number
  method: string
  date: string
}

interface Usage {
  employees: number
  max_employees: number
  devices: number
  max_devices: number
}

/* ======================================================
   Helpers
====================================================== */

function normalizeStatus(status: string): string {
  return String(status || "").trim().toUpperCase()
}

function formatMoney(value: number | null | undefined) {
  const num = Number(value || 0)

  if (Number.isNaN(num)) {
    return "0.00 SAR"
  }

  return `${num.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    useGrouping: false,
  })} SAR`
}

function formatDate(value: string | null | undefined) {
  if (!value) return "-"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "-"

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")

  return `${year}/${month}/${day}`
}

function normalizeCycle(cycle: string | null | undefined) {
  const raw = String(cycle || "").toUpperCase()
  if (raw === "MONTHLY") return "شهري"
  if (raw === "YEARLY") return "سنوي"
  return cycle || "-"
}

function StatusBadge({ status }: { status: string }) {
  const normalized = normalizeStatus(status)

  const isActive = normalized === "ACTIVE"
  const isExpired = normalized === "EXPIRED"

  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
        isActive
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : isExpired
            ? "border-red-200 bg-red-50 text-red-700"
            : "border-amber-200 bg-amber-50 text-amber-700",
      ].join(" ")}
    >
      {isActive ? (
        <ShieldCheck className="me-1 h-3.5 w-3.5" />
      ) : isExpired ? (
        <ShieldX className="me-1 h-3.5 w-3.5" />
      ) : (
        <Clock3 className="me-1 h-3.5 w-3.5" />
      )}
      {status}
    </span>
  )
}

/* ======================================================
   Page
====================================================== */

export default function SubscriptionDetailsPage() {
  const API = useMemo(() => resolveApiBase(), [])
  const params = useParams()
  const id = Array.isArray(params?.id) ? params.id[0] : params?.id

  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [renewals, setRenewals] = useState<Renewal[]>([])
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [payments, setPayments] = useState<Payment[]>([])
  const [usage, setUsage] = useState<Usage | null>(null)

  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      if (!API || !id) {
        setLoading(false)
        return
      }

      try {
        const res = await fetch(
          `${API}/system/subscriptions/${id}/`,
          {
            credentials: "include",
            cache: "no-store",
          }
        )

        const data = await res.json()

        if (!res.ok) {
          toast.error(data?.error || "تعذر تحميل بيانات الاشتراك")
          setSubscription(null)
          return
        }

        setSubscription(data.subscription || null)
        setRenewals(data.renewals || [])
        setInvoices(data.invoices || [])
        setPayments(data.payments || [])
        setUsage(data.usage || null)
      } catch (err) {
        console.error("Subscription fetch error:", err)
        toast.error("تعذر تحميل بيانات الاشتراك")
        setSubscription(null)
      } finally {
        setLoading(false)
      }
    }

    void fetchData()
  }, [API, id])

  function getCookie(name: string) {
    if (typeof document === "undefined") return null

    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)

    if (parts.length === 2) {
      return parts.pop()?.split(";").shift()
    }

    return null
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 p-6 text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading subscription...
      </div>
    )
  }

  if (!subscription) {
    return <div className="p-6">Subscription not found</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">
          Subscription #{subscription.id}
        </h1>

        <StatusBadge status={subscription.status} />
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Company</CardTitle>
          </CardHeader>
          <CardContent>
            {subscription.company_name}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Plan</CardTitle>
          </CardHeader>
          <CardContent>
            {subscription.plan_name}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Billing Cycle</CardTitle>
          </CardHeader>
          <CardContent>
            {normalizeCycle(subscription.billing_cycle)}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Price</CardTitle>
          </CardHeader>
          <CardContent>
            {formatMoney(subscription.price)}
          </CardContent>
        </Card>
      </div>

      {usage && (
        <Card>
          <CardHeader>
            <CardTitle>Usage</CardTitle>
          </CardHeader>

          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              Employees
              <div className="text-xl font-bold">
                {usage.employees} / {usage.max_employees}
              </div>
            </div>

            <div>
              Devices
              <div className="text-xl font-bold">
                {usage.devices} / {usage.max_devices}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Renewal History</CardTitle>
        </CardHeader>

        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Plan</TableHead>
                <TableHead>Amount</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {renewals.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className="text-center text-muted-foreground">
                    No renewal history
                  </TableCell>
                </TableRow>
              ) : (
                renewals.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{formatDate(r.date)}</TableCell>
                    <TableCell>{r.plan}</TableCell>
                    <TableCell>{formatMoney(r.amount)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Invoices</CardTitle>
        </CardHeader>

        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {invoices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    No invoices found
                  </TableCell>
                </TableRow>
              ) : (
                invoices.map((i) => (
                  <TableRow key={i.id}>
                    <TableCell>
                      <Link
                        href={`/system/invoices/${i.invoice}`}
                        className="font-medium text-blue-600 hover:underline"
                      >
                        {i.invoice}
                      </Link>
                    </TableCell>
                    <TableCell>{formatDate(i.date)}</TableCell>
                    <TableCell>{formatMoney(i.amount)}</TableCell>
                    <TableCell>{i.status}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Payments</CardTitle>
        </CardHeader>

        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Method</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {payments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className="text-center text-muted-foreground">
                    No payments found
                  </TableCell>
                </TableRow>
              ) : (
                payments.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell>{formatDate(p.date)}</TableCell>
                    <TableCell>{formatMoney(p.amount)}</TableCell>
                    <TableCell>{p.method}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Subscription Actions</CardTitle>
        </CardHeader>

        <CardContent className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href={`/system/subscriptions/${id}/change-plan`}>
              Change Plan
            </Link>
          </Button>

          <Button
            onClick={async () => {
              try {
                const csrf = getCookie("csrftoken")

                const res = await fetch(
                  `${API}/system/subscriptions/${id}/renew/`,
                  {
                    method: "POST",
                    credentials: "include",
                    headers: {
                      "X-CSRFToken": csrf || "",
                    },
                  }
                )

                const data = await res.json()

                if (!res.ok) {
                  toast.error(data.error || "Renew failed")
                  return
                }

                toast.success("Renewal invoice created successfully")

                setTimeout(() => {
                  window.location.href = `/system/invoices/${data.invoice_number || data.invoice_id}`
                }, 800)
              } catch (err) {
                console.error("Renew error:", err)
                toast.error("Renew failed")
              }
            }}
          >
            Renew Subscription
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}