"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import {
  ArrowLeft,
  BadgeCheck,
  BellRing,
  CheckCircle2,
  Copy,
  Globe,
  Loader2,
  LogOut,
  QrCode,
  RefreshCw,
  Save,
  Send,
  Settings2,
  ShieldCheck,
  Smartphone,
  Sparkles,
  TestTube2,
  Wifi,
  WifiOff,
} from "lucide-react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"

type Locale = "ar" | "en"
type ConnectionMode = "qr" | "pairing_code"
type SessionStatus =
  | "disconnected"
  | "qr_pending"
  | "pair_pending"
  | "connected"
  | "failed"

type CompanyWhatsAppConfig = {
  is_active?: boolean
  is_enabled?: boolean
  provider?: string
  company_name?: string
  default_country_code?: string
  default_test_recipient?: string
  send_test_enabled?: boolean
  allow_templates?: boolean
  send_employee_alerts?: boolean
  send_attendance_alerts?: boolean
  send_leave_alerts?: boolean
  send_payroll_alerts?: boolean
  send_billing_alerts?: boolean
  send_system_copy_alerts?: boolean
  session_name?: string
  session_mode?: ConnectionMode
  session_status?: SessionStatus
  session_connected_phone?: string
  session_device_label?: string
  session_qr_code?: string
  session_pairing_code?: string
  session_last_connected_at?: string | null
  last_health_check_at?: string | null
  last_error_message?: string
}

type SettingsResponse = {
  success?: boolean
  config?: CompanyWhatsAppConfig
  message?: string
}

type StatusResponse = {
  success?: boolean
  connected?: boolean
  provider?: string
  is_active?: boolean
  is_enabled?: boolean
  session_status?: SessionStatus
  session_name?: string | null
  session_mode?: ConnectionMode | null
  qr_code?: string | null
  pairing_code?: string | null
  connected_phone?: string | null
  device_label?: string | null
  last_connected_at?: string | null
  last_check_at?: string | null
  gateway_message?: string | null
  last_error_message?: string | null
  message?: string
}

type SaveResponse = {
  success?: boolean
  message?: string
  config?: CompanyWhatsAppConfig
}

type TestResponse = {
  success?: boolean
  message?: string
}

type SessionActionResponse = {
  success?: boolean
  message?: string
  qr_code?: string | null
  pairing_code?: string | null
  session_status?: SessionStatus
  connected_phone?: string | null
  device_label?: string | null
  last_connected_at?: string | null
}

type FormState = {
  is_active: boolean
  provider: "whatsapp_web_session"
  default_country_code: string
  send_test_enabled: boolean
  allow_templates: boolean
  default_test_recipient: string
  send_employee_alerts: boolean
  send_attendance_alerts: boolean
  send_leave_alerts: boolean
  send_payroll_alerts: boolean
  send_billing_alerts: boolean
  send_system_copy_alerts: boolean
  session_name: string
  session_mode: ConnectionMode
  pairing_phone: string
  test_phone: string
  test_message: string
}

const API = {
  settings: "/api/company/whatsapp/settings/",
  saveSettings: "/api/company/whatsapp/settings/update/",
  status: "/api/company/whatsapp/status/",
  sendTest: "/api/company/whatsapp/send-test/",
  createQr: "/api/company/whatsapp/session/create-qr/",
  createPairingCode: "/api/company/whatsapp/session/create-pairing-code/",
  disconnectSession: "/api/company/whatsapp/session/disconnect/",
} as const

const WEB_SESSION_PROVIDER = "whatsapp_web_session" as const
const DEFAULT_COUNTRY_CODE = "966"
const DEFAULT_TEST_MESSAGE_AR =
  "رسالة اختبار من Primey HR Cloud - Company WhatsApp Center"
const DEFAULT_TEST_MESSAGE_EN =
  "Test message from Primey HR Cloud - Company WhatsApp Center"

