"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Activity,
  ArrowUpRight,
  BadgeCheck,
  CheckCircle2,
  Clock3,
  Cpu,
  Database,
  Fingerprint,
  Link2,
  Loader2,
  RefreshCw,
  Save,
  Search,
  Server,
  Settings2,
  ShieldCheck,
  Unplug,
  Upload,
  UserRound,
  Users,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type Locale = "ar" | "en"
type Direction = "rtl" | "ltr"

type ApiResponse<T = any> = {
  status?: string
  message?: string
  connected?: boolean
  reason?: string
  trace_id?: string
} & T

type BiotimeStatus = {
  connected: boolean
  server_url?: string
  email?: string
  biotime_company?: string
  last_connected_at?: string | null
  reason?: string
}

type DeviceItem = {
  id: number
  name?: string
  sn?: string
  ip?: string
  location?: string
  geo_location?: string | null
  status?: "online" | "offline" | string
  status_reason?: string
  threshold_minutes?: number | null
  last_activity_minutes?: number | null
  last_sync?: string | null
  last_activity?: string | null
  users?: number
}

type BiotimeEmployeeItem = {
  id: number
  biotime_code: string
  full_name: string
  department?: string
  position?: string
  is_active?: boolean
  is_linked?: boolean
}

type SystemEmployeeItem = {
  id: number
  full_name?: string
  name?: string
  username?: string
  email?: string
  phone?: string
  role?: string
  department?: string
  job_title?: string
  biotime_code?: string | null
  is_active?: boolean
  status?: string
}

type SyncLogItem = {
  id: number
  status?: string
  message?: string
  devices_synced?: number
  employees_synced?: number
  logs_synced?: number
  timestamp?: string
}

type SettingsFormState = {
  server_url: string
  company: string
  email: string
  password: string
}

const defaultSettings: SettingsFormState = {
  server_url: "",
  company: "",
  email: "",
  password: "",
}

