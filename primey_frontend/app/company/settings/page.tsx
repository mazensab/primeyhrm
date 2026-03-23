"use client"

import type { ChangeEvent, ReactNode } from "react"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  BadgeCheck,
  Building2,
  FileBadge2,
  Home,
  ImageIcon,
  Info,
  Loader2,
  Mail,
  MapPin,
  Phone,
  RefreshCw,
  Save,
  ShieldCheck,
  Sparkles,
  Settings2,
  Landmark,
  Hash,
  Upload,
  X,
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

function normalizeApiBase(raw?: string) {
  const fallback = "http://localhost:8000"
  return (raw || fallback).replace(/\/$/, "")
}

const API_BASE = normalizeApiBase(process.env.NEXT_PUBLIC_API_URL)
const MAX_LOGO_SIZE_BYTES = 5 * 1024 * 1024
const ALLOWED_LOGO_TYPES = ["image/jpeg", "image/png", "image/webp"]

type Locale = "ar" | "en"
type Direction = "rtl" | "ltr"

type CompanySettingsPayload = {
  id: number | null
  name: string
  email: string
  phone: string
  commercial_number: string
  vat_number: string
  building_number: string
  street: string
  district: string
  city: string
  postal_code: string
  short_address: string
  is_active: boolean
  logo: string | null
}

type SettingsResponse = {
  status: "ok" | "error"
  message?: string
  company?: Partial<CompanySettingsPayload>
}

type Dictionary = {
  settingsBadge: string
  scopeBadge: string
  activeStatus: string
  inactiveStatus: string
  newLogoReady: string
  pageTitle: string
  pageDescription: string
  refresh: string
  reset: string
  saveChanges: string
  loading: string
  companyNameCard: string
  companyStatusCard: string
  profileCompletionCard: string
  internalIdCard: string
  notAddedYet: string
  notAvailable: string
  basicDataTitle: string
  basicDataDesc: string
  companyName: string
  email: string
  phone: string
  shortAddress: string
  nationalAddressTitle: string
  nationalAddressDesc: string
  city: string
  district: string
  street: string
  buildingNumber: string
  postalCode: string
  additionalDetails: string
  generatedAddressHint: string
  officialDataTitle: string
  officialDataDesc: string
  commercialNumber: string
  vatNumber: string
  companyLogoTitle: string
  companyLogoDesc: string
  noLogoTitle: string
  noLogoDesc: string
  chooseLogo: string
  cancelNewLogo: string
  logoRulesTitle: string
  logoTypeRule: string
  logoSizeRule: string
  logoUploadRule: string
  selectedLogoTitle: string
  fileName: string
  fileSize: string
  quickSummaryTitle: string
  quickSummaryDesc: string
  displayName: string
  cityDistrict: string
  emailPhone: string
  commercialVat: string
  changeStatusTitle: string
  changeStatusDesc: string
  currentChanges: string
  unsaved: string
  saved: string
  completionRate: string
  currentStatus: string
  saveCompanySettings: string
  unsupportedLogoType: string
  logoTooLarge: string
  logoSelected: string
  loadFailed: string
  refreshDone: string
  saveFailed: string
  saveSuccess: string
  resetSuccess: string
  fullAddressPlaceholder: string
  placeholderCompanyName: string
  placeholderEmail: string
  placeholderPhone: string
  placeholderShortAddress: string
  placeholderCity: string
  placeholderDistrict: string
  placeholderStreet: string
  placeholderBuildingNumber: string
  placeholderPostalCode: string
  placeholderCommercial: string
  placeholderVat: string
  noData: string
}

