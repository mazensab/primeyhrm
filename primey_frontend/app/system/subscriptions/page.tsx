"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { toast } from "sonner"
import {
  Search,
  RefreshCw,
  Eye,
  CreditCard,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  XCircle,
  Building2,
  Loader2,
  ShieldCheck,
  ShieldX,
} from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

// ======================================================
// Types
// ======================================================

type Locale = "ar" | "en"
type Direction = "rtl" | "ltr"
type FilterType = "all" | "active" | "expired" | "exp7" | "exp30"

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
// Locale Helpers
// ======================================================

const translations = {
  ar: {
    pageTitle: "الاشتراكات",
    pageSubtitle: "إدارة ومتابعة اشتراكات الشركات داخل النظام",
    total: "إجمالي الاشتراكات",
    active: "الاشتراكات النشطة",
    expiring: "قرب الانتهاء",
    expired: "المنتهية",
    searchTitle: "البحث والتصفية",
    searchHint: "يمكنك البحث مباشرة باسم الشركة",
    searchPlaceholder: "ابحث باسم الشركة...",
    all: "الكل",
    exp7: "7 أيام",
    exp30: "30 يومًا",
    tableTitle: "قائمة الاشتراكات",
    company: "الشركة",
    plan: "الخطة",
    status: "الحالة",
    start: "البداية",
    end: "النهاية",
    price: "السعر",
    actions: "الإجراءات",
    view: "عرض",
    loading: "جارٍ تحميل الاشتراكات...",
    empty: "لا توجد اشتراكات مطابقة",
    refresh: "تحديث",
    retry: "إعادة المحاولة",
    fetchSuccess: "تم تحديث الاشتراكات بنجاح",
    fetchError: "تعذر تحميل الاشتراكات",
    statusActive: "نشط",
    statusExpired: "منتهي",
    statusPending: "معلّق",
    statusCanceled: "ملغي",
    statusUnknown: "غير معروف",
    pricePrefix: "SAR",
    mobileListTitle: "قائمة الاشتراكات",
  },
  en: {
    pageTitle: "Subscriptions",
    pageSubtitle: "Manage and monitor company subscriptions across the system",
    total: "Total Subscriptions",
    active: "Active Subscriptions",
    expiring: "Expiring Soon",
    expired: "Expired Subscriptions",
    searchTitle: "Search & Filter",
    searchHint: "You can search directly by company name",
    searchPlaceholder: "Search by company name...",
    all: "All",
    exp7: "7 Days",
    exp30: "30 Days",
    tableTitle: "Subscriptions List",
    company: "Company",
    plan: "Plan",
    status: "Status",
    start: "Start",
    end: "End",
    price: "Price",
    actions: "Actions",
    view: "View",
    loading: "Loading subscriptions...",
    empty: "No matching subscriptions found",
    refresh: "Refresh",
    retry: "Retry",
    fetchSuccess: "Subscriptions refreshed successfully",
    fetchError: "Failed to load subscriptions",
    statusActive: "Active",
    statusExpired: "Expired",
    statusPending: "Pending",
    statusCanceled: "Canceled",
    statusUnknown: "Unknown",
    pricePrefix: "SAR",
    mobileListTitle: "Subscriptions List",
  },
} as const

function detectLocale(): Locale {
  if (typeof document === "undefined") return "en"

  const htmlLang = document.documentElement.lang?.toLowerCase().trim() || ""
  if (htmlLang.startsWith("ar")) return "ar"
  if (htmlLang.startsWith("en")) return "en"

  const bodyLang = document.body?.getAttribute("lang")?.toLowerCase().trim() || ""
  if (bodyLang.startsWith("ar")) return "ar"
  if (bodyLang.startsWith("en")) return "en"

  const htmlDir = document.documentElement.dir?.toLowerCase().trim() || ""
  if (htmlDir === "rtl") return "ar"
  if (htmlDir === "ltr") return "en"

  if (typeof navigator !== "undefined") {
    const language = navigator.language?.toLowerCase() || ""
    if (language.startsWith("ar")) return "ar"
  }

  return "en"
}