const translations = {
  ar: {
    pageBadge: "تكامل BioTime",
    pageTitle: "مركز تحكم BioTime",
    pageDesc:
      "إدارة ربط BioTime للشركة، الأجهزة، الموظفين، وسجلات المزامنة من شاشة موحدة.",
    companyScoped: "خاص بالشركة",
    dbDriven: "حالة من قاعدة البيانات",
    liveActions: "إجراءات مباشرة",
    refresh: "تحديث",
    testConnection: "اختبار الاتصال",

    statsConnection: "حالة الاتصال",
    statsDevices: "الأجهزة المتصلة",
    statsBiotimeEmployees: "موظفو BioTime",
    statsLinked: "الموظفون المرتبطون",
    connected: "متصل",
    notConnected: "غير متصل",

    tabsOverview: "نظرة عامة",
    tabsSettings: "الإعدادات",
    tabsDevices: "الأجهزة",
    tabsEmployees: "موظفو الشركة",
    tabsBiotimeEmployees: "موظفو BioTime",
    tabsLogs: "سجلات المزامنة",

    overviewTitle: "ملخص الحساب",
    overviewDesc: "نظرة سريعة على حالة ربط حساب BioTime الحالي.",
    quickActionsTitle: "إجراءات سريعة",
    quickActionsDesc: "الوصول السريع لأهم العمليات من نفس الصفحة.",

    serverUrl: "رابط السيرفر",
    accountEmail: "بريد الحساب",
    lastConnected: "آخر اتصال",
    reason: "السبب",
    configured: "configured",

    saveSettings: "حفظ الإعدادات",
    syncDevices: "مزامنة الأجهزة",
    syncEmployees: "مزامنة الموظفين",
    openSettings: "فتح إعدادات BioTime",
    manageDevices: "إدارة الأجهزة",
    pushSyncEmployees: "إرسال / مزامنة موظفي الشركة",
    linkExistingEmployees: "ربط موظفي BioTime الحاليين",
    resetConnection: "إعادة تعيين الاتصال",

    settingsTitle: "إعدادات حساب BioTime",
    settingsDesc: "احفظ رابط السيرفر وبيانات حساب BioTime الخاص بالشركة.",
    biotimeCompanyCode: "رمز الشركة في BioTime",
    companyCodePlaceholder: "رمز الشركة / المستأجر",
    accountPassword: "كلمة مرور الحساب",
    httpsNote:
      "ملاحظة: يجب أن يكون الرابط بصيغة HTTPS لأن الباكند يتحقق من ذلك قبل الحفظ.",

    devicesTitle: "أجهزة BioTime",
    devicesDesc: "عرض الأجهزة المسحوبة من BioTime مع حالة الاتصال وآخر نشاط.",
    device: "الجهاز",
    ip: "IP",
    location: "الموقع",
    status: "الحالة",
    users: "المستخدمون",
    lastActivity: "آخر نشاط",
    lastSync: "آخر مزامنة",
    actions: "الإجراءات",
    online: "متصل",
    offline: "غير متصل",
    noDevices: "لا توجد أجهزة حاليًا.",
    test: "اختبار",
    sync: "مزامنة",

    companyEmployeesTitle: "موظفو الشركة",
    companyEmployeesDesc:
      "إرسال موظفي الشركة إلى BioTime أو مزامنتهم إذا كانوا مرتبطين مسبقًا.",
    employee: "الموظف",
    department: "القسم",
    jobTitle: "المسمى الوظيفي",
    role: "الدور",
    biotimeCode: "رمز BioTime",
    searchEmployees: "البحث في موظفي الشركة...",
    noMatchingEmployees: "لا يوجد موظفون مطابقون.",
    linked: "مرتبط",
    notLinked: "غير مرتبط",
    push: "إرسال",

    linkTitle: "ربط موظف BioTime موجود",
    linkDesc: "اربط موظفًا موجودًا في BioTime مع موظف في النظام بدون إنشاء موظف جديد.",
    systemEmployee: "موظف النظام",
    selectSystemEmployee: "اختر موظف النظام",
    biotimeEmployee: "موظف BioTime",
    selectBiotimeEmployee: "اختر موظف BioTime",
    linkEmployee: "ربط الموظف",
    biotimeEmployeesTitle: "موظفو BioTime",
    biotimeEmployeesDesc: "قائمة الموظفين القادمين من BioTime مع حالة الربط الحالية.",
    fullName: "الاسم الكامل",
    position: "المنصب",
    active: "نشط",
    inactive: "غير نشط",
    unlinked: "غير مرتبط",
    searchBiotimeEmployees: "البحث في موظفي BioTime...",
    noBiotimeEmployees: "لا يوجد موظفون في BioTime حاليًا.",

    logsTitle: "سجلات مزامنة BioTime",
    logsDesc: "آخر سجلات المزامنة المسجلة في النظام.",
    message: "الرسالة",
    devices: "الأجهزة",
    employees: "الموظفون",
    logs: "السجلات",
    timestamp: "الوقت",
    success: "نجاح",
    unknown: "غير معروف",
    noLogs: "لا توجد سجلات مزامنة حاليًا.",

    filterCardTitle: "البحث والفلاتر",
    filterCardDesc: "تصفية النتائج مباشرة من نفس الشاشة.",
    summaryCardTitle: "ملخص سريع",
    summaryCardDesc: "مؤشرات أساسية مرتبطة بالتكامل الحالي.",
    records: "سجل",
    empty: "—",
    minutes: "min",

    loadingPage: "جاري تحميل صفحة BioTime...",
    saveSuccess: "تم حفظ إعدادات BioTime بنجاح.",
    saveError: "فشل حفظ الإعدادات.",
    testSuccess: "تم اختبار الاتصال بنجاح.",
    testError: "فشل اختبار الاتصال.",
    resetSuccess: "تمت إعادة تعيين الاتصال.",
    resetError: "فشل إعادة تعيين الاتصال.",
    syncDevicesSuccess: "تمت مزامنة الأجهزة بنجاح.",
    syncDevicesError: "فشل مزامنة الأجهزة.",
    syncEmployeesSuccess: "تمت مزامنة موظفي BioTime بنجاح.",
    syncEmployeesError: "فشل مزامنة الموظفين.",
    deviceReachable: "الجهاز متاح للوصول.",
    deviceTestError: "فشل اختبار الجهاز.",
    singleDeviceSyncSuccess: "تمت مزامنة الجهاز بنجاح.",
    singleDeviceSyncError: "فشل مزامنة الجهاز.",
    pushEmployeeSuccess: "تم إرسال الموظف إلى BioTime.",
    pushEmployeeError: "فشل إرسال الموظف.",
    syncEmployeeSuccess: "تمت مزامنة الموظف مع BioTime.",
    syncEmployeeError: "فشل مزامنة الموظف.",
    selectEmployeesFirst: "اختر موظف النظام وموظف BioTime أولًا.",
    linkEmployeeSuccess: "تم ربط الموظف بنجاح.",
    linkEmployeeError: "فشل ربط الموظف.",
    loadError: "فشل تحميل صفحة BioTime.",
  },
  en: {
    pageBadge: "BioTime Integration",
    pageTitle: "BioTime Control Center",
    pageDesc:
      "Manage the company BioTime connection, devices, employees, and sync logs from one unified screen.",
    companyScoped: "Company Scoped",
    dbDriven: "DB Driven Status",
    liveActions: "Live Actions",
    refresh: "Refresh",
    testConnection: "Test Connection",

    statsConnection: "Connection Status",
    statsDevices: "Devices Online",
    statsBiotimeEmployees: "BioTime Employees",
    statsLinked: "Linked Employees",
    connected: "Connected",
    notConnected: "Not Connected",

    tabsOverview: "Overview",
    tabsSettings: "Settings",
    tabsDevices: "Devices",
    tabsEmployees: "Company Employees",
    tabsBiotimeEmployees: "BioTime Employees",
    tabsLogs: "Sync Logs",

    overviewTitle: "Account Overview",
    overviewDesc: "A quick overview of the current BioTime account connection.",
    quickActionsTitle: "Quick Actions",
    quickActionsDesc: "Fast access to the most important actions from the same page.",

    serverUrl: "Server URL",
    accountEmail: "Account Email",
    lastConnected: "Last Connected",
    reason: "Reason",
    configured: "configured",

    saveSettings: "Save Settings",
    syncDevices: "Sync Devices",
    syncEmployees: "Sync Employees",
    openSettings: "Open BioTime Settings",
    manageDevices: "Manage Devices",
    pushSyncEmployees: "Push / Sync Company Employees",
    linkExistingEmployees: "Link Existing BioTime Employees",
    resetConnection: "Reset Connection",

    settingsTitle: "BioTime Account Settings",
    settingsDesc: "Save the server URL and the company BioTime account credentials.",
    biotimeCompanyCode: "BioTime Company Code",
    companyCodePlaceholder: "Company code / tenant code",
    accountPassword: "Account Password",
    httpsNote:
      "Note: the server URL must use HTTPS because the backend validates that before saving.",

    devicesTitle: "BioTime Devices",
    devicesDesc: "View imported BioTime devices with connection status and last activity.",
    device: "Device",
    ip: "IP",
    location: "Location",
    status: "Status",
    users: "Users",
    lastActivity: "Last Activity",
    lastSync: "Last Sync",
    actions: "Actions",
    online: "Online",
    offline: "Offline",
    noDevices: "No devices available right now.",
    test: "Test",
    sync: "Sync",

    companyEmployeesTitle: "Company Employees",
    companyEmployeesDesc:
      "Push company employees to BioTime or sync them when already linked.",
    employee: "Employee",
    department: "Department",
    jobTitle: "Job Title",
    role: "Role",
    biotimeCode: "BioTime Code",
    searchEmployees: "Search company employees...",
    noMatchingEmployees: "No matching employees found.",
    linked: "Linked",
    notLinked: "Not Linked",
    push: "Push",

    linkTitle: "Link Existing BioTime Employee",
    linkDesc:
      "Link an existing BioTime employee with a system employee without creating a new record.",
    systemEmployee: "System Employee",
    selectSystemEmployee: "Select system employee",
    biotimeEmployee: "BioTime Employee",
    selectBiotimeEmployee: "Select BioTime employee",
    linkEmployee: "Link Employee",
    biotimeEmployeesTitle: "BioTime Employees",
    biotimeEmployeesDesc: "List of BioTime employees with the current link status.",
    fullName: "Full Name",
    position: "Position",
    active: "Active",
    inactive: "Inactive",
    unlinked: "Unlinked",
    searchBiotimeEmployees: "Search BioTime employees...",
    noBiotimeEmployees: "No BioTime employees found right now.",

    logsTitle: "BioTime Sync Logs",
    logsDesc: "Latest sync logs recorded by the system.",
    message: "Message",
    devices: "Devices",
    employees: "Employees",
    logs: "Logs",
    timestamp: "Timestamp",
    success: "Success",
    unknown: "Unknown",
    noLogs: "No sync logs available right now.",

    filterCardTitle: "Search & Filters",
    filterCardDesc: "Filter records directly from the same screen.",
    summaryCardTitle: "Quick Summary",
    summaryCardDesc: "Core indicators related to the current integration.",
    records: "records",
    empty: "—",
    minutes: "min",

    loadingPage: "Loading BioTime page...",
    saveSuccess: "BioTime settings saved successfully.",
    saveError: "Failed to save settings.",
    testSuccess: "Connection tested successfully.",
    testError: "Connection test failed.",
    resetSuccess: "Connection reset successfully.",
    resetError: "Failed to reset connection.",
    syncDevicesSuccess: "Devices synced successfully.",
    syncDevicesError: "Failed to sync devices.",
    syncEmployeesSuccess: "BioTime employees synced successfully.",
    syncEmployeesError: "Failed to sync employees.",
    deviceReachable: "Device is reachable.",
    deviceTestError: "Device test failed.",
    singleDeviceSyncSuccess: "Device synced successfully.",
    singleDeviceSyncError: "Single device sync failed.",
    pushEmployeeSuccess: "Employee pushed to BioTime successfully.",
    pushEmployeeError: "Failed to push employee.",
    syncEmployeeSuccess: "Employee synced with BioTime successfully.",
    syncEmployeeError: "Failed to sync employee.",
    selectEmployeesFirst: "Select the system employee and the BioTime employee first.",
    linkEmployeeSuccess: "Employee linked successfully.",
    linkEmployeeError: "Failed to link employee.",
    loadError: "Failed to load the BioTime page.",
  },
} as const

