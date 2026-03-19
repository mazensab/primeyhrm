"use client"

import { useEffect, useState } from "react"
import Image from "next/image"

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
// System Apps
// ======================================================

const SYSTEM_APPS = [
  "employee",
  "attendance",
  "leave",
  "payroll",
  "performance",
  "biotime"
]

// ======================================================
// Types
// ======================================================

interface Plan {
  id: number
  name: string
  description?: string
  price_monthly: number | null
  price_yearly: number | null
  max_companies: number
  max_employees: number
  is_active: boolean
  apps: string[]
  companies_count?: number
}

// ======================================================
// Page
// ======================================================

export default function PlansPage() {

  const [plans, setPlans] = useState<Plan[]>([])
  const [loading, setLoading] = useState(true)

  const [openCreate, setOpenCreate] = useState(false)
  const [openEdit, setOpenEdit] = useState(false)

  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null)

  const emptyForm = {
    name: "",
    description: "",
    price_monthly: "",
    price_yearly: "",
    max_companies: "",
    max_employees: "",
    apps: [] as string[]
  }

  const [form, setForm] = useState(emptyForm)

  // ======================================================
  // Fetch Plans
  // ======================================================

  async function fetchPlans() {

    try {

      const res = await fetch(
        "http://localhost:8000/api/system/plans/admin/",
        { credentials: "include" }
      )

      const data = await res.json()

      const mapped = (data.plans || []).map((p: Plan) => ({
        ...p,
        companies_count: p.companies_count ?? 0
      }))

      setPlans(mapped)

    } catch (err) {

      console.error("Load plans failed", err)

    } finally {

      setLoading(false)

    }

  }

  useEffect(() => {
    fetchPlans()
  }, [])

  // ======================================================
  // Toggle Plan
  // ======================================================

async function togglePlan(plan: Plan) {

  try {

    const csrf = getCookie("csrftoken")

    await fetch(
      `http://localhost:8000/api/system/plans/${plan.id}/update/`,
      {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf || "",
        },
        body: JSON.stringify({
          is_active: !plan.is_active
        })
      }
    )

    fetchPlans()

  } catch (e) {
    console.error("Toggle failed", e)
  }
}

  // ======================================================
  // Toggle App
  // ======================================================

  function toggleApp(app: string) {

    let updated = [...form.apps]

    if (updated.includes(app)) {
      updated = updated.filter(a => a !== app)
    } else {
      updated.push(app)
    }

    setForm({ ...form, apps: updated })
  }

  // ======================================================
  // Create Plan
  // ======================================================

async function createPlan() {

  try {

    const csrf = getCookie("csrftoken")

    await fetch(
      "http://localhost:8000/api/system/plans/create/",
      {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf || "",
        },
        body: JSON.stringify({
          ...form,
          price_monthly: Number(form.price_monthly),
          price_yearly: Number(form.price_yearly),
          max_companies: Number(form.max_companies),
          max_employees: Number(form.max_employees),
          apps: form.apps
        })
      }
    )

    setOpenCreate(false)
    setForm(emptyForm)

    fetchPlans()

  } catch (err) {
    console.error("Create failed", err)
  }
}

// ======================================================
  // Update Plan
  // ======================================================