const dictionaryMap: Record<Locale, Dictionary> = {
  ar: {
    settingsBadge: "إعدادات الشركة",
    scopeBadge: "نطاق الشركة",
    activeStatus: "نشطة",
    inactiveStatus: "غير نشطة",
    newLogoReady: "شعار جديد جاهز للرفع",
    pageTitle: "إعدادات وبيانات الشركة",
    pageDescription:
      "تحديث بيانات الشركة الأساسية والرسمية والعنوان الوطني بشكل متوافق مع بنية الشركة الحالية في النظام، مع دعم رفع شعار الشركة.",
    refresh: "تحديث",
    reset: "استرجاع",
    saveChanges: "حفظ التغييرات",
    loading: "جاري تحميل إعدادات الشركة...",
    companyNameCard: "اسم الشركة",
    companyStatusCard: "حالة الشركة",
    profileCompletionCard: "اكتمال الملف",
    internalIdCard: "المعرف الداخلي",
    notAddedYet: "غير مضاف بعد",
    notAvailable: "غير متوفر",
    basicDataTitle: "البيانات الأساسية",
    basicDataDesc: "بيانات التواصل الأساسية للشركة داخل النظام.",
    companyName: "اسم الشركة",
    email: "البريد الإلكتروني",
    phone: "الهاتف",
    shortAddress: "العنوان المختصر",
    nationalAddressTitle: "العنوان الوطني",
    nationalAddressDesc: "تفاصيل العنوان التفصيلية للشركة.",
    city: "المدينة",
    district: "الحي",
    street: "الشارع",
    buildingNumber: "رقم المبنى",
    postalCode: "الرمز البريدي",
    additionalDetails: "تفاصيل إضافية",
    generatedAddressHint: "سيتم تكوين وصف مختصر من بيانات العنوان",
    officialDataTitle: "البيانات الرسمية",
    officialDataDesc: "السجل التجاري والرقم الضريبي والبيانات النظامية.",
    commercialNumber: "السجل التجاري",
    vatNumber: "الرقم الضريبي",
    companyLogoTitle: "شعار الشركة",
    companyLogoDesc: "عرض الشعار الحالي القادم من الباكند.",
    noLogoTitle: "لا يوجد شعار مرفوع",
    noLogoDesc: "عند توفر رابط شعار من الباكند سيظهر هنا تلقائيًا.",
    chooseLogo: "اختيار شعار",
    cancelNewLogo: "إلغاء الشعار الجديد",
    logoRulesTitle: "شروط الشعار",
    logoTypeRule: "الصيغ المدعومة: JPG / PNG / WEBP",
    logoSizeRule: "الحد الأقصى للحجم: 5MB",
    logoUploadRule: "سيتم رفع الشعار إلى Google Drive عند الحفظ",
    selectedLogoTitle: "الشعار الجديد المحدد",
    fileName: "الاسم",
    fileSize: "الحجم",
    quickSummaryTitle: "ملخص سريع",
    quickSummaryDesc: "قراءة سريعة لبيانات الشركة الحالية.",
    displayName: "اسم العرض",
    cityDistrict: "المدينة / الحي",
    emailPhone: "البريد / الهاتف",
    commercialVat: "السجل / الضريبة",
    changeStatusTitle: "حالة التعديل",
    changeStatusDesc: "تنبيه سريع حول ما إذا كانت هناك تغييرات غير محفوظة.",
    currentChanges: "التغييرات الحالية",
    unsaved: "غير محفوظة",
    saved: "محفوظ",
    completionRate: "نسبة اكتمال الملف",
    currentStatus: "الحالة الحالية",
    saveCompanySettings: "حفظ إعدادات الشركة",
    unsupportedLogoType: "نوع الشعار غير مدعوم. استخدم JPG أو PNG أو WEBP",
    logoTooLarge: "حجم الشعار كبير جدًا. الحد الأقصى 5MB",
    logoSelected: "تم اختيار الشعار بنجاح",
    loadFailed: "تعذر تحميل إعدادات الشركة",
    refreshDone: "تم تحديث بيانات الإعدادات",
    saveFailed: "تعذر حفظ إعدادات الشركة",
    saveSuccess: "تم حفظ إعدادات الشركة بنجاح",
    resetSuccess: "تم استرجاع القيم الحالية",
    fullAddressPlaceholder: "سيتم تكوين وصف مختصر من بيانات العنوان",
    placeholderCompanyName: "مثال: Primey HR Cloud",
    placeholderEmail: "company@example.com",
    placeholderPhone: "05xxxxxxxx",
    placeholderShortAddress: "العنوان المختصر",
    placeholderCity: "المدينة",
    placeholderDistrict: "الحي",
    placeholderStreet: "اسم الشارع",
    placeholderBuildingNumber: "رقم المبنى",
    placeholderPostalCode: "الرمز البريدي",
    placeholderCommercial: "رقم السجل التجاري",
    placeholderVat: "الرقم الضريبي",
    noData: "—",
  },
  en: {
    settingsBadge: "Company Settings",
    scopeBadge: "Company Scope",
    activeStatus: "Active",
    inactiveStatus: "Inactive",
    newLogoReady: "New logo ready to upload",
    pageTitle: "Company Settings & Profile",
    pageDescription:
      "Update the company core profile, official records, and national address in line with the current company structure in the system, with support for company logo upload.",
    refresh: "Refresh",
    reset: "Reset",
    saveChanges: "Save Changes",
    loading: "Loading company settings...",
    companyNameCard: "Company Name",
    companyStatusCard: "Company Status",
    profileCompletionCard: "Profile Completion",
    internalIdCard: "Internal ID",
    notAddedYet: "Not added yet",
    notAvailable: "Not available",
    basicDataTitle: "Basic Information",
    basicDataDesc: "Primary company contact data inside the system.",
    companyName: "Company Name",
    email: "Email",
    phone: "Phone",
    shortAddress: "Short Address",
    nationalAddressTitle: "National Address",
    nationalAddressDesc: "Detailed company address information.",
    city: "City",
    district: "District",
    street: "Street",
    buildingNumber: "Building Number",
    postalCode: "Postal Code",
    additionalDetails: "Additional Details",
    generatedAddressHint: "A short address summary will be generated from address data",
    officialDataTitle: "Official Information",
    officialDataDesc: "Commercial registration, VAT number, and legal company data.",
    commercialNumber: "Commercial Number",
    vatNumber: "VAT Number",
    companyLogoTitle: "Company Logo",
    companyLogoDesc: "Display the current logo returned by the backend.",
    noLogoTitle: "No logo uploaded",
    noLogoDesc: "When a logo URL is available from the backend, it will appear here automatically.",
    chooseLogo: "Choose Logo",
    cancelNewLogo: "Remove New Logo",
    logoRulesTitle: "Logo Rules",
    logoTypeRule: "Supported formats: JPG / PNG / WEBP",
    logoSizeRule: "Maximum file size: 5MB",
    logoUploadRule: "The logo will be uploaded to Google Drive when saved",
    selectedLogoTitle: "Selected New Logo",
    fileName: "Name",
    fileSize: "Size",
    quickSummaryTitle: "Quick Summary",
    quickSummaryDesc: "A quick snapshot of the current company data.",
    displayName: "Display Name",
    cityDistrict: "City / District",
    emailPhone: "Email / Phone",
    commercialVat: "Commercial / VAT",
    changeStatusTitle: "Change Status",
    changeStatusDesc: "Quick notice about whether there are unsaved changes.",
    currentChanges: "Current Changes",
    unsaved: "Unsaved",
    saved: "Saved",
    completionRate: "Profile Completion",
    currentStatus: "Current Status",
    saveCompanySettings: "Save Company Settings",
    unsupportedLogoType: "Unsupported logo type. Use JPG, PNG, or WEBP",
    logoTooLarge: "Logo file is too large. Maximum size is 5MB",
    logoSelected: "Logo selected successfully",
    loadFailed: "Failed to load company settings",
    refreshDone: "Settings data refreshed successfully",
    saveFailed: "Failed to save company settings",
    saveSuccess: "Company settings saved successfully",
    resetSuccess: "Current values restored successfully",
    fullAddressPlaceholder: "A short summary will be generated from the address data",
    placeholderCompanyName: "Example: Primey HR Cloud",
    placeholderEmail: "company@example.com",
    placeholderPhone: "05xxxxxxxx",
    placeholderShortAddress: "Short address",
    placeholderCity: "City",
    placeholderDistrict: "District",
    placeholderStreet: "Street name",
    placeholderBuildingNumber: "Building number",
    placeholderPostalCode: "Postal code",
    placeholderCommercial: "Commercial number",
    placeholderVat: "VAT number",
    noData: "—",
  },
}

