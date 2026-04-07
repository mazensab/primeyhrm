"use client"

import Image from "next/image"
import { useEffect, useMemo, useState, type ComponentType } from "react"
import { useRouter } from "next/navigation"
import {
  Activity,
  ArrowLeftRight,
  Bell,
  Briefcase,
  Building2,
  CalendarDays,
  CheckCircle2,
  CircleDollarSign,
  ClipboardCheck,
  Clock3,
  Fingerprint,
  Loader2,
  Plane,
  Receipt,
  Shield,
  Sparkles,
  Timer,
  TimerReset,
  TrendingUp,
  UserCheck,
  UserX,
  Users,
  XCircle,
} from "lucide-react"
import { toast } from "sonner"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

/* =========================================
   LANGUAGE / TRANSLATIONS
========================================= */
type Lang = "ar" | "en"

const translations = {
  ar: {
    loading: "جارٍ تحميل لوحة الشركة...",
    failedLoadSession: "فشل في تحميل الجلسة",
    failedReturnToSystem: "فشل في الرجوع إلى النظام",
    returnedToSystem: "تم الرجوع إلى النظام بنجاح",
    serverErrorReturn: "خطأ في الخادم أثناء الرجوع إلى النظام",
    failedLoadDashboard: "فشل في تحميل بيانات لوحة الشركة",
    statusCopied: "تم تحديث الجلسة بنجاح",

    company: "الشركة",
    companyDashboard: "لوحة الشركة",
    companyControlCenter: "مركز تحكم الموارد البشرية والإدارة",

    insideCompanySession:
      "أنت داخل جلسة شركة ويمكنك الرجوع إلى النظام في أي وقت.",

    refreshSession: "تحديث الجلسة",
    returnToSystem: "الرجوع إلى النظام",

    totalEmployees: "إجمالي الموظفين",
    totalEmployeesSubtitle: "القوى العاملة النشطة في الشركة",

    presentToday: "الحاضرون اليوم",
    presentTodaySubtitle: "تم تسجيل حضورهم بنجاح",

    absentToday: "الغائبون اليوم",
    absentTodaySubtitle: "لا توجد سجلات حضور لهم",

    onLeave: "في إجازة",
    onLeaveSubtitle: "طلبات إجازة معتمدة",

    departments: "الأقسام",
    departmentsSubtitle: "أقسام الشركة المُعدّة",

    pendingRequests: "الطلبات المعلقة",
    pendingRequestsSubtitle: "بانتظار مراجعة الموارد البشرية",

    payrollStatus: "حالة الرواتب",
    payrollStatusSubtitle: "الدورة الحالية بانتظار الإجراء",

    monthlyCost: "التكلفة الشهرية",
    monthlyCostSubtitle: "لقطة تقديرية للرواتب",

    draft: "مسودة",
    approved: "معتمد",
    paid: "مدفوع",
    calculated: "محسوب",

    attendanceSnapshot: "ملخص الحضور",
    attendanceSnapshotSubtitle:
      "نظرة يومية على القوى العاملة ومؤشرات الحضور المباشرة",
    liveOverview: "نظرة مباشرة",

    checkedIn: "تم تسجيل الحضور",
    checkedInSubtitle: "الموظفون الحاضرون اليوم",

    lateArrivals: "المتأخرون",
    lateArrivalsSubtitle: "حالات تأخر اليوم",

    missingCheckIn: "بدون تسجيل دخول",
    missingCheckInSubtitle: "لا يوجد حضور صالح حتى الآن",

    syncStatus: "حالة المزامنة",
    syncStatusSubtitle: "اتصال BioTime مستقر",

    attendanceRate: "معدل الحضور",
    attendanceRateSubtitle: "بناءً على سجلات حضور اليوم",

    lastSync: "آخر مزامنة",
    lastSyncSubtitle: "آخر مزامنة ناجحة مع خدمة الأجهزة",

    workforceCoverage: "تغطية القوى العاملة",
    workforceCoverageSubtitle: "إجمالي الفريق ضمن نطاق الحضور",

    healthy: "سليم",

    hrSummary: "ملخص الموارد البشرية",

    leaveRequestsPending: "طلبات الإجازة المعلقة",
    contractsExpiringSoon: "العقود التي ستنتهي قريبًا",
    newEmployeesThisMonth: "الموظفون الجدد هذا الشهر",
    unreadAlerts: "التنبيهات غير المقروءة",

    employeesOverview: "نظرة على الموظفين",
    employeesOverviewSubtitle: "معاينة سريعة لدليل الموظفين وحالة اليوم",
    viewAll: "عرض الكل",

    employee: "الموظف",
    department: "القسم",
    jobTitle: "المسمى الوظيفي",
    status: "الحالة",

    recentActivity: "آخر الأنشطة",
    noRecentActivity: "لا توجد أنشطة حديثة بعد",

    owner: "المالك",
    admin: "مدير",
    hr: "مدير الموارد البشرية",
    manager: "مدير",
    employeeRole: "موظف",
    superAdmin: "سوبر أدمن",
    systemAdmin: "مدير النظام",
    support: "الدعم",

    statusPresent: "حاضر",
    statusLate: "متأخر",
    statusOnLeave: "في إجازة",
    statusAbsent: "غائب",

    activityLeaveRequest: "يوجد طلبات إجازة بانتظار المراجعة",
    activityLeaveRequestMeta: "طلبات الإجازة المعلقة حالياً",

    activityPayrollPending: "آخر دورة رواتب متاحة للمتابعة",
    activityPayrollPendingMeta: "تم جلب آخر حالة تشغيل للرواتب",

    activityAttendanceSync: "بيانات الحضور مرتبطة بالواجهة",
    activityAttendanceSyncMeta: "يتم الآن قراءة ملخص الحضور مباشرة من الـ API",

    activityEmployeeAdded: "تم تحميل دليل الموظفين للشركة",
    activityEmployeeAddedMeta: "يعرض الجدول أول الموظفين من البيانات الفعلية",

    timeNow: "الآن",
    notAvailable: "غير متاح",
  },
  en: {
    loading: "Loading company dashboard...",
    failedLoadSession: "Failed to load session",
    failedReturnToSystem: "Failed to return to system",
    returnedToSystem: "Returned to system successfully",
    serverErrorReturn: "Server error while returning to system",
    failedLoadDashboard: "Failed to load company dashboard data",
    statusCopied: "Session refreshed successfully",

    company: "Company",
    companyDashboard: "Company Dashboard",
    companyControlCenter: "HR & Admin Control Center",

    insideCompanySession:
      "You are inside a company session and can return to system anytime.",

    refreshSession: "Refresh Session",
    returnToSystem: "Return to System",

    totalEmployees: "Total Employees",
    totalEmployeesSubtitle: "Active workforce in company",

    presentToday: "Present Today",
    presentTodaySubtitle: "Checked in successfully",

    absentToday: "Absent Today",
    absentTodaySubtitle: "No attendance recorded",

    onLeave: "On Leave",
    onLeaveSubtitle: "Approved leave requests",

    departments: "Departments",
    departmentsSubtitle: "Configured company departments",

    pendingRequests: "Pending Requests",
    pendingRequestsSubtitle: "Awaiting HR review",

    payrollStatus: "Payroll Status",
    payrollStatusSubtitle: "Current cycle awaiting action",

    monthlyCost: "Monthly Cost",
    monthlyCostSubtitle: "Estimated payroll snapshot",

    draft: "Draft",
    approved: "Approved",
    paid: "Paid",
    calculated: "Calculated",

    attendanceSnapshot: "Attendance Snapshot",
    attendanceSnapshotSubtitle:
      "Daily workforce pulse and live attendance indicators",
    liveOverview: "Live Overview",

    checkedIn: "Checked In",
    checkedInSubtitle: "Employees present today",

    lateArrivals: "Late Arrivals",
    lateArrivalsSubtitle: "Delayed check-ins today",

    missingCheckIn: "Missing Check-in",
    missingCheckInSubtitle: "No valid attendance yet",

    syncStatus: "Sync Status",
    syncStatusSubtitle: "Biotime connection stable",

    attendanceRate: "Attendance Rate",
    attendanceRateSubtitle: "Based on today attendance records",

    lastSync: "Last Sync",
    lastSyncSubtitle: "Latest successful sync with device service",

    workforceCoverage: "Workforce Coverage",
    workforceCoverageSubtitle: "Total team included in attendance scope",

    healthy: "Healthy",

    hrSummary: "HR Summary",

    leaveRequestsPending: "Leave Requests Pending",
    contractsExpiringSoon: "Contracts Expiring Soon",
    newEmployeesThisMonth: "New Employees This Month",
    unreadAlerts: "Unread Alerts",

    employeesOverview: "Employees Overview",
    employeesOverviewSubtitle:
      "Quick preview of employee directory and daily status",
    viewAll: "View All",

    employee: "Employee",
    department: "Department",
    jobTitle: "Job Title",
    status: "Status",

    recentActivity: "Recent Activity",
    noRecentActivity: "No recent activity yet",

    owner: "Owner",
    admin: "Admin",
    hr: "HR Manager",
    manager: "Manager",
    employeeRole: "Employee",
    superAdmin: "Super Admin",
    systemAdmin: "System Admin",
    support: "Support",

    statusPresent: "Present",
    statusLate: "Late",
    statusOnLeave: "On Leave",
    statusAbsent: "Absent",

    activityLeaveRequest: "There are leave requests pending review",
    activityLeaveRequestMeta: "Current pending leave requests",

    activityPayrollPending: "Latest payroll run is available for follow-up",
    activityPayrollPendingMeta: "Latest payroll run status fetched",

    activityAttendanceSync: "Attendance data is connected to the UI",
    activityAttendanceSyncMeta: "Attendance snapshot is now loaded from the API",

    activityEmployeeAdded: "Employee directory loaded for this company",
    activityEmployeeAddedMeta: "The table shows the first real employees",

    timeNow: "Now",
    notAvailable: "Not available",
  },
} as const

