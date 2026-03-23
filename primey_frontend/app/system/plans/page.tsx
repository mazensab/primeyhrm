"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Image from "next/image"
import { toast } from "sonner"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift() ?? null
  }

  return null
}

// ======================================================
// Locale / Direction Helpers
// ======================================================

type Locale = "ar" | "en"
type Direction = "rtl" | "ltr"

function detectLocale(): Locale {
  if (typeof document === "undefined") return "en"

  const htmlLang =
    document.documentElement.lang ||
    document.body.getAttribute("lang") ||
    "en"

  return htmlLang.toLowerCase().startsWith("ar") ? "ar" : "en"
}

function detectDirection(locale: Locale): Direction {
  if (typeof document === "undefined") {
    return locale === "ar" ? "rtl" : "ltr"
  }

  const htmlDir =
    document.documentElement.dir ||
    document.body.getAttribute("dir") ||
    (locale === "ar" ? "rtl" : "ltr")

  return htmlDir === "rtl" ? "rtl" : "ltr"
}

function formatEnglishNumber(value: number | string | null | undefined) {
  const numeric =
    typeof value === "number"
      ? value
      : value === null || value === undefined || value === ""
        ? 0
        : Number(value)

  if (Number.isNaN(numeric)) return "0"

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(numeric)
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
  "biotime",
] as const

// ======================================================
// API Endpoints
// ======================================================

const API_ENDPOINTS = {
  plansAdmin: "/api/system/plans/admin/",
  createPlan: "/api/system/plans/create/",
  updatePlan: (id: number) => `/api/system/plans/${id}/update/`,
} as const

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

interface FormState {
  name: string
  description: string
  price_monthly: string
  price_yearly: string
  max_companies: string
  max_employees: string
  apps: string[]
}

// ======================================================
// i18n Dictionary
// ======================================================

const translations = {
  ar: {
    pageTitle: "خطط الاشتراك",
    pageDescription: "إدارة خطط التسعير والاشتراكات داخل النظام",
    createPlan: "إنشاء خطة",
    editPlan: "تعديل الخطة",
    createPlanTitle: "إنشاء خطة جديدة",
    editPlanTitle: "تعديل الخطة",
    loading: "جاري تحميل الخطط...",
    active: "نشطة",
    disabled: "معطلة",
    perMonth: "/ شهر",
    perYear: "/ سنة",
    monthlyPrice: "السعر الشهري",
    yearlyPrice: "السعر السنوي",
    planName: "اسم الخطة",
    description: "الوصف",
    maxCompanies: "الحد الأقصى للشركات",
    maxEmployees: "الحد الأقصى للموظفين",
    companiesLimit: "حد الشركات",
    employeesLimit: "حد الموظفين",
    companiesUsing: "الشركات المستخدمة",
    applications: "التطبيقات",
    disable: "تعطيل",
    enable: "تفعيل",
    edit: "تعديل",
    saveChanges: "حفظ التعديلات",
    create: "إنشاء",
    noApps: "لا توجد تطبيقات",
    noPlans: "لا توجد خطط حالياً",
    loadFailed: "تعذر تحميل الخطط",
    createSuccess: "تم إنشاء الخطة بنجاح",
    createFailed: "فشل إنشاء الخطة",
    updateSuccess: "تم تحديث الخطة بنجاح",
    updateFailed: "فشل تحديث الخطة",
    toggleSuccessEnabled: "تم تفعيل الخطة بنجاح",
    toggleSuccessDisabled: "تم تعطيل الخطة بنجاح",
    toggleFailed: "فشل تحديث حالة الخطة",
    requiredFields: "يرجى تعبئة جميع الحقول المطلوبة",
    invalidNumbers: "يرجى إدخال قيم رقمية صحيحة",
    actions: "الإجراءات",
  },
  en: {
    pageTitle: "Subscription Plans",
    pageDescription: "Manage system pricing and subscription plans",
    createPlan: "Create Plan",
    editPlan: "Edit Plan",
    createPlanTitle: "Create New Plan",
    editPlanTitle: "Edit Plan",
    loading: "Loading plans...",
    active: "Active",
    disabled: "Disabled",
    perMonth: "/ month",
    perYear: "/ year",
    monthlyPrice: "Monthly Price",
    yearlyPrice: "Yearly Price",
    planName: "Plan Name",
    description: "Description",
    maxCompanies: "Max Companies",
    maxEmployees: "Max Employees",
    companiesLimit: "Companies Limit",
    employeesLimit: "Employees Limit",
    companiesUsing: "Companies Using",
    applications: "Applications",
    disable: "Disable",
    enable: "Enable",
    edit: "Edit",
    saveChanges: "Save Changes",
    create: "Create",
    noApps: "No applications",
    noPlans: "No plans available",
    loadFailed: "Failed to load plans",
    createSuccess: "Plan created successfully",
    createFailed: "Failed to create plan",
    updateSuccess: "Plan updated successfully",
    updateFailed: "Failed to update plan",
    toggleSuccessEnabled: "Plan enabled successfully",
    toggleSuccessDisabled: "Plan disabled successfully",
    toggleFailed: "Failed to update plan status",
    requiredFields: "Please fill in all required fields",
    invalidNumbers: "Please enter valid numeric values",
    actions: "Actions",
  },
} as const

