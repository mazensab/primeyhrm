"use client"

import Image from "next/image"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  ArrowLeft,
  BadgeCheck,
  Clock3,
  CreditCard,
  FileText,
  Loader2,
  Receipt,
  RefreshCw,
  Wallet,
  Building2,
  CircleDollarSign,
  ShieldCheck,
  Repeat,
  Sparkles,
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
import { Separator } from "@/components/ui/separator"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type WhoAmIResponse = {
  authenticated?: boolean
  company_id?: number | null
  active_company_id?: number | null
  company?: {
    id?: number | null
    name?: string | null
  } | null
}

type CompanyDetailResponse = {
  company?: {
    id: number
    name: string
    email?: string | null
    phone?: string | null
    is_active?: boolean
    created_at?: string | null
  }
  owner?: {
    email?: string | null
  }
  subscription?: {
    plan?: string | null
    status?: string | null
  }
  users_count?: number
}

type SubscriptionPayload = {
  id?: number
  plan?: string | null
  status?: string | null
  billing_cycle?: string | null
  started_at?: string | null
  ends_at?: string | null
}

type SubscriptionResponse = {
  status?: string
  subscription?: SubscriptionPayload | null
}

type SubscriptionListItem = {
  id: number
  company_name?: string | null
  plan_name?: string | null
  status?: string | null
  start_date?: string | null
  end_date?: string | null
  price?: number | string | null
}

type SubscriptionsListResponse = {
  subscriptions?: SubscriptionListItem[]
}

type InvoiceItem = {
  id: number
  number?: string | null
  invoice_number?: string | null
  total_amount?: string | number | null
  currency?: string | null
  status?: string | null
  issue_date?: string | null
  due_date?: string | null
  payment_method?: string | null
}

type InvoicesResponse = {
  status?: string
  data?: {
    results?: InvoiceItem[]
    count?: number
  }
}

type PaymentItem = {
  id: number
  amount?: number | string | null
  status?: string | null
  method?: string | null
  payment_method?: string | null
  paid_at?: string | null
  processed_at?: string | null
  reference?: string | null
  reference_number?: string | null
  invoice_id?: number | null
  invoice_number?: string | null
  company_name?: string | null
}

type PaymentsResponse =
  | {
      success?: boolean
      results?: PaymentItem[]
    }
  | PaymentItem[]

type RenewResponse = {
  success?: boolean
  error?: string
  invoice_id?: number
  invoice_number?: string
}

function getCookie(name: string) {
  if (typeof document === "undefined") return null

  const match = document.cookie.match(
    new RegExp(`(^|;\\s*)${name}=([^;]+)`)
  )

  return match ? decodeURIComponent(match[2]) : null
}

