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
  Clock3
} from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

import { toast } from "sonner"

const API_BASE = "http://localhost:8000/api/system/settings"

/* =====================================================
   Types
===================================================== */

type ModulesMap = Record<string, boolean>

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
    updated_at: email.updated_at ?? null
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

function formatDateTime(value?: string | null) {
  if (!value) return "Not available"

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return "Not available"

  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date)
}

export default function SystemSettingsPage() {
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
    updated_at: null
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
    updated_at: null
  })

  const [testEmail, setTestEmail] = useState("")

  /* =====================================================
     Derived
  ===================================================== */

  const emailMissingFields = useMemo(() => {
    const missing: string[] = []

    if (!emailSettings.smtp_server?.trim()) missing.push("SMTP Host")
    if (!emailSettings.smtp_port || Number(emailSettings.smtp_port) <= 0) {
      missing.push("SMTP Port")
    }
    if (!emailSettings.username?.trim()) missing.push("Username")
    if (!emailSettings.password?.trim()) missing.push("Password")

    return missing
  }, [emailSettings])

  const emailValidationErrors = useMemo(() => {
    const errors: string[] = []

    if (emailSettings.smtp_server.trim() && emailSettings.smtp_server.trim().length < 3) {
      errors.push("SMTP Host looks too short")
    }

    if (
      emailSettings.smtp_port &&
      (Number(emailSettings.smtp_port) < 1 || Number(emailSettings.smtp_port) > 65535)
    ) {
      errors.push("SMTP Port must be between 1 and 65535")
    }

    if (
      emailSettings.username.trim() &&
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailSettings.username.trim())
    ) {
      errors.push("Username must be a valid email address")
    }

    if (
      testEmail.trim() &&
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(testEmail.trim())
    ) {
      errors.push("Test recipient email is invalid")
    }

    return errors
  }, [emailSettings, testEmail])

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
    savingField
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
          Accept: "application/json"
        }
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
      toast.error("Failed to load system settings")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSettings()
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
          "X-CSRFToken": csrf || ""
        },
        credentials: "include",
        body: JSON.stringify({
          section: "general",
          field,
          value
        })
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data?.message || "Failed to update setting")
      }

      toast.success("Setting updated successfully")
    } catch (error) {
      console.error(error)
      toast.error(error instanceof Error ? error.message : "Failed to update setting")
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
          "X-CSRFToken": csrf || ""
        },
        credentials: "include",
        body: JSON.stringify({
          section: "email",
          field,
          value
        })
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data?.message || "Failed to update email setting")
      }

      if (data?.email) {
        const normalizedEmail = normalizeEmailSettings(data.email)
        setEmailSettings(normalizedEmail)
        setInitialEmailSettings(normalizedEmail)
      }

      if (!options?.silent) {
        toast.success("Email setting saved successfully")
      }
    } catch (error) {
      console.error(error)
      toast.error(error instanceof Error ? error.message : "Failed to update email setting")
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
      toast.error(`Please complete required fields: ${emailMissingFields.join(", ")}`)
      return
    }

    if (emailValidationErrors.length > 0) {
      toast.error(emailValidationErrors[0])
      return
    }

    if (!hasEmailChanges) {
      toast.info("No email changes to save")
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

      toast.success("All email settings saved successfully")
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
    toast.success("Email form reset to last loaded values")
  }

  /* =====================================================
     TEST EMAIL
  ===================================================== */

  async function handleTestEmail() {
    const csrf = getCookie("csrftoken")

    if (emailMissingFields.length > 0) {
      toast.error(`Please complete required fields: ${emailMissingFields.join(", ")}`)
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
          "X-CSRFToken": csrf || ""
        },
        credentials: "include",
        body: JSON.stringify({
          to: testEmail.trim() || emailSettings.username
        })
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data?.message || "Failed to send test email")
      }

      toast.success(data?.message || "Test email sent successfully")
    } catch (error) {
      console.error(error)
      toast.error(error instanceof Error ? error.message : "Failed to send test email")
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
      [module]: value
    }

    setModules(updatedModules)
    toast.info("Modules UI is shown only here until backend module save is implemented")
  }

  /* =====================================================
     LOADING
  ===================================================== */

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading system settings...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-1">
      {/* HEADER */}
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold">System Settings</h1>
          <p className="text-muted-foreground">
            Primey HR Cloud — Platform Governance & Email Configuration
          </p>
        </div>

        <Button
          variant="outline"
          onClick={loadSettings}
          className="w-full md:w-auto"
          disabled={isBusy}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* PLATFORM CONTROL */}
      <Card className="rounded-2xl border-border/60 shadow-sm">
        <CardHeader>
          <CardTitle>Platform Control</CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <Label>Platform Active</Label>
              <p className="text-sm text-muted-foreground">
                Global kill switch for the whole platform
              </p>
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

          <div className="flex items-center justify-between gap-4">
            <div>
              <Label>Maintenance Mode</Label>
              <p className="text-sm text-muted-foreground">
                Only super admin can access when enabled
              </p>
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

          <div className="flex items-center justify-between gap-4">
            <div>
              <Label>Readonly Mode</Label>
              <p className="text-sm text-muted-foreground">
                Blocks write actions and keeps read-only access
              </p>
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

          <div className="flex items-center justify-between gap-4">
            <div>
              <Label>Billing Enabled</Label>
              <p className="text-sm text-muted-foreground">
                Enable or disable billing system access
              </p>
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
      <div className="grid gap-4 lg:grid-cols-4">
        <Card className="rounded-2xl border-border/60 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Mail className="h-4 w-4" />
              Email Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={emailSettings.is_ready ? "default" : "secondary"}>
              {emailSettings.is_ready ? "Ready" : "Incomplete"}
            </Badge>

            <p className="mt-3 text-sm text-muted-foreground">
              {emailSettings.is_ready
                ? "SMTP configuration is ready for sending."
                : "Some required email fields are still missing."}
            </p>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-border/60 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Server className="h-4 w-4" />
              From Email
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm font-medium break-all">
              {emailSettings.from_email || "Not configured"}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Sender used for test email and outbound SMTP
            </p>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-border/60 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <ShieldCheck className="h-4 w-4" />
              Validation
            </CardTitle>
          </CardHeader>
          <CardContent>
            {emailMissingFields.length === 0 && emailValidationErrors.length === 0 ? (
              <div className="flex items-start gap-2 text-sm">
                <CheckCircle2 className="mt-0.5 h-4 w-4 text-green-600" />
                <span>All required SMTP fields are valid.</span>
              </div>
            ) : (
              <div className="space-y-2 text-sm">
                {emailMissingFields.length > 0 && (
                  <>
                    <div className="flex items-start gap-2">
                      <AlertCircle className="mt-0.5 h-4 w-4 text-amber-600" />
                      <span>Missing fields:</span>
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
              Last Updated
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm font-medium">
              {formatDateTime(emailSettings.updated_at)}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Latest saved email configuration time
            </p>
          </CardContent>
        </Card>
      </div>

      {/* EMAIL SETTINGS */}
      <Card className="rounded-2xl border-border/60 shadow-sm">
        <CardHeader className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <CardTitle>Email Settings</CardTitle>

          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={hasEmailChanges ? "secondary" : "outline"}>
              {hasEmailChanges ? "Unsaved Changes" : "Saved"}
            </Badge>

            <Button
              type="button"
              variant="outline"
              onClick={handleResetEmailChanges}
              disabled={!hasEmailChanges || isBusy}
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Reset Changes
            </Button>

            <Button
              type="button"
              onClick={handleSaveAllEmail}
              disabled={!canSaveAllEmail}
            >
              {savingAll ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save All
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>SMTP Host</Label>
              <Input
                value={emailSettings.smtp_server}
                disabled={isBusy}
                onChange={(e) =>
                  setEmailSettings((prev) => ({
                    ...prev,
                    smtp_server: e.target.value
                  }))
                }
                onBlur={() => {
                  if (emailSettings.smtp_server !== initialEmailSettings.smtp_server) {
                    updateEmailSetting("smtp_server", emailSettings.smtp_server)
                  }
                }}
                placeholder="smtp.gmail.com"
              />
            </div>

            <div className="space-y-2">
              <Label>SMTP Port</Label>
              <Input
                type="number"
                value={emailSettings.smtp_port}
                disabled={isBusy}
                onChange={(e) =>
                  setEmailSettings((prev) => ({
                    ...prev,
                    smtp_port: Number(e.target.value || 0)
                  }))
                }
                onBlur={() => {
                  if (Number(emailSettings.smtp_port) !== Number(initialEmailSettings.smtp_port)) {
                    updateEmailSetting("smtp_port", emailSettings.smtp_port)
                  }
                }}
                placeholder="587"
              />
            </div>

            <div className="space-y-2">
              <Label>Username / Sender Email</Label>
              <Input
                type="email"
                value={emailSettings.username}
                disabled={isBusy}
                onChange={(e) =>
                  setEmailSettings((prev) => ({
                    ...prev,
                    username: e.target.value
                  }))
                }
                onBlur={() => {
                  if (emailSettings.username !== initialEmailSettings.username) {
                    updateEmailSetting("username", emailSettings.username)
                  }
                }}
                placeholder="info@yourdomain.com"
              />
            </div>

            <div className="space-y-2">
              <Label>Password / App Password</Label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  value={emailSettings.password}
                  disabled={isBusy}
                  onChange={(e) =>
                    setEmailSettings((prev) => ({
                      ...prev,
                      password: e.target.value
                    }))
                  }
                  onBlur={() => {
                    if (emailSettings.password !== initialEmailSettings.password) {
                      updateEmailSetting("password", emailSettings.password)
                    }
                  }}
                  placeholder="Enter SMTP password"
                  className="pr-11"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground disabled:pointer-events-none disabled:opacity-50"
                  disabled={isBusy}
                  aria-label={showPassword ? "Hide password" : "Show password"}
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

          <div className="flex items-center justify-between rounded-xl border p-4">
            <div className="space-y-1">
              <Label>Use TLS</Label>
              <p className="text-sm text-muted-foreground">
                Recommended for Gmail and most secure SMTP providers
              </p>
            </div>

            <Switch
              checked={emailSettings.use_tls}
              disabled={savingField === "email:use_tls" || isBusy}
              onCheckedChange={(v) => {
                setEmailSettings((prev) => ({
                  ...prev,
                  use_tls: v
                }))
                updateEmailSetting("use_tls", v)
              }}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-[1fr_auto]">
            <div className="space-y-2">
              <Label>Test Email Recipient</Label>
              <Input
                type="email"
                value={testEmail}
                disabled={isBusy}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder="example@domain.com"
              />
            </div>

            <div className="flex items-end gap-2">
              <Button
                variant="outline"
                onClick={handleTestEmail}
                disabled={testingEmail || !emailSettings.is_ready || isBusy}
                className="w-full md:w-auto"
              >
                {testingEmail ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Mail className="mr-2 h-4 w-4" />
                )}
                Test Email
              </Button>
            </div>
          </div>

          <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
            <p className="font-medium text-foreground">Notes</p>
            <ul className="mt-2 space-y-1">
              <li>• For Gmail, use App Password instead of your normal password.</li>
              <li>• Save happens automatically when you leave each field.</li>
              <li>• Save All is useful when editing multiple fields together.</li>
              <li>• Test Email uses the saved SMTP values from backend.</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* MODULES */}
      <Card className="rounded-2xl border-border/60 shadow-sm">
        <CardHeader>
          <CardTitle>System Modules</CardTitle>
        </CardHeader>

        <CardContent className="space-y-5">
          {Object.keys(modules).length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No module flags returned from backend.
            </p>
          ) : (
            Object.entries(modules).map(([moduleKey, enabled]) => (
              <div
                key={moduleKey}
                className="flex items-center justify-between gap-4"
              >
                <div>
                  <Label className="capitalize">{moduleKey}</Label>
                  <p className="text-sm text-muted-foreground">
                    UI preview only for now
                  </p>
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
      <div className="flex flex-wrap items-center gap-3">
        <Button
          variant="outline"
          onClick={loadSettings}
          disabled={isBusy}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Reload
        </Button>

        <Badge variant={hasEmailChanges ? "secondary" : "outline"}>
          {hasEmailChanges ? "There are unsaved email changes" : "All email changes are saved"}
        </Badge>
      </div>
    </div>
  )
}