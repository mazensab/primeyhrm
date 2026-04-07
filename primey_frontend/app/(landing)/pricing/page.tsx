"use client"

/* =========================================================
   📄 Mham Cloud — Landing Pricing Page
   المسار:
   C:\Users\mazen\primeyhrm\primey_frontend\app\(landing)\pricing\page.tsx
   ========================================================= */

import { useEffect, useMemo, useState } from "react"
import Image from "next/image"
import Link from "next/link"
import {
  Check,
  Loader2,
  AlertCircle,
  Sparkles,
  Users,
  Building2,
  LayoutGrid,
} from "lucide-react"

import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const API = process.env.NEXT_PUBLIC_API_URL

/* =========================================================
   🧩 Types
========================================================= */

type BillingMode = "monthly" | "yearly"

interface Plan {
  id: number
  name: string
  description: string
  price_monthly: number | null
  price_yearly: number | null
  max_companies: number | null
  max_employees: number | null
  is_active: boolean
  apps: string[]
}

interface PlansResponse {
  plans: Plan[]
}

/* =========================================================
   🔧 Helpers
========================================================= */

function normalizeApps(apps: unknown): string[] {
  if (!Array.isArray(apps)) return []

  return apps
    .map((item) => String(item).trim())
    .filter(Boolean)
}

function normalizeNumber(value: unknown): number {
  if (typeof value === "number" && !Number.isNaN(value)) {
    return value
  }

  const parsed = Number(value ?? 0)
  return Number.isNaN(parsed) ? 0 : parsed
}

function formatNumber(value: number | null | undefined): string {
  const safeValue = normalizeNumber(value)

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(safeValue)
}

function formatPrice(value: number | null | undefined): string {
  const safeValue = normalizeNumber(value)

  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(safeValue)
}

