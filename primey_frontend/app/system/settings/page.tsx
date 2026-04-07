"use client"

import { useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  Loader2,
  Mail,
  RefreshCw,
  RotateCcw,
  Save,
  Server,
  ShieldCheck,
  Clock3,
} from "lucide-react"
import { toast } from "sonner"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

const API_BASE = "http://localhost:8000/api/system/settings"

/* =====================================================
   Types
===================================================== */

type ModulesMap = Record<string, boolean>
type Locale = "ar" | "en"
type Direction = "rtl" | "ltr"

interface EmailSettings {
  smtp_server: string
  smtp_port: number
  use_tls: boolean
  username: string
  password: string
  password_masked?: string
  from_email?: string
  is_ready: boolean
  status: "ready" | "incomplete"
  updated_at?: string | null
}

/* =====================================================
   i18n
===================================================== */

const translations = {
  ar: {
    pageTitle: "إعدادات النظام",
    pageSubtitle: "Mham Cloud — حوكمة المنصة وإعدادات البريد الإلكتروني",

    refresh: "تحديث",
    reload: "إعادة تحميل",

    platformControl: "التحكم بالمنصة",
    platformActive: "المنصة مفعلة",
    platformActiveDesc: "مفتاح تشغيل/إيقاف عام لكامل المنصة",

    maintenanceMode: "وضع الصيانة",
    maintenanceModeDesc: "يسمح فقط للسوبر أدمن بالدخول عند التفعيل",

    readonlyMode: "وضع القراءة فقط",
    readonlyModeDesc: "يمنع عمليات التعديل مع إبقاء الوصول للقراءة فقط",

    billingEnabled: "الفوترة مفعلة",
    billingEnabledDesc: "تفعيل أو تعطيل الوصول إلى نظام الفوترة",

    emailStatus: "حالة البريد",
    ready: "جاهز",
    incomplete: "غير مكتمل",
    emailReadyDesc: "إعداد SMTP جاهز للإرسال.",
    emailIncompleteDesc: "بعض الحقول المطلوبة للبريد ما زالت ناقصة.",

    fromEmail: "البريد المرسل",
    notConfigured: "غير مهيأ",
    fromEmailDesc: "العنوان المستخدم في الإرسال التجريبي والبريد الصادر",

    validation: "التحقق",
    allValid: "جميع حقول SMTP المطلوبة صالحة.",
    missingFields: "الحقول الناقصة:",
    lastUpdated: "آخر تحديث",
    lastUpdatedDesc: "آخر وقت تم فيه حفظ إعدادات البريد",
    notAvailable: "غير متوفر",

    emailSettings: "إعدادات البريد الإلكتروني",
    unsavedChanges: "توجد تغييرات غير محفوظة",
    saved: "محفوظ",
    resetChanges: "استرجاع التعديلات",
    saveAll: "حفظ الكل",

    smtpHost: "SMTP Host",
    smtpPort: "SMTP Port",
    usernameSender: "اسم المستخدم / البريد المرسل",
    passwordLabel: "كلمة المرور / App Password",
    showPassword: "إظهار كلمة المرور",
    hidePassword: "إخفاء كلمة المرور",

    useTls: "استخدام TLS",
    useTlsDesc: "موصى به لـ Gmail ومعظم مزودي SMTP الآمنين",

    testEmailRecipient: "مستلم البريد التجريبي",
    testEmail: "إرسال اختبار",

    notes: "ملاحظات",
    note1: "في Gmail استخدم App Password بدل كلمة المرور العادية.",
    note2: "يتم الحفظ تلقائيًا عند مغادرة كل حقل.",
    note3: "زر حفظ الكل مفيد عند تعديل عدة حقول معًا.",
    note4: "الإرسال التجريبي يعتمد على القيم المحفوظة في الـ backend.",

    systemModules: "وحدات النظام",
    noModules: "لم يتم إرجاع أي وحدات من الـ backend.",
    uiPreviewOnly: "عرض واجهة فقط حاليًا",

    footerUnsaved: "توجد تغييرات غير محفوظة في البريد",
    footerSaved: "جميع تغييرات البريد محفوظة",

    loading: "جاري تحميل إعدادات النظام...",
    saving: "جارٍ الحفظ...",
    testSending: "جارٍ إرسال الاختبار...",

    toastLoadFailed: "فشل تحميل إعدادات النظام",
    toastSettingSaved: "تم تحديث الإعداد بنجاح",
    toastSettingUpdateFailed: "فشل تحديث الإعداد",
    toastEmailSaved: "تم حفظ إعداد البريد بنجاح",
    toastEmailSaveFailed: "فشل حفظ إعداد البريد",
    toastSaveAllSuccess: "تم حفظ جميع إعدادات البريد بنجاح",
    toastNoChanges: "لا توجد تغييرات بريد لحفظها",
    toastResetSuccess: "تمت إعادة نموذج البريد إلى آخر القيم المحمّلة",
    toastTestFailed: "فشل إرسال البريد التجريبي",
    toastModuleUiOnly: "تغيير الوحدات ظاهر في الواجهة فقط حتى يتم تنفيذ الحفظ من الـ backend",

    requiredFields: "أكمل الحقول المطلوبة:",
    smtpHostShort: "SMTP Host يبدو قصيرًا جدًا",
    smtpPortInvalid: "SMTP Port يجب أن يكون بين 1 و 65535",
    usernameInvalid: "اسم المستخدم يجب أن يكون بريدًا إلكترونيًا صالحًا",
    testEmailInvalid: "البريد التجريبي غير صالح",

    placeholders: {
      smtpHost: "smtp.gmail.com",
      smtpPort: "587",
      username: "info@yourdomain.com",
      password: "أدخل كلمة مرور SMTP",
      testEmail: "example@domain.com",
    },
  },
  en: {
    pageTitle: "System Settings",
    pageSubtitle: "Mham Cloud — Platform Governance & Email Configuration",

    refresh: "Refresh",
    reload: "Reload",

    platformControl: "Platform Control",
    platformActive: "Platform Active",
    platformActiveDesc: "Global kill switch for the whole platform",

    maintenanceMode: "Maintenance Mode",
    maintenanceModeDesc: "Only super admin can access when enabled",

    readonlyMode: "Readonly Mode",
    readonlyModeDesc: "Blocks write actions and keeps read-only access",

    billingEnabled: "Billing Enabled",
    billingEnabledDesc: "Enable or disable billing system access",

    emailStatus: "Email Status",
    ready: "Ready",
    incomplete: "Incomplete",
    emailReadyDesc: "SMTP configuration is ready for sending.",
    emailIncompleteDesc: "Some required email fields are still missing.",

    fromEmail: "From Email",
    notConfigured: "Not configured",
    fromEmailDesc: "Sender used for test email and outbound SMTP",

    validation: "Validation",
    allValid: "All required SMTP fields are valid.",
    missingFields: "Missing fields:",
    lastUpdated: "Last Updated",
    lastUpdatedDesc: "Latest saved email configuration time",
    notAvailable: "Not available",

    emailSettings: "Email Settings",
    unsavedChanges: "Unsaved Changes",
    saved: "Saved",
    resetChanges: "Reset Changes",
    saveAll: "Save All",

    smtpHost: "SMTP Host",
    smtpPort: "SMTP Port",
    usernameSender: "Username / Sender Email",
    passwordLabel: "Password / App Password",
    showPassword: "Show password",
    hidePassword: "Hide password",

    useTls: "Use TLS",
    useTlsDesc: "Recommended for Gmail and most secure SMTP providers",

    testEmailRecipient: "Test Email Recipient",
    testEmail: "Test Email",

    notes: "Notes",
    note1: "For Gmail, use App Password instead of your normal password.",
    note2: "Save happens automatically when you leave each field.",
    note3: "Save All is useful when editing multiple fields together.",
    note4: "Test Email uses the saved SMTP values from backend.",

    systemModules: "System Modules",
    noModules: "No module flags returned from backend.",
    uiPreviewOnly: "UI preview only for now",

    footerUnsaved: "There are unsaved email changes",
    footerSaved: "All email changes are saved",

    loading: "Loading system settings...",
    saving: "Saving...",
    testSending: "Sending test...",

    toastLoadFailed: "Failed to load system settings",
    toastSettingSaved: "Setting updated successfully",
    toastSettingUpdateFailed: "Failed to update setting",
    toastEmailSaved: "Email setting saved successfully",
    toastEmailSaveFailed: "Failed to update email setting",
    toastSaveAllSuccess: "All email settings saved successfully",
    toastNoChanges: "No email changes to save",
    toastResetSuccess: "Email form reset to last loaded values",
    toastTestFailed: "Failed to send test email",
    toastModuleUiOnly: "Modules UI is shown only here until backend module save is implemented",

    requiredFields: "Please complete required fields:",
    smtpHostShort: "SMTP Host looks too short",
    smtpPortInvalid: "SMTP Port must be between 1 and 65535",
    usernameInvalid: "Username must be a valid email address",
    testEmailInvalid: "Test recipient email is invalid",

    placeholders: {
      smtpHost: "smtp.gmail.com",
      smtpPort: "587",
      username: "info@yourdomain.com",
      password: "Enter SMTP password",
      testEmail: "example@domain.com",
    },
  },
} as const

