"use client"

import { useEffect, useState } from "react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card"

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from "@/components/ui/dialog"

import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table"


// API URL
const API = "http://localhost:8000/api"


interface Discount {

  id: number
  code: string
  type: "percentage" | "fixed"
  value: number
  max_uses: number | null
  used_count: number
  end_date: string | null
  is_active: boolean
}


function getCookie(name: string) {

  if (typeof document === "undefined") return null

  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)

  if (parts.length === 2)
    return parts.pop()?.split(";").shift()

  return null
}


export default function SystemDiscountsPage() {

  const [discounts, setDiscounts] = useState<Discount[]>([])
  const [loading, setLoading] = useState(true)

  const [open, setOpen] = useState(false)

  const [form, setForm] = useState({
    code: "",
    type: "percentage",
    value: "",
    max_uses: "",
    expires_at: ""
  })


  async function fetchDiscounts() {

    try {

      const res = await fetch(`${API}/system/discounts/`, {
        credentials: "include"
      })

      if (!res.ok) throw new Error("failed")

      const data = await res.json()

      setDiscounts(data.results || [])

    } catch (err) {

      console.error(err)
      toast.error("Failed to load discounts")

    } finally {

      setLoading(false)

    }
  }


  useEffect(() => {
    fetchDiscounts()
  }, [])



  async function createDiscount() {

    if (!form.code || !form.value) {
      toast.error("Code and value required")
      return
    }

    try {

      const res = await fetch(`${API}/system/discounts/`, {

        method: "POST",

        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") || ""
        },

        credentials: "include",

        body: JSON.stringify({

          code: form.code,
          discount_type: form.type,
          value: Number(form.value),
          max_uses: form.max_uses ? Number(form.max_uses) : null,
          start_date: new Date().toISOString().split("T")[0],
          end_date: form.expires_at || null

        })

      })

      const data = await res.json()

      if (!res.ok) {
        toast.error(data.detail || "Failed")
        return
      }

      toast.success("Discount created")

      setOpen(false)

      setForm({
        code: "",
        type: "percentage",
        value: "",
        max_uses: "",
        expires_at: ""
      })

      fetchDiscounts()

    } catch (err) {

      console.error(err)
      toast.error("Something went wrong")

    }
  }



  async function toggleDiscount(id: number) {

    try {

      const res = await fetch(`${API}/system/discounts/${id}/toggle/`, {

        method: "PATCH",

        headers: {
          "X-CSRFToken": getCookie("csrftoken") || ""
        },

        credentials: "include"

      })

      if (!res.ok) {
        toast.error("Failed")
        return
      }

      fetchDiscounts()

    } catch (err) {

      console.error(err)
      toast.error("Failed to toggle")

    }
  }



  return (

    <div className="space-y-6">

      <Card>

        <CardHeader className="flex flex-row items-center justify-between">

          <CardTitle>Discount Codes</CardTitle>

          <Dialog open={open} onOpenChange={setOpen}>

            <DialogTrigger asChild>

              <Button>+ Create Discount</Button>

            </DialogTrigger>

            <DialogContent>

              <DialogHeader>

                <DialogTitle>Create Discount</DialogTitle>

              </DialogHeader>

              <div className="space-y-4">

                <Input
                  placeholder="Discount Code"
                  value={form.code}
                  onChange={(e) =>
                    setForm({ ...form, code: e.target.value })
                  }
                />

                <select
                  className="w-full border rounded-md p-2"
                  value={form.type}
                  onChange={(e) =>
                    setForm({ ...form, type: e.target.value })
                  }
                >

                  <option value="percentage">Percentage %</option>
                  <option value="fixed">Fixed Amount</option>

                </select>

                <Input
                  type="number"
                  placeholder="Value"
                  value={form.value}
                  onChange={(e) =>
                    setForm({ ...form, value: e.target.value })
                  }
                />

                <Input
                  type="number"
                  placeholder="Max Uses"
                  value={form.max_uses}
                  onChange={(e) =>
                    setForm({ ...form, max_uses: e.target.value })
                  }
                />

                <Input
                  type="date"
                  value={form.expires_at}
                  onChange={(e) =>
                    setForm({ ...form, expires_at: e.target.value })
                  }
                />

                <Button
                  className="w-full"
                  onClick={createDiscount}
                >
                  Save Discount
                </Button>

              </div>

            </DialogContent>

          </Dialog>

        </CardHeader>



        <CardContent>

          {loading ? (

            <div>Loading...</div>

          ) : (

            <Table>

              <TableHeader>

                <TableRow>

                  <TableHead>Code</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead>Usage</TableHead>
                  <TableHead>Expiry</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead></TableHead>

                </TableRow>

              </TableHeader>

              <TableBody>

                {discounts.map((d) => (

                  <TableRow key={d.id}>

                    <TableCell>{d.code}</TableCell>
                    <TableCell>{d.type}</TableCell>
                    <TableCell>{d.value}</TableCell>

                    <TableCell>
                      {d.used_count || 0} / {d.max_uses ?? "∞"}
                    </TableCell>

                    <TableCell>{d.end_date ?? "-"}</TableCell>

                    <TableCell>

                      {d.is_active
                        ? <Badge>Active</Badge>
                        : <Badge variant="destructive">Disabled</Badge>}

                    </TableCell>

                    <TableCell>

                      <Button
                        variant="outline"
                        onClick={() => toggleDiscount(d.id)}
                      >
                        Toggle
                      </Button>

                    </TableCell>

                  </TableRow>

                ))}

              </TableBody>

            </Table>

          )}

        </CardContent>

      </Card>

    </div>
  )
}