const translations = {
  ar: {
    badge: "Company WhatsApp Settings",
    title: "إعدادات واتساب للشركة",
    description:
      "إدارة جلسة واتساب الخاصة بالشركة عبر QR أو كود الربط مع إعدادات التفعيل ورسائل الاختبار.",
    back: "رجوع",
    refresh: "تحديث",
    save: "حفظ الإعدادات",
    loading: "جاري تحميل إعدادات واتساب للشركة...",
    loadError: "تعذر تحميل إعدادات واتساب للشركة",
    saveError: "تعذر حفظ إعدادات واتساب للشركة",
    saveSuccess: "تم حفظ إعدادات واتساب للشركة بنجاح",
    testError: "تعذر إرسال رسالة الاختبار",
    testSuccess: "تم إرسال رسالة الاختبار بنجاح",
    enterTestPhone: "أدخل رقم الجوال أولًا",
    noCopyValue: "لا توجد قيمة لنسخها",
    copied: "تم النسخ بنجاح",
    connected: "متصل",
    disconnected: "غير متصل",
    active: "نشط",
    inactive: "غير نشط",
    currentConnection: "حالة الربط الحالية",
    currentConnectionDesc: "عرض سريع لحالة جلسة الشركة ومدى جاهزية الربط.",
    lastCheck: "آخر فحص",
    testMessages: "رسائل الاختبار",
    enabled: "مفعلة",
    disabled: "معطلة",
    basicSettings: "الإعدادات الأساسية",
    basicSettingsDesc: "الإعدادات الرئيسية الخاصة بجلسة واتساب للشركة.",
    enableCompany: "تفعيل واتساب للشركة",
    enableCompanyDesc: "تشغيل أو إيقاف تكامل واتساب لهذه الشركة.",
    allowTemplates: "السماح بالقوالب",
    allowTemplatesDesc: "تمكين استخدام القوالب والأحداث المرتبطة بها.",
    enableTestMessages: "تمكين رسائل الاختبار",
    enableTestMessagesDesc: "السماح بإرسال رسائل اختبار قبل الاستخدام الفعلي.",
    provider: "المزوّد",
    defaultCountryCode: "رمز الدولة الافتراضي",
    defaultTestRecipient: "رقم الاختبار الافتراضي",
    sendTestTitle: "إرسال رسالة اختبار",
    sendTestDesc: "اختبر الجلسة الفعلية بعد نجاح الربط.",
    testPhone: "رقم الجوال",
    testMessage: "رسالة الاختبار",
    sendTest: "إرسال اختبار",
    testDisabled: "رسائل الاختبار معطلة حاليًا",
    readiness: "مؤشر الجاهزية",
    readinessDesc: "تحقق سريع من العناصر الأساسية المطلوبة.",
    ready: "جاهز",
    missing: "ناقص",
    summary: "ملخص الإعدادات",
    summaryDesc: "عرض مختصر للقيم الحالية",
    notConfigured: "غير مضبوط",
    notSpecified: "غير محدد",
    activationCheck: "تفعيل الشركة",
    sessionTitle: "ربط الجلسة",
    sessionDesc:
      "يمكنك الربط عبر QR أو عبر رقم الجوال + كود الربط باستخدام WhatsApp Web Session.",
    sessionStatus: "حالة الجلسة",
    sessionName: "اسم الجلسة",
    sessionMode: "طريقة الربط",
    qrMode: "QR Code",
    pairMode: "رقم الجوال + كود الربط",
    pairingPhone: "رقم الجوال للربط",
    createQr: "إنشاء QR",
    createPairingCode: "إنشاء كود ربط",
    disconnectSession: "فصل الجلسة",
    pairingReady: "كود الربط جاهز",
    connectedPhone: "الرقم المرتبط",
    deviceLabel: "الجهاز",
    lastConnectedAt: "آخر اتصال",
    scanQrHint: "افتح واتساب في الجوال ← الأجهزة المرتبطة ← امسح رمز QR.",
    pairingHint: "أدخل رقم الجوال ثم أكمل الربط باستخدام الكود الظاهر.",
    sessionDisconnected: "الجلسة غير متصلة",
    sessionQrPending: "بانتظار مسح QR",
    sessionPairPending: "بانتظار تأكيد الربط",
    sessionConnected: "تم الربط بنجاح",
    sessionFailed: "فشل الربط",
    pairingCode: "كود الربط",
    generateFirst: "قم بإنشاء QR أو كود ربط أولًا",
    enterPairingPhone: "أدخل رقم الجوال أولًا",
    qrCreated: "تم إنشاء QR بنجاح",
    pairingCreated: "تم إنشاء كود الربط بنجاح",
    sessionDisconnectedOk: "تم فصل الجلسة بنجاح",
    sessionActionError: "تعذر تنفيذ العملية على الجلسة",
    connectionMethodFixed: "طريقة الربط المعتمدة",
    webSessionOnly: "WhatsApp Web Session Only",
    qrButtonHint: "زر إنشاء QR يعمل فقط عندما تكون طريقة الربط QR.",
    pairingButtonHint:
      "زر إنشاء كود الربط يعمل فقط عندما تكون طريقة الربط رقم الجوال + كود الربط.",
    employeeAlerts: "تنبيهات الموظفين",
    attendanceAlerts: "تنبيهات الحضور",
    leaveAlerts: "تنبيهات الإجازات",
    payrollAlerts: "تنبيهات الرواتب",
    billingAlerts: "تنبيهات الفوترة",
    systemCopyAlerts: "نسخة للنظام",
    alerts: "التنبيهات",
    alertsDesc: "التحكم في أنواع الإشعارات التي ترسل عبر واتساب للشركة.",
  },
  en: {
    badge: "Company WhatsApp Settings",
    title: "Company WhatsApp Settings",
    description:
      "Manage the company WhatsApp session using QR or pairing code, with activation and test settings.",
    back: "Back",
    refresh: "Refresh",
    save: "Save Settings",
    loading: "Loading company WhatsApp settings...",
    loadError: "Unable to load company WhatsApp settings",
    saveError: "Unable to save company WhatsApp settings",
    saveSuccess: "Company WhatsApp settings saved successfully",
    testError: "Unable to send test message",
    testSuccess: "Test message sent successfully",
    enterTestPhone: "Enter a phone number first",
    noCopyValue: "No value available to copy",
    copied: "Copied successfully",
    connected: "Connected",
    disconnected: "Disconnected",
    active: "Active",
    inactive: "Inactive",
    currentConnection: "Current Connection Status",
    currentConnectionDesc: "Quick overview of the company session and readiness state.",
    lastCheck: "Last Check",
    testMessages: "Test Messages",
    enabled: "Enabled",
    disabled: "Disabled",
    basicSettings: "Basic Settings",
    basicSettingsDesc: "Main settings for the company WhatsApp Web Session integration.",
    enableCompany: "Enable Company WhatsApp",
    enableCompanyDesc: "Turn WhatsApp integration on or off for this company.",
    allowTemplates: "Allow Templates",
    allowTemplatesDesc: "Enable templates and related event usage.",
    enableTestMessages: "Enable Test Messages",
    enableTestMessagesDesc: "Allow sending test messages before real use.",
    provider: "Provider",
    defaultCountryCode: "Default Country Code",
    defaultTestRecipient: "Default Test Recipient",
    sendTestTitle: "Send Test Message",
    sendTestDesc: "Test the live session after a successful connection.",
    testPhone: "Phone Number",
    testMessage: "Test Message",
    sendTest: "Send Test",
    testDisabled: "Test messages are currently disabled",
    readiness: "Readiness Indicator",
    readinessDesc: "Quick validation of required items.",
    ready: "Ready",
    missing: "Missing",
    summary: "Settings Summary",
    summaryDesc: "Quick view of the current values",
    notConfigured: "Not configured",
    notSpecified: "Not specified",
    activationCheck: "Company Activation",
    sessionTitle: "Session Connection",
    sessionDesc:
      "You can connect using QR Code or phone number + pairing code through WhatsApp Web Session.",
    sessionStatus: "Session Status",
    sessionName: "Session Name",
    sessionMode: "Connection Mode",
    qrMode: "QR Code",
    pairMode: "Phone Number + Pairing Code",
    pairingPhone: "Pairing Phone Number",
    createQr: "Generate QR",
    createPairingCode: "Generate Pairing Code",
    disconnectSession: "Disconnect Session",
    pairingReady: "Pairing code is ready",
    connectedPhone: "Connected Phone",
    deviceLabel: "Device",
    lastConnectedAt: "Last Connected",
    scanQrHint: "Open WhatsApp on your phone, go to linked devices, then scan the QR.",
    pairingHint: "Enter the phone number and complete linking using the displayed code.",
    sessionDisconnected: "Session disconnected",
    sessionQrPending: "Waiting for QR scan",
    sessionPairPending: "Waiting for pairing confirmation",
    sessionConnected: "Session connected",
    sessionFailed: "Connection failed",
    pairingCode: "Pairing Code",
    generateFirst: "Generate a QR or pairing code first",
    enterPairingPhone: "Enter a phone number first",
    qrCreated: "QR generated successfully",
    pairingCreated: "Pairing code generated successfully",
    sessionDisconnectedOk: "Session disconnected successfully",
    sessionActionError: "Unable to execute session action",
    connectionMethodFixed: "Applied Connection Method",
    webSessionOnly: "WhatsApp Web Session Only",
    qrButtonHint: "Generate QR only works when the connection mode is QR.",
    pairingButtonHint:
      "Generate Pairing Code only works when the connection mode is Phone Number + Pairing Code.",
    employeeAlerts: "Employee Alerts",
    attendanceAlerts: "Attendance Alerts",
    leaveAlerts: "Leave Alerts",
    payrollAlerts: "Payroll Alerts",
    billingAlerts: "Billing Alerts",
    systemCopyAlerts: "System Copy Alerts",
    alerts: "Alerts",
    alertsDesc: "Control which alert types are sent over company WhatsApp.",
  },
} as const

