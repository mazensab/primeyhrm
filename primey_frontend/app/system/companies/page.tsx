"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Building2,
  Eye,
  FileDown,
  FileSpreadsheet,
  Loader2,
  Plus,
  Power,
  RefreshCw,
  Search,
  ShieldCheck,
  ShieldX,
  Users,
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

type Locale = "ar" | "en"

type Company = {
  id: number
  name: string
  is_active: boolean
  created_at: string
  owner?: {
    email?: string
  }
  subscription?: {
    plan?: string
    status?: string
  }
  users_count: number
}

type Dictionary = {
  pageTitle: string
  pageDescription: string
  addCompany: string
  refresh: string
  pdf: string
  excel: string
  searchTitle: string
  searchPlaceholder: string
  searchHint: string
  companiesList: string
  company: string
  owner: string
  plan: string
  users: string
  status: string
  created: string
  actions: string
  manageCompany: string
  view: string
  active: string
  disabled: string
  loadingCompanies: string
  noCompaniesFound: string
  failedLoad: string
  failedUpdate: string
  serverUpdateError: string
  statusUpdated: string
  exportedSuccessfully: string
  totalCompanies: string
  activeCompanies: string
  disabledCompanies: string
  subscriptionStatus: string
  unknown: string
  noOwner: string
  noPlan: string
  printHint: string
}

const translations: Record<Locale, Dictionary> = {
  ar: {
    pageTitle: "الشركات",
    pageDescription: "إدارة جميع الشركات على المنصة بشكل احترافي ومتوافق مع جميع الأجهزة",
    addCompany: "إضافة شركة",
    refresh: "تحديث",
    pdf: "PDF",
    excel: "Excel",
    searchTitle: "البحث والتصفية",
    searchPlaceholder: "ابحث باسم الشركة...",
    searchHint: "يمكنك البحث مباشرة باسم الشركة",
    companiesList: "قائمة الشركات",
    company: "الشركة",
    owner: "المالك",
    plan: "الخطة",
    users: "المستخدمون",
    status: "الحالة",
    created: "تاريخ الإنشاء",
    actions: "الإجراءات",
    manageCompany: "إدارة الشركة",
    view: "عرض",
    active: "نشطة",
    disabled: "معطلة",
    loadingCompanies: "جاري تحميل الشركات...",
    noCompaniesFound: "لا توجد شركات مطابقة",
    failedLoad: "تعذر تحميل الشركات",
    failedUpdate: "فشل تحديث حالة الشركة",
    serverUpdateError: "حدث خطأ أثناء تحديث حالة الشركة",
    statusUpdated: "تم تحديث حالة الشركة بنجاح",
    exportedSuccessfully: "تم تصدير الشركات بنجاح",
    totalCompanies: "إجمالي الشركات",
    activeCompanies: "الشركات النشطة",
    disabledCompanies: "الشركات المعطلة",
    subscriptionStatus: "حالة الاشتراك",
    unknown: "غير معروف",
    noOwner: "لا يوجد",
    noPlan: "—",
    printHint: "يمكنك طباعة الصفحة الحالية مباشرة",
  },
  en: {
    pageTitle: "Companies",
    pageDescription: "Manage all companies on the platform with a responsive bilingual interface",
    addCompany: "Add Company",
    refresh: "Refresh",
    pdf: "PDF",
    excel: "Excel",
    searchTitle: "Search & Filter",
    searchPlaceholder: "Search by company name...",
    searchHint: "You can instantly filter by company name",
    companiesList: "Companies List",
    company: "Company",
    owner: "Owner",
    plan: "Plan",
    users: "Users",
    status: "Status",
    created: "Created Date",
    actions: "Actions",
    manageCompany: "Manage Company",
    view: "View",
    active: "Active",
    disabled: "Disabled",
    loadingCompanies: "Loading companies...",
    noCompaniesFound: "No matching companies found",
    failedLoad: "Failed to load companies",
    failedUpdate: "Failed to update company status",
    serverUpdateError: "Server error while updating company status",
    statusUpdated: "Company status updated successfully",
    exportedSuccessfully: "Companies exported successfully",
    totalCompanies: "Total Companies",
    activeCompanies: "Active Companies",
    disabledCompanies: "Disabled Companies",
    subscriptionStatus: "Subscription Status",
    unknown: "Unknown",
    noOwner: "N/A",
    noPlan: "—",
    printHint: "You can print the current page directly",
  },
}

