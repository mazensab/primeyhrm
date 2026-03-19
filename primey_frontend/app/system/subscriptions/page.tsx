"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card"

import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

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
  plan_name: string
  status: string
  start_date: string
  end_date: string
  price: number
}


// ======================================================
// Page
// ======================================================

export default function SystemSubscriptionsPage() {

  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [filter, setFilter] = useState<
  "all" | "active" | "expired" | "exp7" | "exp30"
>("all")

  // ======================================================
  // Fetch Subscriptions
  // ======================================================

  useEffect(() => {

    async function fetchSubscriptions() {

      try {

        const res = await fetch("http://localhost:8000/api/system/subscriptions/", {
          credentials: "include",
        })

        const data = await res.json()

        setSubscriptions(data?.subscriptions ?? [])

      } catch (err) {

        console.error("Subscriptions fetch error:", err)

      } finally {

        setLoading(false)

      }
    }

    fetchSubscriptions()

  }, [])


  // ======================================================
  // Filters
  // ======================================================

  const filtered = subscriptions.filter((sub) => {

    if (!sub.company_name.toLowerCase().includes(search.toLowerCase()))
      return false

    const end = new Date(sub.end_date)
    const now = new Date()

    const diffDays =
      (end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)

    if (filter === "active") return sub.status === "ACTIVE"

    if (filter === "expired") return sub.status === "EXPIRED"

    if (filter === "exp7")
      return diffDays <= 7 && diffDays >= 0

    if (filter === "exp30")
      return diffDays <= 30 && diffDays >= 0

    return true
  })

  // ======================================================
  // Stats
  // ======================================================

  const total = subscriptions.length

  const active = subscriptions.filter(
    (s) => s.status === "ACTIVE"
  ).length

  const expired = subscriptions.filter(
    (s) => s.status === "EXPIRED"
  ).length

const expiring = subscriptions.filter((s) => {

  const end = new Date(s.end_date)
  const now = new Date()

  const diffDays =
    (end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)

  return diffDays <= 7 && diffDays >= 0

}).length

  // ======================================================
  // UI
  // ======================================================

  return (

    <div className="space-y-6">

      {/* ===================================== */}
      {/* Page Header */}
      {/* ===================================== */}

      <div className="flex items-center justify-between">

        <h1 className="text-2xl font-bold">
          Subscriptions
        </h1>

      </div>


      {/* ===================================== */}
      {/* Stats */}
      {/* ===================================== */}

      <div className="grid gap-4 md:grid-cols-4">

        <Card>
          <CardHeader>
            <CardTitle>Total</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-bold">
            {total}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-bold text-green-600">
            {active}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Expiring</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-bold text-yellow-600">
            {expiring}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Expired</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-bold text-red-600">
            {expired}
          </CardContent>
        </Card>

      </div>


      {/* ===================================== */}
      {/* Filters */}
      {/* ===================================== */}

      <div className="flex gap-3 items-center flex-wrap">

        <Input
          placeholder="Search company..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <Button
          size="sm"
          variant={filter === "all" ? "default" : "outline"}
          onClick={() => setFilter("all")}
        >
          All
        </Button>

        <Button
          size="sm"
          variant={filter === "active" ? "default" : "outline"}
          onClick={() => setFilter("active")}
         >
          Active
        </Button>

        <Button
          size="sm"
          variant={filter === "exp7" ? "default" : "outline"}
          onClick={() => setFilter("exp7")}
        >
          7 Days
        </Button>

        <Button
          size="sm"
          variant={filter === "exp30" ? "default" : "outline"}
          onClick={() => setFilter("exp30")}
        >
          30 Days
        </Button>

        <Button
          size="sm"
          variant={filter === "expired" ? "default" : "outline"}
          onClick={() => setFilter("expired")}
        >
          Expired
        </Button>

      </div>


      {/* ===================================== */}
      {/* Table */}
      {/* ===================================== */}

      <Card>

        <CardHeader>
          <CardTitle>Subscriptions</CardTitle>
        </CardHeader>

        <CardContent>

          <Table>

            <TableHeader>

              <TableRow>
                <TableHead>Company</TableHead>
                <TableHead>Plan</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Start</TableHead>
                <TableHead>End</TableHead>
                <TableHead>Price</TableHead>
                <TableHead></TableHead>
              </TableRow>

            </TableHeader>

            <TableBody>

              {loading && (

                <TableRow>
                  <TableCell colSpan={7}>
                    Loading...
                  </TableCell>
                </TableRow>

              )}

              {!loading && filtered.length === 0 && (

                <TableRow>
                  <TableCell colSpan={7}>
                    No subscriptions found
                  </TableCell>
                </TableRow>

              )}

              {filtered.map((sub) => (

                <TableRow key={sub.id}>

                  <TableCell className="font-medium">
                    {sub.company_name}
                  </TableCell>

                  <TableCell>
                    {sub.plan_name}
                  </TableCell>

                  <TableCell>

                    <Badge
                      variant={
                        sub.status === "ACTIVE"
                          ? "default"
                          : sub.status === "EXPIRED"
                          ? "destructive"
                          : "secondary"
                      }
                    >
                      {sub.status}
                    </Badge>

                  </TableCell>

                  <TableCell>
                    {sub.start_date}
                  </TableCell>

                  <TableCell>
                    {sub.end_date}
                  </TableCell>

                  <TableCell>
                    {sub.price} SAR
                  </TableCell>

                  <TableCell>

                    <Button
                      asChild
                      size="sm"
                      variant="outline"
                    >
                      <Link href={`/system/subscriptions/${sub.id}`}>
                        View
                      </Link>
                    </Button>

                  </TableCell>
                </TableRow>

              ))}

            </TableBody>

          </Table>

        </CardContent>

      </Card>

    </div>
  )
}