function detectLocale(): Locale {
  if (typeof document === "undefined") return "ar"
  const htmlLang = document.documentElement.lang?.toLowerCase() || ""
  return htmlLang.startsWith("en") ? "en" : "ar"
}

function isLocalHostname(hostname: string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1"
}

function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, "")
}

function getApiBaseCandidates(): string[] {
  const envBase = normalizeBaseUrl(process.env.NEXT_PUBLIC_API_URL || "")

  if (envBase) {
    return [envBase]
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location
    return [`${protocol}//${hostname}:8000`]
  }

  return []
}

function normalizePath(path: string): string {
  if (!path) return "/"
  return path.startsWith("/") ? path : `/${path}`
}

function joinUrl(base: string, path: string): string {
  return `${base.replace(/\/+$/, "")}${path}`
}

function buildCandidateUrls(path: string): string[] {
  const cleanPath = normalizePath(path)
  const urls = new Set<string>()

  for (const base of getApiBaseCandidates()) {
    const full = joinUrl(base, cleanPath)
    urls.add(full)
    if (!full.endsWith("/")) {
      urls.add(`${full}/`)
    }
  }

  return Array.from(urls)
}

function getCookie(name: string): string {
  if (typeof document === "undefined") return ""
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop()?.split(";").shift() || ""
  return ""
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"

  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

function withCacheBust(value: string | null | undefined, nonce: number) {
  if (!value) return null
  if (value.startsWith("data:")) return value
  const separator = value.includes("?") ? "&" : "?"
  return `${value}${separator}v=${nonce}`
}

async function readResponseSafely<T>(
  response: Response,
  requestLabel: string
): Promise<T & { success?: boolean; message?: string }> {
  const contentType = (response.headers.get("content-type") || "").toLowerCase()
  const rawText = await response.text()

  if (!rawText) {
    return {} as T & { success?: boolean; message?: string }
  }

  if (contentType.includes("application/json")) {
    try {
      return JSON.parse(rawText) as T & { success?: boolean; message?: string }
    } catch {
      throw new Error(`Invalid JSON response from ${requestLabel}`)
    }
  }

  const trimmed = rawText.trim()

  if (trimmed.startsWith("<!DOCTYPE") || trimmed.startsWith("<html")) {
    throw new Error(`Non-JSON response returned from ${requestLabel}`)
  }

  try {
    return JSON.parse(trimmed) as T & { success?: boolean; message?: string }
  } catch {
    throw new Error(`Unexpected response format from ${requestLabel}`)
  }
}

async function fetchJson<T>(path: string): Promise<T> {
  const candidates = buildCandidateUrls(path)

  if (!candidates.length) {
    throw new Error("API base URL is not configured.")
  }

  let lastError: Error | null = null

  for (const url of candidates) {
    try {
      const response = await fetch(url, {
        method: "GET",
        credentials: "include",
        cache: "no-store",
        headers: { Accept: "application/json" },
      })

      if (!response.ok) {
        let message = `GET ${url} failed with ${response.status}`
        try {
          const data = await readResponseSafely<{ message?: string }>(response, url)
          if (data?.message) message = data.message
        } catch {
          // ignore
        }
        lastError = new Error(message)
        continue
      }

      return await readResponseSafely<T>(response, url)
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("Unknown fetch error")
    }
  }

  throw lastError || new Error(`Failed to fetch ${path}`)
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const candidates = buildCandidateUrls(path)
  const csrfToken = getCookie("csrftoken")

  if (!candidates.length) {
    throw new Error("API base URL is not configured.")
  }

  let lastError: Error | null = null

  for (const url of candidates) {
    try {
      const response = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
        body: JSON.stringify(body),
      })

      const data = await readResponseSafely<T>(response, url)

      if (!response.ok) {
        lastError = new Error(
          (data &&
            typeof data === "object" &&
            "message" in data &&
            typeof data.message === "string" &&
            data.message) ||
            `POST ${url} failed with ${response.status}`
        )
        continue
      }

      return data
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("Unknown post error")
    }
  }

  throw lastError || new Error(`Failed to post to ${path}`)
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function mergeSessionActionIntoStatus(
  current: StatusResponse | null,
  data: SessionActionResponse,
  fallbackMode: ConnectionMode
): StatusResponse {
  const nextStatus = data.session_status || current?.session_status || "disconnected"

  return {
    ...(current || {}),
    success: true,
    message: data.message || current?.message,
    session_mode: current?.session_mode || fallbackMode,
    session_status: nextStatus,
    qr_code: data.qr_code !== undefined ? data.qr_code : (current?.qr_code ?? null),
    pairing_code:
      data.pairing_code !== undefined ? data.pairing_code : (current?.pairing_code ?? null),
    connected_phone:
      data.connected_phone !== undefined
        ? data.connected_phone
        : (current?.connected_phone ?? null),
    device_label:
      data.device_label !== undefined ? data.device_label : (current?.device_label ?? null),
    last_connected_at:
      data.last_connected_at !== undefined
        ? data.last_connected_at
        : (current?.last_connected_at ?? null),
    connected: nextStatus === "connected" ? true : (current?.connected ?? false),
  }
}

