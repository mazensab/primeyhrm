"use client"

import { useEffect, useState } from "react"
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


// ======================================================
// Types
// ======================================================

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


// ======================================================
// Page
// ======================================================

export default function SubscriptionDetailsPage() {

  const params = useParams()
  const id = params?.id

  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [renewals, setRenewals] = useState<Renewal[]>([])
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [payments, setPayments] = useState<Payment[]>([])
  const [usage, setUsage] = useState<Usage | null>(null)

  const [loading, setLoading] = useState(true)


// ======================================================
// Fetch Data
// ======================================================

useEffect(() => {

  async function fetchData() {

    try {

      const res = await fetch(
        `http://localhost:8000/api/system/subscriptions/${id}/`,
        {
          credentials: "include",
        }
      )

      const data = await res.json()

      setSubscription(data.subscription)
      setRenewals(data.renewals || [])
      setInvoices(data.invoices || [])
      setPayments(data.payments || [])
      setUsage(data.usage || null)

    } catch (err) {

      console.error("Subscription fetch error:", err)

    } finally {

      setLoading(false)

    }
  }

  if (id) fetchData()

}, [id])

if (loading) return <div>Loading subscription...</div>
if (!subscription) return <div>Subscription not found</div>
 // ======================================================
 // CSRF
 // ======================================================

 function getCookie(name: string) {

   if (typeof document === "undefined") return null

   const value = `; ${document.cookie}`
   const parts = value.split(`; ${name}=`)

   if (parts.length === 2)
     return parts.pop()?.split(";").shift()

   return null
 }

  // ======================================================
  // UI
  // ======================================================

  return (

    <div className="space-y-6">

      {/* ================================================= */}
      {/* Header */}
      {/* ================================================= */}

      <div className="flex items-center justify-between">

        <h1 className="text-2xl font-bold">
          Subscription #{subscription.id}
        </h1>

        <Badge
          variant={
            subscription.status === "ACTIVE"
              ? "default"
              : subscription.status === "EXPIRED"
              ? "destructive"
              : "secondary"
          }
        >
          {subscription.status}
        </Badge>

      </div>


      {/* ================================================= */}
      {/* Overview */}
      {/* ================================================= */}

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
            {subscription.billing_cycle}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Price</CardTitle>
          </CardHeader>
          <CardContent>
            {subscription.price} SAR
          </CardContent>
        </Card>

      </div>


      {/* ================================================= */}
      {/* Usage */}
      {/* ================================================= */}

      {usage && (

        <Card>

          <CardHeader>
            <CardTitle>Usage</CardTitle>
          </CardHeader>

          <CardContent className="grid md:grid-cols-2 gap-4">

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


      {/* ================================================= */}
      {/* Renewal History */}
      {/* ================================================= */}

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

              {renewals.map((r) => (

                <TableRow key={r.id}>
                  <TableCell>{r.date}</TableCell>
                  <TableCell>{r.plan}</TableCell>
                  <TableCell>{r.amount} SAR</TableCell>
                </TableRow>

              ))}

            </TableBody>

          </Table>

        </CardContent>

      </Card>


      {/* ================================================= */}
      {/* Invoices */}
      {/* ================================================= */}

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

              {invoices.map((i) => (

                <TableRow key={i.id}>
                  <TableCell>
                    <a
                      href={`/system/invoices/${i.id}`}
                      className="text-blue-600 hover:underline font-medium"
                    >
                      {i.invoice}
                    </a>
                  </TableCell>
                  <TableCell>{i.date}</TableCell>
                  <TableCell>{i.amount} SAR</TableCell>
                  <TableCell>{i.status}</TableCell>
                </TableRow>

              ))}

            </TableBody>

          </Table>

        </CardContent>

      </Card>


      {/* ================================================= */}
      {/* Payments */}
      {/* ================================================= */}

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

              {payments.map((p) => (

                <TableRow key={p.id}>
                  <TableCell>{p.date}</TableCell>
                  <TableCell>{p.amount} SAR</TableCell>
                  <TableCell>{p.method}</TableCell>
                </TableRow>

              ))}

            </TableBody>

          </Table>

        </CardContent>

      </Card>


      {/* ================================================= */}
      {/* Actions */}
      {/* ================================================= */}

      <Card>

        <CardHeader>
          <CardTitle>Subscription Actions</CardTitle>
        </CardHeader>

        <CardContent className="flex gap-3 flex-wrap">

          <Button
            variant="outline"
            onClick={() => {
              window.location.href = `/system/subscriptions/${id}/change-plan`
            }}
          >
            Change Plan
          </Button>
          <Button
            onClick={async () => {

              try {

                const csrf = getCookie("csrftoken")

                const res = await fetch(
                  `http://localhost:8000/api/system/subscriptions/${id}/renew/`,
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
                  window.location.href = `/system/invoices/${data.invoice_id}`
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