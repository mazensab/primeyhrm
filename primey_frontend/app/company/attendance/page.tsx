"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  BadgeCheck,
  Briefcase,
  Building2,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Cpu,
  FileSpreadsheet,
  Fingerprint,
  GitBranch,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  TriangleAlert,
  UserCheck,
  Users,
  Workflow,
  Zap,
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
import { Separator } from "@/components/ui/separator"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type EmployeeItem = {
  id: number
  full_name?: string
  name?: string
  department?: string | null
  job_title?: string | null
  status?: string | null
  biotime_code?: string | null
}

type DeviceItem = {
  id: number
  name?: string | null
  sn?: string | null
  ip?: string | null
  location?: string | null
  geo_location?: string | null
  status?: string | null
  users?: number | null
  last_activity?: string | null
}

type WorkScheduleItem = {
  id: number
  name?: string | null
  schedule_type?: string | null
  period1_start?: string | null
  period1_end?: string | null
  period2_start?: string | null
  period2_end?: string | null
  weekend_days?: string | null
  weekend_days_ar?: string | null
  target_daily_hours?: string | number | null
  allow_night_overlap?: boolean
  is_active?: boolean
}

type DashboardData = {
  today: {
    present: number
    absent: number
    late: number
    leave: number
  }
  total_records: number
}

type AttendanceRow = {
  employee: string
  employee_id: number
  photo_url?: string | null
  date: string
  status: string
  status_ar: string
  schedule_type?: string | null
  schedule_label?: string | null
  period_display?: string | null
  check_in?: string | null
  check_out?: string | null
  actual_hours?: number | null
  late_minutes?: number | null
  overtime_minutes?: number | null
  location?: string | null
}

type AttendancePolicy = {
  grace_minutes: number
  late_after_minutes: number
  absence_after_minutes: number
  auto_absent_if_no_checkin: boolean
  overtime_enabled?: boolean
}

type UnmappedLog = {
  id: number
  employee_code: string
  punch_time: string
  device_sn?: string | null
  terminal_alias?: string | null
  device_ip?: string | null
  raw_id?: string | number | null
}

function formatTime(value?: string | null) {
  if (!value) return "—"
  return String(value).slice(0, 5)
}

function formatDate(value?: string | null) {
  if (!value) return "—"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleDateString("en-CA")
}

function formatDateTime(value?: string | null) {
  if (!value) return "—"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return `${date.toLocaleDateString("en-CA")} ${date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  })}`
}

function getStatusBadgeClass(status?: string | null) {
  const key = String(status || "").toLowerCase()

  if (["active", "present", "online", "success", "linked"].includes(key)) {
    return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300"
  }

  if (["late", "warning", "pending", "unlinked"].includes(key)) {
    return "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-300"
  }

  if (["leave", "weekend", "before_start"].includes(key)) {
    return "border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-900/50 dark:bg-sky-950/40 dark:text-sky-300"
  }

  if (["inactive", "offline", "failed", "error", "absent", "terminated"].includes(key)) {
    return "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300"
  }

  return "border-border bg-muted text-foreground"
}

function getArabicStatusLabel(row: AttendanceRow) {
  const status = String(row.status || "").toLowerCase()
  const statusAr = String(row.status_ar || "").trim()

  const arabicMap: Record<string, string> = {
    present: "حاضر",
    late: "متأخر",
    absent: "غائب",
    leave: "إجازة",
    weekend: "عطلة",
    before_start: "قبل المباشرة",
    terminated: "منتهي خدمة",
    active: "نشط",
    inactive: "معطل",
    online: "متصل",
    offline: "غير متصل",
    success: "ناجح",
    failed: "فشل",
    error: "خطأ",
    warning: "تحذير",
    linked: "مربوط",
    unlinked: "غير مربوط",
  }

  const englishWords = [
    "present",
    "late",
    "absent",
    "leave",
    "weekend",
    "before_start",
    "terminated",
    "active",
    "inactive",
    "online",
    "offline",
    "success",
    "failed",
    "error",
    "warning",
    "linked",
    "unlinked",
  ]

  if (statusAr && !englishWords.includes(statusAr.toLowerCase())) {
    return statusAr
  }

  return arabicMap[status] || statusAr || row.status || "—"
}