/* =====================================================
   CSRF COOKIE
===================================================== */

function getCookie(name: string) {
  if (typeof document === "undefined") return null

  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift()
  }

  return null
}

/* =====================================================
   Helpers
===================================================== */

function normalizeEmailSettings(email: Partial<EmailSettings>): EmailSettings {
  return {
    smtp_server: email.smtp_server ?? "",
    smtp_port: Number(email.smtp_port ?? 587),
    use_tls: email.use_tls ?? true,
    username: email.username ?? "",
    password: email.password ?? "",
    password_masked: email.password_masked ?? "",
    from_email: email.from_email ?? "",
    is_ready: email.is_ready ?? false,
    status: email.status ?? "incomplete",
    updated_at: email.updated_at ?? null,
  }
}

function areEmailSettingsEqual(a: EmailSettings, b: EmailSettings) {
  return (
    a.smtp_server === b.smtp_server &&
    Number(a.smtp_port) === Number(b.smtp_port) &&
    a.use_tls === b.use_tls &&
    a.username === b.username &&
    a.password === b.password
  )
}

function formatDateTimeEnglish(value?: string | null, fallback = "Not available") {
  if (!value) return fallback

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return fallback

  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    numberingSystem: "latn",
  }).format(date)
}

function normalizeDigitsToEnglish(value: string | number) {
  return String(value ?? "").replace(/[٠-٩]/g, (d) => "٠١٢٣٤٥٦٧٨٩".indexOf(d).toString())
}