const EMPTY_FORM: CompanySettingsPayload = {
  id: null,
  name: "",
  email: "",
  phone: "",
  commercial_number: "",
  vat_number: "",
  building_number: "",
  street: "",
  district: "",
  city: "",
  postal_code: "",
  short_address: "",
  is_active: false,
  logo: null,
}

function normalizeCompany(
  data?: Partial<CompanySettingsPayload>
): CompanySettingsPayload {
  return {
    id: data?.id ?? null,
    name: data?.name ?? "",
    email: data?.email ?? "",
    phone: data?.phone ?? "",
    commercial_number: data?.commercial_number ?? "",
    vat_number: data?.vat_number ?? "",
    building_number: data?.building_number ?? "",
    street: data?.street ?? "",
    district: data?.district ?? "",
    city: data?.city ?? "",
    postal_code: data?.postal_code ?? "",
    short_address: data?.short_address ?? "",
    is_active: data?.is_active ?? false,
    logo: data?.logo ?? null,
  }
}

function getCsrfToken(): string {
  if (typeof document === "undefined") return ""
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return match?.[1] || ""
}

function detectLocaleFromDocument(): Locale {
  if (typeof document === "undefined") return "ar"
  const lang = (document.documentElement.lang || "ar").toLowerCase()
  return lang.startsWith("ar") ? "ar" : "en"
}

