"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Activity,
  BadgeCheck,
  Building2,
  CheckCircle2,
  Clock3,
  Cpu,
  Database,
  Fingerprint,
  Loader2,
  RefreshCw,
  Save,
  Search,
  Server,
  Settings2,
  ShieldCheck,
  Unplug,
  Users,
  UserRound,
  Wifi,
  WifiOff,
  Link2,
  Upload,
  ArrowUpRight,
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

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

function formatDate(value?: string | null) {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"
  return date.toLocaleString("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function formatMinutes(value?: number | null) {
  if (value === null || value === undefined) return "—"
  return `${value} min`
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
  const isFormLikeMethod =
    (options.method || "GET").toUpperCase() !== "GET" &&
    (options.method || "GET").toUpperCase() !== "HEAD"

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
    throw new Error(
      data?.message || data?.error || "Unexpected request error."
    )
  }

  return data
}

export default function CompanyBiotimePage() {
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
    const res = await apiFetch<{ employees?: SystemEmployeeItem[] }>(
      "/api/company/employees/"
    )
    setSystemEmployees(Array.isArray(res.employees) ? res.employees : [])
  }, [])

  const loadSyncLogs = useCallback(async () => {
    const res = await apiFetch<{ logs?: SyncLogItem[] }>("/api/company/biotime/sync-logs/")
    setSyncLogs(Array.isArray(res.logs) ? res.logs : [])
  }, [])

  const loadAll = useCallback(async (mode: "initial" | "refresh" = "initial") => {
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
      toast.error(error instanceof Error ? error.message : "Failed to load BioTime page.")
    } finally {
      setPageLoading(false)
      setRefreshing(false)
    }
  }, [loadStatus, loadDevices, loadBiotimeEmployees, loadSystemEmployees, loadSyncLogs])

  useEffect(() => {
    loadAll("initial")
  }, [loadAll])

  const connectedBadge = useMemo(() => {
    if (!status?.connected) {
      return (
        <Badge variant="secondary" className="gap-1 rounded-full">
          <WifiOff className="h-3.5 w-3.5" />
          Not Connected
        </Badge>
      )
    }

    return (
      <Badge className="gap-1 rounded-full">
        <Wifi className="h-3.5 w-3.5" />
        Connected
      </Badge>
    )
  }, [status])

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
      const haystack = [
        item.full_name,
        item.biotime_code,
        item.department,
        item.position,
      ]
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

      toast.success("تم حفظ إعدادات BioTime بنجاح.")
      await loadStatus()
    } catch (error) {
      console.error("Save settings error:", error)
      toast.error(error instanceof Error ? error.message : "Failed to save settings.")
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

      toast.success(res.message || "تم اختبار الاتصال بنجاح.")
      await loadStatus()
    } catch (error) {
      console.error("Test connection error:", error)
      toast.error(error instanceof Error ? error.message : "Connection test failed.")
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

      toast.success(res.message || "تمت إعادة تعيين الاتصال.")
      await loadStatus()
    } catch (error) {
      console.error("Reset connection error:", error)
      toast.error(error instanceof Error ? error.message : "Reset connection failed.")
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

      toast.success(res.message || "تمت مزامنة الأجهزة بنجاح.")
      await Promise.all([loadDevices(), loadSyncLogs()])
    } catch (error) {
      console.error("Sync devices error:", error)
      toast.error(error instanceof Error ? error.message : "Devices sync failed.")
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

      toast.success(res.message || "تمت مزامنة موظفي BioTime بنجاح.")
      await Promise.all([loadBiotimeEmployees(), loadSyncLogs()])
    } catch (error) {
      console.error("Sync employees error:", error)
      toast.error(error instanceof Error ? error.message : "Employees sync failed.")
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

      toast.success(res.message || `Device #${deviceId} is reachable.`)
    } catch (error) {
      console.error("Test device error:", error)
      toast.error(error instanceof Error ? error.message : "Device test failed.")
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

      toast.success(res.message || `Device #${deviceId} synced successfully.`)
      await loadDevices()
    } catch (error) {
      console.error("Sync single device error:", error)
      toast.error(error instanceof Error ? error.message : "Single device sync failed.")
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

      toast.success(res.message || "تم إرسال الموظف إلى BioTime.")
      await Promise.all([loadSystemEmployees(), loadBiotimeEmployees(), loadSyncLogs()])
    } catch (error) {
      console.error("Push employee error:", error)
      toast.error(error instanceof Error ? error.message : "Push employee failed.")
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

      toast.success(res.message || "تمت مزامنة الموظف مع BioTime.")
      await Promise.all([loadSystemEmployees(), loadBiotimeEmployees(), loadSyncLogs()])
    } catch (error) {
      console.error("Sync employee error:", error)
      toast.error(error instanceof Error ? error.message : "Sync employee failed.")
    } finally {
      setEmployeeActionId(null)
    }
  }

  const linkEmployee = async () => {
    try {
      if (!selectedSystemEmployeeId || !selectedBiotimeCode) {
        toast.error("اختر موظف النظام وموظف BioTime أولًا.")
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

      toast.success(res.message || "تم ربط الموظف بنجاح.")
      setSelectedSystemEmployeeId("")
      setSelectedBiotimeCode("")
      await Promise.all([loadSystemEmployees(), loadBiotimeEmployees()])
    } catch (error) {
      console.error("Link employee error:", error)
      toast.error(error instanceof Error ? error.message : "Employee link failed.")
    } finally {
      setLinkBusy(false)
    }
  }

  if (pageLoading) {
    return (
      <div className="space-y-6 p-6">
        <Card className="rounded-3xl border-border/60">
          <CardContent className="flex min-h-[360px] items-center justify-center">
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              جاري تحميل صفحة BioTime...
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* =========================================================
          Hero
      ========================================================= */}
      <div className="flex flex-col gap-4 rounded-3xl border border-border/60 bg-background/70 p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="rounded-full px-3 py-1">
                Company BioTime
              </Badge>
              {connectedBadge}
            </div>

            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                BioTime Control Center
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                إدارة ربط BioTime للشركة، إعدادات الحساب، الأجهزة، الموظفين، وحالة التكامل
                بالكامل من شاشة واحدة.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4" />
                Company Scoped
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Database className="h-4 w-4" />
                DB Driven Status
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Activity className="h-4 w-4" />
                Live Actions
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              onClick={() => loadAll("refresh")}
              disabled={refreshing}
              className="rounded-2xl"
            >
              {refreshing ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Refresh
            </Button>

            <Button
              onClick={testConnection}
              disabled={testBusy}
              className="rounded-2xl"
            >
              {testBusy ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <BadgeCheck className="mr-2 h-4 w-4" />
              )}
              Test Connection
            </Button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card className="rounded-3xl border-border/60">
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-xs text-muted-foreground">Connection Status</p>
                <p className="mt-1 text-xl font-semibold">
                  {status?.connected ? "Connected" : "Not Connected"}
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
              <div>
                <p className="text-xs text-muted-foreground">Devices Online</p>
                <p className="mt-1 text-xl font-semibold">
                  {onlineDevicesCount} / {devices.length}
                </p>
              </div>
              <div className="rounded-2xl border border-border/60 p-3">
                <Cpu className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-3xl border-border/60">
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-xs text-muted-foreground">BioTime Employees</p>
                <p className="mt-1 text-xl font-semibold">{biotimeEmployees.length}</p>
              </div>
              <div className="rounded-2xl border border-border/60 p-3">
                <Fingerprint className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-3xl border-border/60">
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-xs text-muted-foreground">Linked Employees</p>
                <p className="mt-1 text-xl font-semibold">{linkedCount}</p>
              </div>
              <div className="rounded-2xl border border-border/60 p-3">
                <Link2 className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* =========================================================
          Tabs
      ========================================================= */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="h-auto flex-wrap rounded-2xl p-1">
          <TabsTrigger value="overview" className="rounded-xl">
            Overview
          </TabsTrigger>
          <TabsTrigger value="settings" className="rounded-xl">
            Settings
          </TabsTrigger>
          <TabsTrigger value="devices" className="rounded-xl">
            Devices
          </TabsTrigger>
          <TabsTrigger value="employees" className="rounded-xl">
            Company Employees
          </TabsTrigger>
          <TabsTrigger value="biotime-employees" className="rounded-xl">
            BioTime Employees
          </TabsTrigger>
          <TabsTrigger value="logs" className="rounded-xl">
            Sync Logs
          </TabsTrigger>
        </TabsList>

        {/* =======================================================
            Overview
        ======================================================= */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 xl:grid-cols-[1.1fr_.9fr]">
            <Card className="rounded-3xl border-border/60">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="h-5 w-5" />
                  Account Overview
                </CardTitle>
                <CardDescription>
                  نظرة سريعة على حالة ربط حساب BioTime الحالي.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">Server URL</p>
                    <p className="mt-1 break-all text-sm font-medium">
                      {status?.server_url || "—"}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">Account Email</p>
                    <p className="mt-1 break-all text-sm font-medium">
                      {status?.email || "—"}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">Last Connected</p>
                    <p className="mt-1 text-sm font-medium">
                      {formatDate(status?.last_connected_at)}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-border/60 p-4">
                    <p className="text-xs text-muted-foreground">Reason</p>
                    <p className="mt-1 text-sm font-medium">
                      {status?.reason || (status?.connected ? "configured" : "—")}
                    </p>
                  </div>
                </div>

                <Separator />

                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={saveSettings}
                    disabled={settingsBusy}
                    className="rounded-2xl"
                  >
                    {settingsBusy ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="mr-2 h-4 w-4" />
                    )}
                    Save Settings
                  </Button>

                  <Button
                    variant="outline"
                    onClick={testConnection}
                    disabled={testBusy}
                    className="rounded-2xl"
                  >
                    {testBusy ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <BadgeCheck className="mr-2 h-4 w-4" />
                    )}
                    Test Connection
                  </Button>

                  <Button
                    variant="outline"
                    onClick={syncDevices}
                    disabled={syncDevicesBusy}
                    className="rounded-2xl"
                  >
                    {syncDevicesBusy ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Cpu className="mr-2 h-4 w-4" />
                    )}
                    Sync Devices
                  </Button>

                  <Button
                    variant="outline"
                    onClick={syncEmployees}
                    disabled={syncEmployeesBusy}
                    className="rounded-2xl"
                  >
                    {syncEmployeesBusy ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Users className="mr-2 h-4 w-4" />
                    )}
                    Sync Employees
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-3xl border-border/60">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings2 className="h-5 w-5" />
                  Quick Actions
                </CardTitle>
                <CardDescription>
                  إجراءات سريعة لإدارة الاتصال والتكامل من نفس الصفحة.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3">
                <Button
                  variant="outline"
                  className="justify-between rounded-2xl"
                  onClick={() => setActiveTab("settings")}
                >
                  <span className="inline-flex items-center gap-2">
                    <Server className="h-4 w-4" />
                    Open BioTime Settings
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
                    Manage Devices
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
                    Push / Sync Company Employees
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
                    Link Existing BioTime Employees
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
                    Reset Connection
                  </span>
                  <ArrowUpRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* =======================================================
            Settings
        ======================================================= */}
        <TabsContent value="settings" className="space-y-6">
          <Card className="rounded-3xl border-border/60">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                BioTime Account Settings
              </CardTitle>
              <CardDescription>
                احفظ رابط السيرفر وبيانات حساب BioTime الخاص بالشركة.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-5 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="server_url">Server URL</Label>
                  <Input
                    id="server_url"
                    placeholder="https://your-biotime-server.com"
                    value={settings.server_url}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, server_url: e.target.value }))
                    }
                    className="rounded-2xl"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="company">BioTime Company Code</Label>
                  <Input
                    id="company"
                    placeholder="Company code / tenant code"
                    value={settings.company}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, company: e.target.value }))
                    }
                    className="rounded-2xl"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Account Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="account@company.com"
                    value={settings.email}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, email: e.target.value }))
                    }
                    className="rounded-2xl"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Account Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={settings.password}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, password: e.target.value }))
                    }
                    className="rounded-2xl"
                  />
                </div>
              </div>

              <div className="rounded-2xl border border-dashed border-border/70 p-4 text-sm text-muted-foreground">
                ملاحظة: يجب أن يكون الرابط بصيغة HTTPS لأن الباكند يتحقق من ذلك قبل الحفظ.
              </div>

              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={saveSettings}
                  disabled={settingsBusy}
                  className="rounded-2xl"
                >
                  {settingsBusy ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save Settings
                </Button>

                <Button
                  variant="outline"
                  onClick={testConnection}
                  disabled={testBusy}
                  className="rounded-2xl"
                >
                  {testBusy ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <BadgeCheck className="mr-2 h-4 w-4" />
                  )}
                  Test Connection
                </Button>

                <Button
                  variant="outline"
                  onClick={resetConnection}
                  disabled={resetBusy}
                  className="rounded-2xl"
                >
                  {resetBusy ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Unplug className="mr-2 h-4 w-4" />
                  )}
                  Reset Connection
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* =======================================================
            Devices
        ======================================================= */}
        <TabsContent value="devices" className="space-y-6">
          <Card className="rounded-3xl border-border/60">
            <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5" />
                  BioTime Devices
                </CardTitle>
                <CardDescription>
                  عرض الأجهزة المسحوبة من BioTime مع حالة الاتصال وآخر نشاط.
                </CardDescription>
              </div>

              <Button
                onClick={syncDevices}
                disabled={syncDevicesBusy}
                className="rounded-2xl"
              >
                {syncDevicesBusy ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                Sync Devices
              </Button>
            </CardHeader>

            <CardContent>
              <div className="overflow-x-auto rounded-2xl border border-border/60">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Device</TableHead>
                      <TableHead>IP</TableHead>
                      <TableHead>Location</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Users</TableHead>
                      <TableHead>Last Activity</TableHead>
                      <TableHead>Last Sync</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {devices.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                          لا توجد أجهزة حاليًا.
                        </TableCell>
                      </TableRow>
                    ) : (
                      devices.map((device) => {
                        const busy = deviceActionId === device.id

                        return (
                          <TableRow key={device.id}>
                            <TableCell>
                              <div className="space-y-1">
                                <p className="font-medium">{device.name || `Device #${device.id}`}</p>
                                <p className="text-xs text-muted-foreground">
                                  SN: {device.sn || "—"}
                                </p>
                              </div>
                            </TableCell>

                            <TableCell>{device.ip || "—"}</TableCell>

                            <TableCell>
                              <div className="space-y-1">
                                <p>{device.location || "—"}</p>
                                <p className="text-xs text-muted-foreground">
                                  {device.geo_location || "—"}
                                </p>
                              </div>
                            </TableCell>

                            <TableCell>
                              {device.status === "online" ? (
                                <Badge className="rounded-full">Online</Badge>
                              ) : (
                                <Badge variant="secondary" className="rounded-full">
                                  Offline
                                </Badge>
                              )}
                            </TableCell>

                            <TableCell>{device.users ?? 0}</TableCell>

                            <TableCell>{formatMinutes(device.last_activity_minutes)}</TableCell>

                            <TableCell>{formatDate(device.last_sync)}</TableCell>

                            <TableCell className="text-right">
                              <div className="flex flex-wrap justify-end gap-2">
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

        {/* =======================================================
            Company Employees
        ======================================================= */}
        <TabsContent value="employees" className="space-y-6">
          <Card className="rounded-3xl border-border/60">
            <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Company Employees
                </CardTitle>
                <CardDescription>
                  إرسال موظفي الشركة إلى BioTime أو مزامنتهم إذا كانوا مرتبطين مسبقًا.
                </CardDescription>
              </div>

              <div className="relative w-full max-w-sm">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search employees..."
                  value={employeeSearch}
                  onChange={(e) => setEmployeeSearch(e.target.value)}
                  className="rounded-2xl pl-9"
                />
              </div>
            </CardHeader>

            <CardContent>
              <div className="overflow-x-auto rounded-2xl border border-border/60">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Employee</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Job Title</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>BioTime Code</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredSystemEmployees.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                          لا يوجد موظفون مطابقون.
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredSystemEmployees.map((employee) => {
                        const displayName =
                          employee.full_name ||
                          employee.name ||
                          employee.username ||
                          `Employee #${employee.id}`

                        const isLinked = !!employee.biotime_code
                        const busy = employeeActionId === employee.id

                        return (
                          <TableRow key={employee.id}>
                            <TableCell>
                              <div className="space-y-1">
                                <p className="font-medium">{displayName}</p>
                                <p className="text-xs text-muted-foreground">
                                  {employee.email || employee.username || "—"}
                                </p>
                              </div>
                            </TableCell>

                            <TableCell>{employee.department || "—"}</TableCell>
                            <TableCell>{employee.job_title || "—"}</TableCell>
                            <TableCell>{employee.role || "—"}</TableCell>
                            <TableCell>{employee.biotime_code || "—"}</TableCell>

                            <TableCell>
                              {isLinked ? (
                                <Badge className="rounded-full">Linked</Badge>
                              ) : (
                                <Badge variant="secondary" className="rounded-full">
                                  Not Linked
                                </Badge>
                              )}
                            </TableCell>

                            <TableCell className="text-right">
                              <div className="flex flex-wrap justify-end gap-2">
                                {!isLinked ? (
                                  <Button
                                    size="sm"
                                    className="rounded-xl"
                                    onClick={() => pushEmployee(employee.id)}
                                    disabled={busy}
                                  >
                                    {busy ? (
                                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    ) : (
                                      <Upload className="mr-2 h-4 w-4" />
                                    )}
                                    Push
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
                                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    ) : (
                                      <RefreshCw className="mr-2 h-4 w-4" />
                                    )}
                                    Sync
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

        {/* =======================================================
            Biotime Employees
        ======================================================= */}
        <TabsContent value="biotime-employees" className="space-y-6">
          <Card className="rounded-3xl border-border/60">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Link2 className="h-5 w-5" />
                Link Existing BioTime Employee
              </CardTitle>
              <CardDescription>
                اربط موظفًا موجودًا في BioTime مع موظف في النظام بدون إنشاء موظف جديد.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="system_employee_id">System Employee ID</Label>
                  <Input
                    id="system_employee_id"
                    placeholder="مثال: 12"
                    value={selectedSystemEmployeeId}
                    onChange={(e) => setSelectedSystemEmployeeId(e.target.value)}
                    className="rounded-2xl"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="biotime_code">BioTime Code</Label>
                  <Input
                    id="biotime_code"
                    placeholder="مثال: 10045"
                    value={selectedBiotimeCode}
                    onChange={(e) => setSelectedBiotimeCode(e.target.value)}
                    className="rounded-2xl"
                  />
                </div>
              </div>

              <Button onClick={linkEmployee} disabled={linkBusy} className="rounded-2xl">
                {linkBusy ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Link2 className="mr-2 h-4 w-4" />
                )}
                Link Employee
              </Button>
            </CardContent>
          </Card>

          <Card className="rounded-3xl border-border/60">
            <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Fingerprint className="h-5 w-5" />
                  BioTime Employees
                </CardTitle>
                <CardDescription>
                  قائمة الموظفين القادمين من BioTime مع حالة الربط الحالية.
                </CardDescription>
              </div>

              <div className="relative w-full max-w-sm">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search BioTime employees..."
                  value={biotimeSearch}
                  onChange={(e) => setBiotimeSearch(e.target.value)}
                  className="rounded-2xl pl-9"
                />
              </div>
            </CardHeader>

            <CardContent>
              <div className="overflow-x-auto rounded-2xl border border-border/60">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Full Name</TableHead>
                      <TableHead>BioTime Code</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Position</TableHead>
                      <TableHead>Linked</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredBiotimeEmployees.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                          لا يوجد موظفون في BioTime حاليًا.
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredBiotimeEmployees.map((employee) => (
                        <TableRow key={employee.id}>
                          <TableCell className="font-medium">{employee.full_name}</TableCell>
                          <TableCell>{employee.biotime_code}</TableCell>
                          <TableCell>{employee.department || "—"}</TableCell>
                          <TableCell>{employee.position || "—"}</TableCell>
                          <TableCell>
                            {employee.is_linked ? (
                              <Badge className="rounded-full">Linked</Badge>
                            ) : (
                              <Badge variant="secondary" className="rounded-full">
                                Unlinked
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            {employee.is_active ? (
                              <Badge variant="outline" className="rounded-full">
                                Active
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="rounded-full">
                                Inactive
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

        {/* =======================================================
            Logs
        ======================================================= */}
        <TabsContent value="logs" className="space-y-6">
          <Card className="rounded-3xl border-border/60">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock3 className="h-5 w-5" />
                BioTime Sync Logs
              </CardTitle>
              <CardDescription>
                آخر سجلات المزامنة المسجلة في النظام.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto rounded-2xl border border-border/60">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Status</TableHead>
                      <TableHead>Message</TableHead>
                      <TableHead>Devices</TableHead>
                      <TableHead>Employees</TableHead>
                      <TableHead>Logs</TableHead>
                      <TableHead>Timestamp</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {syncLogs.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                          لا توجد سجلات مزامنة حاليًا.
                        </TableCell>
                      </TableRow>
                    ) : (
                      syncLogs.map((log) => (
                        <TableRow key={log.id}>
                          <TableCell>
                            {log.status === "success" ? (
                              <Badge className="rounded-full">
                                <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                                Success
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="rounded-full">
                                {log.status || "unknown"}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell className="max-w-[420px] truncate">
                            {log.message || "—"}
                          </TableCell>
                          <TableCell>{log.devices_synced ?? 0}</TableCell>
                          <TableCell>{log.employees_synced ?? 0}</TableCell>
                          <TableCell>{log.logs_synced ?? 0}</TableCell>
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