export default function CompanyWhatsAppSettingsPage() {
  const [locale, setLocale] = useState<Locale>("ar")
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [creatingQr, setCreatingQr] = useState(false)
  const [creatingPairing, setCreatingPairing] = useState(false)
  const [disconnecting, setDisconnecting] = useState(false)

  const [companyName, setCompanyName] = useState("")
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [qrNonce, setQrNonce] = useState(0)
  const [pairingNonce, setPairingNonce] = useState(0)

  const [form, setForm] = useState<FormState>({
    is_active: false,
    provider: WEB_SESSION_PROVIDER,
    default_country_code: DEFAULT_COUNTRY_CODE,
    send_test_enabled: true,
    allow_templates: true,
    default_test_recipient: "",
    send_employee_alerts: true,
    send_attendance_alerts: true,
    send_leave_alerts: true,
    send_payroll_alerts: true,
    send_billing_alerts: true,
    send_system_copy_alerts: false,
    session_name: "",
    session_mode: "qr",
    pairing_phone: "",
    test_phone: "",
    test_message: DEFAULT_TEST_MESSAGE_AR,
  })

  useEffect(() => {
    setLocale(detectLocale())

    const observer = new MutationObserver(() => setLocale(detectLocale()))
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    return () => observer.disconnect()
  }, [])

  const t = translations[locale]
  const isArabic = locale === "ar"
  const isConnected = status?.session_status === "connected"
  const isQrMode = form.session_mode === "qr"
  const isPairMode = form.session_mode === "pairing_code"

  const sessionStatusLabel = useMemo(() => {
    switch (status?.session_status) {
      case "qr_pending":
        return t.sessionQrPending
      case "pair_pending":
        return t.sessionPairPending
      case "connected":
        return t.sessionConnected
      case "failed":
        return t.sessionFailed
      default:
        return t.sessionDisconnected
    }
  }, [status?.session_status, t])

  const qrImageSrc = useMemo(
    () => withCacheBust(status?.qr_code ?? null, qrNonce),
    [status?.qr_code, qrNonce]
  )

  useEffect(() => {
    setForm((prev) => ({
      ...prev,
      test_message:
        prev.test_message === DEFAULT_TEST_MESSAGE_AR ||
        prev.test_message === DEFAULT_TEST_MESSAGE_EN
          ? locale === "ar"
            ? DEFAULT_TEST_MESSAGE_AR
            : DEFAULT_TEST_MESSAGE_EN
          : prev.test_message,
    }))
  }, [locale])

  const loadPage = useCallback(
    async (isRefresh = false) => {
      try {
        if (isRefresh) setRefreshing(true)
        else setLoading(true)

        const [settingsRes, statusRes] = await Promise.all([
          fetchJson<SettingsResponse>(API.settings),
          fetchJson<StatusResponse>(API.status),
        ])

        const config = settingsRes?.config || {}
        setCompanyName(config.company_name || "")
        setStatus(statusRes || null)

        if (statusRes?.qr_code) {
          setQrNonce(Date.now())
        }

        if (statusRes?.pairing_code) {
          setPairingNonce(Date.now())
        }

        setForm((prev) => ({
          ...prev,
          is_active: !!config.is_active,
          provider: WEB_SESSION_PROVIDER,
          default_country_code: config.default_country_code || DEFAULT_COUNTRY_CODE,
          send_test_enabled: config.send_test_enabled ?? true,
          allow_templates: config.allow_templates ?? true,
          default_test_recipient: config.default_test_recipient || "",
          send_employee_alerts: config.send_employee_alerts ?? true,
          send_attendance_alerts: config.send_attendance_alerts ?? true,
          send_leave_alerts: config.send_leave_alerts ?? true,
          send_payroll_alerts: config.send_payroll_alerts ?? true,
          send_billing_alerts: config.send_billing_alerts ?? true,
          send_system_copy_alerts: config.send_system_copy_alerts ?? false,
          session_name: config.session_name || statusRes?.session_name || "",
          session_mode: config.session_mode || statusRes?.session_mode || "qr",
          pairing_phone: prev.pairing_phone || "",
          test_phone: config.default_test_recipient || prev.test_phone || "",
          test_message:
            prev.test_message ||
            (locale === "ar" ? DEFAULT_TEST_MESSAGE_AR : DEFAULT_TEST_MESSAGE_EN),
        }))
      } catch (error) {
        console.error("Failed to load company WhatsApp settings:", error)
        toast.error(error instanceof Error ? error.message : t.loadError)
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [locale, t.loadError]
  )

  const pollSessionStatus = useCallback(
    async ({
      expect,
      attempts = 20,
      delayMs = 700,
    }: {
      expect: "qr" | "pairing"
      attempts?: number
      delayMs?: number
    }) => {
      for (let i = 0; i < attempts; i += 1) {
        try {
          const latestStatus = await fetchJson<StatusResponse>(API.status)
          setStatus(latestStatus || null)

          if (latestStatus?.qr_code) {
            setQrNonce(Date.now())
          }

          if (latestStatus?.pairing_code) {
            setPairingNonce(Date.now())
          }

          if (expect === "qr" && latestStatus?.qr_code) {
            return latestStatus
          }

          if (expect === "pairing" && latestStatus?.pairing_code) {
            return latestStatus
          }

          if (latestStatus?.session_status === "connected") {
            return latestStatus
          }
        } catch (error) {
          console.error("Polling session status failed:", error)
        }

        await sleep(delayMs)
      }

      return null
    },
    []
  )

  useEffect(() => {
    loadPage()
  }, [loadPage])

  const handleChange = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleCopy = async (value: string) => {
    if (!value) {
      toast.error(t.noCopyValue)
      return
    }

    try {
      await navigator.clipboard.writeText(value)
      toast.success(t.copied)
    } catch {
      toast.error(t.noCopyValue)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)

      const payload = {
        is_active: form.is_active,
        is_enabled: form.is_active,
        provider: WEB_SESSION_PROVIDER,
        default_country_code: form.default_country_code.trim(),
        allow_templates: form.allow_templates,
        send_test_enabled: form.send_test_enabled,
        default_test_recipient: form.default_test_recipient.trim(),
        send_employee_alerts: form.send_employee_alerts,
        send_attendance_alerts: form.send_attendance_alerts,
        send_leave_alerts: form.send_leave_alerts,
        send_payroll_alerts: form.send_payroll_alerts,
        send_billing_alerts: form.send_billing_alerts,
        send_system_copy_alerts: form.send_system_copy_alerts,
        session_name: form.session_name.trim(),
        session_mode: form.session_mode,
      }

      const data = await postJson<SaveResponse>(API.saveSettings, payload)

      if (!data?.success) throw new Error(data?.message || t.saveError)

      toast.success(data?.message || t.saveSuccess)
      await loadPage(true)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t.saveError)
    } finally {
      setSaving(false)
    }
  }

  const handleSendTest = async () => {
    try {
      if (!form.test_phone.trim()) {
        toast.error(t.enterTestPhone)
        return
      }

      setTesting(true)

      const data = await postJson<TestResponse>(API.sendTest, {
        phone_number: form.test_phone.trim(),
        recipient_phone: form.test_phone.trim(),
        message: form.test_message.trim(),
      })

      if (!data?.success) throw new Error(data?.message || t.testError)

      toast.success(data?.message || t.testSuccess)
      await loadPage(true)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t.testError)
    } finally {
      setTesting(false)
    }
  }

  const handleCreateQr = async () => {
    try {
      setCreatingQr(true)

      const data = await postJson<SessionActionResponse>(API.createQr, {
        session_name: form.session_name.trim(),
        mode: "qr",
      })

      if (!data?.success) throw new Error(data?.message || t.sessionActionError)

      setStatus((prev) => mergeSessionActionIntoStatus(prev, data, "qr"))

      if (data?.qr_code) {
        setQrNonce(Date.now())
      }

      toast.success(data?.message || t.qrCreated)

      const immediateStatus = await fetchJson<StatusResponse>(API.status).catch(() => null)
      if (immediateStatus) {
        setStatus(immediateStatus)
        if (immediateStatus.qr_code) {
          setQrNonce(Date.now())
          await loadPage(true)
          return
        }
      }

      await pollSessionStatus({
        expect: "qr",
        attempts: 20,
        delayMs: 700,
      })

      await loadPage(true)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t.sessionActionError)
    } finally {
      setCreatingQr(false)
    }
  }

  const handleCreatePairingCode = async () => {
    try {
      if (!form.pairing_phone.trim()) {
        toast.error(t.enterPairingPhone)
        return
      }

      setCreatingPairing(true)

      const data = await postJson<SessionActionResponse>(API.createPairingCode, {
        session_name: form.session_name.trim(),
        phone_number: form.pairing_phone.trim(),
        mode: "pairing_code",
      })

      if (!data?.success) throw new Error(data?.message || t.sessionActionError)

      setStatus((prev) => mergeSessionActionIntoStatus(prev, data, "pairing_code"))

      if (data?.pairing_code) {
        setPairingNonce(Date.now())
      }

      toast.success(data?.message || t.pairingCreated)

      const immediateStatus = await fetchJson<StatusResponse>(API.status).catch(() => null)
      if (immediateStatus) {
        setStatus(immediateStatus)
        if (immediateStatus.pairing_code) {
          setPairingNonce(Date.now())
          await loadPage(true)
          return
        }
      }

      await pollSessionStatus({
        expect: "pairing",
        attempts: 20,
        delayMs: 700,
      })

      await loadPage(true)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t.sessionActionError)
    } finally {
      setCreatingPairing(false)
    }
  }

  const handleDisconnectSession = async () => {
    try {
      setDisconnecting(true)

      const data = await postJson<SessionActionResponse>(API.disconnectSession, {
        session_name: form.session_name.trim(),
      })

      if (!data?.success) throw new Error(data?.message || t.sessionActionError)

      setStatus((prev) => ({
        ...(prev || {}),
        success: true,
        message: data.message || prev?.message,
        session_status: data.session_status || "disconnected",
        connected: false,
        qr_code: null,
        pairing_code: null,
        connected_phone: null,
      }))

      setQrNonce(Date.now())
      setPairingNonce(Date.now())

      toast.success(data?.message || t.sessionDisconnectedOk)
      await loadPage(true)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t.sessionActionError)
    } finally {
      setDisconnecting(false)
    }
  }

  const checklist = useMemo(
    () => [
      { label: t.activationCheck, ok: form.is_active },
      { label: t.sessionName, ok: !!form.session_name.trim() },
      { label: t.defaultCountryCode, ok: !!form.default_country_code.trim() },
      { label: t.testMessages, ok: form.send_test_enabled },
    ],
    [form, t]
  )

  if (loading) {
    return (
      <div
        dir={isArabic ? "rtl" : "ltr"}
        className="flex min-h-[60vh] items-center justify-center p-6"
      >
        <div className="flex items-center gap-3 rounded-2xl border bg-background px-5 py-4 shadow-sm">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          <span className="text-sm font-medium">{t.loading}</span>
        </div>
      </div>
    )
  }

  return (
    <div dir={isArabic ? "rtl" : "ltr"} className="space-y-6 p-4 md:p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full border bg-background/70 px-3 py-1 text-sm shadow-sm backdrop-blur">
            <Sparkles className="h-4 w-4" />
            <span>{t.badge}</span>
          </div>

          <div>
            <h1 className="text-2xl font-bold tracking-tight md:text-3xl">{t.title}</h1>
            <p className="text-muted-foreground">{t.description}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button asChild variant="outline" className="gap-2">
            <Link href="/company/whatsapp">
              <ArrowLeft className="h-4 w-4" />
              {t.back}
            </Link>
          </Button>

          <Button
            variant="outline"
            onClick={() => loadPage(true)}
            disabled={refreshing}
            className="gap-2"
          >
            {refreshing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            {t.refresh}
          </Button>

          <Button onClick={handleSave} disabled={saving} className="gap-2">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            {t.save}
          </Button>
        </div>
      </div>

      <Card className="overflow-hidden border-0 shadow-xl">
        <div className="bg-gradient-to-l from-primary/10 via-background to-background">
          <CardHeader className="pb-4">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={isConnected ? "default" : "destructive"} className="gap-1">
                    {isConnected ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
                    {isConnected ? t.connected : t.disconnected}
                  </Badge>

                  <Badge variant={form.is_active ? "default" : "secondary"}>
                    {form.is_active ? t.active : t.inactive}
                  </Badge>

                  <Badge variant="outline">{WEB_SESSION_PROVIDER}</Badge>
                </div>

                <div>
                  <CardTitle className="text-xl">{companyName || t.notConfigured}</CardTitle>
                  <CardDescription className="mt-1">{t.currentConnectionDesc}</CardDescription>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border bg-background/80 p-4 shadow-sm backdrop-blur">
                  <p className="text-xs text-muted-foreground">{t.sessionStatus}</p>
                  <div className="mt-1 flex items-center gap-2 text-sm font-semibold">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    <span>{sessionStatusLabel}</span>
                  </div>
                </div>

                <div className="rounded-2xl border bg-background/80 p-4 shadow-sm backdrop-blur">
                  <p className="text-xs text-muted-foreground">{t.lastCheck}</p>
                  <p className="mt-1 text-sm font-semibold">
                    {formatDateTime(status?.last_check_at)}
                  </p>
                </div>
              </div>
            </div>
          </CardHeader>
        </div>

        <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.connectionMethodFixed}</span>
              <QrCode className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-sm font-semibold">{t.webSessionOnly}</p>
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.connectedPhone}</span>
              <Smartphone className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-sm font-semibold">
              {status?.connected_phone || t.notSpecified}
            </p>
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.deviceLabel}</span>
              <Settings2 className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-sm font-semibold">
              {status?.device_label || t.notSpecified}
            </p>
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.testMessages}</span>
              <TestTube2 className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-sm font-semibold">
              {form.send_test_enabled ? t.enabled : t.disabled}
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>{t.basicSettings}</CardTitle>
              <CardDescription>{t.basicSettingsDesc}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="flex items-center justify-between rounded-2xl border p-4">
                  <div className="space-y-1">
                    <Label className="text-sm font-semibold">{t.enableCompany}</Label>
                    <p className="text-xs text-muted-foreground">{t.enableCompanyDesc}</p>
                  </div>
                  <Switch
                    checked={form.is_active}
                    onCheckedChange={(checked) => handleChange("is_active", checked)}
                  />
                </div>

                <div className="flex items-center justify-between rounded-2xl border p-4">
                  <div className="space-y-1">
                    <Label className="text-sm font-semibold">{t.allowTemplates}</Label>
                    <p className="text-xs text-muted-foreground">{t.allowTemplatesDesc}</p>
                  </div>
                  <Switch
                    checked={form.allow_templates}
                    onCheckedChange={(checked) => handleChange("allow_templates", checked)}
                  />
                </div>

                <div className="flex items-center justify-between rounded-2xl border p-4 md:col-span-2">
                  <div className="space-y-1">
                    <Label className="text-sm font-semibold">{t.enableTestMessages}</Label>
                    <p className="text-xs text-muted-foreground">{t.enableTestMessagesDesc}</p>
                  </div>
                  <Switch
                    checked={form.send_test_enabled}
                    onCheckedChange={(checked) => handleChange("send_test_enabled", checked)}
                  />
                </div>
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="provider">{t.provider}</Label>
                  <Input id="provider" value={WEB_SESSION_PROVIDER} readOnly />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="default_country_code">{t.defaultCountryCode}</Label>
                  <div className="relative">
                    <Globe className="pointer-events-none absolute end-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="default_country_code"
                      value={form.default_country_code}
                      onChange={(e) => handleChange("default_country_code", e.target.value)}
                      placeholder="966"
                      className="pe-10"
                    />
                  </div>
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="default_test_recipient">{t.defaultTestRecipient}</Label>
                  <Input
                    id="default_test_recipient"
                    value={form.default_test_recipient}
                    onChange={(e) => handleChange("default_test_recipient", e.target.value)}
                    placeholder="9665XXXXXXXX"
                  />
                </div>
              </div>

              <Separator />

              <div className="space-y-5">
                <div>
                  <h3 className="text-base font-semibold">{t.sessionTitle}</h3>
                  <p className="text-sm text-muted-foreground">{t.sessionDesc}</p>
                </div>

                <div className="grid gap-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="session_name">{t.sessionName}</Label>
                    <div className="flex gap-2">
                      <Input
                        id="session_name"
                        value={form.session_name}
                        onChange={(e) => handleChange("session_name", e.target.value)}
                        placeholder="primey-company-1-session"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        onClick={() => handleCopy(form.session_name)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>{t.sessionMode}</Label>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                      <Button
                        type="button"
                        variant={isQrMode ? "default" : "outline"}
                        className="justify-start gap-2"
                        onClick={() => handleChange("session_mode", "qr")}
                      >
                        <QrCode className="h-4 w-4" />
                        {t.qrMode}
                      </Button>

                      <Button
                        type="button"
                        variant={isPairMode ? "default" : "outline"}
                        className="justify-start gap-2"
                        onClick={() => handleChange("session_mode", "pairing_code")}
                      >
                        <Smartphone className="h-4 w-4" />
                        {t.pairMode}
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="pairing_phone">{t.pairingPhone}</Label>
                    <Input
                      id="pairing_phone"
                      value={form.pairing_phone}
                      onChange={(e) => handleChange("pairing_phone", e.target.value)}
                      placeholder="9665XXXXXXXX"
                    />
                  </div>
                </div>

                <div className="grid gap-3">
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      className="gap-2"
                      onClick={handleCreateQr}
                      disabled={creatingQr || !isQrMode}
                    >
                      {creatingQr ? <Loader2 className="h-4 w-4 animate-spin" /> : <QrCode className="h-4 w-4" />}
                      {t.createQr}
                    </Button>

                    <Button
                      type="button"
                      variant="outline"
                      className="gap-2"
                      onClick={handleCreatePairingCode}
                      disabled={creatingPairing || !isPairMode}
                    >
                      {creatingPairing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Smartphone className="h-4 w-4" />}
                      {t.createPairingCode}
                    </Button>

                    <Button
                      type="button"
                      variant="destructive"
                      className="gap-2"
                      onClick={handleDisconnectSession}
                      disabled={disconnecting}
                    >
                      {disconnecting ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogOut className="h-4 w-4" />}
                      {t.disconnectSession}
                    </Button>
                  </div>

                  <div className="rounded-2xl border bg-muted/20 p-3 text-xs text-muted-foreground">
                    {isQrMode ? t.qrButtonHint : t.pairingButtonHint}
                  </div>
                </div>

                <div className="grid gap-5 lg:grid-cols-2">
                  <div className="rounded-2xl border p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <QrCode className="h-4 w-4 text-primary" />
                      <p className="text-sm font-semibold">{t.qrMode}</p>
                    </div>

                    {qrImageSrc ? (
                      <div className="space-y-3">
                        <div className="overflow-hidden rounded-2xl border bg-white p-4">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={qrImageSrc}
                            alt="WhatsApp QR"
                            className="mx-auto h-64 w-64 object-contain"
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">{t.scanQrHint}</p>
                      </div>
                    ) : (
                      <div className="rounded-2xl border border-dashed p-6 text-center text-sm text-muted-foreground">
                        {t.generateFirst}
                      </div>
                    )}
                  </div>

                  <div className="rounded-2xl border p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <Smartphone className="h-4 w-4 text-primary" />
                      <p className="text-sm font-semibold">{t.pairingCode}</p>
                    </div>

                    {status?.pairing_code ? (
                      <div className="space-y-3">
                        <div className="rounded-2xl border bg-muted/30 p-5">
                          <div className="mb-3 flex items-center justify-between gap-3">
                            <p className="text-xs text-muted-foreground">{t.pairingReady}</p>
                            <Button
                              type="button"
                              variant="outline"
                              size="icon"
                              onClick={() => handleCopy(status.pairing_code || "")}
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                          </div>

                          <div className="flex flex-wrap items-center gap-2">
                            {status.pairing_code.split("").map((char, index) => (
                              <div
                                key={`${char}-${index}-${pairingNonce}`}
                                className="flex h-12 w-12 items-center justify-center rounded-xl border bg-background text-lg font-bold shadow-sm"
                              >
                                {char}
                              </div>
                            ))}
                          </div>
                        </div>

                        <p className="text-xs text-muted-foreground">{t.pairingHint}</p>
                      </div>
                    ) : (
                      <div className="rounded-2xl border border-dashed p-6 text-center text-sm text-muted-foreground">
                        {t.generateFirst}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>{t.alerts}</CardTitle>
              <CardDescription>{t.alertsDesc}</CardDescription>
            </CardHeader>

            <CardContent className="grid gap-4 md:grid-cols-2">
              {[
                ["send_employee_alerts", t.employeeAlerts],
                ["send_attendance_alerts", t.attendanceAlerts],
                ["send_leave_alerts", t.leaveAlerts],
                ["send_payroll_alerts", t.payrollAlerts],
                ["send_billing_alerts", t.billingAlerts],
                ["send_system_copy_alerts", t.systemCopyAlerts],
              ].map(([key, label]) => (
                <div
                  key={key}
                  className="flex items-center justify-between rounded-2xl border p-4"
                >
                  <Label className="text-sm font-semibold">{label}</Label>
                  <Switch
                    checked={form[key as keyof FormState] as boolean}
                    onCheckedChange={(checked) =>
                      handleChange(key as keyof FormState, checked as never)
                    }
                  />
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>{t.sendTestTitle}</CardTitle>
              <CardDescription>{t.sendTestDesc}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-5">
              <div className="grid gap-5 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="test_phone">{t.testPhone}</Label>
                  <Input
                    id="test_phone"
                    value={form.test_phone}
                    onChange={(e) => handleChange("test_phone", e.target.value)}
                    placeholder="9665XXXXXXXX"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="test_message">{t.testMessage}</Label>
                  <Textarea
                    id="test_message"
                    value={form.test_message}
                    onChange={(e) => handleChange("test_message", e.target.value)}
                    placeholder={t.testMessage}
                    rows={4}
                  />
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button
                  onClick={handleSendTest}
                  disabled={testing || !form.send_test_enabled}
                  className="gap-2"
                >
                  {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  {t.sendTest}
                </Button>

                {!form.send_test_enabled ? (
                  <Badge variant="secondary">{t.testDisabled}</Badge>
                ) : null}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>{t.readiness}</CardTitle>
              <CardDescription>{t.readinessDesc}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-3">
              {checklist.map((item) => (
                <div
                  key={item.label}
                  className="flex items-center justify-between rounded-2xl border p-4"
                >
                  <div className="flex items-center gap-3">
                    {item.ok ? (
                      <BadgeCheck className="h-5 w-5 text-emerald-600" />
                    ) : (
                      <Settings2 className="h-5 w-5 text-amber-600" />
                    )}
                    <span className="text-sm font-medium">{item.label}</span>
                  </div>

                  <Badge variant={item.ok ? "default" : "secondary"}>
                    {item.ok ? t.ready : t.missing}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>{t.summary}</CardTitle>
              <CardDescription>{t.summaryDesc}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="rounded-2xl border p-4">
                <div className="flex items-center gap-3">
                  <BellRing className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm text-muted-foreground">{t.provider}</p>
                    <p className="font-semibold">{WEB_SESSION_PROVIDER}</p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border p-4">
                <div className="flex items-center gap-3">
                  <Globe className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm text-muted-foreground">{t.defaultCountryCode}</p>
                    <p className="font-semibold">{form.default_country_code || "—"}</p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border p-4">
                <div className="flex items-center gap-3">
                  <ShieldCheck className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm text-muted-foreground">{t.sessionStatus}</p>
                    <p className="font-semibold">{sessionStatusLabel}</p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border p-4">
                <div className="flex items-center gap-3">
                  <Smartphone className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm text-muted-foreground">{t.connectedPhone}</p>
                    <p className="font-semibold">{status?.connected_phone || t.notSpecified}</p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border p-4">
                <div className="flex items-center gap-3">
                  <TestTube2 className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm text-muted-foreground">{t.defaultTestRecipient}</p>
                    <p className="font-semibold">
                      {form.default_test_recipient || t.notSpecified}
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border p-4">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm text-muted-foreground">{t.lastConnectedAt}</p>
                    <p className="font-semibold">{formatDateTime(status?.last_connected_at)}</p>
                  </div>
                </div>
              </div>

              {status?.gateway_message ? (
                <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                  {status.gateway_message}
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}