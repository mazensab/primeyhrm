"use client"

import { useEffect, useMemo, useState } from "react"
import Image from "next/image"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

const API = process.env.NEXT_PUBLIC_API_URL

/* ============================================================
   🌍 الترجمة
============================================================ */
const translations = {
  ar: {
    pageTitle: "لوحة تحكم النظام",
    pageSubtitle: "Mham Cloud — مركز تحكم السوبر أدمن",

    systemOverview: "نظرة عامة على النظام",
    globalPlatformStats: "إحصائيات المنصة العامة",
    totalCompanies: "إجمالي الشركات",
    activeCompanies: "الشركات النشطة",
    suspended: "الموقوفة",
    totalUsers: "إجمالي المستخدمين",

    subscriptions: "الاشتراكات",
    platformSubscriptionStats: "إحصائيات اشتراكات المنصة",
    totalSubscriptions: "إجمالي الاشتراكات",
    active: "النشطة",
    trial: "التجريبية",
    expired: "المنتهية",

    totalRevenue: "إجمالي الإيرادات",
    fromLastMonth: "مقارنة بالشهر الماضي",

    recentPayments: "آخر المدفوعات",
    latestPlatformPayments: "أحدث مدفوعات المنصة",
    noPaymentsYet: "لا توجد مدفوعات حتى الآن",

    expiringSoon: "تنتهي قريبًا",
    subscriptionsEnding: "الاشتراكات التي قاربت على الانتهاء",
    within7Days: "خلال 7 أيام",
    within30Days: "خلال 30 يومًا",

    paymentMethodSeparator: "•",
  },
  en: {
    pageTitle: "System Dashboard",
    pageSubtitle: "Mham Cloud — Super Admin Control Center",

    systemOverview: "System Overview",
    globalPlatformStats: "Global platform statistics",
    totalCompanies: "Total Companies",
    activeCompanies: "Active Companies",
    suspended: "Suspended",
    totalUsers: "Total Users",

    subscriptions: "Subscriptions",
    platformSubscriptionStats: "Platform subscription statistics",
    totalSubscriptions: "Total Subscriptions",
    active: "Active",
    trial: "Trial",
    expired: "Expired",

    totalRevenue: "Total Revenue",
    fromLastMonth: "from last month",

    recentPayments: "Recent Payments",
    latestPlatformPayments: "Latest platform payments",
    noPaymentsYet: "No payments yet",

    expiringSoon: "Expiring Soon",
    subscriptionsEnding: "Subscriptions ending",
    within7Days: "Within 7 days",
    within30Days: "Within 30 days",

    paymentMethodSeparator: "•",
  },
} as const

type Lang = "ar" | "en"

/* ============================================================
   🔐 Helper — Safe JSON Fetch
============================================================ */
async function safeFetch(path: string) {
  try {
    const res = await fetch(`${API}${path}`, {
      credentials: "include",
      headers: { Accept: "application/json" },
    })

    if (!res.ok) {
      return null
    }

    return await res.json()
  } catch {
    return null
  }
}

/* ============================================================
   🌍 Helpers — Language / Formatting
============================================================ */
function getDocumentLang(): Lang {
  if (typeof document === "undefined") return "ar"

  const lang =
    document.documentElement.lang ||
    document.body.getAttribute("lang") ||
    "ar"

  return lang.toLowerCase().startsWith("en") ? "en" : "ar"
}

/* جميع الأرقام إنجليزية دائمًا */
function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US").format(Number(value || 0))
}

/* التاريخ يحافظ على اللغة لكن بالأرقام الإنجليزية */
function formatDate(value: string, lang: Lang) {
  if (!value) return "-"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat(
    lang === "ar" ? "ar-SA-u-nu-latn" : "en-US",
    {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }
  ).format(date)
}

