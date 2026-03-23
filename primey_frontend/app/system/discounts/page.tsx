"use client"

import { useEffect, useMemo, useState } from "react"
import {
  Loader2,
  Plus,
  Percent,
  BadgePercent,
  ShieldCheck,
  ShieldX,
  Clock3,
} from "lucide-react"
import { toast } from "sonner"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

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
// API
// ======================================================

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// ======================================================
// Types
// ======================================================

type Locale = "ar" | "en"
type Direction = "rtl" | "ltr"

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

interface DiscountFormState {
  code: string
  type: "percentage" | "fixed"
  value: string
  max_uses: string
  expires_at: string
}

// ======================================================
// Locale
// ======================================================

const translations = {
  ar: {
    pageTitle: "أكواد الخصم",
    createDiscount: "إنشاء خصم",
    createDiscountTitle: "إنشاء كود خصم",
    createDiscountDesc: "أضف كود خصم جديد للمنصة",
    code: "الكود",
    type: "النوع",
    value: "القيمة",
    usage: "الاستخدام",
    expiry: "الانتهاء",
    status: "الحالة",
    actions: "الإجراءات",
    toggle: "تبديل",
    active: "نشط",
    disabled: "معطل",
    percentage: "نسبة %",
    fixed: "مبلغ ثابت",
    discountCode: "كود الخصم",
    discountValue: "قيمة الخصم",
    maxUses: "الحد الأقصى للاستخدام",
    saveDiscount: "حفظ الخصم",
    expiresAt: "تاريخ الانتهاء",
    loading: "جارٍ تحميل الأكواد...",
    empty: "لا توجد أكواد خصم حالياً",
    loadError: "تعذر تحميل أكواد الخصم",
    requiredFields: "الكود والقيمة مطلوبان",
    invalidValue: "أدخل قيمة خصم صحيحة",
    invalidMaxUses: "الحد الأقصى للاستخدام غير صالح",
    createSuccess: "تم إنشاء كود الخصم بنجاح",
    createError: "تعذر إنشاء كود الخصم",
    toggleSuccess: "تم تحديث حالة الخصم بنجاح",
    toggleError: "تعذر تحديث حالة الخصم",
    unlimited: "∞",
    used: "مستخدم",
    tableTitle: "قائمة أكواد الخصم",
    activeCount: "النشطة",
    disabledCount: "المعطلة",
    totalCount: "الإجمالي",
    saveLoading: "جارٍ الحفظ...",
    fixedSuffix: "SAR",
  },
  en: {
    pageTitle: "Discount Codes",
    createDiscount: "Create Discount",
    createDiscountTitle: "Create Discount Code",
    createDiscountDesc: "Add a new discount code for the platform",
    code: "Code",
    type: "Type",
    value: "Value",
    usage: "Usage",
    expiry: "Expiry",
    status: "Status",
    actions: "Actions",
    toggle: "Toggle",
    active: "Active",
    disabled: "Disabled",
    percentage: "Percentage %",
    fixed: "Fixed Amount",
    discountCode: "Discount Code",
    discountValue: "Discount Value",
    maxUses: "Max Uses",
    saveDiscount: "Save Discount",
    expiresAt: "Expiry Date",
    loading: "Loading discounts...",
    empty: "No discount codes found",
    loadError: "Failed to load discounts",
    requiredFields: "Code and value are required",
    invalidValue: "Enter a valid discount value",
    invalidMaxUses: "Max uses is invalid",
    createSuccess: "Discount code created successfully",
    createError: "Failed to create discount code",
    toggleSuccess: "Discount status updated successfully",
    toggleError: "Failed to update discount status",
    unlimited: "∞",
    used: "used",
    tableTitle: "Discount Codes List",
    activeCount: "Active",
    disabledCount: "Disabled",
    totalCount: "Total",
    saveLoading: "Saving...",
    fixedSuffix: "SAR",
  },
} as const