function prettifyAppName(app: string): string {
  return app
    .replace(/_/g, " ")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

/* =========================================================
   🎨 Page
========================================================= */

export default function LandingPricingPage() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [billingMode, setBillingMode] = useState<BillingMode>("monthly")

  /* -----------------------------------------------------
     📡 Fetch Active Plans From Real System
     ✅ Project standard:
     NEXT_PUBLIC_API_URL=http://localhost:8000
     Final endpoint:
     /api/system/plans/
  ----------------------------------------------------- */
  useEffect(() => {
    let isMounted = true

    async function fetchPlans() {
      try {
        setLoading(true)
        setError("")

        if (!API) {
          throw new Error("NEXT_PUBLIC_API_URL is not configured")
        }

        const res = await fetch(`${API}/api/system/plans/`, {
          method: "GET",
          headers: {
            Accept: "application/json",
          },
          cache: "no-store",
        })

        if (!res.ok) {
          throw new Error(`Failed to fetch plans: ${res.status}`)
        }

        const data: PlansResponse = await res.json()

        const normalizedPlans: Plan[] = Array.isArray(data?.plans)
          ? data.plans
              .filter((plan) => plan?.is_active !== false)
              .map((plan) => ({
                id: normalizeNumber(plan.id),
                name: String(plan.name || "Plan"),
                description: String(plan.description || ""),
                price_monthly: normalizeNumber(plan.price_monthly),
                price_yearly: normalizeNumber(plan.price_yearly),
                max_companies: normalizeNumber(plan.max_companies),
                max_employees: normalizeNumber(plan.max_employees),
                is_active: Boolean(plan.is_active),
                apps: normalizeApps(plan.apps),
              }))
          : []

        if (!isMounted) return

        setPlans(normalizedPlans)
      } catch (err) {
        console.error("Pricing plans fetch error:", err)

        if (!isMounted) return

        setError("تعذر تحميل الباقات الحالية من النظام")
        toast.error("تعذر تحميل الباقات الحالية")
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    fetchPlans()

    return () => {
      isMounted = false
    }
  }, [])

  /* -----------------------------------------------------
     ⭐ Sort Plans
  ----------------------------------------------------- */
  const sortedPlans = useMemo(() => {
    return [...plans].sort((a, b) => {
      const aPrice =
        billingMode === "monthly"
          ? normalizeNumber(a.price_monthly)
          : normalizeNumber(a.price_yearly)

      const bPrice =
        billingMode === "monthly"
          ? normalizeNumber(b.price_monthly)
          : normalizeNumber(b.price_yearly)

      return aPrice - bPrice
    })
  }, [plans, billingMode])

  const popularPlanId = useMemo(() => {
    if (sortedPlans.length === 0) return null
    if (sortedPlans.length < 3) {
      return sortedPlans[1]?.id ?? sortedPlans[0]?.id ?? null
    }

    return sortedPlans[Math.floor(sortedPlans.length / 2)]?.id ?? null
  }, [sortedPlans])

  return (
    <main className="relative min-h-screen bg-background">
      {/* خلفية ناعمة */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-0 h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute bottom-0 left-0 h-[280px] w-[280px] rounded-full bg-emerald-500/10 blur-3xl" />
        <div className="absolute right-0 top-1/3 h-[260px] w-[260px] rounded-full bg-sky-500/10 blur-3xl" />
      </div>

      <section className="relative container mx-auto px-4 py-16 md:px-6 md:py-24">
        {/* الهيدر */}
        <div className="mx-auto mb-12 max-w-3xl text-center">
          <Badge className="mb-4 rounded-full px-4 py-1.5 text-sm">
            Pricing Plans
          </Badge>

          <h1 className="text-4xl font-bold tracking-tight md:text-6xl">
            اختر الباقة المناسبة لأعمالك
          </h1>

          <p className="mt-4 text-base text-muted-foreground md:text-lg">
            جميع الباقات المعروضة هنا يتم جلبها مباشرة من النظام الفعلي،
            وتُعرض فقط الباقات النشطة الجاهزة للاشتراك.
          </p>
        </div>

        {/* تبديل الفوترة */}
        <div className="mb-10 flex justify-center">
          <div className="inline-flex rounded-2xl border bg-background/80 p-1 shadow-sm backdrop-blur">
            <button
              type="button"
              onClick={() => setBillingMode("monthly")}
              className={[
                "rounded-xl px-5 py-2.5 text-sm font-medium transition-all",
                billingMode === "monthly"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground",
              ].join(" ")}
            >
              Monthly
            </button>

            <button
              type="button"
              onClick={() => setBillingMode("yearly")}
              className={[
                "rounded-xl px-5 py-2.5 text-sm font-medium transition-all",
                billingMode === "yearly"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground",
              ].join(" ")}
            >
              Annually
            </button>
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex min-h-[280px] items-center justify-center">
            <div className="flex items-center gap-3 rounded-2xl border bg-background/80 px-6 py-4 shadow-sm backdrop-blur">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-sm font-medium">جاري تحميل الباقات...</span>
            </div>
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <Card className="mx-auto max-w-2xl rounded-3xl border-destructive/20">
            <CardContent className="flex flex-col items-center justify-center gap-3 py-12 text-center">
              <AlertCircle className="h-10 w-10 text-destructive" />
              <h2 className="text-xl font-semibold">تعذر تحميل الباقات</h2>
              <p className="text-muted-foreground">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Empty State */}
        {!loading && !error && sortedPlans.length === 0 && (
          <Card className="mx-auto max-w-2xl rounded-3xl">
            <CardContent className="flex flex-col items-center justify-center gap-3 py-12 text-center">
              <Sparkles className="h-10 w-10 text-primary" />
              <h2 className="text-xl font-semibold">لا توجد باقات نشطة حاليًا</h2>
              <p className="text-muted-foreground">
                عند تفعيل الباقات من لوحة النظام ستظهر هنا تلقائيًا.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Plans Grid */}
        {!loading && !error && sortedPlans.length > 0 && (
          <div className="grid gap-6 lg:grid-cols-3">
            {sortedPlans.map((plan) => {
              const isPopular = plan.id === popularPlanId
              const currentPrice =
                billingMode === "monthly"
                  ? plan.price_monthly
                  : plan.price_yearly

              const hasDiscount =
                normalizeNumber(plan.price_monthly) > 0 &&
                normalizeNumber(plan.price_yearly) > 0 &&
                normalizeNumber(plan.price_yearly) <
                  normalizeNumber(plan.price_monthly) * 12

              return (
                <Card
                  key={plan.id}
                  className={[
                    "relative overflow-hidden rounded-3xl border bg-background/80 shadow-sm backdrop-blur transition-all duration-300 hover:-translate-y-1 hover:shadow-xl",
                    isPopular
                      ? "border-primary shadow-lg ring-1 ring-primary/20"
                      : "",
                  ].join(" ")}
                >
                  {isPopular && (
                    <div className="absolute right-4 top-4">
                      <Badge className="rounded-full px-3 py-1">
                        Most Popular
                      </Badge>
                    </div>
                  )}

                  <CardHeader className="pb-4">
                    <CardTitle className="text-2xl font-bold">
                      {plan.name}
                    </CardTitle>

                    <CardDescription className="min-h-[48px] text-sm leading-6">
                      {plan.description || "Mham Cloud subscription plan"}
                    </CardDescription>

                    <div className="pt-4">
                      <div className="flex items-end gap-2">
                        <div className="flex items-center gap-2">
                          <Image
                            src="/currency/sar.svg"
                            alt="SAR"
                            width={26}
                            height={26}
                            className="h-6 w-6"
                          />
                          <span className="text-5xl font-bold tracking-tight">
                            {formatPrice(currentPrice)}
                          </span>
                        </div>

                        <span className="pb-1 text-base text-muted-foreground">
                          /{billingMode === "monthly" ? "month" : "year"}
                        </span>
                      </div>

                      {billingMode === "yearly" && hasDiscount && (
                        <p className="mt-2 text-sm font-medium text-emerald-600">
                          وفر أكثر عند الاشتراك السنوي
                        </p>
                      )}
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-6">
                    {/* Stats */}
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="rounded-2xl border bg-muted/40 p-4">
                        <div className="mb-2 flex items-center gap-2 text-muted-foreground">
                          <Building2 className="h-4 w-4" />
                          <span className="text-xs font-medium">
                            Max Companies
                          </span>
                        </div>
                        <p className="text-lg font-semibold">
                          {formatNumber(plan.max_companies)}
                        </p>
                      </div>

                      <div className="rounded-2xl border bg-muted/40 p-4">
                        <div className="mb-2 flex items-center gap-2 text-muted-foreground">
                          <Users className="h-4 w-4" />
                          <span className="text-xs font-medium">
                            Max Employees
                          </span>
                        </div>
                        <p className="text-lg font-semibold">
                          {formatNumber(plan.max_employees)}
                        </p>
                      </div>
                    </div>

                    {/* Apps */}
                    <div>
                      <div className="mb-3 flex items-center gap-2">
                        <LayoutGrid className="h-4 w-4 text-primary" />
                        <h3 className="text-sm font-semibold">
                          Included Apps
                        </h3>
                      </div>

                      <div className="space-y-3">
                        {plan.apps.length > 0 ? (
                          plan.apps.map((app, index) => (
                            <div
                              key={`${plan.id}-${app}-${index}`}
                              className="flex items-start gap-3"
                            >
                              <div className="mt-0.5 rounded-full bg-primary/10 p-1 text-primary">
                                <Check className="h-3.5 w-3.5" />
                              </div>
                              <span className="text-sm text-muted-foreground">
                                {prettifyAppName(app)}
                              </span>
                            </div>
                          ))
                        ) : (
                          <div className="text-sm text-muted-foreground">
                            No apps listed for this plan.
                          </div>
                        )}
                      </div>
                    </div>

                    {/* CTA */}
                    <div className="pt-2">
                      <Button
                        asChild
                        className="h-11 w-full rounded-2xl text-sm font-semibold"
                        variant={isPopular ? "default" : "outline"}
                      >
                        <Link href="/register">
                          Get Started
                        </Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </section>
    </main>
  )
}