async function updatePlan() {

  if (!selectedPlan) return

  try {

    const csrf = getCookie("csrftoken")

    await fetch(
      `http://localhost:8000/api/system/plans/${selectedPlan.id}/update/`,
      {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf || "",
        },
        body: JSON.stringify({
          price_monthly: Number(form.price_monthly),
          price_yearly: Number(form.price_yearly),
          max_employees: Number(form.max_employees),
          is_active: selectedPlan.is_active
        })
      }
    )

    setOpenEdit(false)
    fetchPlans()

  } catch (err) {
    console.error("Update failed", err)
  }
}

  // ======================================================
  // UI
  // ======================================================

  if (loading) {
    return <div className="p-6">Loading plans...</div>
  }

  return (

    <div className="p-6 space-y-6">

      {/* Header */}

      <div className="flex items-center justify-between">

        <div>
          <h1 className="text-2xl font-bold">
            Subscription Plans
          </h1>

          <p className="text-muted-foreground">
            Manage system pricing plans
          </p>
        </div>

        {/* Create Modal */}

        <Dialog open={openCreate} onOpenChange={setOpenCreate}>

          <DialogTrigger asChild>
            <Button>Create Plan</Button>
          </DialogTrigger>

          <DialogContent>

            <DialogHeader>
              <DialogTitle>Create Plan</DialogTitle>
            </DialogHeader>

            <div className="space-y-3">

              <Input
                placeholder="Plan Name"
                value={form.name}
                onChange={(e)=>setForm({...form,name:e.target.value})}
              />

              <Input
                placeholder="Description"
                value={form.description}
                onChange={(e)=>setForm({...form,description:e.target.value})}
              />

              <Input
                type="number"
                placeholder="Monthly Price"
                value={form.price_monthly}
                onChange={(e)=>setForm({...form,price_monthly:e.target.value})}
              />

              <Input
                type="number"
                placeholder="Yearly Price"
                value={form.price_yearly}
                onChange={(e)=>setForm({...form,price_yearly:e.target.value})}
              />

              <Input
                type="number"
                placeholder="Max Companies"
                value={form.max_companies}
                onChange={(e)=>setForm({...form,max_companies:e.target.value})}
              />

              <Input
                type="number"
                placeholder="Max Employees"
                value={form.max_employees}
                onChange={(e)=>setForm({...form,max_employees:e.target.value})}
              />

              {/* Apps Selector */}

              <div className="space-y-2">

                <div className="text-sm font-medium">
                  Applications
                </div>

                {SYSTEM_APPS.map((app) => (

                  <label
                    key={app}
                    className="flex items-center gap-2 text-sm"
                  >

                    <input
                      type="checkbox"
                      checked={form.apps.includes(app)}
                      onChange={()=>toggleApp(app)}
                    />

                    {app}

                  </label>

                ))}

              </div>

              <Button onClick={createPlan}>
                Create
              </Button>

            </div>

          </DialogContent>

        </Dialog>

      </div>

      {/* Plans Grid */}

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">

        {plans.map((plan) => (

          <Card key={plan.id}>

            <CardHeader className="flex justify-between">

              <CardTitle>
                {plan.name}
              </CardTitle>

              {plan.is_active ? (
                <Badge>Active</Badge>
              ) : (
                <Badge variant="destructive">
                  Disabled
                </Badge>
              )}

            </CardHeader>

            <CardContent className="space-y-4">

              {/* Price */}

              <div className="flex items-center gap-2 text-2xl font-bold">

                <Image
                  src="/currency/sar.svg"
                  alt="SAR"
                  width={22}
                  height={22}
                />

                {plan.price_monthly ?? 0}

                <span className="text-sm text-muted-foreground">
                  / month
                </span>

              </div>

              {/* Description */}

              {plan.description && (
                <div className="text-sm text-muted-foreground">
                  {plan.description}
                </div>
              )}

              {/* Limits */}

              <div className="text-sm space-y-1">

                <div>
                  Companies limit:
                  <strong> {plan.max_companies}</strong>
                </div>

                <div>
                  Employees limit:
                  <strong> {plan.max_employees}</strong>
                </div>

                <div>
                  Companies using:
                  <strong> {plan.companies_count}</strong>
                </div>

              </div>

              {/* Apps */}

              <div className="flex flex-wrap gap-2">

                {plan.apps?.map((app, i) => (
                  <Badge key={i} variant="secondary">
                    {app}
                  </Badge>
                ))}

              </div>

              {/* Actions */}

              <div className="flex gap-2">

                <Button
                  variant="outline"
                  onClick={()=>togglePlan(plan)}
                >
                  {plan.is_active ? "Disable" : "Enable"}
                </Button>

                <Button
                  variant="secondary"
                  onClick={()=>{

                    setSelectedPlan(plan)

                    setForm({
                      name: plan.name,
                      description: plan.description || "",
                      price_monthly: String(plan.price_monthly ?? ""),
                      price_yearly: String(plan.price_yearly ?? ""),
                      max_companies: String(plan.max_companies),
                      max_employees: String(plan.max_employees),
                      apps: plan.apps
                    })

                    setOpenEdit(true)

                  }}
                >
                  Edit
                </Button>

              </div>

            </CardContent>

          </Card>

        ))}

      </div>

      {/* Edit Modal */}

      <Dialog open={openEdit} onOpenChange={setOpenEdit}>

        <DialogContent>

          <DialogHeader>
            <DialogTitle>Edit Plan</DialogTitle>
          </DialogHeader>

          <div className="space-y-3">

            <Input
              type="number"
              placeholder="Monthly Price"
              value={form.price_monthly}
              onChange={(e)=>setForm({...form,price_monthly:e.target.value})}
            />

            <Input
              type="number"
              placeholder="Yearly Price"
              value={form.price_yearly}
              onChange={(e)=>setForm({...form,price_yearly:e.target.value})}
            />

            <Input
              type="number"
              placeholder="Max Employees"
              value={form.max_employees}
              onChange={(e)=>setForm({...form,max_employees:e.target.value})}
            />

            <Button onClick={updatePlan}>
              Save Changes
            </Button>

          </div>

        </DialogContent>

      </Dialog>

    </div>

  )
}