function getDocumentLocale(): Locale {
  if (typeof document === "undefined") return "en"

  const htmlLang = (document.documentElement.lang || "").toLowerCase().trim()
  if (htmlLang.startsWith("ar")) return "ar"
  if (htmlLang.startsWith("en")) return "en"

  const bodyLang = (document.body?.getAttribute("lang") || "").toLowerCase().trim()
  if (bodyLang.startsWith("ar")) return "ar"
  if (bodyLang.startsWith("en")) return "en"

  const dir = (document.documentElement.dir || "").toLowerCase().trim()
  if (dir === "rtl") return "ar"
  if (dir === "ltr") return "en"

  return "en"
}

function getDocumentDirection(locale: Locale): Direction {
  if (typeof document === "undefined") {
    return locale === "ar" ? "rtl" : "ltr"
  }

  const dir = (document.documentElement.dir || "").toLowerCase().trim()
  if (dir === "rtl" || dir === "ltr") return dir as Direction

  return locale === "ar" ? "rtl" : "ltr"
}

// ======================================================
// Helpers
// ======================================================

function getCookie(name: string) {
  if (typeof document === "undefined") return null

  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift() || null
  }

  return null
}

function formatNumberEn(value: number | string | null | undefined): string {
  const num = Number(value || 0)

  if (Number.isNaN(num)) return "0"

  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(num)
}

function formatDateEn(dateValue: string | null | undefined): string {
  if (!dateValue) return "-"

  const parsed = new Date(dateValue)
  if (Number.isNaN(parsed.getTime())) return "-"

  const year = parsed.getFullYear()
  const month = String(parsed.getMonth() + 1).padStart(2, "0")
  const day = String(parsed.getDate()).padStart(2, "0")

  return `${year}/${month}/${day}`
}

function getTypeLabel(type: Discount["type"], locale: Locale) {
  const t = translations[locale]
  return type === "percentage" ? t.percentage : t.fixed
}

function getValueLabel(discount: Discount, locale: Locale) {
  const t = translations[locale]

  if (discount.type === "percentage") {
    return `${formatNumberEn(discount.value)}%`
  }

  return `${formatNumberEn(discount.value)} ${t.fixedSuffix}`
}

function DiscountStatusPill({
  isActive,
  locale,
}: {
  isActive: boolean
  locale: Locale
}) {
  const t = translations[locale]
  const Icon = isActive ? ShieldCheck : ShieldX

  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
        isActive
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-red-200 bg-red-50 text-red-700",
      ].join(" ")}
    >
      <Icon className="me-1 h-3.5 w-3.5" />
      {isActive ? t.active : t.disabled}
    </span>
  )
}

// ======================================================
// Page
// ======================================================

