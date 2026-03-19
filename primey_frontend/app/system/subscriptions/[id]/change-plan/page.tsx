"use client"

import { useEffect, useMemo, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import {
  ArrowLeft,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Sparkles,
  Wallet,
  CalendarDays,
  BadgeCheck,
} from "lucide-react"
import { toast } from "sonner"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Plan {
  id: number
  name: string
  price_monthly: number | null
  price_yearly: number | null
  is_active?: boolean
}

interface Subscription {
  id: number
  plan_name: string
  price: number
  billing_cycle: string
  end_date: string
}

interface Preview {
  type: string
  amount_due: number
  message: string
  current_plan?: {
    id: number
    name: string
    price: number
  }
  new_plan?: {
    id: number
    name: string
    price: number
  }
}

export default function ChangePlanPage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id

  const [plans, setPlans] = useState<Plan[]>([])
  const [subscription, setSubscription] = useState<Subscription | null>(null)

  const [selectedPlan, setSelectedPlan] = useState<number | null>(null)
  const [preview, setPreview] = useState<Preview | null>(null)

  const [loading, setLoading] = useState(true)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [confirmLoading, setConfirmLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  function getCookie(name: string) {
    if (typeof document === "undefined") return null

    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)

    if (parts.length === 2) {
      return parts.pop()?.split(";").shift() || null
    }

    return null
  }

  function formatMoney(value: number | null | undefined) {
    return Number(value || 0).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  }

  function formatDate(value: string | null | undefined) {
    if (!value) return "-"
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return "-"
    return date.toLocaleDateString("en-CA")
  }

  function normalizeCycle(cycle: string | null | undefined) {
    const raw = String(cycle || "").toUpperCase()
    if (raw === "MONTHLY") return "شهري"
    if (raw === "YEARLY") return "سنوي"
    return cycle || "-"
  }

  function getRemainingTime(endDate: string) {
    const end = new Date(endDate).getTime()
    const now = new Date().getTime()
    const diff = end - now

    if (diff <= 0) return "منتهٍ"

    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days < 30) {
      return `${days} يوم متبقٍ`
    }

    const months = Math.floor(days / 30)
    return `${months} شهر متبقٍ`
  }

  async function fetchData(silent = false) {
    try {
      if (silent) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      const subRes = await fetch(
        `${API_BASE}/api/system/subscriptions/${id}/`,
        {
          credentials: "include",
          cache: "no-store",
        }
      )

      const subData = await subRes.json()

      if (!subRes.ok) {
        throw new Error(subData?.error || "تعذر تحميل بيانات الاشتراك")
      }

      setSubscription(subData.subscription || null)

      const planRes = await fetch(
        `${API_BASE}/api/system/plans/admin/`,
        {
          credentials: "include",
          cache: "no-store",
        }
      )

      const planData = await planRes.json()

      if (!planRes.ok) {
        throw new Error(planData?.error || "تعذر تحميل الباقات")
      }

      setPlans(planData.plans || [])
    } catch (err) {
      console.error("Fetch error:", err)
      toast.error(
        err instanceof Error ? err.message : "تعذر تحميل بيانات الصفحة"
      )
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    if (id) {
      void fetchData()
    }
  }, [id])

  async function previewChange(planId: number) {
    try {
      setPreviewLoading(true)

      const csrf = getCookie("csrftoken")

      const res = await fetch(
        `${API_BASE}/api/system/subscriptions/${id}/preview-plan-change/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf || "",
          },
          body: JSON.stringify({
            plan_id: planId,
          }),
        }
      )

      const data = await res.json()

      if (!res.ok) {
        toast.error(data.error || "تعذر معاينة تغيير الباقة")
        return
      }

      setPreview(data)
    } catch (err) {
      console.error("Preview error:", err)
      toast.error("تعذر معاينة تغيير الباقة")
    } finally {
      setPreviewLoading(false)
    }
  }

  async function confirmChange() {
    if (!selectedPlan) {
      toast.error("اختر باقة أولًا")
      return
    }

    try {
      setConfirmLoading(true)

      const csrf = getCookie("csrftoken")

      const res = await fetch(
        `${API_BASE}/api/system/subscriptions/${id}/change-plan/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf || "",
          },
          body: JSON.stringify({
            plan_id: selectedPlan,
          }),
        }
      )

      const data = await res.json()

      if (!res.ok) {
        toast.error(data.error || "تعذر تنفيذ تغيير الباقة")
        return
      }

      if (data.action === "upgrade") {
        toast.success("تم إنشاء فاتورة الترقية بنجاح")
        window.location.href = `/system/invoices/${data.invoice_number}`
        return
      }

      toast.success("تم جدولة تغيير الباقة بنجاح")
      window.location.href = `/system/subscriptions/${id}`
    } catch (err) {
      console.error("Change error:", err)
      toast.error("تعذر تنفيذ تغيير الباقة")
    } finally {
      setConfirmLoading(false)
    }
  }

  const availablePlans = useMemo(() => {
    return plans.filter(
      (plan) =>
        plan.name !== subscription?.plan_name &&
        plan.is_active !== false
    )
  }, [plans, subscription])

  if (loading) {
    return (
      <div className="space-y-6 p-6" dir="rtl">
        <Card className="rounded-3xl border-border/60 shadow-sm">
          <CardContent className="flex min-h-[360px] items-center justify-center">
            <div className="flex items-center gap-3 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>جاري تحميل صفحة تغيير الباقة...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="h-10 w-10 rounded-full"
              onClick={() => router.back()}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>

            <h1 className="text-2xl font-bold tracking-tight">
              تغيير الباقة
            </h1>

            <Badge variant="outline" className="rounded-full">
              Subscription #{id}
            </Badge>
          </div>

          <p className="text-sm text-muted-foreground">
            اختر باقة جديدة ثم راجع فرق السعر قبل تنفيذ التغيير.
          </p>
        </div>

        <Button
          type="button"
          variant="outline"
          className="rounded-2xl"
          onClick={() => void fetchData(true)}
          disabled={refreshing}
        >
          {refreshing ? (
            <Loader2 className="ms-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="ms-2 h-4 w-4" />
          )}
          تحديث البيانات
        </Button>
      </div>

      {subscription && (
        <Card className="rounded-[28px] border-border/60 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BadgeCheck className="h-5 w-5" />
              الباقة الحالية
            </CardTitle>
            <CardDescription>
              تفاصيل الاشتراك الحالي قبل تنفيذ عملية التغيير.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
              <div className="rounded-2xl border border-border/60 bg-background p-4">
                <div className="mb-1 text-xs text-muted-foreground">
                  اسم الباقة
                </div>
                <div className="font-semibold">{subscription.plan_name}</div>
              </div>

              <div className="rounded-2xl border border-border/60 bg-background p-4">
                <div className="mb-1 text-xs text-muted-foreground">
                  السعر الحالي
                </div>
                <div className="font-semibold">
                  {formatMoney(subscription.price)} SAR
                </div>
              </div>

              <div className="rounded-2xl border border-border/60 bg-background p-4">
                <div className="mb-1 flex items-center gap-1 text-xs text-muted-foreground">
                  <Wallet className="h-3.5 w-3.5" />
                  دورة الفوترة
                </div>
                <div className="font-semibold">
                  {normalizeCycle(subscription.billing_cycle)}
                </div>
              </div>

              <div className="rounded-2xl border border-border/60 bg-background p-4">
                <div className="mb-1 flex items-center gap-1 text-xs text-muted-foreground">
                  <CalendarDays className="h-3.5 w-3.5" />
                  تاريخ الانتهاء
                </div>
                <div className="font-semibold">
                  {formatDate(subscription.end_date)}
                </div>
              </div>

              <div className="rounded-2xl border border-border/60 bg-background p-4">
                <div className="mb-1 text-xs text-muted-foreground">
                  المدة المتبقية
                </div>
                <div className="font-semibold">
                  {getRemainingTime(subscription.end_date)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="rounded-[28px] border-border/60 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            الباقات المتاحة
          </CardTitle>
          <CardDescription>
            اختر الباقة التي تريد الانتقال إليها لعرض المعاينة.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {availablePlans.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-border/70 p-10 text-center text-sm text-muted-foreground">
              لا توجد باقات أخرى متاحة للتغيير حاليًا.
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {availablePlans.map((plan) => {
                const monthlyPrice = Number(plan.price_monthly || 0)
                const yearlyPrice = Number(plan.price_yearly || 0)
                const isSelected = selectedPlan === plan.id

                return (
                  <Card
                    key={plan.id}
                    className={`cursor-pointer rounded-3xl border transition-all ${
                      isSelected
                        ? "border-primary shadow-md ring-1 ring-primary/20"
                        : "border-border/60 hover:border-primary/40 hover:shadow-sm"
                    }`}
                    onClick={() => {
                      setSelectedPlan(plan.id)
                      void previewChange(plan.id)
                    }}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <CardTitle className="text-lg">{plan.name}</CardTitle>
                          <CardDescription className="mt-1">
                            اختر هذه الباقة لعرض فرق السعر.
                          </CardDescription>
                        </div>

                        {isSelected ? (
                          <Badge className="rounded-full">
                            <CheckCircle2 className="ms-1 h-3.5 w-3.5" />
                            محددة
                          </Badge>
                        ) : null}
                      </div>
                    </CardHeader>

                    <CardContent className="space-y-3">
                      <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
                        <div className="mb-1 text-xs text-muted-foreground">
                          السعر الشهري
                        </div>
                        <div className="text-xl font-bold">
                          {formatMoney(monthlyPrice)} SAR
                        </div>
                      </div>

                      <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
                        <div className="mb-1 text-xs text-muted-foreground">
                          السعر السنوي
                        </div>
                        <div className="text-xl font-bold">
                          {formatMoney(yearlyPrice)} SAR
                        </div>
                      </div>

                      <Button
                        type="button"
                        variant={isSelected ? "default" : "outline"}
                        className="w-full rounded-2xl"
                        onClick={(event) => {
                          event.stopPropagation()
                          setSelectedPlan(plan.id)
                          void previewChange(plan.id)
                        }}
                        disabled={previewLoading}
                      >
                        {previewLoading && selectedPlan === plan.id ? (
                          <Loader2 className="ms-2 h-4 w-4 animate-spin" />
                        ) : (
                          <Sparkles className="ms-2 h-4 w-4" />
                        )}
                        معاينة التغيير
                      </Button>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {preview && (
        <Card className="rounded-[28px] border-border/60 shadow-sm">
          <CardHeader>
            <CardTitle>معاينة تغيير الباقة</CardTitle>
            <CardDescription>
              راجع تفاصيل الفرق قبل تأكيد العملية.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-border/60 bg-background p-4">
                <div className="mb-1 text-xs text-muted-foreground">
                  الباقة الحالية
                </div>
                <div className="font-semibold">
                  {preview.current_plan?.name || "-"}
                </div>
              </div>

              <div className="rounded-2xl border border-border/60 bg-background p-4">
                <div className="mb-1 text-xs text-muted-foreground">
                  الباقة الجديدة
                </div>
                <div className="font-semibold">
                  {preview.new_plan?.name || "-"}
                </div>
              </div>

              <div className="rounded-2xl border border-border/60 bg-background p-4">
                <div className="mb-1 text-xs text-muted-foreground">
                  الفرق المستحق
                </div>
                <div className="font-semibold">
                  {formatMoney(preview.amount_due)} SAR
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-border/60 bg-muted/20 p-4 text-sm text-muted-foreground">
              {preview.message}
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Button
                type="button"
                className="rounded-2xl"
                onClick={confirmChange}
                disabled={confirmLoading || !selectedPlan}
              >
                {confirmLoading ? (
                  <Loader2 className="ms-2 h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="ms-2 h-4 w-4" />
                )}
                تأكيد تغيير الباقة
              </Button>

              <Button
                type="button"
                variant="outline"
                className="rounded-2xl"
                onClick={() => {
                  setSelectedPlan(null)
                  setPreview(null)
                }}
              >
                إلغاء الاختيار
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}