function getCookie(name: string) {
  if (typeof document === "undefined") return null

  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift() || null
  }

  return null
}

function detectLocale(): Locale {
  if (typeof document !== "undefined") {
    const htmlLang = document.documentElement.lang?.toLowerCase().trim() || ""
    if (htmlLang.startsWith("ar")) return "ar"
    if (htmlLang.startsWith("en")) return "en"

    const htmlDir = document.documentElement.dir?.toLowerCase().trim() || ""
    if (htmlDir === "rtl") return "ar"
    if (htmlDir === "ltr") return "en"
  }

  if (typeof navigator !== "undefined") {
    const language = navigator.language?.toLowerCase() || ""
    if (language.startsWith("ar")) return "ar"
  }

  return "en"
}

function getApiBaseUrl() {
  const envBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim()
  if (envBase) {
    return envBase.replace(/\/+$/, "")
  }

  return "http://localhost:8000"
}

function formatNumber(value?: number | string | null) {
  if (value === null || value === undefined || value === "") return "0"

  const numericValue =
    typeof value === "number" ? value : Number(String(value).replace(/,/g, ""))

  if (Number.isNaN(numericValue)) {
    return String(value)
  }

  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
  }).format(numericValue)
}

function formatDate(dateValue?: string | null) {
  if (!dateValue) return "—"

  const date = new Date(dateValue)
  if (Number.isNaN(date.getTime())) return "—"

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")

  return `${year}/${month}/${day}`
}

function downloadCsv(filename: string, rows: string[][]) {
  const csvContent = rows
    .map((row) =>
      row
        .map((cell) => `"${String(cell ?? "").replace(/"/g, '""')}"`)
        .join(",")
    )
    .join("\n")

  const blob = new Blob([`\uFEFF${csvContent}`], {
    type: "text/csv;charset=utf-8;",
  })

  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")

  link.href = url
  link.setAttribute("download", filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function StatusBadge({
  active,
  locale,
}: {
  active: boolean
  locale: Locale
}) {
  const text = active
    ? locale === "ar"
      ? "نشطة"
      : "Active"
    : locale === "ar"
      ? "معطلة"
      : "Disabled"

  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
        active
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-red-200 bg-red-50 text-red-700",
      ].join(" ")}
    >
      {active ? (
        <ShieldCheck className="me-1 h-3.5 w-3.5" />
      ) : (
        <ShieldX className="me-1 h-3.5 w-3.5" />
      )}
      {text}
    </span>
  )
}