/* =========================================
   READ CSRF TOKEN FROM COOKIE
========================================= */
function getCookie(name: string) {
  if (typeof document === "undefined") return null

  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift() || null
  }

  return null
}

function normalizeApiBase(raw?: string) {
  const fallback = "http://localhost:8000"
  return (raw || fallback).replace(/\/$/, "")
}

function getDocumentLang(): Lang {
  if (typeof document === "undefined") return "ar"

  const lang =
    document.documentElement.lang ||
    document.body.getAttribute("lang") ||
    "ar"

  return lang.toLowerCase().startsWith("en") ? "en" : "ar"
}

function formatNumber(value: number | string) {
  return new Intl.NumberFormat("en-US").format(Number(value || 0))
}

function formatTimeLabel(value: string) {
  return value
}

function formatMonthLabel(value?: string | null) {
  if (!value) return "--"
  return value
}

/* =========================================
   TYPES
========================================= */
type WhoAmIResponse = {
  authenticated?: boolean
  user?: {
    id?: number
    username?: string
    email?: string | null
    full_name?: string | null
    avatar?: string | null
  } | null
  role?: string | null
  company?: {
    id?: number
    name?: string
  } | null
  subscription?: {
    apps?: string[]
    apps_snapshot?: string[]
    days_remaining?: number | null
  } | null
  impersonation?: {
    active?: boolean
    source_user_id?: number | null
    source_username?: string | null
    source_email?: string | null
    company_id?: number | null
    company_name?: string | null
    company_user_id?: number | null
    target_user_id?: number | null
    target_username?: string | null
    target_role?: string | null
  } | null
}