function detectLocale(): Locale {
  if (typeof document === "undefined") return "en"
  const lang = (document.documentElement.lang || "en").toLowerCase()
  return lang.startsWith("ar") ? "ar" : "en"
}

function detectDirection(): Direction {
  if (typeof document === "undefined") return "ltr"
  const dir = (document.documentElement.dir || "ltr").toLowerCase()
  return dir === "rtl" ? "rtl" : "ltr"
}

function formatDate(value?: string | null) {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"

  return new Intl.DateTimeFormat("en-GB-u-nu-latn", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date)
}

function formatNumber(value?: number | null) {
  if (value === null || value === undefined) return "0"
  return new Intl.NumberFormat("en-US", {
    numberingSystem: "latn",
    maximumFractionDigits: 0,
  }).format(value)
}

function formatMinutes(value?: number | null, suffix = "min") {
  if (value === null || value === undefined) return "—"
  return `${formatNumber(value)} ${suffix}`
}

function getCsrfToken() {
  if (typeof document === "undefined") return ""
  const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ""
}

async function apiFetch<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const method = (options.method || "GET").toUpperCase()
  const isFormLikeMethod = method !== "GET" && method !== "HEAD"

  const headers = new Headers(options.headers || {})
  if (isFormLikeMethod && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  const csrfToken = getCsrfToken()
  if (isFormLikeMethod && csrfToken) {
    headers.set("X-CSRFToken", csrfToken)
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: "include",
    cache: "no-store",
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok || data?.status === "error") {
    throw new Error(data?.message || data?.error || "Unexpected request error.")
  }

  return data
}