export default function SystemCompaniesPage() {
  const router = useRouter()

  const [locale, setLocale] = useState<Locale>("en")
  const [companies, setCompanies] = useState<Company[]>([])
  const [search, setSearch] = useState("")
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [togglingId, setTogglingId] = useState<number | null>(null)

  const apiBaseUrl = getApiBaseUrl()
  const t = translations[locale]
  const isArabic = locale === "ar"
  const dir = isArabic ? "rtl" : "ltr"

  useEffect(() => {
    const applyLocale = () => {
      setLocale(detectLocale())
    }

    applyLocale()

    const htmlElement = document.documentElement
    const observer = new MutationObserver(() => {
      applyLocale()
    })

    observer.observe(htmlElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    window.addEventListener("languagechange", applyLocale)
    window.addEventListener("focus", applyLocale)

    return () => {
      observer.disconnect()
      window.removeEventListener("languagechange", applyLocale)
      window.removeEventListener("focus", applyLocale)
    }
  }, [])

  const loadCompanies = useCallback(
    async (silent = false) => {
      if (silent) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      try {
        const res = await fetch(`${apiBaseUrl}/api/system/companies/list/`, {
          credentials: "include",
          cache: "no-store",
        })

        if (!res.ok) {
          throw new Error(`Failed with status ${res.status}`)
        }

        const data = await res.json()
        setCompanies(Array.isArray(data) ? data : [])
      } catch (error) {
        console.error("Failed loading companies:", error)
        toast.error(translations[detectLocale()].failedLoad)
        setCompanies([])
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [apiBaseUrl]
  )

  useEffect(() => {
    void loadCompanies()
  }, [loadCompanies])

  const toggleCompany = async (id: number) => {
    setTogglingId(id)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        `${apiBaseUrl}/api/system/companies/${id}/toggle-active/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken || "",
          },
        }
      )

      if (!res.ok) {
        toast.error(translations[detectLocale()].failedUpdate)
        return
      }

      setCompanies((prev) =>
        prev.map((company) =>
          company.id === id
            ? { ...company, is_active: !company.is_active }
            : company
        )
      )

      toast.success(translations[detectLocale()].statusUpdated)
    } catch (error) {
      console.error("Toggle error:", error)
      toast.error(translations[detectLocale()].serverUpdateError)
    } finally {
      setTogglingId(null)
    }
  }

  const filteredCompanies = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return companies

    return companies.filter((company) =>
      (company.name || "").toLowerCase().includes(term)
    )
  }, [companies, search])

  const stats = useMemo(() => {
    const total = companies.length
    const active = companies.filter((company) => company.is_active).length
    const disabled = total - active

    return { total, active, disabled }
  }, [companies])

  const exportExcel = () => {
    const currentLocale = detectLocale()
    const currentT = translations[currentLocale]

    const rows = [
      [
        currentT.company,
        currentT.owner,
        currentT.plan,
        currentT.users,
        currentT.status,
        currentT.created,
      ],
      ...filteredCompanies.map((company) => [
        company.name || "—",
        company.owner?.email || currentT.noOwner,
        company.subscription?.plan || currentT.noPlan,
        formatNumber(company.users_count ?? 0),
        company.is_active ? currentT.active : currentT.disabled,
        formatDate(company.created_at),
      ]),
    ]

    downloadCsv("companies.csv", rows)
    toast.success(currentT.exportedSuccessfully)
  }

  const printPDF = () => {
    window.print()
  }

  return (
    <div dir={dir} className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            {t.pageTitle}
          </h1>
          <p className="text-sm text-muted-foreground md:text-base">
            {t.pageDescription}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            className="gap-2"
            onClick={() => router.push("/system/companies/create")}
          >
            <Plus className="h-4 w-4" />
            {t.addCompany}
          </Button>

          <Button
            variant="outline"
            onClick={exportExcel}
            className="gap-2"
          >
            <FileSpreadsheet className="h-4 w-4" />
            {t.excel}
          </Button>

          <Button
            variant="outline"
            onClick={printPDF}
            className="gap-2"
          >
            <FileDown className="h-4 w-4" />
            {t.pdf}
          </Button>

          <Button
            variant="outline"
            onClick={() => void loadCompanies(true)}
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

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                {t.totalCompanies}
              </p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumber(stats.total)}
              </p>
            </div>

            <div className="rounded-2xl border bg-muted/40 p-3">
              <Building2 className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                {t.activeCompanies}
              </p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumber(stats.active)}
              </p>
            </div>

            <div className="rounded-2xl border bg-muted/40 p-3">
              <ShieldCheck className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60 sm:col-span-2 xl:col-span-1">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                {t.disabledCompanies}
              </p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumber(stats.disabled)}
              </p>
            </div>

            <div className="rounded-2xl border bg-muted/40 p-3">
              <ShieldX className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

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
        </CardContent>
      </Card>

      <Card className="hidden border-border/60 lg:block">
        <CardHeader>
          <CardTitle className="text-base md:text-lg">
            {t.companiesList}
          </CardTitle>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-14 text-muted-foreground">
              <Loader2 className="me-2 h-5 w-5 animate-spin" />
              {t.loadingCompanies}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t.company}</TableHead>
                  <TableHead>{t.owner}</TableHead>
                  <TableHead>{t.plan}</TableHead>
                  <TableHead>{t.users}</TableHead>
                  <TableHead>{t.status}</TableHead>
                  <TableHead>{t.created}</TableHead>
                  <TableHead className={isArabic ? "text-left" : "text-right"}>
                    {t.actions}
                  </TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {filteredCompanies.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="py-12 text-center text-muted-foreground"
                    >
                      {t.noCompaniesFound}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredCompanies.map((company) => (
                    <TableRow key={company.id}>
                      <TableCell>
                        <div className="flex items-center gap-2 font-medium">
                          <Building2 className="h-4 w-4 text-muted-foreground" />
                          <span>{company.name}</span>
                        </div>
                      </TableCell>

                      <TableCell>{company.owner?.email || t.noOwner}</TableCell>

                      <TableCell>
                        {company.subscription?.plan || t.noPlan}
                      </TableCell>

                      <TableCell className="tabular-nums">
                        {formatNumber(company.users_count ?? 0)}
                      </TableCell>

                      <TableCell>
                        <StatusBadge active={company.is_active} locale={locale} />
                      </TableCell>

                      <TableCell className="tabular-nums">
                        {formatDate(company.created_at)}
                      </TableCell>

                      <TableCell className={isArabic ? "text-left" : "text-right"}>
                        <div
                          className={[
                            "flex flex-wrap gap-2",
                            isArabic ? "justify-start" : "justify-end",
                          ].join(" ")}
                        >
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => router.push(`/system/companies/${company.id}`)}
                            className="gap-2"
                          >
                            <Building2 className="h-4 w-4" />
                            {t.manageCompany}
                          </Button>

                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => router.push(`/system/companies/${company.id}`)}
                            aria-label={t.view}
                            title={t.view}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>

                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => void toggleCompany(company.id)}
                            disabled={togglingId === company.id}
                            aria-label={t.status}
                            title={t.status}
                          >
                            {togglingId === company.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Power className="h-4 w-4" />
                            )}
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

      <div className="grid gap-4 lg:hidden">
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="text-base md:text-lg">
              {t.companiesList}
            </CardTitle>
          </CardHeader>

          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-14 text-muted-foreground">
                <Loader2 className="me-2 h-5 w-5 animate-spin" />
                {t.loadingCompanies}
              </div>
            ) : filteredCompanies.length === 0 ? (
              <div className="py-10 text-center text-sm text-muted-foreground">
                {t.noCompaniesFound}
              </div>
            ) : (
              <div className="space-y-4">
                {filteredCompanies.map((company) => (
                  <div
                    key={company.id}
                    className="rounded-2xl border border-border/60 bg-background p-4 shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 shrink-0 text-muted-foreground" />
                          <h3 className="truncate font-semibold">
                            {company.name}
                          </h3>
                        </div>

                        <p className="truncate text-sm text-muted-foreground">
                          {company.owner?.email || t.noOwner}
                        </p>
                      </div>

                      <StatusBadge active={company.is_active} locale={locale} />
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <div className="rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">
                          {t.plan}
                        </p>
                        <p className="mt-1 font-medium">
                          {company.subscription?.plan || t.noPlan}
                        </p>
                      </div>

                      <div className="rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">
                          {t.users}
                        </p>
                        <p className="mt-1 flex items-center gap-1 font-medium tabular-nums">
                          <Users className="h-4 w-4 text-muted-foreground" />
                          {formatNumber(company.users_count ?? 0)}
                        </p>
                      </div>

                      <div className="rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">
                          {t.created}
                        </p>
                        <p className="mt-1 font-medium tabular-nums">
                          {formatDate(company.created_at)}
                        </p>
                      </div>

                      <div className="rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">
                          {t.subscriptionStatus}
                        </p>
                        <p className="mt-1 font-medium">
                          {company.subscription?.status || t.unknown}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      <Button
                        variant="outline"
                        className="flex-1 gap-2"
                        onClick={() => router.push(`/system/companies/${company.id}`)}
                      >
                        <Eye className="h-4 w-4" />
                        {t.view}
                      </Button>

                      <Button
                        variant="outline"
                        className="flex-1 gap-2"
                        onClick={() => router.push(`/system/companies/${company.id}`)}
                      >
                        <Building2 className="h-4 w-4" />
                        {t.manageCompany}
                      </Button>

                      <Button
                        variant="outline"
                        className="w-full gap-2 sm:w-auto"
                        onClick={() => void toggleCompany(company.id)}
                        disabled={togglingId === company.id}
                      >
                        {togglingId === company.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Power className="h-4 w-4" />
                        )}
                        {company.is_active ? t.disabled : t.active}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <p className="text-xs text-muted-foreground">
        {t.printHint}
      </p>
    </div>
  )
}