type StatCard = {
  title: string
  value: string | number
  subtitle: string
  icon: ComponentType<{ className?: string }>
  isCurrency?: boolean
}

type EmployeeStatusKey = "PRESENT" | "LATE" | "ON_LEAVE" | "ABSENT"

type EmployeePreviewRow = {
  id: number
  name: string
  departmentLabel: string
  jobTitleLabel: string
  statusKey: EmployeeStatusKey
  avatar?: string | null
}

type ActivityItem = {
  id: number
  title: string
  meta: string
  time: string
  icon: ComponentType<{ className?: string }>
}

type StatusMeta = {
  label: string
  icon: ComponentType<{ className?: string }>
  className: string
}

type CompanyEmployee = {
  id: number
  name?: string
  full_name?: string
  email?: string | null
  phone?: string | null
  avatar?: string | null
  photo_url?: string | null
  role?: string | null
  department?: string | null
  job_title?: string | null
  join_date?: string | null
  employee_number?: string | null
  status?: string | null
  is_active?: boolean
}

type CompanyEmployeesResponse = {
  status?: string
  employees?: CompanyEmployee[]
}

type AttendanceDashboardResponse = {
  status?: string
  data?: {
    today?: {
      present?: number
      absent?: number
      late?: number
      leave?: number
    }
    total_records?: number
  }
}

type LeaveRequestItem = {
  id: number
  employee_name?: string
  employee_id?: number
  type?: string
  from_date?: string
  to_date?: string
  status?: string
}

type LeaveRequestsResponse = {
  requests?: LeaveRequestItem[]
}

type DepartmentItem = {
  id: number
  name?: string
}

type DepartmentsResponse = {
  status?: string
  departments?: DepartmentItem[]
}

type PayrollRunItem = {
  id: number
  month?: string
  status?: string
  total_net?: number
  progress_percent?: number
  accounting_consistency?: boolean
  total_employees?: number
}

type PayrollRunsResponse = PayrollRunItem[] | { results?: PayrollRunItem[] }

/* =========================================
   HELPERS
========================================= */
function getStatusClasses(status: EmployeeStatusKey) {
  switch (status) {
    case "PRESENT":
      return [
        "border-emerald-200/80",
        "bg-emerald-50",
        "text-emerald-700",
        "dark:border-emerald-500/20",
        "dark:bg-emerald-500/10",
        "dark:text-emerald-300",
      ].join(" ")
    case "LATE":
      return [
        "border-amber-200/80",
        "bg-amber-50",
        "text-amber-700",
        "dark:border-amber-500/20",
        "dark:bg-amber-500/10",
        "dark:text-amber-300",
      ].join(" ")
    case "ON_LEAVE":
      return [
        "border-sky-200/80",
        "bg-sky-50",
        "text-sky-700",
        "dark:border-sky-500/20",
        "dark:bg-sky-500/10",
        "dark:text-sky-300",
      ].join(" ")
    case "ABSENT":
      return [
        "border-rose-200/80",
        "bg-rose-50",
        "text-rose-700",
        "dark:border-rose-500/20",
        "dark:bg-rose-500/10",
        "dark:text-rose-300",
      ].join(" ")
    default:
      return "border-border bg-muted text-foreground"
  }
}

function getStatusMeta(status: EmployeeStatusKey, lang: Lang): StatusMeta {
  const t = translations[lang]

  switch (status) {
    case "PRESENT":
      return {
        label: t.statusPresent,
        icon: CheckCircle2,
        className: getStatusClasses(status),
      }
    case "LATE":
      return {
        label: t.statusLate,
        icon: Timer,
        className: getStatusClasses(status),
      }
    case "ON_LEAVE":
      return {
        label: t.statusOnLeave,
        icon: Plane,
        className: getStatusClasses(status),
      }
    case "ABSENT":
      return {
        label: t.statusAbsent,
        icon: XCircle,
        className: getStatusClasses(status),
      }
    default:
      return {
        label: String(status || ""),
        icon: Activity,
        className: "border-border bg-muted text-foreground",
      }
  }
}