export default function CompanyBiotimePage() {
  const [locale, setLocale] = useState<Locale>("en")
  const [direction, setDirection] = useState<Direction>("ltr")
  const t = translations[locale]

  const [activeTab, setActiveTab] = useState("overview")

  const [pageLoading, setPageLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const [status, setStatus] = useState<BiotimeStatus | null>(null)
  const [devices, setDevices] = useState<DeviceItem[]>([])
  const [biotimeEmployees, setBiotimeEmployees] = useState<BiotimeEmployeeItem[]>([])
  const [systemEmployees, setSystemEmployees] = useState<SystemEmployeeItem[]>([])
  const [syncLogs, setSyncLogs] = useState<SyncLogItem[]>([])

  const [settings, setSettings] = useState<SettingsFormState>(defaultSettings)
  const [settingsBusy, setSettingsBusy] = useState(false)
  const [testBusy, setTestBusy] = useState(false)
  const [resetBusy, setResetBusy] = useState(false)
  const [syncEmployeesBusy, setSyncEmployeesBusy] = useState(false)
  const [syncDevicesBusy, setSyncDevicesBusy] = useState(false)

  const [deviceActionId, setDeviceActionId] = useState<number | null>(null)
  const [employeeActionId, setEmployeeActionId] = useState<number | null>(null)

  const [employeeSearch, setEmployeeSearch] = useState("")
  const [biotimeSearch, setBiotimeSearch] = useState("")

  const [selectedSystemEmployeeId, setSelectedSystemEmployeeId] = useState("")
  const [selectedBiotimeCode, setSelectedBiotimeCode] = useState("")
  const [linkBusy, setLinkBusy] = useState(false)

  useEffect(() => {
    const applyLocaleState = () => {
      setLocale(detectLocale())
      setDirection(detectDirection())
    }

    applyLocaleState()

    if (typeof document === "undefined") return

    const observer = new MutationObserver(() => {
      applyLocaleState()
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    window.addEventListener("languagechange", applyLocaleState)

    return () => {
      observer.disconnect()
      window.removeEventListener("languagechange", applyLocaleState)
    }
  }, [])

  const hydrateStatusIntoForm = useCallback((payload: BiotimeStatus | null) => {
    if (!payload) return
    setSettings((prev) => ({
      ...prev,
      server_url: payload.server_url || prev.server_url,
      company: payload.biotime_company || prev.company,
      email: payload.email || prev.email,
    }))
  }, [])

  const loadStatus = useCallback(async () => {
    const res = await apiFetch<BiotimeStatus>("/api/company/biotime/status/")
    const nextStatus: BiotimeStatus = {
      connected: !!res.connected,
      server_url: res.server_url,
      email: res.email,
      biotime_company: res.biotime_company,
      last_connected_at: res.last_connected_at,
      reason: res.reason,
    }
    setStatus(nextStatus)
    hydrateStatusIntoForm(nextStatus)
  }, [hydrateStatusIntoForm])

  const loadDevices = useCallback(async () => {
    const res = await apiFetch<{ devices?: DeviceItem[] }>("/api/company/biotime/devices/")
    setDevices(Array.isArray(res.devices) ? res.devices : [])
  }, [])

  const loadBiotimeEmployees = useCallback(async () => {
    const res = await apiFetch<{ employees?: BiotimeEmployeeItem[] }>(
      "/api/company/biotime/employees/"
    )
    setBiotimeEmployees(Array.isArray(res.employees) ? res.employees : [])
  }, [])

  const loadSystemEmployees = useCallback(async () => {
    const res = await apiFetch<{ employees?: SystemEmployeeItem[] }>("/api/company/employees/")
    setSystemEmployees(Array.isArray(res.employees) ? res.employees : [])
  }, [])

  const loadSyncLogs = useCallback(async () => {
    const res = await apiFetch<{ logs?: SyncLogItem[] }>("/api/company/biotime/sync-logs/")
    setSyncLogs(Array.isArray(res.logs) ? res.logs : [])
  }, [])

  const loadAll = useCallback(
    async (mode: "initial" | "refresh" = "initial") => {
      try {
        if (mode === "initial") {
          setPageLoading(true)
        } else {
          setRefreshing(true)
        }

        await Promise.all([
          loadStatus(),
          loadDevices(),
          loadBiotimeEmployees(),
          loadSystemEmployees(),
          loadSyncLogs(),
        ])
      } catch (error) {
        console.error("Biotime load error:", error)
        toast.error(error instanceof Error ? error.message : t.loadError)
      } finally {
        setPageLoading(false)
        setRefreshing(false)
      }
    },
    [loadStatus, loadDevices, loadBiotimeEmployees, loadSystemEmployees, loadSyncLogs, t.loadError]
  )

  useEffect(() => {
    loadAll("initial")
  }, [loadAll])

  const connectedBadge = useMemo(() => {
    if (!status?.connected) {
      return (
        <Badge variant="secondary" className="gap-1 rounded-full">
          <WifiOff className="h-3.5 w-3.5" />
          {t.notConnected}
        </Badge>
      )
    }

    return (
      <Badge className="gap-1 rounded-full">
        <Wifi className="h-3.5 w-3.5" />
        {t.connected}
      </Badge>
    )
  }, [status, t.connected, t.notConnected])

  const filteredSystemEmployees = useMemo(() => {
    const keyword = employeeSearch.trim().toLowerCase()
    if (!keyword) return systemEmployees

    return systemEmployees.filter((item) => {
      const haystack = [
        item.full_name,
        item.name,
        item.username,
        item.email,
        item.department,
        item.job_title,
        item.role,
        item.biotime_code,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()

      return haystack.includes(keyword)
    })
  }, [employeeSearch, systemEmployees])

  const filteredBiotimeEmployees = useMemo(() => {
    const keyword = biotimeSearch.trim().toLowerCase()
    if (!keyword) return biotimeEmployees

    return biotimeEmployees.filter((item) => {
      const haystack = [item.full_name, item.biotime_code, item.department, item.position]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()

      return haystack.includes(keyword)
    })
  }, [biotimeEmployees, biotimeSearch])

  const linkedCount = useMemo(
    () => biotimeEmployees.filter((item) => item.is_linked).length,
    [biotimeEmployees]
  )

  const onlineDevicesCount = useMemo(
    () => devices.filter((item) => item.status === "online").length,
    [devices]
  )

  const saveSettings = async () => {
    try {
      setSettingsBusy(true)

      await apiFetch("/api/company/biotime/save-settings/", {
        method: "POST",
        body: JSON.stringify(settings),
      })

      toast.success(t.saveSuccess)
      await loadStatus()
    } catch (error) {
      console.error("Save settings error:", error)
      toast.error(error instanceof Error ? error.message : t.saveError)
    } finally {
      setSettingsBusy(false)
    }
  }

  const testConnection = async () => {
    try {
      setTestBusy(true)
      const res = await apiFetch("/api/company/biotime/test-connection/", {
        method: "POST",
      })

      toast.success(res.message || t.testSuccess)
      await loadStatus()
    } catch (error) {
      console.error("Test connection error:", error)
      toast.error(error instanceof Error ? error.message : t.testError)
    } finally {
      setTestBusy(false)
    }
  }

  const resetConnection = async () => {
    try {
      setResetBusy(true)
      const res = await apiFetch("/api/company/biotime/reset-connection/", {
        method: "POST",
      })

      toast.success(res.message || t.resetSuccess)
      await loadStatus()
    } catch (error) {
      console.error("Reset connection error:", error)
      toast.error(error instanceof Error ? error.message : t.resetError)
    } finally {
      setResetBusy(false)
    }
  }

  const syncDevices = async () => {
    try {
      setSyncDevicesBusy(true)
      const res = await apiFetch("/api/company/biotime/devices/sync/", {
        method: "POST",
      })

      toast.success(res.message || t.syncDevicesSuccess)
      await Promise.all([loadDevices(), loadSyncLogs()])
    } catch (error) {
      console.error("Sync devices error:", error)
      toast.error(error instanceof Error ? error.message : t.syncDevicesError)
    } finally {
      setSyncDevicesBusy(false)
    }
  }

  const syncEmployees = async () => {
    try {
      setSyncEmployeesBusy(true)
      const res = await apiFetch("/api/company/biotime/sync-employees/", {
        method: "POST",
      })

      toast.success(res.message || t.syncEmployeesSuccess)
      await Promise.all([loadBiotimeEmployees(), loadSyncLogs()])
    } catch (error) {
      console.error("Sync employees error:", error)
      toast.error(error instanceof Error ? error.message : t.syncEmployeesError)
    } finally {
      setSyncEmployeesBusy(false)
    }
  }

  const testSingleDevice = async (deviceId: number) => {
    try {
      setDeviceActionId(deviceId)
      const res = await apiFetch(`/api/company/biotime/devices/${deviceId}/test/`, {
        method: "POST",
      })

      toast.success(res.message || t.deviceReachable)
    } catch (error) {
      console.error("Test device error:", error)
      toast.error(error instanceof Error ? error.message : t.deviceTestError)
    } finally {
      setDeviceActionId(null)
    }
  }

  const syncSingleDevice = async (deviceId: number) => {
    try {
      setDeviceActionId(deviceId)
      const res = await apiFetch(`/api/company/biotime/devices/${deviceId}/sync/`, {
        method: "POST",
      })

      toast.success(res.message || t.singleDeviceSyncSuccess)
      await loadDevices()
    } catch (error) {
      console.error("Sync single device error:", error)
      toast.error(error instanceof Error ? error.message : t.singleDeviceSyncError)
    } finally {
      setDeviceActionId(null)
    }
  }

  const pushEmployee = async (employeeId: number) => {
    try {
      setEmployeeActionId(employeeId)
      const res = await apiFetch(`/api/company/biotime/push-employee/${employeeId}/`, {
        method: "POST",
      })

      toast.success(res.message || t.pushEmployeeSuccess)
      await Promise.all([loadSystemEmployees(), loadBiotimeEmployees(), loadSyncLogs()])
    } catch (error) {
      console.error("Push employee error:", error)
      toast.error(error instanceof Error ? error.message : t.pushEmployeeError)
    } finally {
      setEmployeeActionId(null)
    }
  }

  const syncEmployee = async (employeeId: number) => {
    try {
      setEmployeeActionId(employeeId)
      const res = await apiFetch(`/api/company/biotime/sync-employee/${employeeId}/`, {
        method: "POST",
      })

      toast.success(res.message || t.syncEmployeeSuccess)
      await Promise.all([loadSystemEmployees(), loadBiotimeEmployees(), loadSyncLogs()])
    } catch (error) {
      console.error("Sync employee error:", error)
      toast.error(error instanceof Error ? error.message : t.syncEmployeeError)
    } finally {
      setEmployeeActionId(null)
    }
  }

  const linkEmployee = async () => {
    try {
      if (!selectedSystemEmployeeId || !selectedBiotimeCode) {
        toast.error(t.selectEmployeesFirst)
        return
      }

      setLinkBusy(true)

      const res = await apiFetch("/api/company/biotime/link-employee/", {
        method: "POST",
        body: JSON.stringify({
          employee_id: Number(selectedSystemEmployeeId),
          biotime_code: selectedBiotimeCode,
        }),
      })

      toast.success(res.message || t.linkEmployeeSuccess)
      setSelectedSystemEmployeeId("")
      setSelectedBiotimeCode("")
      await Promise.all([loadSystemEmployees(), loadBiotimeEmployees()])
    } catch (error) {
      console.error("Link employee error:", error)
      toast.error(error instanceof Error ? error.message : t.linkEmployeeError)
    } finally {
      setLinkBusy(false)
    }
  }

  const linkedSystemEmployeesCount = useMemo(
    () => systemEmployees.filter((item) => !!item.biotime_code).length,
    [systemEmployees]
  )

  if (pageLoading) {
    return (
      <div dir={direction} className="space-y-6 p-4 sm:p-6">
        <Card className="rounded-3xl border-border/60">
          <CardContent className="flex min-h-[360px] items-center justify-center">
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              {t.loadingPage}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div dir={direction} className="space-y-6 p-4 sm:p-6">
      <div className="rounded-3xl border border-border/60 bg-background p-4 shadow-sm sm:p-6">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="rounded-full px-3 py-1">
                {t.pageBadge}
              </Badge>
              {connectedBadge}
            </div>

            <div className="space-y-2">
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                {t.pageTitle}
              </h1>
              <p className="max-w-3xl text-sm text-muted-foreground">{t.pageDesc}</p>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4" />
                {t.companyScoped}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Database className="h-4 w-4" />
                {t.dbDriven}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Activity className="h-4 w-4" />
                {t.liveActions}
              </span>
            </div>
          </div>

          <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:flex-wrap">
            <Button
              variant="outline"
              onClick={() => loadAll("refresh")}
              disabled={refreshing}
              className="rounded-2xl"
            >
              {refreshing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              <span>{t.refresh}</span>
            </Button>

            <Button
              onClick={testConnection}
              disabled={testBusy}
              className="rounded-2xl"
            >
              {testBusy ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <BadgeCheck className="h-4 w-4" />
              )}
              <span>{t.testConnection}</span>
            </Button>
          </div>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Card className="rounded-3xl border-border/60">
            <CardContent className="flex items-center justify-between p-5">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">{t.statsConnection}</p>
                <p className="text-xl font-semibold">
                  {status?.connected ? t.connected : t.notConnected}
                </p>
              </div>
              <div className="rounded-2xl border border-border/60 p-3">
                {status?.connected ? (
                  <Wifi className="h-5 w-5" />
                ) : (
                  <WifiOff className="h-5 w-5" />
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-3xl border-border/60">
            <CardContent className="flex items-center justify-between p-5">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">{t.statsDevices}</p>
                <p className="text-xl font-semibold">
                  {formatNumber(onlineDevicesCount)} / {formatNumber(devices.length)}
                </p>
              </div>
              <div className="rounded-2xl border border-border/60 p-3">
                <Cpu className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-3xl border-border/60">
            <CardContent className="flex items-center justify-between p-5">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">{t.statsBiotimeEmployees}</p>
                <p className="text-xl font-semibold">{formatNumber(biotimeEmployees.length)}</p>
              </div>
              <div className="rounded-2xl border border-border/60 p-3">
                <Fingerprint className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-3xl border-border/60">
            <CardContent className="flex items-center justify-between p-5">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">{t.statsLinked}</p>
                <p className="text-xl font-semibold">{formatNumber(linkedCount)}</p>
              </div>
              <div className="rounded-2xl border border-border/60 p-3">
                <Link2 className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="h-auto w-full flex-wrap justify-start rounded-2xl p-1">
          <TabsTrigger value="overview" className="rounded-xl">
            {t.tabsOverview}
          </TabsTrigger>
          <TabsTrigger value="settings" className="rounded-xl">
            {t.tabsSettings}
          </TabsTrigger>
          <TabsTrigger value="devices" className="rounded-xl">
            {t.tabsDevices}
          </TabsTrigger>
          <TabsTrigger value="employees" className="rounded-xl">
            {t.tabsEmployees}
          </TabsTrigger>
          <TabsTrigger value="biotime-employees" className="rounded-xl">
            {t.tabsBiotimeEmployees}
          </TabsTrigger>
          <TabsTrigger value="logs" className="rounded-xl">
            {t.tabsLogs}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <Card className="rounded-3xl border-border/60">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="h-5 w-5" />
                  {t.overviewTitle}
                </CardTitle>
                <CardDescription>{t.overviewDesc}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-5">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.serverUrl}</p>
                    <p className="mt-1 break-all text-sm font-medium">
                      {status?.server_url || t.empty}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.accountEmail}</p>
                    <p className="mt-1 break-all text-sm font-medium">
                      {status?.email || t.empty}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.lastConnected}</p>
                    <p className="mt-1 text-sm font-medium">
                      {formatDate(status?.last_connected_at)}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.reason}</p>
                    <p className="mt-1 text-sm font-medium">
                      {status?.reason || (status?.connected ? t.configured : t.empty)}
                    </p>
                  </div>
                </div>

                <Separator />

                <div className="flex flex-wrap gap-2">
                  <Button onClick={saveSettings} disabled={settingsBusy} className="rounded-2xl">
                    {settingsBusy ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    <span>{t.saveSettings}</span>
                  </Button>

                  <Button
                    variant="outline"
                    onClick={testConnection}
                    disabled={testBusy}
                    className="rounded-2xl"
                  >
                    {testBusy ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <BadgeCheck className="h-4 w-4" />
                    )}
                    <span>{t.testConnection}</span>
                  </Button>

                  <Button
                    variant="outline"
                    onClick={syncDevices}
                    disabled={syncDevicesBusy}
                    className="rounded-2xl"
                  >
                    {syncDevicesBusy ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Cpu className="h-4 w-4" />
                    )}
                    <span>{t.syncDevices}</span>
                  </Button>

                  <Button
                    variant="outline"
                    onClick={syncEmployees}
                    disabled={syncEmployeesBusy}
                    className="rounded-2xl"
                  >
                    {syncEmployeesBusy ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Users className="h-4 w-4" />
                    )}
                    <span>{t.syncEmployees}</span>
                  </Button>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-6">
              <Card className="rounded-3xl border-border/60">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings2 className="h-5 w-5" />
                    {t.quickActionsTitle}
                  </CardTitle>
                  <CardDescription>{t.quickActionsDesc}</CardDescription>
                </CardHeader>

                <CardContent className="grid gap-3">
                  <Button
                    variant="outline"
                    className="justify-between rounded-2xl"
                    onClick={() => setActiveTab("settings")}
                  >
                    <span className="inline-flex items-center gap-2">
                      <Server className="h-4 w-4" />
                      {t.openSettings}
                    </span>
                    <ArrowUpRight className="h-4 w-4" />
                  </Button>

                  <Button
                    variant="outline"
                    className="justify-between rounded-2xl"
                    onClick={() => setActiveTab("devices")}
                  >
                    <span className="inline-flex items-center gap-2">
                      <Cpu className="h-4 w-4" />
                      {t.manageDevices}
                    </span>
                    <ArrowUpRight className="h-4 w-4" />
                  </Button>

                  <Button
                    variant="outline"
                    className="justify-between rounded-2xl"
                    onClick={() => setActiveTab("employees")}
                  >
                    <span className="inline-flex items-center gap-2">
                      <UserRound className="h-4 w-4" />
                      {t.pushSyncEmployees}
                    </span>
                    <ArrowUpRight className="h-4 w-4" />
                  </Button>

                  <Button
                    variant="outline"
                    className="justify-between rounded-2xl"
                    onClick={() => setActiveTab("biotime-employees")}
                  >
                    <span className="inline-flex items-center gap-2">
                      <Fingerprint className="h-4 w-4" />
                      {t.linkExistingEmployees}
                    </span>
                    <ArrowUpRight className="h-4 w-4" />
                  </Button>

                  <Button
                    variant="outline"
                    className="justify-between rounded-2xl"
                    onClick={resetConnection}
                    disabled={resetBusy}
                  >
                    <span className="inline-flex items-center gap-2">
                      {resetBusy ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Unplug className="h-4 w-4" />
                      )}
                      {t.resetConnection}
                    </span>
                    <ArrowUpRight className="h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>

              <Card className="rounded-3xl border-border/60">
                <CardHeader>
                  <CardTitle>{t.summaryCardTitle}</CardTitle>
                  <CardDescription>{t.summaryCardDesc}</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.devices}</p>
                    <p className="mt-1 text-lg font-semibold">{formatNumber(devices.length)}</p>
                  </div>
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.employees}</p>
                    <p className="mt-1 text-lg font-semibold">
                      {formatNumber(systemEmployees.length)}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.linked}</p>
                    <p className="mt-1 text-lg font-semibold">
                      {formatNumber(linkedSystemEmployeesCount)}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.logs}</p>
                    <p className="mt-1 text-lg font-semibold">{formatNumber(syncLogs.length)}</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card className="rounded-3xl border-border/60">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                {t.settingsTitle}
              </CardTitle>
              <CardDescription>{t.settingsDesc}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-5">
              <div className="grid gap-5 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="server_url">{t.serverUrl}</Label>
                  <Input
                    id="server_url"
                    placeholder="https://your-biotime-server.com"
                    value={settings.server_url}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, server_url: e.target.value }))
                    }
                    className="rounded-2xl"
                    dir="ltr"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="company">{t.biotimeCompanyCode}</Label>
                  <Input
                    id="company"
                    placeholder={t.companyCodePlaceholder}
                    value={settings.company}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, company: e.target.value }))
                    }
                    className="rounded-2xl"
                    dir="ltr"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">{t.accountEmail}</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="account@company.com"
                    value={settings.email}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, email: e.target.value }))
                    }
                    className="rounded-2xl"
                    dir="ltr"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">{t.accountPassword}</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={settings.password}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, password: e.target.value }))
                    }
                    className="rounded-2xl"
                    dir="ltr"
                  />
                </div>
              </div>

              <div className="rounded-2xl border border-dashed border-border/70 p-4 text-sm text-muted-foreground">
                {t.httpsNote}
              </div>

              <div className="flex flex-wrap gap-2">
                <Button onClick={saveSettings} disabled={settingsBusy} className="rounded-2xl">
                  {settingsBusy ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  <span>{t.saveSettings}</span>
                </Button>

                <Button
                  variant="outline"
                  onClick={testConnection}
                  disabled={testBusy}
                  className="rounded-2xl"
                >
                  {testBusy ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <BadgeCheck className="h-4 w-4" />
                  )}
                  <span>{t.testConnection}</span>
                </Button>

                <Button
                  variant="outline"
                  onClick={resetConnection}
                  disabled={resetBusy}
                  className="rounded-2xl"
                >
                  {resetBusy ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Unplug className="h-4 w-4" />
                  )}
                  <span>{t.resetConnection}</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="devices" className="space-y-6">
          <Card className="rounded-3xl border-border/60">
            <CardHeader className="gap-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Cpu className="h-5 w-5" />
                    {t.devicesTitle}
                  </CardTitle>
                  <CardDescription>{t.devicesDesc}</CardDescription>
                </div>

                <Button
                  onClick={syncDevices}
                  disabled={syncDevicesBusy}
                  className="rounded-2xl"
                >
                  {syncDevicesBusy ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  <span>{t.syncDevices}</span>
                </Button>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <Card className="rounded-2xl border-border/60 shadow-none">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">{t.summaryCardTitle}</CardTitle>
                  <CardDescription>{t.summaryCardDesc}</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.devices}</p>
                    <p className="mt-1 text-lg font-semibold">{formatNumber(devices.length)}</p>
                  </div>
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.online}</p>
                    <p className="mt-1 text-lg font-semibold">
                      {formatNumber(onlineDevicesCount)}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.offline}</p>
                    <p className="mt-1 text-lg font-semibold">
                      {formatNumber(devices.length - onlineDevicesCount)}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <div className="overflow-x-auto rounded-2xl border border-border/60">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t.device}</TableHead>
                      <TableHead>{t.ip}</TableHead>
                      <TableHead>{t.location}</TableHead>
                      <TableHead>{t.status}</TableHead>
                      <TableHead>{t.users}</TableHead>
                      <TableHead>{t.lastActivity}</TableHead>
                      <TableHead>{t.lastSync}</TableHead>
                      <TableHead className={direction === "rtl" ? "text-left" : "text-right"}>
                        {t.actions}
                      </TableHead>
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {devices.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                          {t.noDevices}
                        </TableCell>
                      </TableRow>
                    ) : (
                      devices.map((device) => {
                        const busy = deviceActionId === device.id

                        return (
                          <TableRow key={device.id}>
                            <TableCell>
                              <div className="space-y-1">
                                <p className="font-medium">
                                  {device.name || `Device #${formatNumber(device.id)}`}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  SN: {device.sn || t.empty}
                                </p>
                              </div>
                            </TableCell>

                            <TableCell dir="ltr">{device.ip || t.empty}</TableCell>

                            <TableCell>
                              <div className="space-y-1">
                                <p>{device.location || t.empty}</p>
                                <p className="text-xs text-muted-foreground">
                                  {device.geo_location || t.empty}
                                </p>
                              </div>
                            </TableCell>

                            <TableCell>
                              {device.status === "online" ? (
                                <Badge className="rounded-full">{t.online}</Badge>
                              ) : (
                                <Badge variant="secondary" className="rounded-full">
                                  {t.offline}
                                </Badge>
                              )}
                            </TableCell>

                            <TableCell>{formatNumber(device.users ?? 0)}</TableCell>
                            <TableCell>{formatMinutes(device.last_activity_minutes, t.minutes)}</TableCell>
                            <TableCell>{formatDate(device.last_sync)}</TableCell>

                            <TableCell className={direction === "rtl" ? "text-left" : "text-right"}>
                              <div
                                className={`flex flex-wrap gap-2 ${
                                  direction === "rtl" ? "justify-start" : "justify-end"
                                }`}
                              >
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="rounded-xl"
                                  onClick={() => testSingleDevice(device.id)}
                                  disabled={busy}
                                >
                                  {busy ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                  ) : (
                                    <BadgeCheck className="h-4 w-4" />
                                  )}
                                  <span>{t.test}</span>
                                </Button>

                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="rounded-xl"
                                  onClick={() => syncSingleDevice(device.id)}
                                  disabled={busy}
                                >
                                  {busy ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                  ) : (
                                    <RefreshCw className="h-4 w-4" />
                                  )}
                                  <span>{t.sync}</span>
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        )
                      })
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="employees" className="space-y-6">
          <Card className="rounded-3xl border-border/60">
            <CardHeader className="gap-4">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  {t.companyEmployeesTitle}
                </CardTitle>
                <CardDescription>{t.companyEmployeesDesc}</CardDescription>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <Card className="rounded-2xl border-border/60 shadow-none">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">{t.filterCardTitle}</CardTitle>
                  <CardDescription>{t.filterCardDesc}</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-[1fr_220px_220px]">
                  <div className="relative">
                    <Search
                      className={`pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground ${
                        direction === "rtl" ? "right-3" : "left-3"
                      }`}
                    />
                    <Input
                      placeholder={t.searchEmployees}
                      value={employeeSearch}
                      onChange={(e) => setEmployeeSearch(e.target.value)}
                      className={`rounded-2xl ${direction === "rtl" ? "pr-9" : "pl-9"}`}
                    />
                  </div>

                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.employees}</p>
                    <p className="mt-1 text-lg font-semibold">
                      {formatNumber(filteredSystemEmployees.length)}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.linked}</p>
                    <p className="mt-1 text-lg font-semibold">
                      {formatNumber(linkedSystemEmployeesCount)}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <div className="overflow-x-auto rounded-2xl border border-border/60">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t.employee}</TableHead>
                      <TableHead>{t.department}</TableHead>
                      <TableHead>{t.jobTitle}</TableHead>
                      <TableHead>{t.role}</TableHead>
                      <TableHead>{t.biotimeCode}</TableHead>
                      <TableHead>{t.status}</TableHead>
                      <TableHead className={direction === "rtl" ? "text-left" : "text-right"}>
                        {t.actions}
                      </TableHead>
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {filteredSystemEmployees.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                          {t.noMatchingEmployees}
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredSystemEmployees.map((employee) => {
                        const displayName =
                          employee.full_name ||
                          employee.name ||
                          employee.username ||
                          `Employee #${formatNumber(employee.id)}`

                        const isLinked = !!employee.biotime_code
                        const busy = employeeActionId === employee.id

                        return (
                          <TableRow key={employee.id}>
                            <TableCell>
                              <div className="space-y-1">
                                <p className="font-medium">{displayName}</p>
                                <p className="text-xs text-muted-foreground">
                                  {employee.email || employee.username || t.empty}
                                </p>
                              </div>
                            </TableCell>

                            <TableCell>{employee.department || t.empty}</TableCell>
                            <TableCell>{employee.job_title || t.empty}</TableCell>
                            <TableCell>{employee.role || t.empty}</TableCell>
                            <TableCell dir="ltr">{employee.biotime_code || t.empty}</TableCell>

                            <TableCell>
                              {isLinked ? (
                                <Badge className="rounded-full">{t.linked}</Badge>
                              ) : (
                                <Badge variant="secondary" className="rounded-full">
                                  {t.notLinked}
                                </Badge>
                              )}
                            </TableCell>

                            <TableCell className={direction === "rtl" ? "text-left" : "text-right"}>
                              <div
                                className={`flex flex-wrap gap-2 ${
                                  direction === "rtl" ? "justify-start" : "justify-end"
                                }`}
                              >
                                {!isLinked ? (
                                  <Button
                                    size="sm"
                                    className="rounded-xl"
                                    onClick={() => pushEmployee(employee.id)}
                                    disabled={busy}
                                  >
                                    {busy ? (
                                      <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                      <Upload className="h-4 w-4" />
                                    )}
                                    <span>{t.push}</span>
                                  </Button>
                                ) : (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="rounded-xl"
                                    onClick={() => syncEmployee(employee.id)}
                                    disabled={busy}
                                  >
                                    {busy ? (
                                      <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                      <RefreshCw className="h-4 w-4" />
                                    )}
                                    <span>{t.sync}</span>
                                  </Button>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                        )
                      })
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="biotime-employees" className="space-y-6">
          <Card className="rounded-3xl border-border/60">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Link2 className="h-5 w-5" />
                {t.linkTitle}
              </CardTitle>
              <CardDescription>{t.linkDesc}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-5">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>{t.systemEmployee}</Label>
                  <Select
                    value={selectedSystemEmployeeId}
                    onValueChange={setSelectedSystemEmployeeId}
                  >
                    <SelectTrigger className="rounded-2xl">
                      <SelectValue placeholder={t.selectSystemEmployee} />
                    </SelectTrigger>
                    <SelectContent>
                      {systemEmployees.length === 0 ? (
                        <SelectItem value="__empty_system" disabled>
                          {t.noMatchingEmployees}
                        </SelectItem>
                      ) : (
                        systemEmployees.map((employee) => {
                          const displayName =
                            employee.full_name ||
                            employee.name ||
                            employee.username ||
                            `Employee #${formatNumber(employee.id)}`

                          return (
                            <SelectItem key={employee.id} value={String(employee.id)}>
                              {displayName}
                            </SelectItem>
                          )
                        })
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>{t.biotimeEmployee}</Label>
                  <Select value={selectedBiotimeCode} onValueChange={setSelectedBiotimeCode}>
                    <SelectTrigger className="rounded-2xl">
                      <SelectValue placeholder={t.selectBiotimeEmployee} />
                    </SelectTrigger>
                    <SelectContent>
                      {biotimeEmployees.length === 0 ? (
                        <SelectItem value="__empty_biotime" disabled>
                          {t.noBiotimeEmployees}
                        </SelectItem>
                      ) : (
                        biotimeEmployees.map((employee) => (
                          <SelectItem key={employee.id} value={employee.biotime_code}>
                            {employee.full_name} ({employee.biotime_code})
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button onClick={linkEmployee} disabled={linkBusy} className="rounded-2xl">
                  {linkBusy ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Link2 className="h-4 w-4" />
                  )}
                  <span>{t.linkEmployee}</span>
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-3xl border-border/60">
            <CardHeader className="gap-4">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Fingerprint className="h-5 w-5" />
                  {t.biotimeEmployeesTitle}
                </CardTitle>
                <CardDescription>{t.biotimeEmployeesDesc}</CardDescription>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <Card className="rounded-2xl border-border/60 shadow-none">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">{t.filterCardTitle}</CardTitle>
                  <CardDescription>{t.filterCardDesc}</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-[1fr_220px_220px]">
                  <div className="relative">
                    <Search
                      className={`pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground ${
                        direction === "rtl" ? "right-3" : "left-3"
                      }`}
                    />
                    <Input
                      placeholder={t.searchBiotimeEmployees}
                      value={biotimeSearch}
                      onChange={(e) => setBiotimeSearch(e.target.value)}
                      className={`rounded-2xl ${direction === "rtl" ? "pr-9" : "pl-9"}`}
                    />
                  </div>

                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.employees}</p>
                    <p className="mt-1 text-lg font-semibold">
                      {formatNumber(filteredBiotimeEmployees.length)}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.linked}</p>
                    <p className="mt-1 text-lg font-semibold">{formatNumber(linkedCount)}</p>
                  </div>
                </CardContent>
              </Card>

              <div className="overflow-x-auto rounded-2xl border border-border/60">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t.fullName}</TableHead>
                      <TableHead>{t.biotimeCode}</TableHead>
                      <TableHead>{t.department}</TableHead>
                      <TableHead>{t.position}</TableHead>
                      <TableHead>{t.linked}</TableHead>
                      <TableHead>{t.status}</TableHead>
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {filteredBiotimeEmployees.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                          {t.noBiotimeEmployees}
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredBiotimeEmployees.map((employee) => (
                        <TableRow key={employee.id}>
                          <TableCell className="font-medium">{employee.full_name}</TableCell>
                          <TableCell dir="ltr">{employee.biotime_code}</TableCell>
                          <TableCell>{employee.department || t.empty}</TableCell>
                          <TableCell>{employee.position || t.empty}</TableCell>
                          <TableCell>
                            {employee.is_linked ? (
                              <Badge className="rounded-full">{t.linked}</Badge>
                            ) : (
                              <Badge variant="secondary" className="rounded-full">
                                {t.unlinked}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            {employee.is_active ? (
                              <Badge variant="outline" className="rounded-full">
                                {t.active}
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="rounded-full">
                                {t.inactive}
                              </Badge>
                            )}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs" className="space-y-6">
          <Card className="rounded-3xl border-border/60">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock3 className="h-5 w-5" />
                {t.logsTitle}
              </CardTitle>
              <CardDescription>{t.logsDesc}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <Card className="rounded-2xl border-border/60 shadow-none">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">{t.summaryCardTitle}</CardTitle>
                  <CardDescription>{t.summaryCardDesc}</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-3 sm:grid-cols-4">
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.logs}</p>
                    <p className="mt-1 text-lg font-semibold">{formatNumber(syncLogs.length)}</p>
                  </div>
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.devices}</p>
                    <p className="mt-1 text-lg font-semibold">
                      {formatNumber(
                        syncLogs.reduce((sum, item) => sum + (item.devices_synced ?? 0), 0)
                      )}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.employees}</p>
                    <p className="mt-1 text-lg font-semibold">
                      {formatNumber(
                        syncLogs.reduce((sum, item) => sum + (item.employees_synced ?? 0), 0)
                      )}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">{t.records}</p>
                    <p className="mt-1 text-lg font-semibold">
                      {formatNumber(
                        syncLogs.reduce((sum, item) => sum + (item.logs_synced ?? 0), 0)
                      )}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <div className="overflow-x-auto rounded-2xl border border-border/60">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t.status}</TableHead>
                      <TableHead>{t.message}</TableHead>
                      <TableHead>{t.devices}</TableHead>
                      <TableHead>{t.employees}</TableHead>
                      <TableHead>{t.logs}</TableHead>
                      <TableHead>{t.timestamp}</TableHead>
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {syncLogs.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                          {t.noLogs}
                        </TableCell>
                      </TableRow>
                    ) : (
                      syncLogs.map((log) => (
                        <TableRow key={log.id}>
                          <TableCell>
                            {log.status === "success" ? (
                              <Badge className="rounded-full">
                                <CheckCircle2 className="h-3.5 w-3.5" />
                                <span>{t.success}</span>
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="rounded-full">
                                {log.status || t.unknown}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell className="max-w-[420px] truncate">
                            {log.message || t.empty}
                          </TableCell>
                          <TableCell>{formatNumber(log.devices_synced ?? 0)}</TableCell>
                          <TableCell>{formatNumber(log.employees_synced ?? 0)}</TableCell>
                          <TableCell>{formatNumber(log.logs_synced ?? 0)}</TableCell>
                          <TableCell>{formatDate(log.timestamp)}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}