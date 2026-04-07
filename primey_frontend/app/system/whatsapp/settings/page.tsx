"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import {
  ArrowLeft,
  BadgeCheck,
  BellRing,
  Bot,
  CheckCircle2,
  Copy,
  Globe,
  Loader2,
  LogOut,
  MessageCircle,
  QrCode,
  RefreshCw,
  Save,
  Send,
  Settings2,
  ShieldCheck,
  Smartphone,
  Sparkles,
  TestTube2,
  Unplug,
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

type SystemWhatsAppConfig = {
  is_active?: boolean
  provider?: string
  app_name?: string
  default_country_code?: string
  allow_broadcasts?: boolean
  send_test_enabled?: boolean
  default_test_recipient?: string
  session_name?: string
  session_mode?: ConnectionMode
}

type SettingsResponse = {
  success?: boolean
  config?: SystemWhatsAppConfig
  message?: string
}

type StatusResponse = {
  success?: boolean
  connected?: boolean
  provider?: string
  last_check_at?: string | null
  session_status?: SessionStatus
  session_name?: string | null
  session_mode?: ConnectionMode | null
  qr_code?: string | null
  pairing_code?: string | null
  connected_phone?: string | null
  last_connected_at?: string | null
  device_label?: string | null
  gateway_message?: string | null
  message?: string
}

type SaveResponse = {
  success?: boolean
  message?: string
  config?: SystemWhatsAppConfig
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
}

type FormState = {
  is_active: boolean
  provider: "whatsapp_web_session"
  app_name: string
  default_country_code: string
  allow_broadcasts: boolean
  send_test_enabled: boolean
  default_test_recipient: string
  session_name: string
  session_mode: ConnectionMode
  pairing_phone: string
  test_phone: string
  test_message: string
}

const API = {
  settings: "/api/system/whatsapp/settings/",
  saveSettings: "/api/system/whatsapp/settings/",
  status: "/api/system/whatsapp/status/",
  sendTest: "/api/system/whatsapp/send-test/",
  createQr: "/api/system/whatsapp/session/create-qr/",
  createPairingCode: "/api/system/whatsapp/session/create-pairing-code/",
  disconnectSession: "/api/system/whatsapp/session/disconnect/",
} as const

const WEB_SESSION_PROVIDER = "whatsapp_web_session" as const
const DEFAULT_SESSION_NAME = "primey-system-session"
const DEFAULT_COUNTRY_CODE = "966"
const DEFAULT_TEST_MESSAGE_AR =
  "رسالة اختبار من Mham Cloud - System WhatsApp Center"
const DEFAULT_TEST_MESSAGE_EN =
  "Test message from Mham Cloud - System WhatsApp Center"