function getDepartmentClasses(department?: string | null) {
  const safe = String(department || "").trim().toUpperCase()

  switch (safe) {
    case "HR":
    case "الموارد البشرية":
      return "border-violet-500/20 bg-violet-500/10 text-violet-700 dark:text-violet-300"
    case "PAYROLL":
    case "الرواتب":
      return "border-blue-500/20 bg-blue-500/10 text-blue-700 dark:text-blue-300"
    case "OPERATIONS":
    case "العمليات":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
    case "ADMINISTRATION":
    case "الإدارة":
      return "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300"
    case "FINANCE":
    case "المالية":
      return "border-cyan-500/20 bg-cyan-500/10 text-cyan-700 dark:text-cyan-300"
    default:
      return "border-border bg-muted text-foreground"
  }
}

function getInitials(value?: string | null) {
  const safe = String(value || "").trim()
  if (!safe) return "U"

  return (
    safe
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "U"
  )
}

function getRoleLabel(role: string | null | undefined, lang: Lang) {
  const t = translations[lang]
  const safe = String(role || "").trim().toUpperCase()

  switch (safe) {
    case "OWNER":
      return t.owner
    case "ADMIN":
      return t.admin
    case "HR":
      return t.hr
    case "MANAGER":
      return t.manager
    case "EMPLOYEE":
      return t.employeeRole
    case "SUPER_ADMIN":
      return t.superAdmin
    case "SYSTEM_ADMIN":
      return t.systemAdmin
    case "SUPPORT":
      return t.support
    default:
      return safe || t.admin
  }
}

function getRoleBadgeClass(role?: string | null) {
  const safe = String(role || "").trim().toUpperCase()

  switch (safe) {
    case "OWNER":
      return "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300"
    case "HR":
      return "border-violet-500/30 bg-violet-500/10 text-violet-700 dark:text-violet-300"
    case "MANAGER":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
    case "ADMIN":
      return "border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-300"
    default:
      return "border-primary/20 bg-primary/10 text-primary"
  }
}

function normalizeEmployeeStatus(
  status?: string | null,
  isActive?: boolean
): EmployeeStatusKey {
  const safe = String(status || "").trim().toUpperCase()

  if (safe === "LATE") return "LATE"
  if (safe === "LEAVE" || safe === "ON_LEAVE") return "ON_LEAVE"
  if (safe === "ABSENT" || safe === "INACTIVE") return "ABSENT"
  if (safe === "ACTIVE" || safe === "PRESENT") return "PRESENT"

  return isActive === false ? "ABSENT" : "PRESENT"
}

function getPayrollStatusLabel(
  status: string | null | undefined,
  lang: Lang
): string {
  const t = translations[lang]
  const safe = String(status || "").trim().toUpperCase()

  switch (safe) {
    case "DRAFT":
      return t.draft
    case "APPROVED":
      return t.approved
    case "PAID":
      return t.paid
    case "CALCULATED":
      return t.calculated
    default:
      return safe || t.draft
  }
}

async function fetchJson<T>(url: string): Promise<T | null> {
  const res = await fetch(url, {
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  })

  if (!res.ok) {
    throw new Error(`Request failed: ${url} (${res.status})`)
  }

  return (await res.json()) as T
}

/* =========================================
   REUSABLE STATUS BADGE
========================================= */
function StatusBadge({
  status,
  lang,
}: {
  status: EmployeeStatusKey
  lang: Lang
}) {
  const meta = getStatusMeta(status, lang)
  const Icon = meta.icon
  const isArabic = lang === "ar"

  return (
    <Badge
      variant="outline"
      dir={isArabic ? "rtl" : "ltr"}
      className={[
        "inline-flex h-8 min-w-[112px] items-center justify-center gap-1.5 rounded-full px-3 text-xs font-semibold shadow-sm transition-colors",
        "whitespace-nowrap",
        meta.className,
      ].join(" ")}
    >
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span>{meta.label}</span>
    </Badge>
  )
}