function toModuleLabel(moduleKey: string) {
  return moduleKey.replace(/[_-]+/g, " ").replace(/\b\w/g, (char) => char.toUpperCase())
}

export default function SystemSettingsPage() {
  const [locale, setLocale] = useState<Locale>("en")
  const [direction, setDirection] = useState<Direction>("ltr")

  const [loading, setLoading] = useState(true)
  const [savingField, setSavingField] = useState<string | null>(null)
  const [savingAll, setSavingAll] = useState(false)
  const [testingEmail, setTestingEmail] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const [platformActive, setPlatformActive] = useState(true)
  const [maintenanceMode, setMaintenanceMode] = useState(false)
  const [readonlyMode, setReadonlyMode] = useState(false)
  const [billingEnabled, setBillingEnabled] = useState(true)
  const [modules, setModules] = useState<ModulesMap>({})

  const [emailSettings, setEmailSettings] = useState<EmailSettings>({
    smtp_server: "",
    smtp_port: 587,
    use_tls: true,
    username: "",
    password: "",
    password_masked: "",
    from_email: "",
    is_ready: false,
    status: "incomplete",
    updated_at: null,
  })

  const [initialEmailSettings, setInitialEmailSettings] = useState<EmailSettings>({
    smtp_server: "",
    smtp_port: 587,
    use_tls: true,
    username: "",
    password: "",
    password_masked: "",
    from_email: "",
    is_ready: false,
    status: "incomplete",
    updated_at: null,
  })

  const [testEmail, setTestEmail] = useState("")

  const t = translations[locale]

  /* =====================================================
     Locale + Direction Sync
  ===================================================== */

  useEffect(() => {
    if (typeof document === "undefined") return

    const syncLanguageState = () => {
      const html = document.documentElement
      const rawLang = (html.lang || "en").toLowerCase()
      const rawDir = (html.dir || "ltr").toLowerCase()

      setLocale(rawLang.startsWith("ar") ? "ar" : "en")
      setDirection(rawDir === "rtl" ? "rtl" : "ltr")
    }

    syncLanguageState()

    const observer = new MutationObserver(() => {
      syncLanguageState()
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    return () => observer.disconnect()
  }, [])

  /* =====================================================
     Derived
  ===================================================== */

  const emailMissingFields = useMemo(() => {
    const missing: string[] = []

    if (!emailSettings.smtp_server?.trim()) missing.push(t.smtpHost)
    if (!emailSettings.smtp_port || Number(emailSettings.smtp_port) <= 0) {
      missing.push(t.smtpPort)
    }
    if (!emailSettings.username?.trim()) missing.push(t.usernameSender)
    if (!emailSettings.password?.trim()) missing.push(t.passwordLabel)

    return missing
  }, [emailSettings, t])

  const emailValidationErrors = useMemo(() => {
    const errors: string[] = []

    if (emailSettings.smtp_server.trim() && emailSettings.smtp_server.trim().length < 3) {
      errors.push(t.smtpHostShort)
    }

    if (
      emailSettings.smtp_port &&
      (Number(emailSettings.smtp_port) < 1 || Number(emailSettings.smtp_port) > 65535)
    ) {
      errors.push(t.smtpPortInvalid)
    }

    if (
      emailSettings.username.trim() &&
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailSettings.username.trim())
    ) {
      errors.push(t.usernameInvalid)
    }

    if (testEmail.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(testEmail.trim())) {
      errors.push(t.testEmailInvalid)
    }

    return errors
  }, [emailSettings, testEmail, t])

  const hasEmailChanges = useMemo(() => {
    return !areEmailSettingsEqual(emailSettings, initialEmailSettings)
  }, [emailSettings, initialEmailSettings])

  const canSaveAllEmail = useMemo(() => {
    return (
      hasEmailChanges &&
      emailMissingFields.length === 0 &&
      emailValidationErrors.length === 0 &&
      !savingAll &&
      !testingEmail &&
      !savingField
    )
  }, [
    hasEmailChanges,
    emailMissingFields,
    emailValidationErrors,
    savingAll,
    testingEmail,
    savingField,
  ])

  const isBusy = Boolean(loading || savingField || savingAll || testingEmail)

  /* =====================================================
     LOAD SETTINGS
  ===================================================== */

  async function loadSettings() {
    try {
      setLoading(true)

      const res = await fetch(`${API_BASE}/`, {
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      })

      if (!res.ok) {
        throw new Error("API returned error")
      }

      const data = await res.json()

      setPlatformActive(data.platform_active ?? true)
      setMaintenanceMode(data.maintenance_mode ?? false)
      setReadonlyMode(data.readonly_mode ?? false)
      setBillingEnabled(data.billing_enabled ?? true)
      setModules(data.modules || {})

      const normalizedEmail = normalizeEmailSettings(data.email || {})

      setEmailSettings(normalizedEmail)
      setInitialEmailSettings(normalizedEmail)
      setTestEmail(normalizedEmail.username ?? "")
    } catch (err) {
      console.error(err)
      toast.error(t.toastLoadFailed)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSettings()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* =====================================================
     UPDATE GENERAL SETTING
  ===================================================== */

  async function updateGeneralSetting(field: string, value: boolean) {
    const csrf = getCookie("csrftoken")

    try {
      setSavingField(field)

      const res = await fetch(`${API_BASE}/update/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf || "",
        },
        credentials: "include",
        body: JSON.stringify({
          section: "general",
          field,
          value,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data?.message || t.toastSettingUpdateFailed)
      }

      toast.success(t.toastSettingSaved)
    } catch (error) {
      console.error(error)
      toast.error(error instanceof Error ? error.message : t.toastSettingUpdateFailed)
      await loadSettings()
    } finally {
      setSavingField(null)
    }
  }

  /* =====================================================
     UPDATE EMAIL SETTING
  ===================================================== */

  async function updateEmailSetting(
    field: keyof EmailSettings,
    value: string | number | boolean,
    options?: { silent?: boolean }
  ) {
    const csrf = getCookie("csrftoken")

    try {
      setSavingField(`email:${field}`)

      const res = await fetch(`${API_BASE}/update/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf || "",
        },
        credentials: "include",
        body: JSON.stringify({
          section: "email",
          field,
          value,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data?.message || t.toastEmailSaveFailed)
      }

      if (data?.email) {
        const normalizedEmail = normalizeEmailSettings(data.email)
        setEmailSettings(normalizedEmail)
        setInitialEmailSettings(normalizedEmail)
      }

      if (!options?.silent) {
        toast.success(t.toastEmailSaved)
      }
    } catch (error) {
      console.error(error)
      toast.error(error instanceof Error ? error.message : t.toastEmailSaveFailed)
      await loadSettings()
      throw error
    } finally {
      setSavingField(null)
    }
  }

  /* =====================================================
     SAVE ALL EMAIL SETTINGS
  ===================================================== */

  async function handleSaveAllEmail() {
    if (emailMissingFields.length > 0) {
      toast.error(`${t.requiredFields} ${emailMissingFields.join(", ")}`)
      return
    }

    if (emailValidationErrors.length > 0) {
      toast.error(emailValidationErrors[0])
      return
    }

    if (!hasEmailChanges) {
      toast.info(t.toastNoChanges)
      return
    }

    try {
      setSavingAll(true)

      const changedFields: Array<[keyof EmailSettings, string | number | boolean]> = []

      if (emailSettings.smtp_server !== initialEmailSettings.smtp_server) {
        changedFields.push(["smtp_server", emailSettings.smtp_server])
      }

      if (Number(emailSettings.smtp_port) !== Number(initialEmailSettings.smtp_port)) {
        changedFields.push(["smtp_port", Number(emailSettings.smtp_port)])
      }

      if (emailSettings.use_tls !== initialEmailSettings.use_tls) {
        changedFields.push(["use_tls", emailSettings.use_tls])
      }

      if (emailSettings.username !== initialEmailSettings.username) {
        changedFields.push(["username", emailSettings.username])
      }

      if (emailSettings.password !== initialEmailSettings.password) {
        changedFields.push(["password", emailSettings.password])
      }

      for (const [field, value] of changedFields) {
        await updateEmailSetting(field, value, { silent: true })
      }

      toast.success(t.toastSaveAllSuccess)
    } catch {
      // handled in updateEmailSetting
    } finally {
      setSavingAll(false)
    }
  }

  /* =====================================================
     RESET EMAIL FORM
  ===================================================== */

  function handleResetEmailChanges() {
    setEmailSettings(initialEmailSettings)
    toast.success(t.toastResetSuccess)
  }

  /* =====================================================
     TEST EMAIL
  ===================================================== */

  async function handleTestEmail() {
    const csrf = getCookie("csrftoken")

    if (emailMissingFields.length > 0) {
      toast.error(`${t.requiredFields} ${emailMissingFields.join(", ")}`)
      return
    }

    if (emailValidationErrors.length > 0) {
      toast.error(emailValidationErrors[0])
      return
    }

    try {
      setTestingEmail(true)

      const res = await fetch(`${API_BASE}/email/test/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf || "",
        },
        credentials: "include",
        body: JSON.stringify({
          to: testEmail.trim() || emailSettings.username,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data?.message || t.toastTestFailed)
      }

      toast.success(data?.message || (locale === "ar" ? "تم إرسال البريد التجريبي بنجاح" : "Test email sent successfully"))
    } catch (error) {
      console.error(error)
      toast.error(error instanceof Error ? error.message : t.toastTestFailed)
    } finally {
      setTestingEmail(false)
    }
  }

  /* =====================================================
     MODULE UI ONLY
  ===================================================== */

  async function updateModule(module: string, value: boolean) {
    const updatedModules = {
      ...modules,
      [module]: value,
    }

    setModules(updatedModules)
    toast.info(t.toastModuleUiOnly)
  }

  /* =====================================================
     LOADING
  ===================================================== */

  if (loading) {
    return (
      <div dir={direction} className="p-4 sm:p-6">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>{t.loading}</span>
        </div>
      </div>
    )
  }

  return (
    <div dir={direction} className="space-y-6 p-1 sm:p-2">
      {/* HEADER */}
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-1">
          <h1 className="text-xl font-bold tracking-tight sm:text-2xl">{t.pageTitle}</h1>
          <p className="text-sm text-muted-foreground sm:text-base">{t.pageSubtitle}</p>
        </div>

        <Button
          variant="outline"
          onClick={loadSettings}
          className="w-full sm:w-auto"
          disabled={isBusy}
        >
          <RefreshCw className={`${direction === "rtl" ? "ml-2" : "mr-2"} h-4 w-4`} />
          {t.refresh}
        </Button>
      </div>

      {/* PLATFORM CONTROL */}
      <Card className="rounded-2xl border-border/60 shadow-sm">
        <CardHeader>
          <CardTitle>{t.platformControl}</CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <Label>{t.platformActive}</Label>
              <p className="text-sm text-muted-foreground">{t.platformActiveDesc}</p>
            </div>

            <Switch
              checked={platformActive}
              disabled={savingField === "platform_active" || isBusy}
              onCheckedChange={(v) => {
                setPlatformActive(v)
                updateGeneralSetting("platform_active", v)
              }}
            />
          </div>

          <Separator />

          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <Label>{t.maintenanceMode}</Label>
              <p className="text-sm text-muted-foreground">{t.maintenanceModeDesc}</p>
            </div>

            <Switch
              checked={maintenanceMode}
              disabled={savingField === "maintenance_mode" || isBusy}
              onCheckedChange={(v) => {
                setMaintenanceMode(v)
                updateGeneralSetting("maintenance_mode", v)
              }}
            />
          </div>

          <Separator />

          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <Label>{t.readonlyMode}</Label>
              <p className="text-sm text-muted-foreground">{t.readonlyModeDesc}</p>
            </div>

            <Switch
              checked={readonlyMode}
              disabled={savingField === "readonly_mode" || isBusy}
              onCheckedChange={(v) => {
                setReadonlyMode(v)
                updateGeneralSetting("readonly_mode", v)
              }}
            />
          </div>

          <Separator />

          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <Label>{t.billingEnabled}</Label>
              <p className="text-sm text-muted-foreground">{t.billingEnabledDesc}</p>
            </div>

            <Switch
              checked={billingEnabled}
              disabled={savingField === "billing_enabled" || isBusy}
              onCheckedChange={(v) => {
                setBillingEnabled(v)
                updateGeneralSetting("billing_enabled", v)
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* EMAIL STATUS */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="rounded-2xl border-border/60 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Mail className="h-4 w-4" />
              {t.emailStatus}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={emailSettings.is_ready ? "default" : "secondary"}>
              {emailSettings.is_ready ? t.ready : t.incomplete}
            </Badge>

            <p className="mt-3 text-sm text-muted-foreground">
              {emailSettings.is_ready ? t.emailReadyDesc : t.emailIncompleteDesc}
            </p>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-border/60 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Server className="h-4 w-4" />
              {t.fromEmail}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="break-all text-sm font-medium" dir="ltr">
              {emailSettings.from_email || t.notConfigured}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">{t.fromEmailDesc}</p>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-border/60 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <ShieldCheck className="h-4 w-4" />
              {t.validation}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {emailMissingFields.length === 0 && emailValidationErrors.length === 0 ? (
              <div className="flex items-start gap-2 text-sm">
                <CheckCircle2 className="mt-0.5 h-4 w-4 text-green-600" />
                <span>{t.allValid}</span>
              </div>
            ) : (
              <div className="space-y-2 text-sm">
                {emailMissingFields.length > 0 && (
                  <>
                    <div className="flex items-start gap-2">
                      <AlertCircle className="mt-0.5 h-4 w-4 text-amber-600" />
                      <span>{t.missingFields}</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {emailMissingFields.map((item) => (
                        <Badge key={item} variant="outline">
                          {item}
                        </Badge>
                      ))}
                    </div>
                  </>
                )}

                {emailValidationErrors.length > 0 && (
                  <div className="space-y-2">
                    {emailValidationErrors.map((error) => (
                      <div key={error} className="flex items-start gap-2 text-amber-700">
                        <AlertCircle className="mt-0.5 h-4 w-4" />
                        <span>{error}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-border/60 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Clock3 className="h-4 w-4" />
              {t.lastUpdated}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm font-medium" dir="ltr">
              {formatDateTimeEnglish(emailSettings.updated_at, t.notAvailable)}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">{t.lastUpdatedDesc}</p>
          </CardContent>
        </Card>
      </div>

      {/* EMAIL SETTINGS */}
      <Card className="rounded-2xl border-border/60 shadow-sm">
        <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <CardTitle>{t.emailSettings}</CardTitle>

          <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
            <Badge variant={hasEmailChanges ? "secondary" : "outline"}>
              {hasEmailChanges ? t.unsavedChanges : t.saved}
            </Badge>

            <Button
              type="button"
              variant="outline"
              onClick={handleResetEmailChanges}
              disabled={!hasEmailChanges || isBusy}
              className="w-full sm:w-auto"
            >
              <RotateCcw className={`${direction === "rtl" ? "ml-2" : "mr-2"} h-4 w-4`} />
              {t.resetChanges}
            </Button>

            <Button
              type="button"
              onClick={handleSaveAllEmail}
              disabled={!canSaveAllEmail}
              className="w-full sm:w-auto"
            >
              {savingAll ? (
                <Loader2 className={`${direction === "rtl" ? "ml-2" : "mr-2"} h-4 w-4 animate-spin`} />
              ) : (
                <Save className={`${direction === "rtl" ? "ml-2" : "mr-2"} h-4 w-4`} />
              )}
              {t.saveAll}
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>{t.smtpHost}</Label>
              <Input
                dir="ltr"
                inputMode="text"
                value={emailSettings.smtp_server}
                disabled={isBusy}
                onChange={(e) =>
                  setEmailSettings((prev) => ({
                    ...prev,
                    smtp_server: e.target.value,
                  }))
                }
                onBlur={() => {
                  if (emailSettings.smtp_server !== initialEmailSettings.smtp_server) {
                    updateEmailSetting("smtp_server", emailSettings.smtp_server)
                  }
                }}
                placeholder={t.placeholders.smtpHost}
              />
            </div>

            <div className="space-y-2">
              <Label>{t.smtpPort}</Label>
              <Input
                dir="ltr"
                type="number"
                inputMode="numeric"
                value={normalizeDigitsToEnglish(emailSettings.smtp_port)}
                disabled={isBusy}
                onChange={(e) =>
                  setEmailSettings((prev) => ({
                    ...prev,
                    smtp_port: Number(normalizeDigitsToEnglish(e.target.value || 0)),
                  }))
                }
                onBlur={() => {
                  if (Number(emailSettings.smtp_port) !== Number(initialEmailSettings.smtp_port)) {
                    updateEmailSetting("smtp_port", emailSettings.smtp_port)
                  }
                }}
                placeholder={t.placeholders.smtpPort}
              />
            </div>

            <div className="space-y-2">
              <Label>{t.usernameSender}</Label>
              <Input
                dir="ltr"
                type="email"
                inputMode="email"
                value={emailSettings.username}
                disabled={isBusy}
                onChange={(e) =>
                  setEmailSettings((prev) => ({
                    ...prev,
                    username: e.target.value,
                  }))
                }
                onBlur={() => {
                  if (emailSettings.username !== initialEmailSettings.username) {
                    updateEmailSetting("username", emailSettings.username)
                  }
                }}
                placeholder={t.placeholders.username}
              />
            </div>

            <div className="space-y-2">
              <Label>{t.passwordLabel}</Label>
              <div className="relative">
                <Input
                  dir="ltr"
                  type={showPassword ? "text" : "password"}
                  value={emailSettings.password}
                  disabled={isBusy}
                  onChange={(e) =>
                    setEmailSettings((prev) => ({
                      ...prev,
                      password: e.target.value,
                    }))
                  }
                  onBlur={() => {
                    if (emailSettings.password !== initialEmailSettings.password) {
                      updateEmailSetting("password", emailSettings.password)
                    }
                  }}
                  placeholder={t.placeholders.password}
                  className={direction === "rtl" ? "pl-11" : "pr-11"}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className={`absolute top-1/2 -translate-y-1/2 text-muted-foreground disabled:pointer-events-none disabled:opacity-50 ${
                    direction === "rtl" ? "left-3" : "right-3"
                  }`}
                  disabled={isBusy}
                  aria-label={showPassword ? t.hidePassword : t.showPassword}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          </div>

          <Separator />

          <div className="flex flex-col gap-4 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <Label>{t.useTls}</Label>
              <p className="text-sm text-muted-foreground">{t.useTlsDesc}</p>
            </div>

            <Switch
              checked={emailSettings.use_tls}
              disabled={savingField === "email:use_tls" || isBusy}
              onCheckedChange={(v) => {
                setEmailSettings((prev) => ({
                  ...prev,
                  use_tls: v,
                }))
                updateEmailSetting("use_tls", v)
              }}
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
            <div className="space-y-2">
              <Label>{t.testEmailRecipient}</Label>
              <Input
                dir="ltr"
                type="email"
                inputMode="email"
                value={testEmail}
                disabled={isBusy}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder={t.placeholders.testEmail}
              />
            </div>

            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={handleTestEmail}
                disabled={testingEmail || !emailSettings.is_ready || isBusy}
                className="w-full lg:w-auto"
              >
                {testingEmail ? (
                  <Loader2 className={`${direction === "rtl" ? "ml-2" : "mr-2"} h-4 w-4 animate-spin`} />
                ) : (
                  <Mail className={`${direction === "rtl" ? "ml-2" : "mr-2"} h-4 w-4`} />
                )}
                {t.testEmail}
              </Button>
            </div>
          </div>

          <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
            <p className="font-medium text-foreground">{t.notes}</p>
            <ul className="mt-2 space-y-1">
              <li>• {t.note1}</li>
              <li>• {t.note2}</li>
              <li>• {t.note3}</li>
              <li>• {t.note4}</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* MODULES */}
      <Card className="rounded-2xl border-border/60 shadow-sm">
        <CardHeader>
          <CardTitle>{t.systemModules}</CardTitle>
        </CardHeader>

        <CardContent className="space-y-5">
          {Object.keys(modules).length === 0 ? (
            <p className="text-sm text-muted-foreground">{t.noModules}</p>
          ) : (
            Object.entries(modules).map(([moduleKey, enabled]) => (
              <div
                key={moduleKey}
                className="flex flex-col gap-4 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0">
                  <Label className="block">{toModuleLabel(moduleKey)}</Label>
                  <p className="text-sm text-muted-foreground">{t.uiPreviewOnly}</p>
                </div>

                <Switch
                  checked={enabled}
                  disabled={isBusy}
                  onCheckedChange={(v) => updateModule(moduleKey, v)}
                />
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {/* FOOTER ACTIONS */}
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <Button variant="outline" onClick={loadSettings} disabled={isBusy} className="w-full sm:w-auto">
          <RefreshCw className={`${direction === "rtl" ? "ml-2" : "mr-2"} h-4 w-4`} />
          {t.reload}
        </Button>

        <Badge variant={hasEmailChanges ? "secondary" : "outline"} className="w-fit">
          {hasEmailChanges ? t.footerUnsaved : t.footerSaved}
        </Badge>
      </div>
    </div>
  )
}