function detectDirection(locale: Locale): Direction {
  if (typeof document === "undefined") {
    return locale === "ar" ? "rtl" : "ltr"
  }

  const htmlDir = document.documentElement.dir?.toLowerCase().trim()
  if (htmlDir === "rtl" || htmlDir === "ltr") return htmlDir

  return locale === "ar" ? "rtl" : "ltr"
}

// ======================================================
// Formatting Helpers
// ======================================================

function formatNumberEn(value: number): string {
  const safeValue = Number.isFinite(value) ? value : 0

  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(safeValue)
}

function formatDateEn(dateValue: string): string {
  if (!dateValue) return "—"

  const parsed = new Date(dateValue)
  if (Number.isNaN(parsed.getTime())) return "—"

  const year = parsed.getFullYear()
  const month = String(parsed.getMonth() + 1).padStart(2, "0")
  const day = String(parsed.getDate()).padStart(2, "0")

  return `${year}/${month}/${day}`
}

function getDiffDays(endDate: string): number {
  const end = new Date(endDate)
  const now = new Date()

  if (Number.isNaN(end.getTime())) return Number.POSITIVE_INFINITY

  const diffMs = end.getTime() - now.getTime()
  return diffMs / (1000 * 60 * 60 * 24)
}

function normalizeStatus(status: string): string {
  return String(status || "").trim().toUpperCase()
}

function getLocalizedStatus(status: string, locale: Locale): string {
  const t = translations[locale]
  const normalized = normalizeStatus(status)

  if (normalized === "ACTIVE") return t.statusActive
  if (normalized === "EXPIRED") return t.statusExpired
  if (normalized === "PENDING") return t.statusPending
  if (normalized === "CANCELED" || normalized === "CANCELLED") return t.statusCanceled

  return t.statusUnknown
}

function SubscriptionStatusBadge({
  status,
  locale,
}: {
  status: string
  locale: Locale
}) {
  const normalized = normalizeStatus(status)
  const text = getLocalizedStatus(status, locale)

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
      {text}
    </span>
  )
}

// ======================================================
// Page
// ======================================================