/* ============================================================
   🟦 Page
============================================================ */
export default function Page() {
  const [overview, setOverview] = useState<any>(null)
  const [revenue, setRevenue] = useState<any>(null)
  const [lang, setLang] = useState<Lang>("ar")

  useEffect(() => {
    setLang(getDocumentLang())

    const observer = new MutationObserver(() => {
      setLang(getDocumentLang())
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    async function load() {
      const [o, r] = await Promise.all([
        safeFetch("/api/system/companies/overview/"),
        safeFetch("/api/system/payments/revenue-summary/"),
      ])

      setOverview(o)
      setRevenue(r)
    }

    load()
  }, [])

  const t = useMemo(() => translations[lang], [lang])
  const isArabic = lang === "ar"

  return (
    <div className="space-y-6 p-6" dir={isArabic ? "rtl" : "ltr"}>
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">{t.pageTitle}</h1>
        <p className="text-muted-foreground">{t.pageSubtitle}</p>
      </div>

      {/* =============================== */}
      {/* Top KPI Row */}
      {/* =============================== */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* System Overview */}
        <Card>
          <CardHeader>
            <CardTitle>{t.systemOverview}</CardTitle>
            <CardDescription>{t.globalPlatformStats}</CardDescription>
          </CardHeader>

          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span>{t.totalCompanies}</span>
              <Badge>{formatNumber(overview?.companies?.total ?? 0)}</Badge>
            </div>

            <div className="flex items-center justify-between gap-3">
              <span>{t.activeCompanies}</span>
              <Badge variant="secondary">
                {formatNumber(overview?.companies?.active ?? 0)}
              </Badge>
            </div>

            <div className="flex items-center justify-between gap-3">
              <span>{t.suspended}</span>
              <Badge variant="destructive">
                {formatNumber(overview?.companies?.suspended ?? 0)}
              </Badge>
            </div>

            <Separator />

            <div className="flex items-center justify-between gap-3 font-medium">
              <span>{t.totalUsers}</span>
              <span>{formatNumber(overview?.users_total ?? 0)}</span>
            </div>
          </CardContent>
        </Card>

        {/* Subscriptions Overview */}
        <Card>
          <CardHeader>
            <CardTitle>{t.subscriptions}</CardTitle>
            <CardDescription>{t.platformSubscriptionStats}</CardDescription>
          </CardHeader>

          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span>{t.totalSubscriptions}</span>
              <Badge>{formatNumber(overview?.subscriptions?.total ?? 0)}</Badge>
            </div>

            <div className="flex items-center justify-between gap-3">
              <span>{t.active}</span>
              <Badge variant="secondary">
                {formatNumber(overview?.subscriptions?.active ?? 0)}
              </Badge>
            </div>

            <div className="flex items-center justify-between gap-3">
              <span>{t.trial}</span>
              <Badge variant="outline">
                {formatNumber(overview?.subscriptions?.trial ?? 0)}
              </Badge>
            </div>

            <div className="flex items-center justify-between gap-3">
              <span>{t.expired}</span>
              <Badge variant="destructive">
                {formatNumber(overview?.subscriptions?.expired ?? 0)}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Total Revenue */}
        <Card>
          <CardHeader>
            <CardTitle>{t.totalRevenue}</CardTitle>
            <CardDescription>
              {formatNumber(revenue?.growth_percent ?? 0)}% {t.fromLastMonth}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div
              dir="ltr"
              className="flex items-center justify-start gap-2 text-3xl font-bold"
            >
              <Image
                src="/currency/sar.svg"
                alt="SAR"
                width={20}
                height={20}
                className="h-5 w-5 shrink-0"
              />
              <span>{formatNumber(revenue?.total_revenue ?? 0)}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* =============================== */}
      {/* Bottom Section */}
      {/* =============================== */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Recent Payments */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>{t.recentPayments}</CardTitle>
            <CardDescription>{t.latestPlatformPayments}</CardDescription>
          </CardHeader>

          <CardContent className="space-y-3 text-sm">
            {revenue?.recent?.length ? (
              revenue.recent.map((p: any) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between gap-3 border-b pb-2 last:border-b-0"
                >
                  <div className="flex min-w-0 flex-col">
                    <span className="truncate font-medium">{p.company_name}</span>
                    <span className="text-xs text-muted-foreground">
                      {p.method} {t.paymentMethodSeparator}{" "}
                      {formatDate(p.paid_at, lang)}
                    </span>
                  </div>

                  <div
                    dir="ltr"
                    className="flex shrink-0 items-center gap-1 font-semibold"
                  >
                    <Image
                      src="/currency/sar.svg"
                      alt="SAR"
                      width={16}
                      height={16}
                      className="h-4 w-4 shrink-0"
                    />
                    <span>{formatNumber(p.amount)}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-muted-foreground">
                {t.noPaymentsYet}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Expiring Subscriptions */}
        <Card>
          <CardHeader>
            <CardTitle>{t.expiringSoon}</CardTitle>
            <CardDescription>{t.subscriptionsEnding}</CardDescription>
          </CardHeader>

          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span>{t.within7Days}</span>
              <Badge variant="destructive">
                {formatNumber(overview?.subscriptions?.expiring_7 ?? 0)}
              </Badge>
            </div>

            <div className="flex items-center justify-between gap-3">
              <span>{t.within30Days}</span>
              <Badge variant="secondary">
                {formatNumber(overview?.subscriptions?.expiring_30 ?? 0)}
              </Badge>
            </div>

            <div className="flex items-center justify-between gap-3">
              <span>{t.expired}</span>
              <Badge variant="outline">
                {formatNumber(overview?.subscriptions?.expired ?? 0)}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}