"use client"

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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const MAX_LOGO_SIZE_BYTES = 5 * 1024 * 1024
const ALLOWED_LOGO_TYPES = ["image/jpeg", "image/png", "image/webp"]

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

export default function CompanySettingsPage() {
  const [form, setForm] = useState<CompanySettingsPayload>(EMPTY_FORM)
  const [initialForm, setInitialForm] = useState<CompanySettingsPayload>(EMPTY_FORM)

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [saving, setSaving] = useState(false)

  const [selectedLogoFile, setSelectedLogoFile] = useState<File | null>(null)
  const [logoPreviewUrl, setLogoPreviewUrl] = useState<string | null>(null)
  const [logoLoadError, setLogoLoadError] = useState(false)

  const logoInputRef = useRef<HTMLInputElement | null>(null)

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
    return form.is_active ? "نشطة" : "غير نشطة"
  }, [form.is_active])

  const displayedLogo = useMemo(() => {
    if (logoLoadError) return null
    return logoPreviewUrl || form.logo || null
  }, [logoPreviewUrl, form.logo, logoLoadError])

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
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file) return

      if (!ALLOWED_LOGO_TYPES.includes(file.type)) {
        toast.error("نوع الشعار غير مدعوم. استخدم JPG أو PNG أو WEBP")
        if (logoInputRef.current) {
          logoInputRef.current.value = ""
        }
        return
      }

      if (file.size > MAX_LOGO_SIZE_BYTES) {
        toast.error("حجم الشعار كبير جدًا. الحد الأقصى 5MB")
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

      toast.success("تم اختيار الشعار بنجاح")
    },
    [cleanupPreview]
  )

  const fetchSettings = useCallback(async (showToast = false) => {
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
        throw new Error(data.message || "تعذر تحميل إعدادات الشركة")
      }

      const normalized = normalizeCompany(data.company)

      setForm(normalized)
      setInitialForm(normalized)
      clearLogoSelection()

      if (showToast) {
        toast.success("تم تحديث بيانات الإعدادات")
      }
    } catch (error) {
      console.error("Failed to load company settings:", error)
      toast.error(
        error instanceof Error ? error.message : "تعذر تحميل إعدادات الشركة"
      )
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [clearLogoSelection])

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
        throw new Error(data.message || "تعذر حفظ إعدادات الشركة")
      }

      const normalized = normalizeCompany(data.company)
      setForm(normalized)
      setInitialForm(normalized)
      clearLogoSelection()

      toast.success("تم حفظ إعدادات الشركة بنجاح")
    } catch (error) {
      console.error("Failed to save company settings:", error)
      toast.error(
        error instanceof Error ? error.message : "تعذر حفظ إعدادات الشركة"
      )
    } finally {
      setSaving(false)
    }
  }, [form, clearLogoSelection, selectedLogoFile])

  const handleReset = useCallback(() => {
    setForm(initialForm)
    clearLogoSelection()
    toast.success("تم استرجاع القيم الحالية")
  }, [initialForm, clearLogoSelection])

  if (loading) {
    return (
      <div className="min-h-screen bg-background" dir="rtl">
        <div className="mx-auto w-full max-w-7xl p-6 md:p-8">
          <div className="flex min-h-[60vh] items-center justify-center">
            <div className="flex items-center gap-3 rounded-2xl border bg-card px-5 py-4 shadow-sm">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-sm font-medium text-muted-foreground">
                جاري تحميل إعدادات الشركة...
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background" dir="rtl">
      <div className="mx-auto w-full max-w-7xl space-y-6 p-6 md:p-8">
        <Card className="overflow-hidden border-border/60 shadow-sm">
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary/70 via-primary to-primary/70" />
          <CardHeader className="pb-4">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge className="rounded-full px-3 py-1 text-xs">
                    <Settings2 className="me-1 h-3.5 w-3.5" />
                    إعدادات الشركة
                  </Badge>
                  <Badge
                    variant="secondary"
                    className="rounded-full px-3 py-1 text-xs"
                  >
                    <ShieldCheck className="me-1 h-3.5 w-3.5" />
                    Company Scope
                  </Badge>
                  <Badge
                    variant="outline"
                    className="rounded-full px-3 py-1 text-xs"
                  >
                    <BadgeCheck className="me-1 h-3.5 w-3.5" />
                    {companyStatusLabel}
                  </Badge>
                  {selectedLogoFile ? (
                    <Badge
                      variant="secondary"
                      className="rounded-full px-3 py-1 text-xs"
                    >
                      <Upload className="me-1 h-3.5 w-3.5" />
                      شعار جديد جاهز للرفع
                    </Badge>
                  ) : null}
                </div>

                <div>
                  <CardTitle className="text-2xl font-bold tracking-tight">
                    إعدادات وبيانات الشركة
                  </CardTitle>
                  <CardDescription className="mt-2 max-w-2xl text-sm leading-6">
                    تحديث بيانات الشركة الأساسية والرسمية والعنوان الوطني بشكل
                    متوافق مع بنية الشركة الحالية في النظام، مع دعم رفع شعار
                    الشركة.
                  </CardDescription>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fetchSettings(true)}
                  disabled={refreshing || saving}
                  className="rounded-xl"
                >
                  {refreshing ? (
                    <Loader2 className="me-2 h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="me-2 h-4 w-4" />
                  )}
                  تحديث
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  onClick={handleReset}
                  disabled={!hasChanges || saving}
                  className="rounded-xl"
                >
                  استرجاع
                </Button>

                <Button
                  type="button"
                  onClick={handleSave}
                  disabled={saving || !hasChanges}
                  className="rounded-xl"
                >
                  {saving ? (
                    <Loader2 className="me-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="me-2 h-4 w-4" />
                  )}
                  حفظ التغييرات
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card className="border-border/60 shadow-sm">
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-sm text-muted-foreground">اسم الشركة</p>
                <p className="mt-1 text-base font-semibold">
                  {form.name || "غير مضاف بعد"}
                </p>
              </div>
              <div className="rounded-2xl border bg-background p-3">
                <Building2 className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/60 shadow-sm">
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-sm text-muted-foreground">حالة الشركة</p>
                <p className="mt-1 text-base font-semibold">
                  {companyStatusLabel}
                </p>
              </div>
              <div className="rounded-2xl border bg-background p-3">
                <ShieldCheck className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/60 shadow-sm">
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-sm text-muted-foreground">اكتمال الملف</p>
                <p className="mt-1 text-base font-semibold">
                  {profileCompletion}%
                </p>
              </div>
              <div className="rounded-2xl border bg-background p-3">
                <Sparkles className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/60 shadow-sm">
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-sm text-muted-foreground">المعرف الداخلي</p>
                <p className="mt-1 text-base font-semibold">
                  {form.id ? `#${form.id}` : "غير متوفر"}
                </p>
              </div>
              <div className="rounded-2xl border bg-background p-3">
                <Info className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 xl:grid-cols-3">
          <div className="space-y-6 xl:col-span-2">
            <Card className="border-border/60 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Building2 className="h-5 w-5" />
                  البيانات الأساسية
                </CardTitle>
                <CardDescription>
                  بيانات التواصل الأساسية للشركة داخل النظام.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="name">اسم الشركة</Label>
                    <div className="relative">
                      <Building2 className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="name"
                        value={form.name}
                        onChange={(e) => handleChange("name", e.target.value)}
                        placeholder="مثال: Primey HR Cloud"
                        className="rounded-xl pe-10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">البريد الإلكتروني</Label>
                    <div className="relative">
                      <Mail className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="email"
                        type="email"
                        value={form.email}
                        onChange={(e) => handleChange("email", e.target.value)}
                        placeholder="company@example.com"
                        className="rounded-xl pe-10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone">الهاتف</Label>
                    <div className="relative">
                      <Phone className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="phone"
                        value={form.phone}
                        onChange={(e) => handleChange("phone", e.target.value)}
                        placeholder="05xxxxxxxx"
                        className="rounded-xl pe-10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="short_address">العنوان المختصر</Label>
                    <div className="relative">
                      <MapPin className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="short_address"
                        value={form.short_address}
                        onChange={(e) =>
                          handleChange("short_address", e.target.value)
                        }
                        placeholder="العنوان المختصر"
                        className="rounded-xl pe-10"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/60 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <MapPin className="h-5 w-5" />
                  العنوان الوطني
                </CardTitle>
                <CardDescription>
                  تفاصيل العنوان التفصيلية للشركة.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="city">المدينة</Label>
                    <div className="relative">
                      <MapPin className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="city"
                        value={form.city}
                        onChange={(e) => handleChange("city", e.target.value)}
                        placeholder="المدينة"
                        className="rounded-xl pe-10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="district">الحي</Label>
                    <div className="relative">
                      <Home className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="district"
                        value={form.district}
                        onChange={(e) =>
                          handleChange("district", e.target.value)
                        }
                        placeholder="الحي"
                        className="rounded-xl pe-10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="street">الشارع</Label>
                    <div className="relative">
                      <MapPin className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="street"
                        value={form.street}
                        onChange={(e) => handleChange("street", e.target.value)}
                        placeholder="اسم الشارع"
                        className="rounded-xl pe-10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="building_number">رقم المبنى</Label>
                    <div className="relative">
                      <Hash className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="building_number"
                        value={form.building_number}
                        onChange={(e) =>
                          handleChange("building_number", e.target.value)
                        }
                        placeholder="رقم المبنى"
                        className="rounded-xl pe-10"
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="postal_code">الرمز البريدي</Label>
                  <div className="relative">
                    <Mail className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="postal_code"
                      value={form.postal_code}
                      onChange={(e) =>
                        handleChange("postal_code", e.target.value)
                      }
                      placeholder="الرمز البريدي"
                      className="rounded-xl pe-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="full_address">تفاصيل إضافية</Label>
                  <Textarea
                    id="full_address"
                    value={[
                      form.city,
                      form.district,
                      form.street,
                      form.building_number,
                    ]
                      .filter(Boolean)
                      .join(" - ")}
                    readOnly
                    placeholder="سيتم تكوين وصف مختصر من بيانات العنوان"
                    className="min-h-[120px] rounded-xl"
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/60 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Landmark className="h-5 w-5" />
                  البيانات الرسمية
                </CardTitle>
                <CardDescription>
                  السجل التجاري والرقم الضريبي والبيانات النظامية.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="commercial_number">السجل التجاري</Label>
                    <div className="relative">
                      <FileBadge2 className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="commercial_number"
                        value={form.commercial_number}
                        onChange={(e) =>
                          handleChange("commercial_number", e.target.value)
                        }
                        placeholder="رقم السجل التجاري"
                        className="rounded-xl pe-10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="vat_number">الرقم الضريبي</Label>
                    <div className="relative">
                      <FileBadge2 className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="vat_number"
                        value={form.vat_number}
                        onChange={(e) =>
                          handleChange("vat_number", e.target.value)
                        }
                        placeholder="الرقم الضريبي"
                        className="rounded-xl pe-10"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="border-border/60 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <ImageIcon className="h-5 w-5" />
                  شعار الشركة
                </CardTitle>
                <CardDescription>
                  عرض الشعار الحالي القادم من الباكند.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex min-h-[240px] items-center justify-center rounded-2xl border border-dashed bg-muted/20 p-6">
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
                      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border bg-background">
                        <ImageIcon className="h-6 w-6 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="font-medium">لا يوجد شعار مرفوع</p>
                        <p className="mt-1 text-sm text-muted-foreground">
                          عند توفر رابط شعار من الباكند سيظهر هنا تلقائيًا.
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
                    className="rounded-xl"
                    onClick={() => logoInputRef.current?.click()}
                    disabled={saving}
                  >
                    <Upload className="me-2 h-4 w-4" />
                    اختيار شعار
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    className="rounded-xl"
                    onClick={clearLogoSelection}
                    disabled={saving || (!selectedLogoFile && !logoPreviewUrl)}
                  >
                    <X className="me-2 h-4 w-4" />
                    إلغاء الشعار الجديد
                  </Button>
                </div>

                <div className="rounded-2xl border bg-muted/20 p-4 text-sm text-muted-foreground">
                  <div className="font-medium text-foreground">شروط الشعار</div>
                  <div className="mt-2 space-y-1">
                    <p>• الصيغ المدعومة: JPG / PNG / WEBP</p>
                    <p>• الحد الأقصى للحجم: 5MB</p>
                    <p>• سيتم رفع الشعار إلى Google Drive عند الحفظ</p>
                  </div>
                </div>

                {selectedLogoFile ? (
                  <div className="rounded-2xl border border-dashed border-primary/40 bg-primary/5 p-4 text-sm">
                    <div className="font-medium text-foreground">
                      الشعار الجديد المحدد
                    </div>
                    <div className="mt-2 text-muted-foreground">
                      <p>الاسم: {selectedLogoFile.name}</p>
                      <p>
                        الحجم:{" "}
                        {(selectedLogoFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card className="border-border/60 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">ملخص سريع</CardTitle>
                <CardDescription>
                  قراءة سريعة لبيانات الشركة الحالية.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-2xl border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">اسم العرض</p>
                  <p className="mt-1 font-semibold">{form.name || "—"}</p>
                </div>

                <div className="rounded-2xl border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">المدينة / الحي</p>
                  <p className="mt-1 font-semibold">
                    {[form.city, form.district].filter(Boolean).join(" — ") ||
                      "—"}
                  </p>
                </div>

                <div className="rounded-2xl border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">البريد / الهاتف</p>
                  <p className="mt-1 font-semibold">
                    {form.email || form.phone || "—"}
                  </p>
                </div>

                <div className="rounded-2xl border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">السجل / الضريبة</p>
                  <p className="mt-1 font-semibold">
                    {form.commercial_number || form.vat_number || "—"}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/60 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">حالة التعديل</CardTitle>
                <CardDescription>
                  تنبيه سريع حول ما إذا كانت هناك تغييرات غير محفوظة.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between rounded-2xl border p-4">
                  <span className="text-sm font-medium">التغييرات الحالية</span>
                  <Badge
                    variant={hasChanges ? "default" : "secondary"}
                    className="rounded-full"
                  >
                    {hasChanges ? "غير محفوظة" : "محفوظ"}
                  </Badge>
                </div>

                <Separator />

                <div className="flex items-center justify-between rounded-2xl border p-4">
                  <span className="text-sm font-medium">نسبة اكتمال الملف</span>
                  <Badge variant="outline" className="rounded-full">
                    {profileCompletion}%
                  </Badge>
                </div>

                <div className="flex items-center justify-between rounded-2xl border p-4">
                  <span className="text-sm font-medium">الحالة الحالية</span>
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
                    className="w-full rounded-xl"
                  >
                    {saving ? (
                      <Loader2 className="me-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="me-2 h-4 w-4" />
                    )}
                    حفظ إعدادات الشركة
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