function detectDirectionFromDocument(): Direction {
  if (typeof document === "undefined") return "rtl"
  const dir = (document.documentElement.dir || "rtl").toLowerCase()
  return dir === "ltr" ? "ltr" : "rtl"
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
    maximumFractionDigits: 0,
  }).format(value || 0)
}

function formatPercent(value: number) {
  return `${new Intl.NumberFormat("en-US", {
    useGrouping: false,
    maximumFractionDigits: 0,
  }).format(value || 0)}%`
}

function formatFileSize(size: number) {
  return `${new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    useGrouping: false,
  }).format(size / 1024 / 1024)} MB`
}

function SummaryCard({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 font-semibold break-words">{value}</p>
    </div>
  )
}

function StatCard({
  title,
  value,
  icon,
}: {
  title: string
  value: string
  icon: ReactNode
}) {
  return (
    <Card className="rounded-2xl border-border/60 shadow-sm">
      <CardContent className="flex items-center justify-between gap-3 p-5">
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="mt-1 truncate text-base font-semibold">{value}</p>
        </div>
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-border/60 bg-background">
          {icon}
        </div>
      </CardContent>
    </Card>
  )
}

export default function CompanySettingsPage() {
  const [form, setForm] = useState<CompanySettingsPayload>(EMPTY_FORM)
  const [initialForm, setInitialForm] = useState<CompanySettingsPayload>(EMPTY_FORM)

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [saving, setSaving] = useState(false)

  const [selectedLogoFile, setSelectedLogoFile] = useState<File | null>(null)
  const [logoPreviewUrl, setLogoPreviewUrl] = useState<string | null>(null)
  const [logoLoadError, setLogoLoadError] = useState(false)

  const [locale, setLocale] = useState<Locale>("ar")
  const [direction, setDirection] = useState<Direction>("rtl")

  const logoInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    const updateLanguageState = () => {
      setLocale(detectLocaleFromDocument())
      setDirection(detectDirectionFromDocument())
    }

    updateLanguageState()

    if (typeof document === "undefined") return

    const observer = new MutationObserver(() => {
      updateLanguageState()
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    return () => observer.disconnect()
  }, [])

  const t = dictionaryMap[locale]

  const hasTextChanges = useMemo(() => {
    return JSON.stringify(form) !== JSON.stringify(initialForm)
  }, [form, initialForm])

  const hasChanges = useMemo(() => {
    return hasTextChanges || !!selectedLogoFile
  }, [hasTextChanges, selectedLogoFile])

  const filledCount = useMemo(() => {
    const values = [
      form.name,
      form.email,
      form.phone,
      form.commercial_number,
      form.vat_number,
      form.building_number,
      form.street,
      form.district,
      form.city,
      form.postal_code,
      form.short_address,
    ]
    return values.filter((value) => String(value || "").trim()).length
  }, [form])

  const profileCompletion = useMemo(() => {
    const total = 11
    return Math.min(100, Math.round((filledCount / total) * 100))
  }, [filledCount])

  const companyStatusLabel = useMemo(() => {
    return form.is_active ? t.activeStatus : t.inactiveStatus
  }, [form.is_active, t.activeStatus, t.inactiveStatus])

  const displayedLogo = useMemo(() => {
    if (logoLoadError) return null
    return logoPreviewUrl || form.logo || null
  }, [logoPreviewUrl, form.logo, logoLoadError])

  const generatedAddress = useMemo(() => {
    return [form.city, form.district, form.street, form.building_number]
      .filter(Boolean)
      .join(" - ")
  }, [form.city, form.district, form.street, form.building_number])

  const cleanupPreview = useCallback((previewUrl?: string | null) => {
    if (previewUrl && previewUrl.startsWith("blob:")) {
      URL.revokeObjectURL(previewUrl)
    }
  }, [])

  const handleChange = useCallback(
    (field: keyof CompanySettingsPayload, value: string) => {
      setForm((prev) => ({
        ...prev,
        [field]: value,
      }))
    },
    []
  )

  const clearLogoSelection = useCallback(() => {
    setLogoPreviewUrl((prev) => {
      if (prev && prev.startsWith("blob:")) {
        URL.revokeObjectURL(prev)
      }
      return null
    })

    setSelectedLogoFile(null)
    setLogoLoadError(false)

    if (logoInputRef.current) {
      logoInputRef.current.value = ""
    }
  }, [])

  const handleLogoSelect = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file) return

      if (!ALLOWED_LOGO_TYPES.includes(file.type)) {
        toast.error(t.unsupportedLogoType)
        if (logoInputRef.current) {
          logoInputRef.current.value = ""
        }
        return
      }

      if (file.size > MAX_LOGO_SIZE_BYTES) {
        toast.error(t.logoTooLarge)
        if (logoInputRef.current) {
          logoInputRef.current.value = ""
        }
        return
      }

      setLogoPreviewUrl((prev) => {
        cleanupPreview(prev)
        return URL.createObjectURL(file)
      })

      setSelectedLogoFile(file)
      setLogoLoadError(false)

      toast.success(t.logoSelected)
    },
    [cleanupPreview, t.logoSelected, t.logoTooLarge, t.unsupportedLogoType]
  )

  const fetchSettings = useCallback(
    async (showToast = false) => {
      try {
        setRefreshing(true)
        setLogoLoadError(false)

        const response = await fetch(`${API_BASE}/api/company/settings/`, {
          method: "GET",
          credentials: "include",
          headers: {
            Accept: "application/json",
          },
          cache: "no-store",
        })

        const data: SettingsResponse = await response.json()

        if (!response.ok || data.status !== "ok") {
          throw new Error(data.message || t.loadFailed)
        }

        const normalized = normalizeCompany(data.company)

        setForm(normalized)
        setInitialForm(normalized)
        clearLogoSelection()

        if (showToast) {
          toast.success(t.refreshDone)
        }
      } catch (error) {
        console.error("Failed to load company settings:", error)
        toast.error(error instanceof Error ? error.message : t.loadFailed)
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [clearLogoSelection, t.loadFailed, t.refreshDone]
  )

  useEffect(() => {
    fetchSettings(false)
  }, [fetchSettings])

  useEffect(() => {
    return () => {
      cleanupPreview(logoPreviewUrl)
    }
  }, [cleanupPreview, logoPreviewUrl])

  const handleSave = useCallback(async () => {
    try {
      setSaving(true)
      setLogoLoadError(false)

      const csrfToken = getCsrfToken()

      const formData = new FormData()
      formData.append("name", form.name)
      formData.append("email", form.email)
      formData.append("phone", form.phone)
      formData.append("commercial_number", form.commercial_number)
      formData.append("vat_number", form.vat_number)
      formData.append("building_number", form.building_number)
      formData.append("street", form.street)
      formData.append("district", form.district)
      formData.append("city", form.city)
      formData.append("postal_code", form.postal_code)
      formData.append("short_address", form.short_address)

      if (selectedLogoFile) {
        formData.append("logo", selectedLogoFile)
      }

      const response = await fetch(`${API_BASE}/api/company/settings/update/`, {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
        body: formData,
      })

      const data: SettingsResponse = await response.json()

      if (!response.ok || data.status !== "ok") {
        throw new Error(data.message || t.saveFailed)
      }

      const normalized = normalizeCompany(data.company)
      setForm(normalized)
      setInitialForm(normalized)
      clearLogoSelection()

      toast.success(t.saveSuccess)
    } catch (error) {
      console.error("Failed to save company settings:", error)
      toast.error(error instanceof Error ? error.message : t.saveFailed)
    } finally {
      setSaving(false)
    }
  }, [form, clearLogoSelection, selectedLogoFile, t.saveFailed, t.saveSuccess])

  const handleReset = useCallback(() => {
    setForm(initialForm)
    clearLogoSelection()
    toast.success(t.resetSuccess)
  }, [initialForm, clearLogoSelection, t.resetSuccess])

  if (loading) {
    return (
      <div className="min-h-screen bg-background" dir={direction}>
        <div className="mx-auto w-full max-w-7xl p-4 md:p-6">
          <div className="flex min-h-[60vh] items-center justify-center">
            <div className="flex items-center gap-3 rounded-2xl border border-border/60 bg-card px-5 py-4 shadow-sm">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-sm font-medium text-muted-foreground">
                {t.loading}
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background" dir={direction}>
      <div className="mx-auto w-full max-w-7xl space-y-6 p-4 md:p-6">
        {/* Header */}
        <Card className="overflow-hidden rounded-2xl border-border/60 shadow-sm">
          <div className="h-1 w-full bg-primary" />
          <CardHeader className="pb-4">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge className="rounded-full px-3 py-1 text-xs">
                    <Settings2 className="h-3.5 w-3.5" />
                    <span>{t.settingsBadge}</span>
                  </Badge>

                  <Badge
                    variant="secondary"
                    className="rounded-full px-3 py-1 text-xs"
                  >
                    <ShieldCheck className="h-3.5 w-3.5" />
                    <span>{t.scopeBadge}</span>
                  </Badge>

                  <Badge
                    variant="outline"
                    className="rounded-full px-3 py-1 text-xs"
                  >
                    <BadgeCheck className="h-3.5 w-3.5" />
                    <span>{companyStatusLabel}</span>
                  </Badge>

                  {selectedLogoFile ? (
                    <Badge
                      variant="secondary"
                      className="rounded-full px-3 py-1 text-xs"
                    >
                      <Upload className="h-3.5 w-3.5" />
                      <span>{t.newLogoReady}</span>
                    </Badge>
                  ) : null}
                </div>

                <div>
                  <CardTitle className="text-2xl font-bold tracking-tight">
                    {t.pageTitle}
                  </CardTitle>
                  <CardDescription className="mt-2 max-w-3xl text-sm leading-6">
                    {t.pageDescription}
                  </CardDescription>
                </div>
              </div>

              <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:flex-wrap xl:justify-end">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fetchSettings(true)}
                  disabled={refreshing || saving}
                  className="h-11 rounded-xl"
                >
                  {refreshing ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  <span>{t.refresh}</span>
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  onClick={handleReset}
                  disabled={!hasChanges || saving}
                  className="h-11 rounded-xl"
                >
                  <span>{t.reset}</span>
                </Button>

                <Button
                  type="button"
                  onClick={handleSave}
                  disabled={saving || !hasChanges}
                  className="h-11 rounded-xl"
                >
                  {saving ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  <span>{t.saveChanges}</span>
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title={t.companyNameCard}
            value={form.name || t.notAddedYet}
            icon={<Building2 className="h-5 w-5" />}
          />

          <StatCard
            title={t.companyStatusCard}
            value={companyStatusLabel}
            icon={<ShieldCheck className="h-5 w-5" />}
          />

          <StatCard
            title={t.profileCompletionCard}
            value={formatPercent(profileCompletion)}
            icon={<Sparkles className="h-5 w-5" />}
          />

          <StatCard
            title={t.internalIdCard}
            value={form.id ? `#${formatNumber(form.id)}` : t.notAvailable}
            icon={<Info className="h-5 w-5" />}
          />
        </div>

        {/* Main Grid */}
        <div className="grid gap-6 xl:grid-cols-3">
          {/* Left Content */}
          <div className="space-y-6 xl:col-span-2">
            <Card className="rounded-2xl border-border/60 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Building2 className="h-5 w-5" />
                  {t.basicDataTitle}
                </CardTitle>
                <CardDescription>{t.basicDataDesc}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-6">
                <div className="grid gap-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="name">{t.companyName}</Label>
                    <div className="relative">
                      <Building2
                        className={cn(
                          "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                          direction === "rtl" ? "right-3" : "left-3"
                        )}
                      />
                      <Input
                        id="name"
                        value={form.name}
                        onChange={(e) => handleChange("name", e.target.value)}
                        placeholder={t.placeholderCompanyName}
                        className={cn(
                          "h-11 rounded-xl",
                          direction === "rtl" ? "pe-10" : "ps-10"
                        )}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">{t.email}</Label>
                    <div className="relative">
                      <Mail
                        className={cn(
                          "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                          direction === "rtl" ? "right-3" : "left-3"
                        )}
                      />
                      <Input
                        id="email"
                        type="email"
                        dir="ltr"
                        value={form.email}
                        onChange={(e) => handleChange("email", e.target.value)}
                        placeholder={t.placeholderEmail}
                        className={cn(
                          "h-11 rounded-xl",
                          direction === "rtl" ? "pe-10" : "ps-10"
                        )}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone">{t.phone}</Label>
                    <div className="relative">
                      <Phone
                        className={cn(
                          "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                          direction === "rtl" ? "right-3" : "left-3"
                        )}
                      />
                      <Input
                        id="phone"
                        dir="ltr"
                        value={form.phone}
                        onChange={(e) => handleChange("phone", e.target.value)}
                        placeholder={t.placeholderPhone}
                        className={cn(
                          "h-11 rounded-xl",
                          direction === "rtl" ? "pe-10" : "ps-10"
                        )}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="short_address">{t.shortAddress}</Label>
                    <div className="relative">
                      <MapPin
                        className={cn(
                          "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                          direction === "rtl" ? "right-3" : "left-3"
                        )}
                      />
                      <Input
                        id="short_address"
                        value={form.short_address}
                        onChange={(e) =>
                          handleChange("short_address", e.target.value)
                        }
                        placeholder={t.placeholderShortAddress}
                        className={cn(
                          "h-11 rounded-xl",
                          direction === "rtl" ? "pe-10" : "ps-10"
                        )}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-border/60 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <MapPin className="h-5 w-5" />
                  {t.nationalAddressTitle}
                </CardTitle>
                <CardDescription>{t.nationalAddressDesc}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-6">
                <div className="grid gap-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="city">{t.city}</Label>
                    <div className="relative">
                      <MapPin
                        className={cn(
                          "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                          direction === "rtl" ? "right-3" : "left-3"
                        )}
                      />
                      <Input
                        id="city"
                        value={form.city}
                        onChange={(e) => handleChange("city", e.target.value)}
                        placeholder={t.placeholderCity}
                        className={cn(
                          "h-11 rounded-xl",
                          direction === "rtl" ? "pe-10" : "ps-10"
                        )}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="district">{t.district}</Label>
                    <div className="relative">
                      <Home
                        className={cn(
                          "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                          direction === "rtl" ? "right-3" : "left-3"
                        )}
                      />
                      <Input
                        id="district"
                        value={form.district}
                        onChange={(e) =>
                          handleChange("district", e.target.value)
                        }
                        placeholder={t.placeholderDistrict}
                        className={cn(
                          "h-11 rounded-xl",
                          direction === "rtl" ? "pe-10" : "ps-10"
                        )}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="street">{t.street}</Label>
                    <div className="relative">
                      <MapPin
                        className={cn(
                          "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                          direction === "rtl" ? "right-3" : "left-3"
                        )}
                      />
                      <Input
                        id="street"
                        value={form.street}
                        onChange={(e) => handleChange("street", e.target.value)}
                        placeholder={t.placeholderStreet}
                        className={cn(
                          "h-11 rounded-xl",
                          direction === "rtl" ? "pe-10" : "ps-10"
                        )}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="building_number">{t.buildingNumber}</Label>
                    <div className="relative">
                      <Hash
                        className={cn(
                          "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                          direction === "rtl" ? "right-3" : "left-3"
                        )}
                      />
                      <Input
                        id="building_number"
                        dir="ltr"
                        value={form.building_number}
                        onChange={(e) =>
                          handleChange("building_number", e.target.value)
                        }
                        placeholder={t.placeholderBuildingNumber}
                        className={cn(
                          "h-11 rounded-xl",
                          direction === "rtl" ? "pe-10" : "ps-10"
                        )}
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="postal_code">{t.postalCode}</Label>
                  <div className="relative">
                    <Mail
                      className={cn(
                        "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                        direction === "rtl" ? "right-3" : "left-3"
                      )}
                    />
                    <Input
                      id="postal_code"
                      dir="ltr"
                      value={form.postal_code}
                      onChange={(e) =>
                        handleChange("postal_code", e.target.value)
                      }
                      placeholder={t.placeholderPostalCode}
                      className={cn(
                        "h-11 rounded-xl",
                        direction === "rtl" ? "pe-10" : "ps-10"
                      )}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="full_address">{t.additionalDetails}</Label>
                  <Textarea
                    id="full_address"
                    value={generatedAddress}
                    readOnly
                    placeholder={t.fullAddressPlaceholder}
                    className="min-h-[120px] rounded-xl"
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-border/60 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Landmark className="h-5 w-5" />
                  {t.officialDataTitle}
                </CardTitle>
                <CardDescription>{t.officialDataDesc}</CardDescription>
              </CardHeader>

              <CardContent>
                <div className="grid gap-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="commercial_number">{t.commercialNumber}</Label>
                    <div className="relative">
                      <FileBadge2
                        className={cn(
                          "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                          direction === "rtl" ? "right-3" : "left-3"
                        )}
                      />
                      <Input
                        id="commercial_number"
                        dir="ltr"
                        value={form.commercial_number}
                        onChange={(e) =>
                          handleChange("commercial_number", e.target.value)
                        }
                        placeholder={t.placeholderCommercial}
                        className={cn(
                          "h-11 rounded-xl",
                          direction === "rtl" ? "pe-10" : "ps-10"
                        )}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="vat_number">{t.vatNumber}</Label>
                    <div className="relative">
                      <FileBadge2
                        className={cn(
                          "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                          direction === "rtl" ? "right-3" : "left-3"
                        )}
                      />
                      <Input
                        id="vat_number"
                        dir="ltr"
                        value={form.vat_number}
                        onChange={(e) =>
                          handleChange("vat_number", e.target.value)
                        }
                        placeholder={t.placeholderVat}
                        className={cn(
                          "h-11 rounded-xl",
                          direction === "rtl" ? "pe-10" : "ps-10"
                        )}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            <Card className="rounded-2xl border-border/60 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <ImageIcon className="h-5 w-5" />
                  {t.companyLogoTitle}
                </CardTitle>
                <CardDescription>{t.companyLogoDesc}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="flex min-h-[240px] items-center justify-center rounded-2xl border border-dashed border-border/70 bg-muted/20 p-6">
                  {displayedLogo ? (
                    <div className="flex w-full items-center justify-center">
                      <img
                        src={displayedLogo}
                        alt="Company Logo"
                        className="max-h-28 w-auto max-w-[220px] object-contain"
                        onError={() => setLogoLoadError(true)}
                      />
                    </div>
                  ) : (
                    <div className="space-y-3 text-center">
                      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-border/60 bg-background">
                        <ImageIcon className="h-6 w-6 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="font-medium">{t.noLogoTitle}</p>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {t.noLogoDesc}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                <input
                  ref={logoInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  onChange={handleLogoSelect}
                />

                <div className="grid gap-3 sm:grid-cols-2">
                  <Button
                    type="button"
                    variant="outline"
                    className="h-11 rounded-xl"
                    onClick={() => logoInputRef.current?.click()}
                    disabled={saving}
                  >
                    <Upload className="h-4 w-4" />
                    <span>{t.chooseLogo}</span>
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    className="h-11 rounded-xl"
                    onClick={clearLogoSelection}
                    disabled={saving || (!selectedLogoFile && !logoPreviewUrl)}
                  >
                    <X className="h-4 w-4" />
                    <span>{t.cancelNewLogo}</span>
                  </Button>
                </div>

                <div className="rounded-2xl border border-border/60 bg-muted/20 p-4 text-sm text-muted-foreground">
                  <div className="font-medium text-foreground">{t.logoRulesTitle}</div>
                  <div className="mt-2 space-y-1">
                    <p>• {t.logoTypeRule}</p>
                    <p>• {t.logoSizeRule}</p>
                    <p>• {t.logoUploadRule}</p>
                  </div>
                </div>

                {selectedLogoFile ? (
                  <div className="rounded-2xl border border-dashed border-primary/40 bg-primary/5 p-4 text-sm">
                    <div className="font-medium text-foreground">
                      {t.selectedLogoTitle}
                    </div>
                    <div className="mt-2 space-y-1 text-muted-foreground">
                      <p>
                        {t.fileName}: <span dir="ltr">{selectedLogoFile.name}</span>
                      </p>
                      <p>
                        {t.fileSize}:{" "}
                        <span dir="ltr">{formatFileSize(selectedLogoFile.size)}</span>
                      </p>
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-border/60 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">{t.quickSummaryTitle}</CardTitle>
                <CardDescription>{t.quickSummaryDesc}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                <SummaryCard
                  label={t.displayName}
                  value={form.name || t.noData}
                />

                <SummaryCard
                  label={t.cityDistrict}
                  value={
                    [form.city, form.district].filter(Boolean).join(" — ") || t.noData
                  }
                />

                <SummaryCard
                  label={t.emailPhone}
                  value={form.email || form.phone || t.noData}
                />

                <SummaryCard
                  label={t.commercialVat}
                  value={form.commercial_number || form.vat_number || t.noData}
                />
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-border/60 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">{t.changeStatusTitle}</CardTitle>
                <CardDescription>{t.changeStatusDesc}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="flex items-center justify-between gap-3 rounded-2xl border border-border/60 p-4">
                  <span className="text-sm font-medium">{t.currentChanges}</span>
                  <Badge
                    variant={hasChanges ? "default" : "secondary"}
                    className="rounded-full"
                  >
                    {hasChanges ? t.unsaved : t.saved}
                  </Badge>
                </div>

                <Separator />

                <div className="flex items-center justify-between gap-3 rounded-2xl border border-border/60 p-4">
                  <span className="text-sm font-medium">{t.completionRate}</span>
                  <Badge variant="outline" className="rounded-full" dir="ltr">
                    {formatPercent(profileCompletion)}
                  </Badge>
                </div>

                <div className="flex items-center justify-between gap-3 rounded-2xl border border-border/60 p-4">
                  <span className="text-sm font-medium">{t.currentStatus}</span>
                  <Badge
                    variant={form.is_active ? "default" : "secondary"}
                    className="rounded-full"
                  >
                    {companyStatusLabel}
                  </Badge>
                </div>

                <div className="pt-2">
                  <Button
                    type="button"
                    onClick={handleSave}
                    disabled={saving || !hasChanges}
                    className="h-11 w-full rounded-xl"
                  >
                    {saving ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    <span>{t.saveCompanySettings}</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}