const translations = {
  ar: {
    badge: "System WhatsApp Settings",
    title: "إعدادات واتساب للنظام",
    description:
      "إدارة جلسة واتساب للنظام عبر QR أو كود الربط، مع إعدادات التفعيل ورسائل الاختبار.",
    back: "رجوع",
    refresh: "تحديث",
    save: "حفظ الإعدادات",
    loading: "جاري تحميل إعدادات واتساب...",
    loadError: "تعذر تحميل إعدادات واتساب للنظام",
    saveError: "تعذر حفظ إعدادات واتساب",
    saveSuccess: "تم حفظ إعدادات واتساب بنجاح",
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
    currentConnectionDesc: "عرض سريع لحالة الجلسة الحالية ومدى جاهزية الربط.",
    lastCheck: "آخر فحص",
    broadcasts: "البث الجماعي",
    testMessages: "رسائل الاختبار",
    enabled: "مفعل",
    disabled: "متوقف",
    allowed: "مسموح",
    blocked: "معطل",
    basicSettings: "الإعدادات الأساسية",
    basicSettingsDesc: "الإعدادات الرئيسية لتشغيل واتساب ويب على مستوى النظام.",
    enableSystem: "تفعيل واتساب للنظام",
    enableSystemDesc: "تشغيل أو إيقاف تكامل واتساب على مستوى النظام.",
    allowBroadcasts: "السماح بالبث الجماعي",
    allowBroadcastsDesc: "تمكين الإرسال الجماعي من لوحة النظام.",
    enableTestMessages: "تمكين رسائل الاختبار",
    enableTestMessagesDesc: "السماح بإرسال رسائل اختبار قبل الاستخدام الفعلي.",
    provider: "Provider",
    appName: "اسم التطبيق",
    defaultCountryCode: "رمز الدولة الافتراضي",
    defaultTestRecipient: "رقم اختبار افتراضي",
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
    summaryDesc: "عرض سريع للقيم الحالية",
    notConfigured: "غير مضبوط",
    notSpecified: "غير محدد",
    activationCheck: "تفعيل النظام",

    sessionTitle: "ربط الجلسة",
    sessionDesc:
      "يمكنك الربط عبر QR Code أو عبر رقم الجوال وكود الاقتران باستخدام WhatsApp Web Session.",
    sessionStatus: "حالة الجلسة",
    sessionName: "اسم الجلسة",
    sessionMode: "طريقة الربط",
    qrMode: "QR Code",
    pairMode: "رقم الجوال + كود الربط",
    pairingPhone: "رقم الجوال للربط",
    createQr: "إنشاء QR",
    createPairingCode: "إنشاء كود الربط",
    disconnectSession: "فصل الجلسة",
    pairingReady: "كود الربط جاهز",
    connectedPhone: "الرقم المرتبط",
    deviceLabel: "الجهاز",
    lastConnectedAt: "آخر اتصال",
    scanQrHint: "افتح واتساب في الهاتف ثم الأجهزة المرتبطة وامسح الكود.",
    pairingHint: "أدخل رقم الجوال ثم أكمل الربط باستخدام الكود الظاهر.",
    sessionDisconnected: "الجلسة غير متصلة",
    sessionQrPending: "بانتظار مسح QR",
    sessionPairPending: "بانتظار تفعيل كود الربط",
    sessionConnected: "الجلسة متصلة",
    sessionFailed: "فشل الربط",
    pairingCode: "كود الربط",
    generateFirst: "قم بإنشاء QR أو كود ربط أولًا",
    enterPairingPhone: "أدخل رقم الجوال أولًا",
    qrCreated: "تم إنشاء QR بنجاح",
    pairingCreated: "تم إنشاء كود الربط بنجاح",
    sessionDisconnectedOk: "تم فصل الجلسة بنجاح",
    sessionActionError: "تعذر تنفيذ العملية على الجلسة",
    sessionProviderHint: "هذا الوضع ثابت حاليًا على WhatsApp Web Session",
    sessionConnectedBadge: "جلسة نشطة",
    sessionPendingBadge: "جلسة قيد الربط",
    sessionDisconnectedBadge: "لا توجد جلسة",
    providerModeTitle: "وضع المزود",
    providerModeDesc: "الموديول يعمل هنا على وضع WhatsApp Web Session فقط.",
    connectionMethodFixed: "طريقة الربط المعتمدة",
    webSessionOnly: "WhatsApp Web Session Only",
    useQrFirstHint: "يوصى بالبدء عبر QR لأنه الأسهل والأكثر استقرارًا.",
    qrButtonHint: "زر إنشاء QR يعمل فقط عندما تكون طريقة الربط QR.",
    pairingButtonHint:
      "زر إنشاء كود الربط يعمل فقط عندما تكون طريقة الربط رقم الجوال + كود الربط.",
  },
  en: {
    badge: "System WhatsApp Settings",
    title: "System WhatsApp Settings",
    description:
      "Manage the system WhatsApp session using QR or pairing code, with activation and test settings.",
    back: "Back",
    refresh: "Refresh",
    save: "Save Settings",
    loading: "Loading WhatsApp settings...",
    loadError: "Unable to load system WhatsApp settings",
    saveError: "Unable to save WhatsApp settings",
    saveSuccess: "WhatsApp settings saved successfully",
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
    currentConnectionDesc: "Quick overview of the current session and readiness state.",
    lastCheck: "Last Check",
    broadcasts: "Broadcasts",
    testMessages: "Test Messages",
    enabled: "Enabled",
    disabled: "Disabled",
    allowed: "Allowed",
    blocked: "Blocked",
    basicSettings: "Basic Settings",
    basicSettingsDesc: "Main settings for the system WhatsApp Web Session integration.",
    enableSystem: "Enable System WhatsApp",
    enableSystemDesc: "Turn WhatsApp integration on or off system-wide.",
    allowBroadcasts: "Allow Broadcasts",
    allowBroadcastsDesc: "Enable bulk sending from the system panel.",
    enableTestMessages: "Enable Test Messages",
    enableTestMessagesDesc: "Allow sending test messages before real use.",
    provider: "Provider",
    appName: "App Name",
    defaultCountryCode: "Default Country Code",
    defaultTestRecipient: "Default Test Recipient",
    sendTestTitle: "Send Test Message",
    sendTestDesc: "Test the live session after a successful connection.",
    testPhone: "Phone Number",
    testMessage: "Test Message",
    sendTest: "Send Test",
    testDisabled: "Test messages are currently disabled",
    readiness: "Readiness Indicator",
    readinessDesc: "Quick validation of the required core items.",
    ready: "Ready",
    missing: "Missing",
    summary: "Settings Summary",
    summaryDesc: "Quick view of the current values",
    notConfigured: "Not configured",
    notSpecified: "Not specified",
    activationCheck: "System Activation",

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
    sessionProviderHint: "This mode is fixed to WhatsApp Web Session",
    sessionConnectedBadge: "Active Session",
    sessionPendingBadge: "Pending Session",
    sessionDisconnectedBadge: "No Session",
    providerModeTitle: "Provider Mode",
    providerModeDesc: "This module runs here in WhatsApp Web Session mode only.",
    connectionMethodFixed: "Applied Connection Method",
    webSessionOnly: "WhatsApp Web Session Only",
    useQrFirstHint: "It is recommended to start with QR because it is simpler and more stable.",
    qrButtonHint: "Generate QR only works when the connection mode is QR.",
    pairingButtonHint:
      "Generate Pairing Code only works when the connection mode is Phone Number + Pairing Code.",
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
  const candidates = new Set<string>()
  const envBase = normalizeBaseUrl(process.env.NEXT_PUBLIC_API_URL || "")

  if (envBase) {
    candidates.add(envBase)
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname, port, origin } = window.location

    if (isLocalHostname(hostname)) {
      const likelyDjangoPorts = ["8000", "8001", "8080"]

      for (const djangoPort of likelyDjangoPorts) {
        if (port !== djangoPort) {
          candidates.add(`${protocol}//${hostname}:${djangoPort}`)
        }
      }

      if (port && port !== "3000") {
        candidates.add(origin)
      }
    } else {
      candidates.add(origin)
    }
  }

  return Array.from(candidates).filter(Boolean)
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

function formatDateTime(value: string | null | undefined, locale: Locale) {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"

  return new Intl.DateTimeFormat(locale === "ar" ? "en-GB" : "en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
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
    throw new Error(
      "API base URL is not configured. Set NEXT_PUBLIC_API_URL for local or production."
    )
  }

  let lastError: Error | null = null

  for (const url of candidates) {
    try {
      const response = await fetch(url, {
        method: "GET",
        credentials: "include",
        cache: "no-store",
        headers: {
          Accept: "application/json",
        },
      })

      if (!response.ok) {
        let message = `GET ${url} failed with ${response.status}`

        try {
          const data = await readResponseSafely<{ message?: string }>(response, url)
          if (data?.message) {
            message = data.message
          }
        } catch {
          // نتجاوز استجابات HTML أو redirect الخاطئة ونجرب مرشحًا آخر
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
    throw new Error(
      "API base URL is not configured. Set NEXT_PUBLIC_API_URL for local or production."
    )
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
          (data && "message" in data && data.message) ||
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

export default function SystemWhatsAppSettingsPage() {
  const [locale, setLocale] = useState<Locale>("ar")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const [creatingQr, setCreatingQr] = useState(false)
  const [creatingPairing, setCreatingPairing] = useState(false)
  const [disconnecting, setDisconnecting] = useState(false)

  const [status, setStatus] = useState<StatusResponse | null>(null)

  const [form, setForm] = useState<FormState>({
    is_active: false,
    provider: WEB_SESSION_PROVIDER,
    app_name: "Mham Cloud",
    default_country_code: DEFAULT_COUNTRY_CODE,
    allow_broadcasts: true,
    send_test_enabled: true,
    default_test_recipient: "",
    session_name: DEFAULT_SESSION_NAME,
    session_mode: "qr",
    pairing_phone: "",
    test_phone: "",
    test_message: DEFAULT_TEST_MESSAGE_AR,
  })

  useEffect(() => {
    setLocale(detectLocale())

    const observer = new MutationObserver(() => {
      setLocale(detectLocale())
    })

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
  const isPairingMode = form.session_mode === "pairing_code"

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
  }, [
    status?.session_status,
    t.sessionConnected,
    t.sessionDisconnected,
    t.sessionFailed,
    t.sessionPairPending,
    t.sessionQrPending,
  ])

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

        setStatus(statusRes || null)

        setForm((prev) => ({
          ...prev,
          is_active: !!config.is_active,
          provider: WEB_SESSION_PROVIDER,
          app_name: config.app_name || "Mham Cloud",
          default_country_code: config.default_country_code || DEFAULT_COUNTRY_CODE,
          allow_broadcasts: config.allow_broadcasts ?? true,
          send_test_enabled: config.send_test_enabled ?? true,
          default_test_recipient: config.default_test_recipient || "",
          session_name:
            config.session_name || statusRes?.session_name || DEFAULT_SESSION_NAME,
          session_mode: config.session_mode || statusRes?.session_mode || "qr",
          pairing_phone: prev.pairing_phone || "",
          test_phone: config.default_test_recipient || prev.test_phone || "",
          test_message:
            prev.test_message ||
            (locale === "ar" ? DEFAULT_TEST_MESSAGE_AR : DEFAULT_TEST_MESSAGE_EN),
        }))
      } catch (error) {
        console.error("Failed to load WhatsApp settings page:", error)
        toast.error(error instanceof Error && error.message ? error.message : t.loadError)
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [locale, t.loadError]
  )

  useEffect(() => {
    loadPage()
  }, [loadPage])

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
    } catch (error) {
      console.error("Clipboard copy error:", error)
      toast.error(t.noCopyValue)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)

      const payload = {
        is_active: form.is_active,
        provider: WEB_SESSION_PROVIDER,
        app_name: form.app_name.trim(),
        default_country_code: form.default_country_code.trim(),
        allow_broadcasts: form.allow_broadcasts,
        send_test_enabled: form.send_test_enabled,
        default_test_recipient: form.default_test_recipient.trim(),
        session_name: form.session_name.trim(),
        session_mode: form.session_mode,
      }

      const data = await postJson<SaveResponse>(API.saveSettings, payload)

      if (!data?.success) {
        throw new Error(data?.message || t.saveError)
      }

      toast.success(data?.message || t.saveSuccess)
      await loadPage(true)
    } catch (error) {
      console.error("Save WhatsApp settings error:", error)
      toast.error(error instanceof Error && error.message ? error.message : t.saveError)
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
        message: form.test_message.trim(),
      })

      if (!data?.success) {
        throw new Error(data?.message || t.testError)
      }

      toast.success(data?.message || t.testSuccess)
      await loadPage(true)
    } catch (error) {
      console.error("Send test WhatsApp error:", error)
      toast.error(error instanceof Error && error.message ? error.message : t.testError)
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

      if (!data?.success) {
        throw new Error(data?.message || t.sessionActionError)
      }

      toast.success(data?.message || t.qrCreated)
      await loadPage(true)
    } catch (error) {
      console.error("Create QR session error:", error)
      toast.error(
        error instanceof Error && error.message ? error.message : t.sessionActionError
      )
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

      if (!data?.success) {
        throw new Error(data?.message || t.sessionActionError)
      }

      toast.success(data?.message || t.pairingCreated)
      await loadPage(true)
    } catch (error) {
      console.error("Create pairing code error:", error)
      toast.error(
        error instanceof Error && error.message ? error.message : t.sessionActionError
      )
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

      if (!data?.success) {
        throw new Error(data?.message || t.sessionActionError)
      }

      toast.success(data?.message || t.sessionDisconnectedOk)
      await loadPage(true)
    } catch (error) {
      console.error("Disconnect session error:", error)
      toast.error(
        error instanceof Error && error.message ? error.message : t.sessionActionError
      )
    } finally {
      setDisconnecting(false)
    }
  }

  const checklist = useMemo(
    () => [
      {
        label: t.activationCheck,
        ok: form.is_active,
      },
      {
        label: t.provider,
        ok: form.provider === WEB_SESSION_PROVIDER,
      },
      {
        label: t.sessionName,
        ok: !!form.session_name.trim(),
      },
      {
        label: t.sessionStatus,
        ok: status?.session_status === "connected",
      },
      {
        label: t.defaultTestRecipient,
        ok: !!form.default_test_recipient.trim(),
      },
    ],
    [
      form.is_active,
      form.provider,
      form.session_name,
      form.default_test_recipient,
      status?.session_status,
      t.activationCheck,
      t.defaultTestRecipient,
      t.provider,
      t.sessionName,
      t.sessionStatus,
    ]
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
            <Link href="/system/whatsapp">
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
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            {t.refresh}
          </Button>

          <Button onClick={handleSave} disabled={saving} className="gap-2">
            {saving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
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
                    {isConnected ? (
                      <Wifi className="h-3.5 w-3.5" />
                    ) : (
                      <WifiOff className="h-3.5 w-3.5" />
                    )}
                    {isConnected ? t.connected : t.disconnected}
                  </Badge>

                  <Badge variant={form.is_active ? "default" : "secondary"}>
                    {form.is_active ? t.active : t.inactive}
                  </Badge>

                  <Badge variant="outline">{WEB_SESSION_PROVIDER}</Badge>

                  <Badge variant="secondary">
                    {status?.session_status === "connected"
                      ? t.sessionConnectedBadge
                      : status?.session_status === "qr_pending" ||
                          status?.session_status === "pair_pending"
                        ? t.sessionPendingBadge
                        : t.sessionDisconnectedBadge}
                  </Badge>
                </div>

                <div>
                  <CardTitle className="text-xl">{t.currentConnection}</CardTitle>
                  <CardDescription className="mt-1">
                    {t.currentConnectionDesc}
                  </CardDescription>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border bg-background/80 p-4 shadow-sm backdrop-blur">
                  <p className="text-xs text-muted-foreground">{t.sessionStatus}</p>
                  <div className="mt-1 flex items-center gap-2 text-sm font-semibold">
                    {status?.session_status === "connected" ? (
                      <>
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        <span>{sessionStatusLabel}</span>
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="h-4 w-4 text-amber-600" />
                        <span>{sessionStatusLabel}</span>
                      </>
                    )}
                  </div>
                </div>

                <div className="rounded-2xl border bg-background/80 p-4 shadow-sm backdrop-blur">
                  <p className="text-xs text-muted-foreground">{t.lastCheck}</p>
                  <p className="mt-1 text-sm font-semibold">
                    {formatDateTime(status?.last_check_at, locale)}
                  </p>
                </div>
              </div>
            </div>
          </CardHeader>
        </div>

        <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.connectedPhone}</span>
              <MessageCircle className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 truncate text-sm font-semibold">
              {status?.connected_phone || t.notConfigured}
            </p>
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.sessionName}</span>
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 truncate text-sm font-semibold">
              {status?.session_name || form.session_name || t.notConfigured}
            </p>
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.broadcasts}</span>
              <BellRing className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-sm font-semibold">
              {form.allow_broadcasts ? t.enabled : t.disabled}
            </p>
          </div>

          <div className="rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{t.testMessages}</span>
              <TestTube2 className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-3 text-sm font-semibold">
              {form.send_test_enabled ? t.allowed : t.blocked}
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
                    <Label className="text-sm font-semibold">{t.enableSystem}</Label>
                    <p className="text-xs text-muted-foreground">{t.enableSystemDesc}</p>
                  </div>
                  <Switch
                    checked={form.is_active}
                    onCheckedChange={(checked) => handleChange("is_active", checked)}
                  />
                </div>

                <div className="flex items-center justify-between rounded-2xl border p-4">
                  <div className="space-y-1">
                    <Label className="text-sm font-semibold">{t.allowBroadcasts}</Label>
                    <p className="text-xs text-muted-foreground">{t.allowBroadcastsDesc}</p>
                  </div>
                  <Switch
                    checked={form.allow_broadcasts}
                    onCheckedChange={(checked) => handleChange("allow_broadcasts", checked)}
                  />
                </div>

                <div className="flex items-center justify-between rounded-2xl border p-4 md:col-span-2">
                  <div className="space-y-1">
                    <Label className="text-sm font-semibold">{t.enableTestMessages}</Label>
                    <p className="text-xs text-muted-foreground">
                      {t.enableTestMessagesDesc}
                    </p>
                  </div>
                  <Switch
                    checked={form.send_test_enabled}
                    onCheckedChange={(checked) =>
                      handleChange("send_test_enabled", checked)
                    }
                  />
                </div>
              </div>

              <Separator />

              <div className="rounded-2xl border p-4">
                <div className="mb-4 flex items-center gap-3">
                  <Settings2 className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm font-semibold">{t.providerModeTitle}</p>
                    <p className="text-xs text-muted-foreground">{t.providerModeDesc}</p>
                  </div>
                </div>

                <div className="grid gap-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="provider">{t.provider}</Label>
                    <Input
                      id="provider"
                      value={WEB_SESSION_PROVIDER}
                      readOnly
                      disabled
                      className="bg-muted/40"
                    />
                    <p className="text-xs text-muted-foreground">{t.sessionProviderHint}</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="app_name">{t.appName}</Label>
                    <Input
                      id="app_name"
                      value={form.app_name}
                      onChange={(e) => handleChange("app_name", e.target.value)}
                      placeholder="Mham Cloud"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="default_country_code">{t.defaultCountryCode}</Label>
                    <Input
                      id="default_country_code"
                      value={form.default_country_code}
                      onChange={(e) =>
                        handleChange("default_country_code", e.target.value)
                      }
                      placeholder={DEFAULT_COUNTRY_CODE}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="default_test_recipient">{t.defaultTestRecipient}</Label>
                    <Input
                      id="default_test_recipient"
                      value={form.default_test_recipient}
                      onChange={(e) =>
                        handleChange("default_test_recipient", e.target.value)
                      }
                      placeholder="9665XXXXXXXX"
                    />
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="session_name">{t.sessionName}</Label>
                    <Input
                      id="session_name"
                      value={form.session_name}
                      onChange={(e) => handleChange("session_name", e.target.value)}
                      placeholder={DEFAULT_SESSION_NAME}
                    />
                  </div>
                </div>
              </div>

              <Separator />

              <Card className="border shadow-none">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <QrCode className="h-4 w-4" />
                    {t.sessionTitle}
                  </CardTitle>
                  <CardDescription>{t.sessionDesc}</CardDescription>
                </CardHeader>

                <CardContent className="space-y-5">
                  <div className="rounded-2xl border bg-muted/20 p-4">
                    <div className="flex items-start gap-3">
                      <ShieldCheck className="mt-0.5 h-5 w-5 text-primary" />
                      <div className="space-y-1">
                        <p className="text-sm font-semibold">{t.connectionMethodFixed}</p>
                        <p className="text-xs text-muted-foreground">{t.webSessionOnly}</p>
                        <p className="text-xs text-muted-foreground">{t.useQrFirstHint}</p>
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-5 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="session_mode">{t.sessionMode}</Label>
                      <div className="grid grid-cols-2 gap-2">
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
                          variant={isPairingMode ? "default" : "outline"}
                          className="justify-start gap-2"
                          onClick={() => handleChange("session_mode", "pairing_code")}
                        >
                          <Smartphone className="h-4 w-4" />
                          {t.pairMode}
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
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
                        {creatingQr ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <QrCode className="h-4 w-4" />
                        )}
                        {t.createQr}
                      </Button>

                      <Button
                        type="button"
                        variant="outline"
                        className="gap-2"
                        onClick={handleCreatePairingCode}
                        disabled={creatingPairing || !isPairingMode}
                      >
                        {creatingPairing ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Smartphone className="h-4 w-4" />
                        )}
                        {t.createPairingCode}
                      </Button>

                      <Button
                        type="button"
                        variant="destructive"
                        className="gap-2"
                        onClick={handleDisconnectSession}
                        disabled={disconnecting}
                      >
                        {disconnecting ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <LogOut className="h-4 w-4" />
                        )}
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

                      {status?.qr_code ? (
                        <div className="space-y-3">
                          <div className="overflow-hidden rounded-2xl border bg-white p-4">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                              src={status.qr_code}
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
                                  key={`${char}-${index}`}
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

                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="rounded-2xl border p-4">
                      <p className="text-xs text-muted-foreground">{t.sessionStatus}</p>
                      <p className="mt-2 text-sm font-semibold">{sessionStatusLabel}</p>
                    </div>

                    <div className="rounded-2xl border p-4">
                      <p className="text-xs text-muted-foreground">{t.connectedPhone}</p>
                      <p className="mt-2 text-sm font-semibold">
                        {status?.connected_phone || t.notConfigured}
                      </p>
                    </div>

                    <div className="rounded-2xl border p-4">
                      <p className="text-xs text-muted-foreground">{t.lastConnectedAt}</p>
                      <p className="mt-2 text-sm font-semibold">
                        {formatDateTime(status?.last_connected_at, locale)}
                      </p>
                    </div>
                  </div>

                  {status?.device_label ? (
                    <div className="rounded-2xl border p-4">
                      <div className="flex items-center gap-3">
                        <Unplug className="h-5 w-5 text-primary" />
                        <div>
                          <p className="text-sm text-muted-foreground">{t.deviceLabel}</p>
                          <p className="font-semibold">{status.device_label}</p>
                        </div>
                      </div>
                    </div>
                  ) : null}
                </CardContent>
              </Card>
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
                  {testing ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
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
                  <Bot className="h-5 w-5 text-primary" />
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
                  <QrCode className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm text-muted-foreground">{t.sessionName}</p>
                    <p className="font-semibold">{form.session_name || t.notSpecified}</p>
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
                  <TestTube2 className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm text-muted-foreground">{t.defaultTestRecipient}</p>
                    <p className="font-semibold">
                      {form.default_test_recipient || t.notSpecified}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}