function formatMoney(value: number | string | null | undefined) {
  const amount = Number(value || 0)
  return amount.toLocaleString("en-US", {
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

function normalizeStatus(status: string | null | undefined) {
  const raw = String(status || "").toUpperCase()

  if (raw === "ACTIVE") {
    return {
      label: "نشط",
      className:
        "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800/60 dark:bg-emerald-950/40 dark:text-emerald-300",
    }
  }

  if (raw === "TRIAL") {
    return {
      label: "تجريبي",
      className:
        "border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-800/60 dark:bg-sky-950/40 dark:text-sky-300",
    }
  }

  if (raw === "PAID") {
    return {
      label: "مدفوعة",
      className:
        "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800/60 dark:bg-emerald-950/40 dark:text-emerald-300",
    }
  }

  if (raw === "PENDING") {
    return {
      label: "معلقة",
      className:
        "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800/60 dark:bg-amber-950/40 dark:text-amber-300",
    }
  }

  if (raw === "EXPIRED") {
    return {
      label: "منتهية",
      className:
        "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-800/60 dark:bg-rose-950/40 dark:text-rose-300",
    }
  }

  if (raw === "FAILED") {
    return {
      label: "فشلت",
      className:
        "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-800/60 dark:bg-rose-950/40 dark:text-rose-300",
    }
  }

  if (raw === "COMPLETED" || raw === "SUCCESS") {
    return {
      label: "ناجحة",
      className:
        "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800/60 dark:bg-emerald-950/40 dark:text-emerald-300",
    }
  }

  return {
    label: status || "-",
    className:
      "border-zinc-200 bg-zinc-50 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900/50 dark:text-zinc-300",
  }
}

function normalizeCycle(cycle: string | null | undefined) {
  const raw = String(cycle || "").toUpperCase()

  if (raw === "MONTHLY") return "شهري"
  if (raw === "YEARLY") return "سنوي"
  return cycle || "-"
}

function normalizeMethod(method: string | null | undefined) {
  const raw = String(method || "").toUpperCase()

  if (raw === "CASH") return "نقدي"
  if (raw === "BANK") return "تحويل بنكي"
  if (raw === "CARD") return "بطاقة"
  if (raw === "ONLINE") return "دفع إلكتروني"
  if (raw === "APPLE_PAY") return "Apple Pay"
  if (raw === "MADA") return "مدى"

  return method || "-"
}

export default function CompanyBillingPage() {
  const router = useRouter()

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [renewing, setRenewing] = useState(false)
  const [redirectingPlanChange, setRedirectingPlanChange] = useState(false)

  const [companyId, setCompanyId] = useState<number | null>(null)
  const [companyName, setCompanyName] = useState<string>("")
  const [companyEmail, setCompanyEmail] = useState<string>("")
  const [subscription, setSubscription] = useState<SubscriptionPayload | null>(null)
  const [subscriptions, setSubscriptions] = useState<SubscriptionListItem[]>([])
  const [invoices, setInvoices] = useState<InvoiceItem[]>([])
  const [payments, setPayments] = useState<PaymentItem[]>([])

  const loadData = useCallback(async (silent = false) => {
    try {
      if (silent) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      const whoamiRes = await fetch(`${API_BASE}/api/auth/whoami/`, {
        credentials: "include",
        cache: "no-store",
      })

      if (!whoamiRes.ok) {
        throw new Error("Failed to load session")
      }

      const whoami: WhoAmIResponse = await whoamiRes.json()

      const activeCompanyId =
        whoami.active_company_id ||
        whoami.company_id ||
        whoami.company?.id ||
        null

      if (!activeCompanyId) {
        throw new Error("No active company found")
      }

      setCompanyId(activeCompanyId)

      const [
        companyRes,
        subscriptionRes,
        subscriptionsRes,
        invoicesRes,
        paymentsRes,
      ] = await Promise.all([
        fetch(`${API_BASE}/api/system/companies/${activeCompanyId}/`, {
          credentials: "include",
          cache: "no-store",
        }),
        fetch(`${API_BASE}/api/system/companies/${activeCompanyId}/subscription/`, {
          credentials: "include",
          cache: "no-store",
        }),
        fetch(`${API_BASE}/api/system/subscriptions/`, {
          credentials: "include",
          cache: "no-store",
        }),
        fetch(`${API_BASE}/api/system/companies/${activeCompanyId}/invoices/`, {
          credentials: "include",
          cache: "no-store",
        }),
        fetch(`${API_BASE}/api/system/payments/latest/?company_id=${activeCompanyId}`, {
          credentials: "include",
          cache: "no-store",
        }),
      ])

      if (!companyRes.ok) {
        throw new Error("Failed to load company details")
      }

      const companyJson: CompanyDetailResponse = await companyRes.json()
      const subscriptionJson: SubscriptionResponse = subscriptionRes.ok
        ? await subscriptionRes.json()
        : { subscription: null }

      const subscriptionsJson: SubscriptionsListResponse = subscriptionsRes.ok
        ? await subscriptionsRes.json()
        : { subscriptions: [] }

      const invoicesJson: InvoicesResponse = invoicesRes.ok
        ? await invoicesRes.json()
        : { data: { results: [] } }

      const paymentsJson: PaymentsResponse = paymentsRes.ok
        ? await paymentsRes.json()
        : { results: [] }

      const resolvedCompanyName =
        companyJson.company?.name ||
        whoami.company?.name ||
        "شركتي"

      setCompanyName(resolvedCompanyName)
      setCompanyEmail(
        companyJson.company?.email ||
          companyJson.owner?.email ||
          ""
      )

      setSubscription(subscriptionJson.subscription || null)

      const filteredSubscriptions = (subscriptionsJson.subscriptions || []).filter(
        (item) => (item.company_name || "").trim() === resolvedCompanyName.trim()
      )

      setSubscriptions(filteredSubscriptions)
      setInvoices(invoicesJson.data?.results || [])

      if (Array.isArray(paymentsJson)) {
        setPayments(paymentsJson)
      } else {
        setPayments(paymentsJson.results || [])
      }
    } catch (error) {
      console.error("Billing page load error:", error)
      toast.error("تعذر تحميل بيانات الفوترة")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const handleRenewSubscription = async () => {
    if (!subscription?.id) {
      toast.error("لم يتم العثور على الاشتراك الحالي")
      return
    }

    try {
      setRenewing(true)

      const csrfToken = getCookie("csrftoken")
      const form = new URLSearchParams()

      form.append("action", "RENEWAL")
      form.append(
        "duration",
        String(subscription.billing_cycle || "").toUpperCase() === "YEARLY"
          ? "yearly"
          : "monthly"
      )

      const res = await fetch(
        `${API_BASE}/api/system/subscriptions/${subscription.id}/renew/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
          },
          body: form.toString(),
        }
      )

      const data: RenewResponse = await res.json()

      if (!res.ok) {
        throw new Error(data?.error || "تعذر إنشاء فاتورة التجديد")
      }

      toast.success("تم إنشاء فاتورة تجديد الاشتراك بنجاح")

      await loadData(true)

      if (data.invoice_number) {
        router.push(`/company/invoices/${data.invoice_number}`)
        return
      }

      if (data.invoice_id) {
        router.push("/company/billing")
      }
    } catch (error) {
      console.error("Renew subscription error:", error)
      toast.error(
        error instanceof Error ? error.message : "تعذر تنفيذ تجديد الاشتراك"
      )
    } finally {
      setRenewing(false)
    }
  }

  const handleChangePlan = () => {
    if (!subscription?.id) {
      toast.error("لم يتم العثور على الاشتراك الحالي")
      return
    }

    try {
      setRedirectingPlanChange(true)
      router.push(`/system/subscriptions/${subscription.id}/change-plan`)
    } catch (error) {
      console.error("Redirect to change-plan page error:", error)
      toast.error("تعذر فتح صفحة تغيير الباقة")
      setRedirectingPlanChange(false)
    }
  }

  const summary = useMemo(() => {
    const invoicesTotal = invoices.reduce((sum, item) => {
      return sum + Number(item.total_amount || 0)
    }, 0)

    const paymentsTotal = payments.reduce((sum, item) => {
      return sum + Number(item.amount || 0)
    }, 0)

    const paidInvoices = invoices.filter(
      (item) => String(item.status || "").toUpperCase() === "PAID"
    ).length

    const pendingInvoices = invoices.filter(
      (item) => String(item.status || "").toUpperCase() === "PENDING"
    ).length

    return {
      invoicesTotal,
      paymentsTotal,
      paidInvoices,
      pendingInvoices,
    }
  }, [invoices, payments])

  if (loading) {
    return (
      <div className="space-y-6 p-6" dir="rtl">
        <Card className="rounded-3xl border-border/60 shadow-sm">
          <CardContent className="flex min-h-[420px] items-center justify-center">
            <div className="flex items-center gap-3 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>جاري تحميل صفحة الفوترة...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const subStatus = normalizeStatus(subscription?.status)
  const latestInvoice = invoices[0]
  const latestPayment = payments[0]

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-start gap-3">
          <Button
            asChild
            variant="outline"
            size="icon"
            className="mt-1 h-11 w-11 rounded-full"
          >
            <Link href="/company/profile">
              <ArrowLeft className="h-5 w-5" />
            </Link>
          </Button>

          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-3xl font-bold tracking-tight">الفوترة والاشتراكات</h1>
              <Badge className={subStatus.className}>{subStatus.label}</Badge>
              <Badge variant="outline" className="rounded-full">
                <Building2 className="me-1 h-3.5 w-3.5" />
                {companyName || "الشركة"}
              </Badge>
            </div>

            <p className="text-sm text-muted-foreground">
              عرض اشتراك الشركة الحالي، الفواتير، وسجل الدفعات في صفحة واحدة.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            className="rounded-2xl"
            onClick={() => void loadData(true)}
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
      </div>

      <Card className="overflow-hidden rounded-[28px] border-border/60 shadow-sm">
        <CardContent className="p-0">
          <div className="grid gap-0 lg:grid-cols-[1.45fr_1fr]">
            <div className="relative overflow-hidden bg-gradient-to-br from-background via-background to-muted/40 p-6 md:p-8">
              <div className="mb-6 flex items-center justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                    <ShieldCheck className="h-4 w-4" />
                    مساحة فوترة الشركة
                  </div>
                  <h2 className="text-2xl font-bold">
                    {subscription?.plan || "لا يوجد اشتراك نشط"}
                  </h2>
                  <p className="max-w-2xl text-sm leading-7 text-muted-foreground">
                    {companyEmail || "—"}
                  </p>
                </div>

                <div className="rounded-2xl border border-border/60 bg-background/80 p-3 shadow-sm">
                  <Image
                    src="/currency/sar.svg"
                    alt="SAR"
                    width={34}
                    height={34}
                    className="h-9 w-9 object-contain"
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-3xl border border-border/60 bg-background/80 p-4 shadow-sm">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">إجمالي الفواتير</span>
                    <Receipt className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="text-2xl font-bold">{formatMoney(summary.invoicesTotal)}</div>
                  <div className="mt-1 text-xs text-muted-foreground">SAR</div>
                </div>

                <div className="rounded-3xl border border-border/60 bg-background/80 p-4 shadow-sm">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">إجمالي الدفعات</span>
                    <Wallet className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="text-2xl font-bold">{formatMoney(summary.paymentsTotal)}</div>
                  <div className="mt-1 text-xs text-muted-foreground">SAR</div>
                </div>

                <div className="rounded-3xl border border-border/60 bg-background/80 p-4 shadow-sm">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">فواتير مدفوعة</span>
                    <BadgeCheck className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="text-2xl font-bold">{summary.paidInvoices}</div>
                  <div className="mt-1 text-xs text-muted-foreground">فاتورة</div>
                </div>

                <div className="rounded-3xl border border-border/60 bg-background/80 p-4 shadow-sm">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">فواتير معلقة</span>
                    <Clock3 className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="text-2xl font-bold">{summary.pendingInvoices}</div>
                  <div className="mt-1 text-xs text-muted-foreground">فاتورة</div>
                </div>
              </div>
            </div>

            <div className="border-t border-border/60 bg-muted/20 p-6 md:p-8 lg:border-r lg:border-t-0">
              <div className="space-y-5">
                <div>
                  <div className="mb-1 text-sm text-muted-foreground">حالة الاشتراك</div>
                  <Badge className={subStatus.className}>{subStatus.label}</Badge>
                </div>

                <Separator />

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
                  <div className="rounded-2xl border border-border/60 bg-background p-4">
                    <div className="mb-1 text-xs text-muted-foreground">الباقة</div>
                    <div className="font-semibold">{subscription?.plan || "-"}</div>
                  </div>

                  <div className="rounded-2xl border border-border/60 bg-background p-4">
                    <div className="mb-1 text-xs text-muted-foreground">دورة الفوترة</div>
                    <div className="font-semibold">
                      {normalizeCycle(subscription?.billing_cycle)}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border/60 bg-background p-4">
                    <div className="mb-1 text-xs text-muted-foreground">بداية الاشتراك</div>
                    <div className="font-semibold">
                      {formatDate(subscription?.started_at || null)}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border/60 bg-background p-4">
                    <div className="mb-1 text-xs text-muted-foreground">نهاية الاشتراك</div>
                    <div className="font-semibold">
                      {formatDate(subscription?.ends_at || null)}
                    </div>
                  </div>
                </div>

                <Separator />

                <div className="grid gap-3 sm:grid-cols-2">
                  <Button
                    type="button"
                    size="lg"
                    className="h-12 rounded-2xl"
                    onClick={handleRenewSubscription}
                    disabled={renewing || !subscription?.id}
                  >
                    {renewing ? (
                      <Loader2 className="ms-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Repeat className="ms-2 h-4 w-4" />
                    )}
                    تجديد الاشتراك
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    size="lg"
                    className="h-12 rounded-2xl"
                    onClick={handleChangePlan}
                    disabled={redirectingPlanChange || !subscription?.id}
                  >
                    {redirectingPlanChange ? (
                      <Loader2 className="ms-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Sparkles className="ms-2 h-4 w-4" />
                    )}
                    تغيير الباقة
                  </Button>
                </div>

                <Separator />

                <div className="space-y-3">
                  <div className="text-sm font-semibold">آخر حركة</div>

                  <div className="rounded-2xl border border-border/60 bg-background p-4">
                    <div className="mb-1 flex items-center gap-2 text-sm text-muted-foreground">
                      <FileText className="h-4 w-4" />
                      آخر فاتورة
                    </div>
                    <div className="font-semibold">
                      {latestInvoice?.number || latestInvoice?.invoice_number || "-"}
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {formatDate(latestInvoice?.issue_date || null)}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border/60 bg-background p-4">
                    <div className="mb-1 flex items-center gap-2 text-sm text-muted-foreground">
                      <CreditCard className="h-4 w-4" />
                      آخر دفعة
                    </div>
                    <div className="font-semibold">
                      {formatMoney(latestPayment?.amount)} SAR
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {formatDate(latestPayment?.processed_at || latestPayment?.paid_at || null)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="subscription" className="space-y-6">
        <TabsList className="h-auto w-full flex-wrap justify-start gap-2 rounded-2xl bg-muted/50 p-2">
          <TabsTrigger value="subscription" className="rounded-xl px-4 py-2">
            الاشتراك
          </TabsTrigger>
          <TabsTrigger value="invoices" className="rounded-xl px-4 py-2">
            الفواتير
          </TabsTrigger>
          <TabsTrigger value="payments" className="rounded-xl px-4 py-2">
            الدفعات
          </TabsTrigger>
        </TabsList>

        <TabsContent value="subscription" className="space-y-6">
          <Card className="rounded-[26px] border-border/60 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CircleDollarSign className="h-5 w-5" />
                سجل الاشتراكات
              </CardTitle>
              <CardDescription>
                جميع الاشتراكات المرتبطة بالشركة الحالية.
              </CardDescription>
            </CardHeader>

            <CardContent>
              {subscriptions.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-border/70 p-10 text-center text-sm text-muted-foreground">
                  لا توجد اشتراكات حتى الآن.
                </div>
              ) : (
                <div className="overflow-x-auto rounded-2xl border border-border/60">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-right">المعرف</TableHead>
                        <TableHead className="text-right">الباقة</TableHead>
                        <TableHead className="text-right">السعر</TableHead>
                        <TableHead className="text-right">البداية</TableHead>
                        <TableHead className="text-right">النهاية</TableHead>
                        <TableHead className="text-right">الحالة</TableHead>
                      </TableRow>
                    </TableHeader>

                    <TableBody>
                      {subscriptions.map((item) => {
                        const itemStatus = normalizeStatus(item.status)

                        return (
                          <TableRow key={item.id}>
                            <TableCell className="font-medium">
                              SUB-{item.id}
                            </TableCell>
                            <TableCell>{item.plan_name || "-"}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Image
                                  src="/currency/sar.svg"
                                  alt="SAR"
                                  width={16}
                                  height={16}
                                  className="h-4 w-4 object-contain"
                                />
                                <span>{formatMoney(item.price)}</span>
                              </div>
                            </TableCell>
                            <TableCell>{formatDate(item.start_date)}</TableCell>
                            <TableCell>{formatDate(item.end_date)}</TableCell>
                            <TableCell>
                              <Badge className={itemStatus.className}>
                                {itemStatus.label}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="invoices" className="space-y-6">
          <Card className="rounded-[26px] border-border/60 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Receipt className="h-5 w-5" />
                فواتير الشركة
              </CardTitle>
              <CardDescription>
                جميع الفواتير المرتبطة بالشركة الحالية.
              </CardDescription>
            </CardHeader>

            <CardContent>
              {invoices.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-border/70 p-10 text-center text-sm text-muted-foreground">
                  لا توجد فواتير حتى الآن.
                </div>
              ) : (
                <div className="overflow-x-auto rounded-2xl border border-border/60">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-right">رقم الفاتورة</TableHead>
                        <TableHead className="text-right">التاريخ</TableHead>
                        <TableHead className="text-right">الإجمالي</TableHead>
                        <TableHead className="text-right">طريقة الدفع</TableHead>
                        <TableHead className="text-right">الحالة</TableHead>
                      </TableRow>
                    </TableHeader>

                    <TableBody>
                      {invoices.map((invoice) => {
                        const invoiceStatus = normalizeStatus(invoice.status)
                        const invoiceNumber =
                          invoice.number || invoice.invoice_number || `INV-${invoice.id}`

                        return (
                          <TableRow key={invoice.id}>
                            <TableCell className="font-medium">
                              <Link
                                href={`/company/invoices/${invoiceNumber}`}
                                className="font-medium text-blue-600 hover:text-blue-700 hover:underline dark:text-blue-400 dark:hover:text-blue-300"
                              >
                                {invoiceNumber}
                              </Link>
                            </TableCell>
                            <TableCell>{formatDate(invoice.issue_date)}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Image
                                  src="/currency/sar.svg"
                                  alt="SAR"
                                  width={16}
                                  height={16}
                                  className="h-4 w-4 object-contain"
                                />
                                <span>{formatMoney(invoice.total_amount)}</span>
                              </div>
                            </TableCell>
                            <TableCell>{normalizeMethod(invoice.payment_method)}</TableCell>
                            <TableCell>
                              <Badge className={invoiceStatus.className}>
                                {invoiceStatus.label}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments" className="space-y-6">
          <Card className="rounded-[26px] border-border/60 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wallet className="h-5 w-5" />
                سجل الدفعات
              </CardTitle>
              <CardDescription>
                آخر الدفعات المرتبطة بفواتير الشركة.
              </CardDescription>
            </CardHeader>

            <CardContent>
              {payments.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-border/70 p-10 text-center text-sm text-muted-foreground">
                  لا توجد دفعات حتى الآن.
                </div>
              ) : (
                <div className="overflow-x-auto rounded-2xl border border-border/60">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-right">المرجع</TableHead>
                        <TableHead className="text-right">الفاتورة</TableHead>
                        <TableHead className="text-right">المبلغ</TableHead>
                        <TableHead className="text-right">الطريقة</TableHead>
                        <TableHead className="text-right">التاريخ</TableHead>
                        <TableHead className="text-right">الحالة</TableHead>
                      </TableRow>
                    </TableHeader>

                    <TableBody>
                      {payments.map((payment) => {
                        const paymentStatus = normalizeStatus(payment.status)
                        const paymentMethod =
                          payment.payment_method || payment.method || "-"
                        const paymentDate =
                          payment.processed_at || payment.paid_at || null

                        return (
                          <TableRow key={payment.id}>
                            <TableCell className="font-medium">
                              {payment.reference || payment.reference_number || `PAY-${payment.id}`}
                            </TableCell>
                            <TableCell>{payment.invoice_number || "-"}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Image
                                  src="/currency/sar.svg"
                                  alt="SAR"
                                  width={16}
                                  height={16}
                                  className="h-4 w-4 object-contain"
                                />
                                <span>{formatMoney(payment.amount)}</span>
                              </div>
                            </TableCell>
                            <TableCell>{normalizeMethod(paymentMethod)}</TableCell>
                            <TableCell>{formatDate(paymentDate)}</TableCell>
                            <TableCell>
                              <Badge className={paymentStatus.className}>
                                {paymentStatus.label}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {companyId ? (
        <div className="text-xs text-muted-foreground">
          Company ID: {companyId}
        </div>
      ) : null}
    </div>
  )
}