// ======================================================
// Page
// ======================================================

export default function PlansPage() {
  const [locale, setLocale] = useState<Locale>("en")
  const [direction, setDirection] = useState<Direction>("ltr")

  const [plans, setPlans] = useState<Plan[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  const [openCreate, setOpenCreate] = useState(false)
  const [openEdit, setOpenEdit] = useState(false)

  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null)

  const emptyForm: FormState = {
    name: "",
    description: "",
    price_monthly: "",
    price_yearly: "",
    max_companies: "",
    max_employees: "",
    apps: [],
  }

  const [form, setForm] = useState<FormState>(emptyForm)

  const t = translations[locale]

  // ======================================================
  // Sync locale from document
  // ======================================================

  useEffect(() => {
    const syncLocale = () => {
      const nextLocale = detectLocale()
      const nextDirection = detectDirection(nextLocale)

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

    return () => {
      observer.disconnect()
      window.removeEventListener("languagechange", syncLocale)
    }
  }, [])

  // ======================================================
  // App Labels
  // ======================================================

  const appLabels = useMemo(
    () => ({
      employee: locale === "ar" ? "الموظفين" : "Employee",
      attendance: locale === "ar" ? "الحضور" : "Attendance",
      leave: locale === "ar" ? "الإجازات" : "Leave",
      payroll: locale === "ar" ? "الرواتب" : "Payroll",
      performance: locale === "ar" ? "الأداء" : "Performance",
      biotime: locale === "ar" ? "بايوتايم" : "BioTime",
    }),
    [locale]
  )

  // ======================================================
  // Fetch Plans
  // ======================================================

  const fetchPlans = useCallback(async () => {
    try {
      setLoading(true)

      const res = await fetch(API_ENDPOINTS.plansAdmin, {
        method: "GET",
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      const data = await res.json()

      const plansList = Array.isArray(data?.plans)
        ? data.plans
        : Array.isArray(data)
          ? data
          : []

      const mapped = plansList.map((p: Plan) => ({
        ...p,
        companies_count: p.companies_count ?? 0,
        apps: Array.isArray(p.apps) ? p.apps : [],
      }))

      setPlans(mapped)
    } catch (err) {
      console.error("Load plans failed", err)
      toast.error(t.loadFailed)
    } finally {
      setLoading(false)
    }
  }, [t.loadFailed])

  useEffect(() => {
    fetchPlans()
  }, [fetchPlans])

  // ======================================================
  // Validation
  // ======================================================

  function validateCreateForm() {
    if (
      !form.name.trim() ||
      !form.price_monthly.trim() ||
      !form.price_yearly.trim() ||
      !form.max_companies.trim() ||
      !form.max_employees.trim()
    ) {
      toast.error(t.requiredFields)
      return false
    }

    const numericValues = [
      form.price_monthly,
      form.price_yearly,
      form.max_companies,
      form.max_employees,
    ]

    const hasInvalidNumber = numericValues.some((value) => Number.isNaN(Number(value)))

    if (hasInvalidNumber) {
      toast.error(t.invalidNumbers)
      return false
    }

    return true
  }

  function validateEditForm() {
    if (
      !form.price_monthly.trim() ||
      !form.price_yearly.trim() ||
      !form.max_employees.trim()
    ) {
      toast.error(t.requiredFields)
      return false
    }

    const numericValues = [form.price_monthly, form.price_yearly, form.max_employees]

    const hasInvalidNumber = numericValues.some((value) => Number.isNaN(Number(value)))

    if (hasInvalidNumber) {
      toast.error(t.invalidNumbers)
      return false
    }

    return true
  }

  // ======================================================
  // Toggle Plan
  // ======================================================

  async function togglePlan(plan: Plan) {
    try {
      const csrf = getCookie("csrftoken")

      const res = await fetch(API_ENDPOINTS.updatePlan(plan.id), {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf || "",
          Accept: "application/json",
        },
        body: JSON.stringify({
          is_active: !plan.is_active,
        }),
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      await fetchPlans()

      toast.success(
        !plan.is_active ? t.toggleSuccessEnabled : t.toggleSuccessDisabled
      )
    } catch (error) {
      console.error("Toggle failed", error)
      toast.error(t.toggleFailed)
    }
  }

  // ======================================================
  // Toggle App
  // ======================================================

  function toggleApp(app: string) {
    setForm((prev) => {
      const exists = prev.apps.includes(app)

      return {
        ...prev,
        apps: exists ? prev.apps.filter((item) => item !== app) : [...prev.apps, app],
      }
    })
  }

  // ======================================================
  // Create Plan
  // ======================================================

  async function createPlan() {
    if (!validateCreateForm()) return

    try {
      setSubmitting(true)

      const csrf = getCookie("csrftoken")

      const res = await fetch(API_ENDPOINTS.createPlan, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf || "",
          Accept: "application/json",
        },
        body: JSON.stringify({
          ...form,
          price_monthly: Number(form.price_monthly),
          price_yearly: Number(form.price_yearly),
          max_companies: Number(form.max_companies),
          max_employees: Number(form.max_employees),
          apps: form.apps,
        }),
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      setOpenCreate(false)
      setForm(emptyForm)

      await fetchPlans()
      toast.success(t.createSuccess)
    } catch (err) {
      console.error("Create failed", err)
      toast.error(t.createFailed)
    } finally {
      setSubmitting(false)
    }
  }

  // ======================================================
  // Update Plan
  // ======================================================

  async function updatePlan() {
    if (!selectedPlan) return
    if (!validateEditForm()) return

    try {
      setSubmitting(true)

      const csrf = getCookie("csrftoken")

      const res = await fetch(API_ENDPOINTS.updatePlan(selectedPlan.id), {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf || "",
          Accept: "application/json",
        },
        body: JSON.stringify({
          price_monthly: Number(form.price_monthly),
          price_yearly: Number(form.price_yearly),
          max_employees: Number(form.max_employees),
          is_active: selectedPlan.is_active,
        }),
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      setOpenEdit(false)
      setSelectedPlan(null)
      setForm(emptyForm)

      await fetchPlans()
      toast.success(t.updateSuccess)
    } catch (err) {
      console.error("Update failed", err)
      toast.error(t.updateFailed)
    } finally {
      setSubmitting(false)
    }
  }

  // ======================================================
  // UI
  // ======================================================

  if (loading) {
    return (
      <div
        dir={direction}
        className="flex min-h-[40vh] items-center justify-center px-4 py-10"
      >
        <div className="text-center">
          <p className="text-sm text-muted-foreground">{t.loading}</p>
        </div>
      </div>
    )
  }

  return (
    <div dir={direction} className="w-full px-4 py-4 sm:px-6 sm:py-6">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
              {t.pageTitle}
            </h1>
            <p className="text-sm text-muted-foreground sm:text-base">
              {t.pageDescription}
            </p>
          </div>

          <Dialog
            open={openCreate}
            onOpenChange={(open) => {
              setOpenCreate(open)
              if (!open) setForm(emptyForm)
            }}
          >
            <DialogTrigger asChild>
              <Button className="w-full sm:w-auto">{t.createPlan}</Button>
            </DialogTrigger>

            <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
              <DialogHeader>
                <DialogTitle>{t.createPlanTitle}</DialogTitle>
              </DialogHeader>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <Input
                  placeholder={t.planName}
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />

                <Input
                  placeholder={t.description}
                  value={form.description}
                  onChange={(e) =>
                    setForm({ ...form, description: e.target.value })
                  }
                />

                <Input
                  type="number"
                  inputMode="decimal"
                  placeholder={t.monthlyPrice}
                  value={form.price_monthly}
                  onChange={(e) =>
                    setForm({ ...form, price_monthly: e.target.value })
                  }
                />

                <Input
                  type="number"
                  inputMode="decimal"
                  placeholder={t.yearlyPrice}
                  value={form.price_yearly}
                  onChange={(e) =>
                    setForm({ ...form, price_yearly: e.target.value })
                  }
                />

                <Input
                  type="number"
                  inputMode="numeric"
                  placeholder={t.maxCompanies}
                  value={form.max_companies}
                  onChange={(e) =>
                    setForm({ ...form, max_companies: e.target.value })
                  }
                />

                <Input
                  type="number"
                  inputMode="numeric"
                  placeholder={t.maxEmployees}
                  value={form.max_employees}
                  onChange={(e) =>
                    setForm({ ...form, max_employees: e.target.value })
                  }
                />
              </div>

              <div className="space-y-3">
                <div className="text-sm font-medium">{t.applications}</div>

                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {SYSTEM_APPS.map((app) => {
                    const checked = form.apps.includes(app)

                    return (
                      <label
                        key={app}
                        className="flex cursor-pointer items-center justify-between rounded-lg border px-3 py-2 text-sm transition hover:bg-muted/50"
                      >
                        <span>{appLabels[app]}</span>

                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleApp(app)}
                          className="h-4 w-4"
                        />
                      </label>
                    )
                  })}
                </div>
              </div>

              <Button onClick={createPlan} disabled={submitting} className="w-full">
                {submitting ? t.loading : t.create}
              </Button>
            </DialogContent>
          </Dialog>
        </div>

        {/* Empty State */}
        {!plans.length ? (
          <Card>
            <CardContent className="flex min-h-[220px] items-center justify-center">
              <p className="text-sm text-muted-foreground">{t.noPlans}</p>
            </CardContent>
          </Card>
        ) : null}

        {/* Plans Grid */}
        {plans.length ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {plans.map((plan) => (
              <Card key={plan.id} className="h-full">
                <CardHeader className="space-y-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <CardTitle className="text-lg">{plan.name}</CardTitle>

                    {plan.is_active ? (
                      <Badge>{t.active}</Badge>
                    ) : (
                      <Badge variant="destructive">{t.disabled}</Badge>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="space-y-5">
                  {/* Monthly Price */}
                  <div className="flex flex-wrap items-center gap-2 text-2xl font-bold">
                    <Image
                      src="/currency/sar.svg"
                      alt="SAR"
                      width={22}
                      height={22}
                      className="shrink-0"
                    />

                    <span>{formatEnglishNumber(plan.price_monthly ?? 0)}</span>

                    <span className="text-sm font-normal text-muted-foreground">
                      {t.perMonth}
                    </span>
                  </div>

                  {/* Yearly Price */}
                  <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                    <Image
                      src="/currency/sar.svg"
                      alt="SAR"
                      width={16}
                      height={16}
                      className="shrink-0"
                    />

                    <span>{formatEnglishNumber(plan.price_yearly ?? 0)}</span>
                    <span>{t.perYear}</span>
                  </div>

                  {/* Description */}
                  {plan.description ? (
                    <div className="text-sm leading-6 text-muted-foreground">
                      {plan.description}
                    </div>
                  ) : null}

                  {/* Limits */}
                  <div className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-3">
                    <div className="rounded-lg border p-3">
                      <div className="text-muted-foreground">{t.companiesLimit}</div>
                      <div className="mt-1 font-semibold">
                        {formatEnglishNumber(plan.max_companies)}
                      </div>
                    </div>

                    <div className="rounded-lg border p-3">
                      <div className="text-muted-foreground">{t.employeesLimit}</div>
                      <div className="mt-1 font-semibold">
                        {formatEnglishNumber(plan.max_employees)}
                      </div>
                    </div>

                    <div className="rounded-lg border p-3">
                      <div className="text-muted-foreground">{t.companiesUsing}</div>
                      <div className="mt-1 font-semibold">
                        {formatEnglishNumber(plan.companies_count ?? 0)}
                      </div>
                    </div>
                  </div>

                  {/* Apps */}
                  <div className="space-y-2">
                    <div className="text-sm font-medium">{t.applications}</div>

                    <div className="flex flex-wrap gap-2">
                      {plan.apps?.length ? (
                        plan.apps.map((app, index) => (
                          <Badge key={`${plan.id}-${app}-${index}`} variant="secondary">
                            {appLabels[app as keyof typeof appLabels] ?? app}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-sm text-muted-foreground">{t.noApps}</span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    <Button
                      variant="outline"
                      onClick={() => togglePlan(plan)}
                      className="w-full"
                    >
                      {plan.is_active ? t.disable : t.enable}
                    </Button>

                    <Button
                      variant="secondary"
                      className="w-full"
                      onClick={() => {
                        setSelectedPlan(plan)
                        setForm({
                          name: plan.name,
                          description: plan.description || "",
                          price_monthly: String(plan.price_monthly ?? ""),
                          price_yearly: String(plan.price_yearly ?? ""),
                          max_companies: String(plan.max_companies),
                          max_employees: String(plan.max_employees),
                          apps: Array.isArray(plan.apps) ? plan.apps : [],
                        })
                        setOpenEdit(true)
                      }}
                    >
                      {t.edit}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : null}

        {/* Edit Modal */}
        <Dialog
          open={openEdit}
          onOpenChange={(open) => {
            setOpenEdit(open)
            if (!open) {
              setSelectedPlan(null)
              setForm(emptyForm)
            }
          }}
        >
          <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
            <DialogHeader>
              <DialogTitle>{t.editPlanTitle}</DialogTitle>
            </DialogHeader>

            <div className="grid grid-cols-1 gap-4">
              <Input
                type="number"
                inputMode="decimal"
                placeholder={t.monthlyPrice}
                value={form.price_monthly}
                onChange={(e) =>
                  setForm({ ...form, price_monthly: e.target.value })
                }
              />

              <Input
                type="number"
                inputMode="decimal"
                placeholder={t.yearlyPrice}
                value={form.price_yearly}
                onChange={(e) =>
                  setForm({ ...form, price_yearly: e.target.value })
                }
              />

              <Input
                type="number"
                inputMode="numeric"
                placeholder={t.maxEmployees}
                value={form.max_employees}
                onChange={(e) =>
                  setForm({ ...form, max_employees: e.target.value })
                }
              />

              <Button onClick={updatePlan} disabled={submitting} className="w-full">
                {submitting ? t.loading : t.saveChanges}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}