function getScheduleTypeLabel(type?: string | null) {
  const value = String(type || "").toUpperCase()

  if (value === "FULL_TIME") return "دوام كامل"
  if (value === "PART_TIME") return "فترتين"
  if (value === "HOURLY") return "بالساعات"

  return type || "—"
}

function buildSchedulePeriods(schedule: WorkScheduleItem) {
  const periods: string[] = []

  if (schedule.period1_start && schedule.period1_end) {
    periods.push(`${formatTime(schedule.period1_start)} → ${formatTime(schedule.period1_end)}`)
  }

  if (schedule.period2_start && schedule.period2_end) {
    periods.push(`${formatTime(schedule.period2_start)} → ${formatTime(schedule.period2_end)}`)
  }

  if (periods.length > 0) return periods.join(" | ")

  if (schedule.schedule_type === "HOURLY" && schedule.target_daily_hours) {
    return `${schedule.target_daily_hours} ساعات مطلوبة`
  }

  return "—"
}

export default function CompanyAttendancePage() {
  const today = useMemo(() => new Date().toLocaleDateString("en-CA"), [])

  const [employees, setEmployees] = useState<EmployeeItem[]>([])
  const [devices, setDevices] = useState<DeviceItem[]>([])
  const [workSchedules, setWorkSchedules] = useState<WorkScheduleItem[]>([])
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [rows, setRows] = useState<AttendanceRow[]>([])
  const [policy, setPolicy] = useState<AttendancePolicy>({
    grace_minutes: 15,
    late_after_minutes: 30,
    absence_after_minutes: 180,
    auto_absent_if_no_checkin: true,
    overtime_enabled: true,
  })
  const [unmappedLogs, setUnmappedLogs] = useState<UnmappedLog[]>([])

  const [loadingPage, setLoadingPage] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [syncingDevices, setSyncingDevices] = useState(false)
  const [syncingAttendance, setSyncingAttendance] = useState(false)
  const [loadingRows, setLoadingRows] = useState(false)
  const [savingPolicy, setSavingPolicy] = useState(false)

  const [reportSearch, setReportSearch] = useState("")
  const [employeeSearch, setEmployeeSearch] = useState("")
  const [fromDate, setFromDate] = useState(today)
  const [toDate, setToDate] = useState(today)
  const [statusFilter, setStatusFilter] = useState("all")
  const [showUnmapped, setShowUnmapped] = useState(false)

  const fetchJson = useCallback(async (path: string, init?: RequestInit) => {
    const response = await fetch(`${API_BASE}${path}`, {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
      ...init,
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(data?.message || data?.error || "Request failed")
    }

    return data
  }, [])

  const loadEmployees = useCallback(async () => {
    const data = await fetchJson("/api/company/employees/")
    setEmployees(Array.isArray(data?.employees) ? data.employees : [])
  }, [fetchJson])

  const loadDevices = useCallback(async () => {
    const data = await fetchJson("/api/company/biotime/devices/")
    setDevices(Array.isArray(data?.devices) ? data.devices : [])
  }, [fetchJson])

  const loadWorkSchedules = useCallback(async () => {
    const data = await fetchJson("/api/company/work-schedules/")
    setWorkSchedules(Array.isArray(data?.schedules) ? data.schedules : [])
  }, [fetchJson])

  const loadDashboard = useCallback(async () => {
    const data = await fetchJson("/api/company/attendance/dashboard/")
    setDashboard(data?.data || null)
  }, [fetchJson])

  const loadPolicy = useCallback(async () => {
    const data = await fetchJson("/api/company/attendance/policy/")
    if (data?.policy) {
      setPolicy({
        grace_minutes: Number(data.policy.grace_minutes ?? 15),
        late_after_minutes: Number(data.policy.late_after_minutes ?? 30),
        absence_after_minutes: Number(data.policy.absence_after_minutes ?? 180),
        auto_absent_if_no_checkin: Boolean(data.policy.auto_absent_if_no_checkin),
        overtime_enabled: Boolean(data.policy.overtime_enabled ?? true),
      })
    }
  }, [fetchJson])

  const loadUnmappedLogs = useCallback(async () => {
    const data = await fetchJson("/api/company/attendance/unmapped-logs/")
    setUnmappedLogs(Array.isArray(data?.records) ? data.records : [])
  }, [fetchJson])

  const loadRows = useCallback(async () => {
    setLoadingRows(true)
    try {
      const params = new URLSearchParams()
      if (fromDate) params.set("from_date", fromDate)
      if (toDate) params.set("to_date", toDate)
      if (statusFilter && statusFilter !== "all") params.set("status", statusFilter)

      const data = await fetchJson(`/api/company/attendance/reports/preview/?${params.toString()}`)
      setRows(Array.isArray(data?.rows) ? data.rows : [])
    } catch (error) {
      console.error("Attendance report load error:", error)
      toast.error(error instanceof Error ? error.message : "فشل تحميل تقرير الحضور")
    } finally {
      setLoadingRows(false)
    }
  }, [fetchJson, fromDate, toDate, statusFilter])

  const loadAll = useCallback(
    async (silent = false) => {
      if (silent) {
        setRefreshing(true)
      } else {
        setLoadingPage(true)
      }

      try {
        await Promise.all([
          loadEmployees(),
          loadDevices(),
          loadWorkSchedules(),
          loadDashboard(),
          loadPolicy(),
          loadUnmappedLogs(),
          loadRows(),
        ])
      } catch (error) {
        console.error("Attendance page load error:", error)
        toast.error(error instanceof Error ? error.message : "فشل تحميل صفحة الحضور")
      } finally {
        setLoadingPage(false)
        setRefreshing(false)
      }
    },
    [
      loadDashboard,
      loadDevices,
      loadEmployees,
      loadPolicy,
      loadRows,
      loadUnmappedLogs,
      loadWorkSchedules,
    ]
  )

  useEffect(() => {
    loadAll()
  }, [loadAll])

  const handleSyncDevices = async () => {
    setSyncingDevices(true)
    try {
      const data = await fetchJson("/api/company/biotime/devices/sync/", {
        method: "POST",
      })

      toast.success(data?.message || "تمت مزامنة أجهزة BioTime بنجاح")
      await loadAll(true)
    } catch (error) {
      console.error("BioTime device sync error:", error)
      toast.error(error instanceof Error ? error.message : "فشلت مزامنة الأجهزة")
    } finally {
      setSyncingDevices(false)
    }
  }

  const handleAttendanceSync = async () => {
    setSyncingAttendance(true)
    try {
      const data = await fetchJson("/api/company/attendance/sync/", {
        method: "POST",
      })

      toast.success(data?.message || "تمت مزامنة الحضور بنجاح")
      await Promise.all([loadDashboard(), loadRows(), loadUnmappedLogs()])
    } catch (error) {
      console.error("Attendance sync error:", error)
      toast.error(error instanceof Error ? error.message : "فشلت مزامنة الحضور")
    } finally {
      setSyncingAttendance(false)
    }
  }

  const handleSavePolicy = async () => {
    setSavingPolicy(true)
    try {
      const data = await fetchJson("/api/company/attendance/policy/", {
        method: "PATCH",
        body: JSON.stringify(policy),
      })

      if (data?.policy) {
        setPolicy({
          grace_minutes: Number(data.policy.grace_minutes ?? 15),
          late_after_minutes: Number(data.policy.late_after_minutes ?? 30),
          absence_after_minutes: Number(data.policy.absence_after_minutes ?? 180),
          auto_absent_if_no_checkin: Boolean(data.policy.auto_absent_if_no_checkin),
          overtime_enabled: Boolean(data.policy.overtime_enabled ?? true),
        })
      }

      toast.success("تم حفظ سياسة الحضور بنجاح")
    } catch (error) {
      console.error("Attendance policy save error:", error)
      toast.error(error instanceof Error ? error.message : "فشل حفظ سياسة الحضور")
    } finally {
      setSavingPolicy(false)
    }
  }

  const filteredEmployees = useMemo(() => {
    const query = employeeSearch.trim().toLowerCase()
    if (!query) return employees

    return employees.filter((emp) => {
      return (
        String(emp.full_name || emp.name || "").toLowerCase().includes(query) ||
        String(emp.department || "").toLowerCase().includes(query) ||
        String(emp.job_title || "").toLowerCase().includes(query) ||
        String(emp.biotime_code || "").toLowerCase().includes(query)
      )
    })
  }, [employeeSearch, employees])

  const filteredRows = useMemo(() => {
    const query = reportSearch.trim().toLowerCase()
    if (!query) return rows

    return rows.filter((row) => {
      return (
        String(row.employee || "").toLowerCase().includes(query) ||
        String(getArabicStatusLabel(row)).toLowerCase().includes(query) ||
        String(row.status || "").toLowerCase().includes(query) ||
        String(row.schedule_label || "").toLowerCase().includes(query) ||
        String(row.location || "").toLowerCase().includes(query)
      )
    })
  }, [reportSearch, rows])

  const summary = useMemo(() => {
    const linkedEmployees = employees.filter((emp) => !!emp.biotime_code).length
    const activeEmployees = employees.filter(
      (emp) => String(emp.status || "").toUpperCase() === "ACTIVE"
    ).length
    const activeDevices = devices.filter(
      (device) => String(device.status || "").toLowerCase() === "online"
    ).length
    const activeSchedules = workSchedules.filter((schedule) => !!schedule.is_active).length

    return {
      employeesCount: employees.length,
      linkedEmployees,
      activeEmployees,
      devicesCount: devices.length,
      activeDevices,
      workSchedulesCount: workSchedules.length,
      activeSchedules,
      unmappedCount: unmappedLogs.length,
      totalAttendanceRecords: dashboard?.total_records ?? 0,
      todayPresent: dashboard?.today.present ?? 0,
      todayLate: dashboard?.today.late ?? 0,
      todayAbsent: dashboard?.today.absent ?? 0,
      todayLeave: dashboard?.today.leave ?? 0,
    }
  }, [dashboard, devices, employees, unmappedLogs, workSchedules])

  if (loadingPage) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex items-center gap-3 rounded-2xl border bg-background px-5 py-4 shadow-sm">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm font-medium">جاري تحميل صفحة الحضور...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full border bg-background/80 px-3 py-1 text-xs font-medium text-muted-foreground shadow-sm">
            <Fingerprint className="h-3.5 w-3.5" />
            Company Attendance Center
          </div>

          <div>
            <h1 className="text-2xl font-bold tracking-tight">إدارة الحضور والانصراف</h1>
            <p className="text-sm text-muted-foreground">
              صفحة حضور وانصراف احترافية مربوطة ببيانات الحضور الفعلية، مع عرض BioTime كجزء
              مساند داخل نفس الصفحة دون المساس بهوية صفحة الحضور الأساسية.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            onClick={() => loadAll(true)}
            disabled={refreshing || syncingDevices || syncingAttendance}
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            تحديث
          </Button>

          <Button
            variant="outline"
            onClick={handleSyncDevices}
            disabled={syncingDevices || refreshing || syncingAttendance}
          >
            {syncingDevices ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Cpu className="h-4 w-4" />
            )}
            مزامنة الأجهزة
          </Button>

          <Button
            onClick={handleAttendanceSync}
            disabled={syncingAttendance || refreshing || syncingDevices}
          >
            {syncingAttendance ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4" />
            )}
            مزامنة الحضور
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="rounded-2xl border shadow-sm">
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-muted-foreground">الحضور اليوم</p>
              <p className="mt-2 text-3xl font-bold">{summary.todayPresent}</p>
            </div>
            <div className="rounded-2xl border bg-emerald-50 p-3 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300">
              <UserCheck className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border shadow-sm">
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-muted-foreground">المتأخرون اليوم</p>
              <p className="mt-2 text-3xl font-bold">{summary.todayLate}</p>
            </div>
            <div className="rounded-2xl border bg-amber-50 p-3 text-amber-700 dark:bg-amber-950/30 dark:text-amber-300">
              <Clock3 className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border shadow-sm">
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-muted-foreground">الغياب اليوم</p>
              <p className="mt-2 text-3xl font-bold">{summary.todayAbsent}</p>
            </div>
            <div className="rounded-2xl border bg-rose-50 p-3 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300">
              <TriangleAlert className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border shadow-sm">
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-muted-foreground">إجمالي السجلات</p>
              <p className="mt-2 text-3xl font-bold">{summary.totalAttendanceRecords}</p>
            </div>
            <div className="rounded-2xl border bg-sky-50 p-3 text-sky-700 dark:bg-sky-950/30 dark:text-sky-300">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="rounded-2xl border shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <CardTitle className="text-base">تقرير سجلات الحضور</CardTitle>
              <CardDescription>
                معاينة مباشرة لسجلات الحضور والانصراف الفعلية مع الفلاتر والبحث.
              </CardDescription>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <div className="relative min-w-[220px]">
                <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={reportSearch}
                  onChange={(e) => setReportSearch(e.target.value)}
                  placeholder="بحث باسم الموظف أو الحالة أو الموقع"
                  className="pr-9"
                />
              </div>

              <Button variant="outline" onClick={loadRows} disabled={loadingRows}>
                {loadingRows ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                تحديث التقرير
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">من تاريخ</label>
              <Input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">إلى تاريخ</label>
              <Input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">الحالة</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
              >
                <option value="all">كل الحالات</option>
                <option value="present">حاضر</option>
                <option value="late">متأخر</option>
                <option value="absent">غائب</option>
                <option value="leave">إجازة</option>
                <option value="weekend">عطلة</option>
              </select>
            </div>

            <div className="flex items-end">
              <Button className="w-full" onClick={loadRows} disabled={loadingRows}>
                {loadingRows ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <CalendarDays className="h-4 w-4" />
                )}
                تطبيق الفلاتر
              </Button>
            </div>
          </div>

          <Separator />

          <div className="overflow-x-auto rounded-2xl border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>الموظف</TableHead>
                  <TableHead>التاريخ</TableHead>
                  <TableHead>الحالة</TableHead>
                  <TableHead>الجدول</TableHead>
                  <TableHead>الدخول</TableHead>
                  <TableHead>الخروج</TableHead>
                  <TableHead>ساعات العمل</TableHead>
                  <TableHead>التأخير</TableHead>
                  <TableHead>الإضافي</TableHead>
                  <TableHead>الموقع</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {loadingRows ? (
                  <TableRow>
                    <TableCell colSpan={10} className="h-24 text-center">
                      <div className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        جاري تحميل التقرير...
                      </div>
                    </TableCell>
                  </TableRow>
                ) : filteredRows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={10} className="h-24 text-center text-muted-foreground">
                      لا توجد بيانات مطابقة للفلاتر الحالية.
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredRows.map((row, index) => (
                    <TableRow key={`${row.employee_id}-${row.date}-${index}`}>
                      <TableCell>
                        <div className="min-w-[180px]">
                          <p className="font-medium">{row.employee}</p>
                          <p className="text-xs text-muted-foreground">{row.schedule_label || "—"}</p>
                        </div>
                      </TableCell>
                      <TableCell>{formatDate(row.date)}</TableCell>
                      <TableCell>
                        <Badge className={getStatusBadgeClass(row.status)}>
                          {getArabicStatusLabel(row)}
                        </Badge>
                      </TableCell>
                      <TableCell className="whitespace-pre-line text-sm text-muted-foreground">
                        {row.period_display || "—"}
                      </TableCell>
                      <TableCell>{formatTime(row.check_in)}</TableCell>
                      <TableCell>{formatTime(row.check_out)}</TableCell>
                      <TableCell>{row.actual_hours ?? 0}</TableCell>
                      <TableCell>{row.late_minutes ?? 0} د</TableCell>
                      <TableCell>{row.overtime_minutes ?? 0} د</TableCell>
                      <TableCell>{row.location || "—"}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="rounded-2xl border shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">ملخص الربط والتجهيز</CardTitle>
            <CardDescription>نظرة سريعة على جاهزية بيئة الحضور داخل الشركة.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border bg-muted/30 p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Users className="h-4 w-4" />
                  الموظفون
                </div>
                <p className="mt-2 text-2xl font-bold">{summary.employeesCount}</p>
              </div>

              <div className="rounded-2xl border bg-muted/30 p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <BadgeCheck className="h-4 w-4" />
                  مربوطون بـ BioTime
                </div>
                <p className="mt-2 text-2xl font-bold">{summary.linkedEmployees}</p>
              </div>

              <div className="rounded-2xl border bg-muted/30 p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Cpu className="h-4 w-4" />
                  أجهزة أونلاين
                </div>
                <p className="mt-2 text-2xl font-bold">{summary.activeDevices}</p>
              </div>

              <button
                type="button"
                onClick={() => setShowUnmapped((prev) => !prev)}
                className="rounded-2xl border bg-muted/30 p-4 text-right transition hover:bg-muted/50"
              >
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <TriangleAlert className="h-4 w-4" />
                  سجلات غير مربوطة
                </div>
                <p className="mt-2 text-2xl font-bold">{summary.unmappedCount}</p>
              </button>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">سياسة الحضور</CardTitle>
            <CardDescription>تعديل إعدادات التأخير والغياب وسياسة الحضور للشركة.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3">
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground">Grace Minutes</label>
                <Input
                  type="number"
                  min={0}
                  value={policy.grace_minutes}
                  onChange={(e) =>
                    setPolicy((prev) => ({
                      ...prev,
                      grace_minutes: Number(e.target.value || 0),
                    }))
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground">Late After Minutes</label>
                <Input
                  type="number"
                  min={0}
                  value={policy.late_after_minutes}
                  onChange={(e) =>
                    setPolicy((prev) => ({
                      ...prev,
                      late_after_minutes: Number(e.target.value || 0),
                    }))
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground">Absence After Minutes</label>
                <Input
                  type="number"
                  min={0}
                  value={policy.absence_after_minutes}
                  onChange={(e) =>
                    setPolicy((prev) => ({
                      ...prev,
                      absence_after_minutes: Number(e.target.value || 0),
                    }))
                  }
                />
              </div>
            </div>

            <div className="grid gap-2">
              <button
                type="button"
                onClick={() =>
                  setPolicy((prev) => ({
                    ...prev,
                    auto_absent_if_no_checkin: !prev.auto_absent_if_no_checkin,
                  }))
                }
                className={`flex items-center justify-between rounded-2xl border px-4 py-3 text-sm font-medium transition ${
                  policy.auto_absent_if_no_checkin
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300"
                    : "border-border bg-background text-foreground"
                }`}
              >
                <span className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4" />
                  Auto Absent If No Check-in
                </span>
                <span>{policy.auto_absent_if_no_checkin ? "ON" : "OFF"}</span>
              </button>

              <button
                type="button"
                onClick={() =>
                  setPolicy((prev) => ({
                    ...prev,
                    overtime_enabled: !prev.overtime_enabled,
                  }))
                }
                className={`flex items-center justify-between rounded-2xl border px-4 py-3 text-sm font-medium transition ${
                  policy.overtime_enabled
                    ? "border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-900/50 dark:bg-sky-950/30 dark:text-sky-300"
                    : "border-border bg-background text-foreground"
                }`}
              >
                <span className="flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  Overtime Enabled
                </span>
                <span>{policy.overtime_enabled ? "ON" : "OFF"}</span>
              </button>
            </div>

            <Button className="w-full" onClick={handleSavePolicy} disabled={savingPolicy}>
              {savingPolicy ? <Loader2 className="h-4 w-4 animate-spin" /> : <BadgeCheck className="h-4 w-4" />}
              حفظ السياسة
            </Button>
          </CardContent>
        </Card>
      </div>

      {showUnmapped && (
        <Card className="rounded-2xl border shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle className="text-base">السجلات غير المربوطة</CardTitle>
                <CardDescription>
                  هذه السجلات وصلت من BioTime لكنها غير مرتبطة بموظف داخل النظام.
                </CardDescription>
              </div>

              <Button variant="outline" onClick={() => setShowUnmapped(false)}>
                إخفاء
              </Button>
            </div>
          </CardHeader>

          <CardContent>
            <div className="overflow-x-auto rounded-2xl border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee Code</TableHead>
                    <TableHead>وقت الحركة</TableHead>
                    <TableHead>الجهاز</TableHead>
                    <TableHead>SN</TableHead>
                    <TableHead>IP</TableHead>
                    <TableHead>Raw ID</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {unmappedLogs.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="h-20 text-center text-muted-foreground">
                        لا توجد سجلات غير مربوطة حاليًا.
                      </TableCell>
                    </TableRow>
                  ) : (
                    unmappedLogs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="font-medium">{log.employee_code}</TableCell>
                        <TableCell>{formatDateTime(log.punch_time)}</TableCell>
                        <TableCell>{log.terminal_alias || "—"}</TableCell>
                        <TableCell>{log.device_sn || "—"}</TableCell>
                        <TableCell>{log.device_ip || "—"}</TableCell>
                        <TableCell>{log.raw_id || "—"}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="rounded-2xl border shadow-sm">
          <CardHeader>
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-base">الموظفون الجاهزون للحضور</CardTitle>
                <CardDescription>عرض سريع للموظفين وربطهم الحالي مع BioTime.</CardDescription>
              </div>

              <div className="relative min-w-[220px]">
                <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={employeeSearch}
                  onChange={(e) => setEmployeeSearch(e.target.value)}
                  placeholder="بحث في الموظفين"
                  className="pr-9"
                />
              </div>
            </div>
          </CardHeader>

          <CardContent>
            <div className="overflow-x-auto rounded-2xl border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>الموظف</TableHead>
                    <TableHead>القسم</TableHead>
                    <TableHead>الوظيفة</TableHead>
                    <TableHead>الحالة</TableHead>
                    <TableHead>BioTime</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEmployees.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="h-20 text-center text-muted-foreground">
                        لا توجد بيانات مطابقة.
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredEmployees.slice(0, 10).map((emp) => (
                      <TableRow key={emp.id}>
                        <TableCell className="font-medium">
                          {emp.full_name || emp.name || "—"}
                        </TableCell>
                        <TableCell>{emp.department || "—"}</TableCell>
                        <TableCell>{emp.job_title || "—"}</TableCell>
                        <TableCell>
                          <Badge
                            className={
                              String(emp.status || "").toUpperCase() === "ACTIVE"
                                ? getStatusBadgeClass("active")
                                : getStatusBadgeClass("inactive")
                            }
                          >
                            {emp.status || "—"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {emp.biotime_code ? (
                            <Badge className={getStatusBadgeClass("linked")}>
                              {emp.biotime_code}
                            </Badge>
                          ) : (
                            <Badge className={getStatusBadgeClass("unlinked")}>
                              غير مربوط
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

        <Card className="rounded-2xl border shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">أجهزة BioTime</CardTitle>
            <CardDescription>ملخص سريع لأجهزة الشركة وحالتها الحالية.</CardDescription>
          </CardHeader>

          <CardContent>
            <div className="overflow-x-auto rounded-2xl border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>الجهاز</TableHead>
                    <TableHead>IP</TableHead>
                    <TableHead>الموقع</TableHead>
                    <TableHead>الحالة</TableHead>
                    <TableHead>المستخدمون</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {devices.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="h-20 text-center text-muted-foreground">
                        لا توجد أجهزة مرتبطة حاليًا.
                      </TableCell>
                    </TableRow>
                  ) : (
                    devices.slice(0, 10).map((device) => (
                      <TableRow key={device.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{device.name || "—"}</p>
                            <p className="text-xs text-muted-foreground">{device.sn || "—"}</p>
                          </div>
                        </TableCell>
                        <TableCell>{device.ip || "—"}</TableCell>
                        <TableCell>{device.geo_location || device.location || "—"}</TableCell>
                        <TableCell>
                          <Badge
                            className={
                              String(device.status || "").toLowerCase() === "online"
                                ? getStatusBadgeClass("online")
                                : getStatusBadgeClass("offline")
                            }
                          >
                            {String(device.status || "").toLowerCase() === "online"
                              ? "Online"
                              : "Offline"}
                          </Badge>
                        </TableCell>
                        <TableCell>{device.users ?? 0}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            <div className="mt-4 flex items-center gap-2 rounded-2xl border bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
              <FileSpreadsheet className="h-4 w-4" />
              هذه الصفحة الآن مربوطة بتقرير الحضور الفعلي وسجلات الشركة الحقيقية، مع الإبقاء على
              بيانات BioTime والأجهزة كعناصر مساندة داخل نفس الصفحة بدون كسر الهوية الأساسية للحضور.
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="rounded-2xl border shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">جداول الدوام المعتمدة</CardTitle>
            <CardDescription>عرض سريع لسياسات وجداول الدوام الموجودة فعليًا في النظام.</CardDescription>
          </CardHeader>

          <CardContent className="space-y-3">
            {workSchedules.length === 0 ? (
              <div className="rounded-2xl border bg-muted/30 px-4 py-5 text-sm text-muted-foreground">
                لا توجد جداول دوام حاليًا.
              </div>
            ) : (
              workSchedules.slice(0, 6).map((schedule) => (
                <div key={schedule.id} className="rounded-2xl border bg-muted/30 p-4">
                  <div className="mb-2 flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold">{schedule.name || "—"}</p>
                      <p className="text-xs text-muted-foreground">
                        {getScheduleTypeLabel(schedule.schedule_type)}
                      </p>
                    </div>

                    <Badge
                      className={
                        schedule.is_active
                          ? getStatusBadgeClass("active")
                          : getStatusBadgeClass("inactive")
                      }
                    >
                      {schedule.is_active ? "نشط" : "معطل"}
                    </Badge>
                  </div>

                  <div className="space-y-1 text-sm text-muted-foreground">
                    <p>الفترات: {buildSchedulePeriods(schedule)}</p>
                    <p>
                      الإجازة الأسبوعية:{" "}
                      {schedule.weekend_days_ar || schedule.weekend_days || "—"}
                    </p>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">ملخص البنية التشغيلية</CardTitle>
            <CardDescription>المكونات المتاحة الآن التي تعتمد عليها صفحة الحضور.</CardDescription>
          </CardHeader>

          <CardContent className="space-y-3">
            <div className="rounded-2xl border bg-muted/30 p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Building2 className="h-4 w-4" />
                بنية الصفحة الحالية
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                الصفحة تعتمد الآن على Dashboard الحضور الحقيقي، تقرير السجلات الفعلي،
                سياسة الحضور، الأجهزة، الموظفين، وجداول الدوام.
              </p>
            </div>

            <div className="rounded-2xl border bg-muted/30 p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <GitBranch className="h-4 w-4" />
                جداول الدوام
              </div>
              <p className="mt-2 text-2xl font-bold">{summary.workSchedulesCount}</p>
            </div>

            <div className="rounded-2xl border bg-muted/30 p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <CheckCircle2 className="h-4 w-4" />
                أجهزة BioTime
              </div>
              <p className="mt-2 text-2xl font-bold">{summary.devicesCount}</p>
            </div>

            <div className="rounded-2xl border bg-muted/30 p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Briefcase className="h-4 w-4" />
                موظفون مربوطون
              </div>
              <p className="mt-2 text-2xl font-bold">{summary.linkedEmployees}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}