export default function SystemDiscountsPage() {
  const [locale, setLocale] = useState<Locale>("en")
  const [direction, setDirection] = useState<Direction>("ltr")

  const [discounts, setDiscounts] = useState<Discount[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [togglingId, setTogglingId] = useState<number | null>(null)

  const [open, setOpen] = useState(false)

  const [form, setForm] = useState<DiscountFormState>({
    code: "",
    type: "percentage",
    value: "",
    max_uses: "",
    expires_at: "",
  })

  const t = translations[locale]
  const isArabic = locale === "ar"

  // ======================================================
  // Sync Locale / Direction
  // ======================================================

  useEffect(() => {
    const syncLocale = () => {
      const nextLocale = getDocumentLocale()
      const nextDirection = getDocumentDirection(nextLocale)

      setLocale(nextLocale)
      setDirection(nextDirection)
    }

    syncLocale()

    if (typeof document === "undefined") return

    const observer = new MutationObserver(() => {
      syncLocale()
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    window.addEventListener("languagechange", syncLocale)
    window.addEventListener("focus", syncLocale)

    return () => {
      observer.disconnect()
      window.removeEventListener("languagechange", syncLocale)
      window.removeEventListener("focus", syncLocale)
    }
  }, [])

  // ======================================================
  // Fetch
  // ======================================================

  async function fetchDiscounts() {
    try {
      const res = await fetch(`${API}/api/system/discounts/`, {
        credentials: "include",
        cache: "no-store",
      })

      if (!res.ok) {
        throw new Error("failed")
      }

      const data = await res.json()
      setDiscounts(Array.isArray(data?.results) ? data.results : [])
    } catch (error) {
      console.error("Failed to load discounts:", error)
      toast.error(translations[getDocumentLocale()].loadError)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDiscounts()
  }, [])

  // ======================================================
  // Derived
  // ======================================================

  const stats = useMemo(() => {
    const total = discounts.length
    const active = discounts.filter((item) => item.is_active).length
    const disabled = discounts.filter((item) => !item.is_active).length

    return { total, active, disabled }
  }, [discounts])

  // ======================================================
  // Actions
  // ======================================================

  async function createDiscount() {
    const normalizedCode = form.code.trim().toUpperCase()
    const numericValue = Number(form.value)
    const numericMaxUses =
      form.max_uses.trim() === "" ? null : Number(form.max_uses)

    if (!normalizedCode || !form.value.trim()) {
      toast.error(t.requiredFields)
      return
    }

    if (Number.isNaN(numericValue) || numericValue <= 0) {
      toast.error(t.invalidValue)
      return
    }

    if (
      numericMaxUses !== null &&
      (Number.isNaN(numericMaxUses) || numericMaxUses < 0)
    ) {
      toast.error(t.invalidMaxUses)
      return
    }

    try {
      setSubmitting(true)

      const res = await fetch(`${API}/api/system/discounts/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") || "",
        },
        credentials: "include",
        body: JSON.stringify({
          code: normalizedCode,
          discount_type: form.type,
          value: numericValue,
          max_uses: numericMaxUses,
          start_date: new Date().toISOString().split("T")[0],
          end_date: form.expires_at || null,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        toast.error(data?.detail || t.createError)
        return
      }

      toast.success(t.createSuccess)

      setOpen(false)
      setForm({
        code: "",
        type: "percentage",
        value: "",
        max_uses: "",
        expires_at: "",
      })

      await fetchDiscounts()
    } catch (error) {
      console.error("Create discount error:", error)
      toast.error(t.createError)
    } finally {
      setSubmitting(false)
    }
  }

  async function toggleDiscount(id: number) {
    try {
      setTogglingId(id)

      const res = await fetch(`${API}/api/system/discounts/${id}/toggle/`, {
        method: "PATCH",
        headers: {
          "X-CSRFToken": getCookie("csrftoken") || "",
        },
        credentials: "include",
      })

      if (!res.ok) {
        toast.error(t.toggleError)
        return
      }

      toast.success(t.toggleSuccess)
      await fetchDiscounts()
    } catch (error) {
      console.error("Toggle discount error:", error)
      toast.error(t.toggleError)
    } finally {
      setTogglingId(null)
    }
  }

  // ======================================================
  // UI
  // ======================================================

  return (
    <div dir={direction} className="space-y-6">
      {/* ===================================== */}
      {/* Header */}
      {/* ===================================== */}

      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            {t.pageTitle}
          </h1>
        </div>

        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="w-fit gap-2">
              <Plus className="h-4 w-4" />
              {t.createDiscount}
            </Button>
          </DialogTrigger>

          <DialogContent dir={direction} className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>{t.createDiscountTitle}</DialogTitle>
            </DialogHeader>

            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                {t.createDiscountDesc}
              </p>

              <div className="space-y-2">
                <label className="text-sm font-medium">{t.discountCode}</label>
                <Input
                  placeholder={t.discountCode}
                  value={form.code}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      code: e.target.value.toUpperCase(),
                    }))
                  }
                  className="force-en"
                  dir="ltr"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">{t.type}</label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none transition focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50"
                  value={form.type}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      type: e.target.value as "percentage" | "fixed",
                    }))
                  }
                  dir={direction}
                >
                  <option value="percentage">{t.percentage}</option>
                  <option value="fixed">{t.fixed}</option>
                </select>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">{t.discountValue}</label>
                  <Input
                    type="number"
                    placeholder={t.discountValue}
                    value={form.value}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        value: e.target.value,
                      }))
                    }
                    dir="ltr"
                    lang="en"
                    className="force-en"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">{t.maxUses}</label>
                  <Input
                    type="number"
                    placeholder={t.maxUses}
                    value={form.max_uses}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        max_uses: e.target.value,
                      }))
                    }
                    dir="ltr"
                    lang="en"
                    className="force-en"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">{t.expiresAt}</label>
                <Input
                  type="date"
                  value={form.expires_at}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      expires_at: e.target.value,
                    }))
                  }
                  dir="ltr"
                  lang="en"
                  className="force-en"
                />
              </div>

              <Button
                className="w-full gap-2"
                onClick={createDiscount}
                disabled={submitting}
              >
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <BadgePercent className="h-4 w-4" />
                )}
                {submitting ? t.saveLoading : t.saveDiscount}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* ===================================== */}
      {/* Stats */}
      {/* ===================================== */}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.totalCount}</p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumberEn(stats.total)}
              </p>
            </div>

            <div className="rounded-2xl border bg-muted/40 p-3">
              <BadgePercent className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.activeCount}</p>
              <p className="text-3xl font-semibold tabular-nums text-emerald-600">
                {formatNumberEn(stats.active)}
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
              <p className="text-sm text-muted-foreground">{t.disabledCount}</p>
              <p className="text-3xl font-semibold tabular-nums text-rose-600">
                {formatNumberEn(stats.disabled)}
              </p>
            </div>

            <div className="rounded-2xl border bg-muted/40 p-3">
              <ShieldX className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ===================================== */}
      {/* Table */}
      {/* ===================================== */}

      <Card className="border-border/60">
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
          ) : discounts.length === 0 ? (
            <div className="rounded-2xl border border-dashed p-8 text-center text-sm text-muted-foreground">
              {t.empty}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t.code}</TableHead>
                  <TableHead>{t.type}</TableHead>
                  <TableHead>{t.value}</TableHead>
                  <TableHead>{t.usage}</TableHead>
                  <TableHead>{t.expiry}</TableHead>
                  <TableHead>{t.status}</TableHead>
                  <TableHead className={isArabic ? "text-left" : "text-right"}>
                    {t.actions}
                  </TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {discounts.map((discount) => {
                  const usageText = `${formatNumberEn(discount.used_count)} / ${
                    discount.max_uses === null
                      ? t.unlimited
                      : formatNumberEn(discount.max_uses)
                  }`

                  return (
                    <TableRow key={discount.id}>
                      <TableCell className="font-medium force-en" dir="ltr">
                        {discount.code}
                      </TableCell>

                      <TableCell>
                        <div className="inline-flex items-center gap-2">
                          {discount.type === "percentage" ? (
                            <Percent className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <BadgePercent className="h-4 w-4 text-muted-foreground" />
                          )}
                          <span>{getTypeLabel(discount.type, locale)}</span>
                        </div>
                      </TableCell>

                      <TableCell className="force-en" dir="ltr">
                        {getValueLabel(discount, locale)}
                      </TableCell>

                      <TableCell className="force-en" dir="ltr">
                        {usageText}
                      </TableCell>

                      <TableCell className="force-en" dir="ltr">
                        {formatDateEn(discount.end_date)}
                      </TableCell>

                      <TableCell>
                        <DiscountStatusPill
                          isActive={discount.is_active}
                          locale={locale}
                        />
                      </TableCell>

                      <TableCell className={isArabic ? "text-left" : "text-right"}>
                        <div
                          className={[
                            "flex flex-wrap gap-2",
                            isArabic ? "justify-start" : "justify-end",
                          ].join(" ")}
                        >
                          <Button
                            variant="outline"
                            onClick={() => toggleDiscount(discount.id)}
                            disabled={togglingId === discount.id}
                            className="gap-2"
                          >
                            {togglingId === discount.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Clock3 className="h-4 w-4" />
                            )}
                            {t.toggle}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}