export default function SystemSubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [search, setSearch] = useState("")
  const [filter, setFilter] = useState<FilterType>("all")
  const [locale, setLocale] = useState<Locale>("en")
  const [direction, setDirection] = useState<Direction>("ltr")

  const t = translations[locale]
  const isArabic = locale === "ar"

  // ======================================================
  // Sync Language / Direction
  // ======================================================

  useEffect(() => {
    const syncLanguage = () => {
      const nextLocale = detectLocale()
      const nextDirection = detectDirection(nextLocale)

      setLocale(nextLocale)
      setDirection(nextDirection)
    }

    syncLanguage()

    const observer =
      typeof MutationObserver !== "undefined"
        ? new MutationObserver(() => syncLanguage())
        : null

    if (observer && typeof document !== "undefined") {
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["lang", "dir"],
      })
    }

    window.addEventListener("languagechange", syncLanguage)
    window.addEventListener("focus", syncLanguage)

    return () => {
      observer?.disconnect()
      window.removeEventListener("languagechange", syncLanguage)
      window.removeEventListener("focus", syncLanguage)
    }
  }, [])

  // ======================================================
  // Fetch Subscriptions
  // ======================================================

  const fetchSubscriptions = async (showSuccessToast = false) => {
    try {
      const res = await fetch("http://localhost:8000/api/system/subscriptions/", {
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
        cache: "no-store",
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      const data = await res.json()
      setSubscriptions(Array.isArray(data?.subscriptions) ? data.subscriptions : [])

      if (showSuccessToast) {
        toast.success(translations[detectLocale()].fetchSuccess)
      }
    } catch (error) {
      console.error("Subscriptions fetch error:", error)
      toast.error(translations[detectLocale()].fetchError)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    void fetchSubscriptions(false)
  }, [])

  // ======================================================
  // Actions
  // ======================================================

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchSubscriptions(true)
  }

  // ======================================================
  // Filters
  // ======================================================

  const filtered = useMemo(() => {
    return subscriptions.filter((sub) => {
      const companyName = String(sub.company_name || "").toLowerCase()
      const query = search.trim().toLowerCase()

      if (query && !companyName.includes(query)) {
        return false
      }

      const diffDays = getDiffDays(sub.end_date)
      const normalizedStatus = normalizeStatus(sub.status)

      if (filter === "active") return normalizedStatus === "ACTIVE"
      if (filter === "expired") return normalizedStatus === "EXPIRED"
      if (filter === "exp7") return diffDays <= 7 && diffDays >= 0
      if (filter === "exp30") return diffDays <= 30 && diffDays >= 0

      return true
    })
  }, [subscriptions, search, filter])

  // ======================================================
  // Stats
  // ======================================================

  const stats = useMemo(() => {
    const total = subscriptions.length
    const active = subscriptions.filter(
      (sub) => normalizeStatus(sub.status) === "ACTIVE"
    ).length
    const expired = subscriptions.filter(
      (sub) => normalizeStatus(sub.status) === "EXPIRED"
    ).length
    const expiring = subscriptions.filter((sub) => {
      const diffDays = getDiffDays(sub.end_date)
      return diffDays <= 7 && diffDays >= 0
    }).length

    return { total, active, expired, expiring }
  }, [subscriptions])

  const filterButtons: Array<{
    value: FilterType
    label: string
  }> = [
    { value: "all", label: t.all },
    { value: "active", label: t.active },
    { value: "exp7", label: t.exp7 },
    { value: "exp30", label: t.exp30 },
    { value: "expired", label: t.expired },
  ]

  // ======================================================
  // UI
  // ======================================================

  return (
    <div dir={direction} className="space-y-6">
      {/* ===================================== */}
      {/* Page Header */}
      {/* ===================================== */}

      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            {t.pageTitle}
          </h1>
          <p className="text-sm text-muted-foreground md:text-base">
            {t.pageSubtitle}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing || loading}
            className="gap-2"
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            {t.refresh}
          </Button>
        </div>
      </div>

      {/* ===================================== */}
      {/* Stats */}
      {/* ===================================== */}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.total}</p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumberEn(stats.total)}
              </p>
            </div>

            <div className="rounded-2xl border bg-muted/40 p-3">
              <CreditCard className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.active}</p>
              <p className="text-3xl font-semibold tabular-nums text-emerald-600">
                {formatNumberEn(stats.active)}
              </p>
            </div>

            <div className="rounded-2xl border bg-muted/40 p-3">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.expiring}</p>
              <p className="text-3xl font-semibold tabular-nums text-amber-500">
                {formatNumberEn(stats.expiring)}
              </p>
            </div>

            <div className="rounded-2xl border bg-muted/40 p-3">
              <Clock3 className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60 sm:col-span-2 xl:col-span-1">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.expired}</p>
              <p className="text-3xl font-semibold tabular-nums text-rose-600">
                {formatNumberEn(stats.expired)}
              </p>
            </div>

            <div className="rounded-2xl border bg-muted/40 p-3">
              <XCircle className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ===================================== */}
      {/* Search + Filters */}
      {/* ===================================== */}

      <Card className="border-border/60">
        <CardHeader className="pb-3">
          <CardTitle className="text-base md:text-lg">
            {t.searchTitle}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-3">
          <div className="relative">
            <Search
              className={[
                "absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                isArabic ? "right-3" : "left-3",
              ].join(" ")}
            />

            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t.searchPlaceholder}
              className={isArabic ? "pr-10" : "pl-10"}
            />
          </div>

          <p className="text-xs text-muted-foreground">
            {t.searchHint}
          </p>

          <div
            className={[
              "flex flex-wrap gap-2",
              isArabic ? "justify-start" : "justify-start",
            ].join(" ")}
          >
            {filterButtons.map((item) => (
              <Button
                key={item.value}
                type="button"
                size="sm"
                variant={filter === item.value ? "default" : "outline"}
                onClick={() => setFilter(item.value)}
                className="min-w-[72px]"
              >
                {item.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ===================================== */}
      {/* Desktop / Tablet Table */}
      {/* ===================================== */}

      <Card className="hidden border-border/60 lg:block">
        <CardHeader>
          <CardTitle className="text-base md:text-lg">
            {t.tableTitle}
          </CardTitle>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-14 text-muted-foreground">
              <Loader2 className="me-2 h-5 w-5 animate-spin" />
              {t.loading}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t.company}</TableHead>
                  <TableHead>{t.plan}</TableHead>
                  <TableHead>{t.status}</TableHead>
                  <TableHead>{t.start}</TableHead>
                  <TableHead>{t.end}</TableHead>
                  <TableHead>{t.price}</TableHead>
                  <TableHead className={isArabic ? "text-left" : "text-right"}>
                    {t.actions}
                  </TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="py-12 text-center text-muted-foreground"
                    >
                      {t.empty}
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((sub) => (
                    <TableRow key={sub.id}>
                      <TableCell>
                        <div className="flex items-center gap-2 font-medium">
                          <Building2 className="h-4 w-4 text-muted-foreground" />
                          <span>{sub.company_name || "—"}</span>
                        </div>
                      </TableCell>

                      <TableCell>{sub.plan_name || "—"}</TableCell>

                      <TableCell>
                        <SubscriptionStatusBadge
                          status={sub.status}
                          locale={locale}
                        />
                      </TableCell>

                      <TableCell className="tabular-nums">
                        {formatDateEn(sub.start_date)}
                      </TableCell>

                      <TableCell className="tabular-nums">
                        {formatDateEn(sub.end_date)}
                      </TableCell>

                      <TableCell className="tabular-nums">
                        {t.pricePrefix} {formatNumberEn(Number(sub.price || 0))}
                      </TableCell>

                      <TableCell className={isArabic ? "text-left" : "text-right"}>
                        <div
                          className={[
                            "flex flex-wrap gap-2",
                            isArabic ? "justify-start" : "justify-end",
                          ].join(" ")}
                        >
                          <Button asChild size="sm" variant="outline" className="gap-2">
                            <Link href={`/system/subscriptions/${sub.id}`}>
                              <Eye className="h-4 w-4" />
                              {t.view}
                            </Link>
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* ===================================== */}
      {/* Mobile / Small Tablet Cards */}
      {/* ===================================== */}

      <div className="grid gap-4 lg:hidden">
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="text-base md:text-lg">
              {t.mobileListTitle}
            </CardTitle>
          </CardHeader>

          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-14 text-muted-foreground">
                <Loader2 className="me-2 h-5 w-5 animate-spin" />
                {t.loading}
              </div>
            ) : filtered.length === 0 ? (
              <div className="py-10 text-center text-sm text-muted-foreground">
                {t.empty}
              </div>
            ) : (
              <div className="space-y-4">
                {filtered.map((sub) => (
                  <div
                    key={sub.id}
                    className="rounded-2xl border border-border/60 bg-background p-4 shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 shrink-0 text-muted-foreground" />
                          <h3 className="truncate font-semibold">
                            {sub.company_name || "—"}
                          </h3>
                        </div>

                        <p className="truncate text-sm text-muted-foreground">
                          {sub.plan_name || "—"}
                        </p>
                      </div>

                      <SubscriptionStatusBadge
                        status={sub.status}
                        locale={locale}
                      />
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <div className="rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">
                          {t.start}
                        </p>
                        <p className="mt-1 font-medium tabular-nums">
                          {formatDateEn(sub.start_date)}
                        </p>
                      </div>

                      <div className="rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">
                          {t.end}
                        </p>
                        <p className="mt-1 font-medium tabular-nums">
                          {formatDateEn(sub.end_date)}
                        </p>
                      </div>

                      <div className="col-span-2 rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">
                          {t.price}
                        </p>
                        <p className="mt-1 font-medium tabular-nums">
                          {t.pricePrefix} {formatNumberEn(Number(sub.price || 0))}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      <Button asChild variant="outline" className="flex-1 gap-2">
                        <Link href={`/system/subscriptions/${sub.id}`}>
                          <Eye className="h-4 w-4" />
                          {t.view}
                        </Link>
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}