export default function CompanyPage() {
  const router = useRouter()
  const API_BASE = normalizeApiBase(process.env.NEXT_PUBLIC_API_URL)

  const [sessionData, setSessionData] = useState<WhoAmIResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [returning, setReturning] = useState(false)
  const [lang, setLang] = useState<Lang>("ar")

  const [employeesData, setEmployeesData] = useState<CompanyEmployee[]>([])
  const [attendanceData, setAttendanceData] =
    useState<AttendanceDashboardResponse["data"] | null>(null)
  const [leaveRequests, setLeaveRequests] = useState<LeaveRequestItem[]>([])
  const [departmentsData, setDepartmentsData] = useState<DepartmentItem[]>([])
  const [payrollRuns, setPayrollRuns] = useState<PayrollRunItem[]>([])

  useEffect(() => {
    setLang(getDocumentLang())

    const observer = new MutationObserver(() => {
      setLang(getDocumentLang())
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const loadPageData = async () => {
      setLoading(true)

      try {
        const results = await Promise.allSettled([
          fetchJson<WhoAmIResponse>(`${API_BASE}/api/auth/whoami/`),
          fetchJson<CompanyEmployeesResponse>(`${API_BASE}/api/company/employees/`),
          fetchJson<AttendanceDashboardResponse>(
            `${API_BASE}/api/company/attendance/dashboard/`
          ),
          fetchJson<LeaveRequestsResponse>(`${API_BASE}/api/company/leaves/requests/`),
          fetchJson<DepartmentsResponse>(`${API_BASE}/api/company/departments/list/`),
          fetchJson<PayrollRunsResponse>(`${API_BASE}/api/company/payroll/runs/`),
        ])

        const whoamiResult = results[0]
        const employeesResult = results[1]
        const attendanceResult = results[2]
        const leavesResult = results[3]
        const departmentsResult = results[4]
        const payrollRunsResult = results[5]

        if (whoamiResult.status === "fulfilled") {
          setSessionData(whoamiResult.value || null)
        }

        if (employeesResult.status === "fulfilled") {
          setEmployeesData(employeesResult.value?.employees || [])
        } else {
          setEmployeesData([])
        }

        if (attendanceResult.status === "fulfilled") {
          setAttendanceData(attendanceResult.value?.data || null)
        } else {
          setAttendanceData(null)
        }

        if (leavesResult.status === "fulfilled") {
          setLeaveRequests(leavesResult.value?.requests || [])
        } else {
          setLeaveRequests([])
        }

        if (departmentsResult.status === "fulfilled") {
          setDepartmentsData(departmentsResult.value?.departments || [])
        } else {
          setDepartmentsData([])
        }

        if (payrollRunsResult.status === "fulfilled") {
          const payload = payrollRunsResult.value
          if (Array.isArray(payload)) {
            setPayrollRuns(payload)
          } else {
            setPayrollRuns(payload?.results || [])
          }
        } else {
          setPayrollRuns([])
        }
      } catch (error) {
        console.error("Failed loading company dashboard data", error)
        toast.error(translations[getDocumentLang()].failedLoadDashboard)
      } finally {
        setLoading(false)
      }
    }

    loadPageData()
  }, [API_BASE])

  const t = useMemo(() => translations[lang], [lang])
  const isArabic = lang === "ar"

  const isImpersonationActive = Boolean(sessionData?.impersonation?.active)

  const companyName =
    sessionData?.company?.name ||
    sessionData?.impersonation?.company_name ||
    t.company

  const sessionRole =
    sessionData?.role ||
    sessionData?.impersonation?.target_role ||
    "ADMIN"

  const latestPayrollRun = payrollRuns[0] || null

  const approvedLeaveCount = useMemo(() => {
    return leaveRequests.filter(
      (item) => String(item.status || "").trim().toLowerCase() === "approved"
    ).length
  }, [leaveRequests])

  const pendingLeaveCount = useMemo(() => {
    return leaveRequests.filter(
      (item) => String(item.status || "").trim().toLowerCase() === "pending"
    ).length
  }, [leaveRequests])

  const newEmployeesThisMonth = useMemo(() => {
    const now = new Date()
    const currentMonth = now.getMonth()
    const currentYear = now.getFullYear()

    return employeesData.filter((employee) => {
      if (!employee.join_date) return false
      const joinedAt = new Date(employee.join_date)
      return (
        !Number.isNaN(joinedAt.getTime()) &&
        joinedAt.getMonth() === currentMonth &&
        joinedAt.getFullYear() === currentYear
      )
    }).length
  }, [employeesData])

  const mappedEmployeePreviewRows = useMemo<EmployeePreviewRow[]>(() => {
    return employeesData.slice(0, 5).map((employee) => ({
      id: employee.id,
      name: employee.full_name || employee.name || `EMP-${employee.id}`,
      departmentLabel: employee.department || "-",
      jobTitleLabel: employee.job_title || "-",
      statusKey: normalizeEmployeeStatus(employee.status, employee.is_active),
      avatar: employee.avatar || employee.photo_url || null,
    }))
  }, [employeesData])

  const recentActivities: ActivityItem[] = useMemo(() => {
    const items: ActivityItem[] = []

    if (pendingLeaveCount > 0) {
      items.push({
        id: 1,
        title: t.activityLeaveRequest,
        meta: `${t.activityLeaveRequestMeta} • ${formatNumber(pendingLeaveCount)}`,
        time: t.timeNow,
        icon: CalendarDays,
      })
    }

    if (latestPayrollRun) {
      items.push({
        id: 2,
        title: t.activityPayrollPending,
        meta: `${t.activityPayrollPendingMeta} • ${formatMonthLabel(
          latestPayrollRun.month
        )}`,
        time: t.timeNow,
        icon: Receipt,
      })
    }

    if (attendanceData) {
      items.push({
        id: 3,
        title: t.activityAttendanceSync,
        meta: t.activityAttendanceSyncMeta,
        time: t.timeNow,
        icon: Fingerprint,
      })
    }

    if (employeesData.length > 0) {
      items.push({
        id: 4,
        title: t.activityEmployeeAdded,
        meta: `${t.activityEmployeeAddedMeta} • ${formatNumber(employeesData.length)}`,
        time: t.timeNow,
        icon: Users,
      })
    }

    return items
  }, [attendanceData, employeesData.length, latestPayrollRun, pendingLeaveCount, t])

  const overviewStats: StatCard[] = [
    {
      title: t.totalEmployees,
      value: formatNumber(employeesData.length),
      subtitle: t.totalEmployeesSubtitle,
      icon: Users,
    },
    {
      title: t.presentToday,
      value: formatNumber(attendanceData?.today?.present || 0),
      subtitle: t.presentTodaySubtitle,
      icon: UserCheck,
    },
    {
      title: t.absentToday,
      value: formatNumber(attendanceData?.today?.absent || 0),
      subtitle: t.absentTodaySubtitle,
      icon: UserX,
    },
    {
      title: t.onLeave,
      value: formatNumber(attendanceData?.today?.leave || approvedLeaveCount),
      subtitle: t.onLeaveSubtitle,
      icon: CalendarDays,
    },
  ]

  const managementStats: StatCard[] = [
    {
      title: t.departments,
      value: formatNumber(departmentsData.length),
      subtitle: t.departmentsSubtitle,
      icon: Briefcase,
    },
    {
      title: t.pendingRequests,
      value: formatNumber(pendingLeaveCount),
      subtitle: t.pendingRequestsSubtitle,
      icon: ClipboardCheck,
    },
    {
      title: t.payrollStatus,
      value: getPayrollStatusLabel(latestPayrollRun?.status, lang),
      subtitle: t.payrollStatusSubtitle,
      icon: Receipt,
    },
    {
      title: t.monthlyCost,
      value: formatNumber(latestPayrollRun?.total_net || 0),
      subtitle: t.monthlyCostSubtitle,
      icon: CircleDollarSign,
      isCurrency: true,
    },
  ]

  const attendanceRate = useMemo(() => {
    if (!employeesData.length) return 0
    return Math.round(
      ((attendanceData?.today?.present || 0) / employeesData.length) * 100
    )
  }, [attendanceData?.today?.present, employeesData.length])

  const handleReturnToSystem = async () => {
    setReturning(true)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        `${API_BASE}/api/system/companies/exit-session/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken || "",
          },
        }
      )

      const data = await res.json()

      if (!res.ok) {
        toast.error(data.error || t.failedReturnToSystem)
        return
      }

      toast.success(data.message || t.returnedToSystem)
      window.location.href = data.redirect_to || "/system/companies"
    } catch (error) {
      console.error("Exit session error:", error)
      toast.error(t.serverErrorReturn)
    } finally {
      setReturning(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6" dir={isArabic ? "rtl" : "ltr"}>
        <Card className="rounded-2xl border-border/60 shadow-sm">
          <CardContent className="flex items-center justify-center py-20 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className={isArabic ? "mr-2" : "ml-2"}>{t.loading}</span>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6" dir={isArabic ? "rtl" : "ltr"}>
      {/* =========================================================
         HEADER
      ========================================================= */}
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border bg-background shadow-sm">
              <Building2 className="h-5 w-5" />
            </div>

            <div>
              <h1 className="text-3xl font-semibold tracking-tight">
                {t.companyDashboard}
              </h1>
              <p className="text-sm text-muted-foreground">
                {companyName} — {t.companyControlCenter}
              </p>
            </div>
          </div>

          {isImpersonationActive && (
            <div className="inline-flex rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-900">
              {t.insideCompanySession}
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Badge
            className={`gap-2 px-4 py-2 text-sm font-medium shadow-sm ${getRoleBadgeClass(
              sessionRole
            )}`}
          >
            <Shield className="h-4 w-4" />
            {getRoleLabel(sessionRole, lang)}
          </Badge>

          <Button
            variant="outline"
            onClick={() => {
              router.refresh()
              toast.success(t.statusCopied)
            }}
            className="h-10 rounded-xl px-4"
          >
            {t.refreshSession}
          </Button>

          {isImpersonationActive && (
            <Button
              variant="outline"
              onClick={handleReturnToSystem}
              disabled={returning}
              className="h-10 rounded-xl px-4"
            >
              {returning ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowLeftRight className="h-4 w-4" />
              )}
              <span className={isArabic ? "mr-2" : "ml-2"}>
                {t.returnToSystem}
              </span>
            </Button>
          )}
        </div>
      </div>

      {/* =========================================================
         OVERVIEW CARDS
      ========================================================= */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {overviewStats.map((item) => {
          const Icon = item.icon

          return (
            <Card
              key={item.title}
              className="rounded-2xl border-border/60 shadow-sm"
            >
              <CardContent className="flex items-start justify-between p-4">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">
                    {item.title}
                  </p>
                  <p className="mt-2 text-2xl font-semibold">{item.value}</p>
                  <p className="mt-1.5 text-[11px] text-muted-foreground">
                    {item.subtitle}
                  </p>
                </div>

                <div className="rounded-2xl border bg-muted/40 p-2.5">
                  <Icon className="h-4.5 w-4.5" />
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* =========================================================
         MANAGEMENT / HR CARDS
      ========================================================= */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {managementStats.map((item) => {
          const Icon = item.icon

          return (
            <Card
              key={item.title}
              className="rounded-2xl border-border/60 shadow-sm"
            >
              <CardContent className="flex items-start justify-between p-4">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">
                    {item.title}
                  </p>

                  {item.isCurrency ? (
                    <div
                      dir="ltr"
                      className="mt-2 flex items-center gap-2 text-2xl font-semibold"
                    >
                      <Image
                        src="/currency/sar.svg"
                        alt="SAR"
                        width={16}
                        height={16}
                        className="h-4 w-4 shrink-0"
                      />
                      <span>{item.value}</span>
                    </div>
                  ) : (
                    <p className="mt-2 text-2xl font-semibold">{item.value}</p>
                  )}

                  <p className="mt-1.5 text-[11px] text-muted-foreground">
                    {item.subtitle}
                  </p>
                </div>

                <div className="rounded-2xl border bg-muted/40 p-2.5">
                  <Icon className="h-4.5 w-4.5" />
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* =========================================================
         ATTENDANCE + HR SUMMARY
      ========================================================= */}
      <div className="grid gap-6 xl:grid-cols-[1.6fr_.8fr]">
        <Card className="rounded-2xl border-border/60 shadow-sm">
          <CardHeader className="border-b pb-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle className="text-xl">{t.attendanceSnapshot}</CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">
                  {t.attendanceSnapshotSubtitle}
                </p>
              </div>

              <Badge variant="outline" className="gap-2 px-3 py-1.5">
                <Activity className="h-3.5 w-3.5" />
                {t.liveOverview}
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-4 pt-5">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-2xl border bg-background p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock3 className="h-4 w-4" />
                  {t.checkedIn}
                </div>
                <div className="mt-2.5 text-2xl font-semibold">
                  {formatNumber(attendanceData?.today?.present || 0)}
                </div>
                <p className="mt-1.5 text-[11px] text-muted-foreground">
                  {t.checkedInSubtitle}
                </p>
              </div>

              <div className="rounded-2xl border bg-background p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <TrendingUp className="h-4 w-4" />
                  {t.lateArrivals}
                </div>
                <div className="mt-2.5 text-2xl font-semibold">
                  {formatNumber(attendanceData?.today?.late || 0)}
                </div>
                <p className="mt-1.5 text-[11px] text-muted-foreground">
                  {t.lateArrivalsSubtitle}
                </p>
              </div>

              <div className="rounded-2xl border bg-background p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <UserX className="h-4 w-4" />
                  {t.missingCheckIn}
                </div>
                <div className="mt-2.5 text-2xl font-semibold">
                  {formatNumber(attendanceData?.today?.absent || 0)}
                </div>
                <p className="mt-1.5 text-[11px] text-muted-foreground">
                  {t.missingCheckInSubtitle}
                </p>
              </div>

              <div className="rounded-2xl border bg-background p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Fingerprint className="h-4 w-4" />
                  {t.syncStatus}
                </div>
                <div className="mt-2.5 text-2xl font-semibold">{t.healthy}</div>
                <p className="mt-1.5 text-[11px] text-muted-foreground">
                  {t.syncStatusSubtitle}
                </p>
              </div>
            </div>

            <div className="grid gap-3 lg:grid-cols-3">
              <div className="rounded-2xl border bg-muted/20 p-4">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Sparkles className="h-4 w-4 text-primary" />
                  {t.attendanceRate}
                </div>
                <div className="mt-2.5 text-xl font-semibold">
                  {formatNumber(attendanceRate)}%
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  {t.attendanceRateSubtitle}
                </p>
              </div>

              <div className="rounded-2xl border bg-muted/20 p-4">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <TimerReset className="h-4 w-4 text-primary" />
                  {t.lastSync}
                </div>
                <div dir="ltr" className="mt-2.5 text-xl font-semibold">
                  --
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  {t.lastSyncSubtitle}
                </p>
              </div>

              <div className="rounded-2xl border bg-muted/20 p-4">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Users className="h-4 w-4 text-primary" />
                  {t.workforceCoverage}
                </div>
                <div className="mt-2.5 text-xl font-semibold">
                  {formatNumber(employeesData.length)}
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  {t.workforceCoverageSubtitle}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-border/60 shadow-sm xl:sticky xl:top-6">
          <CardHeader className="border-b pb-4">
            <CardTitle className="text-xl">{t.hrSummary}</CardTitle>
          </CardHeader>

          <CardContent className="pt-5">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <div className="rounded-2xl border bg-background p-4">
                <p className="text-xs font-medium text-muted-foreground">
                  {t.leaveRequestsPending}
                </p>
                <div className="mt-2 flex items-end justify-between gap-3">
                  <p className="text-2xl font-semibold">
                    {formatNumber(pendingLeaveCount)}
                  </p>
                  <CalendarDays className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>

              <div className="rounded-2xl border bg-background p-4">
                <p className="text-xs font-medium text-muted-foreground">
                  {t.contractsExpiringSoon}
                </p>
                <div className="mt-2 flex items-end justify-between gap-3">
                  <p className="text-2xl font-semibold">{formatNumber(0)}</p>
                  <Receipt className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>

              <div className="rounded-2xl border bg-background p-4">
                <p className="text-xs font-medium text-muted-foreground">
                  {t.newEmployeesThisMonth}
                </p>
                <div className="mt-2 flex items-end justify-between gap-3">
                  <p className="text-2xl font-semibold">
                    {formatNumber(newEmployeesThisMonth)}
                  </p>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>

              <div className="rounded-2xl border bg-background p-4">
                <p className="text-xs font-medium text-muted-foreground">
                  {t.unreadAlerts}
                </p>
                <div className="mt-2 flex items-end justify-between gap-3">
                  <p className="text-2xl font-semibold">{formatNumber(0)}</p>
                  <Bell className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* =========================================================
         EMPLOYEES + ACTIVITY
      ========================================================= */}
      <div className="grid gap-6 xl:grid-cols-[1.6fr_.8fr]">
        <Card className="rounded-2xl border-border/60 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between border-b pb-4">
            <div>
              <CardTitle className="text-xl">{t.employeesOverview}</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">
                {t.employeesOverviewSubtitle}
              </p>
            </div>

            <Button
              variant="outline"
              className="h-10 rounded-xl px-4"
              onClick={() => router.push("/company/employees")}
            >
              {t.viewAll}
            </Button>
          </CardHeader>

          <CardContent className="pt-5">
            <div className="overflow-hidden rounded-2xl border bg-background">
              <div className="w-full overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="border-b bg-muted/30 hover:bg-muted/30">
                      <TableHead className="h-12 min-w-[280px] px-5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        {t.employee}
                      </TableHead>
                      <TableHead className="h-12 min-w-[150px] px-5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        {t.department}
                      </TableHead>
                      <TableHead className="h-12 min-w-[180px] px-5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        {t.jobTitle}
                      </TableHead>
                      <TableHead className="h-12 min-w-[140px] px-5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        {t.status}
                      </TableHead>
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {mappedEmployeePreviewRows.map((employee) => (
                      <TableRow
                        key={employee.id}
                        className="group border-b last:border-b-0 hover:bg-muted/20"
                      >
                        <TableCell className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <Avatar className="h-11 w-11 shrink-0 rounded-xl border">
                              <AvatarImage
                                src={employee.avatar || ""}
                                alt={employee.name}
                              />
                              <AvatarFallback className="rounded-xl text-xs font-semibold">
                                {getInitials(employee.name)}
                              </AvatarFallback>
                            </Avatar>

                            <div className="min-w-0">
                              <div className="truncate text-sm font-semibold text-foreground">
                                {employee.name}
                              </div>
                              <div
                                dir="ltr"
                                className="mt-0.5 truncate text-xs text-muted-foreground"
                              >
                                EMP-{String(employee.id).padStart(4, "0")}
                              </div>
                            </div>
                          </div>
                        </TableCell>

                        <TableCell className="px-5 py-4">
                          <span
                            className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${getDepartmentClasses(
                              employee.departmentLabel
                            )}`}
                          >
                            {employee.departmentLabel}
                          </span>
                        </TableCell>

                        <TableCell className="px-5 py-4 text-sm text-muted-foreground">
                          {employee.jobTitleLabel}
                        </TableCell>

                        <TableCell className="px-5 py-4">
                          <StatusBadge
                            status={employee.statusKey}
                            lang={lang}
                          />
                        </TableCell>
                      </TableRow>
                    ))}

                    {mappedEmployeePreviewRows.length === 0 && (
                      <TableRow>
                        <TableCell
                          colSpan={4}
                          className="px-5 py-10 text-center text-sm text-muted-foreground"
                        >
                          {t.notAvailable}
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-border/60 shadow-sm">
          <CardHeader className="border-b pb-4">
            <CardTitle className="text-xl">{t.recentActivity}</CardTitle>
          </CardHeader>

          <CardContent className="pt-5">
            {recentActivities.length === 0 ? (
              <div className="rounded-2xl border bg-background p-6 text-sm text-muted-foreground">
                {t.noRecentActivity}
              </div>
            ) : (
              <div className="relative space-y-0">
                <div
                  className={`absolute top-1 bottom-1 w-px bg-border ${
                    isArabic ? "right-[17px]" : "left-[17px]"
                  }`}
                />

                {recentActivities.map((item, index) => {
                  const Icon = item.icon

                  return (
                    <div
                      key={item.id}
                      className={`relative flex gap-4 ${
                        index !== recentActivities.length - 1 ? "pb-5" : ""
                      }`}
                    >
                      <div className="relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border bg-background shadow-sm">
                        <Icon className="h-4 w-4" />
                      </div>

                      <div className="min-w-0 flex-1 rounded-2xl border bg-background p-4">
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-sm font-semibold leading-6">
                            {item.title}
                          </p>
                          <span
                            dir="ltr"
                            className="shrink-0 text-[11px] text-muted-foreground"
                          >
                            {formatTimeLabel(item.time)}
                          </span>
                        </div>

                        <p className="mt-1 text-sm leading-6 text-muted-foreground">
                          {item.meta}
                        </p>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}